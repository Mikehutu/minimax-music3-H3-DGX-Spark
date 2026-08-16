# Audio & Video Conversion Runbook

## 1. Overview

ComfyUI outputs audio natively as lossless 16-bit / 44.1 kHz stereo `.flac` files in the `output/` directory.

To share audio on Discord, Twitter/X, Instagram, YouTube, Telegram, or mobile devices, use the provided conversion utilities.

---

## 2. Automated CLI Tool

Use `scripts/convert-media.py`:

```bash
# Convert to both MP3 and MP4
python3 scripts/convert-media.py /path/to/track.flac --all

# Convert to MP3 only (320k)
python3 scripts/convert-media.py /path/to/track.flac --mp3

# Convert to MP4 with custom album cover art
python3 scripts/convert-media.py /path/to/track.flac --mp4 --cover cover.jpg
```

---

## 3. Direct FFMPEG Recipes

### Lossy MP3 (High Quality 320 kbps)
```bash
ffmpeg -y -i input.flac -codec:a libmp3lame -b:a 320k output.mp3
```

### MP4 Animated Neon Audio Waveform (720p / 25fps)
```bash
ffmpeg -y -i input.flac -filter_complex \
"[0:a]showwaves=s=1280x720:mode=cline:colors=0x00FFCC|0xFF007F:scale=sqrt[v]" \
-map "[v]" -map 0:a -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest output.mp4
```

### MP4 Full HD (1080p / 60fps Waveform)
```bash
ffmpeg -y -i input.flac -filter_complex \
"[0:a]showwaves=s=1920x1080:mode=cline:colors=0x00F0FF|0xFF0055:scale=sqrt:r=60[v]" \
-map "[v]" -map 0:a -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -b:a 320k -shortest output_1080p.mp4
```

### MP4 with Static Cover Artwork
```bash
ffmpeg -y -loop 1 -i cover.png -i input.flac -c:v libx264 -tune stillimage -c:a aac -b:a 320k -pix_fmt yuv420p -shortest output.mp4
```
