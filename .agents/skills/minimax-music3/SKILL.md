---
name: minimax-music3
description: >-
  Generate high-quality music, songs, rap beats, instrumentals, and audio using MiniMax Music3 on ComfyUI,
  and convert output FLAC files into MP3 or MP4 videos with animated waveforms. Use when generating music,
  creating audio tracks or beats from text/lyrics, managing ComfyUI Music3 workflows, or converting music formats.
---

# MiniMax Music3 in ComfyUI

Generate AI music, full songs with lyrics, rap beats, and background music using the MiniMax Music3 diffusion stack on ComfyUI, with automatic post-processing to MP3 and MP4 formats.

---

## 🌐 Multi-Node Cluster Execution & IP Resolution

> [!IMPORTANT]
> **Check the Target Node IP Before Running across the Cluster:**
> If you are running commands or submitting generation requests from another node in your cluster (e.g. from an orchestrator machine, a worker node, or across Spark nodes), you **must verify and specify the target node's IP address** running ComfyUI before execution.

### Step 1: Identify and verify the target ComfyUI node IP
Check reachability using `curl`:
```bash
# Example: Check if ComfyUI is running on head node or worker node
curl -s http://<NODE_IP>:8188/system_stats
# e.g., curl -s http://<NODE_IP>:8188/system_stats
```

### Step 2: Pass `--host` or export `COMFY_HOST`
When invoking `generate_music.py` remotely, provide the target host:
```bash
# Via CLI argument
${PYTHON_BIN:-$HOME/ComfyUI/comfyui-env/bin/python} ./scripts/generate_music.py \
  --host http://<NODE_IP>:8188 \
  --caption "Energetic electronic synthwave" \
  --lyrics "[instrumental]"

# Or via environment variable
export COMFY_HOST="http://<NODE_IP>:8188"
```

---

## Quick Start (Automated Generation)

Use the built-in helper script to generate music and convert outputs in one step:

```bash
# 1. Ensure ComfyUI server is running (locally or on target node)
bash ./scripts/start_server.sh

# 2. Generate music (FLAC + MP3 + MP4 video with neon waveform visualizer)
${PYTHON_BIN:-$HOME/ComfyUI/comfyui-env/bin/python} ./scripts/generate_music.py \
  --caption "Hard-hitting modern trap rap beat, aggressive 808 bass, crisp snare, melodic piano" \
  --lyrics "[intro]\nYeah let's go\n[verse 1]\nSpitting fire on the microphone\n[chorus]\nNever stopping till we reach the top" \
  --duration 30.0 \
  --prefix "my_track" \
  --format all
```

---

## Environment & Model Layout

- **ComfyUI Tree**: [`${COMFY_DIR:-$HOME/ComfyUI-music3}/`](file://${COMFY_DIR:-$HOME/ComfyUI-music3}/)
- **Python Virtualenv**: `${PYTHON_BIN:-$HOME/ComfyUI/comfyui-env/bin/python}`
- **Model Checkpoints**: Located in [`${HOME}/ComfyUI-music3/models/MiniMax-Music3-Comfy/`](file://${HOME}/ComfyUI-music3/models/MiniMax-Music3-Comfy/)
  - `diffusion_models/minimax_music3_dit_fp16.safetensors` (~4.7 GB)
  - `text_encoders/minimax_music3_text_encoder_pruned_int8_convrot.safetensors` (~8.7 GB)
  - `vae/minimax_music3_dav.safetensors` (~206 MB)
- **Output Directory**: [`${COMFY_DIR:-$HOME/ComfyUI-music3}/output/`](file://${COMFY_DIR:-$HOME/ComfyUI-music3}/output/)
- **ComfyUI API Endpoint**: `http://127.0.0.1:8188` (or `http://<NODE_IP>:8188`)

---

## Server Management

To start the ComfyUI server in the background:
```bash
bash ./scripts/start_server.sh
```

Or manually:
```bash
${PYTHON_BIN:-$HOME/ComfyUI/comfyui-env/bin/python} ${COMFY_DIR:-$HOME/ComfyUI-music3}/main.py \
  --listen 0.0.0.0 --port 8188 --disable-pinned-memory
```

---

## Core ComfyUI Pipeline Graph

To construct or queue a custom workflow via the ComfyUI API `/prompt` endpoint:

1. **`CLIPLoader`**:
   - `clip_name`: `"minimax_music3_text_encoder_pruned_int8_convrot.safetensors"`
   - `type`: `"minimax"`
2. **`UNETLoader`**:
   - `unet_name`: `"minimax_music3_dit_fp16.safetensors"`
   - `weight_dtype`: `"default"`
3. **`VAELoader`**:
   - `vae_name`: `"minimax_music3_dav.safetensors"`
4. **`MiniMaxMusic3TextEncode`**:
   - `clip`: `["1", 0]`
   - `caption`: Description of style, instruments, vocal timbre, mood
   - `lyrics`: Structured lyrics with `[intro]`, `[verse]`, `[chorus]`, `[outro]`, or `[instrumental]`
   - `max_duration`: Length in seconds (e.g. `30.0`)
   - `cfg_scale`: `1.5` to `1.8`
   - `top_k`: `50`
5. **`EmptyMiniMaxMusic3LatentAudio`**:
   - `seconds`: `["4", 1]` (connects duration from TextEncode output 1)
   - `batch_size`: `1`
6. **`ConditioningZeroOut`**:
   - `conditioning`: `["4", 0]`
7. **`KSampler`**:
   - `model`: `["2", 0]`, `positive`: `["4", 0]`, `negative`: `["6", 0]`, `latent_image`: `["5", 0]`
   - `steps`: `20`–`25`, `cfg`: `1.0`, `sampler_name`: `"euler"`, `scheduler`: `"simple"`, `denoise`: `1.0`
8. **`VAEDecodeAudio`**:
   - `samples`: `["7", 0]`, `vae`: `["3", 0]`
9. **`SaveAudio`**:
   - `audio`: `["8", 0]`, `filename_prefix`: `"my_song"`

---

## Format Conversion (FLAC to MP3 / MP4)

Run the conversion helper script:
```bash
${PYTHON_BIN:-$HOME/ComfyUI/comfyui-env/bin/python} ./scripts/convert_media.py \
  ${COMFY_DIR:-$HOME/ComfyUI-music3}/output/my_song_00001.flac --all
```

Or execute direct `ffmpeg` commands:

### Convert to MP3 (High Quality 320 kbps)
```bash
ffmpeg -i input.flac -codec:a libmp3lame -b:a 320k output.mp3
```

### Convert to MP4 with Animated Neon Waveform Visualizer
```bash
ffmpeg -i input.flac -filter_complex \
"[0:a]showwaves=s=1280x720:mode=cline:colors=0x00FFCC|0xFF007F:scale=sqrt[v]" \
-map "[v]" -map 0:a -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest output.mp4
```

### Convert to MP4 with Static Cover Image
```bash
ffmpeg -loop 1 -i cover.jpg -i input.flac -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -shortest output.mp4
```

---

## References

- See [`references/workflow_guide.md`](./references/workflow_guide.md) for full hyperparameter specifications, prompt engineering guidelines, lyrics syntax tags, and DGX Spark cluster co-tenancy details.
