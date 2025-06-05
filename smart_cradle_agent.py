import cv2
import requests
import time
import socket
import qrcode
from PIL import Image, ImageFont, ImageDraw
import paho.mqtt.client as mqtt
import json
import uuid
import threading
from picamera2 import Picamera2
import serial
import datetime
import numpy as np
import base64
import sounddevice as sd
import soundfile as sf
import librosa
import joblib
import mediapipe as mp

# 설정
SERVER_URL = 'http://192.168.219.111:80'
CRADLE_UUID = 'cradle-unique-id-example'
FRAME_UPLOAD_INTERVAL = 0.1
QR_CODE_FILENAME = 'cradle_qrcode.png'

# MQTT 설정
MQTT_BROKER_HOST = "192.168.219.111"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC_TEMPERATURE = f"cradle/{CRADLE_UUID}/temperature"
MQTT_TOPIC_FRAME = f"cradle/{CRADLE_UUID}/frame"
MQTT_TOPIC_CRYING = f"cradle/{CRADLE_UUID}/crying"
MQTT_TOPIC_DIRECTION = f"cradle/{CRADLE_UUID}/direction"
MQTT_TOPIC_SERVO = f"cradle/{CRADLE_UUID}/servo"

# 미디어파이프 설정
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# 오디오 설정
INPUT_SR = 44100
TARGET_SR = 16000
DURATION = 2
N_MFCC = 13
MAX_LEN = 40
MODEL_PATH = "knn_model.joblib"
DEVICE_INDEX = 2
TEMP_AUDIO_FILE = "temp_resampled.wav"

# 시리얼 통신 설정
SERIAL_PORT = '/dev/ttyACM0'
BAUDRATE = 9600
ser = None
try:
    ser = serial.Serial(SERIAL_PORT, BAUDRATE)
    print(f"시리얼 포트 {SERIAL_PORT} 연결 성공")
except serial.SerialException as e:
    print(f"시리얼 포트 {SERIAL_PORT} 연결 실패: {e}")

# MQTT 클라이언트 설정
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT Broker 연결 성공")
        client.subscribe(MQTT_TOPIC_SERVO)
    else:
        print(f"MQTT Broker 연결 실패, rc={rc}")

def on_message(client, userdata, msg):
    if msg.topic == MQTT_TOPIC_SERVO:
        try:
            payload = json.loads(msg.payload.decode())
            action = payload.get('action')
            print(f"모터 제어 명령 수신: {action}")
            
            if action == 'start' and ser:
                ser.write(b'servo\n')
                print("모터 작동 시작")
            elif action == 'stop' and ser:
                ser.write(b'stop\n')
                print("모터 작동 중지")
        except Exception as e:
            print(f"모터 제어 명령 처리 실패: {e}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

try:
    mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"MQTT 연결 오류: {e}")

# 카메라 초기화
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
picam2.start()
time.sleep(2)

try:
    font = ImageFont.truetype('/home/jh/camTest/fonts/SCDream6.otf', 20)
except IOError:
    print("폰트 파일이 없습니다. 기본 폰트를 사용합니다.")
    font = ImageFont.load_default()

def generate_qr_code(uuid, filename):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uuid)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    img.save(filename)
    print(f"QR 코드가 {filename}으로 저장되었습니다.")

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def register_agent():
    agent_ip = get_ip()
    try:
        response = requests.post(f'{SERVER_URL}/register_agent', json={'uuid': CRADLE_UUID, 'ip': agent_ip})
        print(response.json())
    except Exception as e:
        print("서버 연결 실패:", e)

def record_resample():
    try:
        print("[DEBUG] 녹음 시작...")
        audio = sd.rec(int(DURATION * INPUT_SR), samplerate=INPUT_SR,
                      channels=1, dtype='float32', device=DEVICE_INDEX)
        sd.wait()
        audio = audio.flatten()
        y_resampled = librosa.resample(audio, orig_sr=INPUT_SR, target_sr=TARGET_SR)
        sf.write(TEMP_AUDIO_FILE, y_resampled, TARGET_SR)
        print("[DEBUG] 녹음 완료 및 리샘플링")
    except Exception as e:
        print(f"[ERROR] 녹음 실패: {e}")

def extract_mfcc(file_path):
    try:
        print("[DEBUG] MFCC 추출 시작...")
        y, sr = librosa.load(file_path, sr=TARGET_SR, duration=DURATION)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
        if mfcc.shape[1] < MAX_LEN:
            mfcc = np.pad(mfcc, ((0, 0), (0, MAX_LEN - mfcc.shape[1])), mode='constant')
        else:
            mfcc = mfcc[:, :MAX_LEN]
        print("[DEBUG] MFCC 추출 완료")
        return mfcc.flatten()
    except Exception as e:
        print(f"[ERROR] MFCC 추출 실패: {e}")
        return None

def predict_cry():
    try:
        print("[DEBUG] 울음 감지 시작...")
        mfcc = extract_mfcc(TEMP_AUDIO_FILE)
        if mfcc is None:
            print("[ERROR] MFCC 추출 실패로 울음 감지 불가")
            return

        model = joblib.load(MODEL_PATH)
        result = model.predict([mfcc])[0]
        prob = model.predict_proba([mfcc])[0][1]
        
        crying_status = "Crying" if result == 1 else "Silent"
        print(f"[DEBUG] 울음 감지 결과: {crying_status} (확률: {prob:.3f})")
        
        payload = json.dumps({
            "status": crying_status,
            "probability": float(prob),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        mqtt_client.publish(MQTT_TOPIC_CRYING, payload)
        print("[DEBUG] 울음 상태 MQTT 전송 완료")
    except Exception as e:
        print(f"[ERROR] 울음 감지 실패: {e}")

def cry_monitor_loop():
    print("[INFO] 울음 감지 모니터링 시작")
    while True:
        try:
            record_resample()
            predict_cry()
            time.sleep(1)
        except Exception as e:
            print(f"[ERROR] 울음 감지 루프 오류: {e}")
            time.sleep(1)

def process_frame():
    while True:
        try:
            frame = picam2.capture_array()
            
            # 미디어파이프 얼굴 감지
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(image)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            baby_direction = "확인 중..."
            if results.multi_face_landmarks:
                try:
                    face_landmarks = results.multi_face_landmarks[0]
                    
                    # 주요 랜드마크 좌표 추출
                    nose_tip = face_landmarks.landmark[1]  # 코 끝
                    left_eye = face_landmarks.landmark[33]  # 왼쪽 눈
                    right_eye = face_landmarks.landmark[263]  # 오른쪽 눈
                    
                    # 눈의 중심점 계산
                    center_x = (left_eye.x + right_eye.x) / 2
                    
                    # 코와 눈 중심의 상대적 위치 계산
                    dx = nose_tip.x - center_x
                    
                    threshold = 0.02
                    
                    # 방향 판단
                    if abs(dx) < threshold:
                        baby_direction = "정면 유지 중"
                    elif dx < 0:
                        baby_direction = "우측으로 움직임"
                    else:
                        baby_direction = "좌측으로 움직임"
                    
                    print(f"[DEBUG] 얼굴 방향 감지: {baby_direction} (dx: {dx:.3f})")
                    
                    # 디버깅을 위한 시각화
                    h, w, _ = frame.shape
                    nose_x = int(nose_tip.x * w)
                    nose_y = int(nose_tip.y * h)
                    center_x_pixel = int(center_x * w)
                    center_y = int((left_eye.y + right_eye.y) / 2 * h)
                    
                    # 눈 중심점 표시
                    cv2.circle(frame, (center_x_pixel, center_y), 5, (0, 255, 0), -1)
                    # 코 끝점 표시
                    cv2.circle(frame, (nose_x, nose_y), 5, (0, 0, 255), -1)
                    # 방향 텍스트 표시
                    cv2.putText(frame, f'Direction: {baby_direction}', (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                    
                except Exception as e:
                    print(f"[ERROR] 얼굴 방향 계산 오류: {e}")
                    baby_direction = "인식 오류"
            else:
                print("[DEBUG] 얼굴이 감지되지 않음")
                baby_direction = "인식 안됨"

            # 방향 정보 MQTT로 전송
            payload = json.dumps({
                "direction": baby_direction,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            mqtt_client.publish(MQTT_TOPIC_DIRECTION, payload)
            print(f"[DEBUG] 방향 정보 전송: {baby_direction}")

            # 프레임에 텍스트 추가
            pil_image = Image.fromarray(image)
            draw = ImageDraw.Draw(pil_image)
            nowDatetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            draw.text((10, 15), "raspiCam " + nowDatetime, font=font, fill=(255, 255, 255))
            frame = np.array(pil_image)

            # 프레임을 JPEG로 인코딩
            _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            
            # MQTT로 프레임 전송
            payload = json.dumps({
                "frame": base64.b64encode(jpeg).decode('utf-8'),
                "timestamp": nowDatetime
            })
            mqtt_client.publish(MQTT_TOPIC_FRAME, payload)
            
            time.sleep(0.1)  # 10 FPS
        except Exception as e:
            print(f"[ERROR] 프레임 처리 오류: {e}")
            time.sleep(1)

def read_temperature():
    if not ser:
        return
    while True:
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if "아기 체온:" in line:
                    temp = line.replace("아기 체온:", "").replace("\u00b0C", "").strip()
                    payload = json.dumps({"temperature": temp})
                    mqtt_client.publish(MQTT_TOPIC_TEMPERATURE, payload)
        except Exception as e:
            print("체온 센서 읽기 오류:", e)
            time.sleep(1)

def main():
    generate_qr_code(CRADLE_UUID, QR_CODE_FILENAME)
    register_agent()

    # 프레임 처리 스레드
    frame_thread = threading.Thread(target=process_frame)
    frame_thread.daemon = True
    frame_thread.start()

    # 울음 감지 스레드
    cry_thread = threading.Thread(target=cry_monitor_loop)
    cry_thread.daemon = True
    cry_thread.start()

    # 체온 센서 스레드
    if ser:
        temp_thread = threading.Thread(target=read_temperature)
        temp_thread.daemon = True
        temp_thread.start()

    while True:
        time.sleep(1)

if __name__ == '__main__':
    main()