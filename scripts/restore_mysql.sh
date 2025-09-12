#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/restore_mysql.sh path/to/dump.sql
# Restores the provided dump into the database defined in .env

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 path/to/dump.sql"
  exit 2
fi

DUMP_FILE=$1
ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source "$ROOT_DIR/.env" || true

if [ ! -f "$DUMP_FILE" ]; then
  echo "Dump file not found: $DUMP_FILE"
  exit 3
fi

# Stream the dump into the mysql client inside the db container
cat "$DUMP_FILE" | docker compose exec -T db sh -c 'mysql -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" "${MYSQL_DATABASE}"'

echo "Restore completed"
