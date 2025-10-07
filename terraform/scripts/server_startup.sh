#!/bin/bash
set -e

echo "=== 서버 인스턴스 초기 설정 시작 ==="

# admin 사용자 생성 및 SSH 키 설정
echo "=== admin 사용자 생성 ==="
if ! id -u admin > /dev/null 2>&1; then
  # admin 그룹이 이미 존재하면 해당 그룹 사용, 없으면 자동 생성
  if getent group admin > /dev/null 2>&1; then
    useradd -m -s /bin/bash -g admin admin
  else
    useradd -m -s /bin/bash admin
  fi
  usermod -aG sudo admin
  echo "admin ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/admin
  chmod 0440 /etc/sudoers.d/admin
  
  # SSH 디렉터리 생성
  mkdir -p /home/admin/.ssh
  chmod 700 /home/admin/.ssh
  
  # SSH 공개키 추가
  echo "${ssh_public_key}" > /home/admin/.ssh/authorized_keys
  chmod 600 /home/admin/.ssh/authorized_keys
  chown -R admin:admin /home/admin/.ssh
  
  echo "admin 사용자 생성 완료"
fi

# 시스템 업데이트
apt-get update
apt-get upgrade -y

# 필수 패키지 설치 (git 제거 - Docker 이미지 사용으로 불필요)
apt-get install -y net-tools curl ca-certificates gnupg lsb-release vim-tiny

# Docker 설치
echo "=== Docker 설치 ==="
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Docker 서비스 시작
systemctl start docker
systemctl enable docker

# 작업 디렉터리 생성
echo "=== 작업 디렉터리 생성 ==="
mkdir -p /opt/smart-cradle
cd /opt/smart-cradle

# .env 파일 생성
echo "=== .env 파일 생성 ==="
cat > .env <<'ENV_FILE'
MYSQL_ROOT_PASSWORD=root_password_1234
MYSQL_DATABASE=${mysql_database}
MYSQL_USER=${mysql_user}
MYSQL_PASSWORD=${mysql_password}
MYSQL_HOST=${mysql_host}
MYSQL_PORT=${mysql_port}
MQTT_BROKER_HOST=${mqtt_broker_host}
MQTT_BROKER_PORT=${mqtt_broker_port}
SECRET_KEY=${secret_key}
ENV_FILE

chmod 600 .env

# 데이터 디렉터리 생성
echo "=== 데이터 디렉터리 생성 ==="
mkdir -p data
chmod 700 data

# Docker Compose 파일 생성 (Git 클론 불필요!)
echo "=== docker-compose.yml 생성 ==="
cat > docker-compose.yml <<'DOCKER_COMPOSE'
services:
  web:
    image: joohyun7818/smart-cradle-flask:latest
    ports:
      - "80:80"
    env_file:
      - ./.env
    depends_on:
      - mosquitto
    restart: unless-stopped

  mosquitto:
    image: eclipse-mosquitto:2
    ports:
      - "1883:1883"
    volumes:
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf
    restart: unless-stopped

volumes:
  db_data:
DOCKER_COMPOSE

# Mosquitto 설정 파일 생성
echo "=== mosquitto.conf 생성 ==="
cat > mosquitto.conf <<'MOSQUITTO_CONF'
listener 1883
allow_anonymous true
MOSQUITTO_CONF

# Docker 이미지 pull 및 서비스 시작
echo "=== Docker 컨테이너 시작 ==="
docker compose pull
docker compose up -d

# 컨테이너 상태 확인
echo "=== 컨테이너 상태 확인 ==="
sleep 10
docker compose ps

# 로그 확인
echo "=== 초기 로그 확인 ==="
docker compose logs --tail=50

# 데이터 정리 스크립트 생성
echo "=== 데이터 정리 스크립트 생성 ==="
mkdir -p /opt/smart-cradle/scripts
mkdir -p /opt/smart-cradle/logs

cat > /opt/smart-cradle/scripts/cleanup_old_frames.py <<'CLEANUP_SCRIPT'
#!/usr/bin/env python3
"""
영상 프레임 자동 삭제 스크립트
10일 이상 된 비디오 프레임을 자동으로 삭제합니다.
"""

import os
import sys
import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 환경 변수에서 DB 설정 읽기
db_user = os.getenv('MYSQL_USER', '${mysql_user}')
db_pass = os.getenv('MYSQL_PASSWORD', '${mysql_password}')
db_host = os.getenv('MYSQL_HOST', '${mysql_host}')
db_port = os.getenv('MYSQL_PORT', '${mysql_port}')
db_name = os.getenv('MYSQL_DATABASE', '${mysql_database}')

# 데이터베이스 연결
sql_uri = f'mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}'
engine = create_engine(sql_uri)
Session = sessionmaker(bind=engine)

def cleanup_old_frames(days=10):
    """지정된 일수보다 오래된 비디오 프레임을 삭제합니다."""
    session = Session()
    
    try:
        cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        
        # 삭제할 프레임 수 확인
        count_query = text("""
            SELECT COUNT(*) as count 
            FROM video_frames 
            WHERE timestamp < :cutoff_date
        """)
        
        result = session.execute(count_query, {'cutoff_date': cutoff_date})
        count = result.fetchone()[0]
        
        if count == 0:
            print(f"[{datetime.datetime.now()}] 삭제할 프레임이 없습니다. (기준: {days}일 이전)")
            return
        
        print(f"[{datetime.datetime.now()}] {days}일 이전 프레임 {count}개를 삭제합니다...")
        
        # 오래된 프레임 삭제
        delete_query = text("""
            DELETE FROM video_frames 
            WHERE timestamp < :cutoff_date
        """)
        
        session.execute(delete_query, {'cutoff_date': cutoff_date})
        session.commit()
        
        print(f"[{datetime.datetime.now()}] ✅ {count}개의 프레임을 성공적으로 삭제했습니다.")
        
    except Exception as e:
        print(f"[{datetime.datetime.now()}] ❌ 오류 발생: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='비디오 프레임 자동 삭제 스크립트')
    parser.add_argument('--days', type=int, default=10, 
                        help='삭제 기준 일수 (기본값: 10일)')
    
    args = parser.parse_args()
    cleanup_old_frames(args.days)
CLEANUP_SCRIPT

chmod +x /opt/smart-cradle/scripts/cleanup_old_frames.py

# Python 패키지 설치 (pymysql, sqlalchemy)
echo "=== Python 패키지 설치 ==="
apt-get install -y python3-pip
pip3 install pymysql sqlalchemy

# Cron Job 등록 (매일 새벽 3시에 실행)
echo "=== 데이터 정리 Cron Job 등록 ==="
CRON_JOB="0 3 * * * cd /opt/smart-cradle && /usr/bin/python3 /opt/smart-cradle/scripts/cleanup_old_frames.py --days 10 >> /opt/smart-cradle/logs/cleanup.log 2>&1"

# 기존 cleanup cron job 제거 (있으면)
(crontab -l 2>/dev/null | grep -v "cleanup_old_frames.py") | crontab - 2>/dev/null || true

# 새로운 cron job 추가
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ 데이터 정리 Cron Job 등록 완료 (매일 새벽 3시 실행)"

echo "=== 서버 인스턴스 설정 완료 ==="
echo "웹 서비스는 http://$(curl -s ifconfig.me) 에서 접속 가능합니다"
echo "데이터 정리: 매일 새벽 3시에 10일 이상된 프레임 자동 삭제"
