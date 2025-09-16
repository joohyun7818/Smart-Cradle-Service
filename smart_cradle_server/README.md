# Smart Cradle Flask Server

This service runs the Flask-based server with MQTT and MySQL.

Environment variables (compatible with existing .env):

- SECRET_KEY
- MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD
- MQTT_BROKER_HOST (default: mosquitto), MQTT_BROKER_PORT (default: 1883)

Database URL construction:

- If SQLALCHEMY_DATABASE_URI is set, it will be used as-is.
- Else it will be composed as: mysql+pymysql://USER:PASS@HOST:PORT/DB

Primary routes:

- GET / (dashboard; requires session)
- GET/POST /register
- GET/POST /login
- GET /logout
- GET/POST /register_cradle
- POST /register_agent (JSON { uuid, ip })
- GET /stream/&lt;uuid&gt;
- POST /control_motor/&lt;uuid&gt;
- GET /crying_status/&lt;uuid&gt;
- GET /direction_status/&lt;uuid&gt;
- GET /get_sensor_data/&lt;uuid&gt;

Run locally:

- pip install -r requirements.txt
- FLASK_APP=smart_cradle_server.py flask run

Docker image (Gunicorn):

- Listens on port 80 in container.
