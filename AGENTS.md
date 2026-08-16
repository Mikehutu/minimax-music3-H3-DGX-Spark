# AGENTS.md — coding / ops agents working this repo

This file is the ready-to-run execution contract for Cursor, Hermes, AGY, Claude, and human operators.

---

## 🎯 Goal & Zero-to-Working Contract

- **Model Family**: `MiniMax-Music3` (Text-to-Music / Full Songs / Rap Beats / Instrumentals).
- **Weights Source**: Hugging Face [`Comfy-Org/MiniMax-Music-3`](https://huggingface.co/Comfy-Org/MiniMax-Music-3) (or official `MiniMaxAI/MiniMax-Music3`).
- **Backend Runtime**: ComfyUI (tree `ComfyUI-music3` with `comfy-kitchen>=0.2.31`).
- **Cluster Deployment**: Standalone single-node OR co-tenant with **DeepSeek-V4-Flash (TP2)** across dual NVIDIA DGX Sparks (GB10 / SM121).
- **Output Standards**: 44.1 kHz Stereo FLAC -> auto-converted to 320k MP3 + 1080p/720p H.264 MP4 waveform video.

---

## 🚀 Cold-Start Zero-to-Working Runbook (For Any Agent)

When starting on a blank node or environment with **no models, no ComfyUI, and no server running**, follow this exact sequential procedure:

### Option A: One-Shot Automated Bootstrap
```bash
# Runs environment setup, downloads missing models, launches server, and executes smoke test
bash scripts/bootstrap.sh
```

### Option B: Step-by-Step Explicit Execution

#### Step 0: System Prerequisites & Environment Setup
```bash
# 1. Ensure ffmpeg is installed
which ffmpeg || sudo apt-get update && sudo apt-get install -y ffmpeg

# 2. Stage ComfyUI, virtualenv, and install dependencies
bash scripts/setup-env.sh
```

#### Step 1: Model Weights Download
Downloads the 3 required checkpoints from Hugging Face [`Comfy-Org/MiniMax-Music-3`](https://huggingface.co/Comfy-Org/MiniMax-Music-3):
```bash
bash scripts/download-models.sh ./models/MiniMax-Music3-Comfy
```
**Required Checkpoints & File Sizes:**
1. `diffusion_models/minimax_music3_dit_fp16.safetensors` (~4.91 GB)
2. `text_encoders/minimax_music3_text_encoder_pruned_int8_convrot.safetensors` (~9.20 GB)
3. `vae/minimax_music3_dav.safetensors` (~216 MB)

#### Step 2: Launch ComfyUI Server (Cluster-Safe)
```bash
# Launch with standard production profile (or cotenancy profile if sharing with DeepSeek)
bash scripts/start-comfyui-music3.sh profiles/production.env

# Verify server is live and responsive
bash scripts/status-comfyui-music3.sh
```

#### Step 3: Execute Smoke Test Verification (10s Clip)
```bash
bash scripts/smoke-test.sh
```

---

## ⚙️ Canonical Hyperparameters

| Stage | Node / Parameter | Canonical Value | Rationale |
| :--- | :--- | :--- | :--- |
| **TE Loader** | `CLIPLoader` | `minimax_music3_text_encoder_pruned_int8_convrot.safetensors` / `type: minimax` | Stock INT8 convrot acoustic conditioning |
| **DiT Loader** | `UNETLoader` | `minimax_music3_dit_fp16.safetensors` / `weight_dtype: default` | FP16 flow-matching diffusion backbone |
| **VAE Loader** | `VAELoader` | `minimax_music3_dav.safetensors` | Discrete Acoustic VAE (DAV) decoder |
| **AR Encoding** | `MiniMaxMusic3TextEncode` | `cfg_scale: 1.8`, `top_k: 50` | Balances prompt adherence and musicality |
| **Diffusion** | `KSampler` | `steps: 25`, `cfg: 1.0`, `sampler: euler`, `scheduler: simple` | Flow-matching continuous sampling |
| **Negative** | `ConditioningZeroOut` | Connected from positive conditioning | Standard zeroed flow negative |
| **Duration** | `max_duration` | `≤ 35.0s` (Co-Tenancy) / `Any` (Standalone) | Prevents unchunked VAE decode memory spikes |
| **Memory** | CLI flags | `--disable-pinned-memory --disable-smart-memory --disable-cuda-malloc` | Non-negotiable for GB10 co-tenancy |

---

## 🌐 Multi-Node Cluster & IP Resolution Rules (Fail-Closed)

1. **Verify Target Node IP First**:
   - When executing from an orchestrator machine or a secondary worker node, never assume `127.0.0.1`.
   - Resolve target host from CLI argument `--host` OR environment variable `COMFY_HOST` (e.g. `http://<NODE_IP>:8188`).
2. **Pre-flight Health Gate**:
   - Ping target endpoint: `curl -sf http://<TARGET_IP>:8188/system_stats`
   - If endpoint returns non-200 or connection refused, **fail closed** with actionable diagnostic error.
3. **No Redundant Server Starts**:
   - If port 8188 is already bound and responding to `/system_stats`, reuse the live instance; do not kill or restart running jobs without explicit instruction.

---

## 🎼 Production Generation Workflow

```bash
# Generate full song (FLAC + MP3 + MP4 Waveform Video)
python3 scripts/generate-music.py \
  --caption "Hard-hitting trap rap beat with aggressive 808 bass, tight hi-hats, and melodic piano" \
  --lyrics "[intro]\nLet's get it\n[verse 1]\nDigital rhythm flowing sharp through the night\n[chorus]\nUnleash the spark, reaching new heights" \
  --duration 35.0 \
  --prefix "track_production" \
  --format all
```

---

## 🛑 Definition of Done (Agent Tasks)

- [ ] Checkpoints present in `diffusion_models/`, `text_encoders/`, `vae/`
- [ ] ComfyUI server confirmed listening on `0.0.0.0:8188` with `--disable-pinned-memory`
- [ ] Model checkpoints verified via `extra_model_paths.yaml`
- [ ] Generation completes without errors (output status: `success`)
- [ ] Output audio verified: 44.1 kHz, Stereo, duration matching request
- [ ] Converted `.mp3` and `.mp4` files present and playable
- [ ] No temporary files or zombie processes left behind

---

## 🔑 Key Paths

| Path | Description |
| :--- | :--- |
| `scripts/bootstrap.sh` | One-shot zero-to-working cold-start script |
| `scripts/download-models.sh` | Hugging Face checkpoint downloader |
| `scripts/setup-env.sh` | ComfyUI tree and dependency installer |
| `scripts/start-comfyui-music3.sh` | Main server launcher |
| `scripts/generate-music.py` | Full generation pipeline with auto-conversion |
| `scripts/convert-media.py` | Standalone FLAC to MP3 / MP4 converter |
| `scripts/smoke-test.sh` | 10s smoke test validator |
| `workflows/*.json` | Raw ComfyUI API workflow graphs |
| `docs/COTENANCY_DGX_SPARK.md` | DGX Spark memory & co-tenancy reference |
| `docs/PROMPT_LYRICS_GUIDE.md` | Prompt engineering & lyrics tag handbook |
