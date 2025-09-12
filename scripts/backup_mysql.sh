#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/backup_mysql.sh [output-file]
# If no output-file is provided, script writes to backups/smartcradle-YYYYMMDD-HHMMSS.sql

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source "$ROOT_DIR/.env" || true

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUT_DIR="$ROOT_DIR/backups"
mkdir -p "$OUT_DIR"
OUT_FILE=${1:-"$OUT_DIR/smartcradle-$TIMESTAMP.sql"}

# Run mysqldump inside the db container and write to host file
# Uses docker compose so must be executed from project root

echo "Creating DB dump to $OUT_FILE"

docker compose exec db sh -c 'exec mysqldump -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" "${MYSQL_DATABASE}"' > "$OUT_FILE"

if [ $? -eq 0 ]; then
  echo "Dump saved: $OUT_FILE"
else
  echo "Dump failed" >&2
  exit 1
fi
