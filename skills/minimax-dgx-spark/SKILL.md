---
name: minimax-dgx-spark
description: >
  Drive MiniMax Music3 (text-to-music) and MiniMax H3 (text/image-to-video)
  through a local/remote ComfyUI on DGX-Spark hardware. Use when generating
  music, songs, beats, instrumentals, or AI video from prompt/lyrics; or when
  converting them to MP3/MP4. Portable + ENV-driven, no personal config.
---

# MiniMax DGX-Spark (Music3 + H3) via ComfyUI

Generate AI music (Music3) and AI video (H3) by submitting ComfyUI API
workflows, then post-process outputs (MP3 / MP4). All paths/hosts are ENV-driven;
nothing personal is hardcoded. This skill drives the sibling scripts in the
`MiniMax-DGX-Spark` package (or standalone files on the node).

## Prereqs

- A reachable ComfyUI instance.
  - Local: `curl -s http://127.0.0.1:8188/system_stats`
  - Remote node (e.g. a DGX Spark): `curl -s http://<NODE_IP>:8188/system_stats`
- `ffmpeg`, `python3`, and (for H3) no extra GPU beyond ComfyUI's.

Set the target once per session:
```bash
export COMFY_HOST="http://<NODE_IP>:8188"   # or leave unset for localhost:8188
export COMFY_OUTPUT_DIR="..."              # where ComfyUI writes outputs (node-local fs)
```

## Speak in IPs, never hostnames
If remoting to a node, use its IP in `COMFY_HOST`. Hostnames in SSH config are
connection aliases only. `127.0.0.1` works from inside the node.

## Music3 (text-to-music)

### Generate a track (MP3 default)
```bash
python3 music3/generate.py \
  --caption "Hard-hitting trap rap beat, aggressive 808 bass, tight hi-hats, melodic piano" \
  --lyrics "[intro]\nLet's go\n[verse 1]\nDigital rhythm sharp through the night\n[chorus]\nUnleash the spark, reaching new heights" \
  --duration 35.0 --prefix my_track --format mp3
```
- `--format mp3` is the default. Add `--format all` for an MP4 waveform video.
- Keep `--duration ≤ 35.0s` when co-tenant with a large LLM.
- For max fidelity, switch `unet_name` to `minimax_music3_dit_fp16.safetensors` (default is int8).

### Bypass the app (direct API, no app dependency)
If you only have the running ComfyUI and the checkpoint files, submit the raw
API graph directly (see `music3/workflows/*.json` for the exact node wiring).
The canonical pipeline:
`CLIPLoader` (int8 TE) → `UNETLoader` (int8 DiT) → `VAELoader` (dav) →
`MiniMaxMusic3TextEncode` (caption/lyrics/duration/cfg/topk) →
`EmptyMiniMaxMusic3LatentAudio` → `ConditioningZeroOut` →
`KSampler` (euler/simple, cfg 1.0) → `VAEDecodeAudio` → `SaveAudio`.

## H3 (text/image-to-video)

### Generate a short clip
```bash
python3 h3/generate-video.py --prompt "a calm ocean wave at dusk, photorealistic" \
  --duration 5 --prefix my_clip --host "$COMFY_HOST"
```
- `--duration` is rounded UP to H3's `17n+5` frame grid.
- Add `--reference <img-in-comfy-input>` (repeatable) for identity/stability across shots.
- Timings: a 5s 720p clip is ~7–8 min under heavy co-tenant load on GB10; much faster standalone.

## Convert / Watchdog

- Convert a FLAC: `python3 scripts/convert-media.py out.flac --mp3` (or `--mp4`).
- Long generations that could outlive an SSH session: submit, then run detached:
```bash
nohup python3 scripts/convert-watchdog.py --prompt-id <ID> --host "$COMFY_HOST" --format mp3 > /tmp/watchdog.log 2>&1 &
```
The watchdog polls `/history/<ID>` and converts when done, surviving disconnects.

> ⚠️ **If you get a FLAC but no MP3/MP4, the generation SUCCEEDED — the
> post-processing step did not.** Post-processing runs client-side, so a
> disconnected/timed-out session yields the ComfyUI output (FLAC) but the
> conversion never ran. Do NOT resubmit. Run the watchdog or convert manually:
> `python3 scripts/convert-watchdog.py --prompt-id <ID> --format mp3`. The
> prompt ID is printed on success (or fetch it from `$COMFY_HOST/queue`).

## Pitfalls

1. **Get the prompt ID** — `generate*.py` prints it on success. If the client
died before doing so, fetch `curl -s "$COMFY_HOST/queue"`.
2. **Do not start a second ComfyUI** — check `scripts/status-comfyui.sh` / `curl .../queue` first; reuse a live instance.
3. **Audio ownership** — a `<video>` is muted; sound ships as separate `<audio>` (for HyperFrames muxing).
4. **GP10 UMA**: `nvidia-smi` CSV returns `[N/A]` for memory; read `/proc/driver/nvidia/gpus/0/memory` or `system_stats` `vram_*`.
5. **Never interrupt a running ComfyUI job** — wait for the queue to drain; kills orphan the job server-side.
