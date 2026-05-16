import os
import glob
import random
import asyncio
import json
import shutil
import math
from datetime import datetime
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, VideoClip
from moviepy.audio.fx import all as afx
from moviepy.video.fx import all as vfx

import edge_tts


# ================================================================
# INNER DISCIPLINE â€” GROWTH ENGINE v4 COVER
#
# FULL generator. Not a test file.
#
# Adds:
# - background mood folders
# - viral hook engine
# - 30-day series mode
# - retention subtitle animation
# - title/caption/script/cover output
#
# Required:
# - Anton-Regular.ttf
# - logo.png optional
# - music.mp3 optional
# - backgrounds/broken/*.mp4 etc OR root bg1.mp4/bg2.mp4 fallback
# ================================================================


# ================================================================
# PATHS
# ================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
TEMP_DIR = os.path.join(BASE_DIR, "temp_segments")
BG_ROOT = os.path.join(BASE_DIR, "backgrounds")

FONT_PATH = os.path.join(BASE_DIR, "Anton-Regular.ttf")
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")
MUSIC_PATH = os.path.join(BASE_DIR, "music.mp3")

USED_LINES_FILE = os.path.join(BASE_DIR, "used_lines_v3.json")
STATE_FILE = os.path.join(BASE_DIR, "engine_state_v3.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


# ================================================================
# SETTINGS
# ================================================================

W, H = 1080, 1920
FPS = 30
REEL_SECONDS = 20.0

VOICE = "en-US-GuyNeural"
VOLUME = "+0%"

ORANGE = (255, 126, 0)
WHITE = (255, 255, 255)
RED = (255, 42, 42)
BLACK = (0, 0, 0)

TEXT_MAX_WIDTH = 900
TEXT_CENTER_Y = 0.555
TEXT_HOOK_Y = 0.50

LOGO_OPACITY = 0.38
LOGO_SIZE = 112
LOGO_BOTTOM_MARGIN = 100

COVER_LOGO_SIZE = 92
COVER_DARKEN = 0.36
COVER_BLUR_RADIUS = 18

ZOOM_STRENGTH = 0.072
SHAKE_STRENGTH = 5


# ================================================================
# STATE
# ================================================================

if os.path.exists(USED_LINES_FILE):
    with open(USED_LINES_FILE, "r", encoding="utf-8") as f:
        used_lines = json.load(f)
else:
    used_lines = []

if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)
else:
    state = {"category_step": 0, "series_day": 1}

if not isinstance(state.get("category_step"), int):
    state["category_step"] = 0

if not isinstance(state.get("series_day"), int):
    state["series_day"] = 1


# ================================================================
# PACING
# ================================================================

PACING = {
    "attack": {"rate": "-4%", "pitch": "-35Hz", "chunk_size": 2, "music_volume": 0.16, "gap": 0.13},
    "story": {"rate": "-11%", "pitch": "-40Hz", "chunk_size": 3, "music_volume": 0.12, "gap": 0.18},
    "cold": {"rate": "-15%", "pitch": "-45Hz", "chunk_size": 3, "music_volume": 0.10, "gap": 0.22},
}


# ================================================================
# HOOK ENGINE
# ================================================================

HOOK_FORMULAS = {
    "accusation": [
        "You are not lazy. You are addicted to easy.",
        "You are not confused. You are avoiding the work.",
        "You are not stuck. You are comfortable.",
        "You are not tired. You are untrained.",
        "You do not need motivation. You need consequences.",
    ],
    "identity_attack": [
        "You became the man you promised you would never be.",
        "The version of you from five years ago would not respect this.",
        "You lowered the standard and called it maturity.",
        "You are negotiating with the weakness you should be killing.",
        "You are living like your future is not watching.",
    ],
    "fear": [
        "This habit is quietly ruining your future.",
        "Five years can disappear while you keep saying tomorrow.",
        "The scary part is not failure. It is getting used to it.",
        "Comfort does not look dangerous until it owns you.",
        "The drift feels harmless until it becomes your life.",
    ],
    "contradiction": [
        "Discipline is not your problem. Your environment is.",
        "You do not need a new goal. You need a new standard.",
        "Your problem is not time. It is tolerance.",
        "You are not lacking potential. You are lacking pressure.",
        "Your life does not change when you feel ready.",
    ],
    "curiosity": [
        "The first sign of weakness is not what you think.",
        "Most men lose themselves in a way nobody notices.",
        "There is one habit that exposes your entire standard.",
        "The reason you keep restarting is painfully simple.",
        "This is why your motivation keeps dying.",
    ],
}


# ================================================================
# SERIES MODE
# ================================================================

SERIES_NAME = "30 DAYS OF INNER DISCIPLINE"

SERIES_EPISODES = [
    {"day": 1, "title": "NO SNOOZE", "mood": "morning", "task": "Wake up on the first alarm.", "pain": "The snooze button trains betrayal."},
    {"day": 2, "title": "NO PHONE", "mood": "morning", "task": "No phone for the first hour.", "pain": "Your attention is stolen before your day begins."},
    {"day": 3, "title": "MAKE THE BED", "mood": "rebuild", "task": "Make your bed before anything else.", "pain": "A chaotic room creates a chaotic mind."},
    {"day": 4, "title": "WALK ALONE", "mood": "broken", "task": "Take a 20 minute walk without music.", "pain": "You keep avoiding your own thoughts."},
    {"day": 5, "title": "TRAIN TIRED", "mood": "dangerous", "task": "Train for 20 minutes even if you feel weak.", "pain": "You only respect discipline when it is convenient."},
    {"day": 6, "title": "CLEAN YOUR SPACE", "mood": "rebuild", "task": "Clean one area you have been ignoring.", "pain": "Your environment is exposing your standard."},
    {"day": 7, "title": "WRITE THE TRUTH", "mood": "broken", "task": "Journal one honest page.", "pain": "You cannot fix what you refuse to face."},
    {"day": 8, "title": "COLD START", "mood": "morning", "task": "Start the day with discomfort.", "pain": "Comfort has been making your decisions."},
    {"day": 9, "title": "ONE HARD THING", "mood": "dangerous", "task": "Do the hardest task first.", "pain": "You keep giving your best energy to easy things."},
    {"day": 10, "title": "NO EXCUSES", "mood": "challenge", "task": "Complete today with zero excuses.", "pain": "Your excuses are shrinking you."},
    {"day": 11, "title": "SILENT WORK", "mood": "rebuild", "task": "Work for 45 minutes without announcing it.", "pain": "You keep wanting credit before the result."},
    {"day": 12, "title": "FACE THE MIRROR", "mood": "broken", "task": "Say the truth out loud to yourself.", "pain": "The mirror knows when you are lying."},
    {"day": 13, "title": "RUN THE STAIRS", "mood": "dangerous", "task": "Do a short brutal conditioning session.", "pain": "Your mind keeps quitting before your body needs to."},
    {"day": 14, "title": "RESET NIGHT", "mood": "rebuild", "task": "Prepare tomorrow before sleeping.", "pain": "A weak night creates a weak morning."},
    {"day": 15, "title": "HALF WAY", "mood": "challenge", "task": "Review what changed and what still disgusts you.", "pain": "Progress without honesty becomes ego."},
    {"day": 16, "title": "DEEP WORK", "mood": "rebuild", "task": "Give one goal 60 undistracted minutes.", "pain": "Your future is losing to notifications."},
    {"day": 17, "title": "NO COMFORT FOOD", "mood": "dangerous", "task": "Eat like someone who respects his body.", "pain": "Every craving asks who is in control."},
    {"day": 18, "title": "CALL YOURSELF OUT", "mood": "broken", "task": "Write down your top three excuses.", "pain": "Your favorite excuse is your prison."},
    {"day": 19, "title": "TRAIN EARLY", "mood": "morning", "task": "Move your body before the day owns you.", "pain": "If you wait for energy, weakness wins."},
    {"day": 20, "title": "NO COMPLAINING", "mood": "dangerous", "task": "Go one day without complaining.", "pain": "Complaining makes weakness feel justified."},
    {"day": 21, "title": "FIX ONE THING", "mood": "rebuild", "task": "Fix one neglected part of your life.", "pain": "Neglect compounds quietly."},
    {"day": 22, "title": "BE UNREACHABLE", "mood": "rebuild", "task": "Block two hours for your future.", "pain": "Everyone has access to you except your goals."},
    {"day": 23, "title": "SHOW UP ANYWAY", "mood": "dangerous", "task": "Do the work even if the mood is gone.", "pain": "Mood-based discipline is fake discipline."},
    {"day": 24, "title": "CUT THE NOISE", "mood": "broken", "task": "Remove one distraction for 24 hours.", "pain": "Noise is how you avoid the truth."},
    {"day": 25, "title": "BUILD QUIETLY", "mood": "rebuild", "task": "Do one thing today without posting it.", "pain": "Public identity is worthless without private proof."},
    {"day": 26, "title": "PRESSURE DAY", "mood": "challenge", "task": "Tell someone your task and report back.", "pain": "Private promises are too easy to break."},
    {"day": 27, "title": "HARD CONVERSATION", "mood": "broken", "task": "Have the conversation you keep avoiding.", "pain": "Avoidance is costing your respect."},
    {"day": 28, "title": "STANDARD CHECK", "mood": "dangerous", "task": "Raise one standard and obey it today.", "pain": "A man becomes what he tolerates."},
    {"day": 29, "title": "FINAL PUSH", "mood": "challenge", "task": "Do not coast because the finish is close.", "pain": "Most men quit mentally before they quit physically."},
    {"day": 30, "title": "NEW IDENTITY", "mood": "rebuild", "task": "Choose the standard you will carry forward.", "pain": "Thirty days means nothing if you return to the old man."},
]


# ================================================================
# REGULAR CONTENT
# ================================================================

CONTENT = {
    "wasted_potential": {
        "mood": "broken",
        "cover": ["YOU DRIFT", "STILL WEAK", "WASTED TIME", "NO STANDARD", "YOU LOST"],
        "problem": [
            "You wake up with plans and go to sleep with excuses.",
            "You know what to do, but you keep choosing the easiest option.",
            "You lowered your standards so many times they no longer feel low.",
            "Your life is not falling apart loudly. It is drifting quietly.",
        ],
        "mirror": [
            "And the worst part is, you can feel it.",
            "Nobody has to tell you. You already know.",
            "That shame is your standard trying to come back.",
            "Deep down, you know this version of you is not enough.",
        ],
        "consequence": [
            "If you keep moving like this, five years will disappear and nothing will change.",
            "Comfort is charging you interest every single day.",
            "Every weak decision becomes a vote for the man you hate becoming.",
            "You are not just wasting time. You are training weakness.",
        ],
        "cta": [
            "Today, kill one excuse. Comment DISCIPLINE.",
            "No speech. One action today. Comment LOCKED.",
            "Restart now. Not Monday. Comment RESET.",
            "Follow if you are done restarting.",
        ],
    },
    "morning_discipline": {
        "mood": "morning",
        "cover": ["OWN MORNING", "WAKE UP", "FIRST BATTLE", "NO SNOOZE", "WIN EARLY"],
        "problem": [
            "You wake up late, rush everything, and call the day stressful.",
            "You give your best energy to comfort, then give leftovers to your goals.",
            "The phone gets your first attention. Your future gets whatever is left.",
            "You do not need a better life first. You need a better first hour.",
        ],
        "mirror": [
            "Every morning tells the truth before your mouth can lie.",
            "Nobody claps for the morning win. That is why it matters.",
            "The man you become is built before the world sees you.",
            "Discipline is decided when nobody is watching.",
        ],
        "consequence": [
            "Win the first hour and the rest of the day has to respect you.",
            "Lose the morning long enough and weakness starts feeling normal.",
            "You cannot build a hard life with soft mornings.",
            "Your future is waiting for structure, not motivation.",
        ],
        "cta": [
            "Tomorrow, no snooze. Comment 5AM.",
            "Win the first hour. Comment LOCKED.",
            "Set the alarm now. Comment DISCIPLINE.",
            "Follow for the 30 day discipline build.",
        ],
    },
    "masculine_standard": {
        "mood": "dangerous",
        "cover": ["BE THE MAN", "RAISE STANDARD", "NO EXCUSES", "LEAD YOURSELF", "REAL MAN"],
        "problem": [
            "You say you want to lead, but you cannot keep a promise to yourself.",
            "You confuse anger with strength and comfort with peace.",
            "You are physically present but mentally absent where it matters.",
            "You want the title of a man without the private discipline of one.",
        ],
        "mirror": [
            "Your actions are your real reputation.",
            "A standard is not what you post. It is what you refuse to break.",
            "Your word to yourself is either building you or destroying you.",
            "Every man is measured by what he does when it is inconvenient.",
        ],
        "consequence": [
            "If you cannot govern yourself, the world will govern you.",
            "A weak standard does not stay private. It leaks into everything.",
            "Discipline is the price of being trusted.",
            "You rise by living cleaner, not by talking harder.",
        ],
        "cta": [
            "Raise one standard today. Comment STANDARD.",
            "Lead yourself first. Comment DISCIPLINE.",
            "No more fake standards. Comment LOCKED.",
            "Follow if you are rebuilding the man.",
        ],
    },
    "accountability_challenge": {
        "mood": "challenge",
        "cover": ["STOP ALONE", "30 DAYS", "JOIN NOW", "NO HIDING", "REAL ACCOUNTABILITY"],
        "problem": [
            "You start strong, disappear quietly, then promise yourself next week will be different.",
            "You keep relying on willpower, and willpower keeps running out.",
            "Your environment accepts your excuses, so your standard never rises.",
            "Alone, you negotiate. Around disciplined people, you execute.",
        ],
        "mirror": [
            "That is why structure matters.",
            "That is why the right room changes behavior.",
            "Accountability exposes the excuses you hide from yourself.",
            "People show up differently when the standard is visible.",
        ],
        "consequence": [
            "Thirty days of daily check-ins can do what private promises could not.",
            "The group gives you one thing comfort never will: consequence.",
            "You either build with people who push you or stay alone with excuses.",
            "Your next level needs structure, not another motivational video.",
        ],
        "cta": [
            "Join the Inner Discipline Challenge. Link in bio.",
            "Thirty days. Daily check-ins. Link in bio.",
            "Stop doing it alone. Link in bio.",
            "The group is open. Link in bio.",
        ],
    },
}

CATEGORY_ORDER = list(CONTENT.keys())


@dataclass
class Script:
    mode: str
    category: str
    mood: str
    cover: str
    title: str
    pacing: str
    lines: list
    day: int = 0
    task: str = ""


# ================================================================
# UTILS
# ================================================================

def clean_text(text):
    for old, new in {
        "\u2014": "-",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
    }.items():
        text = text.replace(old, new)
    return text.strip()


def save_state():
    with open(USED_LINES_FILE, "w", encoding="utf-8") as f:
        json.dump(used_lines, f, ensure_ascii=False, indent=2)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def pick_unique(pool):
    available = [x for x in pool if x not in used_lines]
    if not available:
        available = pool[:]
    choice = random.choice(available)
    used_lines.append(choice)
    return choice


def pick_hook():
    formula = random.choices(
        list(HOOK_FORMULAS.keys()),
        weights=[0.24, 0.25, 0.22, 0.17, 0.12],
        k=1,
    )[0]
    return pick_unique(HOOK_FORMULAS[formula])


def get_next_category():
    index = state["category_step"] % len(CATEGORY_ORDER)
    state["category_step"] += 1
    return CATEGORY_ORDER[index]


# ================================================================
# SCRIPT BUILDING
# ================================================================

def build_regular_script():
    category = get_next_category()
    bank = CONTENT[category]

    pacing = random.choices(["attack", "story", "cold"], weights=[0.60, 0.28, 0.12], k=1)[0]

    lines = [
        pick_hook(),
        pick_unique(bank["problem"]),
        pick_unique(bank["mirror"]),
        pick_unique(bank["consequence"]),
        pick_unique(bank["cta"]),
    ]

    cover = random.choice(bank["cover"])

    return Script(
        mode="regular",
        category=category,
        mood=bank["mood"],
        cover=cover,
        title=f"{cover} | INNER DISCIPLINE",
        pacing=pacing,
        lines=lines,
    )


def build_series_script():
    day = state["series_day"]
    episode = SERIES_EPISODES[(day - 1) % len(SERIES_EPISODES)]

    state["series_day"] += 1
    if state["series_day"] > 30:
        state["series_day"] = 1

    lines = [
        f"Day {episode['day']} of 30. {episode['title']}.",
        episode["pain"],
        f"Your task is simple. {episode['task']}",
        "Do not negotiate with the weak version of you.",
        "Comment DONE when you finish it.",
    ]

    return Script(
        mode="series",
        category="series",
        mood=episode["mood"],
        cover=f"DAY {episode['day']}",
        title=f"DAY {episode['day']}: {episode['title']} | INNER DISCIPLINE",
        pacing="attack",
        lines=lines,
        day=episode["day"],
        task=episode["task"],
    )


def build_script():
    # 30% series, 70% regular reach reels
    if random.random() < 0.30:
        return build_series_script()
    return build_regular_script()


# ================================================================
# BACKGROUND SELECTION
# ================================================================

VIDEO_EXTENSIONS = ["*.mp4", "*.MP4", "*.mov", "*.MOV"]


def scan_video_files(folder):
    files = []
    for ext in VIDEO_EXTENSIONS:
        files.extend(glob.glob(os.path.join(folder, ext)))
    return files


def root_bg_files():
    files = []
    for pattern in ["bg*.mp4", "bg*.MP4", "bg*.mov", "bg*.MOV"]:
        files.extend(glob.glob(os.path.join(BASE_DIR, pattern)))
    return files


def get_background_pool(mood):
    pool = []

    mood_folder = os.path.join(BG_ROOT, mood)
    if os.path.isdir(mood_folder):
        pool.extend(scan_video_files(mood_folder))

    generic_folder = os.path.join(BG_ROOT, "generic")
    if os.path.isdir(generic_folder):
        pool.extend(scan_video_files(generic_folder))

    pool.extend(root_bg_files())

    if not pool and os.path.isdir(BG_ROOT):
        for folder, _, _ in os.walk(BG_ROOT):
            pool.extend(scan_video_files(folder))

    return sorted(list(set(pool)))


def choose_background(mood):
    pool = get_background_pool(mood)

    print("BASE DIR:", BASE_DIR)
    print("BG ROOT:", BG_ROOT)
    print("MOOD:", mood)
    print("BACKGROUND POOL FOUND:", pool)

    if not pool:
        raise Exception(
            "No background videos found. Add videos to backgrounds/broken, "
            "backgrounds/morning, backgrounds/dangerous, backgrounds/rebuild, "
            "backgrounds/challenge, backgrounds/generic OR add bg1.mp4 in root."
        )

    return random.choice(pool)


# ================================================================
# TTS
# ================================================================

async def tts_async(text, filename, rate, pitch):
    communicate = edge_tts.Communicate(
        clean_text(text),
        VOICE,
        rate=rate,
        pitch=pitch,
        volume=VOLUME,
    )
    await communicate.save(filename)


def generate_voice(text, filename, pacing):
    mode = PACING[pacing]
    asyncio.run(tts_async(text, filename, mode["rate"], mode["pitch"]))


# ================================================================
# TEXT RENDERING
# ================================================================

HOT_WORDS = {
    "WEAK", "WEAKNESS", "LOSING", "FAIL", "FAILED", "KILL", "EXCUSE", "EXCUSES",
    "DISCIPLINE", "STANDARD", "STANDARDS", "RESET", "LOCKED", "ALONE", "QUIT",
    "QUITTING", "DRIFT", "DRIFTING", "WASTING", "MAN", "MORNING", "SNOOZE",
    "NOW", "TODAY", "DONE", "DAY", "NO", "STOP", "HARD", "COMFORT", "CONTROL",
    "ACCOUNTABILITY", "CONSEQUENCE", "FIRST", "BATTLE", "FUTURE",
}

DANGER_WORDS = {
    "WEAK", "WEAKNESS", "FAIL", "FAILED", "QUIT", "QUITTING", "EXCUSE", "EXCUSES",
    "WASTING", "DRIFT", "DRIFTING", "COMFORT", "BETRAYAL",
}


def load_font(size):
    if not os.path.exists(FONT_PATH):
        raise FileNotFoundError("Missing Anton-Regular.ttf in repo root.")
    return ImageFont.truetype(FONT_PATH, size)


def wrap_words(draw, text, font, max_width):
    words = clean_text(text).upper().split()
    lines = []
    current = []
    for word in words:
        test = " ".join(current + [word])
        if draw.textlength(test, font=font) <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(current)
            current = [word]
    if current:
        lines.append(current)
    return lines


def draw_multiline(draw, lines, font, center_y, style="normal"):
    line_gap = int(font.size * 0.20)
    total_h = len(lines) * font.size + max(0, len(lines) - 1) * line_gap
    y0 = int(center_y - total_h / 2)
    first_word_done = False

    for li, words in enumerate(lines):
        widths = [draw.textlength(w, font=font) for w in words]
        space = draw.textlength(" ", font=font)
        line_w = sum(widths) + max(0, len(words) - 1) * space
        x = int((W - line_w) / 2)
        y = y0 + li * (font.size + line_gap)

        for wi, word in enumerate(words):
            raw = word.strip(".,?!:;\"'").upper()

            if style == "cover":
                color = ORANGE if wi == 0 else WHITE
            elif raw in DANGER_WORDS:
                color = RED
            elif raw in HOT_WORDS:
                color = ORANGE
            elif not first_word_done:
                color = ORANGE
                first_word_done = True
            else:
                color = WHITE

            draw.text(
                (x, y),
                word,
                font=font,
                fill=color,
                stroke_width=7,
                stroke_fill=BLACK,
            )
            x += int(widths[wi] + space)


def make_text_frame(text, level="normal"):
    img = Image.new("RGB", (W, H), BLACK)
    draw = ImageDraw.Draw(img)

    wc = len(clean_text(text).split())

    if level == "cover":
        font_size = 170 if wc <= 2 else 135
        y = H * 0.53
    elif level == "hook":
        font_size = 140 if wc <= 4 else 114
        y = H * TEXT_HOOK_Y
    elif wc <= 2:
        font_size = 145
        y = H * TEXT_CENTER_Y
    elif wc <= 5:
        font_size = 114
        y = H * TEXT_CENTER_Y
    else:
        font_size = 92
        y = H * TEXT_CENTER_Y

    font = load_font(font_size)
    lines = wrap_words(draw, text, font, TEXT_MAX_WIDTH)
    draw_multiline(draw, lines, font, y, style="cover" if level == "cover" else "normal")
    return np.array(img)


def make_logo_frame():
    if not os.path.exists(LOGO_PATH):
        return None

    logo = Image.open(LOGO_PATH).convert("RGBA")
    aspect = logo.height / max(1, logo.width)
    new_w = LOGO_SIZE
    new_h = int(LOGO_SIZE * aspect)
    logo = logo.resize((new_w, new_h), Image.LANCZOS)

    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x = (W - new_w) // 2
    y = H - new_h - LOGO_BOTTOM_MARGIN
    canvas.paste(logo, (x, y), logo)

    bg = Image.new("RGB", (W, H), BLACK)
    bg.paste(canvas.convert("RGB"), (0, 0), canvas.split()[3])
    return np.array(bg)


# ================================================================
# VIDEO FX
# ================================================================

def prepare_background(video_path, duration):
    bg = VideoFileClip(video_path)

    ratio = bg.w / bg.h
    target = W / H

    if ratio > target:
        bg = bg.resize(height=H)
    else:
        bg = bg.resize(width=W)

    bg = bg.crop(x_center=bg.w / 2, y_center=bg.h / 2, width=W, height=H)

    if bg.duration < duration:
        bg = vfx.loop(bg, duration=duration)

    max_start = max(0, bg.duration - duration - 0.1)
    start = random.uniform(0, max_start) if max_start > 1 else 0
    return bg.subclip(start, start + duration)


def make_vignette():
    y = np.linspace(0, 1, H).reshape(H, 1)
    x = np.linspace(-1, 1, W).reshape(1, W)

    radial = 1 - 0.42 * np.clip((x ** 2 + (y - 0.45) ** 2), 0, 1)

    top = np.ones((H, W), dtype=np.float32)
    top[: int(H * 0.40), :] *= np.linspace(0.44, 1.0, int(H * 0.40)).reshape(-1, 1)

    bottom = np.ones((H, W), dtype=np.float32)
    bottom[int(H * 0.76):, :] *= np.linspace(1.0, 0.70, H - int(H * 0.76)).reshape(-1, 1)

    return np.clip(radial * top * bottom, 0.32, 1.0).astype(np.float32)


def apply_contrast(frame):
    f = frame.astype(np.float32)
    f = (f - 128) * 1.15 + 128
    f = f + 5
    return np.clip(f, 0, 255).astype(np.uint8)


def composite_rgb(base, overlay, opacity=1.0, offset_y=0, scale=1.0):
    if scale != 1.0:
        pil = Image.fromarray(overlay)
        nw = max(1, int(W * scale))
        nh = max(1, int(H * scale))
        pil = pil.resize((nw, nh), Image.LANCZOS)

        canvas = Image.new("RGB", (W, H), BLACK)
        x = (W - nw) // 2
        y = (H - nh) // 2 + int(offset_y)
        canvas.paste(pil, (x, y))
        overlay = np.array(canvas)
    elif offset_y != 0:
        overlay = np.roll(overlay, int(offset_y), axis=0)

    mask = np.any(overlay > 18, axis=2)
    if not np.any(mask):
        return base

    b = base.astype(np.float32)
    o = overlay.astype(np.float32)
    b[mask] = b[mask] * (1 - opacity) + o[mask] * opacity
    return np.clip(b, 0, 255).astype(np.uint8)


def subtitle_animation_values(t, start, end, event_type):
    local = t - start

    fd = 0.08 if event_type in ["cover", "impact"] else 0.11

    if local < fd:
        alpha = local / fd
    elif end - t < fd:
        alpha = (end - t) / fd
    else:
        alpha = 1.0

    alpha = float(np.clip(alpha, 0.0, 1.0))

    if local < 0.12:
        scale = 1.0 + (0.06 * (1 - local / 0.12))
    else:
        scale = 1.0

    if event_type == "impact":
        offset_y = math.sin(local * 34) * 5 if local < 0.18 else 0
    elif event_type == "cover":
        offset_y = math.sin(local * 28) * 3 if local < 0.20 else 0
    else:
        offset_y = 0

    return alpha, offset_y, scale


# ================================================================
# TIMELINE
# ================================================================

def split_chunks(text, chunk_size):
    words = clean_text(text).split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks if chunks else [text]


def make_text_events(script, voice_data, duration):
    events = []

    events.append({
        "frame": make_text_frame(script.cover, "cover"),
        "start": 0.01,
        "end": min(0.82, duration),
        "type": "cover",
    })

    fade_tail = 0.10

    for i, item in enumerate(voice_data):
        chunks = split_chunks(item["line"], item["chunk_size"])
        chunk_dur = item["duration"] / max(1, len(chunks))

        for j, chunk in enumerate(chunks):
            start = item["start"] + j * chunk_dur
            end = item["start"] + (j + 1) * chunk_dur + fade_tail

            if start >= duration:
                continue

            level = "hook" if i == 0 and j == 0 else "normal"
            raw = chunk.upper()

            event_type = "impact" if any(
                w in raw for w in ["WEAK", "FAIL", "NO ", "STOP", "KILL", "QUIT", "DAY"]
            ) else "text"

            events.append({
                "frame": make_text_frame(chunk, level),
                "start": start,
                "end": min(end, duration),
                "type": event_type,
            })

    if duration > 12:
        flash = random.choice(["NO EXCUSES", "LOCK IN", "WAKE UP", "MOVE NOW", "PROVE IT"])
        t = min(duration - 2.5, max(7.0, duration * 0.52))
        events.append({
            "frame": make_text_frame(flash, "cover"),
            "start": t,
            "end": min(t + 0.42, duration),
            "type": "impact",
        })

    return events


# ================================================================
# VIDEO BUILDER
# ================================================================

def build_video(script, bg_path, out_path):
    voice_files = []
    audio_clips = []
    bg_clip = None

    try:
        print(f"Mode: {script.mode.upper()}")
        print(f"Mood: {script.mood.upper()}")
        print(f"Pacing: {script.pacing.upper()}")
        print(f"Background: {bg_path}")
        print(f"Cover: {script.cover}")

        voice_data = []
        cursor = 0.30
        gap = PACING[script.pacing]["gap"]

        print("Generating voice lines...")
        for i, line in enumerate(script.lines):
            vf = os.path.join(
                TEMP_DIR,
                f"voice_{datetime.now().strftime('%H%M%S')}_{i}_{random.randint(1000,9999)}.mp3",
            )
            voice_files.append(vf)

            generate_voice(line, vf, script.pacing)

            audio_probe = AudioFileClip(vf)
            dur = float(audio_probe.duration)
            audio_probe.close()

            voice_data.append({
                "file": vf,
                "line": line,
                "duration": dur,
                "start": cursor,
                "chunk_size": PACING[script.pacing]["chunk_size"],
            })

            cursor += dur + (gap if i < len(script.lines) - 1 else 0.24)

        duration = min(cursor, REEL_SECONDS)
        print(f"Video duration: {duration:.2f}s")

        for item in voice_data:
            if item["start"] >= duration:
                continue
            audio_clips.append(AudioFileClip(item["file"]).set_start(item["start"]))

        text_events = make_text_events(script, voice_data, duration)
        logo_frame = make_logo_frame()
        vignette = make_vignette()

        bg_clip = prepare_background(bg_path, duration)

        def make_frame(t):
            frame = bg_clip.get_frame(t).astype(np.uint8)

            zoom = 1.0 + ZOOM_STRENGTH * (t / max(duration, 0.001))
            if zoom > 1.001:
                new_w = int(W / zoom)
                new_h = int(H / zoom)
                x1 = (W - new_w) // 2
                y1 = (H - new_h) // 2
                pil = Image.fromarray(frame)
                pil = pil.crop((x1, y1, x1 + new_w, y1 + new_h)).resize((W, H), Image.LANCZOS)
                frame = np.array(pil)

            if t < 0.80:
                dx = int(math.sin(t * 95) * SHAKE_STRENGTH)
                dy = int(math.cos(t * 85) * SHAKE_STRENGTH)
                frame = np.roll(frame, shift=(dy, dx), axis=(0, 1))

            frame = apply_contrast(frame)

            f = frame.astype(np.float32)
            f[:, :, 0] *= vignette
            f[:, :, 1] *= vignette
            f[:, :, 2] *= vignette
            frame = np.clip(f, 0, 255).astype(np.uint8)

            band = frame.astype(np.float32)
            y1 = int(H * 0.34)
            y2 = int(H * 0.72)
            band[y1:y2, :, :] *= 0.74
            frame = np.clip(band, 0, 255).astype(np.uint8)

            for ev in text_events:
                if ev["start"] <= t < ev["end"]:
                    alpha, offset_y, scale = subtitle_animation_values(
                        t, ev["start"], ev["end"], ev["type"]
                    )
                    frame = composite_rgb(frame, ev["frame"], opacity=alpha, offset_y=offset_y, scale=scale)

            if logo_frame is not None:
                frame = composite_rgb(frame, logo_frame, opacity=LOGO_OPACITY)

            return frame

        final_video = VideoClip(make_frame, duration=duration).set_fps(FPS)
        final_voice = CompositeAudioClip(audio_clips)

        if os.path.exists(MUSIC_PATH):
            music = AudioFileClip(MUSIC_PATH)
            music = afx.audio_loop(music, duration=duration)
            music = music.audio_fadein(0.35).audio_fadeout(0.50)
            music = music.volumex(PACING[script.pacing]["music_volume"]).set_start(0)
            final_audio = CompositeAudioClip([music, final_voice.volumex(1.22)])
        else:
            final_audio = final_voice

        final = final_video.set_audio(final_audio).fadeout(0.22)

        print(f"Rendering: {out_path}")
        final.write_videofile(
            out_path,
            fps=FPS,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            preset="fast",
            logger=None,
        )

        final.close()
        final_video.close()
        final_audio.close()

        if bg_clip:
            bg_clip.close()

        return True

    except Exception as e:
        import traceback
        print(f"FAILED: {e}")
        traceback.print_exc()
        return False

    finally:
        for clip in audio_clips:
            try:
                clip.close()
            except Exception:
                pass

        if bg_clip:
            try:
                bg_clip.close()
            except Exception:
                pass

        for vf in voice_files:
            if os.path.exists(vf):
                try:
                    os.remove(vf)
                except Exception:
                    pass


# ================================================================
# METADATA
# ================================================================

def build_caption(script):
    if script.mode == "series":
        return "\n".join([
            SERIES_NAME,
            "",
            f"Day {script.day}: {script.title.replace(' | INNER DISCIPLINE', '')}",
            "",
            f"Task: {script.task}",
            "",
            "Comment DONE when you finish it.",
            "Save this and come back tomorrow.",
            "",
            "#discipline #30daychallenge #innerdiscipline #selfimprovement #accountability #mindset #noexcuses #consistency #growthmindset #hardwork",
        ])

    openers = {
        "wasted_potential": "Most men do not fail loudly. They drift quietly.",
        "morning_discipline": "Win the morning before the world gets access to you.",
        "masculine_standard": "Your standard is not what you say. It is what you repeat.",
        "accountability_challenge": "Discipline gets easier when the room refuses your excuses.",
    }

    hashtags = {
        "wasted_potential": "#discipline #selfimprovement #mindset #noexcuses #selfmastery #growthmindset #mentalstrength #innerdiscipline #accountability #hardwork",
        "morning_discipline": "#morningroutine #discipline #5amclub #selfimprovement #mindset #consistency #focus #innerdiscipline #noexcuses #growthmindset",
        "masculine_standard": "#masculinity #discipline #selfmastery #menwithstandards #mindset #noexcuses #leadership #innerdiscipline #growthmindset #accountability",
        "accountability_challenge": "#30daychallenge #accountability #discipline #innerdisciplinechallenge #selfimprovement #mindset #facebookgroup #consistency #noexcuses #hardwork",
    }

    return "\n".join([
        openers.get(script.category, "Read this twice."),
        "",
        f'"{script.lines[0]}"',
        "",
        script.lines[2],
        "",
        "-",
        script.lines[-1],
        "",
        hashtags.get(script.category, hashtags["wasted_potential"]),
    ])


def make_cinematic_cover_background(bg_path):
    """
    Cover Engine v4:
    Pulls one frame from the chosen background,
    crops it vertical, blurs it, darkens it, then uses it as a cinematic cover.
    """
    try:
        clip = VideoFileClip(bg_path)
        t = min(max(0.15, clip.duration * 0.28), max(0, clip.duration - 0.10))
        frame = clip.get_frame(t).astype(np.uint8)
        clip.close()

        img = Image.fromarray(frame).convert("RGB")

        ratio = img.width / img.height
        target = W / H

        if ratio > target:
            new_h = H
            new_w = int(H * ratio)
            img = img.resize((new_w, new_h), Image.LANCZOS)
        else:
            new_w = W
            new_h = int(W / ratio)
            img = img.resize((new_w, new_h), Image.LANCZOS)

        left = (img.width - W) // 2
        top = (img.height - H) // 2
        img = img.crop((left, top, left + W, top + H))

        # blur without importing extra filters
        small = img.resize((max(1, W // COVER_BLUR_RADIUS), max(1, H // COVER_BLUR_RADIUS)), Image.BILINEAR)
        img = small.resize((W, H), Image.BICUBIC)

        arr = np.array(img).astype(np.float32)
        arr = (arr - 128) * 1.12 + 128
        arr *= COVER_DARKEN
        arr = np.clip(arr, 0, 255).astype(np.uint8)

        return Image.fromarray(arr).convert("RGB")

    except Exception as e:
        print(f"Cover background failed, using black fallback: {e}")
        return Image.new("RGB", (W, H), BLACK)


def draw_cover_text_on_image(img, cover_text):
    img_rgba = img.convert("RGBA")

    # readability band
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    band_draw = ImageDraw.Draw(band)
    band_draw.rectangle((0, int(H * 0.34), W, int(H * 0.70)), fill=(0, 0, 0, 92))
    img_rgba.alpha_composite(band)

    draw = ImageDraw.Draw(img_rgba)
    wc = len(clean_text(cover_text).split())
    font = load_font(178 if wc <= 2 else 136)
    lines = wrap_words(draw, cover_text, font, 940)

    line_gap = int(font.size * 0.20)
    total_h = len(lines) * font.size + max(0, len(lines) - 1) * line_gap
    y0 = int(H * 0.53 - total_h / 2)

    for li, words in enumerate(lines):
        widths = [draw.textlength(w, font=font) for w in words]
        space = draw.textlength(" ", font=font)
        line_w = sum(widths) + max(0, len(words) - 1) * space
        x = int((W - line_w) / 2)
        y = y0 + li * (font.size + line_gap)

        for wi, word in enumerate(words):
            raw = word.strip(".,?!:;\"'").upper()
            color = ORANGE if wi == 0 else WHITE
            if raw in DANGER_WORDS:
                color = RED

            draw.text((x + 5, y + 6), word, font=font, fill=(0, 0, 0, 210))
            draw.text(
                (x, y),
                word,
                font=font,
                fill=color + (255,),
                stroke_width=8,
                stroke_fill=(0, 0, 0, 255),
            )
            x += int(widths[wi] + space)

    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH).convert("RGBA")
        aspect = logo.height / max(1, logo.width)
        new_w = COVER_LOGO_SIZE
        new_h = int(COVER_LOGO_SIZE * aspect)
        logo = logo.resize((new_w, new_h), Image.LANCZOS)
        logo.putalpha(150)
        img_rgba.paste(
            logo,
            ((W - new_w) // 2, H - new_h - LOGO_BOTTOM_MARGIN),
            logo,
        )

    return img_rgba.convert("RGB")


def export_cover(script, out_path, bg_path=None):
    base = os.path.splitext(out_path)[0]
    out = f"{base}_cover.png"

    if bg_path:
        img = make_cinematic_cover_background(bg_path)
    else:
        img = Image.new("RGB", (W, H), BLACK)

    img = draw_cover_text_on_image(img, script.cover)
    img.save(out, quality=95)
    return out


def write_metadata(script, out_path, bg_path=None):
    base = os.path.splitext(out_path)[0]

    with open(f"{base}_title.txt", "w", encoding="utf-8") as f:
        f.write(script.title)

    with open(f"{base}_caption.txt", "w", encoding="utf-8") as f:
        f.write(build_caption(script))

    with open(f"{base}_script.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(script.lines))

    return export_cover(script, out_path, bg_path)


# ================================================================
# MAIN
# ================================================================

def main():
    print("\nINNER DISCIPLINE â€” GROWTH ENGINE v4 COVER")
    print("=" * 64)

    script = build_script()
    bg = choose_background(script.mood)

    date = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(OUTPUT_DIR, f"reel_v3_{script.mode}_{script.category}_{date}.mp4")

    ok = build_video(script, bg, out_path)

    if ok:
        cover = write_metadata(script, out_path, bg)
        print("\nOUTPUTS")
        print(f"Video:   {out_path}")
        print(f"Title:   {os.path.splitext(out_path)[0]}_title.txt")
        print(f"Caption: {os.path.splitext(out_path)[0]}_caption.txt")
        print(f"Script:  {os.path.splitext(out_path)[0]}_script.txt")
        print(f"Cover:   {cover}")

    save_state()

    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)

    print("=" * 64)
    print("COMPLETE")


if __name__ == "__main__":
    main()
