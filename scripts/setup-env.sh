#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

INSTALL_DIR="${1:-$REPO_DIR/..}"
COMFY_DIR="$INSTALL_DIR/ComfyUI-music3"
VENV_DIR="$INSTALL_DIR/comfyui-env"
MODEL_DIR="${2:-${MODEL_DIR:-$REPO_DIR/models/MiniMax-Music3-Comfy}}"

echo "=================================================="
echo " MiniMax Music3 ComfyUI Environment Setup"
echo " ComfyUI Path: $COMFY_DIR"
echo " Virtualenv:   $VENV_DIR"
echo " Models Path:  $MODEL_DIR"
echo "=================================================="

# 1. Verify system tools
if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "[WARN] ffmpeg is not found on PATH. Install it via your system package manager."
fi

# 2. Check or create Python virtual environment
if [ ! -f "$VENV_DIR/bin/python" ]; then
    echo "[INFO] Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"

# 3. Stage ComfyUI if not already present
if [ ! -f "$COMFY_DIR/main.py" ]; then
    echo "[INFO] Staging fresh ComfyUI at $COMFY_DIR..."
    git clone https://github.com/comfyanonymous/ComfyUI.git "$COMFY_DIR"
fi

# 4. Install Python dependencies
echo "[INFO] Installing / upgrading required Python packages..."
"$PIP_BIN" install --upgrade pip
"$PIP_BIN" install torch torchvision torchaudio
"$PIP_BIN" install -r "$COMFY_DIR/requirements.txt" || true
"$PIP_BIN" install "comfy-kitchen>=0.2.31" "comfy-aimdo>=0.4.10" soundfile pydub

# 5. Link / stage model directory
mkdir -p "$COMFY_DIR/models/diffusion_models" "$COMFY_DIR/models/text_encoders" "$COMFY_DIR/models/vae"
if [ -d "$MODEL_DIR" ]; then
    echo "[INFO] Linking models from $MODEL_DIR..."
    [ -d "$MODEL_DIR/diffusion_models" ] && ln -sfn "$MODEL_DIR/diffusion_models"/* "$COMFY_DIR/models/diffusion_models/" 2>/dev/null || true
    [ -d "$MODEL_DIR/text_encoders" ] && ln -sfn "$MODEL_DIR/text_encoders"/* "$COMFY_DIR/models/text_encoders/" 2>/dev/null || true
    [ -d "$MODEL_DIR/vae" ] && ln -sfn "$MODEL_DIR/vae"/* "$COMFY_DIR/models/vae/" 2>/dev/null || true
fi

echo "=================================================="
echo "[SUCCESS] Environment setup complete!"
echo "=================================================="
