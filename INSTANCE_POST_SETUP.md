# 스마트요람 서버 — 인스턴스 생성 후 체크리스트

이 파일은 GCP 또는 기타 클라우드에서 우분투 인스턴스를 생성한 직후 수행해야 할 작업을 단계별로 정리합니다.

> 전제: 인스턴스에서 SSH로 접속 가능하며 root 또는 sudo 권한이 있는 계정으로 작업합니다.


## 1. 시스템 업데이트

```bash
sudo apt update && sudo apt upgrade -y
```


## 2. 필수 패키지 설치

```bash
sudo apt install -y git curl ca-certificates gnupg lsb-release software-properties-common
```


## 3. 편집기 설치 (선택)

```bash
sudo apt install -y vim-tiny
# 또는
sudo apt install -y nano
```


## 4. Docker 설치 (권장: 공식 저장소)

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


## 5. Docker Compose v2 설치

```bash
# 우선 apt 패키지가 있으면 설치
sudo apt install -y docker-compose-plugin || true

# 없을 경우 수동 설치 (x86_64 가정)
sudo mkdir -p /usr/libexec/docker/cli-plugins
VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep -Po '"tag_name": "\K.*?(?=")' || echo "v2.20.2")
sudo curl -SL "https://github.com/docker/compose/releases/download/${VERSION}/docker-compose-linux-x86_64" -o /usr/libexec/docker/cli-plugins/docker-compose
sudo chmod +x /usr/libexec/docker/cli-plugins/docker-compose
```


## 6. 레포지토리 클론 및 브랜치 체크아웃

```bash
git clone https://github.com/DMU-6team/6team.git /opt/6team
cd /opt/6team
git fetch origin
git checkout server
```


## 7. .env 파일 생성 (중요 - 절대 깃에 커밋하지 마세요)

```bash
cp smart_cradle_server/.env.example .env
# 또는 아래 예시로 직접 생성
cat > .env <<EOF
MYSQL_ROOT_PASSWORD=change_me_root
MYSQL_DATABASE=smartcradle
MYSQL_USER=sc_user
MYSQL_PASSWORD=change_me_db
MQTT_BROKER_HOST=mosquitto
MQTT_BROKER_PORT=1883
SECRET_KEY=change_me_secret
EOF
chmod 600 .env
```


## 8. backups 디렉터리 생성

```bash
mkdir -p backups
chown -R $USER:$USER backups
chmod 700 backups
```


## 9. Docker Compose로 스택 빌드 및 시작

```bash
docker compose build --pull
docker compose up -d
```


## 10. 동작 확인

```bash
docker compose ps
docker compose logs -f web
# MySQL 접속 확인
docker compose exec db mysql -u${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE}
```


## 11. 방화벽 / 포트 열기 (GCP: VPC 방화벽 규칙 또는 인스턴스 태그 사용)

- 웹(80), MQTT(1883), SSH(22) 등 필요한 포트만 열고 출처 IP 제한 권장.


## 12. 문제 해결 팁

- permission denied on /var/run/docker.sock: 현재 사용자를 docker 그룹에 추가 후 세션 재시작 또는 sudo 사용
- docker compose 명령이 없으면 `docker compose version` 확인, 필요 시 Compose v2 설치
- .env는 민감정보가 포함되므로 Secret Manager 사용 권장


## 13. 후속 작업(권장)

- Flask-Migrate 등 마이그레이션 도구 도입
- Docker secrets 또는 GCP Secret Manager로 민감정보 관리
- 모니터링/로깅(Cloud Monitoring, 로그 수집)


---

파일이 준비되었습니다. 원하면 이 파일을 리포지토리에 커밋하고 푸시해 드리겠습니다. 어떤 메시지로 커밋할까요?
