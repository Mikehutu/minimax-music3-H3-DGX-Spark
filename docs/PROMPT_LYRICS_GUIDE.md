# 📖 MiniMax Music3 Prompt & Lyrics Engineering Guide

This guide details how **MiniMax Music3** processes style prompts versus lyrics, explains the underlying tokenizer mechanics, and shows how to achieve punchy instrumentals and realistic vocal performances without style words bleeding into sung lyrics.

---

## 🧠 1. How MiniMax Music3 Tokenization Works

Behind the scenes in [`comfy/ldm/minimax_music/prompt.py`](file://${COMFY_DIR:-$HOME/ComfyUI-music3}/comfy/ldm/minimax_music/prompt.py), the text encoder wraps your inputs into a strict token schema:

```text
<|im_start|><|caption_start|>{caption}<|caption_end|><|lyrics_start|>[start]
{lyrics}<|lyrics_end|><|im_end|><|audio_start|>
```

### The Strict Boundary:
1. **`<|caption_start|> ... <|caption_end|>` (Caption / Style)**:
   - Sets the global acoustic conditioning: genre, tempo, instruments, drum types, vocal timbre, and production atmosphere.
   - **The vocalist NEVER sings words in the caption.**
2. **`<|lyrics_start|> ... <|lyrics_end|>` (Lyrics / Vocal Transcript)**:
   - Serves as the **phonetic script** for the vocal synthesizer.
   - **Every word written in this section will be sung or rapped by the vocalist.**

---

## 🚫 2. Why "Boom-Bap Drums" Were Being Sung (The Lyric Bleed Pitfall)

If your vocalist sings: *"Heavy kick drum booming in your chest"* or *"Eight-o-eight thumping on the downbeat"*, it is because those words were placed inside the `lyrics` parameter instead of the `caption` parameter!

### ❌ The Common Mistake (Style in Lyrics):
```text
# CAPTION:
90s hip hop

# LYRICS:
[verse 1 - heavy boom bap drums, cracking snare]
Classic boom bap cracking on the beat
Heavy kick drum booming in your chest
```
> **What happens:** The model reads `"heavy boom bap drums, cracking snare"` and the lines as literal words for the rapper to say!

---

### ✅ The Proper Separation (Clean Sonic Styling):
```text
# CAPTION (Style & Production):
Classic 90s boom-bap hip-hop, loud punchy acoustic kick drum, crisp cracking snare drum on the 2 and 4, swinging dusty hi-hats, deep rhythmic jazz double bass, warm vinyl texture, confident male vocal, studio master

# LYRICS (Story & Rhymes ONLY):
[intro]
Check the microphone, one two.

[verse 1]
Walking through the shadows of the avenue
Got the vision in my mind and the point of view
Never look behind when you're aiming for the crown
Hear the echoes of the rhythm in the underground

[chorus]
Keep the fire burning through the midnight haze
Finding our direction through the endless maze

[outro]
Yeah, that's how we do it.
```

---

## 🏷️ 3. Recognized Structural Section Tags

MiniMax Music3 recognizes standardized bracket tags. **Do not add descriptive notes inside the brackets.**

| Tag | Purpose | Example |
| :--- | :--- | :--- |
| `[intro]` | Spoken intro, atmospheric buildup, or instrumental opening | `[intro]\nWarning. System online.` |
| `[verse]` / `[verse 1]` | Main storytelling verses | `[verse 1]\nCity lights shining in the dark...` |
| `[pre-chorus]` | Dynamic rise before the drop/hook | `[pre-chorus]\nCount down to the overload...` |
| `[chorus]` | Main melodic hook / full arrangement | `[chorus]\nWe are the glitch in the machine!` |
| `[drop]` | Climax / heavy bass drop | `[drop]\n[instrumental]` |
| `[bridge]` | Melodic shift or tempo breakdown | `[bridge]\nEverything is falling apart...` |
| `[instrumental]` | **Completely vocal-free** section (solo, beat break, riff) | `[instrumental]` |
| `[outro]` | Concluding outro or fade-out | `[outro]\nSystem shutdown.` |

---

## 🎯 4. The Golden Formula for Realistic Drum & Bass Production

To get heavy, authentic drums (Boom-Bap, Trap, Drum & Bass, Dubstep), front-load physical acoustic descriptors into the **Caption**:

### 1. Neurofunk / Drum & Bass with Dirty Wobbles:
```bash
python3 scripts/generate-music.py \
  --caption "Heavy 174 BPM Neurofunk Drum and Bass with aggressive dubstep wobbles, distorted reese bassline, screaming metallic synth screeches, loud punchy acoustic kick drum, crisp snapping snare on the 2 and 4, dark cyberpunk atmosphere, studio master" \
  --lyrics "[intro]\nWarning. System overloaded.\n\n[verse 1]\nWalking through the neon rain\nDigital distortion in my brain\n\n[drop]\n[instrumental]\n\n[chorus]\nWe are the glitch in the machine!\n\n[outro]\nFade out." \
  --duration 30.0 \
  --steps 28 \
  --cfg-scale 1.9 \
  --top-k 42
```

### 2. 90s Boom-Bap Hip Hop:
```bash
python3 scripts/generate-music.py \
  --caption "Classic 90s boom-bap hip-hop, loud punchy acoustic kick drum, crisp cracking snare drum on the 2 and 4, swinging dusty hi-hats, deep rhythmic jazz double bass, vintage vinyl crackle, confident male rapper, studio master" \
  --lyrics "[intro]\nYeah. Drop the needle.\n\n[verse 1]\nShadows on the sidewalk, neon in the night\nRhyming on the corner till the morning brings the light\n\n[chorus]\nLive from the heart, never fading away\n\n[outro]\nPeace out." \
  --duration 25.0 \
  --steps 28 \
  --cfg-scale 1.9 \
  --top-k 45
```

### 3. Pure Instrumental Solo (No Vocals):
If you want **100% instrumental music without any singing**:
```bash
python3 scripts/generate-music.py \
  --caption "Melodic liquid drum and bass, warm rolling reese bassline, fast syncopated Amen breakbeat drums, lush rhodes piano chords, uplifting atmosphere, 174 BPM" \
  --lyrics "[instrumental]" \
  --duration 30.0 \
  --prefix "pure_instrumental_dnb"
```

---

## 📊 Summary Checklist

- [x] Put **genre, BPM, kick/snare definitions, bassline type, synth style** in `--caption`.
- [x] Put **story lines, spoken words, vocal hooks** in `--lyrics`.
- [x] Use clean brackets like `[verse 1]`, `[chorus]`, `[drop]`, `[instrumental]`.
- [x] Avoid putting instrument descriptions inside lyric lines.
