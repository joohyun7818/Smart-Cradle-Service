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
import base64

app = Flask(__name__)

# MQTT 설정
MQTT_BROKER_HOST = "192.168.219.111"  # 실제 EC2 서버의 공용 IP 주소
MQTT_BROKER_PORT = 1883

# 에이전트별 마지막 프레임을 저장하는 딕셔너리
agent_last_frame = {}
frame_lock = threading.Lock()

# 에이전트별 최신 센서 값을 저장하는 딕셔너리
agent_sensor_data = {}
sensor_data_lock = threading.Lock()

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
        # 토픽에서 UUID 추출
        uuid = msg.topic.split('/')[1]
        payload = json.loads(msg.payload.decode())
        
        with sensor_data_lock:
            if uuid not in agent_sensor_data:
                agent_sensor_data[uuid] = {}
            
            if 'temperature' in msg.topic:
                agent_sensor_data[uuid]['temperature'] = payload.get('temperature')
            elif 'crying' in msg.topic:
                agent_sensor_data[uuid]['crying'] = payload.get('status')
            elif 'direction' in msg.topic:
                agent_sensor_data[uuid]['direction'] = payload.get('direction')
            elif 'frame' in msg.topic:
                # 프레임 데이터 처리
                frame_data = base64.b64decode(payload.get('frame'))
                nparr = np.frombuffer(frame_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                with frame_lock:
                    agent_last_frame[uuid] = frame
                
    except Exception as e:
        print(f"MQTT 메시지 처리 오류: {e}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

try:
    mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"MQTT 연결 오류: {e}")

app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/smart_cradle'
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

@app.route('/register_cradle', methods=['GET', 'POST'])
def register_cradle():
    if not session.get('user_id'):
        return redirect('/login')

    if request.method == 'POST':
        cradle_uuid = request.form['cradle_uuid']
        user_id = session['user_id']

        existing_agent = Agent.query.filter_by(uuid=cradle_uuid).first()
        if existing_agent:
            existing_agent.user_id = user_id
            db.session.commit()
            return redirect('/')
        else:
            return render_template('register_cradle.html', error="등록되지 않은 UUID입니다.")

    return render_template('register_cradle.html')

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
        action = data.get('action')
        
        if action not in ['start', 'stop']:
            return jsonify({'success': False, 'message': '잘못된 액션입니다.'})
            
        topic = f"cradle/{uuid}/servo"
        payload = json.dumps({'action': action})
        mqtt_client.publish(topic, payload)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/crying_status/<uuid>')
def crying_status(uuid):
    def generate():
        while True:
            with sensor_data_lock:
                status = agent_sensor_data.get(uuid, {}).get('crying', '측정 중...')
            yield f"data: {status}\n\n"
            time.sleep(1)
    return Response(generate(), mimetype='text/event-stream')

@app.route('/direction_status/<uuid>')
def direction_status(uuid):
    def generate():
        while True:
            with sensor_data_lock:
                direction = agent_sensor_data.get(uuid, {}).get('direction', '측정 중...')
            yield f"data: {direction}\n\n"
            time.sleep(1)
    return Response(generate(), mimetype='text/event-stream')

@app.route('/get_sensor_data/<uuid>')
def get_sensor_data(uuid):
    with sensor_data_lock:
        if uuid in agent_sensor_data:
            return jsonify(agent_sensor_data[uuid])
        # 404 대신 빈 데이터 반환
        return jsonify({
            "crying": None,
            "direction": None,
            "temperature": None
        })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=80)