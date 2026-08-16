#!/usr/bin/env python3
"""MiniMax H3 text/image-to-video CLI for ComfyUI (portable, ENV-driven).

Builds and submits an H3 ReferenceToVideo graph to a running ComfyUI instance.
ENV-driven so nothing is personal/cluster-specific:
  COMFY_HOST (or --host)  - ComfyUI server URL
  COMFY_OUTPUT_DIR        - where ComfyUI writes outputs (local fs)
  H3_UNET / H3_CLIP / H3_VAE / H3_AUDIO_VAE  - optional checkpoint name overrides

Usage:
  python h3/generate-video.py --prompt "a serene ocean wave at dusk" \
      --duration 5 --width 1280 --height 720 --prefix my_clip
  # with reference image(s):
  python h3/generate-video.py --prompt "..." --reference refs/hero.png --duration 5

Frames follow H3's 17n+5 grid. A requested duration is rounded UP to the
next valid count (e.g. 5s @24fps = 120 -> 124 = 17*7+5).
If no reference is supplied, a minimal blank frame is generated so the graph
still validates (reference-to-video still drives the latent).
"""
import json, math, os, sys, tempfile, time, urllib.request


def normalize_host(h):
    return (h if h.startswith("http://") or h.startswith("https://") else "http://" + h).rstrip("/")


def frames_for_seconds(seconds, fps=24):
    target = int(round(seconds * fps))
    # H3 wants a 17n+5 frame grid.
    return max((17 * math.ceil((target - 5) / 17)) + 5, 22) if target >= 5 else 22


def build(prompt, width, height, length, refs, seed, steps,
          unet, clip, video_vae, audio_vae, prefix, ref_img_size="max"):
    g = {
        "6": {"class_type": "UNETLoader", "inputs": {"unet_name": unet, "weight_dtype": "default"}},
        "13": {"class_type": "CLIPLoader", "inputs": {"clip_name": clip, "type": "minimax", "device": "default"}},
        "11": {"class_type": "VAELoader", "inputs": {"vae_name": video_vae}},
        "24": {"class_type": "VAELoader", "inputs": {"vae_name": audio_vae}},
    }
    ref_node_ids = []
    for i, (path, name) in enumerate(refs):
        nid = str(201 + i)
        # Each LoadImage names the file as it appears in ComfyUI's input dir.
        g[nid] = {"class_type": "LoadImage", "inputs": {"image": name, "upload": "image"}}
        ref_node_ids.append(nid)
    if not ref_node_ids:
        # Minimal 1x1 blank image node so the graph validates without refs.
        g["200"] = {"class_type": "LoadImage", "inputs": {"image": "h3_blank_ref.png"}}
        ref_node_ids = ["200"]
    g["230"] = {"class_type": "MiniMaxH3ReferenceToVideo",
                "inputs": {"clip": ["13", 0], "vae": ["11", 0], "audio_vae": ["24", 0],
                           "ref_images": ref_node_ids, "prompt": prompt,
                           "width": width, "height": height, "length": length,
                           "ref_image_size": ref_img_size}}
    g.update({
        "16": {"class_type": "BasicGuider", "inputs": {"model": ["6", 0], "conditioning": ["230", 0]}},
        "17": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "res_multistep"}},
        "9": {"class_type": "BasicScheduler", "inputs": {"model": ["6", 0], "scheduler": "simple", "steps": steps, "denoise": 1.0}},
        "15": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "14": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["15", 0], "guider": ["16", 0], "sampler": ["17", 0], "sigmas": ["9", 0], "latent_image": ["230", 1]}},
        "10": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["11", 0]}},
        "23": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["14", 0], "vae": ["24", 0]}},
        "91": {"class_type": "CreateVideo", "inputs": {"images": ["10", 0], "audio": ["23", 0], "fps": 24.0}},
        "92": {"class_type": "SaveVideo", "inputs": {"video": ["91", 0], "filename_prefix": prefix, "format": "auto", "codec": "auto"}},
    })
    return g


def main():
    import argparse
    ap = argparse.ArgumentParser(description="MiniMax H3 text/image-to-video CLI (portable)")
    ap.add_argument("--prompt", required=True, help="video prompt (integrated_multimodal_description schema)")
    ap.add_argument("--duration", type=float, default=5.0, help="desired seconds; rounded UP to H3 frame grid")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--prefix", default="h3_clip")
    ap.add_argument("--host", default=os.environ.get("COMFY_HOST", "http://127.0.0.1:8188"))
    ap.add_argument("--output-dir", default=os.environ.get("COMFY_OUTPUT_DIR", os.path.expanduser("~/ComfyUI/output")))
    ap.add_argument("--reference", action="append", default=[], help="image filename as exposed in ComfyUI input dir (repeatable)")
    # checkpoint overrides
    ap.add_argument("--unet", default=os.environ.get("H3_UNET", "minimax_h3_fl2va_pruned_int8_convrot.safetensors"))
    ap.add_argument("--clip", default=os.environ.get("H3_CLIP", "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"))
    ap.add_argument("--video-vae", default=os.environ.get("H3_VAE", "minimax_h3_video_vae_fp16.safetensors"))
    ap.add_argument("--audio-vae", default=os.environ.get("H3_AUDIO_VAE", "minimax_h3_audio_vae_fp32.safetensors"))
    ap.add_argument("--ref-image-size", default="max")
    ap.add_argument("--files-per-second", type=float, default=24.0)
    args = ap.parse_args()

    host = normalize_host(args.host)
    length = frames_for_seconds(args.duration, int(args.files_per_second))
    print(f"[H3] duration {args.duration}s -> {length} frames @{args.files_per_second:.0f}fps, res {args.width}x{args.height}", flush=True)

    refs = [(None, r) for r in args.reference]
    graph = build(args.prompt, args.width, args.height, length, refs, args.seed, args.steps,
                  args.unet, args.clip, args.video_vae, args.audio_vae, args.prefix)

    t0 = time.time()
    body = json.dumps({"prompt": graph}).encode()
    req = urllib.request.Request(f"{host}/prompt", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        pid = json.loads(r.read().decode()).get("prompt_id")
    print(f"[H3] submitted {pid}, submit {time.time()-t0:.1f}s", flush=True)

    last = time.time()
    while True:
        time.sleep(5)
        try:
            with urllib.request.urlopen(f"{host}/history/{pid}", timeout=20) as r:
                h = json.loads(r.read().decode())
            if pid in h:
                st = h[pid].get("status", {})
                if st.get("status_str") == "error":
                    print("[H3] ERROR", st.get("messages"), file=sys.stderr)
                    sys.exit(1)
                elapsed = time.time() - t0
                print(f"[H3] COMPLETED in {elapsed:.1f}s")
                for _, no in h[pid].get("outputs", {}).items():
                    if "videos" in no:
                        print("VIDEO_OUTPUT", no["videos"][0].get("filename"))
                return 0
        except Exception:
            pass
        now = time.time()
        if now - last > 30:
            print(f"[H3] still running {int(now-t0)}s", flush=True)
            last = now


if __name__ == "__main__":
    sys.exit(main())
