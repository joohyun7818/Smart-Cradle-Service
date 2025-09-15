
Docker로 프로젝트 실행하기

이 문서는 이 저장소를 Docker와 Docker Compose로 실행하는 방법과, 코드 변경 시 이미지를 갱신하는 워크플로우, 데이터 영속성 및 백업 관련 권장사항을 정리합니다.

## 구성 요약
- 서비스: `web` (Flask), `db` (MySQL), `mosquitto` (MQTT), `backup` (덤프 생성)
- 환경변수: 루트의 `.env`와 `smart_cradle_server/.env.example`. 실제 시크릿은 `.env`에만 저장하세요.

## 사전 준비
- Docker와 Docker Compose(또는 Docker Desktop)이 설치되어 있어야 합니다.
- 이 저장소를 클론하고 루트 디렉터리로 이동하세요.

## 1) 초기 설정

```bash
# 루트 .env (Compose에서 사용)
cp .env.example .env

# 웹 서비스 전용 예시 복사
cp smart_cradle_server/.env.example smart_cradle_server/.env

# .env 파일의 값(MYSQL_*, MQTT_BROKER_HOST 등)을 환경에 맞게 수정하세요.
```

## 2) 이미지 빌드 및 서비스 시작

```bash
docker compose build --pull
docker compose up -d
```

## 3) 상태 및 로그 확인

```bash
docker compose ps
docker compose logs -f web
docker compose logs -f db
docker compose logs -f backup
```

## 데이터 영속성
- `db` 서비스는 `db_data`라는 named volume에 MySQL 데이터를 저장합니다. 이 볼륨이 유지되는 한 데이터는 컨테이너 삭제 후에도 보존됩니다.
- 볼륨을 삭제하려면 `docker compose down -v`를 사용하므로 주의하세요.

## 백업
- `backup` 서비스는 `./backups`에 덤프를 저장하도록 구성되어 있습니다.
- 수동 백업:

```bash
./scripts/backup_mysql.sh
```

## 업데이트 워크플로

### 개발(빠른 반복)
- 소스 수정 후 개발 중이라면 `web`을 바인드 마운트하도록 Compose를 변경하면 코드 변경이 즉시 반영됩니다.
- 이미지 재빌드 후 서비스 재시작:

```bash
docker compose build --no-cache web
docker compose up -d --no-deps --build web
```

### 배포(팀 공유)
- 이미지 빌드 및 레지스트리에 푸시:

```bash
docker build -t <registry_user>/smart-cradle-server:latest ./smart_cradle_server
docker push <registry_user>/smart-cradle-server:latest
```

- `docker-compose.yml`에서 `web`을 `image: <registry_user>/smart-cradle-server:latest`로 변경 후, 원격에서 pull 및 재시작:

```bash
docker compose pull
docker compose up -d
```

## 보안 권장
- `.env` 파일을 레포지토리에 커밋하지 마세요. `.gitignore`가 포함되어 있습니다.
- 운영 환경은 Docker Secrets, HashiCorp Vault 등 안전한 시크릿 스토어 사용을 권장합니다.

## 디버깅 팁

```bash
# 컨테이너 쉘 접근
docker compose exec web bash
docker compose exec db bash

# DB 접속
docker compose exec db mysql -u${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE}
```

## 추가 자료
- 백업/복원 스크립트: `scripts/backup_mysql.sh`, `scripts/restore_mysql.sh`
- 스케줄러 설치: `scripts/install_cron.sh` (Linux), `scripts/install_launchd.sh` (macOS)