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
REELS_PER_RUN = 3  # ✅ switched to 3 reels per run (one psychological set)

os.makedirs("outputs", exist_ok=True)

# ---------------- MEMORY ----------------

HOOK_MEMORY_FILE = "hook_memory.json"
CATEGORY_MEMORY_FILE = "category_memory.json"
SET_STEP_FILE = "set_step.json"

if os.path.exists(HOOK_MEMORY_FILE):
    used_hooks = json.load(open(HOOK_MEMORY_FILE))
else:
    used_hooks = []

if os.path.exists(CATEGORY_MEMORY_FILE):
    last_category = json.load(open(CATEGORY_MEMORY_FILE))
else:
    last_category = None

if os.path.exists(SET_STEP_FILE):
    set_step = json.load(open(SET_STEP_FILE))
    if not isinstance(set_step, int):
        set_step = 0
else:
    set_step = 0

# ---------------- CONTENT (UPGRADED PSYCHOLOGICAL SYSTEM) ----------------

HOOKS = {
    "identity": [
        "You became someone you don’t respect.",
        "You don’t trust yourself anymore.",
        "You hear yourself… and ignore it.",
        "You know better. You don’t do better.",
        "You lost control of yourself.",
        "You keep proving you’re unreliable.",
        "You don’t follow your own standards.",
        "You’ve lowered the bar too many times.",
        "You stopped taking yourself seriously.",
        "You’re watching yourself fall off.",
        "You don’t even resist anymore.",
        "You gave up quietly.",
        "You broke your own identity.",
        "You’re not who you said you’d be.",
        "You’ve normalized disappointment.",
        "You’re okay with less now.",
        "You let yourself slip again.",
        "You don’t even fight it anymore.",
        "You’re becoming predictable.",
        "You made weakness routine."
    ],

    "comfort": [
        "You chose easy again.",
        "That felt good… didn’t it?",
        "You took the softer option.",
        "You avoided the hard part.",
        "You stopped where it got uncomfortable.",
        "You stayed where it’s safe.",
        "You picked relief over growth.",
        "You gave in early.",
        "You protected comfort again.",
        "You escaped right on time.",
        "You didn’t push through.",
        "You folded under pressure.",
        "You let comfort decide.",
        "You stayed weak on purpose.",
        "You quit before it counted.",
        "You avoided the real work.",
        "You took the shortcut again.",
        "You chose now over later.",
        "You kept it easy.",
        "You didn’t go far enough."
    ],

    "time": [
        "You lost another day.",
        "That day is gone now.",
        "You’ll never get that back.",
        "You wasted it again.",
        "It’s happening again.",
        "Same day. Same pattern.",
        "You’re running out quietly.",
        "Time moved. You didn’t.",
        "Another delay added.",
        "You stayed stuck again.",
        "You let the day slip.",
        "Nothing changed today.",
        "You paused your life again.",
        "That was your chance.",
        "You missed it again.",
        "The gap is growing.",
        "You’re falling behind slowly.",
        "You’re still where you were.",
        "Time kept going without you.",
        "You did nothing again."
    ]
}

TRUTHS = [
    "That’s who you are right now.",
    "That’s your real standard.",
    "That’s what you accept.",
    "That’s your level.",
    "That’s your pattern showing.",
    "That’s why you don’t move forward.",
    "That’s the version you feed.",
    "That’s what’s holding you down.",
    "That’s your daily decision.",
    "That’s your comfort zone winning.",
    "That’s your real discipline.",
    "That’s your limit right now.",
    "That’s your truth, not your excuse.",
    "That’s what you repeat.",
    "That’s your default setting."
]

QUESTIONS = [
    "Still doing this?",
    "Still okay with that?",
    "Still choosing that version?",
    "Still letting it slide?",
    "Still pretending it’s fine?",
    "Still avoiding it?",
    "Still stopping early?",
    "Still playing safe?",
    "Still lying to yourself?",
    "Still comfortable with that?",
    "Still not changing?",
    "Still repeating it?",
    "Still weak here?",
    "Still the same?",
    "Or are you done?"
]

CTAS = [
    "Prove it. Comment DISCIPLINE.",
    "Type DISCIPLINE if you’re done.",
    "Don’t scroll. Commit.",
    "Say it publicly. DISCIPLINE.",
    "Lock in or leave.",
    "Decide right now.",
    "This is where it changes.",
    "Show me, don’t think.",
    "No excuses. Type DISCIPLINE.",
    "Stand on it. Comment DISCIPLINE.",
    "If you mean it—prove it.",
    "Choose your side.",
    "Stay soft or speak up.",
    "Draw the line here.",
    "This is your moment."
]

# ---------------- USAGE ----------------
# Pick 1 HOOK + 1 TRUTH + 1 QUESTION + 1 CTA
# Stack them in that order for maximum psychological impact.

# Example:
# You stopped where it got uncomfortable.
# That’s your real standard.
# Still okay with that?
# Prove it. Comment DISCIPLINE.

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

# ---------------- SCRIPT BUILDER (SET OF 3 LOOP) ----------------

SET_ORDER = ["identity", "comfort", "time"]

def get_set_category():
    global set_step
    cat = SET_ORDER[set_step % len(SET_ORDER)]
    set_step += 1
    return cat

def get_hook_from_category(category):
    global used_hooks
    pool = HOOKS.get(category, [])
    if not pool:
        pool = sum(HOOKS.values(), [])

    available = [h for h in pool if h not in used_hooks]
    if not available:
        used_hooks = []
        available = pool.copy()

    hook = random.choice(available)
    used_hooks.append(hook)
    return hook

def build_script():
    category = get_set_category()
    hook = get_hook_from_category(category)
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
        x_center=base.w / 2,
        y_center=base.h / 2,
        width=W,
        height=H
    )

    base = base.fx(vfx.colorx, 1.05)
    base = base.fx(vfx.resize, lambda t: 1 + 0.02 * t)

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
        script[0], "",
        script[1], "",
        script[2], "",
        script[3], "",
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
json.dump(set_step, open(SET_STEP_FILE, "w"))

print("🔥 INNER DISCIPLINE SET-OF-3 MODE ACTIVE")
