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
DEFAULT_OUTPUT_DIR = "${COMFY_DIR:-$HOME/ComfyUI-music3}/output"


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
                "unet_name": "minimax_music3_dit_fp16.safetensors",
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
    parser.add_argument("--format", choices=["flac", "mp3", "mp4", "all"], default="all", help="Output formats to produce")
    parser.add_argument("--cover", type=str, default=None, help="Cover image path for MP4 visualizer")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST, help="ComfyUI server URL or IP:Port (e.g. http://<NODE_IP>:8188)")
    args = parser.parse_args()

    host = normalize_host(args.host)

    print(f"[INFO] Connecting to ComfyUI node at: {host}")
    if not check_server(host):
        print(f"[ERROR] ComfyUI is not reachable at {host}.", file=sys.stderr)
        print(f"[HINT] If running across cluster nodes, verify the node IP and network route (e.g. curl {host}/system_stats).", file=sys.stderr)
        print(f"[HINT] If running locally on this node, ensure server is started via scripts/start-comfyui-music3.sh.", file=sys.stderr)
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

    req_data = json.dumps({"prompt": graph}).encode("utf-8")
    req = urllib.request.Request(f"{host}/prompt", data=req_data, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req)
        res_json = json.loads(resp.read().decode("utf-8"))
        prompt_id = res_json.get("prompt_id")
        print(f"[INFO] Prompt queued successfully on {host} (ID: {prompt_id}). Generating audio...")
    except Exception as e:
        print(f"[ERROR] Failed to queue prompt: {e}", file=sys.stderr)
        sys.exit(1)

    # Poll for completion
    start_t = time.time()
    flac_path = None
    while True:
        time.sleep(2)
        try:
            hist_req = urllib.request.urlopen(f"{host}/history/{prompt_id}")
            hist = json.loads(hist_req.read().decode("utf-8"))
            if prompt_id in hist:
                status = hist[prompt_id].get("status", {})
                if status.get("status_str") == "error":
                    print(f"[ERROR] Execution failed on {host}: {status}", file=sys.stderr)
                    sys.exit(1)

                outputs = hist[prompt_id].get("outputs", {})
                save_node = outputs.get("9", {})
                audio_list = save_node.get("audio", [])
                if audio_list:
                    filename = audio_list[0].get("filename")
                    subfolder = audio_list[0].get("subfolder", "")
                    flac_path = os.path.join(DEFAULT_OUTPUT_DIR, subfolder, filename)
                break
        except Exception as e:
            print(f"[WARN] Polling history: {e}")

    elapsed = time.time() - start_t
    print(f"[SUCCESS] Generation completed in {elapsed:.1f}s!")

    if flac_path and os.path.exists(flac_path):
        print(f"[OUTPUT] FLAC: {flac_path}")

        # Post-process formats
        script_dir = os.path.dirname(os.path.abspath(__file__))
        converter_script = os.path.join(script_dir, "convert-media.py")

        convert_cmd = [sys.executable, converter_script, flac_path]
        if args.format == "mp3":
            convert_cmd.append("--mp3")
        elif args.format == "mp4":
            convert_cmd.append("--mp4")
        elif args.format == "all":
            convert_cmd.append("--all")

        if args.cover:
            convert_cmd.extend(["--cover", args.cover])

        if args.format != "flac":
            subprocess.run(convert_cmd)
    else:
        if flac_path:
            print(f"[INFO] Remote generation complete. File saved on node at: {flac_path}")
        else:
            print(f"[WARN] Output file metadata could not be retrieved from {host}.")


if __name__ == "__main__":
    main()
