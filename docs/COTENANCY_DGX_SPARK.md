# DGX Spark Dual-Node Co-Tenancy & Memory Guide

## 1. Unified Memory Architecture (121 GiB UMA)

Each NVIDIA DGX Spark (GB10 / SM121) features **121 GiB of Unified Memory Architecture (UMA)** shared between CPU processes, desktop services, and GPU compute buffers.

---

## 2. Live Measured Memory Breakdown

Measured live on NVIDIA DGX Spark with **DeepSeek-V4-Flash TP2** actively serving:

```text
Component                                       Allocation
───────────────────────────────────────────────────────────
DeepSeek-V4-Flash (TP2 half-share)             95,637 MiB (~93.4 GB)
  ├─ Model Weights (NVFP4 MoE)                 ~79.5 GB
  └─ Physical KV Cache & Activation Buffers    ~13.9 GB
OS, Xorg, Desktop Services                     ~24 MiB
ComfyUI MiniMax Music3 (Peak During 25-35s)    4,463 MiB (~4.35 GB)
ComfyUI MiniMax Music3 (Idle Post-Run)         433 MiB (~0.42 GB)
───────────────────────────────────────────────────────────
Available Headroom Alongside DeepSeek          ~25.2 GiB Total Headroom
Lowest Observed Buffer (at 35s generation)     7.9 GiB Safe Buffer
```

---

## 3. 🚨 Critical Operational Rule: The 35-Second Co-Tenancy Ceiling

During live testing on the active cluster, we established the exact **safe operational duration envelope**:

| Duration | Acoustic Tokens | Latent Samples | Memory Behavior Under Co-Tenancy | Status |
| :---: | :---: | :---: | :--- | :---: |
| **10s – 25s** | 250 – 626 tokens | ~441k – 1.1M | Peak VRAM: **~4.4 GB** (Smooth, 7.9 GiB buffer) | **100% Safe** |
| **30s – 35s** | 750 – 876 tokens | ~1.3M – 1.5M | Peak VRAM: **~4.5 GB** (Clean VAE decode, no thrashing) | **100% Safe** |
| **60.0s+** | 1,501+ tokens | **2.65M+ samples** | **VAEDecodeAudio Memory Spike**: Decoding 2.65M unchunked samples across 128 latent channels while DiT weights remain cached causes an intermediate buffer allocation exceeding the ~25.2 GB headroom, triggering an OOM. | **Unsafe under Co-Tenancy** *(Safe in Standalone mode)* |

### Key Rule for Agents & Operators:
> [!IMPORTANT]
> When sharing the node with **DeepSeek-V4-Flash TP2**, **keep `--duration` at `≤ 35.0` seconds**.
> To run full 60s–300s songs, either run on a dedicated single-model node (with 116 GB free headroom) or execute in chunked clips.

---

## 4. Production Launch Flags

```bash
${PYTHON_BIN:-$HOME/ComfyUI/comfyui-env/bin/python} ${COMFY_DIR:-$HOME/ComfyUI}/main.py \
  --listen 0.0.0.0 \
  --port 8188 \
  --disable-pinned-memory \
  --disable-smart-memory \
  --disable-cuda-malloc
```

### Why These Flags Matter:
- `--disable-pinned-memory`: **Non-negotiable on unified memory**. Prevents CUDA from pre-allocating locked host memory, enabling Linux UMA to dynamically manage page caches without starving DeepSeek.
- `--disable-smart-memory`: Prevents aggressive persistent caching across inference requests.
- `--disable-cuda-malloc`: Uses native PyTorch memory allocator, preventing stream capture errors on dynamic sequence lengths.

---

## 5. Critical Start Order Rule (Tony & Drowzeys Architecture)

1. **Start DeepSeek-V4-Flash FIRST**:
   Let the language model complete its CUDA graph initialization and allocate its physical KV cache pool (~93.4 GB).
2. **Start ComfyUI MiniMax Music3 SECOND**:
   ComfyUI dynamically probes available unallocated memory and safely schedules its modular weights into the remaining ~28 GB headroom.
