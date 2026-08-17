# MiniMax DGX-Spark — Music3 + H3 ComfyUI toolkit

A clean, portable toolkit for running **MiniMax Music3** (text-to-music) and
**MiniMax H3** (text/image-to-video) through ComfyUI, optimized for and
documented against **NVIDIA DGX Spark (GB10 / 121 GB unified memory)**.

A dual-DGX-Spark co-tenant topology is supported as a documented profile, not a
requirement: **DeepSeek-V4-Flash runs tensor-parallel across both nodes (TP2)**,
while **ComfyUI (Music3 + H3) runs on one node** in the remaining unified-memory
headroom.

---

## Updates

### 2026-08-17 — H3 Turbo LoRA (optional, LoRA-only)

Added optional `--lora` support to `h3/generate-video.py`. **LoRA only** — it
loads `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors` (lightx2v
`Minimax-h3-Turbo`, distilled 20→4 NFE) via a `LoraLoaderModelOnly` node and
auto-drops `steps` to 4. Download via `scripts/download-models.sh h3` (drops the
~1.9 GB file into `loras/`), then run with `--lora <filename>`.

**Quality (validated on gx10-b, 2026-08-17):** the turbo LoRA is what makes 4-step
reference-to-video (ref2v) viable. A controlled A/B at identical 1344x768, same
ref, same prompt, same 4 steps, differing only in LoRA, showed the 4-step baseline
(no LoRA) is poor while the 4-step turbo LoRA is usable. **For fast reference UGC,
use `--lora` (do not run bare `--steps 4`).** An earlier low-res Extender test that
suggested turbo degraded quality was confounded; this was corrected.

Both outputs validated: identical proper-res clips, same refs/prompt, only LoRA
differing. Exact timings are environment-dependent (co-tenant memory contention +
model cold-start dominate wall-clock); the LoRA is a quality enabler at 4 steps,
not primarily a speed knob.

---

## Package Layout

```
mini-max-dgx-spark/
├── README.md
├── AGENTS.md                 # zero-to-working contract for coding/ops agents
├── LICENSE
├── profiles/nodes.env        # node-topology profile (single / dual node)
├── scripts/                  # SHARED core (portable, ENV-driven)
│   ├── setup-env.sh          # boots ComfyUI + venv + deps
│   ├── download-models.sh    # [music3|h3] checkpoint downloader
│   ├── start-comfyui.sh      # server launcher (no family hardcode)
│   ├── status-comfyui.sh     # cluster status
│   ├── stop-comfyui.sh       # server stop
│   ├── convert-media.py      # FLAC -> MP3 / MP4 conversion toolkit
│   └── convert-watchdog.py   # disconnect-safe auto-conversion
├── music3/                   # Music3 entry layer
│   ├── generate.py           # text-to-music CLI (MP3 default, int8 DiT)
│   ├── bench_styles.py       # multi-genre benchmark
│   ├── smoke-test.sh
│   └── workflows/*.json
├── h3/                       # H3 entry layer
│   ├── generate-video.py     # text/image-to-video CLI
│   └── workflows/            # (optional API workflow graphs)
├── skills/minimax-dgx-spark/ # Hermes agent skill (auto-loaded)
└── docs/
    ├── CONVERSION_RUNBOOK.md
    ├── COTENANCY_DGX_SPARK.md
    └── PROMPT_LYRICS_GUIDE.md
```

---

## Hardware & Prerequisites

> The VRAM table below is **Music3 audio generation only** — it describes peak
> VRAM during text-to-music, not H3 video. H3 uses a different model stack
> (a ~20 GB int8 UNet + ~15 GB text encoder + VAE) and is far more
> compute/duration-bound, so do not extrapolate these figures to H3 clips.

| Hardware | VRAM / Mem | Supported |
| :--- | :--- | :--- |
| NVIDIA DGX Spark GB10 | 128 GB unified | ✅ primary target (fully tested) |
| NVIDIA RTX PRO 6000 (Blackwell) | 96 GB | ✅ full durations |
| NVIDIA RTX 6000 / RTX A6000 Ada | 48 GB | ✅ full durations |
| H100 / A100 / L40S | 40–80 GB | ✅ full durations |
| NVIDIA RTX 5090 (Blackwell) | 32 GB | ✅ full durations |
| RTX 4090 / 3090 | 24 GB | ✅ (≤60–120s) |
| RTX 4080/3080/4070 | 12–16 GB | ⚠️ (≤35s) |

> Capacities for non-DGX cards are **conservative estimates based on VRAM**, not
> benchmarked timings — only the DGX Spark GB10 has been measured end-to-end in
> this repo. The int8 + fp16 DiT and int8 text-encoder are VRAM-light enough
> that 32 GB+ cards should handle full-duration (≤35s co-tenant) comfortably.
> A ~10–60s clip needs roughly 4–15 GB peak under normal load, so 32 GB+ is
> ample; quality is identical across hardware (it's compute, not VRAM-bound,
> on non-unified cards).

- OS: Linux (Ubuntu 20.04+, Debian, Fedora, Arch, WSL2)
- CUDA 12.1+ / 13.0+, Python 3.10–3.12, `ffmpeg`, `git`
- **Newest ComfyUI release required** — the MiniMax Music3/H3 nodes are part of
  ComfyUI core (`comfy_extras/`), not a separately-installed custom node. Do not
  pin an old ComfyUI tag.

---

## Quick Start (music3)

```bash
# 1. Environment (boots ComfyUI + deps)
bash scripts/setup-env.sh

# 2. Download music3 checkpoints (int8 DiT ~2.5 GB + int8 TE + VAE)
bash scripts/download-models.sh music3

# 3. Start ComfyUI
bash scripts/start-comfyui.sh

# 4. Generate a track (MP3 by default; add --format all for MP4)
python3 music3/generate.py --caption "90s boom-bap hip-hop, punchy kick, dusty hats" \
  --lyrics "[intro]\n[verse 1]\nWalking down the boulevard\n[chorus]\nKeep the groove alive" \
  --duration 30.0 --prefix my_track --format mp3
```

> ⚠️ **Disconnects don't cancel a queued job.** Co-tenant generation can outlast
> your SSH/session; if the client dies before it produces the MP3, ComfyUI
> still finishes and writes the **FLAC**. If you end up with FLAC and no MP3,
> run `python3 scripts/convert-watchdog.py --prompt-id <ID> --format mp3`
> (survives disconnects) or convert manually. A plain `generate.py` client that
> times out will **not** have converted — post-processing runs client-side.

## Quick Start (h3)

```bash
bash scripts/setup-env.sh
bash scripts/download-models.sh h3         # ~all H3 checkpoints (bf16 + int8 variants)
bash scripts/start-comfyui.sh

# 5s video (no reference needed; refs optional for identity control)
python3 h3/generate-video.py --prompt "a calm ocean wave at dusk, photorealistic" --duration 5 --prefix my_clip
```

### H3 usage & options

`h3/generate-video.py` submits an H3 ReferenceToVideo graph to the running
ComfyUI. It is ENV-driven (respects `COMFY_HOST`, `COMFY_OUTPUT_DIR`, and
`H3_UNET / H3_CLIP / H3_VAE / H3_AUDIO_VAE` overrides).

```
python3 h3/generate-video.py \
  --prompt "<integrated_multimodal_description>..." \
  --duration 5 \                    # seconds; rounded UP to H3's 17n+5 grid
  --width 1280 --height 720 \       # default 1280x720
  --seed 42 --steps 20 \            # steps default 20
  --lora minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors \  # optional turbo
  --prefix my_clip \                # output filename prefix
  --reference img.png               # repeatable; filenames as exposed in the
                                    # ComfyUI input dir (== a local path in input/)
```

- **No reference needed**: with no `--reference`, a minimal blank frame is used
  so the graph validates — good for quick style tests.
- **Use references for control**: H3 preserves *identity & continuity* best when
  you supply character/product/scene references and describe them in the prompt.
  Reference pictures ARE the anchor; subjects not referenced are where H3 can
  drift between shots. `ref_image_size` defaults to `max`.
- **Frame grid**: H3 generates on a `17n+5` frame grid at 24 FPS.
  `--duration` is rounded **up** to the next valid count (e.g. 5s → 124 frames
  = 17·7+5 ≈ 5.17s). A typical short clip is 120–366 frames.
- **Prompt format**: use the `integrated_multimodal_description:` prefix and a
  structured block — an 8K/photoreal style line, setting, per-shot `[Shot N]`
  blocks with `[timestamp]` hard cuts and `<d>[Lang] ...</d>` dialogue, then
  `overall_soundscape:` (SFX) and `non_diegetic_music:` (score). See
  `docs/PROMPT_LYRICS_GUIDE.md` for the tokenizer / caption-vs-lyrics split on
  Music3 and the analogous structured-prompt guidance for H3 in the H3 example
  scripts.
- **Timing**: a 5s / 720p clip is ~7–8 min end-to-end under heavy co-tenant
  load on a DGX Spark GB10 (AR encoder + 20 diffusion steps dominate); much
  faster standalone. Novel-content video is compute-bound; don't mistake
  progress stalls for hangs on shared (co-tenant) nodes.
- **Turbo LoRA (REF2V = reference-to-video, REQUIRED for low-step quality)**: pass `--lora` to load
  the lightx2v `Minimax-h3-Turbo` ref2v distilled LoRA (20->4 NFE) via a
  `LoraLoaderModelOnly` node and drop to 4 steps. Corrections applied 2026-08-17:

  **The 4-step baseline is VERY BAD; the 4-step turbo LoRA is usable.** Controlled
  A/B at identical 1344x768 + same ref + same prompt + same 4 steps (only LoRA
  differed): the no-LoRA 4-step render was poor quality, the LoRA 4-step was OK.
  The LoRA is what makes 4-step ref2v viable (regular model needs ~20 steps); use
  `--lora` for fast reference UGC, not bare `--steps 4`. (An earlier low-res,
  different-node test that suggested turbo degraded quality was confounded and
  has been corrected.)

  `--lora` downloads via `scripts/download-models.sh h3` (~1.9 GB into loras/).
  See https://github.com/ModelTC/Minimax-H3-Turbo — Ref2VA 4-step (this is the
  model's Ref2VA turbo, trained 544p, recommended 4 NFE, SAMPLER euler /
  scheduler simple / 1344x768). 8-step variant exists but is FL2VA (text/
  first-last-frame), NOT ref2v — irrelevant to reference-driven video.

### H3 model variants

| Model | Size | Used? |
| :--- | :--- | :--- |
| `minimax_h3_fl2va_pruned_int8_convrot` | ~20 GB | ✅ default (int8) |
| `minimax_h3_fl2va_pruned_bf16` | ~38 GB | ⚠️ opt-in (max fidelity) |
| `qwen3vl_32b_minimax_h3_nvfp4_awq` (text encoder) | ~15 GB | ✅ (NVFP4-AWQ) |
| `minimax_h3_video_vae_fp16` | ~4.9 GB | ✅ |
| `minimax_h3_audio_vae_fp32` | ~0.6 GB | ✅ |
| `minimax_h3_ref2va_pruned_*` (reference VAE) | ~38 GB | only for reference-driven workflows |


### One-shot bootstrap (either family)

```bash
bash scripts/bootstrap.sh music3   # or: bash scripts/bootstrap.sh h3
```

---

## Node Profiles (`profiles/nodes.env`)

The package is **node-aware, not node-fixed**. Source a profile to define the
machine layout; defaults assume a single node.

```bash
# Single node (default): everything local
source profiles/nodes.env

# Dual-node co-tenancy example (documented; not required): DeepSeek-V4-Flash
# runs TP2 across both nodes; ComfyUI (Music3 + H3) on one node in the
# remaining 121 GB unified-memory headroom.
export LLM_NODE_IP=10.0.0.5          # example
source profiles/nodes.env
```

Key ENV knobs (all with sane defaults):
`COMFY_HOST`, `COMFY_DIR`, `COMFY_OUTPUT_DIR`, `PYTHON_BIN`, `MODEL_ROOT`,
`PORT`, `HOST`, `EXTRA_FLAGS`. No personal paths are baked in — everything
falls back to `${HOME}` / `./ComfyUI` / `./models`.

---

## Model choices (Music3)

| File | Size | Used? |
| :--- | :--- | :--- |
| `minimax_music3_dit_int8_convrot.safetensors` | ~2.5 GB | ✅ default |
| `minimax_music3_dit_fp16.safetensors` | ~4.9 GB | opt-in (max fidelity) |
| `minimax_music3_text_encoder_pruned_int8_convrot.safetensors` | ~8.6 GB | ✅ |
| `minimax_music3_dav.safetensors` | ~207 MB | ✅ |

> Int8 DiT is the default (half the memory, same wall-clock, ~same quality in
> testing). To use max-fidelity fp16: set the `unet_name` back to
> `minimax_music3_dit_fp16.safetensors` in `music3/generate.py`.

---

## Troubleshooting

| Issue | Likely cause | Fix |
| :--- | :--- | :--- |
| FLAC but no MP3/MP4 | client died before conversion | run watchdog: `python3 scripts/convert-watchdog.py --prompt-id <ID> --format mp3` |
| Server refused | not running | `bash scripts/start-comfyui.sh` |
| OOM >35s | co-tenancy | keep ≤35s or standalone |
| Missing ffmpeg | not installed | `sudo apt-get install -y ffmpeg` |

---

## License

MIT. See [LICENSE](LICENSE).
