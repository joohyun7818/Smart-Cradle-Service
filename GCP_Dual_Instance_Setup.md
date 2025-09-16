# 스마트요람 서버 — GCP 듀얼 인스턴스 설정 가이드

이 파일은 GCP에서 스마트요람 서버를 **서버 인스턴스**와 **DB 인스턴스**로 분리하여 배포하는 방법을 단계별로 정리합니다.

- **서버 인스턴스**: Flask 앱, MQTT 브로커 (Mosquitto), 웹 서버, 데이터 저장 (프레임 등).
- **DB 인스턴스**: MySQL 서버, 데이터베이스 관리, 백업.

두 인스턴스 모두 Ubuntu 기반 GCP VM을 사용하며, DB는 Cloud SQL이 아닌 VM에 직접 MySQL을 설치합니다.

> 전제: 각 인스턴스에서 SSH로 접속 가능하며 root 또는 sudo 권한이 있는 계정으로 작업합니다. GCP 방화벽에서 필요한 포트(22, 80, 1883, 3306 등)를 열어두세요.

## 공통 준비 작업 (두 인스턴스 모두)

### 1. 시스템 업데이트

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. 필수 패키지 설치

```bash
sudo apt install -y net-tools git curl ca-certificates gnupg lsb-release software-properties-common
```

### 3. 편집기 설치 (선택)

```bash
sudo apt install -y vim-tiny
# 또는
sudo apt install -y nano
```

### 4. Docker 설치 (공식 저장소)

```bash
# 키링 디렉토리 생성
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# 현재 사용자에게 docker 권한 부여 (로그아웃/로그인 필요)
sudo usermod -aG docker $USER
```

### 5. Docker Compose v2 설치

```bash
# apt 패키지 설치 시도
sudo apt install -y docker-compose-plugin || true

# 없을 경우 수동 설치 (x86_64 가정)
sudo mkdir -p /usr/libexec/docker/cli-plugins
VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep -Po '"tag_name": "\K.*?(?=")' || echo "v2.20.2")
sudo curl -SL "https://github.com/docker/compose/releases/download/${VERSION}/docker-compose-linux-x86_64" -o /usr/libexec/docker/cli-plugins/docker-compose
sudo chmod +x /usr/libexec/docker/cli-plugins/docker-compose
```

### 6. 레포지토리 클론 및 브랜치 체크아웃

```bash
git clone https://github.com/DMU-6team/6team.git ./6team
cd ./6team
git fetch origin
git checkout server
```

## DB 인스턴스 전용 작업

DB 인스턴스는 MySQL 서버를 직접 설치하여 운영합니다. 보안과 성능을 위해 컨테이너 대신 직접 설치된 MySQL을 사용합니다.

### 직접 설치 방법

#### 21. MySQL 서버 설치 및 설정

```bash
# MySQL 설치
sudo apt install -y mysql-server

# MySQL 보안 설정 (비밀번호 설정, 익명 사용자 제거 등)
sudo mysql_secure_installation

# MySQL 서비스 시작 및 자동 시작 설정
sudo systemctl start mysql
sudo systemctl enable mysql

# MySQL 루트 비밀번호 설정 (예: root_password_1234)
sudo mysql -u root -p <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root_password_1234';
FLUSH PRIVILEGES;
EOF

# 데이터베이스 및 사용자 생성
sudo mysql -u root -p'root_password_1234' <<EOF
CREATE DATABASE smartcradle;
CREATE USER 'sc_user'@'%' IDENTIFIED BY 'SC_password_1234@';
GRANT ALL PRIVILEGES ON smartcradle.* TO 'sc_user'@'%';
FLUSH PRIVILEGES;
EOF
```

#### 22. MySQL 설정 파일 수정 (외부 연결 허용)

```bash
# MySQL 설정 파일 편집
sudo cp /etc/mysql/mysql.conf.d/mysqld.cnf /etc/mysql/mysql.conf.d/mysqld.cnf.backup
sudo sed -i 's/bind-address\s*=\s*127\.0\.0\.1/bind-address = 0.0.0.0/' /etc/mysql/mysql.conf.d/mysqld.cnf

# MySQL 재시작
sudo systemctl restart mysql
```

#### 23. 백업 디렉터리 생성 및 스크립트 설정

```bash
mkdir -p backups
chown -R $USER:$USER backups
chmod 700 backups

# 백업 스크립트 생성
cat > backups/daily_backup.sh <<EOF
#!/bin/bash
DATE=\$(date +%Y%m%d_%H%M%S)
mysqldump -u sc_user -p'sc_password_1234' smartcradle > backups/smartcradle_\${DATE}.sql
find backups -name "*.sql" -mtime +7 -delete  # 7일 이상 된 백업 삭제
EOF
chmod +x backups/daily_backup.sh

# 크론탭에 백업 스케줄 추가 (매일 오전 2시)
(crontab -l ; echo "0 2 * * * /home/\$USER/backups/daily_backup.sh") | crontab -
```

#### 24. 방화벽 설정 (UFW 사용 시)

```bash
sudo ufw allow 3306/tcp
sudo ufw --force enable
```

#### 25. DB 인스턴스 완료 확인

```bash
# MySQL 접속 테스트
mysql -u sc_user -p'SC_password_1234@' -h localhost smartcradle -e "SELECT 1;"
```

#### 22. 백업 디렉터리 생성

```bash
mkdir -p backups
chown -R $USER:$USER backups
chmod 700 backups
```

#### 23. Docker Compose로 DB만 실행

**참고**: DB 인스턴스에서는 Docker Compose를 사용하지 않습니다. 직접 MySQL 설치를 권장합니다. 아래 단계로 진행하세요.

#### 24. DB 인스턴스 완료 확인

```bash
# MySQL 접속 테스트
mysql -u sc_user -p'SC_password_1234@' -h localhost smartcradle -e "SELECT 1;"

# 백업 테스트
./backups/daily_backup.sh
```

### 방법 A: 직접 설치 (권장)

#### 25. MySQL 서버 설치 및 설정

```bash
# MySQL 설치
sudo apt install -y mysql-server

# MySQL 보안 설정 (비밀번호 설정, 익명 사용자 제거 등)
sudo mysql_secure_installation

# MySQL 서비스 시작 및 자동 시작 설정
sudo systemctl start mysql
sudo systemctl enable mysql

# MySQL 루트 비밀번호 설정 (예: root_password_1234)
sudo mysql -u root -p <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root_password_1234';
FLUSH PRIVILEGES;
EOF

# 데이터베이스 및 사용자 생성
sudo mysql -u root -p'root_password_1234' <<EOF
CREATE DATABASE smartcradle;
CREATE USER 'sc_user'@'%' IDENTIFIED BY 'SC_password_1234@';
GRANT ALL PRIVILEGES ON smartcradle.* TO 'sc_user'@'%';
FLUSH PRIVILEGES;
EOF
```

#### 26. MySQL 설정 파일 수정 (외부 연결 허용)

```bash
# MySQL 설정 파일 편집
sudo cp /etc/mysql/mysql.conf.d/mysqld.cnf /etc/mysql/mysql.conf.d/mysqld.cnf.backup
sudo sed -i 's/bind-address\s*=\s*127\.0\.0\.1/bind-address = 0.0.0.0/' /etc/mysql/mysql.conf.d/mysqld.cnf

# MySQL 재시작
sudo systemctl restart mysql
```

#### 27. 백업 디렉터리 생성 및 스크립트 설정

```bash
mkdir -p backups
chown -R $USER:$USER backups
chmod 700 backups

# 백업 스크립트 생성
cat > backups/daily_backup.sh <<EOF
#!/bin/bash
DATE=\$(date +%Y%m%d_%H%M%S)
mysqldump -u sc_user -p'sc_password_1234' smartcradle > backups/smartcradle_\${DATE}.sql
find backups -name "*.sql" -mtime +7 -delete  # 7일 이상 된 백업 삭제
EOF
chmod +x backups/daily_backup.sh

# 크론탭에 백업 스케줄 추가 (매일 오전 2시)
(crontab -l ; echo "0 2 * * * /home/\$USER/backups/daily_backup.sh") | crontab -
```

#### 28. 방화벽 설정 (UFW 사용 시)

```bash
sudo ufw allow 3306/tcp
sudo ufw --force enable
```

#### 29. DB 인스턴스 완료 확인

```bash
# MySQL 접속 테스트
mysql -u sc_user -p'sc_password_1234' -h localhost smartcradle -e "SELECT 1;"
```

#### 12. MySQL 설정 파일 수정 (외부 연결 허용)

```bash
# /etc/mysql/mysql.conf.d/mysqld.cnf 편집
sudo sed -i 's/bind-address.*/bind-address = 0.0.0.0/' /etc/mysql/mysql.conf.d/mysqld.cnf
sudo systemctl restart mysql
```

#### 13. 백업 디렉터리 생성 및 스크립트 설정

```bash
mkdir -p backups
chown -R $USER:$USER backups
chmod 700 backups

# 백업 스크립트 생성 (예: daily_backup.sh)
cat > backups/daily_backup.sh <<EOF
#!/bin/bash
DATE=\$(date +%Y%m%d_%H%M%S)
mysqldump -u sc_user -p'sc_password_1234' smartcradle > backups/smartcradle_\${DATE}.sql
find backups -name "*.sql" -mtime +7 -delete  # 7일 이상 된 백업 삭제
EOF
chmod +x backups/daily_backup.sh

# 크론탭에 백업 스케줄 추가 (매일 오전 2시)
(crontab -l ; echo "0 2 * * * /home/\$USER/backups/daily_backup.sh") | crontab -
```

#### 14. 방화벽 설정 (UFW 사용 시)

```bash
sudo ufw allow 3306/tcp
sudo ufw --force enable
```

#### 15. DB 인스턴스 완료 확인

```bash
# MySQL 접속 테스트
mysql -u sc_user -p'sc_password_1234' -h localhost smartcradle -e "SELECT 1;"

# 백업 스크립트 테스트
./backups/daily_backup.sh
```

## 서버 인스턴스 전용 작업

서버 인스턴스는 Flask 앱과 MQTT 브로커를 컨테이너로 실행합니다. DB는 외부 DB 인스턴스(직접 설치된 MySQL)에 연결합니다.

**참고**: docker-compose.yml에는 web과 mosquitto 서비스만 포함되어 있습니다. DB와 백업 서비스는 보안상 별도 인스턴스에서 직접 운영합니다.

### 26. .env 파일 생성 (DB 인스턴스 IP 지정)

**중요**: 서버 인스턴스에서는 DB를 로컬이 아닌 외부 DB 인스턴스(직접 설치된 MySQL)에 연결합니다.

```bash
# DB 인스턴스의 내부 IP를 사용 (GCP 내부 네트워크)
cat > .env <<EOF
MYSQL_ROOT_PASSWORD=root_password_1234
MYSQL_DATABASE=smartcradle
MYSQL_USER=sc_user
MYSQL_PASSWORD=SC_password_1234@
MYSQL_HOST=10.128.0.3
MYSQL_PORT=3306
MQTT_BROKER_HOST=mosquitto
MQTT_BROKER_PORT=1883
SECRET_KEY=sc_secret_1234
EOF
chmod 600 .env
```

### 27. 데이터 디렉터리 생성

```bash
mkdir -p data
chown -R $USER:$USER data
chmod 700 data
```

### 28. Docker 이미지 빌드/푸시 (로컬 또는 CI)

```bash
# Flask 서버 이미지 빌드 (amd64)
docker buildx build --platform linux/amd64 -t joohyun7818/smart-cradle-flask:latest ./smart_cradle_server
docker push joohyun7818/smart-cradle-flask:latest
```

### 29. Docker Compose로 서비스 실행 (서버 인스턴스)

**서버 인스턴스에서는 web과 mosquitto 서비스만 실행합니다.**

```bash
# 최신 이미지 받아오고 스택 실행 (web, mosquitto)
docker compose pull
docker compose up -d
```

### 30. 동작 확인

```bash
# 컨테이너 상태 확인
docker compose ps

# 로그 확인
docker compose logs -f web
```

### 31. 방화벽 설정 (UFW 사용 시)

```bash
sudo ufw allow 80/tcp
sudo ufw allow 1883/tcp
sudo ufw --force enable
```

> 참고: Flask 앱은 기동 시 DB 연결을 확인하고 필요한 테이블을 자동 생성합니다(`db.create_all()`). 별도의 마이그레이션 명령은 필요 없습니다.

## 추가 고려사항

- **보안**: DB 인스턴스의 MySQL 포트(3306)는 서버 인스턴스에서만 접근 가능하도록 GCP 방화벽 규칙 설정 (출처 IP 제한).
- **모니터링**: GCP Cloud Monitoring으로 각 인스턴스 모니터링 설정.
- **백업**: DB 인스턴스의 백업을 GCS 버킷으로 업로드하는 스크립트 추가 고려.
- **스케일링**: 서버 인스턴스에 로드 밸런서 추가 가능.
- **문제 해결**: DB 연결 실패 시 `telnet \${DB_INSTANCE_IP} 3306`로 네트워크 확인.
