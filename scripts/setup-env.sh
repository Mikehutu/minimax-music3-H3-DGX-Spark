#!/usr/bin/env bash
set -e

# Portable environment setup for the MiniMax-DGX-Spark package (music3 + h3).
# Everything is ENV-driven from profiles/nodes.env; no personal paths.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

# Load node profile if provided, else defaults (exported so children see them)
if [ -n "${NODE_PROFILE:-}" ] && [ -f "$NODE_PROFILE" ]; then
  set -a; . "$NODE_PROFILE"; set +a
fi

INSTALL_DIR="${INSTALL_DIR:-$REPO_DIR/..}"
COMFY_DIR="${COMFY_DIR:-$INSTALL_DIR/ComfyUI}"
VENV_DIR="${VENV_DIR:-$INSTALL_DIR/comfyui-env}"
MODEL_ROOT="${MODEL_ROOT:-$COMFY_DIR/models}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

# Family-specific model dirs (both under MODEL_ROOT):
MUSIC3_DIR="${MUSIC3_DIR:-$MODEL_ROOT/MiniMax-Music3-Comfy}"
H3_DIR="${H3_DIR:-$MODEL_ROOT/MiniMax-H3}"

if [ ! -f "$VENV_DIR/bin/python" ]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi
PYTHON_BIN="$VENV_DIR/bin/python"; PIP_BIN="$VENV_DIR/bin/pip"

if [ ! -f "$COMFY_DIR/main.py" ]; then
  git clone https://github.com/comfyanonymous/ComfyUI.git "$COMFY_DIR"
fi

"$PIP_BIN" install --upgrade pip
"$PIP_BIN" install torch torchvision torchaudio
"$PIP_BIN" install -r "$COMFY_DIR/requirements.txt" || true
"$PIP_BIN" install "comfy-kitchen>=0.2.31" "comfy-aimdo>=0.4.10" soundfile pydub

# Model dirs prepared (both families)
mkdir -p "$COMFY_DIR/models/diffusion_models" "$COMFY_DIR/models/text_encoders" "$COMFY_DIR/models/vae"
mkdir -p "$MUSIC3_DIR/diffusion_models" "$MUSIC3_DIR/text_encoders" "$MUSIC3_DIR/vae"
mkdir -p "$H3_DIR/diffusion_models" "$H3_DIR/text_encoders" "$H3_DIR/vae"

# Write extra_model_paths.yaml exposing both families to ComfyUI
cat > "$COMFY_DIR/extra_model_paths.yaml" <<EOF
music3:
    base_path: $MUSIC3_DIR/
    diffusion_models: diffusion_models/
    text_encoders: text_encoders/
    vae: vae/
h3:
    base_path: $H3_DIR/
    diffusion_models: diffusion_models/
    text_encoders: text_encoders/
    vae: vae/
EOF

echo "[SUCCESS] Environment ready:"
echo "  ComfyUI:  $COMFY_DIR"
echo "  Python:   $PYTHON_BIN"
echo "  Music3:   $MUSIC3_DIR"
echo "  H3:       $H3_DIR"
echo "  extra_model_paths.yaml written."
