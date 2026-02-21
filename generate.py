import os, random, glob, asyncio, json
import numpy as np
from moviepy.editor import *
from moviepy.video.fx.all import resize
from moviepy.audio.fx import all as afx
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ---------------- SETTINGS ----------------

W, H = 1080, 1920
FPS = 30
MAX_REEL_LENGTH = 14.5   # upgraded for 4-step structure

VOICE = "en-US-GuyNeural"
RATE = "-40%"
PITCH = "-45Hz"
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
"You are not tired. You are undisciplined.",
"Comfort is killing your potential.",
"No one is coming.",
"You are the reason.",
"Weakness feels like relief.",
"Your standards are low.",
"Discipline isn’t your problem. Comfort is.",
"You don’t lack time. You lack control.",
"You’re negotiating with weakness.",
"You’re addicted to easy.",
"Your excuses are polished.",
"You fear structure.",
"You’re choosing distraction.",
"You’re leaking focus.",
"Comfort owns you.",
"You say soon. You mean never.",
"You’re rehearsing failure.",
"You crave results. Avoid process.",
"You’re soft where it matters.",
"You break promises to yourself.",
"You don’t need motivation.",
"You need restraint.",
"You want change without pressure.",
"You’re escaping effort.",
"Weak habits feel normal now.",
"You’re loyal to comfort.",
"You quit silently.",
"You hide behind busy.",
"You know exactly what to fix.",
"And you’re still not fixing it."
]

TRUTHS = [
"Discipline is identity.",
"Control is trained daily.",
"Weakness grows in silence.",
"Comfort compounds regret.",
"Structure removes chaos.",
"Focus is self respect.",
"Standards expose character.",
"Excuses protect ego.",
"Effort rewires the mind.",
"Repetition builds power.",
"Routine kills weakness.",
"Restraint builds dominance.",
"Consistency creates separation.",
"Small lapses become patterns.",
"Discomfort purifies.",
"Control is a decision.",
"Discipline is private.",
"Strength is built quietly.",
"Execution reveals truth.",
"Structure creates power.",
"Focus is warfare.",
"Your habits confess daily.",
"Comfort is expensive.",
"Weakness negotiates.",
"Discipline decides outcomes.",
"Identity follows action.",
"Standards filter everything.",
"Pressure creates clarity.",
"Routine creates dominance.",
"Control is chosen."
]

QUESTIONS = [
"Still negotiating?",
"Still soft?",
"Still comfortable?",
"Still distracted?",
"Still escaping?",
"Still delaying?",
"Still blaming?",
"Still scrolling?",
"Still talking?",
"Still planning?",
"Still starting Monday?",
"Still making excuses?",
"Still doubting?",
"Still quitting early?",
"Still inconsistent?",
"Still hiding?",
"Still waiting?",
"Still unfocused?",
"Still average?",
"Still undisciplined?",
"Still weak under pressure?",
"Still choosing easy?",
"Still breaking promises?",
"Still tolerating less?",
"Still wasting time?",
"Still leaking energy?",
"Still avoiding effort?",
"Still fragile?",
"Still playing small?",
"Or done?"
]

CTAS = [
"Comment discipline.",
"Type DISCIPLINE.",
"Only disciplined comment.",
"Choose discipline.",
"Commit now.",
"Say I commit.",
"Earn it. Comment discipline.",
"Prove it.",
"Stand up in the comments.",
"No excuses. Comment discipline.",
"Claim control.",
"Show up.",
"Separate yourself.",
"Decide publicly.",
"Enter the disciplined.",
"No weak comments.",
"Discipline only.",
"Declare it.",
"Choose strength.",
"Join the disciplined.",
"Say less. Execute more.",
"If you are serious comment.",
"Identity check.",
"Commitment check.",
"Decide here.",
"Lock in.",
"This is your line.",
"Cross it.",
"Earn your standard.",
"Discipline or comfort?"
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

# ---------------- SCRIPT BUILDER (UPGRADED FORMULA) ----------------

def get_hook():
    global used_hooks
    available = [h for h in HOOKS if h not in used_hooks]
    if not available:
        used_hooks = []
        available = HOOKS.copy()
    hook = random.choice(available)
    used_hooks.append(hook)
    return hook

def build_script():
    hook = get_hook()
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

    # Cinematic zoom ramp
    base = base.fx(vfx.resize, lambda t: 1 + 0.015*t)

    clips = []
    audio_clips = []

    timeline = 0.9  # elite dramatic silence before hook

    for i, line in enumerate(script):

        voice_file = f"voice_{index}_{i}.mp3"
        generate_voice(line, voice_file)

        audio = AudioFileClip(voice_file)
        voice_duration = audio.duration

        if i == 0:  # Hook emphasis
            audio = audio.volumex(1.25)
            duration = voice_duration + 0.9

        elif line.endswith("?"):  # Question tension hold
            audio = audio.volumex(1.1)
            duration = voice_duration + 1.3

        else:  # Truth + CTA weight
            audio = audio.volumex(1.15)
            duration = voice_duration + 1.1

        text_img = make_text(line)

        text_clip = (
            ImageClip(text_img)
            .set_start(timeline)
            .set_duration(duration)
            .fadein(0.25)
            .fadeout(0.35)
        )

        clips.append(text_clip)
        audio_clips.append(audio.set_start(timeline))

        timeline += duration

    timeline = min(timeline, MAX_REEL_LENGTH)

    final_video = CompositeVideoClip([base] + clips)
    final_video = final_video.set_duration(timeline)
    final_video = final_video.fadeout(0.4)

    final_voice = CompositeAudioClip(audio_clips)

    # --------- CINEMATIC MUSIC ENGINE ---------

    if os.path.exists("music.mp3"):
        music = AudioFileClip("music.mp3")
        music = afx.audio_loop(music, duration=timeline)
        music = music.audio_fadein(1.2)
        music = music.volumex(0.16)

        voice_boost = final_voice.volumex(1.15)
        final_audio = CompositeAudioClip([music, voice_boost])
        final_audio = final_audio.audio_fadeout(0.6)
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

    # --------- TITLE + CAPTION ENGINE ---------

    title = f"{script[0]} | INNER DISCIPLINE"

    caption = "\n".join([
        script[0],
        "",
        script[1],
        "",
        script[2],
        "",
        script[3],
        "",
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

print("🔥 INNER DISCIPLINE ENGINE ACTIVE")
