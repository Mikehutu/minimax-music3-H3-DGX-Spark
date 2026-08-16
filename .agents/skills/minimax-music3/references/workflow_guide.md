# MiniMax Music3 Architecture and Quality Guide

## 1. Architecture Overview

MiniMax Music3 is a high-fidelity text-to-music generation system:
1. **Autoregressive Text Encoder (Acoustic Conditioning)**:
   - File: `minimax_music3_text_encoder_pruned_int8_convrot.safetensors` (~9.20 GB)
   - Function: Converts style prompt + lyrics tokens into acoustic conditioning frames.
2. **Diffusion Transformer (DiT Backbone)**:
   - File: `minimax_music3_dit_fp16.safetensors` (~4.91 GB)
   - Function: Flow-matching continuous diffusion model generating 128-channel audio latents.
3. **Discrete Acoustic VAE (DAV Decoder)**:
   - File: `minimax_music3_dav.safetensors` (~216 MB)
   - Function: Decodes latent representations into 44.1 kHz stereo waveforms.

Total resident footprint: **~13.6 GB model weights** (Peak VRAM: **~4.4 GB** under dynamic offload).

---

## 2. The Golden Rules for Realistic Drums & Quality

- **Front-load physical drum descriptors**: Mention *acoustic kick drum, cracking snare on 2 and 4, swinging dusty hi-hats, deep bassline* to prevent ambient drift.
- **Syllable Math**: 8–10 syllables per bar for Boom-Bap/Rock (leaves room for the drum pocket); 14–16 syllables for fast Trap.
- **Hyperparameter Sweet Spot**: `steps: 28-35`, `cfg_scale: 1.9`, `top_k: 40-45`.

---

## 3. Multi-Node Cluster Execution & IP Resolution

When running across nodes in the DGX Spark cluster:
1. **Verify target host**: `curl -s http://<NODE_IP>:8188/system_stats`
2. **Specify host parameter**: Pass `--host http://<NODE_IP>:8188` to `generate-music.py` or set `export COMFY_HOST="http://<NODE_IP>:8188"`.
3. **Co-Tenancy Safety**: Always run with `--disable-pinned-memory --disable-smart-memory`.
