import os, random, glob, asyncio, json
import numpy as np
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ---------------- SETTINGS ----------------

W, H = 1080, 1920
FPS = 30

VOICE = "en-US-ChristopherNeural"
RATE = "-20%"
PITCH = "-25Hz"
VOLUME = "+0%"

FONT_PATH = "Anton-Regular.ttf"

REELS_PER_RUN = 5

os.makedirs("outputs", exist_ok=True)

# ---------------- MONETIZATION MEMORY ----------------

HOOK_MEMORY_FILE = "hook_memory.json"
if os.path.exists(HOOK_MEMORY_FILE):
    used_hooks = json.load(open(HOOK_MEMORY_FILE))
else:
    used_hooks = []

# ---------------- CONTENT BANK ----------------

HOOKS = [
"You’re not tired. You’re avoiding effort.",
"Your comfort is lying to you.",
"Nobody ruined your life. You did.",
"You know the answer. You avoid it.",
"Your future is watching you waste time.",
"Comfort is killing your potential.",
"You don’t need motivation. You need rules.",
"You’re not busy. You’re distracted.",
"Your excuses are well practiced.",
"Most people choose easy. Daily.",
]

TRUTHS = [
"Discipline is a decision.",
"Control creates freedom.",
"Structure beats emotion.",
"Action builds clarity.",
"Habits shape identity.",
"Consistency builds power.",
"Standards define outcomes.",
"Focus is trained.",
"Execution builds confidence.",
"Routine creates results.",
]

QUESTIONS = [
"Still choosing easy?",
"Still delaying?",
"Still distracted?",
"Still comfortable?",
"Still negotiating?",
"Still here?",
]

CTAS = [
"Comment discipline.",
"Type discipline.",
"Discipline or regret. Choose.",
"Prove discipline. Comment.",
"Standards begin now. Comment discipline.",
]

# ---------------- TEXT RENDER ----------------

def make_text(text):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_size = 95
    font = ImageFont.truetype(FONT_PATH, font_size)

    max_width = W - 240
    lines = []
    words = text.split()
    current = ""

    for word in words:
        test = (current + " " + word).strip()
        if draw.textlength(test, font=font) <= max_width:
            current = test
        else:
            lines.append(current)
            current = word
    lines.append(current)

    total_height = len(lines) * (font_size + 15)
    y = (H - total_height) // 2

    for line in lines:
        text_width = draw.textlength(line, font=font)
        x = (W - text_width) // 2

        draw.text(
            (x, y),
            line,
            font=font,
            fill="white",
            stroke_width=5,
            stroke_fill="black"
        )
        y += font_size + 15

    return np.array(img)

# ---------------- TTS ----------------

async def tts_async(text, filename):
    communicate = edge_tts.Communicate(
        text,
        VOICE,
        rate=RATE,
        pitch=PITCH,
        volume=VOLUME
    )
    await communicate.save(filename)

def generate_voice(text, filename):
    asyncio.run(tts_async(text, filename))

# ---------------- HOOK ROTATION ----------------

def get_hook():
    global used_hooks
    available = [h for h in HOOKS if h not in used_hooks]

    if not available:
        used_hooks = []
        available = HOOKS.copy()

    hook = random.choice(available)
    used_hooks.append(hook)

    return hook

# ---------------- SCRIPT BUILDER ----------------

def build_script(with_cta=True):
    hook = get_hook()

    script = [
        hook,
        random.choice(TRUTHS),
        random.choice(TRUTHS),
    ]

    if with_cta:
        script.append(random.choice(CTAS))
    else:
        script.append(random.choice(QUESTIONS))

    return script

# ---------------- SEO ENGINE ----------------

def generate_title(hook):
    return f"{hook} | INNER DISCIPLINE"

def generate_caption(script):
    caption = script[0] + "\n\n"
    caption += "Discipline builds identity.\n\n"
    caption += "#discipline #selfcontrol #focus #mindset"
    return caption

# ---------------- REEL BUILDER ----------------

def make_reel(index, with_cta):

    script = build_script(with_cta)

    backgrounds = glob.glob("bg*.mp4")
    if not backgrounds:
        raise Exception("No bg*.mp4 found.")

    bg_path = random.choice(backgrounds)
    base = VideoFileClip(bg_path).without_audio()

    base = base.resize(height=H)

    if base.w < W:
        base = base.resize(width=W)

    base = base.crop(
        x_center=base.w/2,
        y_center=base.h/2,
        width=W,
        height=H
    )

    clips = []
    audio_clips = []
    timeline = 0

    for i, line in enumerate(script):

        voice_file = f"voice_{index}_{i}.mp3"
        generate_voice(line, voice_file)

        audio = AudioFileClip(voice_file)

        if i == 0:
            duration = 2.4
        elif i == len(script) - 1:
            duration = 2.4
        else:
            duration = 2.1

        text_img = make_text(line)

        text_clip = (
            ImageClip(text_img)
            .set_start(timeline)
            .set_duration(duration)
            .fadein(0.25)
            .fadeout(0.25)
        )

        clips.append(text_clip)
        audio_clips.append(audio.set_start(timeline + 0.15))

        timeline += duration

    final_video = CompositeVideoClip([base] + clips).set_duration(timeline)
    final_audio = CompositeAudioClip(audio_clips)

    final = final_video.set_audio(final_audio)

    video_path = f"outputs/reel_{index+1}.mp4"

    final.write_videofile(
        video_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        threads=4
    )

    # --- Save Monetization Assets ---

    title = generate_title(script[0])
    caption = generate_caption(script)

    open(f"outputs/reel_{index+1}_title.txt", "w").write(title)
    open(f"outputs/reel_{index+1}_caption.txt", "w").write(caption)

# ---------------- RUN ----------------

for i in range(REELS_PER_RUN):
    make_reel(i, with_cta=(i < 2))

json.dump(used_hooks, open(HOOK_MEMORY_FILE, "w"))

print("🔥 V13 MONETIZATION ENGINE COMPLETE")
