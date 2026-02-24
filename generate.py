import os, random, glob, asyncio, json
import numpy as np
from moviepy.editor import *
from moviepy.video.fx import all as vfx
from moviepy.audio.fx import all as afx
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ---------------- SETTINGS ----------------

W, H = 1080, 1920
FPS = 30
MAX_REEL_LENGTH = 11.8

VOICE = "en-US-GuyNeural"
RATE = "-38%"
PITCH = "-45Hz"
VOLUME = "+0%"

FONT_PATH = "Anton-Regular.ttf"
REELS_PER_RUN = 5

os.makedirs("outputs", exist_ok=True)

# ---------------- MEMORY ----------------

HOOK_MEMORY_FILE = "hook_memory.json"
CATEGORY_MEMORY_FILE = "category_memory.json"

if os.path.exists(HOOK_MEMORY_FILE):
    used_hooks = json.load(open(HOOK_MEMORY_FILE))
else:
    used_hooks = []

if os.path.exists(CATEGORY_MEMORY_FILE):
    last_category = json.load(open(CATEGORY_MEMORY_FILE))
else:
    last_category = None

# ---------------- CONTENT ----------------

HOOKS = {
    "accusation": [
        "You don’t lack potential. You lack discipline.",
        "You are comfortable. That is the problem.",
        "You keep choosing easy.",
        "You break promises quietly.",
        "You tolerate your own weakness.",
        "You say you want more. But act average.",
        "You’re not stuck. You’re undisciplined.",
        "You know what to fix. You don’t fix it."
    ],

    "authority": [
        "Discipline separates you.",
        "Control is earned daily.",
        "Standards define outcomes.",
        "Structure builds identity.",
        "Execution reveals character.",
        "Restraint creates power.",
        "Routine creates dominance.",
        "Focus is self respect."
    ],

    "paradox": [
        "Comfort feels safe. It makes you weak.",
        "Relief now. Regret later.",
        "Avoid pressure. Stay average.",
        "Soft habits create hard lives.",
        "Easy days build fragile minds.",
        "No structure. No progress.",
        "Motivation fades. Discipline remains.",
        "Silence grows weakness."
    ],

    "consequence": [
        "Every delay compounds.",
        "Small lapses become identity.",
        "Weak habits stack quietly.",
        "Inconsistency erases momentum.",
        "Comfort slowly owns you.",
        "Distraction drains power.",
        "Excuses shape your future.",
        "Avoidance builds regret."
    ],

    "identity": [
        "Who are you becoming?",
        "This is your pattern.",
        "This is your standard.",
        "This is your identity.",
        "This is your ceiling.",
        "This is your limit.",
        "This is the truth.",
        "This is the line."
    ]
}

TRUTHS = [
    "That is why nothing changes.",
    "That is why progress feels slow.",
    "That is the real cost.",
    "That is the pattern repeating.",
    "That is the hidden weakness.",
    "That is what separates you.",
    "That is what exposes you.",
    "That is why you stay average.",
    "That is the decision you make daily.",
    "That is the identity you build."
]

QUESTIONS = [
    "Still choosing comfort?",
    "Still negotiating?",
    "Still undisciplined?",
    "Still soft?",
    "Still delaying?",
    "Still escaping effort?",
    "Still blaming circumstances?",
    "Still waiting for motivation?",
    "Still breaking promises?",
    "Or done?"
]

CTAS = [
    "Comment discipline.",
    "Type DISCIPLINE.",
    "Prove it. Comment discipline.",
    "Choose discipline.",
    "Decide now.",
    "Lock in.",
    "No weak comments.",
    "Stand up in the comments.",
    "Commit publicly.",
    "Separate yourself."
]

# ---------------- TEXT ENGINE ----------------

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

# ---------------- SCRIPT BUILDER ----------------

def get_next_category():
    global last_category
    categories = list(HOOKS.keys())
    if last_category in categories:
        categories.remove(last_category)
    category = random.choice(categories)
    last_category = category
    return category

def build_script():
    category = get_next_category()
    hook = random.choice(HOOKS[category])
    truth = random.choice(TRUTHS)
    question = random.choice(QUESTIONS)
    cta = random.choice(CTAS)
    return [hook, truth, question, cta]

# ---------------- REEL ENGINE ----------------

def make_reel(index):

    script = build_script()

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

    base = base.fx(vfx.colorx, 1.05)
    base = base.fx(vfx.resize, lambda t: 1 + 0.02*t)

    clips = []
    audio_clips = []

    timeline = 0.25

    for i, line in enumerate(script):

        voice_file = f"voice_{index}_{i}.mp3"
        generate_voice(line, voice_file)

        audio = AudioFileClip(voice_file)
        voice_duration = audio.duration

        if i == 0:
            duration = voice_duration + 0.6
        elif i == 1:
            duration = voice_duration + 0.5
        elif i == 2:
            duration = voice_duration + 0.6
        else:
            duration = voice_duration + 0.5

        text_img = make_text(line)

        text_clip = (
            ImageClip(text_img)
            .set_start(timeline)
            .set_duration(duration)
            .fadein(0.15)
            .fadeout(0.2)
        )

        clips.append(text_clip)
        audio_clips.append(audio.set_start(timeline))

        timeline += duration

    if timeline > MAX_REEL_LENGTH:
        timeline = MAX_REEL_LENGTH

    final_video = CompositeVideoClip([base] + clips)
    final_video = final_video.set_duration(timeline)
    final_video = final_video.fadeout(0.25)

    final_voice = CompositeAudioClip(audio_clips).subclip(0, timeline)

    if os.path.exists("music.mp3"):
        music = AudioFileClip("music.mp3")
        music = afx.audio_loop(music, duration=timeline)
        music = music.audio_fadein(0.8)
        music = music.volumex(0.14)
        final_audio = CompositeAudioClip([music, final_voice.volumex(1.12)])
    else:
        final_audio = final_voice

    final = final_video.set_audio(final_audio)

    video_path = f"outputs/reel_{index+1}.mp4"

    final.write_videofile(
        video_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        threads=4
    )

    title = f"{script[0]} | INNER DISCIPLINE"

    caption = "\n".join([
        script[0], "", script[1], "", script[2], "", script[3], "",
        "#discipline #selfcontrol #focus #consistency #mindset #innerdiscipline"
    ])

    with open(f"outputs/reel_{index+1}_title.txt", "w") as f:
        f.write(title)

    with open(f"outputs/reel_{index+1}_caption.txt", "w") as f:
        f.write(caption)

# ---------------- RUN ----------------

for i in range(REELS_PER_RUN):
    make_reel(i)

json.dump(used_hooks, open(HOOK_MEMORY_FILE, "w"))
json.dump(last_category, open(CATEGORY_MEMORY_FILE, "w"))

print("🔥 INNER DISCIPLINE RETENTION MODE ACTIVE")
