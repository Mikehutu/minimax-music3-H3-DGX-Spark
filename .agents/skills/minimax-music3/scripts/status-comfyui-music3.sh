#!/usr/bin/env bash
set -e

HOST="${1:-http://127.0.0.1:8188}"
echo "=================================================="
echo " ComfyUI MiniMax Music3 Cluster Status"
echo " Target: $HOST"
echo "=================================================="

if curl -sf "$HOST/system_stats" >/dev/null 2>&1; then
    echo "[STATUS] ONLINE"
    echo "--- System & VRAM Metrics ---"
    curl -s "$HOST/system_stats" | python3 -m json.tool || true
    echo ""
    echo "--- Active Nodes Check ---"
    curl -s "$HOST/object_info" | python3 -c "
import sys, json
info = json.load(sys.stdin)
music_nodes = ['MiniMaxMusic3TextEncode', 'EmptyMiniMaxMusic3LatentAudio', 'UNETLoader', 'CLIPLoader', 'VAELoader', 'KSampler', 'VAEDecodeAudio']
for k in music_nodes:
    print(f'  {k:30}: {\"AVAILABLE\" if k in info else \"MISSING\"}')
"
else
    echo "[STATUS] OFFLINE or UNREACHABLE"
    echo "[HINT] Verify target IP, port, or launch server locally using scripts/start-comfyui-music3.sh"
    exit 1
fi
