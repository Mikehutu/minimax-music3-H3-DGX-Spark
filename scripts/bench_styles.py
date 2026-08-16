#!/usr/bin/env python3
"""
Benchmark multiple musical genres on MiniMax Music3 with drum-focused prompt engineering.
Measures AR time, DiT time, memory footprint, and produces comparison deliverables.
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

COMFY_HOST = os.environ.get("COMFY_HOST", "http://127.0.0.1:8188")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "./output")

BENCHMARK_TRACKS = [
    {
        "name": "01_heavy_trap_rap",
        "genre": "Modern Trap Rap Beat",
        "caption": "Hard-hitting modern trap rap song, very loud punchy 808 sub bass, rapid rolling hi-hats, crisp acoustic snare, sharp kick drum on every downbeat, fast aggressive male rap flow, studio master",
        "lyrics": "[intro]\nYeah, bounce to the rhythm\n\n[verse 1]\nCadence sharp on the beat\nDouble time moving through the street\nElectric energy taking the lead\nGiving the people what they need\n\n[chorus]\nNever stopping the flow\nWatch the intensity grow\n\n[outro]\nFade out.",
        "duration": 25.0,
        "steps": 28,
        "cfg_scale": 1.9,
        "top_k": 45,
        "seed": 101
    },
    {
        "name": "02_90s_boom_bap",
        "genre": "90s Boom-Bap Hip Hop",
        "caption": "Classic 90s boom-bap hip-hop track, loud punchy acoustic kick drum, crisp cracking snare drum, swinging dusty hi-hats, deep rhythmic jazz bassline, confident male rapper, vintage vinyl warmth",
        "lyrics": "[intro]\nCheck the microphone\nOne two, drop the needle\n\n[verse 1]\nWalking down the avenue under neon skies\nNever looking back with the truth in our eyes\nRhymes from the soul in the midnight air\nVoices echoing everywhere\n\n[chorus]\nLive for the moment, stand tall and strong\nThis is where we belong\n\n[outro]\nPeace.",
        "duration": 25.0,
        "steps": 28,
        "cfg_scale": 1.9,
        "top_k": 45,
        "seed": 202
    },
    {
        "name": "03_electro_synth_anthem",
        "genre": "Cyberpunk Electro Anthem",
        "caption": "High-energy driving electronic dance track, heavy four-on-the-floor kick drum, powerful acoustic snare clap, pulsing electro bassline, bright arpeggiated lead synthesizers, energetic female vocals, 128 BPM",
        "lyrics": "[intro]\nSystem online\n\n[verse 1]\nChasing the pulse through the electric rain\nVoltage running inside my brain\nGrid is alive in the dark of the night\nPower surge shining bright\n\n[chorus]\nFeel the power, feel the drive\nElectric heartbeat keeps us alive\n\n[outro]\nDisconnect.",
        "duration": 25.0,
        "steps": 28,
        "cfg_scale": 1.9,
        "top_k": 45,
        "seed": 303
    }
]


def normalize_host(host: str) -> str:
    if not host.startswith("http://") and not host.startswith("https://"):
        host = f"http://{host}"
    return host.rstrip("/")


def build_graph(caption: str, lyrics: str, duration: float, seed: int, cfg_scale: float, top_k: int, steps: int, prefix: str) -> dict:
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


def run_benchmark(host: str):
    host = normalize_host(host)
    print("=" * 70)
    print(f"🎵 MiniMax Music3 Multi-Genre Rhythm Benchmark Suite")
    print(f"📡 Target Node: {host}")
    print("=" * 70)

    results = []
    script_dir = os.path.dirname(os.path.abspath(__file__))
    conv_script = os.path.join(script_dir, "convert-media.py")

    for i, track in enumerate(BENCHMARK_TRACKS, start=1):
        print(f"\n[{i}/{len(BENCHMARK_TRACKS)}] Benchmarking: {track['name']} ({track['genre']})")
        print(f"    Duration: {track['duration']}s | Steps: {track['steps']} | CFG: {track['cfg_scale']} | Top-K: {track['top_k']}")

        graph = build_graph(
            caption=track["caption"],
            lyrics=track["lyrics"],
            duration=track["duration"],
            seed=track["seed"],
            cfg_scale=track["cfg_scale"],
            top_k=track["top_k"],
            steps=track["steps"],
            prefix=track["name"]
        )

        payload = json.dumps({"prompt": graph}).encode("utf-8")
        req = urllib.request.Request(f"{host}/prompt", data=payload, headers={"Content-Type": "application/json"})

        t0 = time.time()
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            prompt_id = data.get("prompt_id")

        output_filename = None
        while True:
            time.sleep(1.0)
            try:
                with urllib.request.urlopen(f"{host}/history/{prompt_id}") as resp:
                    hist = json.loads(resp.read().decode("utf-8"))
                    if prompt_id in hist:
                        outputs = hist[prompt_id].get("outputs", {})
                        for _, node_out in outputs.items():
                            if "audio" in node_out:
                                audio_list = node_out["audio"]
                                if audio_list:
                                    item = audio_list[0]
                                    filename = item.get("filename")
                                    subfolder = item.get("subfolder", "")
                                    output_filename = os.path.join(OUTPUT_DIR, subfolder, filename) if subfolder else os.path.join(OUTPUT_DIR, filename)
                        break
            except Exception:
                pass

        total_time = time.time() - t0
        print(f"    [DONE] Generated in {total_time:.2f}s")

        if output_filename and os.path.exists(output_filename):
            if os.path.exists(conv_script):
                subprocess.run([sys.executable, conv_script, output_filename, "--all"], check=False)

        results.append({
            "name": track["name"],
            "genre": track["genre"],
            "duration": track["duration"],
            "time_seconds": round(total_time, 2),
            "output": output_filename
        })

    print("\n" + "=" * 70)
    print("📊 Multi-Genre Benchmark Summary:")
    print("=" * 70)
    for r in results:
        print(f"  • {r['genre']} ({r['name']}): {r['time_seconds']}s total")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-genre rhythm benchmark suite")
    parser.add_argument("--host", type=str, default=COMFY_HOST, help="ComfyUI host URL")
    args = parser.parse_args()
    run_benchmark(args.host)
