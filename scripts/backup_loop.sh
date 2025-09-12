#!/usr/bin/env bash
set -euo pipefail

# Backup loop: run an initial dump and then run at each midnight (00:00) using GNU date
if [ -z "${MYSQL_USER:-}" ] || [ -z "${MYSQL_PASSWORD:-}" ] || [ -z "${MYSQL_DATABASE:-}" ]; then
  echo "Missing MYSQL_USER / MYSQL_PASSWORD / MYSQL_DATABASE environment variables"
  exit 2
fi

mkdir -p /backups

do_dump() {
  TIMESTAMP=$(date +%Y%m%d-%H%M%S)
  OUTFILE="/backups/smartcradle-${TIMESTAMP}.sql"
  echo "[$(date)] Creating DB dump to ${OUTFILE}"
  mysqldump -h db -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" "${MYSQL_DATABASE}" > "${OUTFILE}" 2>/tmp/backup_err || {
    echo "mysqldump failed, see /tmp/backup_err"
    cat /tmp/backup_err || true
    return 1
  }
  echo "[$(date)] Dump saved: ${OUTFILE}"
}

# initial dump on startup
do_dump || true

while true; do
  # compute seconds until next midnight (uses GNU date as in Debian-based images)
  now=$(date +%s)
  next=$(date -d 'tomorrow 00:00' +%s)
  sleep_seconds=$((next - now))
  echo "[$(date)] Sleeping for ${sleep_seconds} seconds until next run"
  sleep ${sleep_seconds}
  do_dump || true
done
