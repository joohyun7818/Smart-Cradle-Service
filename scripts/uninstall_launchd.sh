#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
LAUNCH_PLIST_LABEL="com.smartcradle.backup"
PLIST_PATH="$HOME/Library/LaunchAgents/${LAUNCH_PLIST_LABEL}.plist"

launchctl unload "$PLIST_PATH" 2>/dev/null || true
rm -f "$PLIST_PATH"

echo "Uninstalled LaunchAgent: $PLIST_PATH"
