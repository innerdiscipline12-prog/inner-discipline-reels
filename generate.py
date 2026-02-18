```python
# ============================
# V6 MASTER — REEL GENERATOR (7–12s)
# INNER DISCIPLINE • CLEAN BUILD • RANDOM BACKGROUNDS • NO OVERLAP • SAFE TEXT
# Works on GitHub Actions + Google Colab
# Requires: moviepy==1.0.3, numpy, Pillow, edge-tts, imageio, imageio-ffmpeg
# Files needed in repo:
#   bg.mp4 / bg1.mp4 / bg2.mp4 ... (any bg*.mp4)
#   Anton-Regular.ttf  (your font)
#   music.mp3          (optional)
# Output: outputs/01..05/reel.mp4 + caption.txt + thumb.jpg
# ============================

import os, random, glob, asyncio, textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    VideoFileClip, AudioFileClip, ImageClip,
    CompositeVideoClip, CompositeAudioClip
)
from moviepy.video.fx.all import resize
import edge_tts

# ================= SETTINGS =================

W, H = 1080, 1920
FPS = 30

REELS_PER_RUN = 5

# Reel length target (tight, high retention)
REEL_MIN_SEC = 7.0
REEL_MAX_SEC = 12.0

# Backgrounds
REEL_BACKGROUNDS = sorted(glob.glob("bg*.mp4"))
if not REEL_BACKGROUNDS:
    raise Exception("No reel backgrounds found. Add bg.mp4 / bg1.mp4 etc (bg*.mp4).")

# Optional music bed
MUSIC = "music.mp3"
MUSIC_VOL = 0.08

# Font
FONT_PATH = "Anton-Regular.ttf"
if not os.path.exists(FONT_PATH):
    raise Exception("Font not found. Put Anton-Regular.ttf in repo root.")

# Voice (Edge TTS) — deep-ish options
# Try these if you want even deeper:
# "en-US-GuyNeural", "en-US-ChristopherNeural", "en-GB-RyanNeural"
VOICE = "en-US-GuyNeural"
VOICE_RATE = "-20%"      # slower = deeper feel
VOICE_PITCH = "-40Hz"    # lower pitch

# Safe margins so text never cuts off
MARGIN_X = 180
MARGIN_Y = 260

# Fade
FADE_IN = 0.12
FADE_OUT = 0.12

HASHTAGS = [
    "#discipline", "#selfcontrol", "#focus",
    "#mindset", "#innerdiscipline",
    "#consistency", "#stoic", "#growth"
]

# ================= COPY BANK (V6 ALGO BANK) =================

HOOKS = [
    "You're not tired. You're undisciplined.",
    "Your comfort is stealing your future.",
    "You don't lack time. You lack control.",
    "Motivation didn't fail you. You did.",
    "Distraction is your real addiction.",
    "You keep choosing easy. Then you complain.",
    "Your habits are louder than your goals.",
    "You're not overwhelmed. You're unmanaged.",
    "You keep starting. You don't keep standards.",
    "You say you want change. Then you protect comfort.",
    "Your phone owns you more than you admit.",
    "You keep negotiating with weakness.",
    "If it was important, you'd already be consistent.",
    "The problem isn't life. It's your discipline.",
    "You don't need more information. You need execution.",
    "You keep waiting to feel ready.",
    "You're not unlucky. You're unstructured.",
    "You keep chasing dopamine. Then you lose focus.",
    "You're training yourself to quit.",
    "Your future is paying for your excuses."
]

TRUTHS = [
    "Discipline decides outcomes.",
    "Control beats motivation.",
    "Consistency builds identity.",
    "Standards remove struggle.",
    "Your environment shapes your behavior.",
    "You become what you repeat.",
    "Self-control is a skill. Train it.",
    "If you want results, remove the easy option.",
    "Your habits write your future.",
    "You don't rise to goals. You fall to systems.",
    "Small choices become permanent results.",
    "Focus is protected. Not found.",
    "Hard days reveal your real level.",
    "Comfort always sends an invoice.",
    "Discipline is quiet. But it changes everything.",
    "You can't drift and win.",
    "Your attention is your life.",
    "If you don't choose, you get chosen.",
    "Structure creates freedom.",
    "The standard is the solution."
]

RELATABLE = [
    "Some days you don't feel like it.",
    "You scroll and lose an hour.",
    "You delay what matters.",
    "You start strong. Then fade.",
    "You keep restarting the same week.",
    "You know what to do. You just don't do it.",
    "You get distracted easily.",
    "You break promises to yourself.",
    "You wait for the mood.",
    "You avoid the hardest task first.",
    "You chase quick comfort.",
    "You say tomorrow. Then repeat today.",
    "You plan a lot. Execute a little.",
    "You keep making exceptions.",
    "You fall back into old habits fast.",
    "You let small impulses lead your day.",
    "You quit when it gets boring.",
    "You talk about discipline more than you practice it.",
    "You want change without discomfort.",
    "You keep choosing what feels good now."
]

QUESTIONS = [
    "Still here?",
    "Day one. Or day one again?",
    "Are you done making excuses?",
    "Will you finish what you start?",
    "Do you have standards. Or moods?",
    "Who is in control. You or impulses?",
    "Will you do it. Even without the feeling?",
    "Are you building discipline. Or comfort?",
    "Are you consistent. Or just interested?",
    "Do you want results. Or relief?"
]

CTAS = [
    "Comment DISCIPLINE.",
    "Type DISCIPLINE.",
    "Comment CONTROL.",
    "Type CONTROLLED.",
    "Comment CONSISTENT.",
    "Type CONSISTENT.",
    "Comment STANDARDS.",
    "Type STANDARDS."
]

# ================= UTIL =================

def safe_remove(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except:
        pass

async def tts_to_file(text: str, out_path: str):
    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate=VOICE_RATE,
        pitch=VOICE_PITCH
    )
    await communicate.save(out_path)

def run_tts(text: str, out_path: str):
    asyncio.run(tts_to_file(text, out_path))

def pick_background_segment(bg_path: str, duration: float):
    base = VideoFileClip(bg_path).without_audio()

    # Resize/crop to vertical 9:16
    base = base.fx(resize, height=H)
    if base.w < W:
        base = base.resize(width=W)

    # Random subclip so it doesn't look repeated
    if base.duration > duration + 0.5:
        start = random.uniform(0, max(0.0, base.duration - duration - 0.1))
        base = base.subclip(start, start + duration)
    else:
        base = base.subclip(0, min(base.duration, duration))

    base = base.crop(
        x_center=base.w / 2,
        y_center=base.h / 2,
        width=W,
        height=H
    )

    # Subtle zoom for cinematic feel
    base = base.fx(resize, lambda t: 1.0 + 0.010 * t)

    return base

def wrap_lines_to_fit(draw, text, font, max_width):
    words = text.split()
    if len(words) <= 1:
        return text

    # Try wrapping into 2–4 lines for big readable text
    best = text
    for width in range(18, 8, -1):
        wrapped = "\n".join(textwrap.wrap(text, width=width))
        bbox = draw.multiline_textbbox((0,0), wrapped, font=font, spacing=18, align="center")
        w = bbox[2] - bbox[0]
        if w <= max_width:
            best = wrapped
            break
    return best

def fit_text_image(text, w=W, h=H, font_path=FONT_PATH,
                   max_size=150, min_size=68, margin_px=180, shadow=True):
    """
    Returns an RGBA numpy array that is ALWAYS safe within margins.
    """
    img = Image.new("RGBA", (w, h), (0,0,0,0))
    d = ImageDraw.Draw(img)

    max_text_w = w - (margin_px * 2)
    max_text_h = h - (margin_px * 2)

    size = max_size
    chosen_font = ImageFont.truetype(font_path, size)

    while size >= min_size:
        font = ImageFont.truetype(font_path, size)
        wrapped = wrap_lines_to_fit(d, text, font, max_text_w)

        bbox = d.multiline_textbbox((0,0), wrapped, font=font, spacing=22, align="center")
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        if tw <= max_text_w and th <= max_text_h:
            chosen_font = font
            text = wrapped
            break
        size -= 4

    bbox = d.multiline_textbbox((0,0), text, font=chosen_font, spacing=22, align="center")
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    x = (w - tw) // 2
    y = (h - th) // 2

    if shadow:
        d.multiline_text(
            (x+6, y+6), text,
            font=chosen_font, fill=(0,0,0,190),
            spacing=22, align="center"
        )
    d.multiline_text(
        (x, y), text,
        font=chosen_font, fill=(255,255,255,255),
        spacing=22, align="center"
    )

    return np.array(img)

def make_thumbnail(text, out_path):
    # Simple thumb from the HOOK line
    thumb = Image.new("RGB", (1080, 1920), (0,0,0))
    d = ImageDraw.Draw(thumb)

    font = ImageFont.truetype(FONT_PATH, 160)
    wrapped = "\n".join(textwrap.wrap(text, width=10))

    bbox = d.multiline_textbbox((0,0), wrapped, font=font, spacing=18, align="center")
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (1080 - tw)//2
    y = (1920 - th)//2

    d.multiline_text((x+6,y+6), wrapped, font=font, fill=(0,0,0), spacing=18, align="center")
    d.multiline_text((x,y), wrapped, font=font, fill=(255,255,255), spacing=18, align="center")

    thumb.save(out_path)

def make_caption(lines, out_path):
    # Short caption based on first 2 lines
    cap = f"{lines[0]} {lines[1]}"
    tags = " ".join(random.sample(HASHTAGS, 4))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(cap.strip() + "\n\n" + tags)

def build_reel_script(reel_index: int):
    """
    3-line structure for 7–12s:
      Hook (punch)
      Relatable or Truth (reinforce)
      Ending (CTA on 2 reels, Question on 3 reels)
    """
    hook = random.choice(HOOKS)

    mid = random.choice([random.choice(RELATABLE), random.choice(TRUTHS)])

    # 2 reels CTA, 3 reels question (per run of 5)
    # (indexes 1..5) -> CTA on 1,3 ; Question on 2,4,5
    if reel_index in (1, 3):
        end = random.choice(CTAS)
    else:
        end = random.choice(QUESTIONS)

    return [hook, mid, end]

def durations_for_lines(lines):
    """
    Hard control reel length (no overlap, no runaway).
    We don't trust TTS duration. We enforce:
      hook ~2.6s
      mid  ~2.3s
      end  ~2.6s (CTA/Q)
    Total ~7.5–8.0 seconds.
    """
    if len(lines) != 3:
        return [2.4] * len(lines)

    return [2.6, 2.3, 2.6]

# ================= MAIN: MAKE ONE REEL =================

def make_reel(idx: int):
    folder = f"outputs/{idx:02d}"
    os.makedirs(folder, exist_ok=True)

    # pick different background per reel
    bg_path = random.choice(REEL_BACKGROUNDS)

    script = build_reel_script(idx)
    durs = durations_for_lines(script)

    # Build audio + overlays with strict timing
    audio_clips = []
    text_clips = []
    t = 0.0

    # generate & place voice sequentially (no overlap)
    for i, line in enumerate(script):
        tmp = f"{folder}/tmp_{i}.mp3"
        run_tts(line, tmp)

        a = AudioFileClip(tmp)
        dur = float(durs[i])

        # Text overlay image
        overlay = fit_text_image(
            line, W, H, FONT_PATH,
            max_size=150, min_size=68,
            margin_px=MARGIN_X, shadow=True
        )

        txt = (
            ImageClip(overlay, ismask=False)
            .set_start(t)
            .set_duration(dur)
            .fadein(FADE_IN)
            .fadeout(FADE_OUT)
        )

        text_clips.append(txt)

        # AUDIO starts exactly at t (prevents jumping ahead)
        audio_clips.append(a.set_start(t))

        t += dur
        safe_remove(tmp)

    # clamp final length to 7–12 range (our fixed durs already fit)
    final_len = max(REEL_MIN_SEC, min(t, REEL_MAX_SEC))

    # background segment (random start)
    base = pick_background_segment(bg_path, final_len)

    voice_mix = CompositeAudioClip(audio_clips)

    # optional music bed
    if os.path.exists(MUSIC):
        music = AudioFileClip(MUSIC)
        if music.duration > final_len:
            music = music.subclip(0, final_len)
        else:
            # loop by simple concat if needed
            loops = int(final_len // max(0.01, music.duration)) + 1
            music = CompositeAudioClip([music.set_start(i * music.duration) for i in range(loops)])
        music = music.volumex(MUSIC_VOL)

        final_audio = CompositeAudioClip([music, voice_mix])
    else:
        final_audio = voice_mix

    final = CompositeVideoClip([base] + text_clips).set_duration(final_len)
    final = final.set_audio(final_audio)

    out_mp4 = f"{folder}/reel.mp4"
    final.write_videofile(
        out_mp4,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        threads=2,
        preset="medium",
        verbose=False,
        logger=None
    )

    make_thumbnail(script[0], f"{folder}/thumb.jpg")
    make_caption(script, f"{folder}/caption.txt")

# ================= RUN =================

def main():
    os.makedirs("outputs", exist_ok=True)
    for i in range(1, REELS_PER_RUN + 1):
        make_reel(i)
    print("✅ V6 MASTER COMPLETE — reels in /outputs")

if __name__ == "__main__":
    main()
```
