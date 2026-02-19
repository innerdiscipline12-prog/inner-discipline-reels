import os, random, glob, asyncio, json
import numpy as np
from moviepy.editor import *
from moviepy.video.fx.all import resize
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ---------------- SETTINGS ----------------

W, H = 1080, 1920
FPS = 30
MAX_REEL_LENGTH = 9.5

VOICE = "en-US-GuyNeural"
RATE = "-35%"
PITCH = "-40Hz"
VOLUME = "+0%"

FONT_PATH = "Anton-Regular.ttf"
REELS_PER_RUN = 5

os.makedirs("outputs", exist_ok=True)

# ---------------- MEMORY ----------------

HOOK_MEMORY_FILE = "hook_memory.json"
if os.path.exists(HOOK_MEMORY_FILE):
    used_hooks = json.load(open(HOOK_MEMORY_FILE))
else:
    used_hooks = []

# ---------------- CONTENT ----------------

HOOKS = [
"You already know your problem.",
"Your comfort is expensive.",
"You’re training weakness.",
"Your habits are voting.",
"You’re avoiding your potential.",
"You want easy results.",
"You’re loyal to comfort.",
"Your future sees this.",
"You’re feeding distraction.",
"You protect bad habits.",
"You’re choosing delay.",
"You’re practicing excuses.",
"You’re building regret.",
"You fear structure.",
"You escape effort.",
"You waste focus.",
"You avoid discipline.",
"You chase comfort.",
"You repeat mistakes.",
"You know better.",
]

TRUTHS=[
"Discipline is trained.",
"Control is built.",
"Focus is earned.",
"Consistency wins quietly.",
"Structure creates freedom.",
"Habits decide outcomes.",
"Effort compounds daily.",
"Standards shape life.",
"Repetition builds power.",
"Order beats chaos.",
"Action removes doubt.",
"Execution builds identity.",
"Self-control scales success.",
"Routine builds strength.",
"Momentum grows slowly.",
"Pressure creates discipline.",
"Control beats emotion.",
"Clarity follows action.",
"Rules protect focus.",
"Discipline builds respect.",
]

QUESTIONS=[
"Still comfortable?",
"Still delaying?",
"Still distracted?",
"Still escaping?",
"Still negotiating?",
"Still waiting?",
"Still unfocused?",
"Still inconsistent?",
"Still choosing easy?",
"Still scrolling?",
"Still weak on standards?",
"Still blaming mood?",
"Still avoiding?",
"Still restarting?",
"Still here?",
]

CTAS=[
"Comment discipline.",
"Type discipline.",
"Only disciplined comment.",
"Discipline or regret.",
"Choose discipline.",
"Prove discipline. Comment.",
"Serious? Comment discipline.",
"Standards start now. Comment.",
"Commit now. Comment discipline.",
"Earn it. Comment discipline.",
]

# ---------------- TEXT ----------------

def make_text(text):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_size = 92
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

    total_height = len(lines) * (font_size + 22)
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
        y += font_size + 22

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

# ---------------- SCRIPT ----------------

def get_hook():
    global used_hooks
    available = [h for h in HOOKS if h not in used_hooks]

    if not available:
        used_hooks = []
        available = HOOKS.copy()

    hook = random.choice(available)
    used_hooks.append(hook)
    return hook

def build_script(with_cta=True):
    hook = get_hook()
    script = [hook, random.choice(TRUTHS)]
    script.append(random.choice(CTAS if with_cta else QUESTIONS))
    return script

# ---------------- REEL ----------------

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
        voice_duration = audio.duration

        if line.endswith("?"):
            duration = voice_duration + 1.0
        elif line in CTAS:
            duration = voice_duration + 1.2
        else:
            duration = voice_duration + 0.6

        text_img = make_text(line)

        text_clip = (
            ImageClip(text_img)
            .set_start(timeline)
            .set_duration(duration)
            .fadein(0.25)
            .fadeout(0.25)
        )

        clips.append(text_clip)
        audio_clips.append(audio.set_start(timeline + 0.1))

        timeline += duration

    timeline = min(timeline, MAX_REEL_LENGTH)

    final_video = CompositeVideoClip([base] + clips)
    final_video = final_video.set_duration(timeline)  # 🔥 FIX
    final_video = final_video.fadeout(0.3)

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

    # --------- MONETIZATION ENGINE ---------

title = f"{script[0]} | INNER DISCIPLINE"

caption_lines = []
caption_lines.append(script[0])
caption_lines.append("")
caption_lines.append(script[1])
caption_lines.append("")
caption_lines.append("Discipline builds identity.")
caption_lines.append("")
caption_lines.append("#discipline #selfcontrol #focus #consistency #mindset #innerdiscipline")

caption = "\n".join(caption_lines)

with open(f"outputs/reel_{index+1}_title.txt", "w") as f:
    f.write(title)

with open(f"outputs/reel_{index+1}_caption.txt", "w") as f:
    f.write(caption)

# ---------------- RUN ----------------

for i in range(REELS_PER_RUN):
    make_reel(i, with_cta=(i < 2))

json.dump(used_hooks, open(HOOK_MEMORY_FILE, "w"))

print("🔥 REEL ELITE ENGINE FIXED")
