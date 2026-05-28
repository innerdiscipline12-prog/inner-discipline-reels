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
# INNER DISCIPLINE â€” GROWTH ENGINE v17 DAY LOOP FIX
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
LOGO_SIZE = 112
LOGO_BOTTOM_MARGIN = 100

COVER_LOGO_SIZE = 92
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
RECENT_BACKGROUND_BLOCK = 8
RECENT_LINE_BLOCK = 70

GITHUB_RUN_NUMBER_SERIES_FALLBACK = True
SERIES_START_DAY_IF_NO_STATE = 2
SERIES_FAIL_IF_STATE_PUSH_BLOCKED = False

# v17 fix:
# v16 used the current run as the anchor, so it always reset to Day 2.
# This fixed anchor makes GitHub's run number advance the day each run even if state is not saved.
# Change this manually later only if you want to realign the sequence.
SERIES_FIXED_RUN_ANCHOR = 1
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


def load_series_state():
    """
    v17 Day loop fix.

    The real issue:
    GitHub is not persisting series_state.json between runs.
    v16 fallback used the current run as anchor, so every run became Day 2 again.

    v17 fix:
    - If series_state.json exists and is initialized, trust it.
    - If state is not persisted, use GitHub's GITHUB_RUN_NUMBER with a FIXED anchor.
    - Because GITHUB_RUN_NUMBER increases every workflow run, the day now advances.

    Professional note:
    Best fix is still enabling GitHub Actions write permission so series_state.json commits.
    This fallback prevents the endless Day 2 loop.
    """
    state_exists = os.path.exists(SERIES_STATE_FILE)

    data = safe_load_json(
        SERIES_STATE_FILE,
        {
            "next_day": SERIES_START_DAY_IF_NO_STATE,
            "initialized": False,
        }
    )

    try:
        next_day = int(data.get("next_day", SERIES_START_DAY_IF_NO_STATE))
    except Exception:
        next_day = SERIES_START_DAY_IF_NO_STATE

    initialized = bool(data.get("initialized", False))

    if state_exists and initialized:
        if next_day < 1 or next_day > 30:
            next_day = SERIES_START_DAY_IF_NO_STATE
        return {
            "next_day": next_day,
            "initialized": initialized,
            "source": "series_state_json",
        }

    # Fallback when GitHub does not persist the state file.
    if GITHUB_RUN_NUMBER_SERIES_FALLBACK:
        run_number_raw = os.getenv("GITHUB_RUN_NUMBER", "").strip()

        if run_number_raw.isdigit():
            run_number = int(run_number_raw)

            # Fixed-anchor formula.
            # If run number increases, day increases.
            day = ((run_number - SERIES_FIXED_RUN_ANCHOR) + (SERIES_START_DAY_IF_NO_STATE - 1)) % 30 + 1

            if day < 1 or day > 30:
                day = SERIES_START_DAY_IF_NO_STATE

            return {
                "next_day": day,
                "initialized": False,
                "source": "github_run_number_fallback",
                "github_run_number": run_number,
                "series_fixed_run_anchor": SERIES_FIXED_RUN_ANCHOR,
            }

    if next_day < 1 or next_day > 30:
        next_day = SERIES_START_DAY_IF_NO_STATE

    return {
        "next_day": next_day,
        "initialized": False,
        "source": "default_no_state",
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
    if not AUTO_COMMIT_STATE:
        return

    files = [
        "series_state.json",
        "rotation_state.json",
        "used_lines_v3.json",
        "engine_state_v3.json",
        "hook_state.json",
    ]
    existing = [f for f in files if os.path.exists(os.path.join(BASE_DIR, f))]
    if not existing:
        return

    try:
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=BASE_DIR, check=False)
        subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], cwd=BASE_DIR, check=False)
        subprocess.run(["git", "add"] + existing, cwd=BASE_DIR, check=False)

        status = subprocess.run(
            ["git", "status", "--porcelain"] + existing,
            cwd=BASE_DIR,
            text=True,
            capture_output=True,
            check=False,
        )

        if not status.stdout.strip():
            print("STATE COMMIT: no changes.")
            return

        commit = subprocess.run(
            ["git", "commit", "-m", "Update generator state"],
            cwd=BASE_DIR,
            text=True,
            capture_output=True,
            check=False,
        )
        print("STATE COMMIT:", commit.stdout.strip() or commit.stderr.strip())

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
            print("STATE WARNING: GitHub did not allow push. Enable Actions write permission or commit state files manually.")
            if SERIES_FAIL_IF_STATE_PUSH_BLOCKED:
                raise RuntimeError("State push blocked. Enable workflow permissions: contents: write.")

    except Exception as e:
        print(f"STATE AUTO-COMMIT FAILED: {e}")


# ================================================================
# PACING
# ================================================================

PACING = {
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


def build_series_script():
    series_data = load_series_state()
    print("SERIES STATE SOURCE:", series_data.get("source", "unknown"))

    override_day = os.getenv("SERIES_NEXT_DAY", "").strip()
    if override_day.isdigit():
        day = int(override_day)
        print("SERIES DAY OVERRIDE:", day)
    else:
        day = int(series_data.get("next_day", DEFAULT_SERIES_DAY))

    if day < 1 or day > 30:
        day = DEFAULT_SERIES_DAY

    episode = SERIES_EPISODES[day - 1]

    lines = [
        f"Day {episode['day']} of 30. {episode['title']}.",
        episode["pain"],
        f"Your task is simple. {episode['task']}",
        "Do not negotiate with the weak version of you.",
        "Comment DONE when you finish it.",
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
    v15 sequence priority.
    If true, the next run generates the next challenge day.
    """
    if SERIES_PRIORITY_MODE:
        return True

    recent = get_recent_generated_categories(limit=5)
    if recent and recent[0] == "series":
        return False
    return random.random() < SERIES_REEL_PROBABILITY


def build_script():
    """
    v15 selector.
    Series priority fixes the Day 2 problem.
    """
    if SERIES_PRIORITY_MODE and should_make_series():
        script = build_series_script()
        remember_rotation_item("recent_categories", "series", 20)
    else:
        roll = random.random()

        if roll < MEMBER_REEL_PROBABILITY:
            script = build_member_script()
        elif roll < MEMBER_REEL_PROBABILITY + DAY7_REEL_PROBABILITY:
            script = build_day7_script()
        elif should_make_series():
            script = build_series_script()
            remember_rotation_item("recent_categories", "series", 20)
        else:
            script = build_regular_script()

    script = maybe_add_save_share_signal(script)

    if should_use_ebook_bait(script):
        ebook = choose_ebook_screenshot()
        if ebook:
            script.ebook_image = ebook
            print("EBOOK BAIT IMAGE:", ebook)

    return script


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


def choose_background_rotated(mood=None):
    """
    v15 true background rotation:
    - one global cursor across the whole library
    - avoids recent backgrounds
    - forces use of more clips before repeating
    """
    pool = get_background_pool(mood)

    print("BASE DIR:", BASE_DIR)
    print("BG ROOT:", BG_ROOT)
    print("REQUESTED MOOD:", mood)
    print("TOTAL BACKGROUNDS FOUND:", len(pool))
    print("BACKGROUND POOL FOUND:", pool)

    if not pool:
        raise Exception("No background videos found.")

    data = load_rotation_state()
    cursor = data.get("background_cursor", {})
    key = "global" if GLOBAL_BACKGROUND_ROTATION else (mood or "all")

    pool_sorted = sorted(pool)
    recent_bg = data.get("recent_backgrounds", [])[:RECENT_BACKGROUND_BLOCK]

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
    if script.mode == "series":
        return False
    if script.category in ["member_accountability", "ebook_bait"]:
        return True
    return random.random() < EBOOK_BAIT_PROBABILITY


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
    mode = PACING[pacing]
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

    if script.mode == "day7":
        return "\n".join([
            "Most people do not lose consistency loudly.",
            "They drift through small compromises.",
            "",
            "Day 7 exposes the routine.",
            "Habits. Inputs. Standards. Structure.",
            "",
            "#discipline #consistency #day7challenge #innerdiscipline #selfimprovement #habits #standards #mindset #noexcuses #growthmindset",
        ])

    if script.mode == "member":
        return "\n".join([
            "This is not just a group.",
            "It is the room where the standard stays visible.",
            "",
            "Join the Inner Discipline 30 Day Challenge.",
            "Members unlock the Discipline Manual inside the group.",
            "",
            "Link in bio.",
            "",
            "#discipline #accountability #30daychallenge #innerdiscipline #selfimprovement #mindset #noexcuses #growthmindset #hardwork",
        ])

    return "\n".join([
        "Most people do not fail loudly. They drift quietly.",
        "",
        f'"{script.lines[0]}"',
        "",
        script.lines[2],
        "",
        "-",
        script.lines[-1],
        "",
        "#discipline #selfimprovement #mindset #noexcuses #innerdiscipline #accountability #growthmindset #hardwork",
    ])


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
                "chunk_size": PACING[script.pacing]["chunk_size"],
            })

            cursor += dur + (gap if i < len(script.lines) - 1 else 0.24)

        duration = min(cursor, REEL_SECONDS)
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
    print("\nINNER DISCIPLINE â€” GROWTH ENGINE v17 DAY LOOP FIX")
    print("=" * 64)
    print("RUN ID:", RUN_ID)
    print("GITHUB RUN NUMBER:", os.getenv("GITHUB_RUN_NUMBER", "local"))
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
    out_path = os.path.join(OUTPUT_DIR, f"reel_v17_{script.mode}_{script.category}_{date_str}_{RUN_ID}.mp4")

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
    auto_commit_state_files()

    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)

    print("=" * 64)
    print("COMPLETE")


if __name__ == "__main__":
    main()
