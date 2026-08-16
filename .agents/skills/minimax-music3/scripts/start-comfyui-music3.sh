#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

PROFILE="${1:-$REPO_DIR/profiles/production.env}"
if [ -f "$PROFILE" ]; then
    echo "[INFO] Loading profile: $PROFILE"
    # shellcheck disable=SC1090
    source "$PROFILE"
else
    echo "[WARN] Profile not found at $PROFILE, using default environment."
    COMFY_DIR="${COMFY_DIR:-$HOME/ComfyUI-music3}"
    PYTHON_BIN="${PYTHON_BIN:-$HOME/ComfyUI/comfyui-env/bin/python}"
    PORT=8188
    HOST="0.0.0.0"
    EXTRA_FLAGS="--disable-pinned-memory"
fi

if lsof -i :"$PORT" >/dev/null 2>&1; then
    echo "[INFO] ComfyUI is already running and listening on port $PORT."
    exit 0
fi

echo "[INFO] Launching ComfyUI for MiniMax Music3 on $HOST:$PORT..."
# shellcheck disable=SC2086
nohup "$PYTHON_BIN" "$COMFY_DIR/main.py" --listen "$HOST" --port "$PORT" $EXTRA_FLAGS > "$COMFY_DIR/comfy_server.log" 2>&1 &
SERVER_PID=$!

echo "[INFO] ComfyUI process spawned (PID: $SERVER_PID). Awaiting server readiness..."
for i in {1..30}; do
    if curl -sf "http://127.0.0.1:$PORT/system_stats" >/dev/null 2>&1; then
        echo "[SUCCESS] ComfyUI MiniMax Music3 server is live and responsive at http://127.0.0.1:$PORT!"
        exit 0
    fi
    sleep 1
done

echo "[ERROR] Server failed to answer /system_stats within 30s. Inspect logs:"
tail -n 20 "$COMFY_DIR/comfy_server.log"
exit 1
