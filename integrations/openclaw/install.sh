#!/bin/bash
# Git-Map OpenClaw Integration Installer
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GITMAP_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="${OPENCLAW_STATE_DIR:-$HOME/.openclaw}/logs"

mkdir -p "$LOG_DIR"

if [ -f "$SCRIPT_DIR/server.pid" ] && kill -0 "$(cat "$SCRIPT_DIR/server.pid")" 2>/dev/null; then
    echo "gitmap-skill server already running with pid $(cat "$SCRIPT_DIR/server.pid")"
else
    echo "Starting gitmap-skill server..."
    if command -v uv >/dev/null 2>&1; then
        GITMAP_ROOT="$GITMAP_ROOT" nohup uv run --no-project --with deepdiff --with rich --with click \
            python "$SCRIPT_DIR/server.py" > "$LOG_DIR/gitmap-skill.log" 2>&1 &
    else
        GITMAP_ROOT="$GITMAP_ROOT" nohup "${PYTHON_BIN:-python3}" "$SCRIPT_DIR/server.py" > "$LOG_DIR/gitmap-skill.log" 2>&1 &
    fi
    echo $! > "$SCRIPT_DIR/server.pid"
fi

echo "Installing OpenClaw plugin..."
openclaw plugins install -l "$SCRIPT_DIR"

echo "Done! Restart the OpenClaw gateway to activate."
