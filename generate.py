import os, json, random, asyncio, re
import numpy as np
from moviepy.editor import (
    VideoFileClip, ImageClip, CompositeVideoClip,
    AudioFileClip, CompositeAudioClip
)
from moviepy.video.fx.all import resize
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# =========================
# PRO V2 SETTINGS
# =========================
VIDEO = "bg.mp4"                 # your background video in repo
MUSIC = "music.mp3"              # optional (if missing, it will still work)
FONT_PATH = "Anton-Regular.ttf"  # make sure this file is in repo root

W, H = 1080, 1920

SAFE_TOP = 350
SAFE_BOTTOM = 450
SAFE_H = H - SAFE_TOP - SAFE_BOTTOM

MAX_SECONDS = 14.0

# Voice (deeper + calmer)
VOICE = "en-US-ChristopherNeural"
VOICE_RATE = "-40%"   # slower
VOICE_PITCH = "-20Hz" # deeper

# Music mix
VOICE_GAIN = 2.0          # voice louder
MUSIC_BASE = 0.18         # base music volume
DUCK_FACTOR = 0.22        # music becomes ~22% when voice is speaking
MUSIC_FINAL = 0.75        # after ducking, overall trim

# Thumbnail style
THUMB_FONT_START = 210
THUMB_MAX_W = int(1080 * 0.88)

# Caption / CTA / hashtags
CTA_LINE = 'COMMENT "DISCIPLINE" I’ll send you the challenge.'
HASHTAGS = ["#discipline", "#selfcontrol", "#mindset", "#consistency", "#stoic", "#hardwork", "#focus", "#habits"]

# =========================
# SCRIPT PACK (Expand here)
# =========================

# Weighted hooks (stronger lines appear more often)
HOOKS = [
    ("STOP NEGOTIATING", 10),
    ("NO ONE IS COMING", 9),
    ("COMFORT IS THE ENEMY", 9),
    ("DISCIPLINE DECIDES", 8),
    ("CONTROL YOURSELF", 8),
    ("PROVE IT QUIETLY", 7),
    ("DO THE HARD THING", 9),
    ("YOU WAIT FOR MOTIVATION", 7),
]

# Main pool (add 35–50+ here)
LINES = [
    "YOU WAIT FOR MOTIVATION",
    "YOU SAY YOU ARE TIRED",
    "YOU BLAME YOUR MOOD",
    "YOU WANT CHANGE WITHOUT PAIN",
    "COMFORT IS THE ENEMY",
    "NO ONE IS COMING",
    "DISCIPLINE DECIDES",
    "CONTROL YOURSELF",
    "YOUR HABITS SHOW",
    "PROVE IT QUIETLY",
    "YOUR ROUTINE EXPOSES YOU",
    "STOP NEGOTIATING",
    "DO THE HARD THING",
    "CONSISTENCY BUILDS POWER",
    "THIS IS DISCIPLINE",
    "STANDARDS DONT NEGOTIATE",
    "YOUR FEELINGS ARE NOT ORDERS",
    "DO IT WITHOUT APPLAUSE",
    "EXCUSES DONT BUILD RESULTS",
    "YOU DONT NEED MORE TIME",
    "YOU NEED MORE CONTROL",
    "COMMIT THEN EXECUTE",
    "SILENCE YOUR IMPULSE",
    "TRAIN THE BORING DAYS",
    "WIN THE SMALL MOMENTS",
    "DISCIPLINE IS A DECISION",
    "CONTROL IS BUILT NOT FOUND",
    "RESULTS FOLLOW STRUCTURE",
    "DO IT EVEN WHEN ITS QUIET",
    "NO DRAMA JUST REPS",
    "MOVE BEFORE YOU FEEL READY",
    "YOUR FUTURE NEEDS ORDER",
    "DO NOT WAIT FOR A MOOD",
    "SHOW UP WITHOUT EXPLANATION",
    "CONSISTENCY IS YOUR PROOF",
    "YOUR LIFE REFLECTS YOUR RULES",
    "YOU BECOME WHAT YOU REPEAT",
    "DISCIPLINE IS QUIET POWER",
    "NO ONE CAN SAVE YOU",
    "EXECUTION BEATS INTENT",
    "CONTROL IS RESPECT",
    "HABITS ARE YOUR IDENTITY",
    "STOP ASKING START DOING",
    "YOU EITHER LEAD OR REACT",
    "CONTROL THE MOMENT",
    "EARN YOUR CONFIDENCE",
    "DO IT AGAIN TOMORROW",
    "BE RELENTLESS IN SILENCE",
    "PROTECT YOUR ATTENTION",
    "THIS IS HOW YOU WIN",
]

# =========================
# OUTPUT FOLDER (per run)
# =========================
RUN_ID = os.getenv("GITHUB_RUN_NUMBER") or os.getenv("GITHUB_RUN_ID") or "local"
OUTDIR = os.path.join("outputs", str(RUN_ID))
os.makedirs(OUTDIR, exist_ok=True)

# =========================
# MEMORY (avoid repeats)
# =========================
MEM = "memory.json"
MEM_WINDOW = 45  # don’t repeat last ~45 used lines

def load_memory():
    if os.path.exists(MEM):
        try:
            return json.load(open(MEM, "r", encoding="utf-8"))
        except:
            return []
    return []

def save_memory(hist):
    json.dump(hist[-300:], open(MEM, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def pick_hook():
    texts = [h[0] for h in HOOKS]
    weights = [h[1] for h in HOOKS]
    return random.choices(texts, weights=weights, k=1)[0]

def pick_lines(count=4):
    used = load_memory()
    recent = set(used[-MEM_WINDOW:])

    hook = pick_hook()

    # pool excluding recent
    pool = [l for l in LINES if l not in recent and l != hook]
    if len(pool) < (count - 1):
        # reset if we’re running low
        used = []
        recent = set()
        pool = [l for l in LINES if l != hook]

    chosen = [hook] + random.sample(pool, count - 1)

    # update memory
    save_memory(used + chosen)

    return chosen

# =========================
# TEXT FRAME (safe zone + 2 line wrap)
# =========================
def wrap_to_2_lines(draw, font, text, max_w):
    words = text.split()
    lines = []
    cur = ""

    for w in words:
        test = (cur + " " + w).strip()
        box = draw.textbbox((0, 0), test, font=font)
        if (box[2] - box[0]) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)

    if len(lines) <= 2:
        return lines

    # force to 2 lines: first line stays, rest joins into second
    return [lines[0], " ".join(lines[1:])]

def frame(text):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    font = ImageFont.truetype(FONT_PATH, 120)
    max_w = int(W * 0.75)

    lines = wrap_to_2_lines(d, font, text, max_w)

    # measure total height
    heights = []
    for ln in lines:
        b = d.textbbox((0, 0), ln, font=font)
        heights.append(b[3] - b[1])

    gap = 26
    total_h = sum(heights) + gap * (len(lines) - 1)

    # center within safe zone, slightly lower
    y = SAFE_TOP + (SAFE_H - total_h) // 2 + 40

    for i, ln in enumerate(lines):
        b = d.textbbox((0, 0), ln, font=font)
        tw = b[2] - b[0]
        x = (W - tw) // 2

        # shadow
        d.text((x + 5, y + 5), ln, font=font, fill=(0, 0, 0, 200))
        # main
        d.text((x, y), ln, font=font, fill=(255, 255, 255, 255))

        y += heights[i] + gap

    return np.array(img)

# =========================
# THUMBNAIL (2-word hook + auto fit)
# =========================
def make_thumbnail(hook_text):
    words = hook_text.split()[:2]
    text = " ".join(words).upper()

    img = Image.new("RGB", (1080, 1920), (0, 0, 0))
    d = ImageDraw.Draw(img)

    size = THUMB_FONT_START
    font = ImageFont.truetype(FONT_PATH, size)

    # auto shrink until fits
    while True:
        box = d.textbbox((0, 0), text, font=font)
        w = box[2] - box[0]
        if w <= THUMB_MAX_W or size <= 90:
            break
        size -= 6
        font = ImageFont.truetype(FONT_PATH, size)

    box = d.textbbox((0, 0), text, font=font)
    tw = box[2] - box[0]
    th = box[3] - box[1]
    x = (1080 - tw) // 2
    y = (1920 - th) // 2

    # cinematic shadow
    d.text((x + 10, y + 10), text, font=font, fill=(0, 0, 0))
    d.text((x, y), text, font=font, fill=(255, 255, 255))

    img.save(os.path.join(OUTDIR, "thumbnail.jpg"))

# =========================
# CAPTION + 4 HASHTAGS + CTA
# =========================
def make_caption(chosen):
    hook = chosen[0].title()
    body = " ".join(chosen[1:3]).title()
    tags = " ".join(random.sample(HASHTAGS, 4))
    cap = f"{hook}.\n{body}.\n\n{CTA_LINE}\n\n{tags}\n"
    with open(os.path.join(OUTDIR, "caption.txt"), "w", encoding="utf-8") as f:
        f.write(cap)

# =========================
# EDGE TTS (per-line voice = perfect sync)
# =========================
def clean_tts_text(s):
    s = s.strip().upper()
    s = re.sub(r"[^A-Z0-9\s']", "", s)
    return s

async def tts_line_to_file(text, outpath):
    # Add a small pause after each line for rhythm
    # SSML helps pacing and reduces "rushed" delivery
    safe = clean_tts_text(text)
    ssml = f"""
<speak version="1.0" xml:lang="en-US">
  <voice name="{VOICE}">
    <prosody rate="{VOICE_RATE}" pitch="{VOICE_PITCH}">
      {safe}
      <break time="600ms"/>
    </prosody>
  </voice>
</speak>
""".strip()

    communicate = edge_tts.Communicate(ssml, voice=VOICE, rate=VOICE_RATE, pitch=VOICE_PITCH)
    await communicate.save(outpath)

# =========================
# AUTO DUCK MUSIC WHEN VOICE SPEAKS
# =========================
def apply_duck(music_clip, speaking_windows):
    def duck(get_frame, t):
        speaking = any((t >= s and t <= e) for (s, e) in speaking_windows)
        factor = DUCK_FACTOR if speaking else 1.0
        return get_frame(t) * factor
    return music_clip.fl(duck)

# =========================
# MAIN GENERATOR
# =========================
def make():
    if not os.path.exists(VIDEO):
        raise FileNotFoundError(f"Missing {VIDEO}. Add bg.mp4 to repo root.")

    # Start with 4 lines, auto reduce if total > 14s
    chosen = pick_lines(count=4)

    # Background video (cinematic slow zoom)
    base = VideoFileClip(VIDEO).without_audio()
    base = base.fx(resize, lambda t: 1 + 0.015 * t)
    base = base.resize(height=H)
    if base.w < W:
        base = base.resize(width=W)
    base = base.crop(x_center=base.w / 2, y_center=base.h / 2, width=W, height=H)

    # Generate per-line voice and build timeline
    while True:
        # cleanup any old temp voice files
        for fn in os.listdir("."):
            if fn.startswith("v_") and fn.endswith(".mp3"):
                try:
                    os.remove(fn)
                except:
                    pass

        clips = []
        audio_clips = []
        speaking_windows = []

        t = 0.0

        # Create TTS per line (sync)
        for i, line in enumerate(chosen):
            vf = f"v_{i}.mp3"
            asyncio.run(tts_line_to_file(line, vf))

            voice = AudioFileClip(vf)
            dur = float(voice.duration) + 0.20  # tiny gap

            img = frame(line)
            clip = (ImageClip(img)
                    .set_start(t)
                    .set_duration(dur)
                    .fadein(0.25)
                    .fadeout(0.25))

            clips.append(clip)
            audio_clips.append(voice.set_start(t))
            speaking_windows.append((t, t + float(voice.duration)))

            t += dur

        # If too long, reduce to 3 lines and rebuild
        if t > MAX_SECONDS and len(chosen) > 3:
            chosen = chosen[:3]
            continue

        # Final length (strict max 14s)
        final_len = min(t, MAX_SECONDS)

        final = CompositeVideoClip([base] + clips).subclip(0, final_len)

        # subtle film grain
        noise = np.random.randint(0, 15, (H, W, 3)).astype("uint8")
        grain = ImageClip(noise).set_duration(final_len).set_opacity(0.03)
        final = CompositeVideoClip([final, grain])

        # AUDIO MIX
        voice_mix = CompositeAudioClip(audio_clips).volumex(VOICE_GAIN)

        if os.path.exists(MUSIC):
            music = (AudioFileClip(MUSIC)
                     .volumex(MUSIC_BASE)
                     .audio_fadein(1.2)
                     .audio_fadeout(1.2)
                     .subclip(0, final_len))

            music = apply_duck(music, speaking_windows).volumex(MUSIC_FINAL)

            final_audio = CompositeAudioClip([music, voice_mix])
        else:
            # works without music
            final_audio = voice_mix

        final = final.set_audio(final_audio)

        # exports
        make_thumbnail(chosen[0])     # 2-word hook from hook line
        make_caption(chosen)

        out_video = os.path.join(OUTDIR, "reel.mp4")
        final.write_videofile(out_video, fps=30, audio_codec="aac")

        break

if __name__ == "__main__":
    make()
