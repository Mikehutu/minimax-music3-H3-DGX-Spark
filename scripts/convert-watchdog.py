#!/usr/bin/env python3
"""
Disconnect-resilient auto-conversion watchdog for MiniMax (music3) / video outputs on ComfyUI.

Usage:
    python convert-watchdog.py --prompt-id <ID> --host http://<NODE_IP>:8188 \
        --output-dir <dir> --format mp3 [--cover image.jpg] [--converter path/to/convert-media.py]

Designed for the case where generate-music.py is run under an SSH session that
may disconnect before the (slow) AR+DiT generation completes: this watchdog
polls ComfyUI /history for the given prompt, and once the FLAC appears it runs
convert-media.py to make the requested format(s). It is meant to be started
DETACHED (nohup … &  or  setsid … &) right after submitting the prompt, so
conversion happens even if the caller is killed.
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request


def wait_and_convert(host, prompt_id, output_dir, formats, converter=None, cover=None, poll=10, timeout=7200):
    host = host.rstrip("/")
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(f"{host}/history/{prompt_id}", timeout=20) as resp:
                hist = json.loads(resp.read().decode("utf-8"))
            if prompt_id in hist:
                status = hist[prompt_id].get("status", {})
                if status.get("status_str") == "error":
                    print(f"[WATCHDOG] Job {prompt_id} errored: {status.get('messages')}", file=sys.stderr)
                    return 1

                flac_path = None
                for _, node_out in hist[prompt_id].get("outputs", {}).items():
                    for aud in node_out.get("audio", []):
                        fname = aud.get("filename")
                        sub = aud.get("subfolder", "")
                        flac_path = os.path.join(output_dir, sub, fname) if sub else os.path.join(output_dir, fname)
                        break
                    if flac_path:
                        break

                if flac_path and os.path.exists(flac_path):
                    print(f"[WATCHDOG] FLAC ready: {flac_path}")
                    base = os.path.splitext(flac_path)[0]

                    if converter:
                        if "mp3" in formats:
                            print("[WATCHDOG] Converting FLAC -> MP3 (320k)")
                            subprocess.run([sys.executable, converter, flac_path, "--mp3"], check=False)
                        if "mp4" in formats:
                            cmd = [sys.executable, converter, flac_path, "--mp4"]
                            if cover:
                                cmd.extend(["--cover", cover])
                            print("[WATCHDOG] Converting FLAC -> MP4 waveform")
                            subprocess.run(cmd, check=False)
                    else:
                        # Direct ffmpeg fallback
                        if "mp3" in formats:
                            subprocess.run(["ffmpeg", "-y", "-i", flac_path, "-codec:a", "libmp3lame", "-b:a", "320k", f"{base}.mp3"], check=False)
                        if "mp4" in formats:
                            subprocess.run(["ffmpeg", "-y", "-i", flac_path, "-filter_complex", "[0:a]showwaves=s=1280x720:mode=cline:colors=0x00FFCC|0xFF007F:scale=sqrt[v]", "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", f"{base}.mp4"], check=False)
                    print("[WATCHDOG] Conversion complete.")
                    return 0
        except Exception as e:
            print(f"[WATCHDOG] Polling error: {e}", file=sys.stderr)
        time.sleep(poll)

    print(f"[WATCHDOG] Timed out after {timeout}s waiting for {prompt_id}.", file=sys.stderr)
    return 2


def main():
    parser = argparse.ArgumentParser(description="Auto-convert when a ComfyUI prompt finishes, surviving client disconnects")
    parser.add_argument("--prompt-id", required=True, help="ComfyUI prompt ID to watch")
    parser.add_argument("--host", default=os.environ.get("COMFY_HOST", "http://127.0.0.1:8188"), help="ComfyUI server URL (default: COMFY_HOST env or localhost:8188)")
    parser.add_argument("--output-dir", default=os.environ.get("COMFY_OUTPUT_DIR", os.path.expanduser("~/ComfyUI/output")), help="Directory where ComfyUI writes output audio")
    parser.add_argument("--format", action="append", choices=["mp3", "mp4"], help="Format(s) to produce (repeatable; default: mp3)")
    parser.add_argument("--converter", default=None, help="Path to convert-media.py (default: sibling of this script)")
    parser.add_argument("--cover", default=None, help="Cover image for MP4")
    parser.add_argument("--poll", type=int, default=10, help="Poll interval seconds (default 10)")
    parser.add_argument("--timeout", type=int, default=7200, help="Max seconds to wait (default 7200)")
    args = parser.parse_args()

    formats = args.format or ["mp3"]

    if args.converter is None:
        args.converter = os.path.join(os.path.dirname(os.path.abspath(__file__)), "convert-media.py")

    rc = wait_and_convert(
        host=args.host,
        prompt_id=args.prompt_id,
        output_dir=args.output_dir,
        formats=formats,
        converter=args.converter,
        cover=args.cover,
        poll=args.poll,
        timeout=args.timeout,
    )
    sys.exit(rc)


if __name__ == "__main__":
    main()
