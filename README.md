# SmartCradleApp - React Native Mobile Application

React Native + Expo 기반 스마트 요람 모니터링 모바일 애플리케이션입니다.

## 📱 기술 스택

- **Framework**: React Native + Expo
- **Language**: TypeScript
- **State Management**: Redux Toolkit (@reduxjs/toolkit)
- **Navigation**: React Navigation
- **HTTP Client**: Axios
- **UI Components**: React Native Paper

## 🔌 API 엔드포인트

### 인증 (Authentication)

#### 1. 로그인
```typescript
POST /login
Content-Type: application/json

Request:
{
  "username": "string",
  "password": "string"
}

Response (200 OK):
{
  "success": true,
  "message": "로그인 성공",
  "user": {
    "id": number,
    "username": "string"
  }
}

Error (401):
{
  "success": false,
  "message": "아이디 또는 비밀번호가 틀렸습니다."
}
```

#### 2. 회원가입
```typescript
POST /register
Content-Type: application/json

Request:
{
  "username": "string",
  "password": "string"
}

Response (201 Created):
{
  "success": true,
  "message": "회원가입이 완료되었습니다."
}

Error (400):
{
  "success": false,
  "message": "이미 사용 중인 아이디입니다."
}
```

#### 3. 로그아웃
```typescript
POST /logout

Response (200 OK):
{
  "success": true,
  "message": "로그아웃 되었습니다."
}
```

### 요람 관리 (Cradle Management)

#### 4. 요람 목록 조회
```typescript
GET /api/agents

Response (200 OK):
[
  {
    "id": number,
    "uuid": "string",
    "ip": "string",
    "created_at": "ISO8601 string",
    "updated_at": "ISO8601 string"
  }
]
```

#### 5. 요람 등록 (QR 스캔)
```typescript
POST /register_cradle
Content-Type: application/json

Request:
{
  "cradle_uuid": "string"
}

Response (200 OK):
{
  "success": true,
  "message": "요람이 등록되었습니다.",
  "agent": {
    "id": number,
    "uuid": "string",
    "ip": "string",
    "created_at": "ISO8601 string",
    "updated_at": "ISO8601 string"
  }
}

Error (404):
{
  "success": false,
  "message": "등록되지 않은 UUID입니다."
}
```

#### 6. 요람 선택
```typescript
POST /select_cradle
Content-Type: application/json

Request:
{
  "uuid": "string"
}

Response (200 OK):
{
  "success": true,
  "message": "요람이 선택되었습니다."
}
```

#### 7. 요람 삭제
```typescript
POST /delete_cradle
Content-Type: application/json

Request:
{
  "uuid": "string"
}

Response (200 OK):
{
  "success": true,
  "message": "요람이 삭제되었습니다."
}
```

### 모니터링 (Monitoring)

#### 8. 요람 실시간 상태 조회
```typescript
GET /api/agent_status/{uuid}

Response (200 OK):
{
  "agent_uuid": "string",
  "temperature": number | null,
  "crying": "Crying" | "Not Crying" | null,
  "direction": "정면 유지 중" | "좌측으로 움직임" | "우측으로 움직임" | "인식 안됨" | null,
  "face_direction": string | null,
  "last_direction_time": "ISO8601 string" | null,
  "last_normal_face_time": "ISO8601 string" | null,
  "last_update": "ISO8601 string" | null
}
```

#### 9. 센서 데이터 조회 (기간별)
```typescript
GET /api/sensor_data/{uuid}?start_date={start}&end_date={end}

Query Parameters:
- start_date: ISO8601 datetime string
- end_date: ISO8601 datetime string

Response (200 OK):
[
  {
    "timestamp": "ISO8601 string",
    "temperature": number | null,
    "crying": "Crying" | "Not Crying" | null,
    "direction": "정면 유지 중" | "좌측으로 움직임" | "우측으로 움직임" | "인식 안됨" | null
  }
]
```

#### 10. 비디오 스트림 URL
```typescript
GET /stream/{uuid}

Response: multipart/x-mixed-replace (MJPEG stream)
Content-Type: multipart/x-mixed-replace; boundary=frame
```

### 알림 (Alerts)

#### 11. 알림 로그 조회
```typescript
GET /api/alert_logs

Response (200 OK):
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
    "created_at": "ISO8601 string",
    "resolved_at": "ISO8601 string" | null
  }
]
```

#### 12. 알림 해결 처리
```typescript
POST /api/alert_logs/{log_id}/resolve

Response (200 OK):
{
  "success": true
}
```

#### 13. 알림 히스토리 조회 (요람별)
```typescript
GET /api/alert_history/{uuid}

Response (200 OK):
[
  {
    "id": number,
    "alert_type": "string",
    "alert_message": "string",
    "temperature": number | null,
    "face_detected": boolean | null,
    "resolved": boolean,
    "created_at": "ISO8601 string",
    "resolved_at": "ISO8601 string" | null
  }
]
```

#### 14. 알림 상세 정보 조회
```typescript
GET /api/alert_detail/{alert_id}

Response (200 OK):
{
  "alert": {
    "id": number,
    "alert_type": "string",
    "alert_message": "string",
    "temperature": number | null,
    "face_detected": boolean | null,
    "resolved": boolean,
    "created_at": "ISO8601 string",
    "resolved_at": "ISO8601 string" | null
  },
  "sensor_data": [...],
  "video_frames": [
    {
      "id": number,
      "timestamp": "ISO8601 string"
    }
  ],
  "total_frames": number
}
```

#### 15. 알림 프레임 이미지
```typescript
GET /api/alert_frame/{frame_id}

Response: image/jpeg
```

### 알림 설정 (Alert Settings)

#### 16. 알림 설정 조회
```typescript
GET /api/alert_settings/{uuid}

Response (200 OK):
{
  "max_temperature": number,              // 최대 온도 (°C)
  "abnormal_position_timeout": number,    // 비정상 자세 허용 시간 (초)
  "crying_duration_threshold": number,    // 울음 알림 임계값 (초)
  "push_notifications_enabled": boolean,
  "email_notifications_enabled": boolean
}
```

#### 17. 알림 설정 업데이트
```typescript
POST /api/alert_settings/{uuid}
Content-Type: application/json

Request:
{
  "max_temperature": number,
  "abnormal_position_timeout": number,
  "crying_duration_threshold": number,
  "push_notifications_enabled": boolean,
  "email_notifications_enabled": boolean
}

Response (200 OK):
{
  "success": true
}
```

### 제어 (Control)

#### 18. 모터 제어
```typescript
POST /control_motor/{uuid}
Content-Type: application/json

Request:
{
  "action": "start" | "stop"
}

Response (200 OK):
{
  "success": true
}

Error (500):
{
  "success": false,
  "message": "MQTT 메시지 전송 실패"
}
```

### 비디오 (Video)

#### 19. 녹화 영상 조회
```typescript
GET /api/video/{uuid}?date={date}&time={time}

Query Parameters:
- date: YYYY-MM-DD format
- time: HH:MM:SS format

Response: video/mp4
```

## 🔐 인증 방식

**Session-based Authentication**
- 로그인 시 서버에서 세션 쿠키 발급
- 모든 API 요청에 `withCredentials: true` 옵션 필요
- 세션 쿠키는 서버 측에서 자동 관리

```typescript
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  withCredentials: true,  // 세션 쿠키 전송
  headers: {
    'Content-Type': 'application/json',
  },
});
```

## � 프로젝트 구조

```
SmartCradleApp/
├── src/
│   ├── components/          # 재사용 가능한 컴포넌트
│   │   ├── QRScanner.tsx    # QR 코드 스캐너
│   │   └── VideoStream.tsx  # 실시간 영상 스트림
│   ├── navigation/          # 네비게이션 설정
│   │   └── AppNavigator.tsx
│   ├── screens/             # 화면 컴포넌트
│   │   ├── LoginScreen.tsx
│   │   ├── RegisterScreen.tsx
│   │   ├── DashboardScreen.tsx
│   │   ├── AgentSelectionScreen.tsx
│   │   ├── RegisterCradleScreen.tsx
│   │   ├── AlertsScreen.tsx
│   │   ├── AlertDetailScreen.tsx
│   │   ├── HistoryScreen.tsx
│   │   └── SettingsScreen.tsx
│   ├── services/            # API 서비스
│   │   └── api.ts           # Axios API 클라이언트
│   ├── store/               # Redux 상태 관리
│   │   ├── index.ts         # Store 설정
│   │   ├── authSlice.ts     # 인증 상태
│   │   └── agentSlice.ts    # 요람 상태
│   └── types/               # TypeScript 타입 정의
│       └── index.ts
├── App.tsx                  # 앱 진입점
├── index.ts
├── package.json
└── tsconfig.json
```

## � 시작하기

### 1. 의존성 설치
```bash
npm install
# or
yarn install
```

### 2. 개발 서버 실행
```bash
npx expo start
```

### 3. 앱 실행
- **iOS**: `i` 키 (iOS 시뮬레이터 필요)
- **Android**: `a` 키 (Android 에뮬레이터 필요)
- **웹**: `w` 키
- **Expo Go**: QR 코드 스캔

## 🌐 API 서버 URL

```typescript
const API_BASE_URL = 'http://www.smartcradle.kro.kr';
```

도메인을 사용하여 서버 IP 변경에 영향받지 않습니다.

## 📊 상태 관리 (Redux)

### Auth Slice
```typescript
// 인증 상태
interface AuthState {
  user: User | null;
  isLoggedIn: boolean;
}
```

### Agent Slice
```typescript
// 요람 상태
interface AgentState {
  agents: Agent[];
  selectedAgent: Agent | null;
  loading: boolean;
}
```

## 🛠 주요 기능

1. **인증 시스템**: 회원가입, 로그인, 로그아웃
2. **QR 코드 등록**: 카메라로 요람 UUID 스캔하여 등록
3. **실시간 모니터링**: 온도, 얼굴 방향, 울음 감지 상태 표시
4. **비디오 스트리밍**: MJPEG 스트림으로 실시간 영상 확인
5. **알림 관리**: 고온, 비정상 자세, 울음 알림 수신 및 확인
6. **히스토리 조회**: 센서 데이터 그래프, 알림 로그 조회
7. **알림 설정**: 온도 임계값, 울음 감지 시간 등 커스터마이징
8. **원격 제어**: 모터 시작/정지 제어

## 📝 개발 참고사항

- **세션 쿠키**: 모든 API 요청에 `withCredentials: true` 필수
- **타임아웃**: API 요청 타임아웃은 10초로 설정
- **에러 처리**: Axios interceptor로 전역 에러 처리 권장
- **이미지 URL**: 스트리밍은 MJPEG, 프레임은 직접 URL 참조

## 🔧 환경 변수

앱에서 직접 하드코딩된 API URL 대신 환경 변수 사용 권장:

```typescript
// .env 파일 생성 후
const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://www.smartcradle.kro.kr';
```

## 📦 빌드

### iOS
```bash
eas build --platform ios
```

### Android
```bash
eas build --platform android
```

자세한 빌드 가이드는 [Expo 공식 문서](https://docs.expo.dev/build/introduction/) 참조.
- 10초마다 자동 새로고침

### 4. 알림 설정
- 최대 체온 임계값 설정 (기본: 38.0°C)
- 비정상 자세 허용 시간 설정 (기본: 30초)
- 푸시 알림 활성화/비활성화
- 이메일 알림 활성화/비활성화

## 🛠 기술 스택

- **React Native**: 하이브리드 앱 프레임워크
- **Expo**: React Native 개발 플랫폼
- **TypeScript**: 타입 안전성
- **Redux Toolkit**: 상태 관리
- **React Navigation**: 네비게이션
- **Axios**: HTTP 클라이언트

## 📦 설치된 패키지

```json
{
  "@react-navigation/native": "네비게이션 코어",
  "@react-navigation/stack": "스택 네비게이션",
  "@react-navigation/bottom-tabs": "하단 탭 네비게이션",
  "@react-navigation/native-stack": "네이티브 스택",
  "@reduxjs/toolkit": "Redux 상태 관리",
  "react-redux": "React-Redux 바인딩",
  "axios": "HTTP 클라이언트",
  "expo-av": "오디오/비디오 재생",
  "react-native-chart-kit": "차트 라이브러리",
  "react-native-svg": "SVG 지원",
  "react-native-screens": "네이티브 스크린",
  "react-native-safe-area-context": "안전 영역 처리"
}
```

## 🚀 실행 방법

### 1. 패키지 설치
```bash
cd SmartCradleApp
npm install
```

### 2. 개발 서버 실행

#### iOS (Mac에서만 가능)
```bash
npm run ios
```

#### Android
```bash
npm run android
```

#### 웹 브라우저
```bash
npm run web
```

#### Expo Go 앱 사용
```bash
npm start
```
그런 다음 Expo Go 앱에서 QR 코드를 스캔하세요.

## 🌐 서버 연결 설정

`src/services/api.ts` 파일에서 서버 URL을 수정하세요:

```typescript
const API_BASE_URL = 'http://www.smartcradle.kro.kr';  // 도메인 사용 (권장)
// 또는 IP 직접 사용: 'http://34.64.93.207'
```

### 로컬 개발 시
- iOS Simulator: `http://localhost` 또는 도메인/서버 IP
- Android Emulator: `http://10.0.2.2` (localhost 대신)
- 실제 기기: 도메인 사용 권장 (http://www.smartcradle.kro.kr)

## 📝 API 엔드포인트

앱이 사용하는 서버 API:

```
POST /login                          # 로그인
POST /register                       # 회원가입
GET  /logout                         # 로그아웃
GET  /api/agent_status/<uuid>        # 실시간 상태 조회
GET  /api/sensor_data/<uuid>         # 센서 데이터 조회
GET  /api/alert_logs                 # 알림 로그 조회
POST /api/alert_logs/<id>/resolve    # 알림 해결
POST /api/alert_settings/<uuid>      # 알림 설정 업데이트
GET  /api/video/<uuid>               # 비디오 스트림
```

## 🎨 화면 구성

### 1. 로그인 화면
- 사용자 인증
- 회원가입 링크

### 2. 대시보드 (메인 화면)
- 실시간 체온 표시
  - 정상 (녹색): < 37°C
  - 주의 (노랑): 37-38°C
  - 위험 (빨강): > 38°C
- 얼굴 방향 상태
  - ✅ 정면 유지 중 (녹색)
  - ⚠️ 좌측/우측 움직임 (노랑)
  - ❌ 인식 안됨/오류 (빨강)
- 울음 감지 상태
- 요람 정보

### 3. 알림 화면
- 알림 기록 목록
- 알림 유형별 시각적 구분
- 해결/미해결 상태 표시
- 알림 해결 버튼

### 4. 설정 화면
- 온도 임계값 조정
- 자세 감지 시간 설정
- 알림 ON/OFF
- 도움말 정보

## 🔧 개발 중 주의사항

### 1. CORS 이슈
서버에서 CORS 설정이 필요합니다:

```python
from flask_cors import CORS
CORS(app, origins=['*'])  # 개발 환경
```

### 2. 세션 쿠키
Axios 설정에 `withCredentials: true` 포함 필요

### 3. 네트워크 연결
- 실제 기기 테스트 시 같은 WiFi 네트워크 사용
- 또는 외부에서 접근 가능한 서버 IP 사용

## 📱 빌드 및 배포

### Android APK 빌드
```bash
eas build --platform android
```

### iOS 빌드 (Mac 필요)
```bash
eas build --platform ios
```

### 앱 스토어 제출
Expo EAS를 사용하여 빌드 및 제출:
```bash
eas submit --platform android
eas submit --platform ios
```

## 🐛 문제 해결

### 1. 연결 오류
- 서버 URL 확인
- 서버가 실행 중인지 확인
- 방화벽 설정 확인

### 2. 로그인 실패
- 네트워크 연결 확인
- 서버 로그 확인
- CORS 설정 확인

### 3. 실시간 업데이트 안됨
- MQTT 브로커 상태 확인
- 에이전트 연결 상태 확인
- 서버 로그 확인

## 🔮 향후 개발 계획

1. **푸시 알림**
   - Firebase Cloud Messaging 통합
   - 백그라운드 알림 처리

2. **비디오 스트리밍**
   - 실시간 영상 보기
   - 녹화 영상 재생

3. **통계 및 차트**
   - 온도 변화 그래프
   - 수면 패턴 분석
   - 일일/주간/월간 리포트

4. **다국어 지원**
   - 한국어/영어

5. **다크 모드**
   - 시스템 설정 연동

6. **오프라인 모드**
   - 로컬 데이터 캐싱
   - 오프라인 알림 기록

## 📄 라이선스

MIT License

## 👥 개발자

DMU 6team

## 📞 지원

문제가 발생하면 GitHub Issues에 등록해주세요.
# Smart-Cradle-Service
