# smart_cradle_server - Flask REST API Server# 스마트 요람 Flask 서버



Flask 기반 스마트 요람 백엔드 API 서버입니다. MQTT 브로커와 통신하여 IoT 디바이스로부터 실시간 데이터를 수신하고, MySQL 데이터베이스에 저장하며, 웹/모바일 클라이언트에게 RESTful API를 제공합니다.이 서비스는 MQTT와 MySQL을 포함한 Flask 기반 서버를 실행합니다.



## 🛠 기술 스택## 🔧 환경 변수 설정



- **Framework**: Flask 3.x기존 .env 파일과 호환되는 환경 변수들:

- **WSGI Server**: Gunicorn

- **Database**: MySQL 8.0 (SQLAlchemy ORM)- `SECRET_KEY`: Flask 세션 암호화 키

- **Message Broker**: MQTT (Paho MQTT Client)- `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`: MySQL 데이터베이스 연결 정보

- **Authentication**: Session-based (Flask Session + Cookie)- `MQTT_BROKER_HOST` (기본값: mosquitto), `MQTT_BROKER_PORT` (기본값: 1883): MQTT 브로커 연결 정보

- **Video Processing**: OpenCV (cv2)

- **Security**: Werkzeug Password Hashing## 🗄 데이터베이스 URL 구성



## 📡 API 엔드포인트- `SQLALCHEMY_DATABASE_URI`가 설정되어 있으면 그대로 사용됩니다.

- 그렇지 않으면 다음과 같이 구성됩니다: `mysql+pymysql://USER:PASS@HOST:PORT/DB`

### 🔐 인증 API

## 🌐 주요 라우트

#### POST `/register`

사용자 회원가입### 웹 페이지

- `GET /` - 대시보드 (세션 필요)

**Request:**- `GET/POST /register` - 회원가입

```json- `GET/POST /login` - 로그인

{- `GET /logout` - 로그아웃

  "username": "string",- `GET/POST /register_cradle` - 요람 등록

  "password": "string"

}### API 엔드포인트

```- `POST /register_agent` - IoT 디바이스 등록 (JSON: `{ uuid, ip }`)

- `GET /stream/<uuid>` - 비디오 스트림

**Response (201):**- `POST /control_motor/<uuid>` - 모터 제어

```json- `GET /crying_status/<uuid>` - 울음 상태 조회

{- `GET /direction_status/<uuid>` - 방향 상태 조회

  "success": true,- `GET /get_sensor_data/<uuid>` - 센서 데이터 조회

  "message": "회원가입이 완료되었습니다."

}## 🚀 로컬 실행

```

```bash

**Response (400):**# 의존성 설치

```jsonpip install -r requirements.txt

{

  "success": false,# Flask 애플리케이션 실행

  "message": "이미 사용 중인 아이디입니다."FLASK_APP=smart_cradle_server.py flask run

}```

```

## 🐳 Docker 이미지 (Gunicorn)

---

- 컨테이너 내부에서 80번 포트로 수신

#### GET `/check_username/<username>`- Gunicorn WSGI 서버 사용

실시간 아이디 중복 체크- 멀티 워커 프로세스로 안정적인 서비스 제공



**Response (200):**## 📋 요구사항

```json

{Python 패키지 의존성은 `requirements.txt`에 정의되어 있습니다:

  "exists": boolean

}- Flask 2.3.2: 웹 프레임워크

```- SQLAlchemy 3.0.3: ORM

- PyMySQL 1.1.0: MySQL 드라이버

---- paho-mqtt 1.6.1: MQTT 클라이언트

- opencv-python-headless: 영상 처리

#### POST `/login`- gunicorn 21.2.0: WSGI 서버

사용자 로그인 (세션 쿠키 발급)

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "로그인 성공",
  "user": {
    "id": number,
    "username": "string"
  }
}
```

**Response (401):**
```json
{
  "success": false,
  "message": "아이디 또는 비밀번호가 틀렸습니다."
}
```

---

#### POST `/logout`
사용자 로그아웃 (세션 삭제)

**Response (200):**
```json
{
  "success": true,
  "message": "로그아웃 되었습니다."
}
```

---

### 🏠 요람(Agent) 관리 API

#### POST `/register_agent`
IoT 디바이스가 서버에 자신을 등록

**Request:**
```json
{
  "uuid": "string",
  "ip": "string"
}
```

**Response (200):**
```json
{
  "status": "success",
  "message": "에이전트 등록 성공"
}
```

---

#### POST `/register_cradle`
사용자가 요람을 자신의 계정에 등록 (QR 코드 스캔)

**Request:**
```json
{
  "cradle_uuid": "string"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "요람이 등록되었습니다.",
  "agent": {
    "id": number,
    "uuid": "string",
    "ip": "string",
    "created_at": "ISO8601",
    "updated_at": "ISO8601"
  }
}
```

**Response (404):**
```json
{
  "success": false,
  "message": "등록되지 않은 UUID입니다."
}
```

---

#### POST `/select_cradle`
요람 선택 (세션에 저장)

**Request:**
```json
{
  "uuid": "string"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "요람이 선택되었습니다."
}
```

---

#### POST `/delete_cradle`
요람 삭제 (관련 데이터 모두 삭제)

**Request:**
```json
{
  "uuid": "string"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "요람이 삭제되었습니다."
}
```

---

#### GET `/api/agents`
사용자가 등록한 요람 목록 조회

**Response (200):**
```json
[
  {
    "id": number,
    "uuid": "string",
    "ip": "string",
    "created_at": "ISO8601",
    "updated_at": "ISO8601"
  }
]
```

---

### 📊 모니터링 API

#### GET `/api/agent_status/<uuid>`
요람의 실시간 상태 조회

**Response (200):**
```json
{
  "agent_uuid": "string",
  "temperature": number | null,
  "crying": "Crying" | "Not Crying" | null,
  "direction": "정면 유지 중" | "좌측으로 움직임" | "우측으로 움직임" | "인식 안됨" | null,
  "face_direction": string | null,
  "last_direction_time": "ISO8601" | null,
  "last_normal_face_time": "ISO8601" | null,
  "last_update": "ISO8601" | null
}
```

---

#### GET `/get_sensor_data/<uuid>`
요람의 최신 센서 데이터 조회

**Response (200):**
```json
{
  "crying": "Crying" | "Not Crying" | null,
  "direction": "정면 유지 중" | "인식 안됨" | null,
  "temperature": number | null,
  "timestamp": "ISO8601"
}
```

---

#### GET `/api/sensor_data/<uuid>?start_date=<date>&end_date=<date>`
기간별 센서 데이터 조회

**Query Parameters:**
- `start_date`: ISO8601 datetime string
- `end_date`: ISO8601 datetime string

**Response (200):**
```json
[
  {
    "timestamp": "ISO8601",
    "temperature": number | null,
    "crying": "Crying" | "Not Crying" | null,
    "direction": "정면 유지 중" | null
  }
]
```

---

### 🎥 비디오 API

#### GET `/stream/<uuid>`
실시간 MJPEG 스트림

**Response:**
- Content-Type: `multipart/x-mixed-replace; boundary=frame`
- MJPEG 스트림 (10 FPS)

---

#### GET `/api/video/<uuid>?date=<YYYY-MM-DD>&time=<HH:MM:SS>`
녹화된 영상 다운로드 (1분 단위)

**Query Parameters:**
- `date`: YYYY-MM-DD
- `time`: HH:MM:SS

**Response:**
- Content-Type: `video/mp4`
- MP4 비디오 파일

---

### 🔔 알림 API

#### GET `/api/alert_logs`
최근 24시간 알림 로그 조회 (최대 50개)

**Response (200):**
```json
[
  {
    "id": number,
    "agent_uuid": "string",
    "alert_type": "high_temperature" | "crying" | "abnormal_position" | "face_not_detected",
    "message": "string",
    "temperature": number | null,
    "face_detected": boolean | null,
    "notification_sent": boolean,
    "resolved": boolean,
    "created_at": "ISO8601",
    "resolved_at": "ISO8601" | null
  }
]
```

---

#### GET `/api/alert_history/<uuid>`
특정 요람의 알림 히스토리 조회 (최근 30일)

**Response (200):**
```json
[
  {
    "id": number,
    "alert_type": "string",
    "alert_message": "string",
    "temperature": number | null,
    "face_detected": boolean | null,
    "resolved": boolean,
    "created_at": "ISO8601",
    "resolved_at": "ISO8601" | null
  }
]
```

---

#### GET `/api/alert_detail/<alert_id>`
알림 상세 정보 조회 (센서 데이터 + 비디오 프레임 포함)

**Response (200):**
```json
{
  "alert": {
    "id": number,
    "alert_type": "string",
    "alert_message": "string",
    "temperature": number | null,
    "face_detected": boolean | null,
    "resolved": boolean,
    "created_at": "ISO8601",
    "resolved_at": "ISO8601" | null
  },
  "sensor_data": [...],
  "video_frames": [
    {
      "id": number,
      "timestamp": "ISO8601"
    }
  ],
  "total_frames": number
}
```

---

#### GET `/api/alert_frame/<frame_id>`
알림 프레임 이미지 조회

**Response:**
- Content-Type: `image/jpeg`
- JPEG 이미지 데이터

---

#### POST `/api/alert_logs/<log_id>/resolve`
알림 해결 처리

**Response (200):**
```json
{
  "success": true
}
```

---

### ⚙️ 알림 설정 API

#### GET `/api/alert_settings/<uuid>`
알림 설정 조회

**Response (200):**
```json
{
  "max_temperature": 38.0,
  "abnormal_position_timeout": 30,
  "crying_duration_threshold": 30,
  "push_notifications_enabled": true,
  "email_notifications_enabled": false
}
```

---

#### POST `/api/alert_settings/<uuid>`
알림 설정 업데이트

**Request:**
```json
{
  "max_temperature": number,
  "abnormal_position_timeout": number,
  "crying_duration_threshold": number,
  "push_notifications_enabled": boolean,
  "email_notifications_enabled": boolean
}
```

**Response (200):**
```json
{
  "success": true
}
```

---

#### POST `/api/push_subscription`
웹 푸시 구독 등록

**Request:**
```json
{
  "endpoint": "string",
  "keys": {
    "p256dh": "string",
    "auth": "string"
  }
}
```

**Response (200):**
```json
{
  "success": true
}
```

---

### 🎮 제어 API

#### POST `/control_motor/<uuid>`
모터 시작/정지 제어 (MQTT 메시지 전송)

**Request:**
```json
{
  "action": "start" | "stop"
}
```

**Response (200):**
```json
{
  "success": true
}
```

**Response (500):**
```json
{
  "success": false,
  "message": "MQTT 메시지 전송 실패"
}
```

**MQTT Topic:** `cradle/{uuid}/servo`

---

## 🔌 MQTT 통신

### 구독 (Subscribe) 토픽

서버가 IoT 디바이스로부터 데이터를 수신하는 토픽:

1. **`cradle/+/temperature`** - 온도 데이터
   ```json
   {
     "temperature": 36.5
   }
   ```

2. **`cradle/+/crying`** - 울음 감지 데이터
   ```json
   {
     "status": "Crying" | "Not Crying"
   }
   ```

3. **`cradle/+/direction`** - 얼굴 방향 데이터
   ```json
   {
     "direction": "정면 유지 중" | "좌측으로 움직임" | "우측으로 움직임" | "인식 안됨"
   }
   ```

4. **`cradle/+/frame`** - 비디오 프레임 (Base64 인코딩)
   ```json
   {
     "frame": "base64_encoded_jpeg_data"
   }
   ```

### 발행 (Publish) 토픽

서버가 IoT 디바이스로 명령을 전송하는 토픽:

1. **`cradle/{uuid}/servo`** - 모터 제어 명령
   ```json
   {
     "action": "start" | "stop"
   }
   ```

---

## 🗄️ 데이터베이스 스키마

### `users` 테이블
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INT (PK) | 사용자 ID |
| username | VARCHAR(80) | 아이디 (UNIQUE) |
| password | VARCHAR(255) | 해싱된 비밀번호 |

### `agents` 테이블
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INT (PK) | 요람 ID |
| uuid | VARCHAR(255) | 요람 고유 식별자 (UNIQUE) |
| ip | VARCHAR(255) | 요람 IP 주소 |
| user_id | INT (FK) | 소유자 ID |
| created_at | DATETIME | 생성 시간 |
| updated_at | DATETIME | 수정 시간 |

### `sensor_data` 테이블
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INT (PK) | 센서 데이터 ID |
| agent_id | INT (FK) | 요람 ID |
| alert_log_id | INT (FK, NULL) | 알림 ID (알림 녹화 시) |
| timestamp | DATETIME | 측정 시간 |
| temperature | FLOAT | 온도 (°C) |
| crying | VARCHAR(50) | 울음 상태 |
| direction | VARCHAR(50) | 얼굴 방향 |

### `video_frames` 테이블
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INT (PK) | 프레임 ID |
| agent_id | INT (FK) | 요람 ID |
| alert_log_id | INT (FK, NULL) | 알림 ID (알림 녹화 시) |
| timestamp | DATETIME | 촬영 시간 |
| frame | LONGBLOB | JPEG 이미지 데이터 |

### `alert_settings` 테이블
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INT (PK) | 설정 ID |
| user_id | INT (FK) | 사용자 ID |
| agent_id | INT (FK) | 요람 ID |
| max_temperature | FLOAT | 최대 온도 임계값 (°C) |
| abnormal_position_timeout | INT | 비정상 자세 허용 시간 (초) |
| crying_duration_threshold | INT | 울음 알림 임계값 (초) |
| push_notifications_enabled | BOOLEAN | 푸시 알림 활성화 |
| email_notifications_enabled | BOOLEAN | 이메일 알림 활성화 |
| push_endpoint | TEXT | 웹 푸시 엔드포인트 |
| push_p256dh | TEXT | 웹 푸시 공개키 |
| push_auth | TEXT | 웹 푸시 인증키 |

### `alert_logs` 테이블
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INT (PK) | 알림 ID |
| user_id | INT (FK) | 사용자 ID |
| agent_id | INT (FK) | 요람 ID |
| alert_type | VARCHAR(50) | 알림 유형 |
| alert_message | TEXT | 알림 메시지 |
| temperature | FLOAT | 당시 온도 |
| face_detected | BOOLEAN | 얼굴 인식 여부 |
| notification_sent | BOOLEAN | 알림 전송 여부 |
| resolved | BOOLEAN | 해결 여부 |
| created_at | DATETIME | 발생 시간 |
| resolved_at | DATETIME | 해결 시간 |

---

## 🚨 알림 로직

### 알림 유형

1. **고온 알림 (`high_temperature`)**
   - 온도가 설정된 `max_temperature` 초과 시 발생
   - 중복 방지: 5분 이내 재발생 방지

2. **울음 알림 (`crying`)**
   - 울음이 `crying_duration_threshold` 이상 지속 시 발생
   - 중복 방지: 2분 이내 재발생 방지

3. **비정상 자세 알림 (`abnormal_position`)**
   - 얼굴이 정면이 아닌 상태가 `abnormal_position_timeout` 이상 지속 시 발생
   - 중복 방지: 2분 이내 재발생 방지

4. **얼굴 인식 실패 (`face_not_detected`)**
   - 얼굴이 인식되지 않는 상태가 `abnormal_position_timeout` 이상 지속 시 발생
   - 중복 방지: 2분 이내 재발생 방지

### 알림 녹화

- 알림 발생 시 **60초 동안** 센서 데이터와 비디오 프레임을 DB에 저장
- `alert_log_id`로 연결되어 추후 재생 가능
- 실시간 스트리밍용 프레임은 메모리에 항상 유지

---

## 🔧 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `SECRET_KEY` | random | Flask 세션 암호화 키 |
| `MYSQL_HOST` | `34.121.73.128` | MySQL 서버 호스트 |
| `MYSQL_PORT` | `3306` | MySQL 포트 |
| `MYSQL_USER` | `sc_user` | MySQL 사용자 |
| `MYSQL_PASSWORD` | `SC_password_12!45` | MySQL 비밀번호 |
| `MYSQL_DATABASE` | `smartcradle` | 데이터베이스 이름 |
| `MQTT_BROKER_HOST` | `mosquitto` | MQTT 브로커 호스트 |
| `MQTT_BROKER_PORT` | `1883` | MQTT 브로커 포트 |

---

## 🚀 로컬 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
```bash
export MYSQL_HOST=34.121.73.128
export MYSQL_PORT=3306
export MYSQL_USER=sc_user
export MYSQL_PASSWORD=SC_password_12!45
export MYSQL_DATABASE=smartcradle
export MQTT_BROKER_HOST=mosquitto
export MQTT_BROKER_PORT=1883
export SECRET_KEY=your_secret_key
```

### 3. Flask 개발 서버 실행
```bash
python smart_cradle_server.py
```

서버는 `http://0.0.0.0:80`에서 실행됩니다.

---

## 🐳 Docker 실행

### Gunicorn 프로덕션 서버

```bash
docker run -d \
  -p 80:80 \
  -e MYSQL_HOST=34.121.73.128 \
  -e MYSQL_PORT=3306 \
  -e MYSQL_USER=sc_user \
  -e MYSQL_PASSWORD=SC_password_12!45 \
  -e MYSQL_DATABASE=smartcradle \
  -e MQTT_BROKER_HOST=mosquitto \
  -e MQTT_BROKER_PORT=1883 \
  -e SECRET_KEY=your_secret_key \
  your-dockerhub-username/smart-cradle-server:latest
```

컨테이너 내부에서 Gunicorn이 멀티 워커로 실행되어 안정적인 서비스를 제공합니다.

---

## 📊 성능 최적화

- **Gunicorn 워커**: CPU 코어 수에 따라 자동 조정
- **MQTT 재연결**: 연결 끊김 시 자동 재연결 (exponential backoff)
- **DB 연결 풀**: SQLAlchemy가 자동 관리
- **비디오 스트리밍**: 메모리 내 마지막 프레임만 유지 (10 FPS)
- **알림 중복 방지**: 시간 기반 필터링으로 불필요한 알림 방지

---

## 🔒 보안

- **비밀번호 해싱**: Werkzeug의 `generate_password_hash` 사용
- **세션 기반 인증**: Flask Session + Secure Cookie
- **CORS 설정**: 모바일 앱 접근 허용
- **SQL Injection 방지**: SQLAlchemy ORM 사용

---

## 📝 개발 참고사항

- 모든 datetime은 UTC 기준
- 이미지 데이터는 Base64 인코딩 후 MQTT 전송
- 비디오 프레임은 JPEG 압축 (quality=80)
- MQTT QoS 레벨은 0 (최소 전송 보장)
- 세션 쿠키는 브라우저 종료 시 삭제

---

## 🐛 트러블슈팅

### DB 연결 실패
- MySQL 서버 상태 확인: `systemctl status mysql`
- 방화벽 포트 3306 개방 확인
- `wait_for_db()` 함수가 20회 재시도 수행

### MQTT 연결 실패
- Mosquitto 서버 상태 확인: `docker ps | grep mosquitto`
- 포트 1883 개방 확인
- `connect_mqtt_with_retry()` 함수가 무한 재시도 수행

### 비디오 스트림 끊김
- 네트워크 대역폭 확인
- 프레임 크기 조정 (현재 640x480)
- JPEG 품질 조정 (현재 80)
