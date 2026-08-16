# MiniMax DGX-Spark — Music3 + H3 ComfyUI toolkit

A clean, portable toolkit for running **MiniMax Music3** (text-to-music) and
**MiniMax H3** (text/image-to-video) through ComfyUI, optimized for and
documented against **NVIDIA DGX Spark (GB10 / 121 GB unified memory)**.

Designed to be **fully portable** — no personal hostnames, paths, or IPs are
hardcoded. Everything is ENV-driven. A dual-DGX-Spark co-tenant topology (one
node running a large LLM, another running ComfyUI for generation) is supported
as a documented profile, not a requirement.

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

| Hardware | VRAM / Mem | Supported |
| :--- | :--- | :--- |
| NVIDIA DGX Spark GB10 | 121 GB unified | ✅ primary target (fully tested) |
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

## Quick Start (h3)

```bash
bash scripts/setup-env.sh
bash scripts/download-models.sh h3         # ~all H3 checkpoints (bf16 + int8 variants)
bash scripts/start-comfyui.sh

# 5s video (no reference needed; refs optional for identity control)
python3 h3/generate-video.py --prompt "a calm ocean wave at dusk, photorealistic" --duration 5 --prefix my_clip
```

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

# Dual-node co-tenancy example (documented; not required): a large LLM on one
# DGX Spark, ComfyUI for generation on another, sharing 121 GB unified memory.
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
