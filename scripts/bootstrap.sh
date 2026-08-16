#!/usr/bin/env bash
set -e

# One-shot zero-to-working bootstrap for the MiniMax-DGX-Spark package.
# Run:  bash scripts/bootstrap.sh [music3|h3]   (default: music3)
# It: sets up the environment, downloads the family's models, starts ComfyUI,
# and runs that family's smoke test. ENV-driven, no personal paths.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
FAMILY="${1:-music3}"

# Load node profile if provided
if [ -n "${NODE_PROFILE:-}" ] && [ -f "$NODE_PROFILE" ]; then
  set -a; . "$NODE_PROFILE"; set +a
fi

echo "=================================================="
echo " MiniMax ${FAMILY} Zero-to-Working One-Shot Bootstrap"
echo "=================================================="

echo "[STEP 1/4] Setting up ComfyUI & Python environment..."
bash "$SCRIPT_DIR/setup-env.sh"

echo "[STEP 2/4] Verifying and downloading model weights (family=$FAMILY)..."
bash "$SCRIPT_DIR/download-models.sh" "$FAMILY"

echo "[STEP 3/4] Launching ComfyUI server..."
bash "$SCRIPT_DIR/start-comfyui.sh" "$REPO_DIR/profiles/nodes.env"

echo "[STEP 4/4] Executing verification smoke test..."
if [ "$FAMILY" = "h3" ]; then
  ${PYTHON_BIN:-python3} "$REPO_DIR/h3/generate-video.py" --prompt "a calm ocean wave at dusk, photorealistic" --duration 5 --prefix smoke_test --host "${COMFY_HOST:-http://127.0.0.1:8188}"
else
  bash "$REPO_DIR/music3/smoke-test.sh"
fi

echo "=================================================="
echo "[SUCCESS] Zero-to-working bootstrap complete for $FAMILY!"
echo "ComfyUI MiniMax is online and ready."
echo "=================================================="
