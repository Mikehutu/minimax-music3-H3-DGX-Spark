# AGENTS.md — coding/ops agents working this repo

Ready-to-run execution contract for Cursor, Hermes, AGY, Claude, and human operators. This package runs **MiniMax Music3** (text-to-music) and **MiniMax H3** (text/image-to-video) through **ComfyUI**, primarily on **NVIDIA DGX Spark (GB10 / 121 GB unified memory)**.

The package is portable and ENV-driven. A dual-Spark co-tenant split (DeepSeek TP2 across both nodes; ComfyUI Music3+H3 on one node) is a documented profile, not a requirement.

---

## Fresh-install prerequisites (read first — do NOT skip)

- **Newest ComfyUI required — the MiniMax nodes live in ComfyUI core**, not a
  separately-installed custom node: `comfy_extras/nodes_minimax_music.py` and
  `nodes_minimax_h3.py`. An outdated ComfyUI gives "node type not found".
  `setup-env.sh` clones upstream; use the latest release, never an old tag.
- **Disk**: music3 ≈ 11.5 GB (int8 DiT 2.5 + TE 8.6 + VAE 0.2) + ~3 GB ComfyUI/venv → plan ≥ 25 GB. h3 ≈ 41 GB (or ~80 GB with bf16/ref2va variants).
- **GPU**: NVIDIA required (32 GB+ for full durations). Unified-memory DGX
  Spark is primary target. CPU-only is impractically slow.
- **System**: Linux, CUDA 12.1+/13.0+, Python 3.10–3.12, ffmpeg, git.

## Verification (never claim success without evidence)

- After `setup-env.sh`: `ls` the family model dirs.
- `scripts/status-comfyui.sh` must show `MiniMaxMusic3TextEncode` (music3) or
  `MiniMaxH3ReferenceToVideo` (h3) under AVAILABLE — proves the core nodes.
- Run the family smoke test; confirm the output exists and plays via
  `ffprobe`/`ffmpeg`. Report real tool output, not "it should work."

## Goal & Zero-to-Working Contract

- **Families**: `music3` (text-to-music) and `h3` (text/image-to-video).
- **Weights**: public Hugging Face — `Comfy-Org/MiniMax-Music-3` (music3) and the MiniMax H3 hub repo (h3).
- **Backend**: ComfyUI (`main.py`, tree `${COMFY_DIR}`) with `comfy-kitchen>=0.2.31`.
- **Model choices (music3)**: int8 DiT is the default; fp16 opt-in for max fidelity.
- **Output**: 44.1 kHz FLAC (music3) -> MP3; H3 -> MP4 video (muxed audio).

## Zero-to-Working (for any agent)

Choose family `F=<music3|h3>`.

### Option A: One-shot
```bash
bash scripts/bootstrap.sh $F
```

### Option B: Step-by-step
```bash
# environment + deps
bash scripts/setup-env.sh

# checkpoints for the family
bash scripts/download-models.sh $F

# launch ComfyUI
bash scripts/start-comfyui.sh

# verify
bash scripts/status-comfyui.sh

# smoke test (family-specific)
bash music3/smoke-test.sh                 # music3
python3 h3/generate-video.py --prompt "a cat, photorealistic" --duration 5 --prefix smoke  # h3
```

## Node Profiles

Source `profiles/nodes.env` to define topology (single or dual node).
Defaults assume single node. ENV knobs: `COMFY_HOST`, `COMFY_DIR`,
`COMFY_OUTPUT_DIR`, `PYTHON_BIN`, `MODEL_ROOT`, `PORT`, `HOST`, `EXTRA_FLAGS`.

For dual-Spark / co-tenancy (DeepSeek-V4-Flash TP2 across both nodes; ComfyUI
Music3+H3 on one node in remaining headroom), see `docs/COTENANCY_DGX_SPARK.md`
and do NOT set the LLM node's hostname — use its port/IP via ENV.

## Canonical Hyperparameters

| Stage | Node | Value |
| :--- | :--- | :--- |
| TE Loader | `CLIPLoader` | `minimax_music3_text_encoder_pruned_int8_convrot.safetensors` / `type: minimax` |
| DiT Loader | `UNETLoader` | `minimax_music3_dit_int8_convrot.safetensors` / `weight_dtype: default` (fp16 opt-in) |
| VAE Loader | `VAELoader` | `minimax_music3_dav.safetensors` |
| AR Encoding | `MiniMaxMusic3TextEncode` | `cfg_scale: 1.8`, `top_k: 50` |
| Diffusion | `KSampler` | `steps: 25`, `cfg: 1.0`, `sampler: euler`, `scheduler: simple` |
| Duration | `max_duration` | `≤ 35.0s` co-tenancy / any standalone |
| Memory flags | CLI | `--disable-pinned-memory --disable-smart-memory --disable-cuda-malloc` |

Music3 recommended hyperparameters by style:

| Style | duration | steps | cfg | top_k |
| :--- | :--- | :--- | :--- | :--- |
| Vocal / rap | 25–35s | 28 | 1.9 | 42–45 |
| Chiptune | 30–45s | 32 | 1.9 | 42 |
| Neurofunk / dubstep | 30–60s | 32 | 1.9 | 42 |
| Co-tenancy default | ≤35s | 25 | 1.8 | 50 |

H3 defaults: `MiniMaxH3ReferenceToVideo`, `BasicScheduler` steps 20,
`res_multistep` sampler, 1280×720 by default, `17n+5` frame grid.

## Definition of Done (agent tasks)

- [ ] Checkpoints present for the family (`diffusion_models/`, `text_encoders/`, `vae/`)
- [ ] ComfyUI server confirmed listening on `${COMPY_HOST}`
- [ ] Model checkpoints verified via `extra_model_paths.yaml`
- [ ] Generation completes without errors (output status: `success`)
- [ ] Music3 output verified: 44.1 kHz, stereo, correct duration; `.mp3` present (`.mp4` only when requested)
- [ ] H3 output verified: video + audio muxed, correct length/resolution
- [ ] No temp files or zombie processes left

## Scripts map

| Path | Purpose |
| :--- | :--- |
| `scripts/setup-env.sh` | env bootstrap (ComfyUI + deps + extra_model_paths) |
| `scripts/download-models.sh` | family checkpoint downloader |
| `scripts/start-comfyui.sh` | server launcher |
| `scripts/status-comfyui.sh` | server status / node check |
| `scripts/convert-media.py` | FLAC -> MP3 / MP4 conversion |
| `scripts/convert-watchdog.py` | disconnect-safe auto-convert |

> ⚠️ **Co-tenant generations can outlast an SSH/client session.** A disconnected
> client won't run the post-processing step — you'll get the FLAC but no MP3.
> When that happens, either run the watchdog (`scripts/convert-watchdog.py`
> `--prompt-id <ID> --format mp3`) or convert manually. Do not submit a second
> job assuming the first was lost.

| `music3/generate.py` | music3 text-to-music CLI |
| `music3/bench_styles.py` | multi-genre benchmark |
| `h3/generate-video.py` | h3 text/image-to-video CLI |
| `profiles/nodes.env` | node topology profile |
