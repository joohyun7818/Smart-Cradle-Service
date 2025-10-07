from flask import Flask, render_template, request, redirect, session, url_for, jsonify, Response, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
import datetime
import cv2
import numpy as np
import time
import threading
import paho.mqtt.client as mqtt
import json
import base64
from io import BytesIO

app = Flask(__name__)

# CORS 설정 - 모바일 앱에서 API 호출 허용
CORS(app, supports_credentials=True)

# MQTT 설정: 컨테이너 환경에서는 서비스명으로 접근 가능합니다.
# docker-compose에서 설정한 값이 있으면 사용하고, 없으면 'mosquitto'를 기본값으로 사용합니다.
MQTT_BROKER_HOST = os.getenv('MQTT_BROKER_HOST', 'mosquitto')
MQTT_BROKER_PORT = int(os.getenv('MQTT_BROKER_PORT', '1883'))

# 에이전트별 마지막 프레임을 저장하는 딕셔너리
agent_last_frame = {}
frame_lock = threading.Lock()

# 에이전트별 상태 및 알림 관련 변수
agent_face_status = {}  # 에이전트별 얼굴 방향 상태 ('정면 유지 중', '좌측으로 움직임', '우측으로 움직임', '인식 안됨')
agent_last_normal_face = {}  # 에이전트별 마지막 정상 얼굴 인식 시간 ('정면 유지 중'일 때)
agent_temperature_status = {}  # 에이전트별 온도 상태
agent_last_direction_time = {}  # 에이전트별 마지막 방향 데이터 수신 시간
agent_crying_start_time = {}  # 에이전트별 울음 시작 시간

# 에이전트 방향 데이터 기반 알림 체크 함수
def is_face_position_normal(direction):
    """
    에이전트에서 전송된 방향 데이터를 기반으로 정상 상태인지 판단
    Args:
        direction: '정면 유지 중', '좌측으로 움직임', '우측으로 움직임', '인식 안됨', '확인 중...', '인식 오류'
    Returns:
        bool: 정상 상태(정면 유지 중)면 True, 비정상이면 False
    """
    return direction == "정면 유지 중"

# 웹 푸시 알림 전송 함수
def send_push_notification(user_id, title, message, agent_uuid=None):
    """
    웹 푸시 알림을 전송합니다.
    """
    try:
        with app.app_context():
            alert_settings = AlertSettings.query.filter_by(user_id=user_id).first()
            if not alert_settings or not alert_settings.push_notifications_enabled:
                return False
                
            if not alert_settings.push_endpoint:
                print(f"사용자 {user_id}의 푸시 구독 정보가 없습니다.")
                return False
                
            # 실제 웹 푸시 전송 로직은 여기에 구현
            # 현재는 콘솔에 로그만 출력
            print(f"[푸시 알림] 사용자 {user_id}: {title} - {message}")
            return True
            
    except Exception as e:
        print(f"푸시 알림 전송 오류: {e}")
        return False

# 알림 발생 시 데이터 저장을 위한 전역 변수
alert_recording = {}  # {agent_uuid: {'alert_log_id': id, 'start_time': datetime}}

# 알림 체크 및 전송 함수 (에이전트 데이터 기반)
def check_and_send_alerts(agent_uuid, temperature=None, direction=None, crying=None):
    """
    온도, 방향, 울음 데이터를 기반으로 알림을 체크하고 전송합니다.
    """
    try:
        with app.app_context():
            agent = Agent.query.filter_by(uuid=agent_uuid).first()
            if not agent:
                return None
                
            alert_settings = AlertSettings.query.filter_by(agent_id=agent.id).first()
            if not alert_settings:
                return None
                
            current_time = datetime.datetime.utcnow()
            alerts_to_send = []
            
            # 1. 고온 체크
            if temperature is not None:
                try:
                    temp_value = float(temperature)
                    if temp_value > alert_settings.max_temperature:
                        # 중복 알림 방지: 최근 5분 내에 같은 알림이 있는지 체크
                        recent_temp_alert = AlertLog.query.filter_by(
                            agent_id=agent.id,
                            alert_type='high_temperature',
                            resolved=False
                        ).filter(
                            AlertLog.created_at > current_time - datetime.timedelta(minutes=5)
                        ).first()
                        
                        if not recent_temp_alert:
                            alert_message = f"⚠️ 아기의 체온이 {temp_value:.1f}°C로 높습니다!"
                            alerts_to_send.append({
                                'type': 'high_temperature',
                                'title': '체온 경고',
                                'message': alert_message,
                                'temperature': temp_value,
                                'face_detected': True
                            })
                except ValueError:
                    print(f"온도 데이터 변환 오류: {temperature}")
            
            # 2. 얼굴 방향 상태 체크 (에이전트 데이터 기반)
            if direction is not None:
                # 방향 데이터 수신 시간 업데이트
                agent_last_direction_time[agent_uuid] = current_time
                
                # 정상 상태 체크 및 시간 업데이트
                if is_face_position_normal(direction):
                    # 정면을 보고 있으면 정상 시간 업데이트
                    agent_last_normal_face[agent_uuid] = current_time
                    agent_face_status[agent_uuid] = direction
                else:
                    # 정면이 아니거나 인식되지 않는 경우
                    agent_face_status[agent_uuid] = direction
                    
                    # 마지막 정상 상태 시간 확인
                    if agent_uuid not in agent_last_normal_face:
                        agent_last_normal_face[agent_uuid] = current_time
                    
                    last_normal = agent_last_normal_face.get(agent_uuid, current_time)
                    time_diff = (current_time - last_normal).total_seconds()
                    
                    # 설정된 시간 이상 비정상 상태가 지속되면 알림
                    if time_diff > alert_settings.abnormal_position_timeout:
                        # 중복 알림 방지
                        recent_face_alert = AlertLog.query.filter_by(
                            agent_id=agent.id,
                            alert_type='abnormal_position',
                            resolved=False
                        ).filter(
                            AlertLog.created_at > current_time - datetime.timedelta(minutes=2)
                        ).first()
                        
                        if not recent_face_alert:
                            if direction == "인식 안됨" or direction == "인식 오류":
                                alert_message = f"⚠️ 아기 얼굴이 {int(time_diff)}초 동안 인식되지 않았습니다!"
                                alert_type = 'face_not_detected'
                                title = '얼굴 인식 경고'
                            else:
                                alert_message = f"⚠️ 아기가 {int(time_diff)}초 동안 {direction} 상태입니다!"
                                alert_type = 'abnormal_position'
                                title = '자세 경고'
                            
                            alerts_to_send.append({
                                'type': alert_type,
                                'title': title,
                                'message': alert_message,
                                'temperature': temperature,
                                'face_detected': direction not in ["인식 안됨", "인식 오류"]
                            })
            
            # 3. 울음 상태 체크
            if crying is not None:
                if crying == "Crying":
                    # 울음 시작 시간 기록
                    if agent_uuid not in agent_crying_start_time:
                        agent_crying_start_time[agent_uuid] = current_time
                    
                    # 울음 지속 시간 계산
                    crying_duration = (current_time - agent_crying_start_time[agent_uuid]).total_seconds()
                    
                    # 설정된 시간 이상 울음이 지속되면 알림
                    if crying_duration >= alert_settings.crying_duration_threshold:
                        # 중복 알림 방지 (최근 2분 이내)
                        recent_crying_alert = AlertLog.query.filter_by(
                            agent_id=agent.id,
                            alert_type='crying',
                            resolved=False
                        ).filter(
                            AlertLog.created_at > current_time - datetime.timedelta(minutes=2)
                        ).first()
                        
                        if not recent_crying_alert:
                            alert_message = f"😢 아기가 {int(crying_duration)}초 동안 울고 있습니다!"
                            alerts_to_send.append({
                                'type': 'crying',
                                'title': '울음 감지',
                                'message': alert_message,
                                'temperature': temperature,
                                'face_detected': None
                            })
                else:
                    # 울음이 멈추면 시작 시간 초기화
                    if agent_uuid in agent_crying_start_time:
                        del agent_crying_start_time[agent_uuid]
            
            # 4. 알림 전송 및 로그 저장
            created_alert_log_id = None
            for alert in alerts_to_send:
                # 알림 로그 저장
                alert_log = AlertLog(
                    user_id=agent.user_id,
                    agent_id=agent.id,
                    alert_type=alert['type'],
                    alert_message=alert['message'],
                    temperature=alert.get('temperature'),
                    face_detected=alert.get('face_detected')
                )
                db.session.add(alert_log)
                db.session.flush()  # ID를 얻기 위해 flush
                
                created_alert_log_id = alert_log.id
                
                # 알림 녹화 시작 (60초 동안)
                alert_recording[agent_uuid] = {
                    'alert_log_id': created_alert_log_id,
                    'start_time': current_time
                }
                print(f"[ALERT] 알림 녹화 시작: Agent {agent_uuid}, AlertLog ID {created_alert_log_id}")
                
                # 푸시 알림 전송
                if send_push_notification(agent.user_id, alert['title'], alert['message'], agent_uuid):
                    alert_log.notification_sent = True
                
                db.session.commit()
                
            return created_alert_log_id
                
    except Exception as e:
        print(f"알림 체크 오류: {e}")
        if 'db' in locals():
            db.session.rollback()
        return None

# MQTT 클라이언트 설정
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT Broker 연결 성공")
        # 모든 에이전트의 토픽 구독
        client.subscribe("cradle/+/temperature")
        client.subscribe("cradle/+/crying")
        client.subscribe("cradle/+/direction")
        client.subscribe("cradle/+/frame")  # 프레임 토픽 추가
    else:
        print(f"MQTT Broker 연결 실패, rc={rc}")

def on_message(client, userdata, msg):
    try:
        # 토픽에서 UUID 추출 (변수명 변경: uuid 모듈과 충돌 방지)
        agent_uuid = msg.topic.split('/')[1]
        payload = json.loads(msg.payload.decode())
        
        with app.app_context():
            agent = Agent.query.filter_by(uuid=agent_uuid).first()
            if not agent:
                print(f"경고: UUID '{agent_uuid}'에 해당하는 에이전트를 찾을 수 없습니다. 메시지를 무시합니다.")
                return

            current_time = datetime.datetime.utcnow()
            alert_log_id = None
            
            # 알림 녹화 중인지 확인 (60초 이내)
            if agent_uuid in alert_recording:
                recording = alert_recording[agent_uuid]
                time_since_alert = (current_time - recording['start_time']).total_seconds()
                
                if time_since_alert <= 60:  # 60초 동안 녹화
                    alert_log_id = recording['alert_log_id']
                else:
                    # 60초 지나면 녹화 종료
                    del alert_recording[agent_uuid]
                    print(f"[ALERT] 알림 녹화 종료: Agent {agent_uuid}")

            temperature = None
            face_detected = None

            if 'temperature' in msg.topic:
                temperature = payload.get('temperature')
                
                # 센서 데이터는 항상 DB에 저장
                new_sensor_data = SensorData(
                    agent_id=agent.id,
                    alert_log_id=alert_log_id,  # 알림 녹화 중이면 연결, 아니면 None
                    temperature=temperature
                )
                db.session.add(new_sensor_data)
                db.session.commit()
                
                # 온도 알림 체크 (알림 발생 시 영상 녹화 시작)
                if temperature is not None:
                    check_and_send_alerts(agent_uuid, temperature=temperature)

            elif 'crying' in msg.topic:
                crying_status = payload.get('status')
                
                # 센서 데이터는 항상 DB에 저장
                new_sensor_data = SensorData(
                    agent_id=agent.id,
                    alert_log_id=alert_log_id,  # 알림 녹화 중이면 연결, 아니면 None
                    crying=crying_status
                )
                db.session.add(new_sensor_data)
                db.session.commit()
                
                # 울음 알림 체크 (알림 발생 시 영상 녹화 시작)
                if crying_status is not None:
                    check_and_send_alerts(agent_uuid, crying=crying_status)

            elif 'direction' in msg.topic:
                direction = payload.get('direction')
                
                # 센서 데이터는 항상 DB에 저장
                new_sensor_data = SensorData(
                    agent_id=agent.id,
                    alert_log_id=alert_log_id,  # 알림 녹화 중이면 연결, 아니면 None
                    direction=direction
                )
                db.session.add(new_sensor_data)
                db.session.commit()
                
                # 방향 데이터 기반 알림 체크 (알림 발생 시 영상 녹화 시작)
                if direction is not None:
                    check_and_send_alerts(agent_uuid, direction=direction)

            elif 'frame' in msg.topic:
                frame_data_b64 = payload.get('frame')
                if frame_data_b64:
                    frame_data = base64.b64decode(frame_data_b64)
                    
                    # 알림 녹화 중일 때만 DB 저장
                    if alert_log_id:
                        new_frame = VideoFrame(
                            agent_id=agent.id,
                            alert_log_id=alert_log_id,
                            frame=frame_data
                        )
                        db.session.add(new_frame)
                        db.session.commit()
                        print(f"[ALERT] 프레임 저장 (AlertLog {alert_log_id})")

                    # 메모리 내 마지막 프레임은 항상 업데이트 (실시간 스트리밍용)
                    nparr = np.frombuffer(frame_data, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    with frame_lock:
                        agent_last_frame[agent_uuid] = frame

    except Exception as e:
        print(f"MQTT 메시지 처리 및 DB 저장 오류: {e}")
        if 'db' in locals():
            db.session.rollback()


mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message


def connect_mqtt_with_retry(client, host, port, max_retries=None):
    """Try to connect to MQTT broker with exponential backoff.
    If max_retries is None, retry indefinitely."""
    attempt = 0
    wait = 1
    while True:
        try:
            client.connect(host, port, 60)
            client.loop_start()
            print(f"MQTT 연결 시도 성공: {host}:{port}")
            return True
        except Exception as e:
            attempt += 1
            print(f"MQTT 연결 오류 (attempt {attempt}): {e}")
            if max_retries is not None and attempt >= max_retries:
                print("최대 재시도 횟수 초과, MQTT 연결 포기")
                return False
            time.sleep(wait)
            wait = min(wait * 2, 30)  # 최대 30초 대기


# 시작 시 백그라운드에서 MQTT 연결 시도
threading.Thread(target=connect_mqtt_with_retry, args=(mqtt_client, MQTT_BROKER_HOST, MQTT_BROKER_PORT, None), daemon=True).start()

# SECURITY: prefer reading SECRET_KEY from environment; fall back to a generated key for local dev
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or os.urandom(24)

# Database configuration: read full SQLALCHEMY_DATABASE_URI from env if provided,
# otherwise construct one from individual MYSQL_* env vars for compatibility with docker-compose
sql_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
if not sql_uri:
    db_user = os.getenv('MYSQL_USER', 'sc_user')
    db_pass = os.getenv('MYSQL_PASSWORD', 'SC_password_12!45')
    db_host = os.getenv('MYSQL_HOST', '34.121.73.128')
    db_port = os.getenv('MYSQL_PORT', '3306')
    db_name = os.getenv('MYSQL_DATABASE', 'smartcradle')
    sql_uri = f'mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}'

print(f"DEBUG: DB URI: {sql_uri}")  # 디버깅용 출력
app.config['SQLALCHEMY_DATABASE_URI'] = sql_uri

# 임시 DB 연결 테스트
try:
    import pymysql
    conn = pymysql.connect(
        host=db_host,
        port=int(db_port),
        user=db_user,
        password=db_pass,
        database=db_name
    )
    conn.close()
    print("DEBUG: Direct pymysql connection successful")
except Exception as e:
    print(f"DEBUG: Direct pymysql connection failed: {e}")
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # 해싱된 비밀번호를 저장하기 위해 255로 확장
    registered_agents = db.relationship('Agent', backref='user', lazy=True)

class Agent(db.Model):
    __tablename__ = 'agents'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(255), unique=True, nullable=False)
    ip = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    sensor_data = db.relationship('SensorData', backref='agent', lazy=True)
    video_frames = db.relationship('VideoFrame', backref='agent', lazy=True)

class SensorData(db.Model):
    __tablename__ = 'sensor_data'
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False)
    alert_log_id = db.Column(db.Integer, db.ForeignKey('alert_logs.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    temperature = db.Column(db.Float)
    crying = db.Column(db.String(50))
    direction = db.Column(db.String(50))

class VideoFrame(db.Model):
    __tablename__ = 'video_frames'
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False)
    alert_log_id = db.Column(db.Integer, db.ForeignKey('alert_logs.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    frame = db.Column(db.LargeBinary)

class AlertSettings(db.Model):
    __tablename__ = 'alert_settings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False)
    max_temperature = db.Column(db.Float, default=38.0)  # 최대 온도 (섭씨)
    abnormal_position_timeout = db.Column(db.Integer, default=30)  # 비정상 자세 허용 시간 (초)
    crying_duration_threshold = db.Column(db.Integer, default=30)  # 울음 알림 임계값 (초)
    push_notifications_enabled = db.Column(db.Boolean, default=True)
    email_notifications_enabled = db.Column(db.Boolean, default=False)
    push_endpoint = db.Column(db.Text)  # 웹 푸시 엔드포인트
    push_p256dh = db.Column(db.Text)    # 웹 푸시 공개키
    push_auth = db.Column(db.Text)      # 웹 푸시 인증키
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class AlertLog(db.Model):
    __tablename__ = 'alert_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # 'high_temperature', 'face_not_detected'
    alert_message = db.Column(db.Text, nullable=False)
    temperature = db.Column(db.Float)
    face_detected = db.Column(db.Boolean)
    notification_sent = db.Column(db.Boolean, default=False)
    resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    resolved_at = db.Column(db.DateTime)


# Ensure tables are created when the WSGI server (gunicorn) imports this module.
# Earlier `db.create_all()` was inside `if __name__ == '__main__'` which doesn't run under gunicorn.
with app.app_context():
    # Wait for DB to be ready. This avoids a race where the web container
    # starts and tries to create tables before the MySQL server accepts
    # connections. We attempt to connect a few times with exponential backoff.
    def wait_for_db(max_attempts=20, initial_delay=1):
        attempt = 0
        delay = initial_delay
        from sqlalchemy import text
        while True:
            try:
                # simple lightweight query to verify connection
                db.session.execute(text('SELECT 1'))
                print("DB 연결 확인됨")
                return True
            except Exception as e:
                attempt += 1
                print(f"DB 연결 대기 중... (시도 {attempt}): {e}")
                if attempt >= max_attempts:
                    print("DB 연결을 위한 최대 재시도 도달, 계속 진행합니다 (테이블 생성 시 예외가 발생할 수 있음)")
                    return False
                time.sleep(delay)
                delay = min(delay * 2, 10)

    try:
        wait_for_db()
        db.create_all()
        print("DB 테이블 생성/확인 완료")
    except Exception as e:
        print(f"DB 테이블 생성 중 오류: {e}")

@app.route('/')
def index_page():
    if not session.get('user_id'):
        return render_template('welcome.html')
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard_page():
    if not session.get('user_id'):
        return redirect('/login')
    user = User.query.get(session['user_id'])
    
    # 선택된 요람만 표시
    selected_uuid = session.get('selected_cradle_uuid')
    agents = []
    
    if selected_uuid:
        selected_agent = Agent.query.filter_by(uuid=selected_uuid, user_id=user.id).first()
        if selected_agent:
            agents = [selected_agent]
    
    # 선택된 요람이 없으면 첫 번째 요람 자동 선택
    if not agents and user.registered_agents:
        agents = [user.registered_agents[0]]
        session['selected_cradle_uuid'] = agents[0].uuid
    
    # 각 에이전트의 최신 센서 데이터 조회
    agent_sensor_data = {}
    for agent in agents:
        latest_data = SensorData.query.filter_by(agent_id=agent.id).order_by(SensorData.timestamp.desc()).first()
        if latest_data:
            agent_sensor_data[agent.uuid] = latest_data
    
    return render_template('dashboard.html', agents=agents, agent_sensor_data=agent_sensor_data, selected_agent=agents[0] if agents else None)

@app.route('/history')
def history_page():
    if not session.get('user_id'):
        return redirect('/login')
    user = User.query.get(session['user_id'])
    agents = user.registered_agents if user else []
    
    # 선택된 요람 정보 전달
    selected_uuid = session.get('selected_cradle_uuid')
    selected_agent = None
    if selected_uuid:
        selected_agent = Agent.query.filter_by(uuid=selected_uuid, user_id=user.id).first()
    
    # 선택된 요람이 없으면 첫 번째 요람 자동 선택
    if not selected_agent and agents:
        selected_agent = agents[0]
        session['selected_cradle_uuid'] = selected_agent.uuid
    
    return render_template('history.html', agents=agents, selected_agent=selected_agent)

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        # JSON API 요청인지 확인 (모바일 앱)
        if request.is_json or request.content_type == 'application/json':
            try:
                data = request.get_json()
                username = data.get('username')
                password = data.get('password')
            except:
                # FormData로 전송된 경우
                username = request.form.get('username')
                password = request.form.get('password')
        else:
            # 웹 폼 요청
            username = request.form.get('username')
            password = request.form.get('password')
        
        if not username or not password:
            if request.is_json or request.content_type == 'application/json':
                return jsonify({'success': False, 'message': '아이디와 비밀번호를 입력해주세요.'}), 400
            return render_template('signup.html', registration_error='아이디와 비밀번호를 입력해주세요.')
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            if request.is_json or request.content_type == 'application/json':
                return jsonify({'success': False, 'message': '이미 사용 중인 아이디입니다.'}), 400
            return render_template('signup.html', registration_error='이미 사용 중인 아이디입니다.')
        
        # 비밀번호 해싱
        password_hash = generate_password_hash(password)
        new_user = User(username=username, password=password_hash)
        db.session.add(new_user)
        db.session.commit()
        
        if request.is_json or request.content_type == 'application/json':
            return jsonify({'success': True, 'message': '회원가입이 완료되었습니다.'}), 201
        return render_template('signup.html', registration_success='회원가입이 완료되었습니다. 로그인해주세요.')
    
    return render_template('signup.html')

@app.route('/check_username/<username>')
def check_username(username):
    """실시간 아이디 중복 체크 API"""
    existing_user = User.query.filter_by(username=username).first()
    return jsonify({'exists': existing_user is not None})

@app.route('/login', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        # JSON API 요청인지 확인 (모바일 앱)
        is_api_request = request.is_json or request.content_type == 'application/json'
        
        try:
            if is_api_request:
                data = request.get_json()
                username = data.get('username')
                password = data.get('password')
            else:
                # FormData로 전송된 경우도 처리
                username = request.form.get('username')
                password = request.form.get('password')
        except:
            username = request.form.get('username')
            password = request.form.get('password')
        
        if not username or not password:
            if is_api_request:
                return jsonify({'success': False, 'message': '아이디와 비밀번호를 입력해주세요.'}), 400
            return render_template('login.html', error='아이디와 비밀번호를 입력해주세요.')
        
        user = User.query.filter_by(username=username).first()
        # 비밀번호 해시 검증
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            
            # API 요청인 경우 JSON 응답
            if is_api_request:
                return jsonify({
                    'success': True,
                    'message': '로그인 성공',
                    'user': {
                        'id': user.id,
                        'username': user.username
                    }
                }), 200
            
            # 웹 요청인 경우 리다이렉트
            return redirect('/')
        else:
            if is_api_request:
                return jsonify({'success': False, 'message': '아이디 또는 비밀번호가 틀렸습니다.'}), 401
            return render_template('login.html', error='아이디 또는 비밀번호가 틀렸습니다.')
    
    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout_user():
    session.pop('user_id', None)
    
    # API 요청인 경우 JSON 응답
    if request.is_json or request.method == 'POST':
        return jsonify({'success': True, 'message': '로그아웃 되었습니다.'}), 200
    
    return redirect('/login')

@app.route('/register_agent', methods=['POST'])
def register_agent():
    try:
        data = request.get_json()
        agent_uuid = data.get('uuid')
        agent_ip = data.get('ip')
        if agent_uuid and agent_ip:
            existing_agent = Agent.query.filter_by(uuid=agent_uuid).first()
            if existing_agent:
                if existing_agent.ip != agent_ip:
                    existing_agent.ip = agent_ip
                    db.session.commit()
                return jsonify({"status": "success", "message": "에이전트 IP 업데이트 성공"})
            else:
                new_agent = Agent(uuid=agent_uuid, ip=agent_ip)
                db.session.add(new_agent)
                db.session.commit()
                return jsonify({"status": "success", "message": "에이전트 등록 성공"})
        return jsonify({"status": "error", "message": "UUID 또는 IP 주소가 제공되지 않았습니다."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"등록 중 오류 발생: {str(e)}"}), 500

@app.route('/register_cradle', methods=['GET', 'POST'])
def register_cradle():
    if not session.get('user_id'):
        if request.is_json:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        return redirect('/login')

    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        # JSON API 요청인지 확인 (모바일 앱)
        is_api_request = request.is_json or request.content_type == 'application/json'
        
        try:
            if is_api_request:
                data = request.get_json()
                cradle_uuid = data.get('cradle_uuid')
            else:
                cradle_uuid = request.form.get('cradle_uuid')
            
            if not cradle_uuid:
                if is_api_request:
                    return jsonify({'success': False, 'message': '요람 UUID를 입력해주세요.'}), 400
                agents = user.registered_agents if user else []
                selected_agent = Agent.query.filter_by(uuid=session.get('selected_cradle_uuid')).first() if session.get('selected_cradle_uuid') else None
                return render_template('register_cradle.html', agents=agents, selected_agent=selected_agent, error='요람 UUID를 입력해주세요.')
            
            user_id = session['user_id']

            existing_agent = Agent.query.filter_by(uuid=cradle_uuid).first()
            if existing_agent:
                existing_agent.user_id = user_id
                db.session.commit()
                
                # 첫 요람이면 자동 선택
                if not session.get('selected_cradle_uuid'):
                    session['selected_cradle_uuid'] = existing_agent.uuid
                
                if is_api_request:
                    return jsonify({
                        'success': True,
                        'message': '요람이 등록되었습니다.',
                        'agent': {
                            'id': existing_agent.id,
                            'uuid': existing_agent.uuid,
                            'ip': existing_agent.ip,
                            'created_at': existing_agent.created_at.isoformat(),
                            'updated_at': existing_agent.updated_at.isoformat()
                        }
                    }), 200
                
                agents = user.registered_agents if user else []
                selected_agent = Agent.query.filter_by(uuid=session.get('selected_cradle_uuid')).first()
                return render_template('register_cradle.html', agents=agents, selected_agent=selected_agent, success='요람이 등록되었습니다.')
            else:
                if is_api_request:
                    return jsonify({'success': False, 'message': '등록되지 않은 UUID입니다. 요람 기기를 먼저 서버에 연결해주세요.'}), 404
                agents = user.registered_agents if user else []
                selected_agent = Agent.query.filter_by(uuid=session.get('selected_cradle_uuid')).first()
                return render_template('register_cradle.html', agents=agents, selected_agent=selected_agent, error="등록되지 않은 UUID입니다.")
        except Exception as e:
            db.session.rollback()
            if is_api_request:
                return jsonify({'success': False, 'message': f'등록 중 오류가 발생했습니다: {str(e)}'}), 500
            agents = user.registered_agents if user else []
            selected_agent = Agent.query.filter_by(uuid=session.get('selected_cradle_uuid')).first()
            return render_template('register_cradle.html', agents=agents, selected_agent=selected_agent, error=f"등록 중 오류가 발생했습니다: {str(e)}")

    # GET 요청
    agents = user.registered_agents if user else []
    selected_agent = Agent.query.filter_by(uuid=session.get('selected_cradle_uuid')).first() if session.get('selected_cradle_uuid') else None
    
    # 요람이 있는데 선택된 게 없으면 첫 번째 자동 선택
    if agents and not selected_agent:
        session['selected_cradle_uuid'] = agents[0].uuid
        selected_agent = agents[0]
    
    return render_template('register_cradle.html', agents=agents, selected_agent=selected_agent)

# 요람 선택 API
@app.route('/select_cradle', methods=['POST'])
def select_cradle():
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        uuid = data.get('uuid')
        
        if not uuid:
            return jsonify({'success': False, 'message': 'UUID가 필요합니다.'}), 400
        
        user = User.query.get(session['user_id'])
        agent = Agent.query.filter_by(uuid=uuid, user_id=user.id).first()
        
        if not agent:
            return jsonify({'success': False, 'message': '등록되지 않은 요람입니다.'}), 404
        
        session['selected_cradle_uuid'] = uuid
        return jsonify({'success': True, 'message': '요람이 선택되었습니다.'}), 200
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 요람 삭제 API
@app.route('/delete_cradle', methods=['POST'])
def delete_cradle():
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        uuid = data.get('uuid')
        
        if not uuid:
            return jsonify({'success': False, 'message': 'UUID가 필요합니다.'}), 400
        
        user = User.query.get(session['user_id'])
        agent = Agent.query.filter_by(uuid=uuid, user_id=user.id).first()
        
        if not agent:
            return jsonify({'success': False, 'message': '등록되지 않은 요람입니다.'}), 404
        
        # 선택된 요람이면 선택 해제
        if session.get('selected_cradle_uuid') == uuid:
            session.pop('selected_cradle_uuid', None)
            # 다른 요람이 있으면 첫 번째 것 자동 선택
            remaining_agents = Agent.query.filter_by(user_id=user.id).filter(Agent.uuid != uuid).all()
            if remaining_agents:
                session['selected_cradle_uuid'] = remaining_agents[0].uuid
        
        # 요람과 관련된 모든 데이터 삭제
        SensorData.query.filter_by(agent_id=agent.id).delete()
        VideoFrame.query.filter_by(agent_id=agent.id).delete()
        AlertLog.query.filter_by(agent_id=agent.id).delete()
        AlertSettings.query.filter_by(agent_id=agent.id).delete()
        
        # 요람 삭제 (실제로는 user_id만 해제)
        agent.user_id = None
        db.session.commit()
        
        return jsonify({'success': True, 'message': '요람이 삭제되었습니다.'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# 요람 목록 조회 API
@app.route('/api/agents', methods=['GET'])
def get_agents():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        agents = Agent.query.filter_by(user_id=session['user_id']).all()
        result = []
        for agent in agents:
            result.append({
                'id': agent.id,
                'uuid': agent.uuid,
                'ip': agent.ip,
                'created_at': agent.created_at.isoformat(),
                'updated_at': agent.updated_at.isoformat()
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_stream(uuid):
    while True:
        with frame_lock:
            frame = agent_last_frame.get(uuid)
            if frame is not None:
                # 프레임 크기 조정 (선택사항)
                frame = cv2.resize(frame, (640, 480))
                _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        time.sleep(0.1)  # 10 FPS

@app.route('/stream/<uuid>')
def video_feed(uuid):
    return Response(generate_stream(uuid), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/control_motor/<uuid>', methods=['POST'])
def control_motor(uuid):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '요청 데이터가 없습니다.'}), 400
            
        action = data.get('action')
        
        if action not in ['start', 'stop']:
            return jsonify({'success': False, 'message': '잘못된 액션입니다.'}), 400
        
        # 에이전트 존재 여부 확인
        agent = Agent.query.filter_by(uuid=uuid).first()
        if not agent:
            return jsonify({'success': False, 'message': '에이전트를 찾을 수 없습니다.'}), 404
            
        topic = f"cradle/{uuid}/servo"
        payload = json.dumps({'action': action})
        result = mqtt_client.publish(topic, payload)
        
        if result.rc != 0:
            return jsonify({'success': False, 'message': 'MQTT 메시지 전송 실패'}), 500
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"모터 제어 오류: {e}")
        return jsonify({'success': False, 'message': f'오류 발생: {str(e)}'}), 500

@app.route('/get_sensor_data/<uuid>')
def get_sensor_data(uuid):
    try:
        agent = Agent.query.filter_by(uuid=uuid).first()
        if not agent:
            return jsonify({"error": "에이전트를 찾을 수 없습니다."}), 404

        latest_data = SensorData.query.filter_by(agent_id=agent.id).order_by(SensorData.timestamp.desc()).first()
        if latest_data:
            return jsonify({
                "crying": latest_data.crying,
                "direction": latest_data.direction,
                "temperature": latest_data.temperature,
                "timestamp": latest_data.timestamp.isoformat()
            })
        return jsonify({
            "crying": None,
            "direction": None,
            "temperature": None
        })
    except Exception as e:
        print(f"센서 데이터 조회 오류: {e}")
        return jsonify({"error": "데이터 조회 중 오류가 발생했습니다."}), 500

@app.route('/api/sensor_data/<uuid>')
def get_sensor_data_api(uuid):
    try:
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        agent = Agent.query.filter_by(uuid=uuid).first()
        if not agent:
            return jsonify({"error": "에이전트를 찾을 수 없습니다."}), 404

        if not start_date_str or not end_date_str:
            return jsonify({"error": "시작 날짜와 종료 날짜를 제공해야 합니다."}), 400

        try:
            start_date = datetime.datetime.fromisoformat(start_date_str)
            end_date = datetime.datetime.fromisoformat(end_date_str)
        except (ValueError, TypeError) as e:
            return jsonify({"error": f"날짜 형식이 올바르지 않습니다: {str(e)}"}), 400

        sensor_data = SensorData.query.filter(
            SensorData.agent_id == agent.id,
            SensorData.timestamp.between(start_date, end_date)
        ).order_by(SensorData.timestamp).all()

        return jsonify([
            {
                'timestamp': d.timestamp.isoformat(),
                'temperature': d.temperature,
                'crying': d.crying,
                'direction': d.direction
            }
            for d in sensor_data
        ])
    except Exception as e:
        print(f"센서 데이터 API 오류: {e}")
        return jsonify({"error": "데이터 조회 중 오류가 발생했습니다."}), 500

@app.route('/api/alert_history/<uuid>')
def get_alert_history(uuid):
    """특정 요람의 알림 히스토리 조회"""
    try:
        agent = Agent.query.filter_by(uuid=uuid).first()
        if not agent:
            return jsonify({"error": "에이전트를 찾을 수 없습니다."}), 404

        # 최근 30일간의 알림 조회
        since_date = datetime.datetime.utcnow() - datetime.timedelta(days=30)
        alerts = AlertLog.query.filter(
            AlertLog.agent_id == agent.id,
            AlertLog.created_at > since_date
        ).order_by(AlertLog.created_at.desc()).all()

        return jsonify([{
            'id': alert.id,
            'alert_type': alert.alert_type,
            'alert_message': alert.alert_message,
            'temperature': alert.temperature,
            'face_detected': alert.face_detected,
            'resolved': alert.resolved,
            'created_at': alert.created_at.isoformat(),
            'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None
        } for alert in alerts])
    except Exception as e:
        print(f"알림 히스토리 조회 오류: {e}")
        return jsonify({"error": "데이터 조회 중 오류가 발생했습니다."}), 500

@app.route('/api/alert_detail/<int:alert_id>')
def get_alert_detail(alert_id):
    """특정 알림의 상세 정보 (센서 데이터 + 비디오 프레임) 조회"""
    try:
        alert = AlertLog.query.get(alert_id)
        if not alert:
            return jsonify({"error": "알림을 찾을 수 없습니다."}), 404

        # 해당 알림과 연결된 센서 데이터 조회
        sensor_data = SensorData.query.filter_by(
            alert_log_id=alert_id
        ).order_by(SensorData.timestamp).all()

        # 해당 알림과 연결된 비디오 프레임 조회
        video_frames = VideoFrame.query.filter_by(
            alert_log_id=alert_id
        ).order_by(VideoFrame.timestamp).all()

        return jsonify({
            'alert': {
                'id': alert.id,
                'alert_type': alert.alert_type,
                'alert_message': alert.alert_message,
                'temperature': alert.temperature,
                'face_detected': alert.face_detected,
                'resolved': alert.resolved,
                'created_at': alert.created_at.isoformat(),
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None
            },
            'sensor_data': [{
                'timestamp': data.timestamp.isoformat(),
                'temperature': data.temperature,
                'crying': data.crying,
                'direction': data.direction
            } for data in sensor_data],
            'video_frames': [{
                'id': frame.id,
                'timestamp': frame.timestamp.isoformat()
            } for frame in video_frames],
            'total_frames': len(video_frames)
        })
    except Exception as e:
        print(f"알림 상세 조회 오류: {e}")
        return jsonify({"error": "데이터 조회 중 오류가 발생했습니다."}), 500

@app.route('/api/alert_frame/<int:frame_id>')
def get_alert_frame(frame_id):
    """특정 프레임 이미지 반환"""
    try:
        frame = VideoFrame.query.get(frame_id)
        if not frame:
            return jsonify({"error": "프레임을 찾을 수 없습니다."}), 404

        return Response(frame.frame, mimetype='image/jpeg')
    except Exception as e:
        print(f"프레임 조회 오류: {e}")
        return jsonify({"error": "프레임 조회 중 오류가 발생했습니다."}), 500

def create_video_from_frames(frames):
    if not frames:
        return None

    temp_video_path = f"/tmp/{uuid.uuid4()}.mp4"
    
    frame_data = frames[0].frame
    nparr = np.frombuffer(frame_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    height, width, layers = img.shape
    size = (width, height)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video_path, fourcc, 10, size)

    for frame_obj in frames:
        nparr = np.frombuffer(frame_obj.frame, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        out.write(img)
    
    out.release()
    return temp_video_path

@app.route('/api/video/<uuid>')
def get_video_api(uuid):
    date_str = request.args.get('date')
    time_str = request.args.get('time')

    agent = Agent.query.filter_by(uuid=uuid).first()
    if not agent:
        return "Agent not found", 404

    try:
        start_datetime = datetime.datetime.fromisoformat(f"{date_str}T{time_str}")
        end_datetime = start_datetime + datetime.timedelta(minutes=1)
    except (ValueError, TypeError):
        return "Invalid date/time format", 400

    frames = VideoFrame.query.filter(
        VideoFrame.agent_id == agent.id,
        VideoFrame.timestamp.between(start_datetime, end_datetime)
    ).order_by(VideoFrame.timestamp).all()

    if not frames:
        return "No frames found for this period", 404

    video_path = create_video_from_frames(frames)
    if video_path:
        response = send_file(video_path, as_attachment=False, mimetype='video/mp4')
        
        # 응답 후 임시 파일 삭제
        @response.call_on_close
        def cleanup():
            try:
                if os.path.exists(video_path):
                    os.remove(video_path)
            except Exception as e:
                print(f"임시 파일 삭제 오류: {e}")
        
        return response
    else:
        return "Could not create video", 500

# 알림 설정 조회 API
@app.route('/api/alert_settings/<uuid>', methods=['GET'])
def get_alert_settings(uuid):
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        agent = Agent.query.filter_by(uuid=uuid).first()
        if not agent or agent.user_id != session['user_id']:
            return jsonify({'error': 'Agent not found'}), 404
        
        alert_setting = AlertSettings.query.filter_by(agent_id=agent.id).first()
        
        if not alert_setting:
            # 기본값 반환
            return jsonify({
                'max_temperature': 38.0,
                'abnormal_position_timeout': 30,
                'crying_duration_threshold': 30,
                'push_notifications_enabled': True,
                'email_notifications_enabled': False
            }), 200
        
        return jsonify({
            'max_temperature': alert_setting.max_temperature,
            'abnormal_position_timeout': alert_setting.abnormal_position_timeout,
            'crying_duration_threshold': alert_setting.crying_duration_threshold,
            'push_notifications_enabled': alert_setting.push_notifications_enabled,
            'email_notifications_enabled': alert_setting.email_notifications_enabled
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 알림 설정 페이지
@app.route('/alert_settings')
def alert_settings_page():
    if not session.get('user_id'):
        return redirect('/login')
    
    user = User.query.get(session['user_id'])
    agents = user.registered_agents if user else []
    
    # 각 에이전트의 알림 설정 조회
    agent_alerts = {}
    for agent in agents:
        alert_setting = AlertSettings.query.filter_by(agent_id=agent.id).first()
        agent_alerts[agent.uuid] = alert_setting
    
    return render_template('alert_settings.html', agents=agents, agent_alerts=agent_alerts)

# 알림 설정 업데이트
@app.route('/api/alert_settings/<uuid>', methods=['POST'])
def update_alert_settings(uuid):
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        agent = Agent.query.filter_by(uuid=uuid).first()
        if not agent or agent.user_id != session['user_id']:
            return jsonify({'error': 'Agent not found'}), 404
        
        data = request.get_json()
        
        # 기존 설정 조회 또는 새로 생성
        alert_setting = AlertSettings.query.filter_by(agent_id=agent.id).first()
        if not alert_setting:
            alert_setting = AlertSettings(
                user_id=session['user_id'],
                agent_id=agent.id
            )
            db.session.add(alert_setting)
        
        # 설정 업데이트
        alert_setting.max_temperature = float(data.get('max_temperature', 38.0))
        alert_setting.abnormal_position_timeout = int(data.get('abnormal_position_timeout', 30))
        alert_setting.crying_duration_threshold = int(data.get('crying_duration_threshold', 30))
        alert_setting.push_notifications_enabled = bool(data.get('push_notifications_enabled', True))
        alert_setting.email_notifications_enabled = bool(data.get('email_notifications_enabled', False))
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 웹 푸시 구독 등록
@app.route('/api/push_subscription', methods=['POST'])
def register_push_subscription():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        
        # 모든 에이전트에 대해 푸시 구독 정보 업데이트
        user = User.query.get(session['user_id'])
        for agent in user.registered_agents:
            alert_setting = AlertSettings.query.filter_by(agent_id=agent.id).first()
            if not alert_setting:
                alert_setting = AlertSettings(
                    user_id=session['user_id'],
                    agent_id=agent.id
                )
                db.session.add(alert_setting)
            
            alert_setting.push_endpoint = data.get('endpoint')
            alert_setting.push_p256dh = data.get('keys', {}).get('p256dh')
            alert_setting.push_auth = data.get('keys', {}).get('auth')
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 알림 로그 조회
@app.route('/api/alert_logs')
def get_alert_logs():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # 최근 24시간 알림 로그 조회
        since = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        logs = AlertLog.query.filter_by(user_id=session['user_id']).filter(
            AlertLog.created_at > since
        ).order_by(AlertLog.created_at.desc()).limit(50).all()
        
        result = []
        for log in logs:
            agent = Agent.query.get(log.agent_id)
            result.append({
                'id': log.id,
                'agent_uuid': agent.uuid if agent else 'unknown',
                'alert_type': log.alert_type,
                'message': log.alert_message,
                'temperature': log.temperature,
                'face_detected': log.face_detected,
                'notification_sent': log.notification_sent,
                'resolved': log.resolved,
                'created_at': log.created_at.isoformat(),
                'resolved_at': log.resolved_at.isoformat() if log.resolved_at else None
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 알림 해결 처리
@app.route('/api/alert_logs/<int:log_id>/resolve', methods=['POST'])
def resolve_alert(log_id):
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        log = AlertLog.query.filter_by(id=log_id, user_id=session['user_id']).first()
        if not log:
            return jsonify({'error': 'Alert log not found'}), 404
        
        log.resolved = True
        log.resolved_at = datetime.datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 현재 상태 조회 (얼굴 인식, 온도 등)
@app.route('/api/agent_status/<uuid>')
def get_agent_status(uuid):
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        agent = Agent.query.filter_by(uuid=uuid).first()
        if not agent or agent.user_id != session['user_id']:
            return jsonify({'error': 'Agent not found'}), 404
        
        # 최신 센서 데이터
        latest_sensor = SensorData.query.filter_by(agent_id=agent.id).order_by(
            SensorData.timestamp.desc()
        ).first()
        
        # 얼굴/방향 상태
        face_direction = agent_face_status.get(uuid, None)
        last_direction_time = agent_last_direction_time.get(uuid)
        last_normal_time = agent_last_normal_face.get(uuid)
        
        result = {
            'agent_uuid': uuid,
            'temperature': latest_sensor.temperature if latest_sensor else None,
            'crying': latest_sensor.crying if latest_sensor else None,
            'direction': latest_sensor.direction if latest_sensor else None,
            'face_direction': face_direction,
            'last_direction_time': last_direction_time.isoformat() if last_direction_time else None,
            'last_normal_face_time': last_normal_time.isoformat() if last_normal_time else None,
            'last_update': latest_sensor.timestamp.isoformat() if latest_sensor else None
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=80)