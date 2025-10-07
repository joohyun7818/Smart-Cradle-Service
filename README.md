# 스마트 아기요람 시스템 아키텍처

> 최종 업데이트: 2025년 10월 3일

## 📋 목차

1. [시스템 개요](#시스템-개요)
2. [전체 아키텍처](#전체-아키텍처)
3. [컴포넌트 상세](#컴포넌트-상세)
4. [데이터 플로우](#데이터-플로우)
5. [통신 프로토콜](#통신-프로토콜)
6. [데이터베이스 스키마](#데이터베이스-스키마)
7. [보안 및 인증](#보안-및-인증)
8. [배포 구조](#배포-구조)

---

## 시스템 개요목적

IoT 기술과 AI를 활용하여 아기의 안전을 실시간으로 모니터링하고, 위험 상황 발생 시 즉각적으로 보호자에게 알림을 제공하는 스마트 요람 시스템

### 주요 기능

- 🎥 실시간 영상 모니터링 (ESP32-CAM / Raspberry Pi)
- 🤖 AI 기반 얼굴 방향 감지 (MediaPipe Face Mesh)
- 🎤 울음 소리 감지 (KNN 모델 기반 음성 분류)
- 🌡️ 체온 모니터링 (시리얼 통신)
- 🔔 실시간 알림 시스템 (MQTT + HTTP)
- 📊 데이터 분석 및 통계 대시보드
- 🔄 모터 제어 (원격 요람 흔들기)

---

## 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                        사용자 인터페이스                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐              ┌──────────────────┐            │
│  │   모바일 앱       │              │   웹 대시보드     │            │
│  │  (React Native)  │◄────────────►│    (Flask)       │            │
│  │   iOS/Android    │   HTTP/REST  │  Jinja2 템플릿   │            │
│  └──────────────────┘              └──────────────────┘            │
│           │                                   │                     │
└───────────┼───────────────────────────────────┼─────────────────────┘
            │                                   │
            │          HTTP/REST API            │
            └───────────────┬───────────────────┘
                            │
┌───────────────────────────▼────────────────────────────────────────┐
│                      백엔드 서버 (GCP)                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              Flask API Server (Gunicorn)                     │ │
│  │  ┌────────────┐  ┌────────────┐  ┌─────────────┐           │ │
│  │  │ 인증/세션   │  │ 알림 관리  │  │ 데이터 수집  │           │ │
│  │  │   관리     │  │   로직     │  │  및 저장     │           │ │
│  │  └────────────┘  └────────────┘  └─────────────┘           │ │
│  └──────────────────────────────────────────────────────────────┘ │
│           │                    │                    │              │
│           │                    │                    │              │
│  ┌────────▼────────┐  ┌────────▼────────┐  ┌──────▼──────┐      │
│  │  MySQL DB       │  │  MQTT Broker    │  │  파일 저장   │      │
│  │ (별도 인스턴스)  │  │  (Mosquitto)    │  │  (Optional)  │      │
│  └─────────────────┘  └─────────────────┘  └─────────────┘      │
│                                │                                   │
└────────────────────────────────┼───────────────────────────────────┘
                                 │
                        MQTT Protocol
                         (1883 Port)
                                 │
┌────────────────────────────────▼───────────────────────────────────┐
│                   IoT 에이전트 (Raspberry Pi)                       │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  카메라 모듈  │  │  오디오 입력  │  │  시리얼 통신  │           │
│  │ (Picamera2)  │  │ (sounddevice)│  │  (Arduino)   │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                 │                 │                     │
│         ▼                 ▼                 ▼                     │
│  ┌─────────────────────────────────────────────────┐             │
│  │           smart_cradle_agent.py                 │             │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐│             │
│  │  │ 얼굴 방향   │  │  울음 감지   │  │ 체온 수집 ││             │
│  │  │ 감지 (MP)   │  │  (KNN ML)   │  │          ││             │
│  │  └─────────────┘  └─────────────┘  └──────────┘│             │
│  └─────────────────────────────────────────────────┘             │
│                            │                                      │
│                            │ MQTT Publish                         │
│                            ▼                                      │
│                    Topic: cradle/{uuid}/...                       │
│                    - /frame (영상 프레임)                          │
│                    - /direction (얼굴 방향)                        │
│                    - /crying (울음 상태)                           │
│                    - /temperature (체온)                          │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 컴포넌트 상세

### 1. IoT 에이전트 (Raspberry Pi)

**파일**: `smart_cradle_agent.py`

#### 역할

- 하드웨어 센서 데이터 수집
- AI 기반 실시간 분석
- MQTT를 통한 데이터 전송
- 서버 명령 수신 및 실행

#### 주요 기능

##### 1.1 얼굴 방향 감지

```python
# 사용 기술: MediaPipe Face Mesh
- 468개의 얼굴 랜드마크 추출
- 코 끝(landmark[1])과 눈 중심점 비교
- 방향 판단 알고리즘:
  * dx = nose_tip.x - eye_center.x
  * |dx| < 0.02: "정면 유지 중"
  * dx < 0: "우측으로 움직임"
  * dx > 0: "좌측으로 움직임"
```

**출력 데이터**:

```json
{
  "direction": "정면 유지 중",
  "timestamp": "2025-10-03 12:34:56"
}
```

##### 1.2 울음 감지

```python
# 사용 기술: KNN 머신러닝 모델 + MFCC 특징 추출
프로세스:
1. 2초 오디오 녹음 (44.1kHz → 16kHz 리샘플링)
2. MFCC 특징 추출 (13개 계수, 40프레임)
3. KNN 모델로 분류 (Crying/Silent)
4. 확률값과 함께 결과 반환
```

**출력 데이터**:

```json
{
  "status": "Crying",
  "probability": 0.89,
  "timestamp": "2025-10-03 12:34:56"
}
```

##### 1.3 체온 모니터링

```python
# 시리얼 통신 (Arduino → Raspberry Pi)
- 포트: /dev/ttyACM0
- 전송률: 9600 baud
- 프로토콜: 텍스트 기반 ("아기 체온: XX.X°C")
```

**출력 데이터**:

```json
{
  "temperature": "36.5"
}
```

##### 1.4 영상 스트리밍

```python
# Picamera2 사용
해상도: 640x480
프레임레이트: 10 FPS
인코딩: JPEG (품질 80)
전송: Base64 인코딩 후 MQTT 전송
```

**출력 데이터**:

```json
{
  "frame": "base64_encoded_jpeg_string",
  "timestamp": "2025-10-03 12:34:56"
}
```

#### MQTT Topics (Publish)

```
cradle/{CRADLE_UUID}/frame        - 영상 프레임
cradle/{CRADLE_UUID}/direction    - 얼굴 방향
cradle/{CRADLE_UUID}/crying       - 울음 상태
cradle/{CRADLE_UUID}/temperature  - 체온 데이터
```

#### MQTT Topics (Subscribe)

```
cradle/{CRADLE_UUID}/servo        - 모터 제어 명령
```

**모터 제어 명령**:

```json
{
  "action": "start"  // 또는 "stop"
}
```

#### 스레드 구조

```
main()
  ├─ frame_thread (영상 처리 + 얼굴 감지)
  ├─ cry_thread (울음 감지)
  └─ temp_thread (체온 수집)
```

---

### 2. 백엔드 서버 (Flask)

**파일**: `smart_cradle_server/smart_cradle_server.py`

#### 역할

- RESTful API 제공
- MQTT 브로커와 통신
- 데이터베이스 관리
- 실시간 알림 로직
- 웹 대시보드 렌더링

#### 주요 엔드포인트

##### 2.1 인증 API

```
POST /register         - 사용자 회원가입
POST /login            - 로그인
POST /logout           - 로그아웃
GET  /check_username/<username> - 중복 확인
```

##### 2.2 요람(Agent) 관리

```
POST /register_agent   - 에이전트 등록 (QR 스캔)
POST /register_cradle  - 요람 등록
GET  /api/agents       - 사용자의 요람 목록
GET  /api/agent/<uuid> - 특정 요람 상태
```

##### 2.3 센서 데이터

```
GET  /api/sensor_data/<agent_uuid>  - 최근 센서 데이터
GET  /api/sensor_stats/<agent_uuid> - 통계 데이터
```

##### 2.4 알림

```
GET  /api/alerts/<agent_uuid>       - 알림 목록
POST /api/alert_settings/<agent_id> - 알림 설정 저장
GET  /api/alert_settings/<agent_id> - 알림 설정 조회
```

##### 2.5 영상 스트리밍

```
GET  /video_feed/<agent_uuid>       - MJPEG 스트림
```

##### 2.6 모터 제어

```
POST /api/control_servo/<agent_uuid> - 모터 제어
```

**요청 바디**:

```json
{
  "action": "start"  // 또는 "stop"
}
```

#### MQTT 통신 구조

##### 서버 측 MQTT 클라이언트

```python
# 구독 Topics
cradle/+/frame        - 모든 에이전트의 프레임
cradle/+/temperature  - 모든 에이전트의 체온
cradle/+/direction    - 모든 에이전트의 방향
cradle/+/crying       - 모든 에이전트의 울음

# 발행 Topics
cradle/{uuid}/servo   - 특정 에이전트의 모터 제어
```

##### 메시지 핸들러

```python
def on_message(client, userdata, msg):
    # 1. Topic 파싱 (cradle/{uuid}/{data_type})
    # 2. 데이터 파싱 (JSON)
    # 3. 데이터베이스 저장
    # 4. 알림 조건 체크
    # 5. 알림 발송 (필요시)
```

#### 알림 로직

##### 알림 조건

```python
1. 고온 알림
   - 조건: temperature > max_temperature
   - 중복 방지: 5분 이내 중복 알림 차단

2. 비정상 자세 알림
   - 조건: direction != "정면 유지 중"
   - 지속 시간: abnormal_position_timeout 초 이상
   - 중복 방지: 5분 이내 중복 알림 차단

3. 울음 알림
   - 조건: crying_status == "Crying"
   - 지속 시간: crying_duration_threshold 초 이상
   - 중복 방지: 3분 이내 중복 알림 차단
```

##### 알림 전송 프로세스

```
1. 조건 감지
   ↓
2. AlertLog 레코드 생성
   ↓
3. 사용자 설정 확인
   ├─ push_notifications_enabled → 웹 푸시
   └─ email_notifications_enabled → 이메일
   ↓
4. 알림 발송
   ↓
5. 상태 업데이트 (resolved 시)
```

#### 데이터 저장 전략

##### 센서 데이터

```python
# SensorData 테이블
- 온도, 방향, 울음 상태 저장
- 타임스탬프 기록
- 에이전트 UUID 연결
```

##### 비디오 프레임

```python
# VideoFrame 테이블
- Base64 인코딩된 JPEG 저장
- 타임스탬프 기록
- 자동 정리: 10일 이상된 프레임 삭제 (Cron)
```

##### 알림 로그

```python
# AlertLog 테이블
- 알림 유형 (high_temperature, abnormal_position, crying)
- 발생 시간 및 해결 시간
- 메시지 내용
- 해결 여부 (is_resolved)
```

---

### 3. 모바일 앱 (React Native)

**디렉토리**: `SmartCradleApp/`

#### 기술 스택

- **프레임워크**: React Native (Expo)
- **언어**: TypeScript
- **상태 관리**: Redux Toolkit
- **네비게이션**: React Navigation
- **HTTP 클라이언트**: Axios

#### 화면 구조

##### 인증 흐름

```
LoginScreen (로그인)
    ↓
    ├─ 성공 → AgentSelectionScreen (요람 선택)
    └─ 회원가입 → RegisterScreen
```

##### 메인 탭 (하단 네비게이션)

```
MainTabs
  ├─ DashboardScreen (대시보드) - 실시간 모니터링
  ├─ AlertsScreen (알림) - 알림 목록
  ├─ HistoryScreen (히스토리) - 데이터 통계
  ├─ SettingsScreen (설정) - 알림 설정
  └─ AgentSelectionScreen (요람 선택)
```

#### 주요 컴포넌트

##### 1. VideoStream (실시간 영상)

```typescript
// WebView 기반 MJPEG 스트리밍
<WebView
  source={{ uri: `${API_BASE_URL}/video_feed/${agentUuid}` }}
/>
```

##### 2. QRScanner (QR 코드 스캔)

```typescript
// Expo Camera로 QR 코드 스캔
// 에이전트 UUID 추출 후 서버 등록
```

#### Redux Store 구조

```typescript
store/
  ├─ authSlice.ts      // 인증 상태 관리
  │   ├─ isAuthenticated
  │   ├─ userId
  │   └─ username
  │
  └─ agentSlice.ts     // 선택된 요람 관리
      ├─ selectedAgentId
      ├─ selectedAgentUuid
      └─ selectedAgentName
```

#### API 통신

##### api.ts 서비스

```typescript
export const cradleApi = {
  // 인증
  login(username, password)
  register(username, password)
  logout()
  
  // 요람 관리
  getAgents()              // 요람 목록
  registerCradle(qrData)   // QR로 요람 등록
  
  // 센서 데이터
  getSensorData(uuid)      // 최근 데이터
  getSensorStats(uuid)     // 통계
  
  // 알림
  getAlerts(uuid)          // 알림 목록
  getAlertSettings(id)     // 설정 조회
  updateAlertSettings(id, settings) // 설정 저장
  
  // 제어
  controlServo(uuid, action) // 모터 제어
}
```

#### 데이터 폴링

```typescript
// 대시보드에서 주기적으로 데이터 갱신
useEffect(() => {
  const interval = setInterval(() => {
    fetchSensorData();
    fetchAlerts();
  }, 5000); // 5초마다
  
  return () => clearInterval(interval);
}, []);
```

---

### 4. 웹 대시보드 (Flask + Jinja2)

**디렉토리**: `smart_cradle_server/templates/`

#### 페이지 구조

```
base.html (공통 레이아웃)
  ├─ welcome.html (랜딩 페이지)
  ├─ login.html (로그인)
  ├─ signup.html (회원가입)
  └─ 인증 후:
      ├─ dashboard.html (대시보드)
      ├─ register_cradle.html (요람 등록)
      ├─ history.html (히스토리)
      └─ alert_settings.html (알림 설정)
```

#### 주요 기능

##### 1. 실시간 영상 (dashboard.html)

```html
<img id="video-feed" 
     src="/video_feed/{{ agent_uuid }}" 
     alt="실시간 영상">
```

##### 2. 센서 데이터 표시

```javascript
// AJAX로 주기적 업데이트
setInterval(() => {
  fetch(`/api/sensor_data/${agentUuid}`)
    .then(res => res.json())
    .then(data => updateDashboard(data));
}, 2000); // 2초마다
```

##### 3. Chart.js 통계

```html
<!-- 온도 그래프 -->
<canvas id="tempChart"></canvas>

<!-- 울음 빈도 차트 -->
<canvas id="cryingChart"></canvas>
```

##### 4. 모터 제어 버튼

```javascript
function controlServo(action) {
  fetch(`/api/control_servo/${agentUuid}`, {
    method: 'POST',
    body: JSON.stringify({ action }),
    headers: { 'Content-Type': 'application/json' }
  });
}
```

---

## 데이터 플로우

### 1. 센서 데이터 수집 플로우

```
[IoT 에이전트]
    │
    │ 1. 센서 데이터 수집
    │    - 카메라: 640x480 JPEG
    │    - 마이크: 2초 오디오
    │    - 시리얼: 체온 데이터
    ↓
[AI 처리]
    │
    │ 2. 데이터 분석
    │    - MediaPipe: 얼굴 방향 감지
    │    - KNN 모델: 울음 분류
    │    - 파싱: 체온 추출
    ↓
[MQTT Publish]
    │
    │ 3. 데이터 전송
    │    Topic: cradle/{uuid}/{type}
    │    Format: JSON
    ↓
[MQTT Broker]
    │
    │ 4. 메시지 라우팅
    ↓
[Flask 서버]
    │
    │ 5. 데이터 처리
    │    - 데이터베이스 저장
    │    - 알림 조건 체크
    │    - 상태 업데이트
    ↓
[알림 로직]
    │
    │ 6. 알림 발송 (조건 충족 시)
    │    - 웹 푸시
    │    - 이메일 (선택)
    ↓
[클라이언트]
    │
    │ 7. 데이터 표시
    │    - 모바일 앱: API 폴링
    │    - 웹: AJAX 폴링
    │    - 영상: MJPEG 스트림
```

### 2. 사용자 명령 플로우

```
[사용자]
    │
    │ 1. 모터 제어 버튼 클릭
    ↓
[클라이언트]
    │
    │ 2. API 요청
    │    POST /api/control_servo/{uuid}
    │    Body: {"action": "start"}
    ↓
[Flask 서버]
    │
    │ 3. MQTT 메시지 발행
    │    Topic: cradle/{uuid}/servo
    │    Payload: {"action": "start"}
    ↓
[MQTT Broker]
    │
    │ 4. 메시지 전달
    ↓
[IoT 에이전트]
    │
    │ 5. 명령 수신 및 실행
    │    - 메시지 파싱
    │    - 시리얼 통신: "servo\n"
    ↓
[Arduino]
    │
    │ 6. 모터 작동
    │    - 서보 모터 제어
```

### 3. 알림 플로우

```
[센서 데이터] → [알림 조건 체크]
                      ↓
              조건 충족 여부?
                ├─ No → 계속 모니터링
                └─ Yes ↓
          
[AlertLog 생성]
    │
    │ - alert_type: high_temperature/abnormal_position/crying
    │ - message: 알림 메시지
    │ - created_at: 현재 시간
    │ - is_resolved: False
    ↓
[사용자 설정 확인]
    │
    ├─ push_notifications_enabled?
    │   └─ Yes → 웹 푸시 전송
    │
    └─ email_notifications_enabled?
        └─ Yes → 이메일 전송
    
[중복 알림 방지]
    │
    │ - 최근 N분 이내 동일 알림 있는지 체크
    │ - 있으면 전송 생략
  
[알림 해결]
    │
    │ - 상태 정상화 시
    │ - is_resolved = True
    │ - resolved_at = 현재 시간
```

---

## 통신 프로토콜

### 1. MQTT 프로토콜

#### 설정

```yaml
Broker: Eclipse Mosquitto 2.x
Host: mosquitto (Docker 서비스명)
Port: 1883
QoS: 0 (기본)
Retain: False
```

#### Topic 네이밍 규칙

```
패턴: cradle/{agent_uuid}/{data_type}

예시:
- cradle/cradle-abc-123/frame
- cradle/cradle-abc-123/temperature
- cradle/cradle-abc-123/direction
- cradle/cradle-abc-123/crying
- cradle/cradle-abc-123/servo
```

#### 메시지 포맷

##### 영상 프레임

```json
{
  "frame": "base64_encoded_jpeg",
  "timestamp": "2025-10-03 12:34:56"
}
```

##### 체온

```json
{
  "temperature": "36.5"
}
```

##### 얼굴 방향

```json
{
  "direction": "정면 유지 중",
  "timestamp": "2025-10-03 12:34:56"
}
```

##### 울음 상태

```json
{
  "status": "Crying",
  "probability": 0.89,
  "timestamp": "2025-10-03 12:34:56"
}
```

##### 모터 제어

```json
{
  "action": "start"
}
```

### 2. HTTP REST API

#### 인증

```
세션 기반 인증 (Flask Session)
- 로그인 시 세션 생성
- 쿠키에 세션 ID 저장
- 서버에서 세션 유효성 검증
```

#### 요청/응답 포맷

##### 성공 응답

```json
{
  "success": true,
  "data": { ... },
  "message": "Success"
}
```

##### 오류 응답

```json
{
  "success": false,
  "error": "Error message",
  "code": 400
}
```

#### CORS 설정

```python
# 모바일 앱 허용
CORS(app, supports_credentials=True)
```

---

## 데이터베이스 스키마

### ERD 개요

```
User (사용자)
  │
  │ 1:N
  ↓
UserAgent (사용자-요람 연결)
  │
  │ N:1
  ↓
Agent (요람)
  │
  ├─ 1:N → SensorData (센서 데이터)
  ├─ 1:N → VideoFrame (영상 프레임)
  ├─ 1:N → AlertLog (알림 로그)
  └─ 1:1 → AlertSettings (알림 설정)
```

### 테이블 상세

#### 1. User (사용자)

```sql
CREATE TABLE user (
  id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(80) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. Agent (요람)

```sql
CREATE TABLE agent (
  id INT PRIMARY KEY AUTO_INCREMENT,
  uuid VARCHAR(100) UNIQUE NOT NULL,
  name VARCHAR(100),
  ip VARCHAR(50),
  status VARCHAR(20) DEFAULT 'offline',
  registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. UserAgent (사용자-요람 연결)

```sql
CREATE TABLE user_agent (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  agent_id INT NOT NULL,
  assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user(id),
  FOREIGN KEY (agent_id) REFERENCES agent(id)
);
```

#### 4. SensorData (센서 데이터)

```sql
CREATE TABLE sensor_data (
  id INT PRIMARY KEY AUTO_INCREMENT,
  agent_id INT NOT NULL,
  temperature FLOAT,
  direction VARCHAR(50),
  crying_status VARCHAR(20),
  crying_probability FLOAT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (agent_id) REFERENCES agent(id)
);
```

#### 5. VideoFrame (영상 프레임)

```sql
CREATE TABLE video_frames (
  id INT PRIMARY KEY AUTO_INCREMENT,
  agent_id INT NOT NULL,
  frame LONGBLOB,  -- Base64 인코딩된 JPEG
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (agent_id) REFERENCES agent(id),
  INDEX idx_timestamp (timestamp)
);
```

#### 6. AlertLog (알림 로그)

```sql
CREATE TABLE alert_logs (
  id INT PRIMARY KEY AUTO_INCREMENT,
  agent_id INT NOT NULL,
  user_id INT NOT NULL,
  alert_type VARCHAR(50) NOT NULL,  -- high_temperature, abnormal_position, crying
  message TEXT,
  is_resolved BOOLEAN DEFAULT FALSE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  resolved_at DATETIME,
  FOREIGN KEY (agent_id) REFERENCES agent(id),
  FOREIGN KEY (user_id) REFERENCES user(id),
  INDEX idx_created_at (created_at)
);
```

#### 7. AlertSettings (알림 설정)

```sql
CREATE TABLE alert_settings (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  agent_id INT NOT NULL,
  max_temperature FLOAT DEFAULT 38.0,
  abnormal_position_timeout INT DEFAULT 30,  -- 초
  crying_duration_threshold INT DEFAULT 30,   -- 초
  push_notifications_enabled BOOLEAN DEFAULT TRUE,
  email_notifications_enabled BOOLEAN DEFAULT FALSE,
  push_endpoint TEXT,
  push_p256dh TEXT,
  push_auth TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user(id),
  FOREIGN KEY (agent_id) REFERENCES agent(id),
  UNIQUE KEY unique_user_agent (user_id, agent_id)
);
```

### 인덱스 전략

```sql
-- 자주 조회되는 컬럼에 인덱스
CREATE INDEX idx_agent_uuid ON agent(uuid);
CREATE INDEX idx_sensor_timestamp ON sensor_data(timestamp);
CREATE INDEX idx_video_timestamp ON video_frames(timestamp);
CREATE INDEX idx_alert_created_at ON alert_logs(created_at);
CREATE INDEX idx_alert_resolved ON alert_logs(is_resolved);
```

### 데이터 정리 정책

```bash
# Cron Job (매일 새벽 3시)
# 10일 이상된 비디오 프레임 삭제
DELETE FROM video_frames 
WHERE timestamp < DATE_SUB(NOW(), INTERVAL 10 DAY);

# 30일 이상된 센서 데이터 삭제 (선택적)
DELETE FROM sensor_data 
WHERE timestamp < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

---

## 보안 및 인증

### 1. 사용자 인증

#### 비밀번호 보안

```python
# Werkzeug 보안 라이브러리 사용
from werkzeug.security import generate_password_hash, check_password_hash

# 회원가입 시
password_hash = generate_password_hash(password, method='pbkdf2:sha256')

# 로그인 시
is_valid = check_password_hash(stored_hash, input_password)
```

#### 세션 관리

```python
# Flask Session
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# 로그인 시
session['user_id'] = user.id
session['username'] = user.username

# 로그아웃 시
session.clear()
```

### 2. API 보안

#### 인증 확인 데코레이터

```python
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function
```

#### CORS 설정

```python
# 특정 도메인만 허용 (프로덕션 환경)
CORS(app, 
     origins=['http://www.smartcradle.kro.kr'],
     supports_credentials=True)
```

### 3. MQTT 보안

#### 현재 설정

```yaml
# 개발 환경 (allow_anonymous: true)
listener 1883
allow_anonymous true
```

#### 프로덕션 권장 설정

```yaml
# 인증 활성화
listener 1883
allow_anonymous false
password_file /mosquitto/config/passwd

# TLS/SSL 설정 (선택)
listener 8883
certfile /mosquitto/certs/server.crt
keyfile /mosquitto/certs/server.key
cafile /mosquitto/certs/ca.crt
```

### 4. 데이터베이스 보안

#### 연결 보안

```python
# 환경 변수로 credential 관리
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_HOST = os.getenv('MYSQL_HOST')

# SQLAlchemy 연결
SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:3306/smartcradle'
```

#### 방화벽 규칙

```bash
# GCP Firewall Rules
- MySQL: 3306 (내부 IP만 허용)
- MQTT: 1883 (에이전트 IP만 허용)
- HTTP: 80 (전체 허용)
- HTTPS: 443 (전체 허용, 권장)
```

---

## 배포 구조

### GCP 인프라 (Terraform)

#### 리소스 구성

```
GCP Project: smart-cradle
Region: asia-northeast3 (Seoul)

Resources:
  ├─ VPC Network
  │   └─ Subnet: 10.128.0.0/20
  │
  ├─ Compute Instances
  │   ├─ smart-cradle-server (e2-medium)
  │   │   ├─ Ubuntu 22.04
  │   │   ├─ Docker + Docker Compose
  │   │   └─ Public IP
  │   │
  │   └─ smart-cradle-db (e2-medium)
  │       ├─ Ubuntu 22.04
  │       ├─ MySQL 8.0
  │       └─ Internal IP
  │
  └─ Firewall Rules
      ├─ allow-http (0.0.0.0/0 → 80)
      ├─ allow-https (0.0.0.0/0 → 443)
      ├─ allow-mqtt (에이전트 → 1883)
      └─ allow-mysql (내부 → 3306)
```

#### 서버 인스턴스 구조

```
smart-cradle-server
  │
  ├─ Docker Compose Services
  │   ├─ web (Flask + Gunicorn)
  │   │   └─ Image: joohyun7818/smart-cradle-flask:latest
  │   │
  │   └─ mosquitto (MQTT Broker)
  │       └─ Image: eclipse-mosquitto:2
  │
  ├─ Scripts
  │   └─ cleanup_old_frames.py (Cron: 매일 03:00)
  │
  └─ Logs
      └─ cleanup.log
```

#### DB 인스턴스 구조

```
smart-cradle-db
  │
  ├─ MySQL 8.0
  │   ├─ Database: smartcradle
  │   ├─ User: sc_user
  │   └─ Bind: 0.0.0.0:3306
  │
  ├─ Backups
  │   ├─ daily_backup.sh (Cron: 매일 02:00)
  │   └─ /home/backups/*.sql (7일 보관)
  │
  └─ Configuration
      └─ /etc/mysql/mysql.conf.d/mysqld.cnf
```

### 배포 프로세스

#### 1. Docker 이미지 빌드

```bash
# 멀티 아키텍처 이미지 빌드
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t joohyun7818/smart-cradle-flask:latest \
  --push .
```

#### 2. Terraform 배포

```bash
cd terraform

# 초기화
terraform init

# 계획 확인
terraform plan

# 배포
terraform apply
```

#### 3. 자동 설정 내역

```
✅ Docker 컨테이너 자동 시작
✅ MySQL 데이터베이스 및 사용자 생성
✅ 외부 연결 허용 설정
✅ 매일 새벽 2시 DB 백업 (7일 보관)
✅ 매일 새벽 3시 오래된 프레임 삭제 (10일 이상)
✅ MQTT Broker 자동 시작
✅ 방화벽 규칙 자동 설정
```

### 모니터링

#### 서버 상태 확인

```bash
# SSH 접속
ssh smart-cradle-server

# 컨테이너 상태
cd /opt/smart-cradle
sudo docker compose ps

# 로그 확인
sudo docker compose logs web --tail=100
sudo docker compose logs mosquitto --tail=100
```

#### 데이터베이스 확인

```bash
# SSH 접속
ssh smart-cradle-db

# MySQL 접속
mysql -u sc_user -p smartcradle

# 테이블 상태
SHOW TABLES;
SELECT COUNT(*) FROM sensor_data;
SELECT COUNT(*) FROM video_frames;
```

### 스케일링 고려사항

#### 수평 확장

```
현재: 단일 서버 구조
개선: 
  ├─ Load Balancer (GCP Load Balancing)
  ├─ 다중 Flask 인스턴스 (Auto Scaling)
  └─ MQTT Broker 클러스터링
```

#### 데이터베이스 최적화

```
현재: 단일 MySQL 인스턴스
개선:
  ├─ Read Replica (읽기 분산)
  ├─ Connection Pooling
  └─ 쿼리 최적화
```

#### 저장소 최적화

```
현재: MySQL LONGBLOB (영상 프레임)
개선:
  ├─ Google Cloud Storage (영상 저장)
  ├─ CDN 활용 (스트리밍)
  └─ Redis (캐싱)
```

---

## 개발 환경

### 로컬 개발 설정

#### 서버 실행

```bash
cd smart_cradle_server

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집

# 가상환경 생성 및 패키지 설치
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 개발 서버 실행
python smart_cradle_server.py
```

#### 모바일 앱 실행

```bash
cd SmartCradleApp

# 패키지 설치
npm install

# Expo 개발 서버 시작
npx expo start

# iOS 시뮬레이터
npx expo start --ios

# Android 에뮬레이터
npx expo start --android
```

#### 에이전트 실행 (Raspberry Pi)

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate

# 패키지 설치
pip install opencv-python requests paho-mqtt Pillow picamera2 \
            sounddevice soundfile librosa joblib mediapipe numpy

# 실행
python smart_cradle_agent.py
```

### 환경 변수

#### 서버 (.env)

```bash
MYSQL_USER=sc_user
MYSQL_PASSWORD=your_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=smartcradle
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
SECRET_KEY=your-secret-key-here
```

#### 에이전트 (smart_cradle_agent.py)

```python
SERVER_URL = 'http://localhost'
CRADLE_UUID = 'cradle-unique-id-example'
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
```

---

## 트러블슈팅

### 일반적인 문제

#### 1. MQTT 연결 실패

```bash
# Broker 상태 확인
sudo docker compose logs mosquitto

# 포트 확인
netstat -an | grep 1883

# 방화벽 확인
sudo ufw status
```

#### 2. 데이터베이스 연결 오류

```bash
# MySQL 서비스 상태
sudo systemctl status mysql

# 연결 테스트
mysql -u sc_user -p -h 10.128.0.2

# 로그 확인
sudo tail -f /var/log/mysql/error.log
```

#### 3. Docker 컨테이너 오류

```bash
# 컨테이너 상태
sudo docker compose ps

# 로그 확인
sudo docker compose logs --tail=200

# 재시작
sudo docker compose restart

# 완전 재배포
sudo docker compose down
sudo docker compose pull
sudo docker compose up -d
```

#### 4. 영상 스트리밍 끊김

```bash
# 에이전트 로그 확인
python smart_cradle_agent.py

# MQTT 메시지 구독 테스트
mosquitto_sub -h localhost -t "cradle/+/frame"

# 네트워크 대역폭 확인
iftop
```

---

## 성능 최적화

### 현재 성능 지표

```
영상 스트리밍: 10 FPS, 640x480, JPEG 80%
센서 데이터: 1초 간격
데이터베이스: 단일 인스턴스
동시 접속: ~10 사용자
```

### 최적화 방안

#### 1. 영상 전송 최적화

```python
# 프레임 압축률 조정
cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])

# 해상도 조정
config = picam2.create_video_configuration(main={"size": (320, 240)})

# 프레임레이트 동적 조정
if network_bandwidth < threshold:
    frame_interval = 0.2  # 5 FPS
```

#### 2. 데이터베이스 최적화

```sql
-- 오래된 데이터 파티셔닝
ALTER TABLE sensor_data 
PARTITION BY RANGE (YEAR(timestamp)) (
  PARTITION p2024 VALUES LESS THAN (2025),
  PARTITION p2025 VALUES LESS THAN (2026)
);

-- 인덱스 최적화
CREATE INDEX idx_composite ON sensor_data(agent_id, timestamp);
```

#### 3. 캐싱 전략

```python
# Redis 캐싱 (최근 센서 데이터)
import redis
r = redis.Redis(host='localhost', port=6379)

def get_sensor_data(agent_uuid):
    cached = r.get(f'sensor:{agent_uuid}')
    if cached:
        return json.loads(cached)
    # DB 조회
    data = db.query(...)
    r.setex(f'sensor:{agent_uuid}', 60, json.dumps(data))
    return data
```

---

## 향후 개선 사항

### 단기 개선 (1-3개월)

- [ ] HTTPS 적용 (Let's Encrypt)
- [ ] MQTT 인증 활성화
- [ ] 웹 푸시 알림 구현
- [ ] 이메일 알림 구현
- [ ] Redis 캐싱 도입

### 중기 개선 (3-6개월)

- [ ] Google Cloud Storage 활용 (영상 저장)
- [ ] Load Balancer 적용
- [ ] Auto Scaling 구현
- [ ] Monitoring (Prometheus + Grafana)
- [ ] 로그 수집 (ELK Stack)

### 장기 개선 (6개월 이상)

- [ ] AI 모델 개선 (얼굴 인식 정확도)
- [ ] 수면 패턴 분석 기능
- [ ] 건강 상태 예측 AI
- [ ] 음성 명령 기능
- [ ] 다국어 지원

---

## 참고 문서

### 기술 스택 문서

- [Flask Documentation](https://flask.palletsprojects.com/)
- [React Native Documentation](https://reactnative.dev/)
- [MQTT Protocol](https://mqtt.org/)
- [MediaPipe Face Mesh](https://google.github.io/mediapipe/solutions/face_mesh.html)
- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)

### API 레퍼런스

- [Flask RESTful API Guide](https://flask-restful.readthedocs.io/)
- [Paho MQTT Python](https://www.eclipse.org/paho/index.php?page=clients/python/index.php)

### 프로젝트 문서

- [README.md](./README.md) - 프로젝트 개요
- [terraform/README.md](./terraform/README.md) - 인프라 배포 상세

---

**문서 버전**: 1.0
**최종 업데이트**: 2025년 10월 3일
**작성자**: 임주현
