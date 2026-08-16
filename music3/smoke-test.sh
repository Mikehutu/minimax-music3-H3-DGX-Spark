#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_BIN="${PYTHON_BIN:-python3}"
HOST="${1:-http://127.0.0.1:8188}"

echo "=================================================="
echo " MiniMax Music3 End-to-End Smoke Test (10s Clip)"
echo " Target Host: $HOST"
echo "=================================================="

# Ensure server is active
if ! curl -sf "$HOST/system_stats" >/dev/null 2>&1; then
    echo "[INFO] ComfyUI server is offline. Starting server locally..."
    bash "$REPO_DIR/scripts/start-comfyui.sh"
fi

echo "[INFO] Running smoke test generation..."
"$PYTHON_BIN" "$SCRIPT_DIR/generate.py" \
  --host "$HOST" \
  --caption "High-energy synthwave electro track, punchy kick, analog synth brass" \
  --lyrics "[instrumental]" \
  --duration 10.0 \
  --prefix "smoke_test" \
  --format mp3

echo "=================================================="
echo "[SUCCESS] MiniMax Music3 smoke test completed successfully!"
echo "=================================================="
