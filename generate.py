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
LOGO_OPACITY       = 0.85
LOGO_SIZE          = 180
LOGO_BOTTOM_MARGIN = 80
MUSIC_DELAY        = 1.5
VOICE              = "en-US-GuyNeural"
VOLUME             = "+0%"

os.makedirs("outputs",       exist_ok=True)
os.makedirs("temp_segments", exist_ok=True)

# ================================================================
# PACING MODES
# ================================================================

PACING_MODES = {
    "confrontation": {"rate": "-5%",  "pitch": "-40Hz", "chunk_size": 2},
    "build":         {"rate": "-25%", "pitch": "-55Hz", "chunk_size": 3},
    "story":         {"rate": "-15%", "pitch": "-45Hz", "chunk_size": 3},
}

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
    return glob.glob("bg*.mp4") + glob.glob("bg*.mov") + glob.glob("bg*.MP4")

# ================================================================
# CONTENT BANK
# ================================================================

CONTENT = {
    "identity": {
        "confrontation": {
            "hooks": [
                "You became someone you don't recognise.",
                "You broke the promise you made to yourself.",
                "You stopped fighting. Nobody even had to beat you.",
                "You made peace with failing. That's the worst part.",
                "You lowered the bar so many times you forgot where it was.",
                "You told yourself you'd change. You didn't.",
                "You sold yourself out. For nothing.",
                "You don't even flinch anymore. That's how deep it goes.",
            ],
            "truths": [
                "That's not a bad day. That's a pattern.",
                "That's not a mistake. That's who you're choosing to be.",
                "You did this. Every single day, you chose this.",
                "The man you used to respect wouldn't recognise you.",
                "This is what giving up slowly looks like.",
                "Every compromise you made added up to this moment.",
            ],
            "questions": [
                "Is this the man you're going to stay as?",
                "How much longer are you going to watch yourself fall?",
                "At what point did you decide this was acceptable?",
                "Can you even look at yourself honestly anymore?",
            ],
        },
        "build": {
            "hooks": [
                "Somewhere along the way you stopped showing up for yourself.",
                "There was a version of you that used to fight back.",
                "You remember the last time you were proud of yourself.",
                "The man you planned to be is still waiting.",
                "Every morning you wake up and feel the gap.",
                "You carry this quietly. The weight of knowing you're capable of more.",
            ],
            "truths": [
                "The silence between who you are and who you could be is deafening.",
                "You haven't lost the ability. You've lost the decision.",
                "Nobody is coming to pull you back. This is yours to fix.",
                "The version of you that didn't quit is still in there.",
            ],
            "questions": [
                "How much more time are you willing to give this version of yourself?",
                "What are you waiting for before you take yourself seriously?",
                "If not now, when. And if not you, who.",
            ],
        },
        "story": [
            "He had a plan. A real one. He wrote it down and believed every word. Then life got heavy. And instead of pushing through, he adjusted. Just this once. Then again. Then it wasn't adjusting anymore. It was retreating. Nobody saw it happen. Not even him. Until one day he looked up and the man in the mirror was a stranger.",
            "There is a man who checks his phone first thing every morning. Not for opportunity. For escape. He used to have a standard. He is not sure exactly when he let go. But he can feel the distance between then and now every single day.",
            "He made a promise to himself at twenty. A real one. By thirty he could not remember the last time he kept it. He did not fail dramatically. He failed quietly. One small compromise after another. Together they built the life he never wanted.",
        ],
    },
    "comfort": {
        "confrontation": {
            "hooks": [
                "You chose easy. Again.",
                "Comfort is the cage you built yourself.",
                "You stopped before it got hard. Like always.",
                "You folded the moment it cost you something real.",
                "Soft choices make a soft life. This is the proof.",
                "You avoided the hard thing and called it self-care.",
                "The version of you that was hungry is gone. Comfort killed it.",
            ],
            "truths": [
                "Everything you want is on the other side of what you keep avoiding.",
                "Every time you chose easy, you made hard things harder.",
                "The cage has no lock. You just stopped trying the door.",
                "You will never accidentally become great. You have to fight for it.",
            ],
            "questions": [
                "How comfortable are you willing to let yourself become?",
                "What has choosing easy actually given you?",
                "Is the short-term relief worth the long-term cost?",
                "What are you protecting yourself from by staying safe?",
            ],
        },
        "build": {
            "hooks": [
                "Comfort does not feel like the enemy. That is why it wins.",
                "You have been resting so long that rest feels normal.",
                "The soft life crept up on you. You did not choose it all at once.",
                "It was supposed to be temporary. The break. The pause. The wait.",
                "Nobody told you that comfort was the most dangerous place to stay.",
            ],
            "truths": [
                "Comfort is a slow thief. It takes your edge first. Then your hunger. Then your identity.",
                "You do not notice you have stopped growing until you try to move and cannot.",
                "Ease is the environment where potential dies quietly.",
                "You were made for resistance. Without it you soften in ways you do not see coming.",
            ],
            "questions": [
                "When did you last do something that genuinely challenged you?",
                "What are you capable of that comfort has been keeping hidden?",
                "If ease is the strategy, what is the destination?",
            ],
        },
        "story": [
            "He told himself he had earned the rest. So he rested. And resting felt so good he did it a little longer. Months passed. He was comfortable. Then he looked at his life and realised that comfortable and happy are not the same thing. And one of them had been slowly replacing the other without asking permission.",
            "She used to push hard. The kind of push that leaves fire in your chest. Then she found a rhythm. Safe. Good enough. And good enough became the new ceiling. And the ceiling got lower every year. Not dramatically. Just quietly. The way all important things are lost.",
        ],
    },
    "time": {
        "confrontation": {
            "hooks": [
                "That day is gone. You are not getting it back.",
                "You wasted another one. That is the truth of it.",
                "Time does not pause while you figure it out.",
                "The clock moved. You did not.",
                "You keep saying tomorrow like it is guaranteed.",
                "Every hour you delay is an hour you will never spend building.",
                "Time is the only thing you spend that you cannot replace.",
            ],
            "truths": [
                "The right moment you are waiting for does not exist. It never did.",
                "Delay is a decision. You just do not frame it that way.",
                "The years are going whether you use them or not.",
                "While you wait, someone else is building.",
            ],
            "questions": [
                "What exactly are you waiting for?",
                "How many more days are you willing to lose?",
                "Five years from now, what will you wish you had started today?",
                "At what point does delay become a permanent choice?",
            ],
        },
        "build": {
            "hooks": [
                "You feel it sometimes. The quiet weight of time passing.",
                "Another year. And the thing you planned to do is still just a plan.",
                "You are not running out of time dramatically. You are losing it quietly.",
                "The things you keep meaning to start are still exactly where you left them.",
            ],
            "truths": [
                "Time does not end suddenly. It erodes. Day by day until there is less than you thought.",
                "The future you plan for is built from the days you are spending right now.",
                "Every day you do not start is a day you will have to make up later.",
            ],
            "questions": [
                "What would you do differently if you truly felt how limited your time was?",
                "Which regret are you building toward. Trying or not trying.",
                "What would it mean if you started today. Not tomorrow. Today.",
            ],
        },
        "story": [
            "He had five years left on the plan. Then four. Then three. He kept adjusting the timeline but not the effort. The deadline moved. The dream did not. Eventually the deadline passed. And the dream just sat there unchased quietly becoming the thing he used to want.",
            "At forty she looked back at thirty and thought about everything she had said she would do. At thirty she had looked back at twenty and thought the same thing. The pattern scared her more than the lost time.",
        ],
    },
    "challenge": {
        "confrontation": {
            "hooks": [
                "You have been trying alone. It is not working.",
                "Willpower runs out. Accountability does not.",
                "You do not need more motivation. You need someone watching.",
                "You keep starting over because there is nobody to answer to.",
                "30 days with the right people changes more than 3 years alone.",
                "Stop making private promises you have no reason to keep.",
            ],
            "truths": [
                "The environment you are in determines the standard you hold.",
                "When people are watching, you show up differently. Every time.",
                "You do not have a discipline problem. You have an accountability gap.",
                "A room full of people who will not accept your excuses is priceless.",
            ],
            "questions": [
                "How many more times are you going to restart alone?",
                "What would change if someone was watching every day?",
                "If not this, then what is the plan?",
                "At what point does doing it alone become the problem?",
            ],
        },
        "build": {
            "hooks": [
                "There is a reason the best athletes have coaches. Even when they are already great.",
                "Discipline is easier when the environment demands it.",
                "The men who changed their lives did not do it in isolation.",
                "The 30 day challenge exists because accountability changes the brain.",
            ],
            "truths": [
                "Community is not a crutch. It is the structure that lets you go further.",
                "You rise to the standard of the people around you. Always.",
                "Under twenty dollars a month. No excuses. Just accountability.",
                "Daily check-ins make the invisible visible. That is where change happens.",
            ],
            "questions": [
                "What would thirty days of real accountability produce in your life?",
                "What is twenty dollars if it is the thing that finally makes the difference?",
                "When was the last time you invested in yourself the way you invest in everything else?",
            ],
        },
        "story": [
            "He had tried alone seventeen times. He counted once. Seventeen fresh starts, seventeen slow stops. Each one began with certainty and ended with the same familiar drift. Then someone put him in a room with people who checked in every morning. People who did not accept excuses. The eighteenth time was different. Not because he was different. Because the environment was.",
        ],
    },
    "purpose": {
        "confrontation": {
            "hooks": [
                "You were built for more than this comfortable nothing.",
                "Legacy does not build itself while you wait.",
                "Greatness does not wait. And it does not forgive wasted years.",
                "You have one life. This is it. Not the practice run.",
                "Stop treating your potential like a backup plan.",
                "Every day you coast is a day the better version of you does not exist.",
            ],
            "truths": [
                "Purpose is not found. It is built. One decision at a time.",
                "The man you want to become is made in the moments nobody watches.",
                "You do not become great by accident. You become great by decision.",
                "The mark you leave on the world starts with the mark you make on yourself.",
            ],
            "questions": [
                "What do you want people to say about you when it is over?",
                "Are you building something that will outlast you?",
                "Who would you become if you stopped playing small?",
                "Is the life you are living the one you were built for?",
            ],
        },
        "build": {
            "hooks": [
                "Legacy is a quiet thing. It builds in the years nobody celebrates.",
                "The men who are remembered were not always the loudest. They were the most consistent.",
                "The work you are doing in silence right now is the foundation of everything.",
                "Becoming who you are meant to be is slower than you want and more real than you expect.",
            ],
            "truths": [
                "Legacy is not a destination. It is the sum of daily decisions made over years.",
                "Discipline practiced in private becomes character displayed in public.",
                "You do not have to be extraordinary every day. You have to be consistent.",
                "The best version of you is not waiting for perfect conditions. It is built through imperfect ones.",
            ],
            "questions": [
                "What are you building that will still matter in ten years?",
                "Who is the man you are becoming, and are you proud of him?",
                "If today was a brick in the foundation of your legacy, what kind of brick was it?",
            ],
        },
        "story": [
            "He was not famous. Nobody interviewed him. Nobody watched him train at five in the morning. But he showed up. Every day for years he showed up. And slowly quietly the life he built became the kind of life other people pointed at and said. That is what is possible. He never set out to inspire anyone. He just refused to disappear.",
            "She decided at thirty two that she was going to become someone her children would be proud of. Not rich. Not famous. Just honest. Disciplined. Consistent. She started small. Too small to matter she thought. But small things done every day do not stay small.",
            "The young man asked the old man how he had built something that lasted. The old man thought for a long time. Then he said. I just refused to stop on the days I wanted to quit. Every other day was easy. It was the days I wanted to stop that mattered. And I just did not.",
        ],
    },
}

# ================================================================
# LONG VIDEO ARC â€” 7 acts, one continuous monologue
# ================================================================

LONG_VIDEO_ARC = [
    {"name": "HOOK",    "pacing": "confrontation", "categories": ["identity", "comfort", "time"],    "section": "hooks",     "count": 1},
    {"name": "DEEPEN",  "pacing": "build",         "categories": ["identity", "comfort"],            "section": "hooks",     "count": 1},
    {"name": "STORY",   "pacing": "story",         "categories": ["identity", "comfort", "time"],    "section": "story",     "count": 1},
    {"name": "TRUTH",   "pacing": "confrontation", "categories": ["identity", "time", "comfort"],    "section": "truths",    "count": 2},
    {"name": "TENSION", "pacing": "build",         "categories": ["time", "identity"],               "section": "questions", "count": 2},
    {"name": "TURN",    "pacing": "story",         "categories": ["purpose"],                        "section": "story",     "count": 1},
    {"name": "CLOSE",   "pacing": "confrontation", "categories": ["challenge", "purpose"],           "section": "hooks",     "count": 1},
]

SET_ORDER = ["identity", "comfort", "time", "challenge", "purpose"]

# ================================================================
# CONTENT SELECTION
# ================================================================

used_lines = []

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

        # ---- Step 3: Build timeline â€” (chunk_text, start, end) list ----
        timeline   = 0.5
        gap        = 0.12
        FADE_OUT   = 0.10
        text_events = []   # (chunk_text, t_start, t_end)
        audio_clips = []

        for i, (vf, voice_duration, pacing, chunk_size, line) in enumerate(voice_data):
            audio = AudioFileClip(vf)
            audio_clips.append(audio.set_start(timeline))

            chunks         = split_into_chunks(line, chunk_size)
            num_chunks     = len(chunks)
            chunk_duration = voice_duration / num_chunks

            for j, chunk in enumerate(chunks):
                t_start = timeline + j * chunk_duration
                if j == num_chunks - 1:
                    t_end = timeline + voice_duration + FADE_OUT
                else:
                    t_end = t_start + chunk_duration
                text_events.append((chunk, t_start, t_end))

            timeline += voice_duration + (gap if i < len(voice_data) - 1 else FADE_OUT)

        reel_duration = float(timeline)
        if max_duration:
            reel_duration = min(reel_duration, float(max_duration))

        print(f"  â±ï¸  Duration: {reel_duration:.2f}s | Text events: {len(text_events)}")

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

            # Composite active text chunks
            for text_frame, t_start, t_end in rendered_texts:
                if t_start <= t < t_end:
                    # Blend: anywhere text_frame is not black, overlay it
                    # Mask = any channel > 20 (text pixels)
                    mask = np.any(text_frame > 20, axis=2)   # (H, W) bool
                    bg[mask] = text_frame[mask]

            # Composite logo (always visible)
            if logo_frame is not None:
                logo_mask = np.any(logo_frame > 10, axis=2)
                # Apply logo opacity
                bg_f    = bg.astype(np.float32)
                logo_f  = logo_frame.astype(np.float32)
                blended = bg_f.copy()
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

        # ---- Step 12: Hard trim reel to exactly 15s ----
        if max_duration:
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
    "challenge": ["Link in bio. Join the Inner Discipline Challenge.", "Under $20 per month. Link in bio."],
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
bg_video = all_videos[0]

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
    video_path=bg_video,
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
    video_path=bg_video,
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

print("\n" + "=" * 52)
print(f"âœ… COMPLETE")
print(f"   ðŸ“± Reel      â†’ {reel_path}")
print(f"   ðŸŽ¥ Long video â†’ {long_path}")
print("=" * 52)
