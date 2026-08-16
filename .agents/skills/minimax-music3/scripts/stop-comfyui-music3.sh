#!/usr/bin/env bash
set -e

PORT="${1:-8188}"
echo "[INFO] Stopping ComfyUI process on port $PORT..."

PIDS=$(lsof -ti :"$PORT" 2>/dev/null || true)
if [ -n "$PIDS" ]; then
    echo "[INFO] Terminating PID(s): $PIDS"
    # shellcheck disable=SC2086
    kill $PIDS 2>/dev/null || true
    sleep 2
fi

# Force cleanup if still running
pkill -f "ComfyUI-music3/main.py" 2>/dev/null || true
sleep 1

if lsof -i :"$PORT" >/dev/null 2>&1; then
    echo "[WARN] Port $PORT is still occupied!"
    lsof -i :"$PORT"
    exit 1
else
    echo "[SUCCESS] ComfyUI server stopped cleanly. Port $PORT released."
fi
