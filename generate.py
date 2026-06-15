import os
import glob
import random
import asyncio
import json
import shutil
import math
import time
import uuid
import subprocess
from datetime import datetime
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, VideoClip
from moviepy.audio.fx import all as afx
from moviepy.video.fx import all as vfx

import edge_tts


# ================================================================
# INNER DISCIPLINE â€” MIRROR ENGINE v30.1 FULLSCREEN RETENTION
#
# Clean rebuild. No patch stacking.
#
# Includes:
# - cinematic dark grading
# - lower-center text
# - emerging-from-darkness text animation
# - sequential series_state.json
# - rotation_state.json for lines/covers/backgrounds
# - ebook screenshot bait overlays
# - member/manual/accountability reels
# - background round-robin
# - audio ducking / silence control
# - cover export
# ================================================================


# ================================================================
# PATHS
# ================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
TEMP_DIR = os.path.join(BASE_DIR, "temp_segments")
BG_ROOT = os.path.join(BASE_DIR, "backgrounds")
EBOOK_ROOT = os.path.join(BASE_DIR, "ebook_screenshots")

FONT_PATH = os.path.join(BASE_DIR, "Anton-Regular.ttf")
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")
MUSIC_PATH = os.path.join(BASE_DIR, "music.mp3")

USED_LINES_FILE = os.path.join(BASE_DIR, "used_lines_v3.json")
STATE_FILE = os.path.join(BASE_DIR, "engine_state_v3.json")
SERIES_STATE_FILE = os.path.join(BASE_DIR, "series_state.json")
ROTATION_STATE_FILE = os.path.join(BASE_DIR, "rotation_state.json")
HOOK_STATE_FILE = os.path.join(BASE_DIR, "hook_state.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


# ================================================================
# RANDOM
# ================================================================

RUN_ID = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
random.seed(f"{RUN_ID}_{time.time_ns()}")


# ================================================================
# SETTINGS
# ================================================================

W, H = 1080, 1920
FPS = 30
RETENTION_REEL_MODE = True
RETENTION_MIN_SECONDS = 18.0
RETENTION_MAX_SECONDS = 22.5
RETENTION_LINE_COUNT_MIN = 6
RETENTION_LINE_COUNT_MAX = 7

IDENTITY_ENGINE_MODE = True
IDENTITY_DOMINANCE_ENGINE_MODE = True
COMPLETION_ENGINE_MODE = True
MIRROR_ENGINE_MODE = True
FULLSCREEN_RETENTION_MODE = True
NO_BORDERED_VIDEO = True
NO_BLACK_PANELS = True
TARGET_REEL_SECONDS_MIN = 18.0
TARGET_REEL_SECONDS_MAX = 22.5
TEXT_SCREEN_COVERAGE_TARGET = 0.40
ONE_LINE_AT_A_TIME = True

V30_STRUCTURE = "hook_curiosity_resolution"
V30_PRIMARY_GOAL = "make_viewer_feel_personally_addressed"

V30_WEIGHTING = "70_mirror_15_identity_10_consequence_5_standards"
V30_GOAL = "increase_completion_with_self_confrontation"

OPEN_LOOP_SCRIPTING = True
WATCH_TIME_TARGET_SECONDS = 10.0
V28_IDENTITY_WEIGHT_TARGET = 0.70
PUBLIC_REELS_ONLY = True
DISABLE_DAY_SEQUENCE_PUBLIC = True
IDENTITY_ENGINE_VERSION = "v30"


META_MONETIZATION_MIN_SECONDS = 10.0
META_RETENTION_TARGET_SECONDS = 12.0
MAX_HASHTAGS_V26 = 7
WATERMARK_SCALE_V26 = 0.72
WATERMARK_OPACITY_V26 = 0.58


BANNED_COVERS_V24 = [
    "THIS CHANGES",
    "WATCH THIS",
    "HIDDEN COST",
    "READ THIS",
]



CAPTION_BANK_V26 = {
    "identity": [
        "Your routine tells the truth before your results do.",
        "Discipline is built privately before it shows publicly.",
        "Standards are not what you say. They are what you repeat.",
        "Your habits are building a version of you. Choose carefully.",
    ],
    "consequence": [
        "Weak habits feel small until they compound.",
        "Comfort is never free. The cost just arrives later.",
        "Excuses feel harmless until they become identity.",
        "The bill for avoided discipline always arrives.",
    ],
    "regret": [
        "Time moves whether you build yourself or not.",
        "Potential means nothing without proof.",
        "Regret starts quietly. Usually as a repeated routine.",
        "Later becomes expensive when habits do not change.",
    ],
    "structure": [
        "Structure beats motivation when feelings change.",
        "Rules protect you from your weakest mood.",
        "Decide once. Repeat daily.",
        "Discipline becomes easier when negotiation ends.",
    ],
    "community": [
        "Quiet discipline. Clear standards. No negotiation.",
        "Private standards. Public results.",
        "Control yourself quietly. Let the results speak.",
        "Do what you said when the mood changes.",
    ],
}

HASHTAG_PACKS_V26 = [
    "#discipline #selfdiscipline #consistency #innerdiscipline #mentalstrength",
    "#discipline #habits #standards #selfcontrol #growth",
    "#discipline #routine #focus #mindset #selfrespect",
    "#innerdiscipline #consistency #selfmastery #habits #growthmindset",
    "#discipline #accountability #mentalcontrol #standards #focus",
    "#selfcontrol #discipline #mensmindset #consistency #growth",
]


CAPTION_BANK_V25 = {
    "reflection": [
        "Most people lose discipline long before they lose results.\n\nResults simply reveal what habits already decided.",
        "The routine always speaks first.\n\nThe result only arrives later.",
        "Discipline does not disappear loudly.\n\nIt fades through small decisions repeated too often.",
        "You do not need a new life first.\n\nYou need a new standard repeated long enough.",
    ],
    "identity": [
        "Discipline is not something you do once.\n\nEventually, it becomes who you are.",
        "Your identity is being trained daily.\n\nBy what you repeat when nobody is watching.",
        "A man becomes what he keeps allowing.\n\nStandards are not private forever.",
        "Your habits are voting for a version of you.\n\nMake sure you respect who they are building.",
    ],
    "accountability": [
        "Be honest.\n\nWhat excuse have you repeated so many times it now feels true?",
        "Look at the pattern.\n\nNot the intention. The pattern.",
        "The question is not what you want.\n\nThe question is what you keep proving.",
        "Accountability begins when the excuse stops sounding reasonable.",
    ],
    "consequence": [
        "The cost of weak habits is rarely immediate.\n\nThat is why most people keep paying it.",
        "Small compromises do not look dangerous at first.\n\nThat is what makes them dangerous.",
        "Weak routines charge interest.\n\nEventually, the bill becomes visible.",
        "Comfort feels cheap in the moment.\n\nThe long-term price is always higher.",
    ],
    "regret": [
        "Years pass whether you build yourself or not.\n\nTime is moving either way.",
        "Regret rarely starts as a disaster.\n\nIt starts as a routine you refused to fix.",
        "One day, potential stops sounding impressive.\n\nOnly proof remains.",
        "You are not too late.\n\nBut you are too old to keep pretending time is free.",
    ],
    "structure": [
        "Motivation is unstable.\n\nStructure is what keeps moving when feelings change.",
        "Rules protect you from your weakest mood.",
        "Discipline becomes easier when decisions stop reopening every day.",
        "A serious life requires serious systems.\n\nNot better moods.",
    ],
    "community": [
        "Quiet work.\n\nClear standards.\n\nNo negotiation.",
        "Private discipline first.\n\nPublic results later.",
        "The standard is simple.\n\nDo what you said when the mood changes.",
        "Control yourself quietly.\n\nLet the results speak later.",
    ],
    "soft_promo": [
        "Accountability changes behavior.\n\nStructure beats motivation.",
        "Some people do not need more advice.\n\nThey need a standard they cannot hide from.",
        "A serious room changes how you move.\n\nExcuses get exposed faster.",
        "Private promises break easily.\n\nVisible standards hit different.",
    ],
}

HASHTAG_PACKS_V25 = [
    "#discipline #selfdiscipline #consistency #mindset #growth",
    "#discipline #habits #accountability #selfcontrol #standards",
    "#mentalstrength #discipline #focus #routine #success",
    "#innerdiscipline #consistency #dailyhabits #selfmastery #growthmindset",
    "#disciplinechallenge #discipline #accountability #mentalcontrol #habits",
    "#selfcontrol #discipline #mensmindset #standards #growth",
    "#disciplineovermotivation #habits #mindsetshift #consistency #focus",
    "#mentalcontrol #discipline #routine #selfrespect #innerdiscipline",
]



REEL_SECONDS = 20.0

VOICE = "en-US-GuyNeural"
VOLUME = "+0%"

ORANGE = (255, 126, 0)
WHITE = (255, 255, 255)
RED = (255, 42, 42)
BLACK = (0, 0, 0)

TEXT_MAX_WIDTH = 900
TEXT_CENTER_Y = 0.585
TEXT_HOOK_Y = 0.535

LOGO_OPACITY = 0.38
LOGO_SIZE = 50
LOGO_BOTTOM_MARGIN = 100

COVER_LOGO_SIZE = 50
COVER_DARKEN = 0.36
COVER_BLUR_RADIUS = 18

ZOOM_STRENGTH = 0.088
SHAKE_STRENGTH = 2

CINEMATIC_CONTRAST = 1.18
CINEMATIC_BRIGHTNESS = -12
CINEMATIC_SATURATION = 0.90
CINEMATIC_HIGHLIGHT_CAP = 238
CINEMATIC_SHADOW_LIFT = -10

TEXT_BAND_STRENGTH = 0.66
TEXT_BAND_TOP = 0.40
TEXT_BAND_BOTTOM = 0.73

MUSIC_BASE_VOLUME = 0.14
MUSIC_DUCK_VOLUME = 0.055

EBOOK_BAIT_PROBABILITY = 0.14
MEMBER_REEL_PROBABILITY = 0.16
SERIES_REEL_PROBABILITY = 0.18

SERIES_PRIORITY_MODE = True
GLOBAL_BACKGROUND_ROTATION = True
BACKGROUND_RUN_NUMBER_ROTATION = True
SCENE_MATCHING_ENABLED = True

SCENE_KEYWORDS = {
    "broken": [
        "avoid", "alone", "thoughts", "truth", "excuse", "excuses", "prison",
        "disgusts", "journal", "mirror", "conversation", "weak", "weakness",
        "lost", "drift", "wasted", "regret", "disappear", "years", "excuses", "failure", "cost", "damage",
    ],
    "morning": [
        "wake", "alarm", "snooze", "morning", "first hour", "early",
        "before the day", "start the day", "tomorrow", "night",
    ],
    "dangerous": [
        "train", "training", "pressure", "hard", "body", "stairs",
        "conditioning", "complaining", "standard", "standards", "respect",
        "control", "craving", "move", "brutal", "standard", "private proof", "self control",
    ],
    "rebuild": [
        "bed", "room", "space", "clean", "fix", "reset", "prepare",
        "deep work", "work", "undistracted", "build", "structure",
        "goal", "environment", "future", "phone", "inputs", "attention", "system", "routine",
    ],
    "challenge": [
        "day", "challenge", "done", "accountability", "report back",
        "30", "thirty", "finish", "complete", "task",
    ],
}
RECENT_BACKGROUND_BLOCK = 8
RECENT_LINE_BLOCK = 70

SERIES_START_DAY = 2
SERIES_FAIL_IF_STATE_PUSH_BLOCKED = False
DAY7_REEL_PROBABILITY = 0.18

SILENCE_GAP_MIN = 0.15
SILENCE_GAP_MAX = 0.45

FIRST_FRAME_CONTRAST_BOOST = 1.25
FIRST_FRAME_BRIGHTNESS_MULT = 0.90
FIRST_FRAME_ORANGE_BOOST = 1.10

MIN_RETENTION_SCORE = 7

SAVE_SIGNAL_PROBABILITY = 0.42
SHARE_SIGNAL_PROBABILITY = 0.35

CORE_TOPICS = [
    "discipline", "drifting", "pressure", "weak habits", "self-respect",
    "consistency", "mental control", "routine collapse", "structure",
    "comfort addiction", "standards", "inputs", "identity", "control",
    "silent decay", "wasted years", "regret", "private habits",
    "attention", "environment", "routine", "consequence",
]

BANNED_PHRASES = [
    "never give up",
    "keep pushing",
    "stay motivated",
    "you got this",
    "believe in yourself",
    "greatness",
    "success mindset",
    "dream big",
    "hustle harder",
]

RETENTION_ENDING_LINES = [
    "The routine always tells the truth.",
    "Weak habits always collect consequences.",
    "Your standards decide your future.",
    "Pressure exposes every weak routine.",
    "Comfort slowly destroys structure.",
    "Discipline is built in silence.",
    "Your future reflects your standards.",
    "Control returns when negotiation ends.",
    "Structure decides who stays consistent.",
    "Private standards create public results.",
    "Nothing changes until the routine changes.",
    "A weak standard always becomes visible.",
    "Discipline dies quietly first.",
    "Time exposes every repeated compromise.",
    "Your private habits are not private forever.",
]

DEFAULT_SERIES_DAY = 2
AUTO_COMMIT_STATE = True

# v21:
# If this cannot save state back to GitHub, the next run has no memory.
# So the script fails loudly instead of silently repeating Day 2 / same background.
STRICT_STATE_SEQUENCE = False


# ================================================================
# STATE
# ================================================================

def safe_load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, type(default)):
                return data
        except Exception:
            pass
    return default


used_lines = safe_load_json(USED_LINES_FILE, [])
state = safe_load_json(STATE_FILE, {"category_step": 0})

if not isinstance(state.get("category_step"), int):
    state["category_step"] = 0


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_state():
    save_json(USED_LINES_FILE, used_lines)
    save_json(STATE_FILE, state)


def infer_next_series_day_from_outputs():
    """
    Reads generated metadata in outputs/ to infer the next challenge day.
    This is a backup only. Primary source is series_state.json.
    """
    import re

    if not os.path.isdir(OUTPUT_DIR):
        return None

    found_days = []

    patterns = [
        os.path.join(OUTPUT_DIR, "*_title.txt"),
        os.path.join(OUTPUT_DIR, "*_caption.txt"),
        os.path.join(OUTPUT_DIR, "*_script.txt"),
    ]

    for pattern in patterns:
        for path in glob.glob(pattern):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                matches = re.findall(r"\bDAY\s+(\d{1,2})\b|\bDay\s+(\d{1,2})\b", text)
                for a, b in matches:
                    value = a or b
                    if value:
                        day = int(value)
                        if 1 <= day <= 30:
                            found_days.append(day)
            except Exception:
                pass

    if not found_days:
        return None

    last_day = max(found_days)
    next_day = last_day + 1
    if next_day > 30:
        next_day = 1

    return next_day


def load_series_state():
    """
    v21 clean state logic.

    No run-number day guessing.
    If series_state.json exists, use it.
    If it does not exist, start at Day 2.
    After generation, auto_commit_state_files() must push Day 3 back to GitHub.
    """
    state_exists = os.path.exists(SERIES_STATE_FILE)

    data = safe_load_json(
        SERIES_STATE_FILE,
        {"next_day": SERIES_START_DAY, "initialized": False}
    )

    try:
        next_day = int(data.get("next_day", SERIES_START_DAY))
    except Exception:
        next_day = SERIES_START_DAY

    if next_day < 1 or next_day > 30:
        next_day = SERIES_START_DAY

    return {
        "next_day": next_day,
        "initialized": bool(data.get("initialized", False)),
        "source": "series_state_json" if state_exists else "default_day_2_no_state_file",
    }


def save_series_state(next_day):
    if next_day < 1 or next_day > 30:
        next_day = 1

    data = {
        "next_day": next_day,
        "initialized": True,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "note": "Auto-updated by generate.py so challenge reels stay sequential."
    }

    save_json(SERIES_STATE_FILE, data)
    return data


def advance_series_day(current_day):
    next_day = current_day + 1
    if next_day > 30:
        next_day = 1
    save_series_state(next_day)


def load_rotation_state():
    default = {
        "recent_line_keys": [],
        "recent_covers": [],
        "recent_categories": [],
        "recent_backgrounds": [],
        "background_cursor": {},
        "updated_at": ""
    }
    data = safe_load_json(ROTATION_STATE_FILE, default)
    for k, v in default.items():
        data.setdefault(k, v)
    return data


def save_rotation_state(data):
    data["updated_at"] = datetime.now().isoformat(timespec="seconds")
    save_json(ROTATION_STATE_FILE, data)


def auto_commit_state_files():
    """
    Commits state memory files back to GitHub.

    If this fails, the next workflow run cannot know the next day or next background.
    """
    if not AUTO_COMMIT_STATE:
        print("STATE COMMIT DISABLED.")
        return False

    files = [
        "series_state.json",
        "rotation_state.json",
        "used_lines_v3.json",
        "engine_state_v3.json",
        "hook_state.json",
    ]

    existing = [f for f in files if os.path.exists(os.path.join(BASE_DIR, f))]
    if not existing:
        print("STATE COMMIT: no state files found.")
        return False

    try:
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=BASE_DIR, check=False)
        subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], cwd=BASE_DIR, check=False)

        add = subprocess.run(
            ["git", "add"] + existing,
            cwd=BASE_DIR,
            text=True,
            capture_output=True,
            check=False,
        )
        print("STATE ADD:", add.stdout.strip() or add.stderr.strip() or "ok")

        status = subprocess.run(
            ["git", "status", "--porcelain"] + existing,
            cwd=BASE_DIR,
            text=True,
            capture_output=True,
            check=False,
        )

        if not status.stdout.strip():
            print("STATE COMMIT: no changes.")
            return True

        commit = subprocess.run(
            ["git", "commit", "-m", "Update generator state"],
            cwd=BASE_DIR,
            text=True,
            capture_output=True,
            check=False,
        )
        print("STATE COMMIT:", commit.stdout.strip() or commit.stderr.strip())

        if commit.returncode != 0:
            print("STATE ERROR: commit failed.")
            return False

        push = subprocess.run(
            ["git", "push"],
            cwd=BASE_DIR,
            text=True,
            capture_output=True,
            check=False,
        )

        print("STATE PUSH:", push.stdout.strip() or push.stderr.strip())
        print("STATE PUSH RETURN CODE:", push.returncode)

        if push.returncode != 0:
            print("STATE ERROR: GitHub did not save series_state.json or rotation_state.json.")
            print("FIX: Settings > Actions > General > Workflow permissions > Read and write permissions.")
            return False

        return True

    except Exception as e:
        print(f"STATE AUTO-COMMIT FAILED: {e}")
        return False


# ================================================================
# PACING
# ================================================================

PACING = {
    "controlled": {
        "line_pause": 0.18,
        "sentence_pause": 0.28,
        "voice_speed": 1.02,
        "min_line_duration": 1.35,
        "max_line_duration": 2.45,
        "subtitle_hold": 0.12,
    },

    "attack": {"rate": "-4%", "pitch": "-35Hz", "chunk_size": 2, "gap": 0.16},
    "story": {"rate": "-11%", "pitch": "-40Hz", "chunk_size": 3, "gap": 0.22},
    "cold": {"rate": "-15%", "pitch": "-45Hz", "chunk_size": 3, "gap": 0.25},
}


# ================================================================
# CONTENT
# ================================================================

HOOK_FORMULAS = {
    "silent_decay": [
        "Most men decay quietly.",
        "Nobody notices when discipline dies.",
        "Weak habits look harmless at first.",
        "You did not fall apart. You drifted.",
        "This is how men waste years.",
        "Your standards are disappearing slowly.",
        "You stopped leading yourself.",
        "The dangerous part is how normal this feels.",
        "You are not failing loudly. You are fading quietly.",
        "Weakness becomes normal before it becomes visible.",
        "Your life is not stuck. Your discipline is leaking.",
        "You are losing years in small compromises.",
    ],
    "identity_exposure": [
        "Your habits are telling the truth about you.",
        "Your routine exposed your real standard.",
        "Your private life is building your public result.",
        "You became reliable at breaking your own word.",
        "You are becoming the man your habits repeat.",
        "Your discipline disappeared before your results did.",
        "Your standards are lower than your goals.",
        "The man you are becoming is being built in private.",
        "Your excuses are starting to sound like identity.",
        "Your future is watching your routine.",
    ],
    "older_male_regret": [
        "A man can waste years and still call it waiting.",
        "You are old enough to know better now.",
        "At some point, excuses become embarrassing.",
        "The years do not warn you before they disappear.",
        "Most men wake up late to their own life.",
        "The cost of weak habits gets heavier with age.",
        "You cannot keep living like time is unlimited.",
        "One day, potential stops sounding impressive.",
        "You are not young enough to keep restarting forever.",
        "Regret starts as a routine you refused to fix.",
    ],
    "control_and_inputs": [
        "Your inputs are controlling your discipline.",
        "Your phone is training your weakness.",
        "Your attention is being spent before your day begins.",
        "You cannot build control while feeding distraction.",
        "Your routine is stronger than your intention.",
        "Your environment keeps voting against your future.",
        "Your discipline is only as strong as your system.",
        "Your mind follows what you keep consuming.",
        "Your distractions are shaping your identity.",
        "Your habits are not random. Your inputs built them.",
    ],
    "day7_pressure": [
        "Day 7 is where most people disappear.",
        "This is the part most people quit.",
        "The first week exposes the lie.",
        "By Day 7, your real routine shows up.",
        "Consistency does not fail loudly.",
        "Most people lose the standard before the challenge ends.",
        "Day 7 does not break people. It reveals them.",
        "This is where motivation stops protecting you.",
        "The routine always wins after the mood fades.",
        "Your structure gets tested when comfort returns.",
    ],
    "structure_truth": [
        "Discipline is not emotion. It is structure.",
        "Consistency is designed before it is repeated.",
        "Rules protect you when feelings change.",
        "A serious life requires serious systems.",
        "Structure does what motivation cannot.",
        "Your standard must survive your mood.",
        "Control returns when negotiation ends.",
        "Discipline is built before pressure arrives.",
        "Your future reflects your repeated systems.",
        "Private structure creates public change.",
    ],
}


CONTENT = {
    "wasted_potential": {
        "mood": "broken",
        "cover": ["YOU DRIFT", "STILL WEAK", "WASTED TIME", "NO STANDARD", "QUIET FAILURE", "WEAK HABITS", "SAME PATTERN", "COMFORT WON"],
        "problem": [
            "You wake up with plans and repeat the same private weakness.",
            "You know what to do, but you keep choosing the easiest option.",
            "You lowered your standards so many times they no longer feel low.",
            "Your life is not falling apart loudly. It is fading through small compromises.",
        ],
        "mirror": [
            "And the worst part is, you can feel it.",
            "Nobody has to tell you. You already know.",
            "That shame is your standard trying to come back.",
            "Deep down, you know this version of you is not enough.",
        ],
        "consequence": [
            "If you keep moving like this, five years will disappear and nothing will change.",
            "Comfort is collecting interest from your future every day.",
            "Every weak decision becomes a vote for the man you hate becoming.",
            "You are not just wasting time. You are becoming easier to control.",
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
        "cover": ["OWN MORNING", "WAKE UP", "FIRST BATTLE", "NO SNOOZE", "WIN EARLY", "PHONE FIRST", "WEAK MORNING", "FIRST HOUR"],
        "problem": [
            "You wake up late, rush everything, and call the day stressful.",
            "You give your best energy to comfort, then give leftovers to your goals.",
            "Your phone gets your first attention. Your future gets the leftovers.",
            "You do not need a better life first. You need a better first hour.",
        ],
        "mirror": [
            "Every morning tells the truth before your mouth can lie.",
            "Nobody claps for the morning win. That is why it matters.",
            "The man you become is built before anyone sees the result.",
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
        "cover": ["BE THE MAN", "RAISE STANDARD", "NO EXCUSES", "LEAD YOURSELF", "REAL MAN", "LOW STANDARD", "CONTROL YOURSELF", "PRIVATE PROOF"],
        "problem": [
            "You say you want to lead, but you cannot keep a promise to yourself.",
            "You confuse anger with strength and comfort with peace.",
            "You are physically present but mentally absent where it matters.",
            "You want the respect of a man without the private discipline of one.",
        ],
        "mirror": [
            "Your actions are your real reputation.",
            "A standard is not what you post. It is what you refuse to break.",
            "Your word to yourself is either building you or destroying you.",
            "Every man is measured by what he does when it is inconvenient.",
        ],
        "consequence": [
            "If you cannot govern yourself, the world will govern you.",
            "A weak standard never stays private. It leaks into everything.",
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
        "cover": ["STOP ALONE", "30 DAYS", "JOIN NOW", "NO HIDING", "REAL ACCOUNTABILITY", "NO CONSEQUENCE", "PRIVATE PROMISES", "VISIBLE STANDARD"],
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

MEMBER_CONTENT = {
    "member_accountability": {
        "mood": "challenge",
        "cover": ["MEMBERS ONLY", "NO HIDING", "REAL PRESSURE", "JOIN THE ROOM", "STOP ALONE"],
        "lines": [
            [
                "Nobody notices when you disappear.",
                "That is why most people stay weak.",
                "Inside the challenge, the standard stays visible.",
                "Daily check-ins. Real accountability. No private hiding.",
                "Members unlock the Discipline Manual inside the group.",
            ],
            [
                "You keep restarting because there is no consequence.",
                "Private promises are too easy to break.",
                "The challenge gives you pressure before motivation dies.",
                "The manual is inside the group. The work starts after you join.",
                "Join the Inner Discipline Challenge. Link in bio.",
            ],
        ],
    },
    "ebook_bait": {
        "mood": "rebuild",
        "cover": ["THE MANUAL", "PRIVATE MANUAL", "INSIDE ONLY", "DISCIPLINE MANUAL"],
        "lines": [
            [
                "This is not extra content.",
                "It is the first weapon inside the group.",
                "The Discipline Manual gives you the rules.",
                "The group gives you the pressure.",
                "Members unlock it after joining.",
            ],
            [
                "The public reels expose the problem.",
                "The group creates accountability.",
                "The manual gives the structure.",
                "That is the system.",
                "Members get access inside.",
            ],
        ],
    },
}


DAY7_CONTENT = {
    "day7_consistency": {
        "mood": "challenge",
        "cover": [
            "DAY 7",
            "MOST QUIT",
            "QUIET DRIFT",
            "WEAK ROUTINE",
            "STOP RESETTING",
            "MOOD FADED",
            "SYSTEMS STAY",
            "STANDARD TEST",
        ],
        "scripts": [
            ["Day 7 is where most people disappear.", "The goal did not change.", "Their structure did.", "That is the truth."],
            ["You keep restarting your life every Monday.", "By Day 7, the pattern returns.", "Same habits.", "Same result."],
            ["Day 7 does not break people.", "It reveals the routine.", "Weak structure collapses.", "Strong standards stay."],
            ["Most people do not quit loudly.", "They miss one day.", "Then they stop correcting themselves.", "That is how discipline dies."],
            ["Motivation fades first.", "Then your system gets tested.", "If there is no structure.", "Comfort takes control."],
            ["The first week exposes your standard.", "Not your goals.", "Not your plans.", "Your real standard."],
            ["You are not tired.", "You are overstimulated.", "Your attention is scattered.", "Your discipline follows."],
            ["The weak version waits for Day 7.", "Then it asks for one exception.", "One exception becomes identity.", "That is the cost."],
            ["Your future is not waiting for motivation.", "It is waiting for proof.", "Repeated proof.", "Daily proof."],
            ["If discipline disappears by Day 7.", "Do not blame pressure.", "Look at your habits.", "They were never aligned."],
        ],
    }
}

SERIES_TASK_INTROS = [
    "Your task is simple.",
    "Todayâ€™s rule is simple.",
    "The work is simple.",
    "Your standard today is simple.",
    "Do this without negotiation.",
]

SERIES_STANDARD_LINES = [
    "Do not negotiate with the weak version of you.",
    "Do not let comfort rewrite the rule.",
    "Keep the standard when the mood changes.",
    "The task is small. The standard is not.",
    "This is where discipline becomes identity.",
]

SERIES_DONE_LINES = [
    "Comment DONE when you finish it.",
    "Comment DONE when the task is complete.",
    "Finish it, then comment DONE.",
    "Complete the task before you speak.",
    "Let the action come first.",
]

VIRAL_RETENTION_BANK = {
    "mirror": {
        "mood": "dangerous",
        "cover_style": "mirror",
        "covers": [
            "YOU KNOW THIS ALREADY", "YOU FELT THE WARNING", "YOU KEEP NEGOTIATING",
            "YOU'RE NOT CONFUSED", "YOU KNOW WHAT TO DO", "THE STANDARD SLIPPED",
            "YOU WATCHED IT HAPPEN", "YOU CALLED IT TOMORROW", "YOU SAW IT COMING",
            "YOU KEEP EXPLAINING", "YOU FELT THAT DROP", "YOU BROKE IT QUIETLY",
            "YOU LET IT SLIDE", "YOU KNOW THE PATTERN", "YOU'RE AVOIDING IT",
            "YOU SAID TOMORROW",
        ],
        "scripts": [
            ["YOU KNOW THIS ALREADY.", "The problem is not information.", "You already saw the habit.", "You already felt the warning.", "You already knew the cost.", "The real problem is obedience.", "When comfort gets loud."],
            ["YOU FELT THE WARNING.", "Before the result changed.", "Before anyone noticed.", "Before the habit looked serious.", "Something in you knew.", "That was not random.", "That was the signal."],
            ["YOU KEEP NEGOTIATING.", "With the same standard.", "You already decided.", "Then the mood changed.", "Then the excuse sounded reasonable.", "Then the result stayed familiar.", "That is the pattern."],
            ["YOU'RE NOT CONFUSED.", "You know what needs to change.", "You know what keeps costing you.", "The hard part is not knowing.", "It is obeying the truth.", "When comfort argues back.", "That is discipline."],
            ["YOU KNOW WHAT TO DO.", "That is why it bothers you.", "Not because life is unclear.", "Not because the answer is hidden.", "Because the standard is clear.", "And you keep letting mood vote.", "That has to stop."],
            ["THE STANDARD SLIPPED.", "Not in one big failure.", "Not where people could see it.", "It slipped in small private choices.", "One exception.", "Then another.", "Until it felt normal."],
            ["YOU WATCHED IT HAPPEN.", "The routine got weaker.", "The excuses got easier.", "The standard moved lower.", "And you called it temporary.", "Until temporary became normal.", "That is how drift wins."],
            ["YOU CALLED IT TOMORROW.", "Again.", "Then tomorrow became a pattern.", "Then the pattern became proof.", "The problem is not time.", "It is the standard.", "That keeps moving."],
            ["YOU SAW IT COMING.", "The warning was there.", "The drop was there.", "The old habit was there.", "You did not lack clarity.", "You delayed the truth.", "Until the result spoke."],
            ["YOU KEEP EXPLAINING.", "The same pattern.", "With better words.", "You can make the excuse sound intelligent.", "But the routine still knows.", "What really happened.", "So do you."],
            ["YOU FELT THAT DROP.", "That small loss of respect.", "After you broke your word.", "After you chose comfort.", "After you said tomorrow again.", "That feeling was feedback.", "Not weakness."],
            ["YOU BROKE IT QUIETLY.", "Not your life.", "Not all at once.", "You broke your word first.", "Then your standard.", "Then your trust in yourself.", "That is the real cost."],
            ["YOU LET IT SLIDE.", "Once.", "Then again.", "Then it stopped feeling wrong.", "Then the habit got stronger.", "Then the standard got weaker.", "That is how it happens."],
            ["YOU KNOW THE PATTERN.", "Strong start.", "Private compromise.", "Silent guilt.", "Another explanation.", "Another restart.", "Same routine."],
            ["YOU'RE AVOIDING IT.", "Not because it is impossible.", "Because it demands proof.", "And proof removes excuses.", "That is why it feels heavy.", "But that is also why it works.", "Start there."],
            ["YOU SAID TOMORROW.", "Again.", "Then again.", "The problem is not time.", "The problem is not knowledge.", "The problem is the standard.", "That keeps moving."],
        ],
    },
    "mirror_two_stage": {
        "mood": "broken",
        "cover_style": "mirror",
        "covers": [
            "THE HARDEST PART", "THE MOMENT YOU STOP", "THIS IS THE PART",
            "THE REAL PROBLEM", "THE PART YOU AVOID", "WHERE IT BREAKS",
            "THIS IS WHY", "THE QUIET TRUTH", "THE FIRST CRACK", "THE REAL TEST",
        ],
        "scripts": [
            ["THE HARDEST PART.", "Is not starting.", "Starting feels good.", "Starting gives you hope.", "The hardest part is continuing.", "When nobody is watching.", "And no mood is helping."],
            ["THE MOMENT YOU STOP.", "Lying to yourself.", "Is the moment things change.", "Not because life gets easier.", "But because the excuse loses power.", "And the standard becomes visible.", "That is where control begins."],
            ["THIS IS THE PART.", "Most people avoid.", "They want the result.", "They want the identity.", "They want the respect.", "But not the standard.", "That creates all of it."],
            ["THE REAL PROBLEM.", "Is not lack of motivation.", "Motivation comes and goes.", "The real problem is the routine.", "You keep protecting.", "With excuses.", "That sound reasonable."],
            ["THE PART YOU AVOID.", "Is the part that changes you.", "Not the plan.", "Not the quote.", "Not the announcement.", "The proof.", "Repeated quietly."],
            ["WHERE IT BREAKS.", "Is not the goal.", "It is the private choice.", "After the emotion fades.", "After nobody is watching.", "After comfort starts talking.", "That is the test."],
            ["THIS IS WHY.", "You keep restarting.", "The emotion comes back.", "The plan looks new.", "The promise sounds serious.", "But the system never changed.", "So the pattern returns."],
            ["THE QUIET TRUTH.", "Nobody has to see it.", "For it to matter.", "Nobody has to clap.", "For it to count.", "Your future still records it.", "Every time."],
            ["THE FIRST CRACK.", "Is not failure.", "It is permission.", "One excuse.", "One lowered standard.", "One compromise.", "You stop challenging."],
            ["THE REAL TEST.", "Is not the beginning.", "It is the repetition.", "After the mood fades.", "After comfort speaks.", "After nobody is watching.", "That is where identity forms."],
        ],
    },
    "identity": {
        "mood": "dangerous",
        "cover_style": "identity",
        "covers": ["NO ONE IS COMING", "DISCIPLINE IS FREEDOM", "MOST PEOPLE QUIT HERE", "WHO ARE YOU", "RESULTS DON'T LIE", "PRIVATE PROOF", "THE EXCUSE WON", "THE TRUTH SHOWED"],
        "scripts": [
            ["NO ONE IS COMING.", "Not to fix your habits.", "Not to rescue your standards.", "Not to force your discipline.", "Not to save your routine.", "You move first.", "That is the standard."],
            ["DISCIPLINE IS FREEDOM.", "Not because it feels easy.", "Because it removes the chaos.", "That weak choices create.", "It gives your life structure.", "When emotion keeps changing.", "That is freedom."],
            ["MOST PEOPLE QUIT HERE.", "Not at failure.", "Not at the final loss.", "They quit at discomfort.", "Before the work gets real.", "Before the standard is proven.", "That is the line."],
            ["WHO ARE YOU.", "When nobody is watching.", "When the mood leaves.", "When comfort calls.", "When the excuse sounds reasonable.", "That is the real answer.", "Not the speech."],
            ["RESULTS DON'T LIE.", "They repeat back.", "The private habits.", "You practiced quietly.", "The things nobody saw.", "The choices you allowed.", "That is the truth."],
            ["PRIVATE PROOF MATTERS.", "Nobody saw the choice.", "Nobody clapped.", "Nobody rewarded it.", "But your future felt it.", "Your identity felt it.", "Every time."],
            ["THE EXCUSE WON.", "Not because it was true.", "Because you let it speak louder.", "Than your standard.", "Then you protected it.", "Then you repeated it.", "That is the loss."],
            ["THE TRUTH SHOWED.", "Not in your words.", "Not in your plans.", "In your routine.", "In what you repeated.", "In what you allowed.", "Every day."],
        ],
    },
    "consequence": {
        "mood": "broken",
        "cover_style": "consequence",
        "covers": ["LATER GETS EXPENSIVE", "YEARS DISAPPEAR", "THE DAMAGE GROWS", "THE BILL ARRIVES", "NOTHING STAYS SMALL", "WEAKNESS COMPOUNDS", "EXCUSES HAVE INTEREST", "TIME DOES NOT WAIT"],
        "scripts": [
            ["LATER GETS EXPENSIVE.", "Most people miss the cost.", "Because it does not arrive immediately.", "It arrives as a pattern.", "Then as a result.", "Then as a life.", "That is why today matters."],
            ["YEARS DISAPPEAR.", "Not all at once.", "One repeated excuse.", "One delayed decision.", "One weak routine.", "One lowered standard.", "Until it becomes normal."],
            ["THE DAMAGE GROWS.", "When you keep excusing it.", "Small habits become normal.", "Normal becomes identity.", "Identity becomes results.", "Then you call it life.", "That is the danger."],
            ["THE BILL ARRIVES.", "For every habit you ignored.", "For every standard you lowered.", "For every promise you delayed.", "Nothing stays free.", "Not even comfort.", "Not forever."],
            ["NOTHING STAYS SMALL.", "Not the excuse.", "Not the delay.", "Not the habit.", "Not the compromise.", "If you keep feeding it.", "It grows."],
            ["WEAKNESS COMPOUNDS.", "First in private.", "Then in routine.", "Then in identity.", "Then in results.", "Then in regret.", "That is the sequence."],
            ["EXCUSES HAVE INTEREST.", "They feel harmless now.", "Then they charge your future.", "One repeated delay.", "One weak decision.", "One comfortable lie.", "At a time."],
            ["TIME DOES NOT WAIT.", "Your mood can change tomorrow.", "Your plan can improve tomorrow.", "But today still counts.", "So does every excuse.", "So does every choice.", "That is the truth."],
        ],
    },
    "standards": {
        "mood": "dangerous",
        "cover_style": "standards",
        "covers": ["THE STANDARD MOVED", "YOU LOWERED IT", "THE BAR DROPPED", "DECIDE ONCE", "NO NEGOTIATION", "STANDARD OVER MOOD"],
        "scripts": [
            ["THE STANDARD MOVED.", "Not because life changed.", "Because the mood changed.", "Then the excuse got louder.", "Then the standard got softer.", "That is the problem.", "Fix the standard."],
            ["YOU LOWERED IT.", "Quietly.", "One exception at a time.", "Until weakness felt normal.", "Until discipline felt optional.", "Until the result made sense.", "That is how standards die."],
            ["THE BAR DROPPED.", "Not in one big failure.", "In the small private choices.", "You stopped correcting.", "You stopped noticing.", "You stopped caring enough.", "That is where it happened."],
            ["DECIDE ONCE.", "Stop reopening the same battle.", "Every time your mood changes.", "A standard is not a discussion.", "It is a decision.", "Repeated under pressure.", "That is control."],
            ["NO NEGOTIATION.", "The standard is the decision.", "The mood is just noise.", "The excuse is just pressure.", "The routine is the proof.", "Move anyway.", "That is discipline."],
            ["STANDARD OVER MOOD.", "Because mood changes.", "Because pressure changes.", "Because comfort lies.", "Your life cannot depend.", "On unstable emotion.", "The standard must survive."],
        ],
    },
}



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
    {"day": 29, "title": "FINAL PUSH", "mood": "challenge", "task": "Do not coast because the finish is close.", "pain": "Most people quit mentally before they quit physically."},
    {"day": 30, "title": "NEW IDENTITY", "mood": "rebuild", "task": "Choose the standard you will carry forward.", "pain": "Thirty days means nothing if you return to the old version."},
]


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
    ebook_image: str = ""



# ================================================================
# HOOK STATE + RETENTION SCORING
# ================================================================

def load_hook_state():
    default = {"recent_hooks": [], "winning_hook_types": {}, "updated_at": ""}
    data = safe_load_json(HOOK_STATE_FILE, default)
    for k, v in default.items():
        data.setdefault(k, v)
    return data


def save_hook_state(data):
    data["updated_at"] = datetime.now().isoformat(timespec="seconds")
    save_json(HOOK_STATE_FILE, data)


def remember_hook(hook):
    data = load_hook_state()
    items = data.get("recent_hooks", [])
    key = line_key(hook)
    if key in items:
        items.remove(key)
    items.insert(0, key)
    data["recent_hooks"] = items[:40]
    save_hook_state(data)


def hook_available(pool):
    recent = set(load_hook_state().get("recent_hooks", [])[:12])
    candidates = [h for h in pool if line_key(h) not in recent]
    return candidates if candidates else pool[:]


def contains_banned_phrase(text):
    low = text.lower()
    return any(bad in low for bad in BANNED_PHRASES)


def tension_word_count(text):
    words = [
        "weak", "weakness", "stuck", "quit", "control", "pressure", "drift",
        "standards", "habits", "routine", "comfort", "discipline", "exposing",
        "identity", "lost", "consistent", "consequence", "structure",
        "negotiation", "future", "private", "truth",
    ]
    low = text.lower()
    return sum(1 for w in words if w in low)


def core_topic_count(text):
    low = text.lower()
    return sum(1 for topic in CORE_TOPICS if topic in low)


def score_script(script):
    joined = " ".join(script.lines)
    hook = script.lines[0] if script.lines else ""
    score = 0

    hook_words = len(hook.split())
    if hook_words <= 8:
        score += 2
    if tension_word_count(hook) >= 1:
        score += 2
    if any(x in hook.lower() for x in ["you", "your", "most people", "most men", "this is why"]):
        score += 2

    if tension_word_count(joined) >= 4:
        score += 2
    if core_topic_count(joined) >= 2:
        score += 2

    # older_male_regret_score_boost
    if any(x in joined.lower() for x in ["years", "regret", "private", "quietly", "silence", "standard"]):
        score += 2

    if any(x in joined.lower() for x in ["remember this", "come back", "most men understand"]):
        score += 1

    lengths = [len(x.split()) for x in script.lines]
    if lengths and min(lengths) <= 4 and max(lengths) >= 7:
        score += 1
    if len(script.lines) in [4, 5]:
        score += 1

    final_line = script.lines[-1] if script.lines else ""
    if tension_word_count(final_line) >= 1 or core_topic_count(final_line) >= 1:
        score += 1

    if any(contains_banned_phrase(x) for x in script.lines):
        score -= 5
    if hook_words > 12:
        score -= 2
    if len(set(line_key(x) for x in script.lines)) != len(script.lines):
        score -= 2

    return score


def apply_retention_ending(lines):
    if random.random() < 0.55:
        lines = list(lines)
        lines[-1] = pick_unique_rotated(RETENTION_ENDING_LINES)
    return lines


def rhythm_refine(lines):
    refined = [clean_text(x) for x in lines if clean_text(x)]
    if len(refined) > 5:
        refined = refined[:5]
    refined = [x for x in refined if not contains_banned_phrase(x)]
    if refined and len(refined[-1].split()) > 12:
        refined[-1] = pick_unique_rotated(RETENTION_ENDING_LINES)
    return refined



def maybe_add_save_share_signal(script):
    """
    Adds subtle save/share psychology without sounding needy.
    No spoken CTA. Lines are built to feel worth saving or sending.
    """
    if script.mode not in ["regular", "day7"]:
        return script

    save_lines = [
        "Remember this when the mood disappears.",
        "This is the line most people ignore.",
        "Save the standard before the feeling fades.",
        "This is the part your routine keeps exposing.",
        "Come back to this when comfort starts talking.",
    ]

    share_lines = [
        "Some men need to hear this quietly.",
        "This is the truth most people avoid.",
        "Someone is drifting and calling it patience.",
        "Most men understand this too late.",
        "This is why discipline dies in silence.",
    ]

    lines = list(script.lines)

    if random.random() < SAVE_SIGNAL_PROBABILITY and len(lines) >= 4:
        lines[-1] = pick_unique_rotated(save_lines)

    if random.random() < SHARE_SIGNAL_PROBABILITY and len(lines) >= 4:
        lines[-2] = pick_unique_rotated(share_lines)

    script.lines = rhythm_refine(lines)
    return script


def enforce_retention_quality(script, max_attempts=8):
    best = script
    best_score = score_script(script)

    for _ in range(max_attempts):
        if best_score >= MIN_RETENTION_SCORE:
            break

        candidate = build_regular_script_raw()
        candidate_score = score_script(candidate)
        if candidate_score > best_score:
            best = candidate
            best_score = candidate_score

    print("RETENTION SCORE:", best_score)
    if best_score < MIN_RETENTION_SCORE:
        print("RETENTION WARNING: accepted best available script, but score is below target.")
    return best


# ================================================================
# TEXT UTILS / ROTATION
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


def line_key(text):
    return clean_text(text).lower().strip()


def remember_rotation_item(key, value, max_items=80):
    data = load_rotation_state()
    items = data.get(key, [])
    if value in items:
        items.remove(value)
    items.insert(0, value)
    data[key] = items[:max_items]
    save_rotation_state(data)


def pick_unique_rotated(pool, memory_key="recent_line_keys", max_recent=RECENT_LINE_BLOCK):
    data = load_rotation_state()
    recent = set(data.get(memory_key, [])[:max_recent])

    candidates = [x for x in pool if line_key(x) not in recent]
    if not candidates:
        candidates = pool[:]

    choice = random.choice(candidates)
    remember_rotation_item(memory_key, line_key(choice), max_recent)
    return choice


def pick_cover_rotated(pool):
    data = load_rotation_state()
    recent = set(data.get("recent_covers", [])[:20])
    candidates = [x for x in pool if x not in recent]
    if not candidates:
        candidates = pool[:]
    choice = random.choice(candidates)
    remember_rotation_item("recent_covers", choice, 30)
    return choice


def pick_category_rotated():
    data = load_rotation_state()
    recent = data.get("recent_categories", [])[:3]
    weights = []
    for cat in CATEGORY_ORDER:
        if recent and cat == recent[0]:
            weights.append(0.05)
        elif cat in recent:
            weights.append(0.25)
        else:
            weights.append(1.0)
    choice = random.choices(CATEGORY_ORDER, weights=weights, k=1)[0]
    remember_rotation_item("recent_categories", choice, 20)
    return choice


def pick_hook():
    """
    v14 Next Evolution hook engine.
    Built from analytics: older male audience, non-follower reach, comment-heavy response.
    Prioritizes silent decay, identity exposure, wasted years, and structure.
    """
    keys = list(HOOK_FORMULAS.keys())
    weights = [0.24, 0.20, 0.18, 0.14, 0.12, 0.12]
    hook_type = random.choices(keys, weights=weights, k=1)[0]
    pool = hook_available(HOOK_FORMULAS[hook_type])
    hook = pick_unique_rotated(pool)
    remember_hook(hook)
    print("HOOK TYPE:", hook_type)
    print("HOOK:", hook)
    return hook

def get_recent_generated_categories(limit=20):
    return load_rotation_state().get("recent_categories", [])[:limit]


# ================================================================
# SCRIPT BUILDERS
# ================================================================

def build_regular_script_raw():
    category = pick_category_rotated()
    bank = CONTENT[category]
    pacing = random.choices(["attack", "story", "cold"], weights=[0.60, 0.28, 0.12], k=1)[0]

    lines = [
        pick_hook(),
        pick_unique_rotated(bank["problem"]),
        pick_unique_rotated(bank["mirror"]),
        pick_unique_rotated(bank["consequence"]),
        pick_unique_rotated(bank["cta"]),
    ]

    lines = apply_retention_ending(lines)
    lines = rhythm_refine(lines)

    cover = pick_cover_rotated(bank["cover"])

    return Script(
        mode="regular",
        category=category,
        mood=bank["mood"],
        cover=cover,
        title=f"{cover} | INNER DISCIPLINE",
        pacing=pacing,
        lines=lines,
    )



def build_regular_script():
    script = build_regular_script_raw()
    return enforce_retention_quality(script)


def build_member_script():
    key = random.choice(list(MEMBER_CONTENT.keys()))
    bank = MEMBER_CONTENT[key]

    options = bank["lines"]
    full_options = [" | ".join(x) for x in options]
    selected_key = pick_unique_rotated(full_options)
    selected_index = full_options.index(selected_key) if selected_key in full_options else 0
    lines = list(options[selected_index])

    cover = pick_cover_rotated(bank["cover"])

    return Script(
        mode="member",
        category=key,
        mood=bank["mood"],
        cover=cover,
        title=f"{cover} | INNER DISCIPLINE",
        pacing=random.choice(["attack", "story"]),
        lines=lines,
    )



def build_day7_script():
    """
    Calm, serious Day 7 Challenge lane.
    Short 7-9 second style scripts.
    No spoken CTA. No hype.
    """
    bank = DAY7_CONTENT["day7_consistency"]

    script_options = bank["scripts"]
    full_options = [" | ".join(x) for x in script_options]
    selected_key = pick_unique_rotated(full_options)
    selected_index = full_options.index(selected_key) if selected_key in full_options else 0
    lines = list(script_options[selected_index])

    cover = pick_cover_rotated(bank["cover"])

    remember_rotation_item("recent_categories", "day7_consistency", 20)

    return Script(
        mode="day7",
        category="day7_consistency",
        mood=bank["mood"],
        cover=cover,
        title=f"{cover} | INNER DISCIPLINE DAY 7 CHALLENGE",
        pacing="cold",
        lines=lines,
    )


def build_retention_reel_script():
    """
    v30.1 FULLSCREEN RETENTION MIRROR ENGINE.

    Meta signal:
    - Best length is now 15-30 seconds.
    - View completion rate is the bottleneck.
    - Bordered videos are being flagged.
    - Winning posts are self-confrontation posts.
    """
    categories = list(VIRAL_RETENTION_BANK.keys())

    weights_by_category = {
        "mirror": 0.45,
        "mirror_two_stage": 0.25,
        "identity": 0.15,
        "consequence": 0.10,
        "standards": 0.05,
    }

    weights = [weights_by_category.get(c, 0.0) for c in categories]
    if sum(weights) <= 0:
        weights = [1 for _ in categories]

    category = random.choices(categories, weights=weights, k=1)[0]

    bank = VIRAL_RETENTION_BANK[category]
    script_options = bank["scripts"]
    script_keys = [" | ".join(x) for x in script_options]

    selected_key = pick_unique_rotated(
        script_keys,
        memory_key="recent_fullscreen_mirror_scripts_v30_1",
        max_recent=300,
    )

    selected_index = script_keys.index(selected_key) if selected_key in script_keys else 0
    lines = list(script_options[selected_index])
    lines = rhythm_refine(lines)

    if len(lines) > RETENTION_LINE_COUNT_MAX:
        lines = lines[:RETENTION_LINE_COUNT_MAX]

    while len(lines) < RETENTION_LINE_COUNT_MIN:
        lines.append(
            pick_unique_rotated(
                RETENTION_ENDING_LINES,
                memory_key="recent_fullscreen_mirror_endings_v30_1",
                max_recent=160,
            )
        )

    cover = pick_unique_rotated(
        bank["covers"],
        memory_key="recent_fullscreen_mirror_covers_v30_1",
        max_recent=260,
    )

    remember_rotation_item("recent_categories", category, 160)

    print("V30.1 CATEGORY:", category)
    print("V30.1 COVER STYLE:", bank.get("cover_style", "default"))
    print("V30.1 COVER:", cover)
    print("V30.1 SCRIPT:", " | ".join(lines))

    return Script(
        mode="fullscreen_mirror_engine",
        category=category,
        mood=bank["mood"],
        cover=cover,
        title=f"{cover} | INNER DISCIPLINE",
        pacing="cold",
        lines=lines,
    )



def build_series_script():
    """
    v19 clean sequential challenge generator.
    No random jumps.
    No mixed reels.
    Uses series_state.json first.
    Starts at Day 2 only if no real state exists.
    """
    series_data = load_series_state()
    print("SERIES STATE SOURCE:", series_data.get("source", "unknown"))

    day = int(series_data.get("next_day", SERIES_START_DAY))

    if day < 1 or day > 30:
        day = SERIES_START_DAY

    episode = SERIES_EPISODES[day - 1]

    intro = pick_unique_rotated(SERIES_TASK_INTROS, memory_key="recent_series_intros", max_recent=10)
    standard_line = pick_unique_rotated(SERIES_STANDARD_LINES, memory_key="recent_series_standards", max_recent=10)
    done_line = pick_unique_rotated(SERIES_DONE_LINES, memory_key="recent_series_done_lines", max_recent=10)

    lines = [
        f"Day {episode['day']} of 30. {episode['title']}.",
        episode["pain"],
        f"{intro} {episode['task']}",
        standard_line,
        done_line,
    ]

    script = Script(
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

    advance_series_day(day)

    print("SERIES DAY SELECTED:", day)
    print("SERIES NEXT DAY SAVED:", load_series_state().get("next_day"))

    return script


def should_make_series():
    """
    v30.1: public reels do not use the Day system.
    """
    return False


def build_script():
    """
    v30.1 FULLSCREEN RETENTION MIRROR ENGINE.

    No Day system.
    No challenge sequence.
    No ebook overlay.
    No bordered/panel-style public reels.

    Built for 18-22 second full-screen Mirror Engine reels.
    """
    return build_retention_reel_script()


# ================================================================
# BACKGROUNDS
# ================================================================

VIDEO_EXTENSIONS = ["*.mp4", "*.MP4", "*.mov", "*.MOV"]


def scan_video_files(folder):
    files = []
    for ext in VIDEO_EXTENSIONS:
        files.extend(glob.glob(os.path.join(folder, ext)))
    return sorted(list(set(files)))


def root_bg_files():
    files = []
    for pattern in ["bg*.mp4", "bg*.MP4", "bg*.mov", "bg*.MOV"]:
        files.extend(glob.glob(os.path.join(BASE_DIR, pattern)))
    return sorted(list(set(files)))


def get_background_pool(mood=None):
    """
    v15 global background pool.
    Scans every background folder so the engine rotates all 15-20 clips,
    instead of getting trapped inside one mood folder.
    """
    pool = []

    if os.path.isdir(BG_ROOT):
        for folder, _, _ in os.walk(BG_ROOT):
            pool.extend(scan_video_files(folder))

    pool.extend(root_bg_files())

    return sorted(list(set(pool)))



def folder_video_pool(folder_name):
    folder = os.path.join(BG_ROOT, folder_name)
    if not os.path.isdir(folder):
        return []
    return scan_video_files(folder)


def score_scene_folder(script, folder_name):
    """
    Scores how strongly the script matches a background folder.
    Higher score = better visual meaning match.
    """
    text = " ".join([
        str(script.mode),
        str(script.category),
        str(script.mood),
        str(script.cover),
        str(script.title),
        " ".join(script.lines),
        str(script.task),
    ]).lower()

    score = 0

    # Mood from the episode is the strongest signal.
    if script.mood == folder_name:
        score += 12

    # Series task/title keywords.
    for kw in SCENE_KEYWORDS.get(folder_name, []):
        if kw in text:
            score += 3

    # Extra specific rules for the 30-day sequence.
    if script.mode == "series":
        if any(x in text for x in ["snooze", "phone", "first hour", "wake", "alarm"]):
            if folder_name == "morning":
                score += 10

        if any(x in text for x in ["train", "stairs", "conditioning", "pressure", "craving", "body"]):
            if folder_name == "dangerous":
                score += 10

        if any(x in text for x in ["clean", "bed", "space", "reset", "fix", "work", "prepare"]):
            if folder_name == "rebuild":
                score += 10

        if any(x in text for x in ["journal", "truth", "mirror", "alone", "conversation", "avoid"]):
            if folder_name == "broken":
                score += 10

        if any(x in text for x in ["done", "challenge", "report back", "day "]):
            if folder_name == "challenge":
                score += 4

    return score


def choose_scene_folder(script):
    """
    Chooses the best folder based on what is being said.
    Not random. Meaning first, rotation second.
    """
    available_folders = []
    for folder in ["broken", "morning", "dangerous", "rebuild", "challenge", "generic"]:
        if folder_video_pool(folder):
            available_folders.append(folder)

    if not available_folders:
        return None, []

    scored = []
    for folder in available_folders:
        scored.append((score_scene_folder(script, folder), folder))

    scored.sort(reverse=True)
    best_score, best_folder = scored[0]

    if best_score <= 0 and "generic" in available_folders:
        best_folder = "generic"

    # Fallback chain keeps meaning close before going fully global.
    fallback_order = [best_folder]
    for folder in [script.mood, "challenge", "generic", "broken", "rebuild", "dangerous", "morning"]:
        if folder in available_folders and folder not in fallback_order:
            fallback_order.append(folder)

    print("SCENE FOLDER SCORES:", scored)
    print("SCENE SELECTED FOLDER:", best_folder)

    return best_folder, fallback_order


def choose_background_from_pool(pool, rotation_key):
    """
    Rotates inside the selected scene folder.

    Meaning match stays intact.
    The clip changes only inside the matching folder.
    """
    if not pool:
        return None

    pool_sorted = sorted(list(set(pool)))
    data = load_rotation_state()
    cursor = data.get("background_cursor", {})
    recent_bg = data.get("recent_backgrounds", [])[:RECENT_BACKGROUND_BLOCK]

    start_index = int(cursor.get(rotation_key, 0)) % len(pool_sorted)
    chosen = None
    chosen_index = start_index

    for offset in range(len(pool_sorted)):
        idx = (start_index + offset) % len(pool_sorted)
        candidate = pool_sorted[idx]
        if candidate not in recent_bg:
            chosen = candidate
            chosen_index = idx
            break

    if chosen is None:
        chosen = pool_sorted[start_index]
        chosen_index = start_index

    cursor[rotation_key] = (chosen_index + 1) % len(pool_sorted)
    data["background_cursor"] = cursor

    if chosen in recent_bg:
        recent_bg.remove(chosen)
    recent_bg.insert(0, chosen)
    data["recent_backgrounds"] = recent_bg[:max(RECENT_BACKGROUND_BLOCK, 20)]

    save_rotation_state(data)

    print("BACKGROUND ROTATION KEY:", rotation_key)
    print("BACKGROUND ROTATION INDEX:", chosen_index)
    print("SELECTED BACKGROUND:", chosen)

    return chosen


def choose_background_for_script(script):
    """
    Scene-matched background selector.

    Step 1: read the script meaning.
    Step 2: choose the best matching folder.
    Step 3: rotate inside that folder.
    Step 4: only fallback if that folder is empty.

    This replaces blind/random background choice.
    """
    if not SCENE_MATCHING_ENABLED:
        return choose_background_rotated(script.mood)

    selected_folder, fallback_order = choose_scene_folder(script)

    print("REQUESTED MOOD:", script.mood)
    print("BACKGROUND FALLBACK ORDER:", fallback_order)

    for folder in fallback_order:
        pool = folder_video_pool(folder)
        if pool:
            print("BACKGROUND MATCHED FOLDER:", folder)
            print("MATCHED FOLDER POOL:", pool)
            chosen = choose_background_from_pool(pool, f"scene_{folder}")
            if chosen:
                return chosen

    # Last emergency fallback: all backgrounds.
    pool = get_background_pool(script.mood)
    print("BACKGROUND EMERGENCY GLOBAL POOL:", pool)
    chosen = choose_background_from_pool(pool, "scene_global")
    if chosen:
        return chosen

    raise Exception("No background videos found.")

def choose_background_rotated(mood=None):
    """
    v19 true background rotation.

    Uses the full background library across all folders.
    If GitHub state does not persist, GITHUB_RUN_NUMBER still rotates backgrounds.
    This prevents the engine from getting stuck on only 2 clips.
    """
    pool = get_background_pool(mood)

    print("BASE DIR:", BASE_DIR)
    print("BG ROOT:", BG_ROOT)
    print("REQUESTED MOOD:", mood)
    print("TOTAL BACKGROUNDS FOUND:", len(pool))
    print("BACKGROUND POOL FOUND:", pool)

    if not pool:
        raise Exception("No background videos found.")

    pool_sorted = sorted(pool)
    data = load_rotation_state()
    cursor = data.get("background_cursor", {})
    key = "global" if GLOBAL_BACKGROUND_ROTATION else (mood or "all")
    recent_bg = data.get("recent_backgrounds", [])[:RECENT_BACKGROUND_BLOCK]

    run_number_raw = os.getenv("GITHUB_RUN_NUMBER", "").strip()

    if BACKGROUND_RUN_NUMBER_ROTATION and run_number_raw.isdigit():
        source = "github_run_number"
        start_index = int(run_number_raw) % len(pool_sorted)
    else:
        source = "rotation_state_cursor"
        start_index = int(cursor.get(key, 0)) % len(pool_sorted)

    chosen = None
    chosen_index = start_index

    for offset in range(len(pool_sorted)):
        idx = (start_index + offset) % len(pool_sorted)
        candidate = pool_sorted[idx]
        if candidate not in recent_bg:
            chosen = candidate
            chosen_index = idx
            break

    if chosen is None:
        chosen = pool_sorted[start_index]
        chosen_index = start_index

    cursor[key] = (chosen_index + 1) % len(pool_sorted)
    data["background_cursor"] = cursor

    if chosen in recent_bg:
        recent_bg.remove(chosen)
    recent_bg.insert(0, chosen)
    data["recent_backgrounds"] = recent_bg[:max(RECENT_BACKGROUND_BLOCK, 20)]

    save_rotation_state(data)

    print("BACKGROUND ROTATION SOURCE:", source)
    print("BACKGROUND ROTATION KEY:", key)
    print("BACKGROUND ROTATION INDEX:", chosen_index)
    print("SELECTED BACKGROUND:", chosen)

    return chosen


# ================================================================
# EBOOK SCREENSHOTS
# ================================================================

IMAGE_EXTENSIONS = ["*.png", "*.jpg", "*.jpeg", "*.webp", "*.PNG", "*.JPG", "*.JPEG", "*.WEBP"]


def scan_image_files(folder):
    files = []
    for ext in IMAGE_EXTENSIONS:
        files.extend(glob.glob(os.path.join(folder, ext)))
    return sorted(list(set(files)))


def get_ebook_screenshot_pool():
    pool = []
    if os.path.isdir(EBOOK_ROOT):
        for sub in ["quotes", "trackers", "rules", "phases", "generic"]:
            folder = os.path.join(EBOOK_ROOT, sub)
            if os.path.isdir(folder):
                pool.extend(scan_image_files(folder))
        if not pool:
            for folder, _, _ in os.walk(EBOOK_ROOT):
                pool.extend(scan_image_files(folder))
    return sorted(list(set(pool)))


def choose_ebook_screenshot():
    pool = get_ebook_screenshot_pool()
    return random.choice(pool) if pool else None


def should_use_ebook_bait(script):
    """
    v30.1: no ebook overlays in public growth reels.
    """
    return False


def prepare_ebook_overlay(image_path):
    if not image_path or not os.path.exists(image_path):
        return None

    try:
        img = Image.open(image_path).convert("RGB")
        max_w = int(W * 0.72)
        max_h = int(H * 0.52)
        ratio = img.width / max(1, img.height)

        if ratio > max_w / max_h:
            new_w = max_w
            new_h = int(max_w / ratio)
        else:
            new_h = max_h
            new_w = int(max_h * ratio)

        img = img.resize((new_w, new_h), Image.LANCZOS)
        img_rgba = img.convert("RGBA").rotate(-3, expand=True, resample=Image.BICUBIC)

        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        shadow = Image.new("RGBA", img_rgba.size, (0, 0, 0, 135))

        x = (W - img_rgba.width) // 2
        y = int(H * 0.19)
        canvas.paste(shadow, (x + 18, y + 18), shadow)
        canvas.paste(img_rgba, (x, y), img_rgba)

        draw = ImageDraw.Draw(canvas)
        label_font = load_font(48)
        label = "MEMBERS ONLY"
        tw = draw.textlength(label, font=label_font)
        lx = int((W - tw) / 2)
        ly = int(H * 0.735)
        draw.text((lx + 3, ly + 4), label, font=label_font, fill=(0, 0, 0, 220))
        draw.text((lx, ly), label, font=label_font, fill=ORANGE + (255,), stroke_width=4, stroke_fill=(0, 0, 0, 255))

        return np.array(canvas.convert("RGB"))
    except Exception as e:
        print(f"Ebook overlay failed: {e}")
        return None


# ================================================================
# TTS
# ================================================================

async def tts_async(text, filename, rate, pitch):
    communicate = edge_tts.Communicate(clean_text(text), VOICE, rate=rate, pitch=pitch, volume=VOLUME)
    await communicate.save(filename)


def generate_voice(text, filename, pacing):
    mode = PACING.get(pacing, PACING.get('cold', list(PACING.values())[0]))
    asyncio.run(tts_async(text, filename, mode["rate"], mode["pitch"]))


# ================================================================
# TEXT RENDERING
# ================================================================

HOT_WORDS = {
    "WEAK", "WEAKNESS", "DISCIPLINE", "STANDARD", "STANDARDS", "RESET", "LOCKED",
    "ALONE", "QUIT", "DRIFT", "MAN", "MORNING", "SNOOZE", "NOW", "TODAY",
    "DONE", "DAY", "NO", "STOP", "HARD", "COMFORT", "CONTROL", "ACCOUNTABILITY",
    "CONSEQUENCE", "FUTURE", "MEMBERS", "MANUAL", "PRIVATE", "JOIN",
}

DANGER_WORDS = {
    "WEAK", "WEAKNESS", "FAIL", "FAILED", "QUIT", "QUITTING", "EXCUSE", "EXCUSES",
    "WASTING", "DRIFT", "COMFORT", "BETRAYAL",
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

            draw.text((x + 5, y + 6), word, font=font, fill=(0, 0, 0), stroke_width=8, stroke_fill=(0, 0, 0))
            draw.text((x, y), word, font=font, fill=color, stroke_width=7, stroke_fill=BLACK)
            x += int(widths[wi] + space)


def make_text_frame(text, level="normal"):
    img = Image.new("RGB", (W, H), BLACK)
    draw = ImageDraw.Draw(img)
    wc = len(clean_text(text).split())

    if level == "cover":
        font_size = 170 if wc <= 2 else 132
        y = H * 0.53
    elif level == "hook":
        font_size = 132 if wc <= 5 else 108
        y = H * TEXT_HOOK_Y
    elif wc <= 2:
        font_size = 140
        y = H * TEXT_CENTER_Y
    elif wc <= 5:
        font_size = 110
        y = H * TEXT_CENTER_Y
    else:
        font_size = 88
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
# VISUAL FX
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


def apply_cinematic_grade(frame):
    f = frame.astype(np.float32)
    f = (f - 128) * CINEMATIC_CONTRAST + 128
    f = f + CINEMATIC_BRIGHTNESS + CINEMATIC_SHADOW_LIFT
    gray = f.mean(axis=2, keepdims=True)
    f = gray + (f - gray) * CINEMATIC_SATURATION
    f = np.minimum(f, CINEMATIC_HIGHLIGHT_CAP)
    return np.clip(f, 0, 255).astype(np.uint8)


def add_film_grain(frame, t):
    rng = np.random.default_rng(int(t * 1000) % 100000)
    grain = rng.normal(0, 2.1, frame.shape).astype(np.float32)
    return np.clip(frame.astype(np.float32) + grain, 0, 255).astype(np.uint8)


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
    fd_in = 0.18 if event_type in ["cover", "impact"] else 0.16
    fd_out = 0.10

    if local < fd_in:
        alpha = local / fd_in
    elif end - t < fd_out:
        alpha = (end - t) / fd_out
    else:
        alpha = 1.0

    alpha = float(np.clip(alpha, 0.0, 1.0))
    scale = 1.0 + (0.025 * (1 - local / 0.18)) if local < 0.18 else 1.0
    offset_y = 10 * (1 - local / 0.22) if local < 0.22 else 0
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
    cover_end = min(0.78, duration)

    events.append({
        "frame": make_text_frame(script.cover, "cover"),
        "start": 0.01,
        "end": cover_end,
        "type": "cover",
    })

    last_end = cover_end + 0.08
    gap_between_texts = 0.035
    fade_tail = 0.055

    for i, item in enumerate(voice_data):
        chunks = split_chunks(item["line"], item["chunk_size"])
        chunk_dur = item["duration"] / max(1, len(chunks))

        for j, chunk in enumerate(chunks):
            natural_start = item["start"] + j * chunk_dur
            natural_end = item["start"] + (j + 1) * chunk_dur + fade_tail
            start = max(natural_start, last_end + gap_between_texts)
            end = min(natural_end, duration)

            if end - start < 0.16:
                continue

            raw = chunk.upper()
            event_type = "impact" if any(w in raw for w in ["WEAK", "FAIL", "NO ", "STOP", "KILL", "QUIT", "DAY", "JOIN"]) else "text"
            level = "hook" if i == 0 and j == 0 else "normal"

            events.append({
                "frame": make_text_frame(chunk, level),
                "start": start,
                "end": end,
                "type": event_type,
            })
            last_end = end

    return events


# ================================================================
# AUDIO DUCKING
# ================================================================

def build_music_duck_segments(duration, voice_data):
    duck_windows = []

    for item in voice_data:
        line = item.get("line", "")
        start = float(item.get("start", 0))
        end = start + float(item.get("duration", 0))
        raw = line.upper()

        is_impact = any(word in raw for word in [
            "WEAK", "WEAKNESS", "QUIT", "NO EXCUSES", "DONE", "LINK IN BIO",
            "COMMENT", "STANDARD", "DISCIPLINE", "DAY ", "STOP", "KILL",
            "JOIN", "MEMBERS", "MANUAL", "ACCOUNTABILITY"
        ])

        if is_impact:
            duck_windows.append((max(0, start - 0.05), min(duration, end + 0.08)))

    if not duck_windows:
        return [(0, duration, MUSIC_BASE_VOLUME)]

    duck_windows.sort()
    merged = []
    for s, e in duck_windows:
        if not merged or s > merged[-1][1]:
            merged.append([s, e])
        else:
            merged[-1][1] = max(merged[-1][1], e)

    segments = []
    cursor = 0.0
    for s, e in merged:
        if s > cursor:
            segments.append((cursor, s, MUSIC_BASE_VOLUME))
        segments.append((s, e, MUSIC_DUCK_VOLUME))
        cursor = e

    if cursor < duration:
        segments.append((cursor, duration, MUSIC_BASE_VOLUME))

    return segments


def build_ducked_music(music_path, duration, voice_data):
    music = AudioFileClip(music_path)
    music = afx.audio_loop(music, duration=duration)
    music = music.audio_fadein(0.55).audio_fadeout(0.75)

    clips = []
    for s, e, vol in build_music_duck_segments(duration, voice_data):
        if e <= s:
            continue
        clips.append(music.subclip(s, e).volumex(vol).set_start(s))

    return CompositeAudioClip(clips)


# ================================================================
# COVER
# ================================================================

def make_cinematic_cover_background(bg_path):
    try:
        clip = VideoFileClip(bg_path)
        t = min(max(0.15, clip.duration * 0.28), max(0, clip.duration - 0.10))
        frame = clip.get_frame(t).astype(np.uint8)
        clip.close()

        img = Image.fromarray(frame).convert("RGB")
        ratio = img.width / img.height
        target = W / H

        if ratio > target:
            img = img.resize((int(H * ratio), H), Image.LANCZOS)
        else:
            img = img.resize((W, int(W / ratio)), Image.LANCZOS)

        left = (img.width - W) // 2
        top = (img.height - H) // 2
        img = img.crop((left, top, left + W, top + H))

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
            color = RED if raw in DANGER_WORDS else (ORANGE if wi == 0 else WHITE)

            draw.text((x + 5, y + 6), word, font=font, fill=(0, 0, 0, 210))
            draw.text((x, y), word, font=font, fill=color + (255,), stroke_width=8, stroke_fill=(0, 0, 0, 255))
            x += int(widths[wi] + space)

    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH).convert("RGBA")
        aspect = logo.height / max(1, logo.width)
        new_w = COVER_LOGO_SIZE
        new_h = int(COVER_LOGO_SIZE * aspect)
        logo = logo.resize((new_w, new_h), Image.LANCZOS)
        logo.putalpha(150)
        img_rgba.paste(logo, ((W - new_w) // 2, H - new_h - LOGO_BOTTOM_MARGIN), logo)

    return img_rgba.convert("RGB")


def export_cover(script, out_path, bg_path=None):
    base = os.path.splitext(out_path)[0]
    out = f"{base}_cover.png"
    img = make_cinematic_cover_background(bg_path) if bg_path else Image.new("RGB", (W, H), BLACK)
    img = draw_cover_text_on_image(img, script.cover)
    img.save(out, quality=95)
    return out


# ================================================================
# METADATA
# ================================================================

def choose_caption_type_v25(script):
    category = str(getattr(script, "category", "")).lower()
    cover = str(getattr(script, "cover", "")).lower()
    joined = " ".join(getattr(script, "lines", [])).lower()
    text = " ".join([category, cover, joined])

    if "promo" in category or "accountability" in text or "room" in text:
        return "soft_promo"
    if any(x in text for x in ["years", "time", "potential", "regret", "old enough"]):
        return "regret"
    if any(x in text for x in ["cost", "damage", "charge", "interest", "consequence", "worse"]):
        return "consequence"
    if any(x in text for x in ["standard", "identity", "private", "habit", "routine"]):
        return "identity"
    if any(x in text for x in ["structure", "rules", "systems", "negotiation", "motivation"]):
        return "structure"
    if any(x in text for x in ["be honest", "you know", "this is you", "stop lying"]):
        return "accountability"
    return random.choice(["reflection", "identity", "consequence", "structure", "community"])


def build_caption_v25(script):
    caption_type = choose_caption_type_v25(script)
    caption_pool = CAPTION_BANK_V25.get(caption_type, CAPTION_BANK_V25["reflection"])

    caption = pick_unique_rotated(caption_pool, memory_key="recent_captions_v25", max_recent=80)
    hashtags = pick_unique_rotated(HASHTAG_PACKS_V25, memory_key="recent_hashtags_v25", max_recent=20)

    print("CAPTION TYPE:", caption_type)
    print("CAPTION:", caption.replace("\n", " / "))
    print("HASHTAGS:", hashtags)

    return caption + "\n\n" + hashtags


def choose_caption_type_v26(script):
    text = " ".join([
        str(getattr(script, "category", "")),
        str(getattr(script, "cover", "")),
        " ".join(getattr(script, "lines", [])),
    ]).lower()

    if any(x in text for x in ["cost", "price", "bill", "interest", "excuse", "comfort", "compound"]):
        return "consequence"
    if any(x in text for x in ["years", "time", "potential", "regret", "later"]):
        return "regret"
    if any(x in text for x in ["structure", "rules", "systems", "negotiate", "motivation", "mood"]):
        return "structure"
    if any(x in text for x in ["discipline", "standard", "routine", "habits", "identity", "proof"]):
        return "identity"
    return random.choice(["identity", "consequence", "structure", "community"])


def build_caption_v26(script):
    """
    Meta-aligned caption engine:
    short, relevant, no engagement bait, under 10 hashtags.
    """
    caption_type = choose_caption_type_v26(script)
    caption_pool = CAPTION_BANK_V26.get(caption_type, CAPTION_BANK_V26["identity"])

    caption = pick_unique_rotated(
        caption_pool,
        memory_key="recent_captions_v26",
        max_recent=100,
    )

    hashtags = pick_unique_rotated(
        HASHTAG_PACKS_V26,
        memory_key="recent_hashtags_v26",
        max_recent=30,
    )

    print("CAPTION TYPE V26:", caption_type)
    print("CAPTION V26:", caption)
    print("HASHTAGS V26:", hashtags)

    return caption + "\n\n" + hashtags



CAPTION_BANK_V27 = {
    "identity": [
        "Identity is built in private before it is seen in public.",
        "Your standards are not what you say. They are what you repeat.",
        "The routine tells the truth before the result arrives.",
        "Discipline is not a mood. It is a standard.",
    ],
    "consequence": [
        "Weak choices feel small until they compound.",
        "Comfort is never free. The cost arrives later.",
        "The bill for avoided discipline always comes.",
        "Small excuses become expensive when repeated.",
    ],
    "standards": [
        "Raise the standard before you chase the result.",
        "A standard that changes with mood is not a standard.",
        "Rules protect you from your weakest mood.",
        "No negotiation. Decide once. Repeat daily.",
    ],
    "accountability": [
        "Look at the pattern. That is where the truth is.",
        "Accountability begins where the excuse ends.",
        "Your private habits eventually become public results.",
        "Stop explaining the pattern. Correct it.",
    ],
    "self_control": [
        "Control starts with the first small choice.",
        "The urge passes. The choice remains.",
        "Protect your attention. It is training your life.",
        "Self-control is quiet proof.",
    ],
    "habits": [
        "Habits vote daily. Your future counts them.",
        "What you repeat becomes what you trust.",
        "The routine wins when the standard is weak.",
        "Small habits decide more than big speeches.",
    ],
    "masculinity": [
        "Keep your word. Especially to yourself.",
        "Be reliable when pressure arrives.",
        "Quiet strength does not need applause.",
        "A serious man protects his standard.",
    ],
}

HASHTAG_PACKS_V27 = [
    "#discipline #selfdiscipline #consistency #innerdiscipline #mentalstrength",
    "#discipline #habits #standards #selfcontrol #growth",
    "#discipline #routine #focus #mindset #selfrespect",
    "#innerdiscipline #consistency #selfmastery #habits #growthmindset",
    "#discipline #accountability #mentalcontrol #standards #focus",
    "#selfcontrol #discipline #mensmindset #consistency #growth",
]

def choose_caption_type_v27(script):
    category = str(getattr(script, "category", "")).lower()
    text = " ".join([
        category,
        str(getattr(script, "cover", "")),
        " ".join(getattr(script, "lines", [])),
    ]).lower()

    if category in CAPTION_BANK_V27:
        return category
    if any(x in text for x in ["cost", "bill", "interest", "comfort", "damage", "years"]):
        return "consequence"
    if any(x in text for x in ["standard", "rules", "negotiation", "structure"]):
        return "standards"
    if any(x in text for x in ["pattern", "honest", "excuse", "accountability"]):
        return "accountability"
    if any(x in text for x in ["control", "urge", "attention", "inputs"]):
        return "self_control"
    if any(x in text for x in ["habit", "routine", "repeat"]):
        return "habits"
    if any(x in text for x in ["man", "men", "word", "reliable"]):
        return "masculinity"
    return "identity"


def build_caption_v27(script):
    caption_type = choose_caption_type_v27(script)
    caption_pool = CAPTION_BANK_V27.get(caption_type, CAPTION_BANK_V27["identity"])
    caption = pick_unique_rotated(caption_pool, memory_key="recent_captions_v27", max_recent=120)
    hashtags = pick_unique_rotated(HASHTAG_PACKS_V27, memory_key="recent_hashtags_v27", max_recent=40)

    print("CAPTION TYPE V27:", caption_type)
    print("CAPTION V27:", caption)
    print("HASHTAGS V27:", hashtags)

    return caption + "\n\n" + hashtags



CAPTION_BANK_V28 = {
    "identity": ["The pattern tells the truth.", "Your routine is already voting.", "Identity is built when nobody is watching.", "What you repeat becomes proof.", "Private choices become public results."],
    "identity_open_loop": ["The drift starts quietly.", "The promise was not the hard part.", "The old pattern always leaves clues.", "The routine tells you before the result does.", "You usually notice it before anyone else does."],
    "consequence": ["Nothing stays small when repeated.", "The cost usually arrives later.", "Weak choices compound quietly.", "Time keeps score."],
    "standards": ["Standards create outcomes.", "A moving standard cannot build a stable life.", "Decide once. Repeat daily.", "Your mood cannot own your standard."],
    "accountability": ["Look at the pattern.", "Excuses lose power when the pattern is exposed.", "Correct the routine before it becomes identity.", "Accountability begins where hiding ends."],
    "habits": ["Habits vote daily.", "The routine wins when the standard is weak.", "What you repeat becomes what you trust."],
    "self_control": ["The urge passes. The choice stays.", "Protect your attention.", "Control begins before the result."],
    "masculinity": ["Keep your word. Especially to yourself.", "Quiet strength does not need applause.", "A serious man protects his standard."],
}

HASHTAG_PACKS_V28 = [
    "#discipline #selfdiscipline #consistency #innerdiscipline #mentalstrength",
    "#discipline #habits #standards #selfcontrol #growth",
    "#discipline #routine #focus #mindset #selfrespect",
    "#innerdiscipline #consistency #selfmastery #habits #growthmindset",
    "#discipline #accountability #mentalcontrol #standards #focus",
]

def choose_caption_type_v28(script):
    category = str(getattr(script, "category", "")).lower()
    if category in CAPTION_BANK_V28:
        return category
    text = " ".join([category, str(getattr(script, "cover", "")), " ".join(getattr(script, "lines", []))]).lower()
    if "cost" in text or "bill" in text or "years" in text or "damage" in text:
        return "consequence"
    if "standard" in text or "rules" in text:
        return "standards"
    if "pattern" in text or "honest" in text or "accountability" in text:
        return "accountability"
    if "habit" in text or "routine" in text:
        return "habits"
    return "identity"


def build_caption_v28(script):
    caption_type = choose_caption_type_v28(script)
    caption_pool = CAPTION_BANK_V28.get(caption_type, CAPTION_BANK_V28["identity"])
    caption = pick_unique_rotated(caption_pool, memory_key="recent_captions_v28", max_recent=160)
    hashtags = pick_unique_rotated(HASHTAG_PACKS_V28, memory_key="recent_hashtags_v28", max_recent=50)
    print("CAPTION TYPE V28:", caption_type)
    print("CAPTION V28:", caption)
    print("HASHTAGS V28:", hashtags)
    return caption + "\n\n" + hashtags



CAPTION_BANK_V29 = {
    "identity": [
        "You usually know the problem before the result appears. The question is whether you correct it or keep explaining it away.",
        "Your routine tells the truth before your results do. Listen to the pattern.",
        "Identity is built in private. The public result only reveals what was repeated.",
        "The promise is not the hard part. Keeping it when the mood changes is.",
    ],
    "open_loop_identity": [
        "The first warning usually comes before the failure. Most people ignore it because nothing has collapsed yet.",
        "The drift starts quietly. One small excuse becomes a routine if you stop correcting it.",
        "You often feel the standard dropping before anyone else sees the result.",
        "The old pattern always leaves clues. The question is whether you correct them early.",
    ],
    "consequence": [
        "Weak choices feel small until they compound. That is why the small decisions matter.",
        "The cost usually arrives later. That delay is what makes weak habits dangerous.",
        "Nothing stays small when repeated. Not excuses. Not comfort. Not avoidance.",
        "Time keeps score even when nobody else is watching.",
    ],
    "standards": [
        "A standard that changes with mood cannot build a stable life.",
        "Raise the standard before you chase the result.",
        "The more you negotiate with the standard, the weaker it becomes.",
        "Structure protects you when motivation disappears.",
    ],
}

HASHTAG_PACKS_V29 = [
    "#discipline #selfdiscipline #consistency #innerdiscipline #mentalstrength",
    "#discipline #habits #standards #selfcontrol #growth",
    "#discipline #routine #focus #mindset #selfrespect",
    "#innerdiscipline #consistency #selfmastery #habits #growthmindset",
    "#discipline #accountability #mentalcontrol #standards #focus",
]

def choose_caption_type_v29(script):
    category = str(getattr(script, "category", "")).lower()
    if category in CAPTION_BANK_V29:
        return category

    text = " ".join([
        category,
        str(getattr(script, "cover", "")),
        " ".join(getattr(script, "lines", [])),
    ]).lower()

    if "open" in category or "felt" in text or "warning" in text or "drift" in text:
        return "open_loop_identity"
    if "cost" in text or "bill" in text or "years" in text or "damage" in text:
        return "consequence"
    if "standard" in text or "rules" in text or "structure" in text:
        return "standards"
    return "identity"


def build_caption_v29(script):
    caption_type = choose_caption_type_v29(script)
    caption_pool = CAPTION_BANK_V29.get(caption_type, CAPTION_BANK_V29["identity"])

    caption = pick_unique_rotated(
        caption_pool,
        memory_key="recent_captions_v29",
        max_recent=180,
    )

    hashtags = pick_unique_rotated(
        HASHTAG_PACKS_V29,
        memory_key="recent_hashtags_v29",
        max_recent=60,
    )

    print("CAPTION TYPE V29:", caption_type)
    print("CAPTION V29:", caption)
    print("HASHTAGS V29:", hashtags)

    return caption + "\n\n" + hashtags




CAPTION_BANK_V30 = {
    "mirror": [
        "You usually feel the warning before the result changes. The question is whether you correct it early or explain it away.",
        "Most patterns do not surprise you. You saw the first sign. You just waited too long to act.",
        "The standard rarely disappears loudly. It slips through small private choices.",
        "You are not lacking information. You are avoiding the moment that demands proof.",
    ],
    "mirror_two_stage": [
        "The hardest part is rarely starting. It is continuing when there is no emotion left.",
        "Change begins when the explanation stops protecting the pattern.",
        "The real test is not the beginning. It is the repetition after the mood fades.",
        "Most people do not lose discipline suddenly. They lose it quietly, then call it temporary.",
    ],
    "identity": [
        "Identity is built in private before it is seen in public.",
        "Your routine tells the truth before your results do.",
        "The promise is not the hard part. Keeping it when the mood changes is.",
        "Private choices become public results.",
    ],
    "consequence": [
        "Nothing stays small when repeated. Not excuses. Not comfort. Not avoidance.",
        "The cost usually arrives later. That delay is what makes weak habits dangerous.",
        "Weak choices feel small until they compound.",
        "Time keeps score even when nobody else is watching.",
    ],
    "standards": [
        "A standard that changes with mood cannot build a stable life.",
        "The more you negotiate with the standard, the weaker it becomes.",
        "Structure protects you when motivation disappears.",
        "Raise the standard before you chase the result.",
    ],
}

HASHTAG_PACKS_V30 = [
    "#discipline #selfdiscipline #consistency #innerdiscipline #mentalstrength",
    "#discipline #habits #standards #selfcontrol #growth",
    "#discipline #routine #focus #mindset #selfrespect",
    "#innerdiscipline #consistency #selfmastery #habits #growthmindset",
    "#discipline #accountability #mentalcontrol #standards #focus",
]

def choose_caption_type_v30(script):
    category = str(getattr(script, "category", "")).lower()
    if category in CAPTION_BANK_V30:
        return category

    text = " ".join([
        category,
        str(getattr(script, "cover", "")),
        " ".join(getattr(script, "lines", [])),
    ]).lower()

    if "mirror" in category or "warning" in text or "felt" in text or "tomorrow" in text:
        return "mirror"
    if "hardest" in text or "moment" in text or "part" in text:
        return "mirror_two_stage"
    if "cost" in text or "bill" in text or "years" in text or "damage" in text:
        return "consequence"
    if "standard" in text or "rules" in text or "structure" in text:
        return "standards"
    return "identity"


def build_caption_v30(script):
    caption_type = choose_caption_type_v30(script)
    caption_pool = CAPTION_BANK_V30.get(caption_type, CAPTION_BANK_V30["mirror"])

    caption = pick_unique_rotated(
        caption_pool,
        memory_key="recent_captions_v30",
        max_recent=200,
    )

    hashtags = pick_unique_rotated(
        HASHTAG_PACKS_V30,
        memory_key="recent_hashtags_v30",
        max_recent=60,
    )

    print("CAPTION TYPE V30:", caption_type)
    print("CAPTION V30:", caption)
    print("HASHTAGS V30:", hashtags)

    return caption + "\n\n" + hashtags




CAPTION_BANK_V30_1 = {
    "mirror": [
        "You usually feel the warning before the result changes. The question is whether you correct it early or explain it away.",
        "Most patterns do not surprise you. You saw the first sign. You just waited too long to act.",
        "The standard rarely disappears loudly. It slips through small private choices.",
        "You are not lacking information. You are avoiding the moment that demands proof.",
    ],
    "mirror_two_stage": [
        "The hardest part is rarely starting. It is continuing when there is no emotion left.",
        "Change begins when the explanation stops protecting the pattern.",
        "The real test is not the beginning. It is the repetition after the mood fades.",
        "Most people do not lose discipline suddenly. They lose it quietly, then call it temporary.",
    ],
    "identity": [
        "Identity is built in private before it is seen in public.",
        "Your routine tells the truth before your results do.",
        "The promise is not the hard part. Keeping it when the mood changes is.",
        "Private choices become public results.",
    ],
    "consequence": [
        "Nothing stays small when repeated. Not excuses. Not comfort. Not avoidance.",
        "The cost usually arrives later. That delay is what makes weak habits dangerous.",
        "Weak choices feel small until they compound.",
        "Time keeps score even when nobody else is watching.",
    ],
    "standards": [
        "A standard that changes with mood cannot build a stable life.",
        "The more you negotiate with the standard, the weaker it becomes.",
        "Structure protects you when motivation disappears.",
        "Raise the standard before you chase the result.",
    ],
}

HASHTAG_PACKS_V30_1 = [
    "#discipline #selfdiscipline #consistency #innerdiscipline #mentalstrength",
    "#discipline #habits #standards #selfcontrol #growth",
    "#discipline #routine #focus #mindset #selfrespect",
    "#innerdiscipline #consistency #selfmastery #habits #growthmindset",
    "#discipline #accountability #mentalcontrol #standards #focus",
]

def choose_caption_type_v30_1(script):
    category = str(getattr(script, "category", "")).lower()
    if category in CAPTION_BANK_V30_1:
        return category

    text = " ".join([
        category,
        str(getattr(script, "cover", "")),
        " ".join(getattr(script, "lines", [])),
    ]).lower()

    if "mirror" in category or "warning" in text or "felt" in text or "tomorrow" in text:
        return "mirror"
    if "hardest" in text or "moment" in text or "part" in text:
        return "mirror_two_stage"
    if "cost" in text or "bill" in text or "years" in text or "damage" in text:
        return "consequence"
    if "standard" in text or "rules" in text or "structure" in text:
        return "standards"
    return "mirror"


def build_caption_v30_1(script):
    caption_type = choose_caption_type_v30_1(script)
    caption_pool = CAPTION_BANK_V30_1.get(caption_type, CAPTION_BANK_V30_1["mirror"])

    caption = pick_unique_rotated(
        caption_pool,
        memory_key="recent_captions_v30_1",
        max_recent=220,
    )

    hashtags = pick_unique_rotated(
        HASHTAG_PACKS_V30_1,
        memory_key="recent_hashtags_v30_1",
        max_recent=80,
    )

    print("CAPTION TYPE V30.1:", caption_type)
    print("CAPTION V30.1:", caption)
    print("HASHTAGS V30.1:", hashtags)

    return caption + "\n\n" + hashtags



def build_caption(script):
    """
    V30.1 captions: clear, relevant, self-confrontational, no engagement bait.
    """
    return build_caption_v30_1(script)


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
        cursor = 0.95
        gap = random.uniform(SILENCE_GAP_MIN, SILENCE_GAP_MAX)

        print("Generating voice lines...")
        for i, line in enumerate(script.lines):
            vf = os.path.join(TEMP_DIR, f"voice_{datetime.now().strftime('%H%M%S')}_{i}_{random.randint(1000,9999)}.mp3")
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
                "chunk_size": PACING.get(script.pacing, PACING.get('cold', list(PACING.values())[0]))["chunk_size"],
            })

            cursor += dur + (gap if i < len(script.lines) - 1 else 0.24)

        duration = min(cursor, REEL_SECONDS)
        duration = min(RETENTION_MAX_SECONDS, max(RETENTION_MIN_SECONDS, duration))
        print(f"Video duration: {duration:.2f}s")

        for item in voice_data:
            if item["start"] < duration:
                audio_clips.append(AudioFileClip(item["file"]).set_start(item["start"]))

        text_events = make_text_events(script, voice_data, duration)
        logo_frame = make_logo_frame()
        vignette = make_vignette()

        ebook_overlay = prepare_ebook_overlay(script.ebook_image) if script.ebook_image else None
        ebook_start = max(2.2, duration * 0.26)
        ebook_end = min(duration - 2.0, ebook_start + 3.2)

        bg_clip = prepare_background(bg_path, duration)

        reel_zoom_strength = random.uniform(0.055, 0.095)

        def make_frame(t):
            frame = bg_clip.get_frame(t).astype(np.uint8)

            zoom = 1.0 + reel_zoom_strength * (t / max(duration, 0.001))
            if zoom > 1.001:
                new_w = int(W / zoom)
                new_h = int(H / zoom)
                x1 = (W - new_w) // 2
                y1 = (H - new_h) // 2
                pil = Image.fromarray(frame)
                pil = pil.crop((x1, y1, x1 + new_w, y1 + new_h)).resize((W, H), Image.LANCZOS)
                frame = np.array(pil)

            if t < 0.65:
                dx = int(math.sin(t * 70) * SHAKE_STRENGTH)
                dy = int(math.cos(t * 60) * SHAKE_STRENGTH)
                frame = np.roll(frame, shift=(dy, dx), axis=(0, 1))

            frame = apply_cinematic_grade(frame)

            # First-frame pressure boost: first 0.55 sec must feel visually heavier.
            if t < 0.55:
                ff = frame.astype(np.float32)
                ff = (ff - 128) * FIRST_FRAME_CONTRAST_BOOST + 128
                ff *= FIRST_FRAME_BRIGHTNESS_MULT
                ff[:, :, 0] *= FIRST_FRAME_ORANGE_BOOST
                frame = np.clip(ff, 0, 255).astype(np.uint8)

            f = frame.astype(np.float32)
            f[:, :, 0] *= vignette
            f[:, :, 1] *= vignette
            f[:, :, 2] *= vignette
            frame = np.clip(f, 0, 255).astype(np.uint8)

            band = frame.astype(np.float32)
            y1 = int(H * TEXT_BAND_TOP)
            y2 = int(H * TEXT_BAND_BOTTOM)
            band[y1:y2, :, :] *= TEXT_BAND_STRENGTH
            frame = np.clip(band, 0, 255).astype(np.uint8)

            frame = add_film_grain(frame, t)

            if ebook_overlay is not None and ebook_start <= t < ebook_end:
                local = t - ebook_start
                if local < 0.18:
                    ebook_alpha = local / 0.18
                elif ebook_end - t < 0.18:
                    ebook_alpha = (ebook_end - t) / 0.18
                else:
                    ebook_alpha = 1.0
                ebook_alpha = float(np.clip(ebook_alpha, 0.0, 1.0))
                ebook_scale = 1.0 + 0.018 * math.sin(local * 2.6)
                frame = composite_rgb(frame, ebook_overlay, opacity=ebook_alpha * 0.92, scale=ebook_scale)

            for ev in text_events:
                if ev["start"] <= t < ev["end"]:
                    alpha, offset_y, scale = subtitle_animation_values(t, ev["start"], ev["end"], ev["type"])
                    frame = composite_rgb(frame, ev["frame"], opacity=alpha, offset_y=offset_y, scale=scale)

            if logo_frame is not None:
                frame = composite_rgb(frame, logo_frame, opacity=LOGO_OPACITY)

            return frame

        final_video = VideoClip(make_frame, duration=duration).set_fps(FPS)
        final_voice = CompositeAudioClip(audio_clips)

        if os.path.exists(MUSIC_PATH):
            music = build_ducked_music(MUSIC_PATH, duration, voice_data)
            final_audio = CompositeAudioClip([music, final_voice.volumex(1.24)])
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
# MAIN
# ================================================================

def main():
    print("\nINNER DISCIPLINE â€” MIRROR ENGINE v30.1 FULLSCREEN RETENTION")
    print("=" * 64)
    print("RUN ID:", RUN_ID)
    print("SERIES STATE FILE:", SERIES_STATE_FILE)
    print("SERIES STATE LOADED:", load_series_state())
    print("SERIES NEXT DAY:", load_series_state().get("next_day"))
    print("ROTATION STATE FILE:", ROTATION_STATE_FILE)
    print("HOOK STATE FILE:", HOOK_STATE_FILE)
    print("RECENT ROTATION CATEGORIES:", load_rotation_state().get("recent_categories", [])[:5])
    print("RECENT ROTATION BACKGROUNDS:", load_rotation_state().get("recent_backgrounds", [])[:5])
    print("EBOOK ROOT:", EBOOK_ROOT)
    print("EBOOK SCREENSHOTS FOUND:", get_ebook_screenshot_pool())

    script = build_script()

    print("SELECTED MODE:", script.mode)
    print("SELECTED CATEGORY:", script.category)
    print("SELECTED MOOD:", script.mood)

    bg = choose_background_rotated(script.mood)

    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(OUTPUT_DIR, f"reel_v30_1_{script.mode}_{script.category}_{date_str}_{RUN_ID}.mp4")

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
    state_saved_ok = auto_commit_state_files()
    if STRICT_STATE_SEQUENCE and not state_saved_ok:
        raise RuntimeError('State was not saved to GitHub. Enable Settings > Actions > General > Workflow permissions > Read and write permissions. Without this, Day 2 and the same background will repeat.')

    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)

    print("=" * 64)
    print("COMPLETE")


if __name__ == "__main__":
    main()
