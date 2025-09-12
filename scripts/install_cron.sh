#!/usr/bin/env bash
set -euo pipefail

# Installs a crontab entry to run the backup script daily at 00:00 (midnight)
ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CRON_CMD="cd $ROOT_DIR && ./scripts/backup_mysql.sh >> $ROOT_DIR/backups/backup.log 2>&1"

# create a temp file with the current crontab plus our job if not already present
(crontab -l 2>/dev/null || true) | grep -Fv "$CRON_CMD" > /tmp/current_cron || true
printf "0 0 * * * %s\n" "$CRON_CMD" >> /tmp/current_cron
crontab /tmp/current_cron
rm -f /tmp/current_cron

echo "Installed cron job: daily at midnight"
