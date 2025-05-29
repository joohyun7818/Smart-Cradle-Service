from flask import Flask, render_template, request, redirect, session, url_for, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
import os
import uuid
import datetime
import cv2
import numpy as np
import time
import threading
import paho.mqtt.client as mqtt
import json

app = Flask(__name__)

# MQTT 설정 
MQTT_BROKER_HOST = "your_ec2_public_ip"  # 서버의 IP 주소
MQTT_BROKER_PORT = 1883
MQTT_TOPIC_TEMPERATURE_PREFIX = "cradle/temperature/"  # 요람 UUID를 포함하는 토픽 접두사

# 에이전트별 마지막 프레임을 저장하는 딕셔너리 (UUID 기반으로 관리)
agent_last_frame = {}
frame_lock = threading.Lock()

# 에이전트별 최신 센서 값을 저장하는 딕셔너리
agent_sensor_data = {}
sensor_data_lock = threading.Lock()

# MQTT 클라이언트 설정
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT Broker 연결 성공 (서버)")
        client.subscribe(f"{MQTT_TOPIC_TEMPERATURE_PREFIX}+")  # 모든 온도 관련 토픽 구독
    else:
        print(f"MQTT Broker 연결 실패 (서버), rc={rc}")

def on_message(client, userdata, msg):
    if msg.topic.startswith(MQTT_TOPIC_TEMPERATURE_PREFIX):
        try:
            uuid = msg.topic[len(MQTT_TOPIC_TEMPERATURE_PREFIX):]  # 토픽에서 UUID 추출
            payload = json.loads(msg.payload.decode())
            temperature = payload.get('temperature')
            with sensor_data_lock:
                agent_sensor_data[uuid] = {'temperature': temperature}
            print(f"서버 수신 온도 ({uuid}): {temperature}")
        except Exception as e:
            print(f"MQTT 메시지 처리 오류 (서버): {e}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

try:
    mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
    mqtt_client.loop_start()  # 백그라운드 스레드 시작
except Exception as e:
    print(f"MQTT 연결 오류 (서버): {e}")

app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/smart_cradle' # 실제 비밀번호로 변경
db = SQLAlchemy(app)

# 사용자 모델
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    registered_agents = db.relationship('Agent', backref='user', lazy=True)

# 등록된 에이전트 모델 (DB 테이블 구조와 일치)
class Agent(db.Model):
    __tablename__ = 'agents'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(255), unique=True, nullable=False)
    ip = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

@app.route('/')
def dashboard_page():
    if not session.get('user_id'):
        return redirect('/login')
    user = User.query.get(session['user_id'])
    agents = user.registered_agents if user else []
    return render_template('dashboard.html', agents=agents, agent_sensor_data=agent_sensor_data)

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('signup.html', registration_error='이미 사용 중인 아이디입니다.')
        new_user = User(username=username, password=password) 
        db.session.add(new_user)
        db.session.commit()
        return render_template('signup.html', registration_success='회원가입이 완료되었습니다. 로그인해주세요.')
    return render_template('signup.html')

@app.route('/check_username/<username>')
def check_username(username):
    existing_user = User.query.filter_by(username=username).first()
    return jsonify({'exists': bool(existing_user)})

@app.route('/login', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password: 
            session['user_id'] = user.id
            return redirect('/')
        else:
            return render_template('login.html', error='아이디 또는 비밀번호가 틀렸습니다.')
    return render_template('login.html')

@app.route('/logout')
def logout_user():
    session.pop('user_id', None)
    return redirect('/login')

@app.route('/register_agent', methods=['POST'])
def register_agent():
    data = request.get_json()
    agent_uuid = data.get('uuid')
    agent_ip = data.get('ip')
    if agent_uuid and agent_ip:
        existing_agent = Agent.query.filter_by(uuid=agent_uuid).first()
        if existing_agent:
            # UUID가 존재하면 IP 주소 업데이트
            if existing_agent.ip != agent_ip:
                existing_agent.ip = agent_ip
                db.session.commit()
                print(f"에이전트 IP 업데이트: UUID={agent_uuid}, Old IP={existing_agent.ip}, New IP={agent_ip}")
                return jsonify({"status": "success", "message": "에이전트 IP 업데이트 성공"})
            else:
                print(f"기존 에이전트 정보 재보고 (IP 동일): UUID={agent_uuid}, IP={agent_ip}")
                return jsonify({"status": "info", "message": "이미 등록된 에이전트 정보입니다. IP 동일."})
        else:
            # UUID가 없으면 새로 등록
            new_agent = Agent(uuid=agent_uuid, ip=agent_ip)
            db.session.add(new_agent)
            db.session.commit()
            print(f"새로운 에이전트 등록: UUID={agent_uuid}, IP={agent_ip}")
            return jsonify({"status": "success", "message": "에이전트 등록 성공"})
    return jsonify({"status": "error", "message": "UUID 또는 IP 주소가 제공되지 않았습니다."})


@app.route('/register_cradle', methods=['GET', 'POST'])
def register_cradle():
    if not session.get('user_id'):
        return redirect('/login')

    if request.method == 'POST':
        cradle_uuid = request.form['cradle_uuid']
        user_id = session['user_id']

        existing_agent = Agent.query.filter_by(uuid=cradle_uuid).first()
        if existing_agent:
            # 이미 등록된 에이전트를 현재 사용자에 연결
            existing_agent.user_id = user_id
            db.session.commit()
            return redirect('/') # 등록 성공 후 대시보드로 리다이렉트
        else:
            return render_template('register_cradle.html', error="등록되지 않은 UUID입니다.")

    return render_template('register_cradle.html')

def generate_stream(uuid):
    while True:
        with frame_lock:
            frame = agent_last_frame.get(uuid)
            if frame is not None:
                with sensor_data_lock:
                    sensor_data = agent_sensor_data.get(uuid)
                    if sensor_data and 'temperature' in sensor_data:
                        temperature = sensor_data['temperature']
                        text = f"체온: {temperature}"
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        font_scale = 1
                        font_thickness = 2
                        text_color = (0, 255, 0)
                        text_size = cv2.getTextSize(text, font, font_scale, font_thickness)[0]
                        text_x = 10
                        text_y = 50
                        cv2.putText(frame, text, (text_x, text_y), font, font_scale, text_color, font_thickness, cv2.LINE_AA)

                _, jpeg = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        time.sleep(0.1)

@app.route('/stream/<uuid>')
def video_feed(uuid):
    return Response(generate_stream(uuid), mimetype='multipart/x-mixed-replace; boundary=frame')

# 에이전트 프레임 수신 엔드포인트
@app.route('/upload_frame/<uuid>', methods=['POST'])
def upload_frame(uuid):
    if 'frame' not in request.files:
        return "No file part", 400
    file = request.files['frame']
    if file.filename == '':
        return "No selected file", 400
    if file:
        nparr = np.frombuffer(file.read(), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        with frame_lock:
            agent_last_frame[uuid] = frame
        return "Frame uploaded successfully", 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=8888)