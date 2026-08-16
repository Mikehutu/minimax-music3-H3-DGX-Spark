#!/usr/bin/env python3
"""
Convert generated FLAC audio to MP3 and/or MP4 with an animated waveform visualizer.
Usage:
    python convert_media.py input.flac [--mp3] [--mp4] [--all] [--cover cover.jpg]
"""

import argparse
import os
import subprocess
import sys


def convert_to_mp3(input_flac: str, output_mp3: str, bitrate: str = "320k") -> bool:
    print(f"[INFO] Converting {input_flac} -> {output_mp3} (bitrate: {bitrate})...")
    cmd = [
        "ffmpeg", "-y",
        "-i", input_flac,
        "-codec:a", "libmp3lame",
        "-b:a", bitrate,
        output_mp3
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[ERROR] MP3 conversion failed: {res.stderr}", file=sys.stderr)
        return False
    print(f"[SUCCESS] Created MP3: {output_mp3} ({os.path.getsize(output_mp3) / 1024:.1f} KB)")
    return True


def convert_to_mp4(input_flac: str, output_mp4: str, cover_image: str = None) -> bool:
    print(f"[INFO] Converting {input_flac} -> {output_mp4}...")
    if cover_image and os.path.exists(cover_image):
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", cover_image,
            "-i", input_flac,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            output_mp4
        ]
    else:
        # Generate neon audio waveform visualizer (1280x720 25fps)
        cmd = [
            "ffmpeg", "-y",
            "-i", input_flac,
            "-filter_complex", "[0:a]showwaves=s=1280x720:mode=cline:colors=0x00FFCC|0xFF007F:scale=sqrt[v]",
            "-map", "[v]",
            "-map", "0:a",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_mp4
        ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[ERROR] MP4 conversion failed: {res.stderr}", file=sys.stderr)
        return False
    print(f"[SUCCESS] Created MP4: {output_mp4} ({os.path.getsize(output_mp4) / (1024*1024):.1f} MB)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Convert FLAC audio to MP3 and/or MP4")
    parser.add_argument("input_file", help="Path to input FLAC file")
    parser.add_argument("--mp3", action="store_true", help="Generate MP3 output")
    parser.add_argument("--mp4", action="store_true", help="Generate MP4 video with visualizer")
    parser.add_argument("--all", action="store_true", help="Generate both MP3 and MP4")
    parser.add_argument("--cover", type=str, default=None, help="Optional cover image for MP4")
    parser.add_argument("--bitrate", type=str, default="320k", help="Audio bitrate for MP3")
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"[ERROR] Input file not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    base, _ = os.path.splitext(args.input_file)
    do_all = args.all or (not args.mp3 and not args.mp4)

    if do_all or args.mp3:
        convert_to_mp3(args.input_file, f"{base}.mp3", bitrate=args.bitrate)

    if do_all or args.mp4:
        convert_to_mp4(args.input_file, f"{base}.mp4", cover_image=args.cover)


if __name__ == "__main__":
    main()
