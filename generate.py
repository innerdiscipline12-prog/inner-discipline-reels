import os, json, random, asyncio, glob
import numpy as np
from moviepy.editor import *
from moviepy.video.fx.all import resize
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ================= SETTINGS =================

REEL_BACKGROUNDS = glob.glob("bg*.mp4")
LONG_BACKGROUNDS = glob.glob("bg_long*.mp4")

if not REEL_BACKGROUNDS:
    raise Exception("No reel backgrounds found (bg*.mp4)")
if not LONG_BACKGROUNDS:
    raise Exception("No long backgrounds found (bg_long*.mp4)")

MUSIC = "music.mp3"
FONT_PATH = "Anton-Regular.ttf"

W, H = 1080, 1920
LW, LH = 1280, 720

REELS_PER_RUN = 5

VOICE = "en-US-ChristopherNeural"
VOICE_RATE = "-35%"
VOICE_PITCH = "-20Hz"

HASHTAGS = [
    "#discipline", "#selfcontrol", "#focus",
    "#mindset", "#innerdiscipline",
    "#consistency", "#stoic", "#growth"
]

# ================= LINES =================
HOOK = [
    "You're not tired. You're undisciplined.",
    "Comfort is ruining your future.",
    "Your habits expose you.",
    "You don't lack time. You lack control.",
    "No one is coming to save you.",
    "You are negotiating with weakness.",
    "Your comfort is costing you years."
]
AUTHORITY = [
    "Comfort is expensive.",
    "Discipline decides outcomes.",
    "Weak habits create hard lives.",
    "Control beats motivation."
]
RELATABLE = [
    "Some days you don't feel like it.",
    "You get distracted easily.",
    "You delay what matters.",
    "You know what to do."
]
CHALLENGE = [
    "Day 7. Still disciplined?",
    "Can you stay consistent?",
    "Will you finish what you start?",
    "Still here?"
]

ALL_LINES = HOOK + AUTHORITY + RELATABLE + CHALLENGE

# ================= MEMORY =================

MEM = "memory.json"
used = json.load(open(MEM)) if os.path.exists(MEM) else []

# ================= VOICE =================

async def make_voice(text, path):
    tts = edge_tts.Communicate(
        text,
        voice=VOICE,
        rate=VOICE_RATE,
        pitch=VOICE_PITCH
    )
    await tts.save(path)

def run_tts(text, path):
    # Safe wrapper for GitHub Actions / normal Python runs
    asyncio.run(make_voice(text, path))

# ================= TEXT HELPERS =================

def smart_split(text, max_words_single=3):
    words = text.split()
    if len(words) > max_words_single:
        mid = len(words) // 2
        return " ".join(words[:mid]) + "\n" + " ".join(words[mid:])
    return text

# ================= TEXT FRAME =================

def frame(text, w=W, h=H, size=120):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    text = smart_split(text, max_words_single=3)

    font = ImageFont.truetype(FONT_PATH, size)

    box = d.multiline_textbbox((0, 0), text, font=font, spacing=20)
    x = (w - (box[2] - box[0])) // 2
    y = (h - (box[3] - box[1])) // 2

    d.multiline_text((x + 6, y + 6), text, font=font, fill=(0, 0, 0, 180), align="center", spacing=20)
    d.multiline_text((x, y), text, font=font, fill="white", align="center", spacing=20)

    return np.array(img)

# ================= THUMBNAIL =================

def make_thumbnail(text, path):
    img = Image.new("RGB", (1080, 1920), (0, 0, 0))
    d = ImageDraw.Draw(img)

    text = smart_split(text, max_words_single=2)
    font = ImageFont.truetype(FONT_PATH, 170)

    box = d.multiline_textbbox((0, 0), text, font=font, spacing=30)
    x = (1080 - (box[2] - box[0])) // 2
    y = (1920 - (box[3] - box[1])) // 2

    d.multiline_text((x, y), text, font=font, fill="white", align="center", spacing=30)
    img.save(path)

# ================= CAPTION =================

def make_caption(lines, path):
    cap = " • ".join(lines[:2]).title()
    tags = " ".join(random.sample(HASHTAGS, 4))
    open(path, "w").write(cap + "\n\n" + tags)

# ================= MEMORY-SAFE PICK =================

def pick_unique(pool):
    """
    Pick a line from pool that isn't in memory yet.
    If pool is exhausted, reset memory for only that pool's items.
    """
    global used
    pool = list(pool)

    available = [x for x in pool if x not in used]
    if not available:
        # reset only this pool's items from used
        used = [u for u in used if u not in pool]
        available = pool[:]

    choice = random.choice(available)
    used.append(choice)
    return choice

# ================= PICK LINES =================

def pick_lines():
    # Micro-arc: Hook -> Relatable -> Authority -> Extra punch -> Challenge
    hook = pick_unique(HOOK)
    relatable = pick_unique(RELATABLE)
    authority = pick_unique(AUTHORITY)

    # Extra punch can be from any category but should avoid repeating above
    extra_pool = [x for x in ALL_LINES if x not in {hook, relatable, authority}]
    extra = pick_unique(extra_pool) if extra_pool else pick_unique(ALL_LINES)

    challenge = pick_unique(CHALLENGE)

    return [hook, relatable, authority, extra, challenge]

# ================= BUILD REEL =================

def make_reel(idx):
    folder = f"outputs/{idx:02d}"
    os.makedirs(folder, exist_ok=True)

    chosen = pick_lines()

    # Pick a DIFFERENT background per reel
    VIDEO = random.choice(REEL_BACKGROUNDS)

    base = VideoFileClip(VIDEO).without_audio()
    base = base.fx(resize, lambda t: 1 + 0.008 * t).resize(height=H)

    if base.w < W:
        base = base.resize(width=W)

    base = base.crop(x_center=base.w / 2, y_center=base.h / 2, width=W, height=H)

    clips = []
    audio = []
    t = 0

    for i, line in enumerate(chosen):
        vp = f"{folder}/line{i}.mp3"
        run_tts(line, vp)

        a = AudioFileClip(vp)
        dur = a.duration + 0.4

        img = frame(line, W, H, 120)

        txt = (
            ImageClip(img)
            .set_start(t)
            .set_duration(dur)
            .fadein(0.3)
            .fadeout(0.3)
        )

        clips.append(txt)
        audio.append(a.set_start(t + 0.25))
        t += dur

    final = CompositeVideoClip([base] + clips).subclip(0, t)
    voice_mix = CompositeAudioClip(audio)

    if os.path.exists(MUSIC):
        music = AudioFileClip(MUSIC).audio_loop(duration=t).volumex(0.1).audio_fadeout(1.0)
        final = final.set_audio(CompositeAudioClip([music, voice_mix]))
    else:
        final = final.set_audio(voice_mix)

    final.write_videofile(f"{folder}/reel.mp4", fps=30)

    make_thumbnail(chosen[0], f"{folder}/thumbnail.jpg")
    make_caption(chosen, f"{folder}/caption.txt")

# ================= SMART FLOW LONG VIDEO =================

def make_long_video():
    print("🔥 Generating SMART FLOW 10-minute video...")

    os.makedirs("outputs", exist_ok=True)

    target_len = 600
    timestamps = []

    # Pick a DIFFERENT background per long video
    LONG_VIDEO = random.choice(LONG_BACKGROUNDS)

    base = VideoFileClip(LONG_VIDEO).without_audio()
    base = base.fx(vfx.loop, duration=target_len)
    base = base.fx(resize, lambda t: 1 + 0.002 * t).resize(height=LH)

    if base.w < LW:
        base = base.resize(width=LW)

    base = base.crop(x_center=base.w / 2, y_center=base.h / 2, width=LW, height=LH)

    # Prevent repeats: shuffle pool and consume
    lines_pool = ALL_LINES.copy()
    random.shuffle(lines_pool)

    clips = []
    audio = []
    t = 0
    idx = 0

    while t < target_len:
        if not lines_pool:
            lines_pool = ALL_LINES.copy()
            random.shuffle(lines_pool)

        line = lines_pool.pop()

        vp = f"outputs/long_{idx}.mp3"
        run_tts(line, vp)

        a = AudioFileClip(vp)
        dur = max(6, a.duration + 1.2)

        timestamps.append(f"{int(t//60)}:{int(t%60):02d} {line.title()}")

        img = frame(line, LW, LH, 90)

        txt = (
            ImageClip(img)
            .set_start(t)
            .set_duration(dur)
            .fadein(0.8)
            .fadeout(0.8)
        )

        clips.append(txt)
        audio.append(a.set_start(t + 0.4))

        t += dur
        idx += 1

    final = CompositeVideoClip([base] + clips).subclip(0, target_len)
    voice_mix = CompositeAudioClip(audio)

    if os.path.exists(MUSIC):
        music = AudioFileClip(MUSIC).audio_loop(duration=target_len).volumex(0.05).audio_fadeout(3.0)
        final = final.set_audio(CompositeAudioClip([music, voice_mix]))
    else:
        final = final.set_audio(voice_mix)

    final.write_videofile("outputs/long_video.mp4", fps=30)

    title = "10 Minutes to Build Discipline"
    open("outputs/long_title.txt", "w").write(title)

    desc = f"""
Build discipline, self-control and focus.

CHAPTERS:
{chr(10).join(timestamps)}

#discipline #focus #mindset
"""
    open("outputs/long_description.txt", "w").write(desc)

    thumb = Image.new("RGB", (1280, 720), (0, 0, 0))
    d = ImageDraw.Draw(thumb)
    font = ImageFont.truetype(FONT_PATH, 120)

    text = "DISCIPLINE\nBUILDS YOU"
    box = d.multiline_textbbox((0, 0), text, font=font, spacing=20)

    x = (1280 - (box[2] - box[0])) // 2
    y = (720 - (box[3] - box[1])) // 2

    d.multiline_text((x, y), text, font=font, fill="white", align="center", spacing=20)
    thumb.save("outputs/long_thumbnail.jpg")

    print("✅ LONG VIDEO COMPLETE")

# ================= RUN =================

os.makedirs("outputs", exist_ok=True)

for i in range(1, REELS_PER_RUN + 1):
    make_reel(i)

make_long_video()

json.dump(used, open(MEM, "w"))

print("🔥 MASTER V10.5 COMPLETE")
