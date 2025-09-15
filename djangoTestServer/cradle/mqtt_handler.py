import paho.mqtt.client as mqtt
import json
import base64
import cv2
import numpy as np
import threading
import time
import os

# Global variables for sensor data and frames
agent_sensor_data = {}
sensor_data_lock = threading.Lock()

agent_last_frame = {}
frame_lock = threading.Lock()

mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT Broker 연결 성공")
        client.subscribe("cradle/+/temperature")
        client.subscribe("cradle/+/crying")
        client.subscribe("cradle/+/direction")
        client.subscribe("cradle/+/frame")
    else:
        print(f"MQTT Broker 연결 실패, rc={rc}")

def on_message(client, userdata, msg):
    try:
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
                frame_data = base64.b64decode(payload.get('frame'))
                nparr = np.frombuffer(frame_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                with frame_lock:
                    agent_last_frame[uuid] = frame
    except Exception as e:
        print(f"MQTT 메시지 처리 오류: {e}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def connect_mqtt():
    MQTT_BROKER_HOST = os.getenv('MQTT_BROKER_HOST', 'mosquitto')
    MQTT_BROKER_PORT = int(os.getenv('MQTT_BROKER_PORT', '1883'))
    try:
        mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
        mqtt_client.loop_start()
        print(f"MQTT 연결 성공: {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
    except Exception as e:
        print(f"MQTT 연결 실패: {e}")

# Start MQTT in a thread
threading.Thread(target=connect_mqtt, daemon=True).start()