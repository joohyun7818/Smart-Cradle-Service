#!/usr/bin/env bash
set -euo pipefail

# macOS: install a LaunchAgent plist to run the backup script daily at midnight
ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
LAUNCH_PLIST_LABEL="com.smartcradle.backup"
PLIST_PATH="$HOME/Library/LaunchAgents/${LAUNCH_PLIST_LABEL}.plist"

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>${LAUNCH_PLIST_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
      <string>$ROOT_DIR/scripts/backup_mysql.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
      <key>Hour</key>
      <integer>0</integer>
      <key>Minute</key>
      <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>$ROOT_DIR/backups/backup.log</string>
    <key>StandardErrorPath</key>
    <string>$ROOT_DIR/backups/backup.log</string>
    <key>RunAtLoad</key>
    <true/>
  </dict>
</plist>
EOF

# load the plist
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

echo "Installed LaunchAgent at $PLIST_PATH (runs daily at 00:00)"
