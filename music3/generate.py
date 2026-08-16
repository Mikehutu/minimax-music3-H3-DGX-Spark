#!/usr/bin/env python3
"""
CLI tool to generate music, songs, or instrumentals using MiniMax Music3 on ComfyUI.
Supports local or remote cluster execution and automatic post-processing (MP3 / MP4).
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

DEFAULT_HOST = os.environ.get("COMFY_HOST", "http://127.0.0.1:8188")
DEFAULT_OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "./output")


def normalize_host(host: str) -> str:
    if not host.startswith("http://") and not host.startswith("https://"):
        host = f"http://{host}"
    return host.rstrip("/")


def build_music3_graph(caption: str, lyrics: str, duration: float, seed: int, cfg_scale: float, top_k: int, steps: int, prefix: str) -> dict:
    return {
        "1": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": "minimax_music3_text_encoder_pruned_int8_convrot.safetensors",
                "type": "minimax"
            }
        },
        "2": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "minimax_music3_dit_int8_convrot.safetensors",
                "weight_dtype": "default"
            }
        },
        "3": {
            "class_type": "VAELoader",
            "inputs": {
                "vae_name": "minimax_music3_dav.safetensors"
            }
        },
        "4": {
            "class_type": "MiniMaxMusic3TextEncode",
            "inputs": {
                "clip": ["1", 0],
                "caption": caption,
                "lyrics": lyrics,
                "seed": seed,
                "max_duration": duration,
                "cfg_scale": cfg_scale,
                "top_k": top_k
            }
        },
        "5": {
            "class_type": "EmptyMiniMaxMusic3LatentAudio",
            "inputs": {
                "seconds": ["4", 1],
                "batch_size": 1
            }
        },
        "6": {
            "class_type": "ConditioningZeroOut",
            "inputs": {
                "conditioning": ["4", 0]
            }
        },
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["2", 0],
                "positive": ["4", 0],
                "negative": ["6", 0],
                "latent_image": ["5", 0],
                "seed": seed,
                "steps": steps,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0
            }
        },
        "8": {
            "class_type": "VAEDecodeAudio",
            "inputs": {
                "samples": ["7", 0],
                "vae": ["3", 0]
            }
        },
        "9": {
            "class_type": "SaveAudio",
            "inputs": {
                "audio": ["8", 0],
                "filename_prefix": prefix
            }
        }
    }


def check_server(host: str) -> bool:
    try:
        req = urllib.request.urlopen(f"{host}/system_stats", timeout=4)
        return req.getcode() == 200
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate music with MiniMax Music3 in ComfyUI")
    parser.add_argument("--caption", type=str, required=True, help="Style/genre/instrumentation prompt")
    parser.add_argument("--lyrics", type=str, default="[instrumental]", help="Lyrics with structure tags ([verse], [chorus], [instrumental], etc.)")
    parser.add_argument("--duration", type=float, default=30.0, help="Duration in seconds (e.g. 10.0 to 120.0)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--cfg-scale", type=float, default=1.8, help="Text encoder CFG scale")
    parser.add_argument("--top-k", type=int, default=50, help="Top-K token sampling")
    parser.add_argument("--steps", type=int, default=25, help="DiT sampling steps")
    parser.add_argument("--prefix", type=str, default="minimax_music3_track", help="Output filename prefix")
    parser.add_argument("--format", choices=["flac", "mp3", "mp4", "all"], default="mp3", help="Output formats to produce (default: mp3 only; use 'all' to also make an MP4 waveform video)")
    parser.add_argument("--cover", type=str, default=None, help="Cover image path for MP4 visualizer")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST, help="ComfyUI server URL or IP:Port (e.g. http://<NODE_IP>:8188)")
    args = parser.parse_args()

    host = normalize_host(args.host)

    if args.duration > 35.0:
        print(f"[WARN] Duration is set to {args.duration}s. Under live GPU co-tenancy (alongside large LLMs), durations > 35.0s can cause memory spikes during unchunked VAE decoding. Recommended co-tenancy ceiling: <= 35.0s.")

    print(f"[INFO] Connecting to ComfyUI node at: {host}")
    if not check_server(host):
        print(f"[ERROR] ComfyUI is not reachable at {host}.", file=sys.stderr)
        print(f"[HINT] If running across cluster nodes, verify the node IP and network route (e.g. curl {host}/system_stats).", file=sys.stderr)
        print(f"[HINT] If running locally on this node, ensure server is started via scripts/start-comfyui.sh.", file=sys.stderr)
        sys.exit(1)

    graph = build_music3_graph(
        caption=args.caption,
        lyrics=args.lyrics,
        duration=args.duration,
        seed=args.seed,
        cfg_scale=args.cfg_scale,
        top_k=args.top_k,
        steps=args.steps,
        prefix=args.prefix
    )

    payload = json.dumps({"prompt": graph}).encode("utf-8")
    req = urllib.request.Request(f"{host}/prompt", data=payload, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            prompt_id = data.get("prompt_id")
    except Exception as e:
        print(f"[ERROR] Failed to queue prompt: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Prompt queued successfully on {host} (ID: {prompt_id}). Generating audio...")

    start_time = time.time()
    last_poll = start_time
    output_filename = None

    while True:
        time.sleep(1.0)
        try:
            with urllib.request.urlopen(f"{host}/history/{prompt_id}") as resp:
                hist = json.loads(resp.read().decode("utf-8"))
                if prompt_id in hist:
                    status = hist[prompt_id].get("status", {})
                    if status.get("status_str") == "error":
                        print(f"[ERROR] Generation failed: {status.get('messages')}", file=sys.stderr)
                        sys.exit(1)

                    outputs = hist[prompt_id].get("outputs", {})
                    for _, node_out in outputs.items():
                        if "audio" in node_out:
                            audio_list = node_out["audio"]
                            if audio_list:
                                item = audio_list[0]
                                filename = item.get("filename")
                                subfolder = item.get("subfolder", "")
                                output_filename = os.path.join(DEFAULT_OUTPUT_DIR, subfolder, filename) if subfolder else os.path.join(DEFAULT_OUTPUT_DIR, filename)
                    break
        except Exception:
            pass

        if time.time() - last_poll > 15:
            elapsed = int(time.time() - start_time)
            print(f"[INFO] Generation in progress... ({elapsed}s elapsed)")
            last_poll = time.time()

    elapsed = time.time() - start_time
    print(f"[SUCCESS] Generation completed in {elapsed:.1f}s!")

    if output_filename and os.path.exists(output_filename):
        print(f"[OUTPUT] FLAC: {output_filename}")
        repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        conv_script = os.path.join(repo_dir, "scripts", "convert-media.py")

        if args.format in ("mp3", "all") and os.path.exists(conv_script):
            subprocess.run([sys.executable, conv_script, output_filename, "--mp3"], check=False)
        if args.format in ("mp4", "all") and os.path.exists(conv_script):
            cmd = [sys.executable, conv_script, output_filename, "--mp4"]
            if args.cover:
                cmd.extend(["--cover", args.cover])
            subprocess.run(cmd, check=False)
    else:
        print(f"[WARN] Completed but could not locate output file at {output_filename}")


if __name__ == "__main__":
    main()
