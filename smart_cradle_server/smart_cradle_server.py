from flask import Flask, render_template, request, redirect, session, url_for, jsonify, Response, send_file
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

# MQTT 설정: 컨테이너 환경에서는 서비스명으로 접근 가능합니다.
# docker-compose에서 설정한 값이 있으면 사용하고, 없으면 'mosquitto'를 기본값으로 사용합니다.
MQTT_BROKER_HOST = os.getenv('MQTT_BROKER_HOST', 'mosquitto')
MQTT_BROKER_PORT = int(os.getenv('MQTT_BROKER_PORT', '1883'))

# 에이전트별 마지막 프레임을 저장하는 딕셔너리
agent_last_frame = {}
frame_lock = threading.Lock()

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

            if 'temperature' in msg.topic:
                new_sensor_data = SensorData(
                    agent_id=agent.id,
                    temperature=payload.get('temperature')
                )
                db.session.add(new_sensor_data)
                db.session.commit()

            elif 'crying' in msg.topic:
                new_sensor_data = SensorData(
                    agent_id=agent.id,
                    crying=payload.get('status')
                )
                db.session.add(new_sensor_data)
                db.session.commit()

            elif 'direction' in msg.topic:
                new_sensor_data = SensorData(
                    agent_id=agent.id,
                    direction=payload.get('direction')
                )
                db.session.add(new_sensor_data)
                db.session.commit()

            elif 'frame' in msg.topic:
                frame_data = base64.b64decode(payload.get('frame'))
                new_frame = VideoFrame(
                    agent_id=agent.id,
                    frame=frame_data
                )
                db.session.add(new_frame)
                db.session.commit()

                # 메모리 내 마지막 프레임도 업데이트 (실시간 스트리밍용)
                nparr = np.frombuffer(frame_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                with frame_lock:
                    agent_last_frame[agent_uuid] = frame

    except Exception as e:
        print(f"MQTT 메시지 처리 및 DB 저장 오류: {e}")


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
    password = db.Column(db.String(120), nullable=False)
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
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    temperature = db.Column(db.Float)
    crying = db.Column(db.String(50))
    direction = db.Column(db.String(50))

class VideoFrame(db.Model):
    __tablename__ = 'video_frames'
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    frame = db.Column(db.LargeBinary)


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
def dashboard_page():
    if not session.get('user_id'):
        return redirect('/login')
    user = User.query.get(session['user_id'])
    agents = user.registered_agents if user else []
    
    # 각 에이전트의 최신 센서 데이터 조회
    agent_sensor_data = {}
    for agent in agents:
        latest_data = SensorData.query.filter_by(agent_id=agent.id).order_by(SensorData.timestamp.desc()).first()
        if latest_data:
            agent_sensor_data[agent.uuid] = latest_data
    
    return render_template('dashboard.html', agents=agents, agent_sensor_data=agent_sensor_data)

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('signup.html', registration_error='이미 사용 중인 아이디입니다.')
        # 비밀번호 해싱
        password_hash = generate_password_hash(password)
        new_user = User(username=username, password=password_hash)
        db.session.add(new_user)
        db.session.commit()
        return render_template('signup.html', registration_success='회원가입이 완료되었습니다. 로그인해주세요.')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        # 비밀번호 해시 검증
        if user and check_password_hash(user.password, password):
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
        return redirect('/login')

    if request.method == 'POST':
        try:
            cradle_uuid = request.form['cradle_uuid']
            user_id = session['user_id']

            existing_agent = Agent.query.filter_by(uuid=cradle_uuid).first()
            if existing_agent:
                existing_agent.user_id = user_id
                db.session.commit()
                return redirect('/')
            else:
                return render_template('register_cradle.html', error="등록되지 않은 UUID입니다.")
        except Exception as e:
            db.session.rollback()
            return render_template('register_cradle.html', error=f"등록 중 오류가 발생했습니다: {str(e)}")

    return render_template('register_cradle.html')

@app.route('/viewer/<uuid>')
def viewer_page(uuid):
    if not session.get('user_id'):
        return redirect('/login')
    return render_template('viewer.html', uuid=uuid)

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=80)