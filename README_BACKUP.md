Backup & restore for smartcradle MySQL

Overview

This repository includes simple scripts to create and restore SQL dumps from the MySQL container used by docker-compose.

Scripts

- `scripts/backup_mysql.sh`
  - Creates a timestamped SQL dump under `backups/` by default.
  - Usage: `./scripts/backup_mysql.sh` or `./scripts/backup_mysql.sh backups/mydump.sql`

- `scripts/restore_mysql.sh`
  - Restores a dump file into the database from `.env` credentials.
  - Usage: `./scripts/restore_mysql.sh backups/mydump.sql`

Scheduling

Two installers are provided depending on your OS:

- cron (Linux / generic): `scripts/install_cron.sh` — installs a crontab entry to run the backup daily at midnight (00:00).
- launchd (macOS): `scripts/install_launchd.sh` — installs a LaunchAgent that runs the backup daily at midnight.

Install examples

Cron (Linux):

```bash
./scripts/install_cron.sh
```

LaunchAgent (macOS):

```bash
./scripts/install_launchd.sh
```

Uninstall LaunchAgent (macOS):

```bash
./scripts/uninstall_launchd.sh
```

Notes

- Scripts read DB credentials from project root `.env`. Make sure `.env` exists and contains `MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_DATABASE`.
- The resulting dump files are saved to `backups/` which is gitignored by default.
- For production, use managed backups or scheduled jobs with secure secret handling.
