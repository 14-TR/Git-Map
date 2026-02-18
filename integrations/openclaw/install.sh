#!/bin/bash
# Git-Map OpenClaw Integration Installer
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting gitmap-skill server..."
nohup python3 "$SCRIPT_DIR/server.py" > ~/.openclaw/logs/gitmap-skill.log 2>&1 &
echo $! > "$SCRIPT_DIR/server.pid"

echo "Installing OpenClaw plugin..."
openclaw plugins install -l "$SCRIPT_DIR"

echo "Done! Restart the OpenClaw gateway to activate."
