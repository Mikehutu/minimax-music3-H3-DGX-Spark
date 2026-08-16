#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

echo "=================================================="
echo " MiniMax Music3 Zero-to-Working One-Shot Bootstrap"
echo "=================================================="

# Step 1: Check and setup environment
echo "[STEP 1/4] Setting up ComfyUI & Python environment..."
bash "$SCRIPT_DIR/setup-env.sh"

# Step 2: Download models from Hugging Face if missing
echo "[STEP 2/4] Verifying and downloading model weights..."
bash "$SCRIPT_DIR/download-models.sh"

# Step 3: Launch ComfyUI server with cluster-safe memory flags
echo "[STEP 3/4] Launching ComfyUI server..."
bash "$SCRIPT_DIR/start-comfyui-music3.sh" "$REPO_DIR/profiles/production.env"

# Step 4: Run end-to-end smoke test
echo "[STEP 4/4] Executing verification smoke test (10s audio generation)..."
bash "$SCRIPT_DIR/smoke-test.sh"

echo "=================================================="
echo "[SUCCESS] Zero-to-working bootstrap complete!"
echo "ComfyUI MiniMax Music3 is online and ready for production."
echo "=================================================="
