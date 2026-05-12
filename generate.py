import os, random, glob, asyncio, json, shutil, subprocess
import numpy as np
from moviepy.editor import (
    VideoFileClip, ImageClip, AudioFileClip,
    CompositeVideoClip, CompositeAudioClip, VideoClip
)
from moviepy.audio.fx import all as afx
from moviepy.video.fx import all as vfx
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import edge_tts

# ================================================================
# SETTINGS
# ================================================================

W, H            = 1080, 1920
FPS             = 30
MAX_REEL_LENGTH = 15.0
LONG_VIDEO_SECS = 300

FONT_PATH          = "Anton-Regular.ttf"
LOGO_PATH          = "logo.png"
LOGO_OPACITY       = 0.60
LOGO_SIZE          = 150
LOGO_BOTTOM_MARGIN = 120
MUSIC_DELAY        = 1.5
VOICE              = "en-US-GuyNeural"
VOLUME             = "+0%"

os.makedirs("outputs",       exist_ok=True)
os.makedirs("temp_segments", exist_ok=True)

# ================================================================
# PACING MODES
# ================================================================

PACING_MODES = {
    "confrontation": {"rate": "-18%", "pitch": "-40Hz", "chunk_size": 2},  # controlled punch
    "build":         {"rate": "-32%", "pitch": "-55Hz", "chunk_size": 3},  # heavy, weighted
    "story":         {"rate": "-22%", "pitch": "-45Hz", "chunk_size": 3},  # measured, human
}

# ================================================================
# MEMORY
# ================================================================

HOOK_MEMORY_FILE     = "hook_memory.json"
CATEGORY_MEMORY_FILE = "category_memory.json"
SET_STEP_FILE        = "set_step.json"
USED_LINES_FILE      = "used_lines.json"   # âœ… persists used content across runs

used_hooks    = json.load(open(HOOK_MEMORY_FILE))     if os.path.exists(HOOK_MEMORY_FILE)     else []
last_category = json.load(open(CATEGORY_MEMORY_FILE)) if os.path.exists(CATEGORY_MEMORY_FILE) else None
set_step      = json.load(open(SET_STEP_FILE))         if os.path.exists(SET_STEP_FILE)         else 0
if not isinstance(set_step, int):
    set_step = 0

# ================================================================
# VIDEO POOL
# ================================================================

def get_all_videos():
    return glob.glob("bg*.mp4") + glob.glob("bg*.mov") + glob.glob("bg*.MP4")

# ================================================================
# CONTENT BANK â€” Fresh lines across 4 directions:
# Identity crisis, Mental toughness, Masculinity, Daily habits
# ================================================================

CONTENT = {

    # ----------------------------------------------------------------
    # IDENTITY â€” Deeper crisis. Who you have become.
    # ----------------------------------------------------------------
    "identity": {
        "confrontation": {
            "hooks": [
                "You do not even recognise yourself anymore.",
                "You used to have standards. Look at them now.",
                "The man you promised to be is watching you settle.",
                "You have become the person you used to judge.",
                "You traded your edge for comfort and called it growth.",
                "You know exactly what you are doing. That is the worst part.",
                "You stopped holding yourself accountable. Nobody else will.",
                "You are building a life you will be ashamed of.",
                "The version of you from five years ago would not respect you.",
                "You do not even fight yourself anymore. You just give in.",
                "You lowered the bar so many times the bar is on the floor.",
                "You are performing discipline. You are not living it.",
                "Every mirror shows you the man you chose to become.",
                "You made weakness a habit. Now it feels like personality.",
                "You are comfortable with failure. That is the real problem.",
            ],
            "truths": [
                "That is not a rough patch. That is who you are becoming.",
                "The man you are today is the sum of every choice you avoided.",
                "You are not stuck. You are choosing this every single day.",
                "Somewhere you decided less was acceptable. That decision stuck.",
                "Nobody forced this on you. You built it one excuse at a time.",
                "This is what slow surrender looks like from the inside.",
                "The identity you are living was never chosen. It was settled for.",
                "You are not struggling. You are coasting. There is a difference.",
            ],
            "questions": [
                "When did you stop being someone you respected?",
                "What would it take for you to finally hold yourself accountable?",
                "How long are you going to pretend this version of you is acceptable?",
                "If nothing changes, who will you be in five years?",
                "At what point did you stop being the man and start being the excuse?",
                "Are you building an identity or inheriting one by default?",
            ],
        },
        "build": {
            "hooks": [
                "There is a version of you buried under years of small surrenders.",
                "You feel it every morning. The distance between who you are and who you were meant to be.",
                "The man you planned to become did not disappear. He is waiting.",
                "Identity is not what you say you are. It is what you do when no one is watching.",
                "You have been drifting so long that drift feels like direction.",
                "The gap between your standards and your actions has never been wider.",
                "You carry a version of yourself that you have never fully become.",
            ],
            "truths": [
                "Character is built in the moments you think do not matter. They all matter.",
                "You do not find yourself. You build yourself through repeated decisions.",
                "The man you are becoming is decided in the hours nobody sees.",
                "Reclaiming your identity starts with one decision held long enough to become a pattern.",
                "You cannot think your way into a new identity. You have to act your way there.",
            ],
            "questions": [
                "What would you do differently if you truly believed you were capable of more?",
                "Who were you before the world convinced you to aim lower?",
                "What is one standard you dropped that you need to pick back up today?",
                "If you lived by your own values for thirty days who would you become?",
            ],
        },
        "story": [
            "He used to be the one people counted on. The one who followed through. Then gradually almost invisibly he stopped. Not all at once. Just a little less reliable each month. A little more willing to let himself down quietly. Until one day someone who used to admire him looked at him differently. And he knew why. Because he had been looking at himself the same way for a long time.",
            "He had a standard once. It was not written anywhere but he felt it. Like a line he would not cross. Then one day he crossed it. Just barely. Then again. Then the line moved. Not dramatically. Just enough that he did not have to feel it. He told himself he was evolving. He was not. He was retreating. And calling it wisdom.",
            "Every morning he woke up with intentions. Every night he went to sleep with excuses. The gap between the two was his life. He knew it. He had known it for years. But knowing and changing are not the same thing. And every day he did not change the gap got a little more permanent.",
            "He was not a bad man. That was the thing. He was a decent man who had made peace with not becoming the man he was capable of being. And somewhere in that peace was a quiet tragedy that nobody around him could see. But he could feel it. Every single day.",
        ],
    },

    # ----------------------------------------------------------------
    # MENTAL â€” Toughness. Suffering. Not breaking.
    # ----------------------------------------------------------------
    "mental": {
        "confrontation": {
            "hooks": [
                "You quit the moment it got uncomfortable.",
                "Pain is a signal. You are reading it wrong.",
                "You are not tired. You are soft. There is a difference.",
                "Every hard thing you avoided made the next one harder.",
                "You fold under pressure because you have never practiced staying.",
                "The first sign of difficulty and you look for the exit.",
                "Mental weakness does not announce itself. It just keeps choosing easy.",
                "You called it burnout. It was resistance. And you lost.",
                "Discomfort is the price of growth. You keep refusing to pay.",
                "You stop exactly where it starts to count.",
            ],
            "truths": [
                "Toughness is not a trait. It is a practice. And you are out of practice.",
                "Every time you quit early you train yourself to quit early.",
                "The mind breaks before the body. Every time. Train the mind first.",
                "Suffering is not the enemy. Avoidance is.",
                "You do not get stronger by staying comfortable. You get comfortable.",
                "The reps that build you are the ones you do not want to do.",
            ],
            "questions": [
                "When was the last time you stayed when everything in you said go?",
                "What are you capable of if you stop listening to the part that wants to quit?",
                "How much of your ceiling is self-imposed?",
                "What would change if you decided discomfort was not a reason to stop?",
                "What are you avoiding right now that you know you need to face?",
            ],
        },
        "build": {
            "hooks": [
                "The hard days are not punishment. They are curriculum.",
                "Toughness is built in the moments you stay when you want to leave.",
                "Nobody becomes mentally strong in comfort. Comfort is where strength dies.",
                "Every difficult season you survived made you something. Did you notice?",
                "Pressure does not create character. It reveals it. And it can build it.",
                "The version of you that does not break is built through repeated exposure to breaking points.",
            ],
            "truths": [
                "The suffering you avoid now becomes the weakness you carry later.",
                "Mental toughness is not about feeling nothing. It is about moving despite feeling everything.",
                "You become what you repeatedly do under pressure. Not what you intend.",
                "The hardest moments are the ones that decide who you are becoming.",
                "Resilience is not bouncing back. It is walking forward while still carrying the weight.",
            ],
            "questions": [
                "What would you be capable of if you stopped letting discomfort make your decisions?",
                "Which hard thing have you been avoiding that is quietly making you weaker?",
                "What does the strongest version of you do in the moment you want to quit?",
            ],
        },
        "story": [
            "He did not quit dramatically. He just stopped pushing. And stopping felt reasonable at the time. It always does. A week passed. Then a month. Then the thing he had been building started to feel like something that happened to someone else. He had not lost his ability. He had lost his willingness. And willingness is harder to rebuild than ability.",
            "There was a morning he showed up when everything in him said do not. His body was heavy. His mind was loud with reasons to stay. He went anyway. He did not perform well. He did not feel good about it afterward. But he showed up. And that showing up quietly without drama without reward was the most important thing he did that year.",
            "He thought mental toughness was about never feeling weak. He was wrong. It was about feeling completely broken and still not using it as a reason to stop. The feeling was allowed. The quitting was not. Once he understood that everything changed. Not immediately. But permanently.",
        ],
    },

    # ----------------------------------------------------------------
    # MASCULINITY â€” Being a real man. Standards. Presence.
    # ----------------------------------------------------------------
    "masculinity": {
        "confrontation": {
            "hooks": [
                "You are not the man your household needs you to be.",
                "Real men do not need applause for doing what they should.",
                "You have been waiting for someone to make you step up.",
                "The world does not need your potential. It needs your presence.",
                "You outsourced your responsibilities and called it balance.",
                "A man who cannot lead himself cannot lead anything.",
                "You are present in the room but absent in the ways that matter.",
                "The sons watching you are learning what a man does.",
                "You demand respect you have not earned through consistent action.",
                "Masculinity is not performance. It is what you do when no one is watching.",
            ],
            "truths": [
                "A real man does not need external pressure to hold his standard.",
                "Your presence or absence is shaping people around you whether you know it or not.",
                "The measure of a man is not what he says. It is what he does consistently.",
                "Leadership starts with self-governance. You cannot give what you do not have.",
                "Strength is not loudness. It is steadiness under pressure over time.",
                "The men who matter are not the ones who were perfect. They are the ones who kept showing up.",
            ],
            "questions": [
                "Are you the kind of man you would want your son to become?",
                "What standard are you setting for the people who are watching you?",
                "Are you leading or just occupying space?",
                "If your actions were the only definition of masculinity what would it mean?",
                "What does the man you most respect do that you are not doing?",
            ],
        },
        "build": {
            "hooks": [
                "Becoming a real man is not a moment. It is a decade of decisions.",
                "The standard of a man is set by what he tolerates in himself.",
                "A man is built in his private decisions. Not his public ones.",
                "Masculinity that only shows up when it is convenient is not masculinity.",
                "The most powerful thing a man can do is hold himself accountable before anyone else does.",
            ],
            "truths": [
                "A man who disciplines himself does not need to be controlled by the world.",
                "Real strength is built in silence tested in difficulty and revealed under pressure.",
                "The men worth following are not the most talented. They are the most consistent.",
                "Your word to yourself is the foundation of your character. Keep it.",
                "A man who shows up for himself will naturally show up for everyone who depends on him.",
            ],
            "questions": [
                "What is one standard you need to raise starting today?",
                "Are the people who depend on you getting the best version of you or the leftover version?",
                "What would change if you held yourself to the same standard you expect from others?",
            ],
        },
        "story": [
            "His father was not perfect. Nobody is. But he showed up. Every morning every obligation every hard conversation. He did not complain loudly. He did not demand credit. He just handled what needed to be handled and moved on. When he was gone the people who loved him did not talk about his achievements. They talked about how he made them feel safe. How nothing felt uncertain when he was in the room.",
            "He used to think being a man meant never showing weakness. Then he watched a man he respected cry at his father funeral. Controlled. Present. Not hiding. And he realised that was not weakness. That was strength that was complete enough to feel everything without letting it make him irresponsible.",
        ],
    },

    # ----------------------------------------------------------------
    # HABITS â€” Daily discipline. Routine. The unsexy work.
    # ----------------------------------------------------------------
    "habits": {
        "confrontation": {
            "hooks": [
                "Your mornings are soft and your results show it.",
                "You do not have bad luck. You have bad habits.",
                "The routine you keep is the life you build. Look at it honestly.",
                "You sleep in and wonder why you fall behind.",
                "Every day without a standard is a vote for the man you do not want to be.",
                "You are what you repeatedly do. Not what you plan to do.",
                "Your habits are either building you or shrinking you. There is no neutral.",
                "The undisciplined morning costs the entire day.",
                "You are waiting for motivation. Discipline does not wait.",
                "Consistency is the only strategy that actually works. You know this.",
            ],
            "truths": [
                "Motivation gets you started. Habit keeps you going. You need the second one.",
                "The gap between who you are and who you want to be is filled by daily action.",
                "You cannot think your way to a better life. You have to routine your way there.",
                "Small daily actions compounded over years are more powerful than any single decision.",
                "The person you become is built in the hours everyone else uses for comfort.",
                "Discipline is not restriction. It is the foundation that makes freedom possible.",
            ],
            "questions": [
                "What does your morning say about who you are becoming?",
                "If your daily routine stayed exactly as it is where will you be in two years?",
                "What is one habit you need to kill and one you need to build starting today?",
                "Are your habits designed by intention or inherited by default?",
                "What would your life look like if you treated your daily habits as seriously as your biggest goals?",
            ],
        },
        "build": {
            "hooks": [
                "Every great life was built by someone who showed up on the days they did not feel like it.",
                "The unsexy work done consistently produces the only results worth having.",
                "Your daily habits are quietly writing the story of your life.",
                "The morning belongs to the man who claims it before the world does.",
                "Small disciplines practiced daily become the architecture of a life worth living.",
                "You do not rise to the level of your goals. You fall to the level of your habits.",
            ],
            "truths": [
                "A habit takes weeks to build and days to lose. Protect what you have built.",
                "The man who controls his morning controls his mindset. The man who controls his mindset controls his life.",
                "Routine is not the enemy of freedom. It is the structure that makes everything else possible.",
                "The compounding of daily discipline is invisible in the short term and undeniable in the long term.",
                "You do not need a perfect system. You need a consistent one.",
            ],
            "questions": [
                "Which part of your routine is serving the man you are becoming?",
                "What would you add to your mornings if you truly believed they shaped everything else?",
                "What would your life look like if you treated every day as if it mattered?",
            ],
        },
        "story": [
            "He did not have a dramatic transformation. There was no single moment that changed everything. Just one morning where he decided to do the thing he had been postponing. Then the next morning he did it again. Three weeks later it was not a decision anymore. It was just what he did. Six months later the results showed up. Not because he was gifted. Because he was consistent.",
            "He used to say he would start when things settled down. When work slowed. When life got easier. He said it for three years. Things never settled. They never do. The men who built something real did not wait for the right conditions. They built the conditions through the consistency of their habits.",
            "Every morning at five he did the same things in the same order. Not because someone told him to. Because he had learned that the structure of his morning determined the quality of his day. And the quality of his days was determining the direction of his life. Nobody posted about it. But it was quietly building something real.",
        ],
    },

    # ----------------------------------------------------------------
    # CHALLENGE â€” Paid accountability group
    # ----------------------------------------------------------------
    "challenge": {
        "confrontation": {
            "hooks": [
                "You have been trying alone. It is not working.",
                "Willpower runs out. Accountability does not.",
                "You do not need more motivation. You need someone watching.",
                "You keep starting over because there is nobody to answer to.",
                "30 days with the right people changes more than 3 years alone.",
                "Stop making private promises you have no reason to keep.",
                "The reason you quit is always the same. No consequence.",
                "Isolation is not strength. It is the reason most men fail.",
            ],
            "truths": [
                "The environment you are in determines the standard you hold.",
                "When people are watching you show up differently. Every time.",
                "You do not have a discipline problem. You have an accountability gap.",
                "A room full of people who will not accept your excuses is priceless.",
                "The men who changed their lives did not do it alone. Nobody does.",
            ],
            "questions": [
                "How many more times are you going to restart alone?",
                "What would change if someone was watching every single day?",
                "If not this what exactly is the plan?",
                "At what point does doing it alone become the problem and not the solution?",
                "What is twenty dollars a month if it is the thing that finally makes the difference?",
            ],
        },
        "build": {
            "hooks": [
                "There is a reason the best athletes in the world have coaches.",
                "Discipline is easier when the environment demands it.",
                "The 30 day challenge exists because accountability rewires the brain.",
                "You rise to the standard of the people you surround yourself with. Always.",
            ],
            "truths": [
                "Community is not weakness. It is the structure that lets you go further.",
                "Under twenty dollars a month. Daily check-ins. Real accountability. No excuses.",
                "Daily check-ins make the invisible visible. That is where real change begins.",
                "Thirty days of consistent accountability creates the foundation of a new standard.",
            ],
            "questions": [
                "What would thirty days of real accountability produce in your life?",
                "When was the last time you invested in yourself the way you invest in everything else?",
                "What is stopping you from joining the men who are already building?",
            ],
        },
        "story": [
            "He had tried alone seventeen times. He counted once. Seventeen fresh starts seventeen slow stops. Each one began with certainty and ended with the same familiar drift. Then someone put him in a room with people who checked in every morning. People who did not accept the usual excuses. The eighteenth time was different. Not because he was different. Because the environment was.",
            "He thought accountability was for people who lacked self-discipline. Then he realised that self-discipline without structure is just willpower. And willpower always runs out. Accountability is the structure that makes discipline sustainable. He joined a group. He showed up every day because people were watching. Then he kept showing up after they stopped watching. That is when it became identity.",
        ],
    },

    # ----------------------------------------------------------------
    # PURPOSE â€” Legacy. The long game.
    # ----------------------------------------------------------------
    "purpose": {
        "confrontation": {
            "hooks": [
                "You were built for more than this comfortable nothing.",
                "Legacy does not build itself while you wait.",
                "You have one life. This is it. Not the practice run.",
                "Stop treating your potential like a backup plan.",
                "Every day you coast is a day the better version of you does not exist.",
                "The world does not need your intentions. It needs your output.",
                "Greatness belongs to the consistent not the talented.",
                "You are running out of time to become who you were supposed to be.",
            ],
            "truths": [
                "Purpose is not found. It is built. One decision at a time.",
                "The man you want to become is made in the moments nobody watches.",
                "You do not become great by accident. You become great by daily decision.",
                "The mark you leave on the world starts with the mark you make on yourself.",
                "Legacy is the sum of ordinary days lived with extraordinary intention.",
            ],
            "questions": [
                "What do you want people to say about you when it is over?",
                "Are you building something that will outlast you?",
                "Who would you become if you stopped playing small?",
                "Is the life you are living the one you were built for?",
                "What would your life look like if you lived it at full capacity every day?",
            ],
        },
        "build": {
            "hooks": [
                "Legacy is a quiet thing. It builds in the years nobody celebrates.",
                "The men who are remembered were not the loudest. They were the most consistent.",
                "The work you are doing in silence right now is the foundation of everything.",
                "Not every chapter looks like progress. Some look like patience. Both build the same thing.",
            ],
            "truths": [
                "Legacy is not a destination. It is the sum of daily decisions made over years.",
                "Discipline practiced in private becomes character displayed in public.",
                "You do not have to be extraordinary every day. You have to be consistent.",
                "The best version of you is not waiting for perfect conditions. It is built through imperfect ones.",
                "A life of purpose is built in ten thousand small acts that nobody sees.",
            ],
            "questions": [
                "What are you building that will still matter in ten years?",
                "Who is the man you are becoming and are you proud of him?",
                "If today was a brick in the foundation of your legacy what kind of brick was it?",
            ],
        },
        "story": [
            "He was not famous. Nobody interviewed him. Nobody watched him train at five in the morning. But he showed up. Every day for years he showed up. And slowly quietly the life he built became the kind of life other people pointed at and said. That is what is possible. He never set out to inspire anyone. He just refused to disappear.",
            "The young man asked the old man how he had built something that lasted. The old man thought for a long time. Then he said. I just refused to stop on the days I wanted to quit. Every other day was easy. It was the days I wanted to stop that mattered. And I just did not. That is all it was. Decades of not stopping on the days I wanted to.",
            "She decided she was going to become someone her children would be proud of. Not rich. Not famous. Just honest. Disciplined. Present. She started small. Too small to matter she thought. But small things done every day do not stay small. Five years later her children did not know exactly when she changed. They just knew she was different. Solid. The kind of person you lean on without thinking about it.",
        ],
    },
}

# ================================================================
# LONG VIDEO ARC â€” 7 acts, one continuous monologue
# ================================================================

LONG_VIDEO_ARC = [
    {"name": "HOOK",      "pacing": "confrontation", "categories": ["identity", "mental", "habits"],       "section": "hooks",     "count": 1},
    {"name": "HOOK2",     "pacing": "confrontation", "categories": ["masculinity", "mental"],              "section": "hooks",     "count": 1},
    {"name": "DEEPEN",    "pacing": "build",         "categories": ["identity", "habits"],                 "section": "hooks",     "count": 2},
    {"name": "STORY1",    "pacing": "story",         "categories": ["identity", "mental", "habits"],       "section": "story",     "count": 1},
    {"name": "TRUTH",     "pacing": "confrontation", "categories": ["identity", "mental", "masculinity"],  "section": "truths",    "count": 3},
    {"name": "QUESTIONS", "pacing": "build",         "categories": ["habits", "identity", "mental"],       "section": "questions", "count": 3},
    {"name": "DEEPEN2",   "pacing": "build",         "categories": ["masculinity", "purpose"],             "section": "truths",    "count": 2},
    {"name": "TURN",      "pacing": "story",         "categories": ["purpose", "masculinity"],             "section": "story",     "count": 1},
    {"name": "PURPOSE",   "pacing": "confrontation", "categories": ["purpose"],                            "section": "hooks",     "count": 2},
    {"name": "FINAL_Q",   "pacing": "build",         "categories": ["purpose", "identity"],                "section": "questions", "count": 2},
    {"name": "CLOSE",     "pacing": "confrontation", "categories": ["challenge"],                          "section": "hooks",     "count": 1},
    {"name": "CTA",       "pacing": "confrontation", "categories": ["challenge"],                          "section": "truths",    "count": 1},
]

SET_ORDER = ["identity", "mental", "masculinity", "habits", "challenge", "purpose"]

# ================================================================
# CONTENT SELECTION
# ================================================================

used_lines = json.load(open(USED_LINES_FILE)) if os.path.exists(USED_LINES_FILE) else []

def pick_line(category, section, pacing=None):
    cat_data = CONTENT.get(category, {})
    if section == "story":
        pool = cat_data.get("story", [])
    elif pacing and pacing in cat_data:
        pool = cat_data[pacing].get(section, [])
    else:
        pool = []
        for mode_data in cat_data.values():
            if isinstance(mode_data, dict):
                pool += mode_data.get(section, [])

    available = [l for l in pool if l not in used_lines]
    if not available:
        available = pool.copy()
    if not available:
        return "You know what you need to do."

    chosen = random.choice(available)
    used_lines.append(chosen)
    return chosen

def get_next_category():
    global set_step, last_category
    cat           = SET_ORDER[set_step % len(SET_ORDER)]
    set_step     += 1
    last_category = cat
    return cat

def build_reel_script(category):
    pacing   = random.choice(["confrontation", "build"])
    hook     = pick_line(category, "hooks",     pacing)
    truth    = pick_line(category, "truths",    pacing)
    question = pick_line(category, "questions", pacing)

    if category == "challenge":
        cta = random.choice([
            "Join the Inner Discipline Challenge. DM DISCIPLINE.",
            "30 days. Facebook group. Under 20$. DM DISCIPLINE.",
            "The group is open. DM DISCIPLINE.",
            "Stop doing it alone. DM DISCIPLINE.",
        ])
    elif category == "purpose":
        cta = random.choice([
            "Comment LEGEND if you are building.",
            "Type LEGACY if this hit.",
            "This is your sign. Comment LEGEND.",
        ])
    else:
        cta = random.choice([
            "Prove it. Comment DISCIPLINE.",
            "Type DISCIPLINE if you are done.",
            "Lock in or leave.",
            "No excuses. Type DISCIPLINE.",
            "This is your moment.",
        ])
    return [hook, truth, question, cta], pacing

def build_long_video_script():
    lines = []
    for act in LONG_VIDEO_ARC:
        for _ in range(act["count"]):
            cat  = random.choice(act["categories"])
            line = pick_line(cat, act["section"], act["pacing"] if act["section"] != "story" else None)
            if line:
                lines.append((line, act["pacing"]))
    return lines

# ================================================================
# TTS
# ================================================================

async def tts_async(text, filename, rate, pitch):
    communicate = edge_tts.Communicate(text, VOICE, rate=rate, pitch=pitch, volume=VOLUME)
    await communicate.save(filename)

def generate_voice(text, filename, pacing="confrontation"):
    mode = PACING_MODES.get(pacing, PACING_MODES["confrontation"])
    asyncio.run(tts_async(text, filename, mode["rate"], mode["pitch"]))

# ================================================================
# TEXT RENDERER
# Returns RGB numpy array (H, W, 3) with text composited on
# transparent black. Text pixels are white/orange, rest is black.
# We return RGB so MoviePy ImageClip works without mask issues.
# ================================================================

def make_text_frame(text):
    """Render text onto black RGB frame. Orange first word, white rest."""
    text = text.replace("\u2014", "-").replace("\u2013", "-")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2026", "...")
    text = text.upper()

    # Render on black background â€” we'll blend it in using numpy
    img  = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(img)

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
    if current:
        lines.append(current)

    total_height     = len(lines) * (font_size + 22)
    y                = int(H * 0.62) - total_height // 2
    first_word_drawn = False
    ORANGE           = (255, 140, 0)
    WHITE            = (255, 255, 255)

    for line in lines:
        line_words = line.split()
        if not line_words:
            y += font_size + 22
            continue
        line_width = draw.textlength(line, font=font)
        x          = (W - line_width) // 2
        for idx, word in enumerate(line_words):
            word_width  = draw.textlength(word, font=font)
            space_width = draw.textlength(" ", font=font) if idx < len(line_words) - 1 else 0
            color = ORANGE if not first_word_drawn else WHITE
            first_word_drawn = True
            draw.text((x, y), word, font=font, fill=color, stroke_width=5, stroke_fill=(0, 0, 0))
            x += word_width + space_width
        y += font_size + 22

    return np.array(img)   # shape (H, W, 3)

# ================================================================
# LOGO RENDERER
# Returns RGB numpy array (H, W, 3)
# ================================================================

def make_logo_frame():
    if not os.path.exists(LOGO_PATH):
        return None
    logo   = Image.open(LOGO_PATH).convert("RGBA")
    aspect = logo.height / logo.width
    new_w  = LOGO_SIZE
    new_h  = int(LOGO_SIZE * aspect)
    logo   = logo.resize((new_w, new_h), Image.LANCZOS)

    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x      = (W - new_w) // 2
    y      = H - new_h - LOGO_BOTTOM_MARGIN
    canvas.paste(logo, (x, y), logo)

    # Flatten to RGB with black background
    bg  = Image.new("RGB", (W, H), (0, 0, 0))
    bg.paste(canvas.convert("RGB"), (0, 0), canvas.split()[3])
    return np.array(bg)

# ================================================================
# VIGNETTE â€” precomputed numpy mask
# ================================================================

def make_vignette_mask():
    mask            = np.ones((H, W), dtype=np.float32)
    vignette_height = int(H * 0.55)
    for row in range(vignette_height):
        mask[row, :] = (row / vignette_height) ** 1.6
    return mask   # values 0.0 (black at top) to 1.0

# ================================================================
# CHUNK SPLITTER â€” always word count, never punctuation
# ================================================================

def split_into_chunks(text, chunk_size):
    words  = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks if chunks else [text]

# ================================================================
# CORE VIDEO BUILDER
# Uses VideoClip(make_frame) for bg â€” proven MoviePy pattern.
# Text composited via numpy inside make_frame â€” no RGBA clip issues.
# ================================================================

def build_video(lines_with_pacing, video_path, output_path, max_duration=None, seg_index=0):
    voice_files = []

    try:
        # ---- Step 1: Generate all voice files and measure durations ----
        print(f"  ðŸŽ™ï¸  Generating {len(lines_with_pacing)} voice lines...")
        voice_data = []   # (file, duration, pacing, chunk_size, line_text)

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

        # ---- Step 2: If reel, trim lines until total fits under max_duration ----
        if max_duration:
            gap   = 0.12
            lead  = 0.5
            total = lead + sum(d + gap for _, d, _, _, _ in voice_data)
            while total > max_duration and len(voice_data) > 1:
                removed = voice_data.pop()
                if os.path.exists(removed[0]):
                    os.remove(removed[0])
                    voice_files.remove(removed[0])
                total = lead + sum(d + gap for _, d, _, _, _ in voice_data)

        # ---- Step 3: Build timeline from EXACT audio durations ----
        # âœ… All timestamps calculated upfront from measured durations.
        # No floating point accumulation â€” last line stays in sync.
        FADE_DUR    = 0.15   # fade in / fade out duration seconds
        LINE_GAP    = 0.25   # silence between lines â€” breathing room
        lead        = 0.5    # lead-in before first word

        # First pass â€” calculate exact start time of every line
        line_starts = []
        cursor      = lead
        for i, (vf, voice_duration, pacing, chunk_size, line) in enumerate(voice_data):
            line_starts.append(cursor)
            cursor += voice_duration + (LINE_GAP if i < len(voice_data) - 1 else FADE_DUR)

        reel_duration = float(cursor)
        if max_duration:
            reel_duration = min(reel_duration, float(max_duration))

        # Second pass â€” build text_events and audio_clips from exact starts
        text_events = []   # (chunk_text, t_start, t_end)
        audio_clips = []

        for i, (vf, voice_duration, pacing, chunk_size, line) in enumerate(voice_data):
            line_t = line_starts[i]
            audio  = AudioFileClip(vf)
            audio_clips.append(audio.set_start(line_t))

            chunks         = split_into_chunks(line, chunk_size)
            num_chunks     = len(chunks)
            chunk_duration = voice_duration / num_chunks   # exact equal slice

            for j, chunk in enumerate(chunks):
                t_start = line_t + j * chunk_duration
                # Last chunk ends exactly when voice ends + small fade tail
                if j == num_chunks - 1:
                    t_end = line_t + voice_duration + FADE_DUR
                else:
                    t_end = t_start + chunk_duration + FADE_DUR * 0.5
                text_events.append((chunk, t_start, min(t_end, reel_duration)))

        print(f"  â±ï¸  Duration: {reel_duration:.2f}s | Lines: {len(voice_data)} | Chunks: {len(text_events)}")

        # ---- Step 4: Pre-render all text frames ----
        print(f"  ðŸ–¼ï¸  Pre-rendering {len(text_events)} text frames...")
        rendered_texts = []
        for chunk, t_start, t_end in text_events:
            frame = make_text_frame(chunk)
            rendered_texts.append((frame, t_start, t_end))

        # ---- Step 5: Pre-render logo ----
        logo_frame = make_logo_frame()

        # ---- Step 6: Load and prep background video ----
        print(f"  ðŸŽ¬  Loading background: {video_path}")
        bg_clip      = VideoFileClip(video_path)
        clip_ratio   = bg_clip.w / bg_clip.h
        target_ratio = W / H
        if clip_ratio > target_ratio:
            bg_clip = bg_clip.resize(height=H)
        else:
            bg_clip = bg_clip.resize(width=W)
        bg_clip = bg_clip.crop(
            x_center=bg_clip.w / 2,
            y_center=bg_clip.h / 2,
            width=W, height=H
        )
        if bg_clip.duration < reel_duration:
            bg_clip = vfx.loop(bg_clip, duration=reel_duration)
        bg_clip = bg_clip.subclip(0, reel_duration)

        # ---- Step 7: Precompute vignette ----
        vignette_mask = make_vignette_mask()   # (H, W) float32 0-1

        # ================================================================
        # ---- Step 8: make_frame â€” composites everything via numpy ----
        # This is the proven pattern. No fl(), no RGBA ImageClip issues.
        # ================================================================

        def make_frame(t):
            # Get background frame
            bg = bg_clip.get_frame(t).astype(np.float32)

            # Apply vignette (darken top)
            bg[:, :, 0] *= vignette_mask
            bg[:, :, 1] *= vignette_mask
            bg[:, :, 2] *= vignette_mask
            bg = np.clip(bg, 0, 255).astype(np.uint8)

            # âœ… Composite text with fade in / fade out
            for text_frame, t_start, t_end in rendered_texts:
                if t_start <= t < t_end:
                    duration = t_end - t_start

                    # Fade in over FADE_DUR seconds
                    if t - t_start < FADE_DUR:
                        alpha = (t - t_start) / FADE_DUR
                    # Fade out over FADE_DUR seconds
                    elif t_end - t < FADE_DUR:
                        alpha = (t_end - t) / FADE_DUR
                    else:
                        alpha = 1.0

                    alpha = float(np.clip(alpha, 0.0, 1.0))

                    # Blend text pixels only (not black background)
                    mask   = np.any(text_frame > 20, axis=2)
                    bg_f   = bg.astype(np.float32)
                    txt_f  = text_frame.astype(np.float32)
                    bg_f[mask] = bg_f[mask] * (1.0 - alpha) + txt_f[mask] * alpha
                    bg     = np.clip(bg_f, 0, 255).astype(np.uint8)

            # Composite logo (always visible)
            if logo_frame is not None:
                logo_mask = np.any(logo_frame > 10, axis=2)
                bg_f      = bg.astype(np.float32)
                logo_f    = logo_frame.astype(np.float32)
                blended   = bg_f.copy()
                blended[logo_mask] = (
                    bg_f[logo_mask] * (1.0 - LOGO_OPACITY) +
                    logo_f[logo_mask] * LOGO_OPACITY
                )
                bg = np.clip(blended, 0, 255).astype(np.uint8)

            return bg

        # ---- Step 9: Build final video ----
        final_video = VideoClip(make_frame, duration=reel_duration).set_fps(FPS)
        final_video = final_video.fadeout(0.3)

        # ---- Step 10: Audio ----
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

        # ---- Step 11: Render ----
        print(f"  ðŸ“¼  Rendering â†’ {output_path}")
        final.write_videofile(
            output_path, fps=FPS,
            codec="libx264", audio_codec="aac",
            threads=4, preset="fast",
            logger=None
        )

        # ---- Step 12: Hard trim reel to exactly 15s (reel only) ----
        if max_duration and max_duration <= MAX_REEL_LENGTH:
            trimmed = output_path.replace(".mp4", "_t.mp4")
            subprocess.run([
                "ffmpeg", "-y", "-i", output_path,
                "-t", str(MAX_REEL_LENGTH),
                "-c", "copy", trimmed
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(trimmed):
                os.replace(trimmed, output_path)

        print(f"  âœ… Done â†’ {output_path}")
        bg_clip.close()
        return output_path

    except Exception as e:
        import traceback
        print(f"  âŒ Failed: {e}")
        traceback.print_exc()
        return None

    finally:
        for vf in voice_files:
            if os.path.exists(vf):
                os.remove(vf)

# ================================================================
# CAPTION BUILDER
# ================================================================

CAPTION_OPENERS = {
    "identity": ["Most people won't admit this.", "Read this slowly.", "The truth nobody says."],
    "comfort":  ["Comfort is the most dangerous place.", "This is what playing safe costs you."],
    "time":     ["You needed to hear this today.", "The most expensive thing you keep wasting."],
    "challenge":["You have been trying alone. There is a better way.", "The group is open. This is your sign."],
    "purpose":  ["This is for the men building in silence.", "Legacy is built in the years nobody celebrates."],
}
CAPTION_CLOSERS = {
    "identity":  ["Comment DISCIPLINE if you are locking in.", "Follow @innerdiscipline."],
    "comfort":   ["Comment DISCIPLINE if you are done settling.", "Follow @innerdiscipline."],
    "time":      ["Comment DISCIPLINE if today is the day.", "Follow @innerdiscipline."],
    "challenge": ["Link in bio. Join the Inner Discipline Challenge.", "Under $20 per month. DM DISCIPLINE."],
    "purpose":   ["Comment LEGEND if you are building.", "Type LEGACY if this hit."],
}
HASHTAGS = {
    "identity":  "#discipline #mindset #selfimprovement #innerdiscipline #accountability #noexcuses #selfmastery #growthmindset #hardwork #mentalstrength",
    "comfort":   "#discipline #motivation #selfimprovement #innerdiscipline #growthmindset #noexcuses #selfmastery #hardwork #mindset #consistency",
    "time":      "#discipline #motivation #mindset #innerdiscipline #selfimprovement #consistency #focus #hardwork #growthmindset #dailymotivation",
    "challenge": "#30daychallenge #accountability #innerdisciplinechallenge #disciplinegroup #30days #facebookgroup #selfimprovement #discipline #mindset #hardwork",
    "purpose":   "#legacy #purpose #innerdiscipline #becomelegend #growthmindset #selfmastery #discipline #mentalstrength #levelup #hardwork",
}

def build_caption(lines, category):
    opener   = random.choice(CAPTION_OPENERS.get(category, CAPTION_OPENERS["identity"]))
    closer   = random.choice(CAPTION_CLOSERS.get(category, CAPTION_CLOSERS["identity"]))
    hashtags = HASHTAGS.get(category, HASHTAGS["identity"])
    hook     = lines[0] if lines else ""
    body     = lines[1] if len(lines) > 1 else ""
    return "\n".join([opener, "", f'"{hook}"', "", body, "", "-", closer, "", hashtags])

# ================================================================
# RUN
# ================================================================

print("\nðŸŽ¬ INNER DISCIPLINE â€” DAILY ENGINE")
print("=" * 52)

all_videos = get_all_videos()
if not all_videos:
    raise Exception("No background videos found. Add bg1.mp4 to this folder.")

date_str = datetime.now().strftime("%Y%m%d_%H%M")

# âœ… Random video per output â€” reel and long video each pick independently
reel_video = random.choice(all_videos)
long_video = random.choice(all_videos)
print(f"   ðŸ“¹ Reel video  â†’ {reel_video}")
print(f"   ðŸ“¹ Long video  â†’ {long_video}")

# ================================================================
# PHASE 1 â€” REEL (exactly 15s)
# ================================================================

print("\nðŸ“± Phase 1 â€” Daily Reel (15s)...")

reel_category            = get_next_category()
reel_script, reel_pacing = build_reel_script(reel_category)
reel_lines               = [(line, reel_pacing) for line in reel_script]
reel_path                = f"outputs/reel_{date_str}.mp4"

print(f"   Category: {reel_category.upper()} | Pacing: {reel_pacing}")

reel_result = build_video(
    lines_with_pacing=reel_lines,
    video_path=reel_video,
    output_path=reel_path,
    max_duration=MAX_REEL_LENGTH,
    seg_index=0,
)

if reel_result:
    base    = os.path.splitext(reel_path)[0]
    caption = build_caption(reel_script, reel_category)
    open(f"{base}_title.txt",   "w").write(f"{reel_script[0]} | INNER DISCIPLINE")
    open(f"{base}_caption.txt", "w").write(caption)
    print(f"   ðŸ“„ Caption â†’ {base}_caption.txt")

# ================================================================
# PHASE 2 â€” LONG VIDEO (~5 min continuous monologue)
# ================================================================

print("\nðŸŽ¥ Phase 2 â€” Long Video (~5 min)...")

long_script = build_long_video_script()
long_path   = f"outputs/longvideo_{date_str}.mp4"

print(f"   Arc: {len(long_script)} lines | {len(LONG_VIDEO_ARC)} acts")

long_result = build_video(
    lines_with_pacing=long_script,
    video_path=long_video,
    output_path=long_path,
    max_duration=LONG_VIDEO_SECS,
    seg_index=99,
)

if long_result:
    long_lines = [line for line, _ in long_script]
    base       = os.path.splitext(long_path)[0]
    caption    = build_caption(long_lines, "purpose")
    open(f"{base}_title.txt",   "w").write("Inner Discipline | Full Motivation | INNER DISCIPLINE")
    open(f"{base}_caption.txt", "w").write(caption)
    print(f"   ðŸ“„ Caption â†’ {base}_caption.txt")

# ================================================================
# CLEANUP + MEMORY
# ================================================================

if os.path.exists("temp_segments"):
    shutil.rmtree("temp_segments")

json.dump(used_hooks,    open(HOOK_MEMORY_FILE,     "w"))
json.dump(last_category, open(CATEGORY_MEMORY_FILE, "w"))
json.dump(set_step,      open(SET_STEP_FILE,         "w"))
json.dump(used_lines,    open(USED_LINES_FILE,       "w"))  # âœ… saves all used lines

print("\n" + "=" * 52)
print(f"âœ… COMPLETE")
print(f"   ðŸ“± Reel      â†’ {reel_path}")
print(f"   ðŸŽ¥ Long video â†’ {long_path}")
print("=" * 52)
