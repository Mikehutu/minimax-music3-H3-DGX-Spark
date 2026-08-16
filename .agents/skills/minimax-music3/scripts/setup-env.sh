#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

INSTALL_DIR="${1:-$HOME}"
COMFY_DIR="$INSTALL_DIR/ComfyUI-music3"
VENV_DIR="$INSTALL_DIR/ComfyUI/comfyui-env"
MODEL_DIR="${2:-${HOME}/ComfyUI-music3/models/MiniMax-Music3-Comfy}"

echo "=================================================="
echo " MiniMax Music3 ComfyUI Environment Setup"
echo " ComfyUI Path: $COMFY_DIR"
echo " Virtualenv:   $VENV_DIR"
echo " Models Path:  $MODEL_DIR"
echo "=================================================="

# 1. Verify system tools
if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "[WARN] ffmpeg is not found on PATH. Install it via 'sudo apt-get install -y ffmpeg'."
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
"$PIP_BIN" install -r "$COMFY_DIR/requirements.txt" || true
"$PIP_BIN" install "comfy-kitchen>=0.2.31" soundfile torchaudio huggingface_hub

# 5. Configure extra_model_paths.yaml
echo "[INFO] Configuring extra_model_paths.yaml..."
cat <<EOF > "$COMFY_DIR/extra_model_paths.yaml"
music3:
    base_path: $MODEL_DIR/
    diffusion_models: diffusion_models/
    text_encoders: text_encoders/
    vae: vae/
EOF

echo "[SUCCESS] Environment setup complete!"
echo "  - Python: $PYTHON_BIN"
echo "  - ComfyUI: $COMFY_DIR"
echo "  - Model config: $COMFY_DIR/extra_model_paths.yaml"
