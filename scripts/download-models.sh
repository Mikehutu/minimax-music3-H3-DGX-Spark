#!/usr/bin/env bash
set -e

# Portable model downloader for the MiniMax-DGX-Spark package.
# Downloads a family's checkpoints from the public HF hub into MODEL_ROOT.
#
# Usage:  scripts/download-models.sh [music3|h3] [MODEL_DIR]
#   family defaults to music3; MODEL_DIR overrides MODEL_ROOT/<family>.
#   ENV overrides: MODEL_ROOT, HF_REPO. Nothing personal/hardcoded except
#   the public HF repo IDs (which are shared by everyone).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

FAMILY="${1:-music3}"
MODEL_ROOT="${MODEL_ROOT:-$REPO_DIR/models}"

case "$FAMILY" in
  music3)
    HF_REPO="${HF_REPO:-Comfy-Org/MiniMax-Music-3}"
    MODEL_DIR="${2:-${MODEL_DIR:-$MODEL_ROOT/MiniMax-Music3-Comfy}}"
    FILES=(
      "diffusion_models/minimax_music3_dit_int8_convrot.safetensors"
      "text_encoders/minimax_music3_text_encoder_pruned_int8_convrot.safetensors"
      "vae/minimax_music3_dav.safetensors"
    )
    ;;
  h3)
    HF_REPO="${HF_REPO:-MiniMaxAI/MiniMax-H3}"
    MODEL_DIR="${2:-${MODEL_DIR:-$MODEL_ROOT/MiniMax-H3}}"
    FILES=(
      "diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors"
      "diffusion_models/minimax_h3_fl2va_pruned_bf16.safetensors"
      "diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors"
      "diffusion_models/minimax_h3_ref2va_pruned_bf16.safetensors"
      "text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"
      "vae/minimax_h3_video_vae_fp16.safetensors"
      "vae/minimax_h3_audio_vae_fp32.safetensors"
    )
    ;;
  *)
    echo "[ERROR] Unknown family '$FAMILY'. Use 'music3' or 'h3'." >&2
    exit 1
    ;;
esac

echo "=================================================="
echo " MiniMax ${FAMILY} Model Checkpoint Downloader"
echo " Source Repo: https://huggingface.co/$HF_REPO"
echo " Destination: $MODEL_DIR"
echo "=================================================="

mkdir -p "$MODEL_DIR/diffusion_models" "$MODEL_DIR/text_encoders" "$MODEL_DIR/vae"

# Check which files are already present
ALL_PRESENT=true
for file in "${FILES[@]}"; do
    if [ ! -f "$MODEL_DIR/$file" ]; then
        ALL_PRESENT=false
        break
    fi
done

if [ "$ALL_PRESENT" = true ]; then
    echo "[INFO] All required $FAMILY checkpoints already exist in $MODEL_DIR."
    ls -lh "$MODEL_DIR"/diffusion_models/* "$MODEL_DIR"/text_encoders/* "$MODEL_DIR"/vae/*
    exit 0
fi

echo "[INFO] Downloading missing $FAMILY checkpoints from Hugging Face ($HF_REPO)..."

# Method 1: hf CLI
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
    python3 - "$HF_REPO" "$MODEL_DIR" "${FILES[@]}" <<'PYEOF'
import os, sys
from huggingface_hub import hf_hub_download
repo_id, target_dir = sys.argv[1], sys.argv[2]
files = sys.argv[3:]
for f in files:
    out = os.path.join(target_dir, f)
    if not os.path.exists(out):
        print(f"[INFO] Downloading {f}...")
        hf_hub_download(repo_id=repo_id, filename=f, local_dir=target_dir)
    else:
        print(f"[INFO] Already exists: {f}")
PYEOF
fi

echo "[SUCCESS] All $FAMILY checkpoints verified in $MODEL_DIR!"
ls -lh "$MODEL_DIR"/diffusion_models/* "$MODEL_DIR"/text_encoders/* "$MODEL_DIR"/vae/*
