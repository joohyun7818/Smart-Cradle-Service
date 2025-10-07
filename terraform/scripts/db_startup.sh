#!/bin/bash
set -e

echo "=== DB 인스턴스 초기 설정 시작 ==="

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

# 필수 패키지 설치
apt-get install -y net-tools git curl ca-certificates gnupg lsb-release vim-tiny

# MySQL 서버 설치
echo "=== MySQL 서버 설치 ==="
apt-get install -y mysql-server

# MySQL 서비스 시작
systemctl start mysql
systemctl enable mysql

# MySQL root 비밀번호 설정
echo "=== MySQL root 비밀번호 설정 ==="
mysql -u root <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${mysql_root_password}';
FLUSH PRIVILEGES;
EOF

# 데이터베이스 및 사용자 생성
echo "=== 데이터베이스 및 사용자 생성 ==="
mysql -u root -p'${mysql_root_password}' <<EOF
CREATE DATABASE IF NOT EXISTS ${mysql_database};
CREATE USER IF NOT EXISTS '${mysql_user}'@'%' IDENTIFIED BY '${mysql_password}';
GRANT ALL PRIVILEGES ON ${mysql_database}.* TO '${mysql_user}'@'%';
FLUSH PRIVILEGES;
EOF

# MySQL 외부 연결 허용
echo "=== MySQL 외부 연결 설정 ==="
cp /etc/mysql/mysql.conf.d/mysqld.cnf /etc/mysql/mysql.conf.d/mysqld.cnf.backup
sed -i 's/bind-address\s*=\s*127\.0\.0\.1/bind-address = 0.0.0.0/' /etc/mysql/mysql.conf.d/mysqld.cnf

# MySQL 재시작
systemctl restart mysql

# 백업 디렉터리 생성
echo "=== 백업 디렉터리 생성 ==="
mkdir -p /home/backups
chmod 700 /home/backups

# 백업 스크립트 생성
cat > /home/backups/daily_backup.sh <<'BACKUP_SCRIPT'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mysqldump -u ${mysql_user} -p'${mysql_password}' ${mysql_database} > /home/backups/${mysql_database}_$${DATE}.sql
find /home/backups -name "*.sql" -mtime +7 -delete
BACKUP_SCRIPT

chmod +x /home/backups/daily_backup.sh

# 크론탭에 백업 스케줄 추가 (매일 오전 2시)
echo "=== 백업 크론탭 설정 ==="
(crontab -l 2>/dev/null; echo "0 2 * * * /home/backups/daily_backup.sh") | crontab -

echo "=== DB 인스턴스 설정 완료 ==="
