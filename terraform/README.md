# terraform - GCP Infrastructure as Code# terraform - GCP Infrastructure as Code# terraform - GCP Infrastructure as Code# terraform - GCP Infrastructure as Code# 🏗️ 스마트 요람 시스템 아키텍처 & 인프라 구축 가이드



Terraform을 사용하여 Google Cloud Platform에 스마트 요람 시스템 인프라를 자동으로 구축합니다.



## 사용하는 GCP 서비스Terraform을 사용하여 Google Cloud Platform에 스마트 요람 시스템 인프라를 자동으로 프로비저닝합니다.



### 네트워크

- **VPC Network**: `smart-cradle-network`

- **Subnet**: `10.128.0.0/20` (asia-northeast3)## 프로비저닝되는 GCP 서비스Terraform을 사용하여 Google Cloud Platform에 스마트 요람 시스템 인프라를 자동으로 프로비저닝합니다.

- **Firewall Rules**: 

  - SSH (22)

  - HTTP (80)

  - MQTT (1883)### 1. VPC Network (네트워크)

  - MySQL (3306, 내부만)



### 컴퓨팅

- **서버 인스턴스** (smart-cradle-server)**리소스**: `google_compute_network.smart_cradle_network`## 🏗️ 프로비저닝되는 리소스Terraform을 사용하여 Google Cloud Platform에 스마트 요람 시스템 인프라를 자동으로 프로비저닝합니다.## 🎯 시스템 아키텍처 개요

  - 머신: e2-medium (2 vCPU, 4GB RAM)

  - OS: Ubuntu 22.04 LTS

  - 디스크: 30GB

  - 설치: Docker, Flask, Mosquitto- 이름: `smart-cradle-network`



- **DB 인스턴스** (smart-cradle-db)- 설명: 스마트 요람 시스템 전용 Virtual Private Cloud

  - 머신: e2-medium (2 vCPU, 4GB RAM)

  - OS: Ubuntu 22.04 LTS- 자동 서브넷 생성: `false` (수동 관리)### 1. 네트워킹 (Networking)

  - 디스크: 20GB

  - 설치: MySQL 8.0



## 변수 설정### 2. Subnet (서브넷)



`terraform.tfvars` 파일 생성:



```hcl**리소스**: `google_compute_subnetwork.smart_cradle_subnet`#### VPC Network## 🏗️ 프로비저닝되는 리소스스마트 요람 시스템은 **마이크로서비스 아키텍처**를 기반으로 한 **IoT 플랫폼**입니다. 클라우드 네이티브 설계를 통해 확장성과 안정성을 보장합니다.

project_id           = "your-gcp-project-id"

region               = "asia-northeast3"

zone                 = "asia-northeast3-a"

mysql_root_password  = "your-root-password"- 이름: `smart-cradle-subnet`- **리소스**: `google_compute_network.smart_cradle_network`

mysql_password       = "your-user-password"

secret_key           = "your-secret-key"- CIDR 범위: `10.128.0.0/20` (4,096개 IP 주소)

docker_image         = "yourdockerhub/smart-cradle-server:latest"

```- 리전: `asia-northeast3` (서울)- **이름**: `smart-cradle-network`



## 실행 방법



### 1. 사전 준비### 3. Firewall Rules (방화벽 규칙)- **설명**: 스마트 요람 시스템 전용 Virtual Private Cloud



```bash

# GCP 인증

gcloud auth application-default login#### SSH 접근 규칙- **자동 서브넷 생성**: `false` (수동 관리)### 1. **네트워킹 (Networking)**### 🏛️ 전체 시스템 아키텍처



# API 활성화- 이름: `smart-cradle-allow-ssh`

gcloud services enable compute.googleapis.com

- 프로토콜: TCP

# SSH 키 생성 (선택)

ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa- 포트: `22`

```

- 소스: `0.0.0.0/0`#### Subnet

### 2. 배포

- 대상 태그: `smart-cradle-server`, `smart-cradle-db`

```bash

# 초기화- **리소스**: `google_compute_subnetwork.smart_cradle_subnet`

cd terraform/

terraform init#### HTTP 접근 규칙



# 변수 파일 작성- 이름: `smart-cradle-allow-http`- **이름**: `smart-cradle-subnet`#### VPC Network```

cp terraform.tfvars.example terraform.tfvars

nano terraform.tfvars- 프로토콜: TCP



# 배포 실행- 포트: `80`- **CIDR 범위**: `10.128.0.0/20` (4,096 IP 주소)

terraform apply

```- 소스: `0.0.0.0/0`



### 3. 확인- 대상 태그: `smart-cradle-server`- **리전**: `asia-northeast3` (서울)- **리소스**: `google_compute_network.smart_cradle_network`┌─────────────────────────────────────────────────────────────────────┐



```bash

# 배포된 IP 확인

terraform output#### MQTT 접근 규칙



# 웹 서비스 테스트- 이름: `smart-cradle-allow-mqtt`

curl http://$(terraform output -raw server_instance_external_ip)

- 프로토콜: TCP### 2. 방화벽 규칙 (Firewall Rules)- **이름**: `smart-cradle-network`│                        GCP Cloud Platform                          │

# SSH 접속

gcloud compute ssh smart-cradle-server --zone=asia-northeast3-a- 포트: `1883`

```

- 소스: `0.0.0.0/0`

### 4. 삭제

- 대상 태그: `smart-cradle-server`

```bash

# 모든 리소스 삭제#### SSH 접근 규칙- **설명**: 스마트 요람 시스템 전용 Virtual Private Cloud├─────────────────────────────────────────────────────────────────────┤

terraform destroy

```#### MySQL 내부 접근 규칙



## 자동화 스크립트- 이름: `smart-cradle-allow-mysql-internal`- **리소스**: `google_compute_firewall.allow_ssh`



### 서버 인스턴스- 프로토콜: TCP

- **프레임 정리**: 매일 03:00, 10일 이상 된 프레임 삭제

- 포트: `3306`- **이름**: `smart-cradle-allow-ssh`- **자동 서브넷 생성**: `false` (수동 관리)│  ┌─────────────────────┐         ┌─────────────────────────────────┐ │

### DB 인스턴스

- **DB 백업**: 매일 02:00, 7일 보관- 소스 태그: `smart-cradle-server`



## 예상 비용- 대상 태그: `smart-cradle-db`- **프로토콜**: TCP



| 항목 | 비용 |- 보안: VPC 내부 통신만 허용

|------|------|

| 서버 인스턴스 (e2-medium) | $24/월 |- **포트**: `22`│  │   Server Instance   │         │        DB Instance              │ │

| DB 인스턴스 (e2-medium) | $24/월 |

| 스토리지 (50GB) | $2/월 |#### 내부 통신 규칙

| 외부 IP (2개) | $6/월 |

| **총계** | **$56/월** |- 이름: `smart-cradle-allow-internal`- **소스**: `0.0.0.0/0` (전체 인터넷)



## 트러블슈팅- 프로토콜: TCP/UDP/ICMP



### API 오류- 포트: 전체 (`0-65535`)- **대상 태그**: `smart-cradle-server`, `smart-cradle-db`#### Subnet│  │   (10.128.0.3)      │◀────────│       (10.128.0.2)             │ │

```bash

gcloud services enable compute.googleapis.com- 소스: `10.128.0.0/20`

```

- **용도**: 원격 서버 관리 및 디버깅

### 접속 불가

```bash### 4. Compute Engine Instances

# 방화벽 확인

gcloud compute firewall-rules list- **리소스**: `google_compute_subnetwork.smart_cradle_subnet`│  │                     │         │                                 │ │



# 시작 로그 확인#### 서버 인스턴스 (smart-cradle-server)

gcloud compute instances get-serial-port-output smart-cradle-server

```#### HTTP 접근 규칙



### 컨테이너 미실행**리소스**: `google_compute_instance.server_instance`

```bash

# SSH 접속 후- **리소스**: `google_compute_firewall.allow_http`- **이름**: `smart-cradle-subnet`│  │ ┌─────────────────┐ │         │ ┌─────────────────────────────┐ │ │

sudo docker ps

sudo journalctl -u google-startup-scripts.service**사양**:

```

- 머신 타입: `e2-medium` (2 vCPU, 4GB RAM)- **이름**: `smart-cradle-allow-http`

## 참고

- 영역: `asia-northeast3-a`

- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)

- [Google Compute Engine](https://cloud.google.com/compute/docs)- OS 이미지: Ubuntu 22.04 LTS- **프로토콜**: TCP- **CIDR 범위**: `10.128.0.0/20` (4,096 IP 주소)│  │ │ Flask Web App   │ │         │ │       MySQL 8.0             │ │ │


- 부트 디스크: 30GB Standard Persistent Disk

- 외부 IP: Ephemeral (자동 할당)- **포트**: `80`

- 태그: `smart-cradle-server`

- **소스**: `0.0.0.0/0` (전체 인터넷)- **리전**: `asia-northeast3` (서울)│  │ │ (Gunicorn)      │ │         │ │                             │ │ │

**설치되는 서비스**:

1. Docker Engine- **대상 태그**: `smart-cradle-server`

2. Docker Compose

3. Flask Web Application (Gunicorn WSGI)- **용도**: 웹 대시보드 및 API 접근│  │ │ Port: 80        │ │         │ │ Database: smartcradle       │ │ │

   - 포트: 80

4. Mosquitto MQTT Broker

   - 포트: 1883

#### MQTT 접근 규칙### 2. **방화벽 규칙 (Firewall Rules)**│  │ └─────────────────┘ │         │ │ User: sc_user               │ │ │

**자동화**:

- 프레임 정리 스크립트: 매일 03:00 실행 (10일 이상 된 프레임 삭제)- **리소스**: `google_compute_firewall.allow_mqtt`



#### DB 인스턴스 (smart-cradle-db)- **이름**: `smart-cradle-allow-mqtt`│  │                     │         │ │ Tables: users, agents,      │ │ │



**리소스**: `google_compute_instance.db_instance`- **프로토콜**: TCP



**사양**:- **포트**: `1883`#### SSH 접근 규칙│  │ ┌─────────────────┐ │         │ │         sensor_data,        │ │ │

- 머신 타입: `e2-medium` (2 vCPU, 4GB RAM)

- 영역: `asia-northeast3-a`- **소스**: `0.0.0.0/0` (전체 인터넷)

- OS 이미지: Ubuntu 22.04 LTS

- 부트 디스크: 20GB Standard Persistent Disk- **대상 태그**: `smart-cradle-server`- **리소스**: `google_compute_firewall.allow_ssh`│  │ │ MQTT Broker     │ │         │ │         video_frames        │ │ │

- 외부 IP: Ephemeral (자동 할당)

- 태그: `smart-cradle-db`- **용도**: IoT 디바이스 MQTT 통신



**설치되는 서비스**:- **이름**: `smart-cradle-allow-ssh`│  │ │ (Mosquitto)     │ │         │ └─────────────────────────────┘ │ │

1. MySQL 8.0 Server

   - 데이터베이스: `smartcradle`#### MySQL 내부 접근 규칙

   - 사용자: `sc_user`

   - 바인드 주소: `0.0.0.0` (VPC 내부 접근 허용)- **리소스**: `google_compute_firewall.allow_mysql_internal`- **프로토콜**: TCP│  │ │ Port: 1883      │ │         │                                 │ │



**자동화**:- **이름**: `smart-cradle-allow-mysql-internal`

- DB 백업: 매일 02:00 실행

- 백업 보관: 7일 (8일 이상 된 백업 자동 삭제)- **프로토콜**: TCP- **포트**: `22`│  │ └─────────────────┘ │         │ ┌─────────────────────────────┐ │ │



## 변수 (Variables)- **포트**: `3306`



### 필수 변수- **소스 태그**: `smart-cradle-server`- **소스**: `0.0.0.0/0` (전체 인터넷)│  └─────────────────────┘         │ │     Automated Backup        │ │ │



| 변수명 | 타입 | 기본값 | 설명 |- **대상 태그**: `smart-cradle-db`

|--------|------|--------|------|

| project_id | string | - | GCP 프로젝트 ID (필수) |- **용도**: 서버 인스턴스에서 DB 인스턴스로 연결- **대상 태그**: `smart-cradle-server`, `smart-cradle-db`│                                  │ │     Daily at 02:00          │ │ │

| region | string | asia-northeast3 | GCP 리전 |

| zone | string | asia-northeast3-a | GCP 영역 |- **보안**: 내부 통신만 허용

| mysql_root_password | string | - | MySQL root 비밀번호 (필수) |

| mysql_database | string | smartcradle | 데이터베이스 이름 |- **용도**: 원격 서버 관리 및 디버깅│                                  │ │     Cron + mysqldump        │ │ │

| mysql_user | string | sc_user | 데이터베이스 사용자 |

| mysql_password | string | - | 데이터베이스 비밀번호 (필수) |#### 내부 통신 규칙

| ssh_public_key_path | string | ~/.ssh/id_rsa.pub | SSH 공개키 경로 |

| ssh_username | string | admin | SSH 사용자 이름 |- **리소스**: `google_compute_firewall.allow_internal`│                                  │ └─────────────────────────────┘ │ │

| secret_key | string | - | Flask SECRET_KEY (필수) |

| docker_image | string | - | Flask Docker 이미지 (필수) |- **이름**: `smart-cradle-allow-internal`

| server_machine_type | string | e2-medium | 서버 머신 타입 |

| db_machine_type | string | e2-medium | DB 머신 타입 |- **프로토콜**: TCP/UDP/ICMP#### HTTP 접근 규칙│                                  └─────────────────────────────────┘ │



### terraform.tfvars 예시- **포트**: 전체 (`0-65535`)



```hcl- **소스**: `10.128.0.0/20` (VPC 내부)- **리소스**: `google_compute_firewall.allow_http`└─────────────────────────────────────────────────────────────────────┘

project_id           = "your-gcp-project-id"

region               = "asia-northeast3"- **용도**: VPC 내 인스턴스 간 자유로운 통신

zone                 = "asia-northeast3-a"

mysql_root_password  = "SecureRootPassword123!"- **이름**: `smart-cradle-allow-http`                                   │

mysql_database       = "smartcradle"

mysql_user           = "sc_user"### 3. Compute Engine 인스턴스

mysql_password       = "SC_password_12!45"

ssh_public_key_path  = "~/.ssh/id_rsa.pub"- **프로토콜**: TCP                    ┌──────────────┼──────────────┐

ssh_username         = "admin"

secret_key           = "your-secret-key-here"#### 서버 인스턴스 (smart-cradle-server)

docker_image         = "yourdockerhub/smart-cradle-server:latest"

server_machine_type  = "e2-medium"- **리소스**: `google_compute_instance.server_instance`- **포트**: `80`                    │              │              │

db_machine_type      = "e2-medium"

```- **머신 타입**: `e2-medium` (2 vCPU, 4GB RAM)



## 배포 가이드- **영역**: `asia-northeast3-a`- **소스**: `0.0.0.0/0` (전체 인터넷)        ┌───────────▼───┐  ┌──────▼──────┐  ┌───▼────────┐



### 1. 사전 준비- **OS 이미지**: Ubuntu 22.04 LTS



#### GCP 프로젝트 설정- **부트 디스크**: 30GB Standard Persistent Disk- **대상 태그**: `smart-cradle-server`        │  ESP32 Device │  │ Web Browser │  │ Mobile App │



```bash- **네트워크 인터페이스**:

# GCP 프로젝트 생성

gcloud projects create your-project-id  - 서브넷: `smart-cradle-subnet`- **용도**: 웹 대시보드 및 API 접근        │  (IoT Cradle) │  │ Dashboard   │  │ (Future)   │



# 프로젝트 설정  - 외부 IP: Ephemeral (자동 할당)

gcloud config set project your-project-id

- **태그**: `smart-cradle-server`        │               │  │             │  │            │

# Compute Engine API 활성화

gcloud services enable compute.googleapis.com- **서비스 범위**: `cloud-platform` (전체 GCP API 접근)

```

#### MQTT 접근 규칙        │ - 온습도 센서  │  │ - 실시간    │  │ - 푸시알림 │

#### 인증 설정

**설치되는 서비스:**

```bash

# Application Default Credentials 설정- **리소스**: `google_compute_firewall.allow_mqtt`        │ - 기울기 센서  │  │   모니터링  │  │ - 원격제어 │

gcloud auth application-default login

```1. **Docker Engine** - 컨테이너 런타임



#### SSH 키 생성2. **Docker Compose** - 멀티 컨테이너 오케스트레이션- **이름**: `smart-cradle-allow-mqtt`        │ - 모터 제어   │  │ - 원격제어  │  │            │



```bash3. **Flask Web Application** (Gunicorn WSGI)

ssh-keygen -t rsa -b 4096 -C "admin@smartcradle" -f ~/.ssh/id_rsa

```   - Docker 이미지: 사용자 지정 이미지- **프로토콜**: TCP        │ - 카메라      │  │ - 사용자    │  │            │



### 2. Terraform 초기화   - 포트: `80`



```bash   - 환경 변수: MySQL 연결 정보, MQTT 설정- **포트**: `1883`        └───────────────┘  │   관리      │  │            │

cd terraform/

terraform init4. **Mosquitto MQTT Broker**

```

   - Docker 이미지: `eclipse-mosquitto:2`- **소스**: `0.0.0.0/0` (전체 인터넷)                          └─────────────┘  └────────────┘

### 3. 변수 파일 작성

   - 포트: `1883`

```bash

cp terraform.tfvars.example terraform.tfvars   - 익명 접속 허용 (개발 환경)- **대상 태그**: `smart-cradle-server````

nano terraform.tfvars

```



### 4. 배포 계획 확인**자동화 스크립트:**- **용도**: IoT 디바이스 MQTT 통신



```bash- **cleanup_old_frames.py** - 10일 이상 된 비디오 프레임 삭제

terraform plan

```- **Cron Job**: 매일 03:00에 자동 실행### 🌐 네트워크 아키텍처



### 5. 인프라 배포



```bash#### DB 인스턴스 (smart-cradle-db)#### MySQL 내부 접근 규칙

terraform apply

```- **리소스**: `google_compute_instance.db_instance`



배포 시간: 약 3-5분- **머신 타입**: `e2-medium` (2 vCPU, 4GB RAM)- **리소스**: `google_compute_firewall.allow_mysql_internal````



### 6. 배포 완료 확인- **영역**: `asia-northeast3-a`



```bash- **OS 이미지**: Ubuntu 22.04 LTS- **이름**: `smart-cradle-allow-mysql-internal`Internet Gateway

terraform output

```- **부트 디스크**: 20GB Standard Persistent Disk



출력 예시:- **네트워크 인터페이스**:- **프로토콜**: TCP        │

```

server_instance_external_ip = "34.64.93.207"  - 서브넷: `smart-cradle-subnet`

db_instance_external_ip = "34.64.123.45"

```  - 외부 IP: Ephemeral (자동 할당)- **포트**: `3306`        ▼



### 7. 서비스 상태 확인- **태그**: `smart-cradle-db`



#### SSH 접속- **서비스 범위**: `cloud-platform`- **소스 태그**: `smart-cradle-server`┌─────────────────────────────────────────────────────┐



```bash

# 서버 인스턴스

gcloud compute ssh smart-cradle-server --zone=asia-northeast3-a**설치되는 서비스:**- **대상 태그**: `smart-cradle-db`│              VPC Network                            │



# DB 인스턴스

gcloud compute ssh smart-cradle-db --zone=asia-northeast3-a

```1. **MySQL 8.0 Server**- **용도**: 서버 인스턴스에서 DB 인스턴스로 연결│            (smart-cradle-network)                   │



#### Docker 컨테이너 확인   - 데이터베이스: `smartcradle`



```bash   - 사용자: `sc_user`- **보안**: 내부 통신만 허용│                                                     │

sudo docker ps

```   - 바인드 주소: `0.0.0.0` (내부 네트워크 접근 허용)



#### 웹 서비스 확인│  Subnet: 10.128.0.0/20 (asia-northeast3)          │



```bash**자동화 스크립트:**

curl http://$(terraform output -raw server_instance_external_ip)

```- **daily_backup.sh** - 전체 DB 백업#### 내부 통신 규칙│  ┌─────────────────┐    ┌─────────────────────────┐ │



## 관리 명령어- **Cron Job**: 매일 02:00에 자동 실행



### 인프라 수정- **백업 보관**: 7일 (8일 이상 된 백업 자동 삭제)- **리소스**: `google_compute_firewall.allow_internal`│  │ Server Instance │    │     DB Instance         │ │



```bash

# 변수 수정 후 재배포

terraform apply### 4. 시작 스크립트 (Startup Scripts)- **이름**: `smart-cradle-allow-internal`│  │ Internal: .3    │    │   Internal: .2          │ │



# 특정 리소스만 재생성

terraform taint google_compute_instance.server_instance

terraform apply#### 서버 인스턴스 시작 스크립트- **프로토콜**: TCP/UDP/ICMP│  │ External: Public│    │   External: Public      │ │

```

**파일**: `scripts/server_startup.sh`

### 인프라 삭제

- **포트**: 전체 (`0-65535`)│  └─────────────────┘    └─────────────────────────┘ │

```bash

terraform destroy**실행 순서:**

```

- **소스**: `10.128.0.0/20` (VPC 내부)│                                                     │

**주의**: 모든 데이터가 삭제됩니다!

1. **사용자 생성**: `admin` 계정 + SSH 키 등록

### 상태 확인

2. **Docker 설치**: Docker CE + Docker Compose- **용도**: VPC 내 인스턴스 간 자유로운 통신│  Firewall Rules:                                   │

```bash

# 현재 상태 확인3. **docker-compose.yml 생성**: Flask + Mosquitto 서비스 정의

terraform show

4. **mosquitto.conf 생성**: 익명 접속 허용 설정│  ✅ HTTP (80)      - 0.0.0.0/0                     │

# 리소스 목록

terraform state list5. **Docker 이미지 풀**: 최신 이미지 다운로드



# 특정 리소스 상세 정보6. **컨테이너 시작**: `docker-compose up -d`### 3. **Compute Engine 인스턴스**│  ✅ MQTT (1883)    - 0.0.0.0/0                     │

terraform state show google_compute_instance.server_instance

```7. **프레임 정리 스크립트 생성**: `/opt/smart-cradle/scripts/cleanup_old_frames.py`



## 비용 최적화8. **Cron 등록**: 매일 03:00에 자동 정리│  ✅ SSH (22)       - 0.0.0.0/0                     │



### 현재 구성 비용 (월 예상)



| 리소스 | 스펙 | 예상 비용 |#### DB 인스턴스 시작 스크립트#### 서버 인스턴스 (smart-cradle-server)│  ✅ MySQL (3306)   - 10.128.0.0/20 (Internal)     │

|--------|------|-----------|

| Server Instance | e2-medium | $24 |**파일**: `scripts/db_startup.sh`

| DB Instance | e2-medium | $24 |

| Persistent Disk | 50GB | $2 |- **리소스**: `google_compute_instance.server_instance`│  ✅ Internal       - 10.128.0.0/20                 │

| External IP | 2개 | $6 |

| 총계 | | $56/월 |**실행 순서:**



### 비용 절감 방법- **머신 타입**: `e2-medium` (2 vCPU, 4GB RAM)└─────────────────────────────────────────────────────┘



1. 인스턴스 크기 축소1. **사용자 생성**: `admin` 계정 + SSH 키 등록

   - e2-small 사용 시 각 $12/월

   2. **MySQL 설치**: MySQL 8.0 Server- **영역**: `asia-northeast3-a````

2. 예약 인스턴스 사용

   - 1년 약정 시 최대 57% 할인3. **Root 비밀번호 설정**



3. Preemptible VM 사용4. **데이터베이스 생성**: `smartcradle`- **OS 이미지**: Ubuntu 22.04 LTS

   - 개발 환경용, 최대 80% 할인

5. **사용자 생성 및 권한 부여**: `sc_user`

## 보안 권장사항

6. **bind-address 설정**: `0.0.0.0` (내부 네트워크 접근)- **부트 디스크**: 30GB Standard Persistent Disk## � 기술 스택 & 컴포넌트

### 현재 보안 설정

7. **백업 디렉토리 생성**: `/home/backups`

- VPC 네트워크 격리

- 내부 MySQL 접근 제한8. **백업 스크립트 생성**: `daily_backup.sh`- **네트워크 인터페이스**:

- SSH 키 기반 인증

- Flask SECRET_KEY 환경 변수 관리9. **Cron 등록**: 매일 02:00에 자동 백업



### 개선 권장사항  - 서브넷: `smart-cradle-subnet`### 인프라 계층



1. SSH 접근 제한## 📋 변수 (Variables)

   - 특정 IP만 허용하도록 방화벽 규칙 수정

  - 외부 IP: Ephemeral (자동 할당)| 구분 | 기술 | 용도 | 설정 |

2. MQTT 인증 활성화

   - mosquitto.conf에서 allow_anonymous false 설정### 필수 변수



3. MySQL Root 접근 비활성화- **태그**: `smart-cradle-server`|------|------|------|------|

   - localhost 외 접근 차단

| 변수 | 타입 | 기본값 | 설명 |

4. Cloud Armor 적용

   - DDoS 방어|------|------|--------|------|- **서비스 범위**: `cloud-platform` (전체 GCP API 접근)| **Cloud Provider** | Google Cloud Platform | 클라우드 인프라 | asia-northeast3 리전 |



5. Secret Manager 사용| `project_id` | string | - | GCP 프로젝트 ID (필수) |

   - 비밀번호를 Secret Manager에 저장

| `region` | string | `asia-northeast3` | GCP 리전 || **IaC** | Terraform | 인프라 자동화 | 버전 관리형 배포 |

## 트러블슈팅

| `zone` | string | `asia-northeast3-a` | GCP 영역 |

### 문제 1: Terraform apply 실패

| `mysql_root_password` | string | - | MySQL root 비밀번호 (필수) |**설치되는 서비스:**| **Compute** | Compute Engine (e2-medium) | VM 인스턴스 | 2 vCPU, 4GB RAM |

**증상**: Error creating instance

| `mysql_database` | string | `smartcradle` | 데이터베이스 이름 |

**해결**:

```bash| `mysql_user` | string | `sc_user` | 데이터베이스 사용자 |1. **Docker Engine** - 컨테이너 런타임| **Networking** | VPC + Subnet | 네트워크 격리 | 10.128.0.0/20 |

gcloud services enable compute.googleapis.com

gcloud auth application-default login| `mysql_password` | string | - | 데이터베이스 비밀번호 (필수) |

```

| `ssh_public_key_path` | string | `~/.ssh/id_rsa.pub` | SSH 공개키 경로 |2. **Docker Compose** - 멀티 컨테이너 오케스트레이션| **Security** | Cloud Firewall | 접근 제어 | 포트별 규칙 설정 |

### 문제 2: 인스턴스 접속 불가

| `ssh_username` | string | `admin` | SSH 사용자 이름 |

**증상**: SSH connection timeout

| `secret_key` | string | - | Flask SECRET_KEY (필수) |3. **Flask Web Application** (Gunicorn WSGI)

**해결**:

```bash| `docker_image` | string | - | Flask Docker 이미지 (필수) |

# 방화벽 규칙 확인

gcloud compute firewall-rules list| `server_machine_type` | string | `e2-medium` | 서버 머신 타입 |   - Docker 이미지: `{var.docker_image}`### 애플리케이션 계층



# 시작 로그 확인| `db_machine_type` | string | `e2-medium` | DB 머신 타입 |

gcloud compute instances get-serial-port-output smart-cradle-server --zone=asia-northeast3-a

```   - 포트: `80`| 구분 | 기술 | 용도 | 설정 |



### 문제 3: Docker 컨테이너 실행 안 됨### terraform.tfvars 예시



**증상**: docker ps 결과 비어있음   - 환경 변수: MySQL 연결 정보, MQTT 설정|------|------|------|------|



**해결**:```hcl

```bash

# 로그 확인project_id           = "your-gcp-project-id"4. **Mosquitto MQTT Broker**| **Web Framework** | Flask 2.3.2 | 웹 애플리케이션 | Python 3.11 |

sudo journalctl -u google-startup-scripts.service

region               = "asia-northeast3"

# 수동 시작

cd /opt/smart-cradlezone                 = "asia-northeast3-a"   - Docker 이미지: `eclipse-mosquitto:2`| **WSGI Server** | Gunicorn | 프로덕션 서버 | 멀티 워커 |

sudo docker-compose up -d

```mysql_root_password  = "SecureRootPassword123!"



### 문제 4: DB 연결 실패mysql_database       = "smartcradle"   - 포트: `1883`| **Container** | Docker + Compose | 컨테이너화 | 멀티 아키텍처 |



**증상**: Can't connect to MySQL servermysql_user           = "sc_user"



**해결**:mysql_password       = "SC_password_12!45"   - 익명 접속 허용 (개발 환경)| **Database** | MySQL 8.0 | 관계형 DB | InnoDB 엔진 |

```bash

# MySQL 상태 확인ssh_public_key_path  = "~/.ssh/id_rsa.pub"

sudo systemctl status mysql

ssh_username         = "admin"| **Message Broker** | Eclipse Mosquitto | MQTT 통신 | IoT 디바이스 연결 |

# 포트 확인

sudo netstat -tuln | grep 3306secret_key           = "your-secret-key-here"

```

docker_image         = "yourdockerhub/smart-cradle-server:latest"**자동화 스크립트:**

## 유지보수

server_machine_type  = "e2-medium"

### 자동 백업 확인

db_machine_type      = "e2-medium"- **cleanup_old_frames.py** - 10일 이상 된 비디오 프레임 삭제### 파일 구조

```bash

# DB 인스턴스에서```

ls -lh /home/backups/

```- **Cron Job**: 매일 03:00에 자동 실행```



### 프레임 정리 확인## 🚀 배포 가이드



```bashterraform/

# 서버 인스턴스에서

sudo crontab -l### 1. 사전 준비

```

#### DB 인스턴스 (smart-cradle-db)├── 📁 main.tf                    # 🏗️ 메인 인프라 정의

### 로그 모니터링

#### GCP 프로젝트 설정

```bash

# Flask 로그- **리소스**: `google_compute_instance.db_instance`├── 📁 variables.tf               # 📝 변수 및 설정값 정의

sudo docker logs -f <container_id>

```bash

# MySQL 로그

sudo tail -f /var/log/mysql/error.log# GCP 프로젝트 생성- **머신 타입**: `e2-medium` (2 vCPU, 4GB RAM)├── 📁 outputs.tf                 # 📤 배포 결과 출력

```

gcloud projects create your-project-id

## 다음 단계

- **영역**: `asia-northeast3-a`├── 📁 terraform.tfvars.example   # 🔑 환경변수 템플릿

1. DNS 설정 - Cloud DNS로 도메인 연결

2. HTTPS 적용 - Let's Encrypt 인증서# 프로젝트 설정

3. 모니터링 - Cloud Monitoring 설정

4. CI/CD - Cloud Build 자동 배포gcloud config set project your-project-id- **OS 이미지**: Ubuntu 22.04 LTS├── 📁 scripts/

5. 백업 자동화 - Cloud Storage 연동

6. 스케일링 - Load Balancer + Auto Scaling



## 참고 문서# Compute Engine API 활성화- **부트 디스크**: 20GB Standard Persistent Disk│   ├── 🔧 server_startup.sh      # 서버 인스턴스 초기화



- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)gcloud services enable compute.googleapis.com

- [Google Compute Engine](https://cloud.google.com/compute/docs)

- [GCP Networking](https://cloud.google.com/vpc/docs)```- **네트워크 인터페이스**:│   └── 🗄️ db_startup.sh          # DB 인스턴스 초기화




#### 인증 설정  - 서브넷: `smart-cradle-subnet`└── 📋 README.md                  # 이 문서



```bash  - 외부 IP: Ephemeral (자동 할당)```

# Application Default Credentials 설정

gcloud auth application-default login- **태그**: `smart-cradle-db`



# 또는 서비스 계정 키 사용- **서비스 범위**: `cloud-platform`## 🚀 인프라 구축 가이드

export GOOGLE_APPLICATION_CREDENTIALS="/path/to/keyfile.json"

```



#### SSH 키 생성 (없는 경우)**설치되는 서비스:**### 📋 구축 전 체크리스트



```bash1. **MySQL 8.0 Server**

ssh-keygen -t rsa -b 4096 -C "admin@smartcradle" -f ~/.ssh/id_rsa

```   - 데이터베이스: `smartcradle`#### ✅ 필수 준비사항



### 2. Terraform 초기화   - 사용자: `sc_user`- [ ] GCP 계정 및 프로젝트 생성



```bash   - 바인드 주소: `0.0.0.0` (내부 네트워크 접근 허용)- [ ] 결제 계정 연결 (약 $70/월 예상)

cd terraform/

terraform init- [ ] Compute Engine API 활성화

```

**자동화 스크립트:**- [ ] gcloud CLI 설치 및 인증

**출력 예시:**

```- **daily_backup.sh** - 전체 DB 백업- [ ] Terraform 설치 (v1.0+)

Initializing the backend...

Initializing provider plugins...- **Cron Job**: 매일 02:00에 자동 실행- [ ] Git 저장소 접근 권한

- Finding hashicorp/google versions matching "~> 5.0"...

- Installing hashicorp/google v5.x.x...- **백업 보관**: 7일 (8일 이상 된 백업 자동 삭제)



Terraform has been successfully initialized!#### ✅ 보안 요구사항

```

### 4. **시작 스크립트 (Startup Scripts)**- [ ] 강력한 DB 비밀번호 준비 (16자+ 권장)

### 3. 변수 파일 작성

- [ ] SECRET_KEY 생성 (32자+ 랜덤 문자열)

```bash

cp terraform.tfvars.example terraform.tfvars#### 서버 인스턴스 시작 스크립트- [ ] SSH 키 페어 생성 (선택사항)

nano terraform.tfvars

```**파일**: `scripts/server_startup.sh`



**필수 변수 입력:**### 🔧 단계별 구축 프로세스

- `project_id`: GCP 프로젝트 ID

- `mysql_root_password`: MySQL root 비밀번호**실행 순서:**

- `mysql_password`: sc_user 비밀번호

- `secret_key`: Flask SECRET_KEY1. **사용자 생성**: `admin` 계정 + SSH 키 등록#### 1️⃣ 환경 설정

- `docker_image`: Docker Hub 이미지 이름

2. **Docker 설치**: Docker CE + Docker Compose

### 4. 배포 계획 확인

3. **docker-compose.yml 생성**: Flask + Mosquitto 서비스 정의**GCP 환경 준비**

```bash

terraform plan   ```yaml```bash

```

   services:# gcloud CLI 설치 확인

**확인 사항:**

- 생성될 리소스 목록 (11개)     web:gcloud --version

- VPC, Subnet, Firewall Rules

- 2개의 Compute Engine 인스턴스       image: {docker_image}

- 시작 스크립트 내용

       ports:# GCP 로그인 및 프로젝트 설정

### 5. 인프라 배포

         - "80:80"gcloud auth login

```bash

terraform apply       environment:gcloud config set project YOUR_PROJECT_ID

```

         - MYSQL_HOST={db_internal_ip}gcloud auth application-default login

**확인 메시지:** `yes` 입력

         - MYSQL_PORT=3306

**배포 시간:** 약 3-5분

         - MYSQL_DATABASE={mysql_database}# 필수 API 활성화

**배포 순서:**

1. VPC 네트워크 생성         - MYSQL_USER={mysql_user}gcloud services enable compute.googleapis.com

2. 서브넷 생성

3. 방화벽 규칙 생성         - MYSQL_PASSWORD={mysql_password}```

4. DB 인스턴스 생성 및 시작

5. 서버 인스턴스 생성 및 시작         - MQTT_BROKER_HOST=mosquitto



### 6. 배포 완료 확인         - MQTT_BROKER_PORT=1883**Terraform 설치 (macOS)**



```bash         - SECRET_KEY={secret_key}```bash

terraform output

```     # Homebrew 설치



**출력 예시:**     mosquitto:/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

```

db_instance_external_ip = "34.64.123.45"       image: eclipse-mosquitto:2

db_instance_internal_ip = "10.128.0.2"

db_instance_name = "smart-cradle-db"       ports:# Terraform 설치

server_instance_external_ip = "34.64.93.207"

server_instance_internal_ip = "10.128.0.3"         - "1883:1883"brew tap hashicorp/tap

server_instance_name = "smart-cradle-server"

```   ```brew install hashicorp/tap/terraform



### 7. 서비스 상태 확인4. **mosquitto.conf 생성**: 익명 접속 허용 설정



#### SSH 접속5. **Docker 이미지 풀**: 최신 이미지 다운로드# 설치 확인



```bash6. **컨테이너 시작**: `docker-compose up -d`terraform --version

# 서버 인스턴스

gcloud compute ssh smart-cradle-server --zone=asia-northeast3-a7. **프레임 정리 스크립트 생성**: `/opt/smart-cradle/scripts/cleanup_old_frames.py````



# DB 인스턴스8. **Cron 등록**: 매일 03:00에 자동 정리

gcloud compute ssh smart-cradle-db --zone=asia-northeast3-a

```#### 2️⃣ 프로젝트 설정



#### Docker 컨테이너 확인#### DB 인스턴스 시작 스크립트



```bash**파일**: `scripts/db_startup.sh````bash

# 서버 인스턴스에서

sudo docker ps# 저장소 클론



# 예상 출력:**실행 순서:**git clone https://github.com/DMU-6team/6team.git

# CONTAINER ID   IMAGE                           STATUS

# 1234567890ab   yourdockerhub/smart-cradle...   Up 5 minutes1. **사용자 생성**: `admin` 계정 + SSH 키 등록cd 6team/terraform

# abcdef123456   eclipse-mosquitto:2             Up 5 minutes

```2. **MySQL 설치**: MySQL 8.0 Server



#### MySQL 접속 확인3. **Root 비밀번호 설정**# 환경 변수 파일 생성



```bash4. **데이터베이스 생성**: `smartcradle`cp terraform.tfvars.example terraform.tfvars

# DB 인스턴스에서

mysql -u sc_user -p5. **사용자 생성 및 권한 부여**: `sc_user````

# 비밀번호 입력 후

SHOW DATABASES;6. **bind-address 설정**: `0.0.0.0` (내부 네트워크 접근)

USE smartcradle;

SHOW TABLES;7. **백업 디렉토리 생성**: `/home/backups`**terraform.tfvars 필수 수정**

```

8. **백업 스크립트 생성**: `daily_backup.sh````hcl

#### 웹 서비스 확인

   ```bash# 프로젝트 정보

```bash

# 로컬 터미널에서   mysqldump -u root -p{password} smartcradle > backup_YYYYMMDD.sqlproject_id = "organic-palace-471901-u0"  # 실제 GCP 프로젝트 ID

curl http://$(terraform output -raw server_instance_external_ip)

   find /home/backups -name "*.sql" -mtime +7 -deleteregion     = "asia-northeast3"           # 서울 리전

# 웹 브라우저

open http://$(terraform output -raw server_instance_external_ip)   ```zone       = "asia-northeast3-a"

```

9. **Cron 등록**: 매일 02:00에 자동 백업

## 🔧 관리 명령어

# 인스턴스 설정

### 인프라 수정

---server_machine_type = "e2-medium"        # 2 vCPU, 4GB RAM

```bash

# 변수 수정 후 재배포db_machine_type     = "e2-medium"

terraform apply

## 📋 변수 (Variables)

# 특정 리소스만 재생성

terraform taint google_compute_instance.server_instance# 보안 설정 (반드시 변경!)

terraform apply

```### 필수 변수mysql_root_password = "복잡한_루트_비밀번호_16자이상"



### 인프라 삭제mysql_password      = "복잡한_유저_비밀번호_16자이상"  



```bash| 변수 | 타입 | 기본값 | 설명 |secret_key          = "랜덤_시크릿_키_32자이상"

# 모든 리소스 삭제

terraform destroy|------|------|--------|------|



# 확인 메시지에 yes 입력| `project_id` | string | - | GCP 프로젝트 ID (필수) |# Docker 이미지

```

| `region` | string | `asia-northeast3` | GCP 리전 |docker_image = "joohyun7818/smart-cradle-flask:latest"

**⚠️ 주의**: 데이터베이스 포함 모든 데이터가 삭제됩니다!

| `zone` | string | `asia-northeast3-a` | GCP 영역 |```

### 상태 확인

| `mysql_root_password` | string | - | MySQL root 비밀번호 (필수) |

```bash

# 현재 상태 확인| `mysql_database` | string | `smartcradle` | 데이터베이스 이름 |#### 3️⃣ 인프라 배포

terraform show

| `mysql_user` | string | `sc_user` | 데이터베이스 사용자 |

# 리소스 목록

terraform state list| `mysql_password` | string | - | 데이터베이스 비밀번호 (필수) |```bash



# 특정 리소스 상세 정보| `ssh_public_key_path` | string | `~/.ssh/id_rsa.pub` | SSH 공개키 경로 |# Terraform 초기화

terraform state show google_compute_instance.server_instance

```| `ssh_username` | string | `admin` | SSH 사용자 이름 |terraform init



## 📊 비용 최적화| `secret_key` | string | - | Flask SECRET_KEY (필수) |



### 현재 구성 비용 (월 예상)| `docker_image` | string | - | Flask Docker 이미지 (필수) |# 배포 계획 확인 (중요!)



| 리소스 | 스펙 | 예상 비용 || `server_machine_type` | string | `e2-medium` | 서버 머신 타입 |terraform plan

|--------|------|-----------|

| Server Instance (e2-medium) | 2 vCPU, 4GB RAM | ~$24 || `db_machine_type` | string | `e2-medium` | DB 머신 타입 |

| DB Instance (e2-medium) | 2 vCPU, 4GB RAM | ~$24 |

| Standard Persistent Disk (50GB) | 30GB + 20GB | ~$2 |# 인프라 배포 실행

| External IP (2개) | Ephemeral | ~$6 |

| **총계** | | **~$56/월** |### terraform.tfvars 예시terraform apply



### 비용 절감 방법# "yes" 입력하여 배포 승인



1. **인스턴스 크기 축소**```hcl```

   ```hcl

   server_machine_type = "e2-small"  # ~$12/월project_id           = "your-gcp-project-id"

   db_machine_type     = "e2-small"  # ~$12/월

   ```region               = "asia-northeast3"**배포 진행 상황**



2. **예약 인스턴스 사용** (1년 약정)zone                 = "asia-northeast3-a"```

   - 최대 57% 할인 가능

mysql_root_password  = "SecureRootPassword123!"⏳ VPC 네트워크 생성...

3. **Preemptible VM 사용** (개발 환경)

   - 최대 80% 할인mysql_database       = "smartcradle"⏳ 서브넷 생성...

   - 단, 24시간마다 자동 종료

mysql_user           = "sc_user"⏳ 방화벽 규칙 5개 생성...

4. **Cloud SQL 대신 Self-hosted MySQL**

   - 현재 구성 유지 (이미 최적화됨)mysql_password       = "SC_password_12!45"⏳ 서버 인스턴스 생성...



## 🔐 보안 권장사항ssh_public_key_path  = "~/.ssh/id_rsa.pub"⏳ DB 인스턴스 생성...



### 현재 보안 설정ssh_username         = "admin"⏳ Startup Script 실행... (5-10분 소요)



✅ **적용됨:**secret_key           = "your-secret-key-here"✅ 배포 완료!

- VPC 네트워크 격리

- 내부 MySQL 접근 제한 (10.128.0.0/20만 허용)docker_image         = "yourdockerhub/smart-cradle-server:latest"```

- SSH 키 기반 인증

- Flask SECRET_KEY 환경 변수 관리server_machine_type  = "e2-medium"



⚠️ **개선 필요:**db_machine_type      = "e2-medium"#### 4️⃣ 배포 확인 및 테스트



1. **SSH 접근 제한**```

   ```hcl

   source_ranges = ["your-ip-address/32"]  # 특정 IP만 허용**배포 결과 확인**

   ```

---```bash

2. **MQTT 인증 활성화**

   ```conf# 배포 출력 정보 확인

   allow_anonymous false

   password_file /mosquitto/config/passwd## 🚀 배포 가이드terraform output

   ```



3. **MySQL Root 접근 비활성화**

   ```sql### 1. 사전 준비# 출력 예시:

   DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1');

   FLUSH PRIVILEGES;# server_instance_external_ip = "34.64.170.248"

   ```

#### GCP 프로젝트 설정# db_instance_external_ip = "34.64.206.202"

4. **Cloud Armor 적용** (DDoS 방어)

5. **Secret Manager 사용** (비밀번호 관리)```bash# web_url = "http://34.64.170.248"



## 🐛 트러블슈팅# GCP 프로젝트 생성```



### 문제 1: Terraform apply 실패gcloud projects create your-project-id



**증상**: `Error: Error creating instance`**서비스 상태 확인**



**원인**: Compute Engine API 비활성화 또는 권한 부족# 프로젝트 설정```bash



**해결**:gcloud config set project your-project-id# 웹 서비스 접속 테스트

```bash

gcloud services enable compute.googleapis.comcurl -I http://$(terraform output -raw server_instance_external_ip)

gcloud auth application-default login

```# Compute Engine API 활성화



### 문제 2: 인스턴스 접속 불가gcloud services enable compute.googleapis.com# SSH 접속 테스트 (admin 계정)



**증상**: `ssh: connect to host X.X.X.X port 22: Connection timed out````ssh smart-cradle-server "hostname && uptime"



**원인**: 방화벽 규칙 미적용 또는 시작 스크립트 실행 중



**해결**:#### 인증 설정# Docker 컨테이너 상태 확인

```bash

# 방화벽 규칙 확인```bashssh smart-cradle-server "cd /opt/smart-cradle && sudo docker compose ps"

gcloud compute firewall-rules list

# Application Default Credentials 설정```

# 인스턴스 시작 로그 확인

gcloud compute instances get-serial-port-output smart-cradle-server --zone=asia-northeast3-agcloud auth application-default login

```

## 🛠️ 운영 및 관리

### 문제 3: Docker 컨테이너 실행 안 됨

# 또는 서비스 계정 키 사용

**증상**: `docker ps` 결과가 비어있음

export GOOGLE_APPLICATION_CREDENTIALS="/path/to/keyfile.json"### 📊 모니터링 방법

**원인**: 시작 스크립트 실행 실패 또는 이미지 풀 실패

```

**해결**:

```bash```bash

# 로그 확인

sudo journalctl -u google-startup-scripts.service#### SSH 키 생성 (없는 경우)# 시스템 리소스 모니터링



# 수동으로 컨테이너 시작```bashssh smart-cradle-server "htop"

cd /opt/smart-cradle

sudo docker-compose up -dssh-keygen -t rsa -b 4096 -C "admin@smartcradle" -f ~/.ssh/id_rsa

```

```# 애플리케이션 로그 확인

### 문제 4: DB 연결 실패

ssh smart-cradle-server "cd /opt/smart-cradle && docker compose logs -f"

**증상**: Flask 앱에서 `Can't connect to MySQL server`

### 2. Terraform 초기화

**원인**: MySQL 설치 실패 또는 방화벽 문제

# 데이터베이스 상태 확인

**해결**:

```bash```bashssh smart-cradle-db "sudo systemctl status mysql"

# DB 인스턴스에서

sudo systemctl status mysqlcd terraform/```

sudo netstat -tuln | grep 3306

terraform init

# 방화벽 확인

sudo iptables -L -n```### � 업데이트 프로세스

```



## 📝 유지보수

**출력 예시:****코드 업데이트**

### 자동 백업 확인

``````bash

```bash

# DB 인스턴스에서Initializing the backend...# 서버 접속

ls -lh /home/backups/

cat /var/spool/cron/crontabs/rootInitializing provider plugins...ssh smart-cradle-server

```

- Finding hashicorp/google versions matching "~> 5.0"...

### 프레임 정리 확인

- Installing hashicorp/google v5.x.x...# 최신 코드 반영

```bash

# 서버 인스턴스에서cd /opt/smart-cradle

sudo crontab -l

ls -lh /opt/smart-cradle/scripts/Terraform has been successfully initialized!git pull origin server

```

```docker compose pull

### 로그 모니터링

docker compose up -d

```bash

# 서버 인스턴스 - Flask 로그### 3. 변수 파일 작성```

sudo docker logs -f <web_container_id>



# DB 인스턴스 - MySQL 로그

sudo tail -f /var/log/mysql/error.log```bash**인프라 업데이트**

```

cp terraform.tfvars.example terraform.tfvars```bash

## 🎯 다음 단계

nano terraform.tfvars# 변경사항이 있는 경우

1. **DNS 설정**: Cloud DNS로 도메인 연결

2. **HTTPS 적용**: Let's Encrypt 인증서```terraform plan

3. **모니터링**: Cloud Monitoring 설정

4. **CI/CD**: Cloud Build로 자동 배포terraform apply

5. **백업 자동화**: Cloud Storage로 백업 이관

6. **스케일링**: Load Balancer + Auto Scaling**필수 변수 입력:**```



## 📚 참고 문서- `project_id`: GCP 프로젝트 ID



- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)- `mysql_root_password`: MySQL root 비밀번호### 💾 백업 관리

- [Google Compute Engine](https://cloud.google.com/compute/docs)

- [GCP Networking](https://cloud.google.com/vpc/docs)- `mysql_password`: sc_user 비밀번호

- [Cloud SQL Alternative](https://cloud.google.com/sql/docs)

- `secret_key`: Flask SECRET_KEY**자동 백업 (이미 설정됨)**

- `docker_image`: Docker Hub 이미지 이름- 매일 02:00 MySQL 전체 백업

- 백업 파일 위치: `/home/backups/`

### 4. 배포 계획 확인- 자동 정리: 7일 이상 된 백업 파일 삭제



```bash**수동 백업**

terraform plan```bash

```# DB 백업 생성

ssh smart-cradle-db "sudo /scripts/backup_mysql.sh"

**확인 사항:**

- 생성될 리소스 목록 (11개)# 백업 파일 확인

- VPC, Subnet, Firewall Rulesssh smart-cradle-db "ls -lh /home/backups/"

- 2개의 Compute Engine 인스턴스```

- 시작 스크립트 내용

## 🔒 보안 및 최적화

### 5. 인프라 배포

### 🛡️ 보안 체크리스트

```bash

terraform apply- [x] 방화벽 규칙으로 포트 제한

```- [x] MySQL 외부 접근 차단 (내부 네트워크만)

- [x] 강력한 비밀번호 사용

**확인 메시지:** `yes` 입력- [x] SSH 키 기반 인증

- [ ] SSL/TLS 인증서 설정 (선택사항)

**배포 시간:** 약 3-5분- [ ] GCP Secret Manager 연동 (선택사항)



**배포 순서:**### ⚡ 성능 최적화

1. VPC 네트워크 생성

2. 서브넷 생성**데이터베이스 튜닝**

3. 방화벽 규칙 생성```bash

4. DB 인스턴스 생성 및 시작# MySQL 설정 최적화

5. 서버 인스턴스 생성 및 시작ssh smart-cradle-db "sudo vim /etc/mysql/mysql.conf.d/mysqld.cnf"



### 6. 배포 완료 확인# 권장 설정:

# innodb_buffer_pool_size = 2G

```bash# max_connections = 100

terraform output# query_cache_size = 64M

``````



**출력 예시:****웹 서버 튜닝**

``````bash

db_instance_external_ip = "34.64.123.45"# Gunicorn 워커 수 조정

db_instance_internal_ip = "10.128.0.2"ssh smart-cradle-server "cd /opt/smart-cradle && vim docker-compose.yml"

db_instance_name = "smart-cradle-db"

server_instance_external_ip = "34.64.93.207"# 권장 설정: workers = (CPU 코어 수 × 2) + 1

server_instance_internal_ip = "10.128.0.3"```

server_instance_name = "smart-cradle-server"

```## � 비용 최적화



### 7. 서비스 상태 확인### 📊 예상 비용 (월간)



#### SSH 접속| 항목 | 사양 | 예상 비용 |

```bash|------|------|-----------|

# 서버 인스턴스| Compute Engine (Server) | e2-medium | $25-30 |

gcloud compute ssh smart-cradle-server --zone=asia-northeast3-a| Compute Engine (DB) | e2-medium | $25-30 |

| 네트워크 트래픽 | ~10GB/월 | $1-3 |

# DB 인스턴스| 디스크 스토리지 | 20GB × 2 | $4 |

gcloud compute ssh smart-cradle-db --zone=asia-northeast3-a| **총 예상 비용** |  | **$55-67** |

```

### � 비용 절약 팁

#### Docker 컨테이너 확인

```bash1. **예약 인스턴스 사용** (1년 약정 시 30% 할인)

# 서버 인스턴스에서2. **자동 정지 스케줄링** (개발/테스트 시)

sudo docker ps3. **불필요한 로그 정리** (디스크 사용량 절약)

4. **네트워크 트래픽 최적화** (압축, 캐싱)

# 예상 출력:

# CONTAINER ID   IMAGE                           STATUS## 🚨 문제 해결 (Troubleshooting)

# 1234567890ab   yourdockerhub/smart-cradle...   Up 5 minutes

# abcdef123456   eclipse-mosquitto:2             Up 5 minutes### 자주 발생하는 문제들

```

#### ❌ "API not enabled" 오류

#### MySQL 접속 확인```bash

```bash# 해결: Compute Engine API 활성화

# DB 인스턴스에서gcloud services enable compute.googleapis.com

mysql -u sc_user -p```

# 비밀번호 입력 후

SHOW DATABASES;#### ❌ 웹 서비스 접속 불가

USE smartcradle;```bash

SHOW TABLES;# 1. Startup script 완료 대기 (10분)

```ssh smart-cradle-server "sudo journalctl -u google-startup-scripts.service"



#### 웹 서비스 확인# 2. Docker 상태 확인

```bashssh smart-cradle-server "docker compose ps"

# 로컬 터미널에서

curl http://$(terraform output -raw server_instance_external_ip)# 3. 방화벽 규칙 확인

gcloud compute firewall-rules list --filter="name~smart-cradle"

# 웹 브라우저```

open http://$(terraform output -raw server_instance_external_ip)

```#### ❌ DB 연결 오류

```bash

---# 1. MySQL 서비스 상태

ssh smart-cradle-db "sudo systemctl status mysql"

## 🔧 관리 명령어

# 2. 네트워크 연결 테스트

### 인프라 수정ssh smart-cradle-server "telnet 10.128.0.2 3306"



```bash# 3. DB 사용자 권한 확인

# 변수 수정 후 재배포ssh smart-cradle-db "mysql -u root -p -e 'SELECT User, Host FROM mysql.user;'"

terraform apply```



# 특정 리소스만 재생성## 🧹 인프라 정리

terraform taint google_compute_instance.server_instance

terraform apply**완전 삭제 (주의!)**

``````bash

# 모든 리소스 삭제

### 인프라 삭제terraform destroy



```bash# 확인 후 "yes" 입력

# 모든 리소스 삭제# ⚠️ 복구 불가능!

terraform destroy```



# 확인 메시지에 yes 입력**선택적 삭제**

``````bash

# 특정 인스턴스만 삭제

**⚠️ 주의**: 데이터베이스 포함 모든 데이터가 삭제됩니다!terraform taint google_compute_instance.server_instance

terraform apply

### 상태 확인```



```bash---

# 현재 상태 확인

terraform show## � 추가 지원



# 리소스 목록- 📧 기술 지원: [팀 이메일]

terraform state list- 📖 상세 문서: `/Users/joohyun/joohyun/python/6team-server/README.md`

- 🐛 버그 리포트: [GitHub Issues](https://github.com/DMU-6team/6team/issues)

# 특정 리소스 상세 정보

terraform state show google_compute_instance.server_instance---

```

<div align="center">

---

**🏗️ Infrastructure as Code로 안정적인 스마트 요람 시스템을! 🏗️**

## 📊 비용 최적화

</div>

### 현재 구성 비용 (월 예상)

| 리소스 | 스펙 | 예상 비용 |
|--------|------|-----------|
| Server Instance (e2-medium) | 2 vCPU, 4GB RAM | ~$24 |
| DB Instance (e2-medium) | 2 vCPU, 4GB RAM | ~$24 |
| Standard Persistent Disk (50GB) | 30GB + 20GB | ~$2 |
| External IP (2개) | Ephemeral | ~$6 |
| **총계** | | **~$56/월** |

### 비용 절감 방법

1. **인스턴스 크기 축소**
   ```hcl
   server_machine_type = "e2-small"  # ~$12/월
   db_machine_type     = "e2-small"  # ~$12/월
   ```

2. **예약 인스턴스 사용** (1년 약정)
   - 최대 57% 할인 가능

3. **Preemptible VM 사용** (개발 환경)
   - 최대 80% 할인
   - 단, 24시간마다 자동 종료

4. **Cloud SQL 대신 Self-hosted MySQL**
   - 현재 구성 유지 (이미 최적화됨)

---

## 🔐 보안 권장사항

### 현재 보안 설정

✅ **적용됨:**
- VPC 네트워크 격리
- 내부 MySQL 접근 제한 (10.128.0.0/20만 허용)
- SSH 키 기반 인증
- Flask SECRET_KEY 환경 변수 관리

⚠️ **개선 필요:**

1. **SSH 접근 제한**
   ```hcl
   source_ranges = ["your-ip-address/32"]  # 특정 IP만 허용
   ```

2. **MQTT 인증 활성화**
   ```conf
   allow_anonymous false
   password_file /mosquitto/config/passwd
   ```

3. **MySQL Root 접근 비활성화**
   ```sql
   DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1');
   FLUSH PRIVILEGES;
   ```

4. **Cloud Armor 적용** (DDoS 방어)
5. **Secret Manager 사용** (비밀번호 관리)

---

## 🐛 트러블슈팅

### 문제 1: Terraform apply 실패

**증상**: `Error: Error creating instance`

**원인**: Compute Engine API 비활성화 또는 권한 부족

**해결**:
```bash
gcloud services enable compute.googleapis.com
gcloud auth application-default login
```

---

### 문제 2: 인스턴스 접속 불가

**증상**: `ssh: connect to host X.X.X.X port 22: Connection timed out`

**원인**: 방화벽 규칙 미적용 또는 시작 스크립트 실행 중

**해결**:
```bash
# 방화벽 규칙 확인
gcloud compute firewall-rules list

# 인스턴스 시작 로그 확인
gcloud compute instances get-serial-port-output smart-cradle-server --zone=asia-northeast3-a
```

---

### 문제 3: Docker 컨테이너 실행 안 됨

**증상**: `docker ps` 결과가 비어있음

**원인**: 시작 스크립트 실행 실패 또는 이미지 풀 실패

**해결**:
```bash
# 로그 확인
sudo journalctl -u google-startup-scripts.service

# 수동으로 컨테이너 시작
cd /opt/smart-cradle
sudo docker-compose up -d
```

---

### 문제 4: DB 연결 실패

**증상**: Flask 앱에서 `Can't connect to MySQL server`

**원인**: MySQL 설치 실패 또는 방화벽 문제

**해결**:
```bash
# DB 인스턴스에서
sudo systemctl status mysql
sudo netstat -tuln | grep 3306

# 방화벽 확인
sudo iptables -L -n
```

---

## 📝 유지보수

### 자동 백업 확인

```bash
# DB 인스턴스에서
ls -lh /home/backups/
cat /var/spool/cron/crontabs/root
```

### 프레임 정리 확인

```bash
# 서버 인스턴스에서
sudo crontab -l
ls -lh /opt/smart-cradle/scripts/
```

### 로그 모니터링

```bash
# 서버 인스턴스 - Flask 로그
sudo docker logs -f <web_container_id>

# DB 인스턴스 - MySQL 로그
sudo tail -f /var/log/mysql/error.log
```

---

## 🎯 다음 단계

1. **DNS 설정**: Cloud DNS로 도메인 연결
2. **HTTPS 적용**: Let's Encrypt 인증서
3. **모니터링**: Cloud Monitoring 설정
4. **CI/CD**: Cloud Build로 자동 배포
5. **백업 자동화**: Cloud Storage로 백업 이관
6. **스케일링**: Load Balancer + Auto Scaling

---

## 📚 참고 문서

- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Google Compute Engine](https://cloud.google.com/compute/docs)
- [GCP Networking](https://cloud.google.com/vpc/docs)
- [Cloud SQL Alternative](https://cloud.google.com/sql/docs)
