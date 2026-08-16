#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

# Target directory where models will be placed (Comfy-Org layout)
MODEL_DIR="${1:-${MODEL_DIR:-$REPO_DIR/models/MiniMax-Music3-Comfy}}"
HF_REPO="Comfy-Org/MiniMax-Music-3"

echo "=================================================="
echo " MiniMax Music3 Model Checkpoint Downloader"
echo " Source Repo: https://huggingface.co/$HF_REPO"
echo " Destination: $MODEL_DIR"
echo "=================================================="

mkdir -p "$MODEL_DIR/diffusion_models" "$MODEL_DIR/text_encoders" "$MODEL_DIR/vae"

FILES=(
    "diffusion_models/minimax_music3_dit_fp16.safetensors"
    "text_encoders/minimax_music3_text_encoder_pruned_int8_convrot.safetensors"
    "vae/minimax_music3_dav.safetensors"
)

# Check which files are already present
ALL_PRESENT=true
for file in "${FILES[@]}"; do
    if [ ! -f "$MODEL_DIR/$file" ]; then
        ALL_PRESENT=false
        break
    fi
done

if [ "$ALL_PRESENT" = true ]; then
    echo "[INFO] All required MiniMax Music3 checkpoints already exist in $MODEL_DIR."
    ls -lh "$MODEL_DIR"/diffusion_models/* "$MODEL_DIR"/text_encoders/* "$MODEL_DIR"/vae/*
    exit 0
fi

echo "[INFO] Downloading missing checkpoints from Hugging Face ($HF_REPO)..."

# Method 1: huggingface-cli / hf CLI
if command -v hf >/dev/null 2>&1; then
    echo "[INFO] Using hf CLI..."
    for file in "${FILES[@]}"; do
        if [ ! -f "$MODEL_DIR/$file" ]; then
            echo "[INFO] Downloading $file..."
            hf download "$HF_REPO" "$file" --local-dir "$MODEL_DIR"
        fi
    done
elif command -v huggingface-cli >/dev/null 2>&1; then
    echo "[INFO] Using huggingface-cli..."
    for file in "${FILES[@]}"; do
        if [ ! -f "$MODEL_DIR/$file" ]; then
            echo "[INFO] Downloading $file..."
            huggingface-cli download "$HF_REPO" "$file" --local-dir "$MODEL_DIR"
        fi
    done
else
    # Method 2: Python huggingface_hub fallback
    echo "[INFO] Using Python huggingface_hub fallback..."
    python3 -c "
import os, sys
from huggingface_hub import hf_hub_download

repo_id = '$HF_REPO'
target_dir = '$MODEL_DIR'
files = [
    'diffusion_models/minimax_music3_dit_fp16.safetensors',
    'text_encoders/minimax_music3_text_encoder_pruned_int8_convrot.safetensors',
    'vae/minimax_music3_dav.safetensors'
]

for f in files:
    out_path = os.path.join(target_dir, f)
    if not os.path.exists(out_path):
        print(f'[INFO] Downloading {f}...')
        hf_hub_download(repo_id=repo_id, filename=f, local_dir=target_dir)
    else:
        print(f'[INFO] Already exists: {f}')
"
fi

echo "[SUCCESS] All MiniMax Music3 checkpoints verified in $MODEL_DIR!"
ls -lh "$MODEL_DIR"/diffusion_models/* "$MODEL_DIR"/text_encoders/* "$MODEL_DIR"/vae/*
