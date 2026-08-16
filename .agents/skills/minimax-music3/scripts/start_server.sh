#!/usr/bin/env bash
set -e

COMFY_DIR="${COMFY_DIR:-$HOME/ComfyUI-music3}"
PYTHON_BIN="${PYTHON_BIN:-$HOME/ComfyUI/comfyui-env/bin/python}"
PORT=8188

if lsof -i :$PORT >/dev/null 2>&1; then
    echo "[INFO] ComfyUI server is already running on port $PORT."
    exit 0
fi

echo "[INFO] Starting ComfyUI server with MiniMax Music3 on port $PORT..."
nohup $PYTHON_BIN $COMFY_DIR/main.py --listen 0.0.0.0 --port $PORT --disable-pinned-memory > "$COMFY_DIR/comfy_server.log" 2>&1 &

echo "[INFO] Waiting for server to become responsive..."
for i in {1..30}; do
    if curl -s "http://127.0.0.1:$PORT/system_stats" >/dev/null 2>&1; then
        echo "[INFO] ComfyUI server started successfully (PID: $!)."
        exit 0
    fi
    sleep 1
done

echo "[ERROR] ComfyUI server failed to respond within 30 seconds. Check logs at $COMFY_DIR/comfy_server.log"
exit 1
