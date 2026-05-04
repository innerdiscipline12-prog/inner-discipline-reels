import os, random, glob, asyncio, json, shutil
import numpy as np
from moviepy.editor import *
from moviepy.video.fx import all as vfx
from moviepy.audio.fx import all as afx
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import edge_tts

# ================================================================
# INNER DISCIPLINE — DAILY ENGINE
# Output per run:
#   1 x reel_[date].mp4         — 15s short form
#   1 x longvideo_[date].mp4    — ~5 min continuous monologue
#
# Background videos: name them bg1.mp4, bg2.mp4 etc.
# ================================================================

W, H            = 1080, 1920
FPS             = 30
MAX_REEL_LENGTH = 15.0
LONG_VIDEO_SECS = 300   # 5 minutes target

FONT_PATH          = "Anton-Regular.ttf"
LOGO_PATH          = "logo.png"
LOGO_OPACITY       = 0.85
LOGO_SIZE          = 200
LOGO_BOTTOM_MARGIN = 120

MUSIC_DELAY = 1.5

os.makedirs("outputs", exist_ok=True)
os.makedirs("temp_segments", exist_ok=True)

# ================================================================
# PACING MODES
# Each mode changes TTS rate/pitch and chunk display speed.
# Confrontation = fast, punchy — hits like a slap
# Build         = slow, heavy — presses like a weight
# Story         = measured, human — lands like a truth
# ================================================================

PACING_MODES = {
    "confrontation": {
        "rate":  "-5%",     # Fast delivery
        "pitch": "-40Hz",   # Sharp tone
        "chunk_size": 2,    # Shorter chunks — rapid fire
    },
    "build": {
        "rate":  "-25%",    # Slow, weighted delivery
        "pitch": "-55Hz",   # Deeper tone
        "chunk_size": 3,    # Normal chunks — let words breathe
    },
    "story": {
        "rate":  "-15%",    # Measured, natural pace
        "pitch": "-45Hz",   # Neutral tone
        "chunk_size": 4,    # Longer chunks — narrative flow
    },
}

VOICE  = "en-US-GuyNeural"
VOLUME = "+0%"

# ================================================================
# MEMORY
# ================================================================

HOOK_MEMORY_FILE     = "hook_memory.json"
CATEGORY_MEMORY_FILE = "category_memory.json"
SET_STEP_FILE        = "set_step.json"

used_hooks    = json.load(open(HOOK_MEMORY_FILE))     if os.path.exists(HOOK_MEMORY_FILE)     else []
last_category = json.load(open(CATEGORY_MEMORY_FILE)) if os.path.exists(CATEGORY_MEMORY_FILE) else None
set_step      = json.load(open(SET_STEP_FILE))         if os.path.exists(SET_STEP_FILE)         else 0
if not isinstance(set_step, int):
    set_step = 0

# ================================================================
# VIDEO POOL
# ================================================================

def get_all_videos():
    return (
        glob.glob("bg*.mp4") +
        glob.glob("bg*.mov") +
        glob.glob("bg*.MP4")
    )

# ================================================================
# CONTENT BANK — REWRITTEN FOR EMOTIONAL WEIGHT
#
# Three pacing modes per category:
#   confrontation — fast, direct, aggressive
#   build         — slow, heavy, pressing
#   story         — narrative, third person, cinematic
# ================================================================

CONTENT = {

    # ----------------------------------------------------------------
    # IDENTITY — Who you've become vs who you said you'd be
    # ----------------------------------------------------------------
    "identity": {
        "confrontation": {
            "hooks": [
                "You became someone you don't recognise.",
                "You broke the promise you made to yourself.",
                "You know exactly what you're doing. And you keep doing it.",
                "You stopped fighting. Nobody even had to beat you.",
                "You made peace with failing. That's the worst part.",
                "You don't even flinch anymore. That's how deep it goes.",
                "You lowered the bar so many times you forgot where it was.",
                "You told yourself you'd change. You didn't.",
                "You built a comfortable version of failure and called it life.",
                "You sold yourself out. For nothing.",
            ],
            "truths": [
                "That's not a bad day. That's a pattern.",
                "That's not a mistake. That's who you're choosing to be.",
                "You did this. Every single day, you chose this.",
                "The man you used to respect wouldn't recognise you.",
                "This is what giving up slowly looks like.",
                "You are the thing standing between you and everything.",
                "There's no villain in this story. Just you.",
                "Every compromise you made added up to this moment.",
            ],
            "questions": [
                "Is this the man you're going to stay as?",
                "How much longer are you going to watch yourself fall?",
                "What would the version of you from five years ago say right now?",
                "At what point did you decide this was acceptable?",
                "Can you even look at yourself honestly anymore?",
            ],
        },
        "build": {
            "hooks": [
                "Somewhere along the way... you stopped showing up for yourself.",
                "There was a version of you that used to fight back.",
                "You remember the last time you were proud of yourself. It was a while ago.",
                "The man you planned to be is still waiting. He's been waiting for years.",
                "You used to have standards. Real ones. What happened to them.",
                "Every morning you wake up and feel it. The gap between who you are and who you meant to be.",
                "You carry this quietly. The weight of knowing you're capable of more.",
            ],
            "truths": [
                "The silence between who you are and who you could be is louder than anything.",
                "You haven't lost the ability. You've lost the decision.",
                "The gap doesn't close on its own. You have to walk toward it.",
                "Nobody is coming to pull you back. This is yours to fix.",
                "The version of you that didn't quit is still in there. Buried. But in there.",
            ],
            "questions": [
                "How much more time are you willing to give this version of yourself?",
                "What are you waiting for before you take yourself seriously?",
                "If not now, when. And if not you, who.",
            ],
        },
        "story": [
            "He had a plan. A real one. He wrote it down, told his friends, believed every word of it. Then life got heavy. And instead of pushing through, he adjusted. Just this once. Then again. Then it wasn't adjusting anymore. It was retreating. Nobody saw it happen. Not even him. Until one day he looked up and the man in the mirror was a stranger wearing his face.",
            "There's a man who checks his phone first thing every morning. Not for opportunity. For escape. He's been doing it so long he doesn't even notice anymore. He used to have a routine. A standard. He used to hold himself to something. He's not sure exactly when he let go. But he can feel the distance between then and now every single day.",
            "He made a promise to himself at twenty. A real one. The kind that felt unbreakable. By thirty, he couldn't remember the last time he kept it. He didn't fail dramatically. He failed quietly. One small compromise after another. Each one seemed reasonable at the time. Together they built the life he never wanted.",
        ],
    },

    # ----------------------------------------------------------------
    # COMFORT — The enemy that feels like a friend
    # ----------------------------------------------------------------
    "comfort": {
        "confrontation": {
            "hooks": [
                "You chose easy. Again.",
                "Comfort is the cage you built yourself.",
                "You stopped before it got hard. Like always.",
                "You knew what the right choice was. You made the other one.",
                "You protected your feelings instead of building your future.",
                "You folded the moment it cost you something real.",
                "You didn't fail. You chose not to try.",
                "Soft choices make a soft life. This is the proof.",
                "You avoided the hard thing and called it self-care.",
                "The version of you that was hungry is gone. Comfort killed it.",
            ],
            "truths": [
                "Comfort doesn't feel like failure because it feels good. That's the trap.",
                "Everything you want is on the other side of what you keep avoiding.",
                "Every time you chose easy, you made hard things harder.",
                "The cage has no lock. You just stopped trying the door.",
                "You'll never accidentally become great. You have to fight for it.",
            ],
            "questions": [
                "How comfortable are you willing to let yourself become?",
                "What has choosing easy actually given you?",
                "At what point does comfort become the thing you regret?",
                "Is the short-term relief worth the long-term cost?",
                "What are you protecting yourself from by staying safe?",
            ],
        },
        "build": {
            "hooks": [
                "Comfort doesn't feel like the enemy. That's why it wins.",
                "You've been resting long enough that the rest feels normal.",
                "The soft life crept up on you. You didn't choose it all at once.",
                "You earned the right to relax. Then relaxing became the plan.",
                "It was supposed to be temporary. The break, the pause, the wait. But here you still are.",
                "Nobody told you that comfort was the most dangerous place to stay.",
            ],
            "truths": [
                "Comfort is a slow thief. It takes your edge first. Then your hunger. Then your identity.",
                "You don't notice you've stopped growing until you try to move and can't.",
                "The things you keep postponing are the things that matter most.",
                "Ease is the environment where potential dies quietly.",
                "You were made for resistance. Without it, you soften in ways you don't see coming.",
            ],
            "questions": [
                "When did you last do something that genuinely challenged you?",
                "What are you capable of that comfort has been keeping hidden?",
                "If ease is the strategy, what is the destination?",
            ],
        },
        "story": [
            "He told himself he'd earned the rest. After everything. He deserved to breathe for a while. So he did. And breathing felt so good he did it a little longer. Then a little longer still. Months passed. He was comfortable. Happy, even. Then he looked at his life and realised that comfortable and happy aren't the same thing. And one of them had been slowly replacing the other without asking permission.",
            "She used to push. Hard. The kind of push that leaves marks on your hands and fire in your chest. Then she found a rhythm. Steady. Safe. Good enough. And good enough became the new ceiling. And the ceiling got lower every year. Not dramatically. Just quietly. The way all important things are lost. Slowly, then all at once.",
        ],
    },

    # ----------------------------------------------------------------
    # TIME — The resource you can't earn back
    # ----------------------------------------------------------------
    "time": {
        "confrontation": {
            "hooks": [
                "That day is gone. You're not getting it back.",
                "You wasted another one. That's the truth of it.",
                "Time doesn't pause while you figure it out.",
                "The clock moved. You didn't.",
                "Another day spent waiting for the right moment.",
                "You keep saying tomorrow like it's guaranteed.",
                "The gap between you and where you want to be just got wider.",
                "Every hour you delay is an hour you'll never spend building.",
                "You burned it. On nothing. Again.",
                "Time is the only thing you spend that you cannot replace.",
            ],
            "truths": [
                "The right moment you're waiting for doesn't exist. It never did.",
                "Delay is a decision. You just don't frame it that way.",
                "The years are going whether you use them or not.",
                "You can recover from almost anything. But you can't recover time.",
                "While you wait, someone else is building.",
            ],
            "questions": [
                "What exactly are you waiting for?",
                "How many more days are you willing to lose?",
                "Five years from now, what will you wish you'd started today?",
                "At what point does delay become a permanent choice?",
                "What would your life look like if you'd started six months ago?",
            ],
        },
        "build": {
            "hooks": [
                "You feel it sometimes. The quiet weight of time passing.",
                "Another year. And the thing you planned to do is still just a plan.",
                "You're not running out of time dramatically. You're losing it quietly.",
                "The version of your life you imagined is still waiting to begin.",
                "Somewhere between intentions and action, the days disappeared.",
                "The things you keep meaning to start are still exactly where you left them.",
            ],
            "truths": [
                "Time doesn't end suddenly. It erodes. Day by day until there's less of it than you thought.",
                "The future you plan for is built from the days you're spending right now.",
                "You can have urgency without panic. You just have to choose to move.",
                "Every day you don't start is a day you'll have to make up later.",
                "The life you want doesn't wait indefinitely. Neither does your ability to build it.",
            ],
            "questions": [
                "What would you do differently if you truly felt how limited your time was?",
                "Which version of regret are you building toward. The regret of trying or the regret of not.",
                "What would it mean for your future if you started today. Not tomorrow. Today.",
            ],
        },
        "story": [
            "He had five years left on the plan. Then four. Then three. He kept adjusting the timeline but not the effort. The deadline moved. The dream didn't. Eventually the deadline passed. And the dream just sat there, unchased, quietly becoming the thing he used to want. He's not sure exactly when the future became the past. But he knows it happened somewhere between waiting for the right moment and waiting too long.",
            "At forty she looked back at thirty and thought about everything she'd said she'd do. At thirty she'd looked back at twenty and thought the same thing. The pattern scared her more than the lost time. Not the individual years, but the rhythm of them. The way each decade became a container for good intentions and unused potential.",
        ],
    },

    # ----------------------------------------------------------------
    # CHALLENGE — The paid accountability group
    # ----------------------------------------------------------------
    "challenge": {
        "confrontation": {
            "hooks": [
                "You've been trying alone. It's not working.",
                "Willpower runs out. Accountability doesn't.",
                "You don't need more motivation. You need someone watching.",
                "Every person who has ever changed had a room around them.",
                "Doing it alone is a strategy. It's just not a winning one.",
                "You keep starting over because there's nobody to answer to.",
                "The reason you quit is always the same. There's no consequence.",
                "Accountability isn't weakness. It's the thing that actually works.",
                "30 days with the right people changes more than 3 years alone.",
                "Stop making private promises you have no reason to keep.",
            ],
            "truths": [
                "The environment you're in determines the standard you hold.",
                "When people are watching, you show up differently. Every time.",
                "A room full of people who won't accept your excuses is priceless.",
                "You don't have a discipline problem. You have an accountability gap.",
                "The group exists because lone wolves starve in winter.",
            ],
            "questions": [
                "How many more times are you going to restart alone?",
                "What would change if someone was watching every day?",
                "What's your excuse for not having accountability right now?",
                "If not this, then what's the plan?",
                "At what point does doing it alone become the problem rather than the solution?",
            ],
        },
        "build": {
            "hooks": [
                "There's a reason the best athletes have coaches. Even when they're already great.",
                "Discipline is easier when the environment demands it.",
                "The men who changed their lives didn't do it in isolation.",
                "You can be self-reliant and still need a room.",
                "The 30-day challenge exists because 30 days of accountability changes the brain.",
            ],
            "truths": [
                "Community isn't a crutch. It's the structure that lets you go further.",
                "You rise to the standard of the people around you. Always.",
                "The Inner Discipline Challenge is for the people who are serious enough to invest in themselves.",
                "Under twenty dollars a month. No excuses. Just accountability.",
                "Daily check-ins make the invisible visible. That's where change happens.",
            ],
            "questions": [
                "What would thirty days of real accountability produce in your life?",
                "What's twenty dollars if it's the thing that finally makes the difference?",
                "When was the last time you invested in yourself the way you invest in everything else?",
            ],
        },
        "story": [
            "He'd tried alone seventeen times. He counted once. Seventeen fresh starts, seventeen slow stops. Each one began with certainty and ended with the same familiar drift. He told himself he just needed more willpower. Then someone put him in a room with people who checked in every morning. People who didn't accept the usual excuses. The eighteenth time was different. Not because he was different. Because the environment was.",
        ],
    },

    # ----------------------------------------------------------------
    # PURPOSE — The deepest layer. Who you're becoming.
    # ----------------------------------------------------------------
    "purpose": {
        "confrontation": {
            "hooks": [
                "You were built for more than this comfortable nothing.",
                "Legacy doesn't build itself while you wait.",
                "The man you're meant to be is watching you settle.",
                "Greatness doesn't wait. And it doesn't forgive wasted years.",
                "You have one life. This is it. Not the practice run.",
                "Stop treating your potential like a backup plan.",
                "The world doesn't remember people who played it safe.",
                "The version of you that achieves something real starts today.",
                "Every day you coast is a day the better version of you doesn't exist.",
                "Your legacy is being written right now. What does today's line say?",
            ],
            "truths": [
                "Purpose isn't found. It's built. One decision at a time.",
                "The man you want to become is made in the moments nobody watches.",
                "You don't become great by accident. You become great by decision.",
                "Everything you want to leave behind gets built in private first.",
                "The mark you leave on the world starts with the mark you make on yourself.",
            ],
            "questions": [
                "What do you want people to say about you when it's over?",
                "Are you building something that will outlast you?",
                "What would your life look like if you lived it at full capacity?",
                "Who would you become if you stopped playing small?",
                "Is the life you're living the one you were built for?",
            ],
        },
        "build": {
            "hooks": [
                "Legacy is a quiet thing. It builds in the years nobody celebrates.",
                "The men who are remembered weren't always the loudest. They were the most consistent.",
                "There's a version of your life that future people will look back on with something like awe.",
                "The work you're doing in silence right now is the foundation of everything.",
                "Not every chapter looks like progress. Some look like patience. That counts too.",
                "Becoming who you're meant to be is slower than you want and more real than you expect.",
            ],
            "truths": [
                "Legacy is not a destination. It's the sum of daily decisions made over years.",
                "The man you're becoming shows up in how you handle the days that don't matter.",
                "Discipline practiced in private becomes character displayed in public.",
                "You don't have to be extraordinary every day. You have to be consistent.",
                "The best version of you isn't waiting for perfect conditions. It's built through imperfect ones.",
            ],
            "questions": [
                "What are you building that will still matter in ten years?",
                "Who is the man you are becoming, and are you proud of him?",
                "If today was a brick in the foundation of your legacy, what kind of brick was it?",
            ],
        },
        "story": [
            "He wasn't famous. Nobody interviewed him. Nobody watched him train at five in the morning or stay late when everyone else went home. But he showed up. Every day, for years, he showed up. And slowly, quietly, the life he built became the kind of life other people pointed at and said. That's what's possible. He never set out to inspire anyone. He just refused to disappear.",
            "She decided at thirty-two that she was going to become someone her children would be proud of. Not rich. Not famous. Just honest. Disciplined. Consistent. She started small. Too small to matter, she thought at the time. But small things done every day don't stay small. Five years later her kids didn't know the exact moment she changed. They just knew she was different. Solid. The kind of person you can lean on without warning.",
            "The young man asked the old man how he'd built something that lasted. The old man thought for a long time. Then he said. I just refused to stop on the days I wanted to quit. That's all. Every other day was easy. It was the days I wanted to stop that mattered. And I just didn't.",
        ],
    },
}

# ================================================================
# LONG VIDEO MONOLOGUE ARC
# The 5-minute video is one continuous speech with 7 acts.
# Each act has a different pacing mode and emotional register.
# Together they form a complete narrative journey.
# ================================================================

LONG_VIDEO_ARC = [
    # Act 1 — Cold hook. Confrontation. Pattern interrupt.
    {
        "name":   "HOOK",
        "pacing": "confrontation",
        "category_pool": ["identity", "comfort", "time"],
        "section": "hooks",
        "count":  1,
    },
    # Act 2 — Deepen the pain. Build mode. Let it press.
    {
        "name":   "DEEPEN",
        "pacing": "build",
        "category_pool": ["identity", "comfort"],
        "section": "hooks",
        "count":  1,
    },
    # Act 3 — Story. Third person. Viewer sees themselves in it.
    {
        "name":   "STORY",
        "pacing": "story",
        "category_pool": ["identity", "comfort", "time"],
        "section": "story",
        "count":  1,
    },
    # Act 4 — Truth. Confrontation. Hard landing.
    {
        "name":   "TRUTH",
        "pacing": "confrontation",
        "category_pool": ["identity", "time", "comfort"],
        "section": "truths",
        "count":  2,
    },
    # Act 5 — Rising tension. Build. Questions that press.
    {
        "name":   "TENSION",
        "pacing": "build",
        "category_pool": ["time", "identity"],
        "section": "questions",
        "count":  2,
    },
    # Act 6 — Purpose. Story. The turn. Hope through discipline.
    {
        "name":   "TURN",
        "pacing": "story",
        "category_pool": ["purpose"],
        "section": "story",
        "count":  1,
    },
    # Act 7 — CTA. Confrontation. Close hard.
    {
        "name":   "CLOSE",
        "pacing": "confrontation",
        "category_pool": ["challenge", "purpose"],
        "section": "hooks",
        "count":  1,
    },
]

# ================================================================
# REEL CATEGORY ROTATION
# ================================================================

SET_ORDER = ["identity", "comfort", "time", "challenge", "purpose"]

def get_next_category():
    global set_step, last_category
    cat           = SET_ORDER[set_step % len(SET_ORDER)]
    set_step     += 1
    last_category = cat
    return cat

# ================================================================
# CONTENT SELECTION — with memory to avoid repeats
# ================================================================

used_lines = []   # tracks all lines used this session to avoid repeats

def pick_line(category, section, pacing=None):
    """
    Picks a random unused line from the content bank.
    section: 'hooks', 'truths', 'questions', 'story'
    pacing: 'confrontation', 'build', 'story' (None = any)
    """
    cat_data = CONTENT.get(category, {})

    if section == "story":
        pool = cat_data.get("story", [])
    else:
        if pacing and pacing in cat_data:
            pool = cat_data[pacing].get(section, [])
        else:
            # Merge all pacing modes for this section
            pool = []
            for mode_data in cat_data.values():
                if isinstance(mode_data, dict):
                    pool += mode_data.get(section, [])

    available = [l for l in pool if l not in used_lines]
    if not available:
        available = pool.copy()   # reset if exhausted

    if not available:
        return ""

    chosen = random.choice(available)
    used_lines.append(chosen)
    return chosen

def build_reel_script(category):
    """Builds a 4-line script for a 15s reel."""
    pacing = random.choice(["confrontation", "build"])

    hook     = pick_line(category, "hooks",     pacing)
    truth    = pick_line(category, "truths",    pacing)
    question = pick_line(category, "questions", pacing)

    # CTA
    if category == "challenge":
        cta_pool = [
            "Join the Inner Discipline Challenge. DM DISCIPLINE.",
            "30 days. Facebook group. Under $20. DM DISCIPLINE.",
            "The group is open. DM DISCIPLINE.",
            "Stop doing it alone. DM DISCIPLINE.",
            "Daily check-ins. Real accountability. DM DISCIPLINE.",
        ]
    elif category == "purpose":
        cta_pool = [
            "Comment LEGEND if you're building.",
            "Type LEGACY if this hit.",
            "Start today. Comment PURPOSE.",
            "This is your sign. Comment LEGEND.",
            "Type LEGEND if you felt this.",
        ]
    else:
        cta_pool = [
            "Prove it. Comment DISCIPLINE.",
            "Type DISCIPLINE if you're done.",
            "Don't scroll. Commit.",
            "Lock in or leave.",
            "No excuses. Type DISCIPLINE.",
            "If you mean it - prove it.",
            "This is your moment.",
        ]

    cta = random.choice(cta_pool)
    return [hook, truth, question, cta], pacing

def build_long_video_script():
    """
    Builds the full monologue script for the 5-min long video.
    Returns list of (text, pacing_mode) tuples — one per line spoken.
    """
    lines = []
    used_categories = {}

    for act in LONG_VIDEO_ARC:
        pacing    = act["pacing"]
        cat_pool  = act["category_pool"]
        section   = act["section"]
        count     = act["count"]

        for _ in range(count):
            category = random.choice(cat_pool)
            line     = pick_line(category, section, pacing if section != "story" else None)
            if line:
                lines.append((line, pacing))

    return lines

# ================================================================
# LOGO OVERLAY
# ================================================================

def make_logo_overlay():
    if not os.path.exists(LOGO_PATH):
        print(f"⚠️  Logo not found — skipping.")
        return None

    logo   = Image.open(LOGO_PATH).convert("RGBA")
    aspect = logo.height / logo.width
    new_w  = LOGO_SIZE
    new_h  = int(LOGO_SIZE * aspect)
    logo   = logo.resize((new_w, new_h), Image.LANCZOS)

    r, g, b, a = logo.split()
    a    = a.point(lambda p: int(p * LOGO_OPACITY))
    logo = Image.merge("RGBA", (r, g, b, a))

    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x      = (W - new_w) // 2
    y      = H - new_h - LOGO_BOTTOM_MARGIN
    canvas.paste(logo, (x, y), logo)
    return np.array(canvas)

# ================================================================
# TEXT ENGINE — orange first word, chest position
# ================================================================

def make_text(text, highlight_first_word=True):
    text = text.replace("\u2014", "-").replace("\u2013", "-")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2026", "...")
    text = text.upper()

    img  = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if not os.path.exists(FONT_PATH):
        raise FileNotFoundError(f"Font not found: '{FONT_PATH}'. Download Anton-Regular.ttf from Google Fonts.")

    font_size = 88
    font      = ImageFont.truetype(FONT_PATH, font_size)
    max_width = W - 240

    words   = text.split()
    lines   = []
    current = ""

    for word in words:
        test = (current + " " + word).strip()
        if draw.textlength(test, font=font) <= max_width:
            current = test
        else:
            lines.append(current)
            current = word
    lines.append(current)

    total_height     = len(lines) * (font_size + 22)
    y                = int(H * 0.62) - total_height // 2
    first_word_drawn = False
    ORANGE           = (255, 140, 0, 255)
    WHITE            = (255, 255, 255, 255)

    for line in lines:
        line_words = line.split()
        if not line_words:
            y += font_size + 22
            continue

        line_width = draw.textlength(line, font=font)
        x          = (W - line_width) // 2

        for i, word in enumerate(line_words):
            word_width  = draw.textlength(word, font=font)
            space_width = draw.textlength(" ", font=font) if i < len(line_words) - 1 else 0

            if highlight_first_word and not first_word_drawn:
                color            = ORANGE
                first_word_drawn = True
            else:
                color = WHITE

            draw.text((x, y), word, font=font, fill=color, stroke_width=5, stroke_fill="black")
            x += word_width + space_width

        y += font_size + 22

    return np.array(img)

# ================================================================
# TTS — pacing-aware
# ================================================================

async def tts_async(text, filename, rate, pitch):
    communicate = edge_tts.Communicate(text, VOICE, rate=rate, pitch=pitch, volume=VOLUME)
    await communicate.save(filename)

def generate_voice(text, filename, pacing="confrontation"):
    mode  = PACING_MODES.get(pacing, PACING_MODES["confrontation"])
    asyncio.run(tts_async(text, filename, mode["rate"], mode["pitch"]))

# ================================================================
# PUNCH ZOOM ENGINE
# ================================================================

def get_punch_scale(t, punches):
    base  = 1.0
    scale = base
    for punch_t, peak, attack in punches:
        delta = t - punch_t
        if delta < 0:
            continue
        elif delta < attack:
            punch_scale = base + (peak - base) * (delta / attack) ** 0.5
        else:
            release     = max(0.0, 1.0 - (delta - attack) / 3.0)
            punch_scale = base + (peak - base) * release
        scale = max(scale, punch_scale)
    return scale

LINE_PUNCH = {
    0: (1.08, 0.6),
    2: (1.07, 0.5),
    3: (1.06, 0.4),
}

# ================================================================
# VIDEO BACKGROUND LOADER
# ================================================================

def load_video_background(video_path, target_duration):
    clip = VideoFileClip(video_path)

    clip_ratio   = clip.w / clip.h
    target_ratio = W / H

    if clip_ratio > target_ratio:
        clip = clip.resize(height=H)
    else:
        clip = clip.resize(width=W)

    x_center = clip.w / 2
    y_center  = clip.h / 2
    clip      = clip.crop(x_center=x_center, y_center=y_center, width=W, height=H)

    if clip.duration < target_duration:
        clip = vfx.loop(clip, duration=target_duration)

    clip = clip.subclip(0, target_duration)
    clip = clip.fx(vfx.colorx, 0.90)
    return clip

# ================================================================
# VIGNETTE OVERLAY
# ================================================================

def make_vignette(duration):
    arr             = np.zeros((H, W, 4), dtype=np.uint8)
    vignette_height = int(H * 0.55)
    for row in range(vignette_height):
        alpha          = int(255 * (1.0 - (row / vignette_height) ** 1.6))
        arr[row, :, 3] = alpha
    return ImageClip(arr).set_duration(duration)

# ================================================================
# CHUNK SPLITTER
# ================================================================

def split_into_chunks(text, chunk_size=3):
    """Split text into word chunks. Story mode splits at punctuation."""
    # Try punctuation split first for natural phrasing
    import re
    sentences = re.split(r'(?<=[.!?,])\s+', text.strip())
    if len(sentences) > 1:
        return [s.strip() for s in sentences if s.strip()]
    # Fallback: word chunks
    words  = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i + chunk_size]))
    return chunks

# ================================================================
# TEXT CLIP BUILDER — reel vs long video transitions
# ================================================================

def make_text_clip(text_img, start, duration, mode="reel"):
    """
    mode="reel"  → pop/snap: scale 0.7→1.0 in 0.08s, hard cut out
    mode="long"  → fade/slide: fadein 0.2s, fadeout 0.2s
    """
    clip = ImageClip(text_img).set_start(start).set_duration(duration)

    if mode == "reel":
        # Pop/snap — aggressive scale up
        def pop_frame(get_frame, t):
            frame = get_frame(t)
            snap_dur = 0.08
            if t < snap_dur:
                scale    = 0.75 + 0.25 * (t / snap_dur)
                new_w    = max(1, int(W * scale))
                new_h    = max(1, int(H * scale))
                pil      = Image.fromarray(frame).resize((new_w, new_h), Image.BILINEAR)
                canvas   = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                offset_x = (W - new_w) // 2
                offset_y = (H - new_h) // 2
                canvas.paste(Image.fromarray(frame) if scale == 1.0 else pil, (offset_x, offset_y))
                return np.array(canvas)
            return frame
        clip = clip.fl(pop_frame)
        clip = clip.fadeout(0.06)

    else:
        # Smooth fade + slide up from 18px below
        def slide_frame(get_frame, t):
            frame    = get_frame(t)
            fade_dur = 0.20
            if t < fade_dur:
                progress  = t / fade_dur
                offset_y  = int(18 * (1.0 - progress))
                alpha     = progress
                pil       = Image.fromarray(frame)
                shifted   = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                shifted.paste(pil, (0, offset_y))
                arr       = np.array(shifted).astype(float)
                arr[..., 3] = arr[..., 3] * alpha
                return arr.astype(np.uint8)
            return frame
        clip = clip.fl(slide_frame)
        clip = clip.fadeout(0.20)

    return clip

# ================================================================
# CORE VIDEO BUILDER
# Shared by reel and long video.
# mode="reel"  → 15s hard cap, pop transitions, confrontation pacing
# mode="long"  → arc pacing, slide transitions, sync per voice duration
# ================================================================

def build_video_segment(
    lines_with_pacing,   # list of (text, pacing_mode)
    video_path,
    output_path,
    max_duration=None,
    seg_index=0,
    transition_mode="reel",   # "reel" or "long"
):
    voice_files = []

    try:
        # ================================================================
        # PHASE A — Generate all voice files FIRST
        # Measure actual durations before building timeline.
        # This is the sync fix — we never assume duration, we measure it.
        # ================================================================

        print(f"  🎙️  Generating voice for {len(lines_with_pacing)} lines...")
        voice_data = []   # list of (voice_file, actual_duration, pacing, chunk_size)

        for i, (line, pacing) in enumerate(lines_with_pacing):
            mode       = PACING_MODES.get(pacing, PACING_MODES["confrontation"])
            chunk_size = mode["chunk_size"]
            vf         = f"temp_segments/v_{seg_index}_{i}.mp3"
            voice_files.append(vf)
            generate_voice(line, vf, pacing)
            audio    = AudioFileClip(vf)
            duration = audio.duration
            audio.close()
            voice_data.append((vf, duration, pacing, chunk_size, line))

        # ================================================================
        # PHASE B — Check total duration fits max_duration (reel only)
        # If total voice would exceed 15s, drop last lines until it fits.
        # ================================================================

        if max_duration:
            lead_in  = 0.5
            gap      = 0.12
            total    = lead_in + sum(d + gap for _, d, _, _, _ in voice_data)
            # Trim lines from the end until it fits
            while total > max_duration and len(voice_data) > 1:
                removed  = voice_data.pop()
                if removed[0] in voice_files:
                    voice_files.remove(removed[0])
                    if os.path.exists(removed[0]):
                        os.remove(removed[0])
                total = lead_in + sum(d + gap for _, d, _, _, _ in voice_data)

        # ================================================================
        # PHASE C — Build subtitle + audio timeline from measured durations
        # ================================================================

        clips       = []
        audio_clips = []
        punch_times = []
        timeline    = 0.5
        FADE_OUT    = 0.12

        for i, (vf, voice_duration, pacing, chunk_size, line) in enumerate(voice_data):
            audio = AudioFileClip(vf)
            audio_clips.append(audio.set_start(timeline))

            # Punch registration
            is_punch = i == 0 or i == len(voice_data) - 2 or i == len(voice_data) - 1
            if is_punch:
                peak   = 1.08 if i == 0 else 1.06
                attack = 0.6  if i == 0 else 0.4
                punch_times.append((timeline, peak, attack))

            # ✅ SYNC FIX — chunks sized from ACTUAL voice_duration
            chunks         = split_into_chunks(line, chunk_size)
            num_chunks     = max(len(chunks), 1)
            chunk_duration = voice_duration / num_chunks   # exact slice per chunk

            for j, chunk in enumerate(chunks):
                chunk_start = timeline + j * chunk_duration

                # Last chunk absorbs any remainder exactly
                if j == num_chunks - 1:
                    text_duration = max(0.1, (voice_duration - j * chunk_duration) + FADE_OUT)
                else:
                    text_duration = chunk_duration

                text_img  = make_text(chunk, highlight_first_word=(j == 0))
                text_clip = make_text_clip(text_img, chunk_start, text_duration, mode=transition_mode)
                clips.append(text_clip)

            gap       = 0.12 if i < len(voice_data) - 1 else FADE_OUT
            timeline += voice_duration + gap

        reel_duration = float(timeline)
        if max_duration:
            reel_duration = min(reel_duration, float(max_duration))

        print(f"  ⏱️  Duration: {reel_duration:.2f}s")

        # ================================================================
        # PHASE D — Render video
        # ================================================================

        bg_clip = load_video_background(video_path, reel_duration)

        def zoom_frame(get_frame, t):
            scale = get_punch_scale(t, punch_times)
            frame = get_frame(t)
            if scale < 1.005:
                return frame
            new_w = int(W * scale)
            new_h = int(H * scale)
            pil   = Image.fromarray(frame).resize((new_w, new_h), Image.BILINEAR)
            arr   = np.array(pil)
            top   = (new_h - H) // 2
            left  = (new_w - W) // 2
            return arr[top:top+H, left:left+W]

        bg_clip    = bg_clip.fl(zoom_frame, apply_to=["mask"])
        logo_array = make_logo_overlay()
        all_layers = [bg_clip, make_vignette(reel_duration)] + clips

        if logo_array is not None:
            all_layers.append(
                ImageClip(logo_array).set_duration(reel_duration).fadein(0.4)
            )

        final_video = CompositeVideoClip(all_layers, size=(W, H))
        final_video = final_video.set_duration(reel_duration).fadeout(0.3)

        # Audio
        final_voice = CompositeAudioClip(audio_clips)

        if os.path.exists("music.mp3"):
            music = AudioFileClip("music.mp3")
            md    = reel_duration - MUSIC_DELAY
            if md > 0:
                music       = afx.audio_loop(music, duration=md)
                music       = music.audio_fadein(0.8).volumex(0.13).set_start(MUSIC_DELAY)
                final_audio = CompositeAudioClip([music, final_voice.volumex(1.12)])
            else:
                final_audio = final_voice
        else:
            final_audio = final_voice

        final = final_video.set_audio(final_audio)
        final.write_videofile(
            output_path, fps=FPS, codec="libx264",
            audio_codec="aac", threads=4, preset="fast"
        )
        print(f"  ✅ Done → {output_path}  ({reel_duration:.2f}s)")
        return output_path

    except Exception as e:
        import traceback
        print(f"  ❌ Failed: {e}")
        traceback.print_exc()
        return None

    finally:
        for vf in voice_files:
            if os.path.exists(vf):
                os.remove(vf)

# ================================================================
# CAPTION + HASHTAG BUILDER
# ================================================================

CAPTION_OPENERS = {
    "identity": [
        "Most people won't admit this to themselves.",
        "Read this slowly. It's about you.",
        "The truth nobody wants to say.",
        "Be honest with yourself for 10 seconds.",
        "This is the part nobody talks about.",
    ],
    "comfort": [
        "Comfort is the most dangerous place to stay.",
        "This is what playing it safe actually costs you.",
        "The cage you built yourself is still a cage.",
        "Stop scrolling. This is for you.",
    ],
    "time": [
        "You needed to hear this today.",
        "The most expensive thing you keep wasting.",
        "Save this. You'll need it again.",
        "Time doesn't wait. And neither does this.",
    ],
    "challenge": [
        "You've been trying to do this alone. There's a better way.",
        "30 days of accountability. A room that won't accept your excuses.",
        "Most people quit because no one is watching. We fix that.",
        "The Inner Discipline Challenge is open. This is your sign.",
    ],
    "purpose": [
        "This one is for the men building in silence.",
        "Legacy is built in the moments nobody celebrates.",
        "The man you're meant to be is built today.",
        "Not everyone is meant for average. This is for you.",
    ],
}

CAPTION_CLOSERS = {
    "identity":  ["Comment DISCIPLINE if you're locking in.", "Tag someone who needs this.", "Follow @innerdiscipline for daily content."],
    "comfort":   ["Comment DISCIPLINE if you're done settling.", "Save this for the next time comfort wins.", "Follow @innerdiscipline."],
    "time":      ["Comment DISCIPLINE if today is the day.", "Stop waiting. Comment DISCIPLINE.", "Follow @innerdiscipline for more."],
    "challenge": ["Link in bio. Join the Inner Discipline Challenge.", "Under $20/month. Link in bio. No excuses.", "The group is open. Link in bio."],
    "purpose":   ["Comment LEGEND if you're building.", "Type LEGACY if this hit.", "Follow @innerdiscipline — for the ones who are serious."],
}

HASHTAGS = {
    "identity":  "#discipline #mindset #selfimprovement #innerdiscipline #accountability #noexcuses #selfmastery #growthmindset #hardwork #mentalstrength",
    "comfort":   "#discipline #motivation #selfimprovement #innerdiscipline #growthmindset #noexcuses #selfmastery #hardwork #mindset #consistency",
    "time":      "#discipline #motivation #mindset #innerdiscipline #selfimprovement #consistency #focus #hardwork #growthmindset #dailymotivation",
    "challenge": "#30daychallenge #accountability #innerdisciplinechallenge #disciplinegroup #30days #facebookgroup #selfimprovement #discipline #mindset #hardwork",
    "purpose":   "#legacy #purpose #innerdiscipline #becomelegend #growthmindset #selfmastery #discipline #mentalstrength #levelup #hardwork",
}

def build_caption(script_lines, category):
    opener   = random.choice(CAPTION_OPENERS.get(category, CAPTION_OPENERS["identity"]))
    closer   = random.choice(CAPTION_CLOSERS.get(category, CAPTION_CLOSERS["identity"]))
    hashtags = HASHTAGS.get(category, HASHTAGS["identity"])
    hook     = script_lines[0] if script_lines else ""

    return "\n".join([
        opener, "",
        f'"{hook}"', "",
        script_lines[1] if len(script_lines) > 1 else "", "",
        "-",
        closer, "",
        hashtags,
    ])

# ================================================================
# RUN
# ================================================================

print("\n🎬 INNER DISCIPLINE — DAILY ENGINE")
print("   Output: 1 reel (15s) + 1 long video (~5 min)")
print("=" * 52)

all_videos = get_all_videos()
if not all_videos:
    raise Exception("No background videos found. Add bg1.mp4 etc.")

date_str = datetime.now().strftime("%Y%m%d_%H%M")
bg_video = all_videos[0]   # use first available — add more for variety

# ================================================================
# PHASE 1 — Daily Reel (15s)
# ================================================================

print("\n📱 Phase 1 — Daily Reel...")

reel_category             = get_next_category()
reel_script, reel_pacing  = build_reel_script(reel_category)
reel_lines                = [(line, reel_pacing) for line in reel_script]
reel_path                 = f"outputs/reel_{date_str}.mp4"

print(f"   Category: {reel_category.upper()} | Pacing: {reel_pacing}")

result = build_video_segment(
    lines_with_pacing=reel_lines,
    video_path=bg_video,
    output_path=reel_path,
    max_duration=MAX_REEL_LENGTH,
    seg_index=0,
    transition_mode="reel",
)

if result:
    caption  = build_caption(reel_script, reel_category)
    base     = os.path.splitext(reel_path)[0]
    open(f"{base}_title.txt",   "w").write(f"{reel_script[0]} | INNER DISCIPLINE")
    open(f"{base}_caption.txt", "w").write(caption)

# ================================================================
# PHASE 2 — Long Video (~5 min continuous monologue)
# ================================================================

print("\n🎥 Phase 2 — Long Video monologue...")

long_script   = build_long_video_script()
long_path     = f"outputs/longvideo_{date_str}.mp4"

print(f"   Arc: {len(long_script)} lines across {len(LONG_VIDEO_ARC)} acts")
for act, (line, pacing) in zip(LONG_VIDEO_ARC, long_script):
    print(f"   [{act['name']}:{pacing}] {line[:60]}...")

build_video_segment(
    lines_with_pacing=long_script,
    video_path=bg_video,
    output_path=long_path,
    max_duration=LONG_VIDEO_SECS,
    seg_index=99,
    transition_mode="long",
)

# ================================================================
# CLEANUP + MEMORY
# ================================================================

if os.path.exists("temp_segments"):
    shutil.rmtree("temp_segments")

json.dump(used_hooks,    open(HOOK_MEMORY_FILE,     "w"))
json.dump(last_category, open(CATEGORY_MEMORY_FILE, "w"))
json.dump(set_step,      open(SET_STEP_FILE,         "w"))

print("\n" + "=" * 52)
print(f"✅ COMPLETE")
print(f"   📱 Reel      → {reel_path}")
print(f"   🎥 Long video → {long_path}")
print("=" * 52)
