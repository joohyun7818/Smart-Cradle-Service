from flask import Flask, jsonify, request, Response, send_file
from flask_sqlalchemy import SQLAlchemy
import os
import datetime
import base64
import threading
import time
import uuid as uuidlib
import numpy as np
import cv2
import paho.mqtt.client as mqtt

# App setup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or os.urandom(24)

# DB config
sql_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
if not sql_uri:
    db_user = os.getenv('MYSQL_USER', 'sc_user')
    db_pass = os.getenv('MYSQL_PASSWORD', 'sc_pass')
    db_host = os.getenv('MYSQL_HOST', 'db')
    db_name = os.getenv('MYSQL_DATABASE', 'smartcradle')
    sql_uri = f'mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}'

app.config['SQLALCHEMY_DATABASE_URI'] = sql_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Storage paths
BASE_DATA_DIR = os.getenv('DATA_DIR', '/data')
FRAMES_DIR = os.path.join(BASE_DATA_DIR, 'frames')
os.makedirs(FRAMES_DIR, exist_ok=True)

# Models
class SensorReading(db.Model):
    __tablename__ = 'sensor_readings'
    id = db.Column(db.Integer, primary_key=True)
    agent_uuid = db.Column(db.String(255), index=True, nullable=False)
    sensor_type = db.Column(db.String(64), nullable=False)
    value = db.Column(db.Text, nullable=True)
    metadata = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)

class Frame(db.Model):
    __tablename__ = 'frames'
    id = db.Column(db.Integer, primary_key=True)
    agent_uuid = db.Column(db.String(255), index=True, nullable=False)
    path = db.Column(db.String(1024), nullable=False)
    format = db.Column(db.String(32), nullable=True)
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    size_bytes = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)

# Ensure tables exist (wait for DB ready similar to v1)
with app.app_context():
    def wait_for_db(max_attempts=20, initial_delay=1):
        attempt = 0
        delay = initial_delay
        from sqlalchemy import text
        while True:
            try:
                db.session.execute(text('SELECT 1'))
                print('DB ready')
                return True
            except Exception as e:
                attempt += 1
                print(f'Waiting for DB (attempt {attempt}): {e}')
                if attempt >= max_attempts:
                    print('Max DB retry reached')
                    return False
                time.sleep(delay)
                delay = min(delay * 2, 10)

    wait_for_db()
    try:
        db.create_all()
        print('v2 DB tables ensured')
    except Exception as e:
        print('Error creating v2 tables:', e)

# MQTT setup
MQTT_BROKER_HOST = os.getenv('MQTT_BROKER_HOST', 'mosquitto')
MQTT_BROKER_PORT = int(os.getenv('MQTT_BROKER_PORT', '1883'))

mqtt_client = mqtt.Client()


def save_sensor_reading(agent_uuid, sensor_type, value, metadata=None):
    try:
        r = SensorReading(agent_uuid=agent_uuid, sensor_type=sensor_type, value=str(value), metadata=(str(metadata) if metadata is not None else None))
        db.session.add(r)
        db.session.commit()
    except Exception as e:
        print('Failed to save sensor reading:', e)
        db.session.rollback()


def save_frame_from_payload(agent_uuid, payload):
    try:
        frame_b64 = payload.get('frame')
        if not frame_b64:
            return None
        frame_data = base64.b64decode(frame_b64)
        nparr = np.frombuffer(frame_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            print('Failed to decode image from payload')
            return None
        h, w = img.shape[:2]
        filename = f"{agent_uuid}-{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%S')}-{uuidlib.uuid4().hex[:8]}.jpg"
        agent_dir = os.path.join(FRAMES_DIR, agent_uuid)
        os.makedirs(agent_dir, exist_ok=True)
        path = os.path.join(agent_dir, filename)
        cv2.imwrite(path, img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        size = os.path.getsize(path)
        fr = Frame(agent_uuid=agent_uuid, path=path, format='jpg', width=w, height=h, size_bytes=size)
        db.session.add(fr)
        db.session.commit()
        return fr
    except Exception as e:
        print('Failed to save frame:', e)
        db.session.rollback()
        return None


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print('MQTT connected (v2)')
        client.subscribe('cradle/+/temperature')
        client.subscribe('cradle/+/crying')
        client.subscribe('cradle/+/direction')
        client.subscribe('cradle/+/frame')
    else:
        print('MQTT connect failed rc=', rc)


def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        parts = topic.split('/')
        if len(parts) < 3:
            return
        agent_uuid = parts[1]
        kind = parts[2]
        payload = None
        try:
            payload = json.loads(msg.payload.decode())
        except Exception:
            try:
                # fallback: plain text
                payload = { 'value': msg.payload.decode() }
            except Exception:
                payload = { 'value': None }

        if kind == 'frame':
            save_frame_from_payload(agent_uuid, payload)
        else:
            # save sensor reading
            value = None
            if isinstance(payload, dict):
                # prefer common keys
                value = payload.get('temperature') or payload.get('status') or payload.get('value') or payload
            else:
                value = payload
            save_sensor_reading(agent_uuid, kind, value, metadata=str(payload))
    except Exception as e:
        print('MQTT message handling error (v2):', e)

import json
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message


def connect_mqtt_with_retry(client, host, port, max_retries=None):
    attempt = 0
    wait = 1
    while True:
        try:
            client.connect(host, port, 60)
            client.loop_start()
            print(f'MQTT connected to {host}:{port} (v2)')
            return True
        except Exception as e:
            attempt += 1
            print(f'MQTT connect error (v2) attempt {attempt}:', e)
            if max_retries is not None and attempt >= max_retries:
                return False
            time.sleep(wait)
            wait = min(wait * 2, 30)

threading.Thread(target=connect_mqtt_with_retry, args=(mqtt_client, MQTT_BROKER_HOST, MQTT_BROKER_PORT, None), daemon=True).start()

# Simple API endpoints
@app.route('/api/agents/<agent_uuid>/sensors')
def get_sensor_readings(agent_uuid):
    sensor_type = request.args.get('type')
    since = request.args.get('since')
    limit = int(request.args.get('limit', '500'))
    q = SensorReading.query.filter_by(agent_uuid=agent_uuid)
    if sensor_type:
        q = q.filter_by(sensor_type=sensor_type)
    if since:
        try:
            dt = datetime.datetime.fromisoformat(since)
            q = q.filter(SensorReading.created_at >= dt)
        except Exception:
            pass
    q = q.order_by(SensorReading.created_at.desc()).limit(limit)
    res = []
    for r in q:
        res.append({
            'id': r.id,
            'agent_uuid': r.agent_uuid,
            'sensor_type': r.sensor_type,
            'value': r.value,
            'metadata': r.metadata,
            'created_at': r.created_at.isoformat()
        })
    return jsonify(res)

@app.route('/api/agents/<agent_uuid>/frames')
def list_frames(agent_uuid):
    limit = int(request.args.get('limit', '100'))
    q = Frame.query.filter_by(agent_uuid=agent_uuid).order_by(Frame.created_at.desc()).limit(limit)
    res = []
    for f in q:
        res.append({
            'id': f.id,
            'path': f.path,
            'format': f.format,
            'width': f.width,
            'height': f.height,
            'size_bytes': f.size_bytes,
            'created_at': f.created_at.isoformat()
        })
    return jsonify(res)

@app.route('/api/frames/<int:frame_id>/download')
def download_frame(frame_id):
    f = Frame.query.get(frame_id)
    if not f:
        return jsonify({'error': 'not found'}), 404
    try:
        return send_file(f.path, mimetype='image/jpeg', as_attachment=False)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
