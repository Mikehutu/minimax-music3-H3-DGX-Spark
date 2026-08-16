# MiniMax-Music3-ComfyUI-DGX-Spark

A clean, high-performance text-to-music generation pipeline for **MiniMax Music3** in ComfyUI, featuring **Dual DGX Spark (GB10 / 121 GB UMA)** co-tenancy optimization, cold-start bootstrap, universal GPU support, and automated **FLAC → MP3 (320k) / MP4** audio visualizer rendering.

---

## 🖥️ System Compatibility & Prerequisites

### Supported Hardware & Requirements
| Hardware Family | VRAM Requirement | Supported Durations | Notes |
| :--- | :---: | :---: | :--- |
| **NVIDIA DGX Spark (GB10 / 121 GB UMA)** | 121 GB Unified | Full (`10s – 300s`) | Co-tenancy optimized (`≤ 35s` alongside DeepSeek-V4-Flash TP2). |
| **NVIDIA H100 / A100 / L40S** | 40 GB / 80 GB | Full (`10s – 300s`) | Flawless standalone execution with high batch throughput. |
| **NVIDIA RTX 4090 / 3090** | 24 GB VRAM | Up to `60s – 120s` | Full FP16 DiT + INT8 text encoder fits comfortably. |
| **NVIDIA RTX 4080 / 3080 / 4070** | 12 GB – 16 GB VRAM | `10s – 35s` | ComfyUI dynamic offloading automatically swaps weights. |

### System Prerequisites
- **OS**: Linux (Ubuntu 20.04+, Debian, Fedora, Arch, WSL2)
- **CUDA**: CUDA 12.1+ / 13.0+
- **Python**: Python 3.10, 3.11, or 3.12
- **System Tools**: `ffmpeg`, `curl`, `git`
  ```bash
  sudo apt-get update && sudo apt-get install -y ffmpeg curl git
  ```

---

## ⚡ Hardware, Memory & Thermal Profiles Across Durations

Measured on **NVIDIA DGX Spark (GB10 / 121 GiB Unified Memory)**:

| Audio Length | Generation Time | Peak VRAM | Thermal & Operating Profile | Operational Guidelines |
| :---: | :---: | :---: | :--- | :--- |
| **10s – 25s** | ~60s – 90s | **~4.4 GB** | **48°C – 54°C** · Co-Tenant Safe | Leaves **7.9 GiB free headroom** alongside DeepSeek-V4-Flash (TP2 holding 95.6 GB). |
| **30s – 35s** | ~80s – 120s | **~4.5 GB** | **52°C – 57°C** · Co-Tenant Safe | Recommended safe duration ceiling when co-tenanted with large LLMs. |
| **45.0s** | ~136s | **~14.4 GB** | **57°C – 61°C** · Standalone / Cooled | Higher latent frame count (1.98M samples). Stable with active cooling. |
| **60.0s** | ~192s | **~9.7 GB – 15 GB** | **60°C – 65°C** · Standalone Mode | Full 2.65M sample sequence. Sustained 3+ min compute load. Requires standalone mode to prevent thermal throttling / memory contention. |
| **Idle (Post-Run)** | — | **~339 MiB** | **44°C – 47°C** · Idle | Dynamic memory management frees all intermediate model weights and caches. |

> [!NOTE]
> **Thermals & Hardware Co-Tenancy**: Longer sequences (45s–60s) sustain 95%+ GPU compute load over 2–3.5 minutes. Ensure proper airflow / external cooling to maintain maximum boost clocks and avoid thermal throttling under heavy workloads.

---

## 🎯 Prompting & Lyrics Engineering Guide

MiniMax Music3 uses two separate token channels: `<|caption_start|>...<|caption_end|>` and `<|lyrics_start|>...<|lyrics_end|>`.

### Rule 1: Place ALL Style, Drums, Tempo & Vocal Tone in `--caption`
The vocalist will **never** sing words from the caption:
```text
--caption "High-energy 172 BPM Synthwave Electro Rock song, screaming 80s lead synthesizer, punchy acoustic rock kick drum, crisp cracking snare on the 2 and 4, driving synth bassline, powerful emotive male vocal, studio master"
```

### Rule 2: Place ONLY Sung Lyrics & Clean Section Tags in `--lyrics`
Everything written in the lyrics block is pronounced phonetically. Do not add descriptive adjectives inside tags:
- ✅ Use clean tags: `[intro]`, `[verse 1]`, `[pre-chorus]`, `[chorus]`, `[drop]`, `[bridge]`, `[outro]`, `[instrumental]`
- ❌ Avoid: `[verse 1 - fast boom bap drums]` *(The model will sing "fast boom bap drums")*

### Rule 3: Creating 100% Instrumental Tracks (Zero Vocals)
Use `[instrumental]` for pure instrumental solos, drops, and video game music:
```text
--lyrics "[intro]\n[instrumental]\n\n[verse 1]\n[instrumental]\n\n[drop]\n[instrumental]\n\n[outro]\n[instrumental]"
```

---

## ⚙️ Recommended Hyperparameter Configurations

| Style / Use Case | `duration` | `steps` | `cfg_scale` | `top_k` | Description |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Vocal Songs & Rap** | `25.0s – 35.0s` | `28` | `1.9` | `42 – 45` | Tight melodic cadence, clear vocal diction, punchy rhythm |
| **Chiptune & 8-Bit** | `30.0s – 45.0s` | `32` | `1.9` | `42` | Sharp pulse-wave leads, crisp bitcrushed percussion |
| **Neurofunk & Dubstep** | `30.0s – 60.0s` | `32` | `1.9` | `42` | Maximum bass distortion dynamics and complex transient textures |
| **Co-Tenancy Default** | `≤ 35.0s` | `25` | `1.8` | `50` | Balanced musicality with lowest VRAM footprint (~4.4 GB) |

---

## 🚀 Quick Start & CLI Usage

### 1. One-Shot Automated Setup
```bash
# 1. Clone repository
git clone https://github.com/Mikehutu/MiniMax-Music3-ComfyUI-DGX-Spark.git
cd MiniMax-Music3-ComfyUI-DGX-Spark

# 2. Run one-shot bootstrap (Installs ComfyUI, downloads weights, launches server, runs smoke test)
bash scripts/bootstrap.sh
```

### 2. Generate Music (Auto FLAC + MP3 + MP4)
```bash
python3 scripts/generate-music.py \
  --caption "Classic 90s boom-bap hip-hop, loud punchy acoustic kick drum, crisp cracking snare on the 2 and 4, swinging dusty hats, jazz bass" \
  --lyrics "[intro]\nCheck the mic.\n\n[verse 1]\nWalking down the boulevard under streetlights\nChasing the vision through the long nights\n\n[chorus]\nKeep the groove alive." \
  --duration 30.0 \
  --steps 28 \
  --cfg-scale 1.9 \
  --top-k 42 \
  --prefix "my_track" \
  --format all
```

### 3. Output Deliverables
Files are automatically created in `output/`:
- `my_track_00001.flac`: Lossless 44.1 kHz Stereo audio
- `my_track_00001.mp3`: 320 kbps High-Bitrate MP3
- `my_track_00001.mp4`: 1080p/720p H.264 Neon Audio Waveform Video

---

## 🔧 Troubleshooting & Debugging

| Issue / Error | Likely Cause | Solution |
| :--- | :--- | :--- |
| **Server Connection Refused** (`http://127.0.0.1:8188`) | ComfyUI daemon is not running | Start the server with `bash scripts/start-comfyui-music3.sh` and verify with `curl http://127.0.0.1:8188/system_stats`. |
| **Out of Memory (OOM) on Unified Memory** | Track duration > 35s during live co-tenancy | Keep `--duration ≤ 35.0s` when co-tenanted with DeepSeek-V4-Flash. For 60s+ tracks, run in standalone mode. |
| **Missing `ffmpeg` Error** | `ffmpeg` is not installed on PATH | Run `sudo apt-get install -y ffmpeg` (required for MP3/MP4 conversion). |
| **Slow AR Sampling** | CPU offload or thermal throttling | Check GPU thermals (`nvidia-smi`) and ensure active cooling. Confirm GPU compute utilization is 90%+. |
| **Missing Model Checkpoints** | Incomplete Hugging Face download | Run `bash scripts/download-models.sh` to verify and download missing safetensors. |

---

## 📜 License

Licensed under the [MIT License](LICENSE).
