import os, random, glob, asyncio, json
import numpy as np
from moviepy.editor import *
from moviepy.video.fx import all as vfx
from moviepy.audio.fx import all as afx
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ================================================================
# INNER DISCIPLINE â€” VIDEO BACKGROUND ENGINE
# 5-Set System:
#   rain_*.mp4   â†’ Endurance  â†’ identity category
#   fire_*.mp4   â†’ Power      â†’ comfort category
#   smoke_*.mp4  â†’ Mental     â†’ time category
#   dust_*.mp4   â†’ Battle     â†’ challenge category
#   light_*.mp4  â†’ Purpose    â†’ rotates as 5th set
#
# Name your video files:
#   rain_1.mp4, rain_2.mp4 ...
#   fire_1.mp4, fire_2.mp4 ...
#   smoke_1.mp4 ...
#   dust_1.mp4  ...
#   light_1.mp4 ...
# ================================================================

W, H   = 1080, 1920
FPS    = 30
MAX_REEL_LENGTH = 15.0

VOICE  = "en-US-GuyNeural"
RATE   = "-10%"
PITCH  = "-45Hz"
VOLUME = "+0%"

FONT_PATH          = "Anton-Regular.ttf"
LOGO_PATH          = "logo.png"
LOGO_OPACITY       = 0.38
LOGO_SIZE          = 160
LOGO_BOTTOM_MARGIN = 90

REELS_PER_RUN = 5   # one full 5-set rotation per run

MUSIC_DELAY = 1.5

os.makedirs("outputs", exist_ok=True)

# ---------------- MEMORY ----------------

HOOK_MEMORY_FILE     = "hook_memory.json"
CATEGORY_MEMORY_FILE = "category_memory.json"
SET_STEP_FILE        = "set_step.json"

used_hooks    = json.load(open(HOOK_MEMORY_FILE))     if os.path.exists(HOOK_MEMORY_FILE)     else []
last_category = json.load(open(CATEGORY_MEMORY_FILE)) if os.path.exists(CATEGORY_MEMORY_FILE) else None
set_step      = json.load(open(SET_STEP_FILE))         if os.path.exists(SET_STEP_FILE)         else 0
if not isinstance(set_step, int):
    set_step = 0

# ---------------- VIDEO POOL ----------------
# Upload your background videos to GitHub named:
#   bg1.mp4, bg2.mp4, bg3.mp4 ... bgN.mp4
# The engine picks 5 unique videos per run â€” one per category.
# Add more bg videos for more variety. Minimum 5 required.

def get_all_videos():
    return (
        glob.glob("bg*.mp4") +
        glob.glob("bg*.mov") +
        glob.glob("bg*.MP4")
    )

# ---------------- CONTENT ----------------

HOOKS = {
    "identity": [
        "You became someone you don't respect.",
        "You don't trust yourself anymore.",
        "You hear yourself... and ignore it.",
        "You know better. You don't do better.",
        "You lost control of yourself.",
        "You keep proving you're unreliable.",
        "You don't follow your own standards.",
        "You've lowered the bar too many times.",
        "You stopped taking yourself seriously.",
        "You're watching yourself fall off.",
        "You don't even resist anymore.",
        "You gave up quietly.",
        "You broke your own identity.",
        "You're not who you said you'd be.",
        "You've normalized disappointment.",
        "You're okay with less now.",
        "You let yourself slip again.",
        "You don't even fight it anymore.",
        "You're becoming predictable.",
        "You made weakness routine.",
    ],
    "comfort": [
        "You chose easy again.",
        "That felt good... didn't it?",
        "You took the softer option.",
        "You avoided the hard part.",
        "You stopped where it got uncomfortable.",
        "You stayed where it's safe.",
        "You picked relief over growth.",
        "You gave in early.",
        "You protected comfort again.",
        "You escaped right on time.",
        "You didn't push through.",
        "You folded under pressure.",
        "You let comfort decide.",
        "You stayed weak on purpose.",
        "You quit before it counted.",
        "You avoided the real work.",
        "You took the shortcut again.",
        "You chose now over later.",
        "You kept it easy.",
        "You didn't go far enough.",
    ],
    "time": [
        "You lost another day.",
        "That day is gone now.",
        "You'll never get that back.",
        "You wasted it again.",
        "It's happening again.",
        "Same day. Same pattern.",
        "You're running out quietly.",
        "Time moved. You didn't.",
        "Another delay added.",
        "You stayed stuck again.",
        "You let the day slip.",
        "Nothing changed today.",
        "You paused your life again.",
        "That was your chance.",
        "You missed it again.",
        "The gap is growing.",
        "You're falling behind slowly.",
        "You're still where you were.",
        "Time kept going without you.",
        "You did nothing again.",
    ],
    "challenge": [
        "You've been doing this alone.",
        "Discipline is easier with a room full of people doing it too.",
        "You don't need more motivation. You need accountability.",
        "30 days. One decision. Everything changes.",
        "The problem isn't you. It's that you're doing it alone.",
        "You've tried alone. It didn't stick.",
        "What if 30 days actually changed your standard?",
        "You keep starting over because no one is watching.",
        "Accountability isn't weakness. It's what actually works.",
        "Every day you wait is a day someone else locks in.",
        "You know what to do. You just need someone to do it with.",
        "30 days of showing up. That's the whole challenge.",
        "You don't need a perfect plan. You need people who won't let you quit.",
        "The version of you that shows up daily - that's who's inside.",
        "One group. 30 days. No excuses accepted.",
    ],
    "purpose": [
        "You were built for more than this.",
        "There's a version of you that doesn't quit.",
        "Legacy isn't given. It's built in silence.",
        "One day you'll look back. Make sure it was worth it.",
        "The work you do in private shows up in public.",
        "You don't rise to the occasion. You fall to your standard.",
        "The man you're becoming is built today.",
        "Comfort is the enemy of the man you're meant to be.",
        "Every rep. Every decision. Every day. It adds up.",
        "You're not just building a body. You're building a mind.",
        "Greatness doesn't announce itself. It shows up daily.",
        "The best version of you is already inside. Start digging.",
        "Your future self is watching every decision you make now.",
        "Discipline today. Freedom tomorrow.",
        "Become the man you needed when you were younger.",
    ],
}

TRUTHS = [
    "That's who you are right now.",
    "That's your real standard.",
    "That's what you accept.",
    "That's your level.",
    "That's your pattern showing.",
    "That's why you don't move forward.",
    "That's the version you feed.",
    "That's what's holding you down.",
    "That's your daily decision.",
    "That's your comfort zone winning.",
    "That's your real discipline.",
    "That's your limit right now.",
    "That's your truth, not your excuse.",
    "That's what you repeat.",
    "That's your default setting.",
]

CHALLENGE_TRUTHS = [
    "That's why the group exists.",
    "That's what 30 days of accountability builds.",
    "That's the difference between alone and locked in.",
    "That's what changes when people are watching.",
    "Inside the group - that version of you shows up.",
    "30 days fixes that.",
    "That's what the challenge is designed to break.",
    "The group holds you to a standard you can't hold alone.",
    "That's exactly who joins the Inner Discipline Challenge.",
    "Daily check-ins make that impossible to ignore.",
]

PURPOSE_TRUTHS = [
    "That's the man you're building.",
    "That's what legacy looks like in real time.",
    "That's your standard rising.",
    "That's purpose showing up as action.",
    "That's the version of you the world needs.",
    "That's what separates the ones who make it.",
    "That's discipline becoming identity.",
    "That's the foundation nobody sees but everybody feels.",
    "That's what it looks like when you choose yourself.",
    "That's the work that changes everything.",
]

QUESTIONS = [
    "Still doing this?",
    "Still okay with that?",
    "Still choosing that version?",
    "Still letting it slide?",
    "Still pretending it's fine?",
    "Still avoiding it?",
    "Still stopping early?",
    "Still playing safe?",
    "Still lying to yourself?",
    "Still comfortable with that?",
    "Still not changing?",
    "Still repeating it?",
    "Still weak here?",
    "Still the same?",
    "Or are you done?",
]

PURPOSE_QUESTIONS = [
    "Are you building or just existing?",
    "What are you leaving behind?",
    "Is today worth remembering?",
    "Are you becoming him?",
    "What does your future self see right now?",
    "Are you doing the work?",
    "Is this the standard you want to live by?",
    "Are you showing up?",
    "What story are you writing today?",
    "Are you the man you said you'd be?",
]

CTAS = [
    "Prove it. Comment DISCIPLINE.",
    "Type DISCIPLINE if you're done.",
    "Don't scroll. Commit.",
    "Say it publicly. DISCIPLINE.",
    "Lock in or leave.",
    "Decide right now.",
    "This is where it changes.",
    "Show me, don't think.",
    "No excuses. Type DISCIPLINE.",
    "Stand on it. Comment DISCIPLINE.",
    "If you mean it - prove it.",
    "Choose your side.",
    "Stay soft or speak up.",
    "Draw the line here.",
    "This is your moment.",
]

CHALLENGE_CTAS = [
    "Join the Inner Discipline Challenge. DM DISCIPLINE.",
    "30 days. Facebook group. DM DISCIPLINE.",
    "The group is open. DM DISCIPLINE.",
    "Join 30 days of accountability. DM DISCIPLINE.",
    "Stop doing it alone. DM DISCIPLINE.",
    "Daily check-ins. Real accountability. DM DISCIPLINE.",
    "Your 30-day standard starts here. DM DISCIPLINE.",
    "The group won't wait. DM DISCIPLINE.",
    "Lock in for 30 days. DM DISCIPLINE.",
    "Join the challenge. DM DISCIPLINE.",
]

PURPOSE_CTAS = [
    "Comment LEGEND if you're building.",
    "Type LEGACY if this hit.",
    "Start today. Comment PURPOSE.",
    "Say it. I AM BUILDING.",
    "This is your sign. Comment LEGEND.",
    "Lock in. Comment PURPOSE.",
    "Decide who you're becoming. Comment LEGACY.",
    "The work starts now. Comment BUILD.",
    "Type LEGEND if you felt this.",
    "Your legacy starts here. Comment PURPOSE.",
]

# ---------------- LOGO OVERLAY ----------------

def make_logo_overlay():
    if not os.path.exists(LOGO_PATH):
        print(f"âš ï¸  Logo not found at '{LOGO_PATH}' â€” skipping.")
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

# ---------------- TEXT ENGINE ----------------

def make_text(text, highlight_first_word=True):
    # ================================================================
    # âœ… ORANGE FIRST-WORD HIGHLIGHT ENGINE
    # First word of every chunk = orange. Rest = white.
    # Matches the Wisdom Uncle style â€” stops the scroll.
    # ================================================================
    text = text.replace("\u2014", "-").replace("\u2013", "-")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2026", "...")
    text = text.upper()

    img  = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if not os.path.exists(FONT_PATH):
        raise FileNotFoundError(
            f"Font not found: '{FONT_PATH}'. "
            "Download Anton-Regular.ttf from Google Fonts."
        )

    font_size = 92
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
    y                = (H - total_height) // 2
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

            draw.text(
                (x, y), word, font=font,
                fill=color, stroke_width=5, stroke_fill="black"
            )
            x += word_width + space_width

        y += font_size + 22

    return np.array(img)

# ---------------- TTS ----------------

async def tts_async(text, filename):
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH, volume=VOLUME)
    await communicate.save(filename)

def generate_voice(text, filename):
    asyncio.run(tts_async(text, filename))

# ---------------- SCRIPT BUILDER ----------------

SET_ORDER = ["identity", "comfort", "time", "challenge", "purpose"]

def get_hook_from_category(category):
    global used_hooks
    pool = HOOKS.get(category, [])
    if not pool:
        pool = sum(HOOKS.values(), [])

    available = [h for h in pool if h not in used_hooks]
    if not available:
        used_hooks = []
        available  = pool.copy()

    hook = random.choice(available)
    used_hooks.append(hook)
    return hook

def build_script(category):
    # âœ… category passed in â€” never overwritten by get_set_category()
    hook = get_hook_from_category(category)

    if category == "challenge":
        truth    = random.choice(CHALLENGE_TRUTHS)
        question = random.choice(QUESTIONS)
        cta      = random.choice(CHALLENGE_CTAS)
    elif category == "purpose":
        truth    = random.choice(PURPOSE_TRUTHS)
        question = random.choice(PURPOSE_QUESTIONS)
        cta      = random.choice(PURPOSE_CTAS)
    else:
        truth    = random.choice(TRUTHS)
        question = random.choice(QUESTIONS)
        cta      = random.choice(CTAS)

    return [hook, truth, question, cta]

# ---------------- VIDEO BACKGROUND ENGINE ----------------

def load_video_background(video_path, target_duration):
    """
    Loads a video, crops/scales to 1080x1920, loops if shorter than target_duration,
    trims to target_duration, applies cinematic grade.
    Returns a VideoClip ready to composite.
    """
    clip = VideoFileClip(video_path)

    # âœ… Scale to fill 1080x1920 â€” no black bars
    clip_ratio   = clip.w / clip.h
    target_ratio = W / H

    if clip_ratio > target_ratio:
        # Wider than target â€” fit height, crop sides
        clip = clip.resize(height=H)
    else:
        # Taller/narrower â€” fit width, crop top/bottom
        clip = clip.resize(width=W)

    # Center crop to exact W x H
    x_center = clip.w / 2
    y_center  = clip.h / 2
    clip      = clip.crop(
        x_center=x_center, y_center=y_center,
        width=W, height=H
    )

    # âœ… Loop if video is shorter than reel duration
    if clip.duration < target_duration:
        clip = vfx.loop(clip, duration=target_duration)

    # Trim to exact duration
    clip = clip.subclip(0, target_duration)

    # âœ… Cinematic grade â€” darken + contrast, matches image pipeline
    clip = clip.fx(vfx.colorx, 0.72)         # brightness ~0.72
    clip = clip.fx(vfx.lum_contrast, lum=0, contrast=40, contrast_thr=127)

    return clip

# ---------------- PUNCH ZOOM ENGINE ----------------

def get_punch_scale(t, punches):
    """
    punches: list of (timestamp, peak_scale, attack_seconds)
    Between punches: drifts back to base 1.0 over 1.8s.
    """
    base  = 1.0
    scale = base
    for punch_t, peak, attack in punches:
        delta = t - punch_t
        if delta < 0:
            continue
        elif delta < attack:
            punch_scale = base + (peak - base) * (delta / attack)
        else:
            release     = max(0.0, 1.0 - (delta - attack) / 1.8)
            punch_scale = base + (peak - base) * release
        scale = max(scale, punch_scale)
    return scale

# Punch strength per script line
LINE_PUNCH = {
    0: (1.14, 0.20),   # hook      â€” hardest
    1: (1.08, 0.25),   # truth     â€” medium
    2: (1.11, 0.18),   # question  â€” sharp
    3: (1.09, 0.22),   # CTA       â€” firm
}
CHUNK_PUNCH_SCALE  = 1.06
CHUNK_PUNCH_ATTACK = 0.25

# ---------------- REEL ENGINE ----------------

def split_into_chunks(line, chunk_size=3):
    words  = line.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i + chunk_size]))
    return chunks

def make_reel(index, category, video_path):

    # âœ… category comes from run_queue â€” script is built to match it
    script      = build_script(category)
    voice_files = []

    try:
        print(f"\nðŸŽ¬ Reel {index+1} | Category: {category.upper()} | Video: {video_path}")

        # ---- Build subtitle + audio timeline first ----
        # We need total duration BEFORE creating video clips
        # so punch_times and reel_duration are ready.

        logo_array  = make_logo_overlay()
        clips       = []
        audio_clips = []
        punch_times = []
        timeline    = 0.5   # âœ… Small lead-in on video (no still frame needed â€” video moves)
        FADE_OUT    = 0.12
        LINE_NAMES  = {0: "HOOK", 1: "TRUTH", 2: "QUESTION", 3: "CTA"}

        for i, line in enumerate(script):

            voice_file = f"voice_{index}_{i}.mp3"
            voice_files.append(voice_file)
            generate_voice(line, voice_file)

            audio          = AudioFileClip(voice_file)
            voice_duration = audio.duration

            if voice_duration > 4.0:
                label = LINE_NAMES.get(i, f"LINE {i}")
                print(f"  âš ï¸  {label} is {voice_duration:.1f}s â€” consider shortening: \"{line[:50]}\"")

            chunks         = split_into_chunks(line, chunk_size=3)
            num_chunks     = len(chunks)
            chunk_duration = voice_duration / num_chunks

            audio_clips.append(audio.set_start(timeline))

            for j, chunk in enumerate(chunks):
                chunk_start = timeline + j * chunk_duration

                # Register punch
                if j == 0:
                    peak, attack = LINE_PUNCH.get(i, (1.08, 0.25))
                else:
                    peak, attack = CHUNK_PUNCH_SCALE, CHUNK_PUNCH_ATTACK
                punch_times.append((chunk_start, peak, attack))

                if j == num_chunks - 1:
                    text_duration = (voice_duration - j * chunk_duration) + FADE_OUT
                else:
                    text_duration = chunk_duration

                text_img  = make_text(chunk)
                text_clip = (
                    ImageClip(text_img)
                    .set_start(chunk_start)
                    .set_duration(text_duration)
                    .fadein(0.08)
                    .fadeout(FADE_OUT)
                )
                clips.append(text_clip)

            if i == len(script) - 1:
                timeline += voice_duration + FADE_OUT
            else:
                timeline += voice_duration + FADE_OUT + 0.15

        reel_duration = float(min(timeline, MAX_REEL_LENGTH))

        if timeline > MAX_REEL_LENGTH:
            print(f"  âš ï¸  Reel {index+1} is {timeline:.1f}s â€” trimmed to {MAX_REEL_LENGTH}s.")

        # ---- Load + grade video background ----
        bg_clip = load_video_background(video_path, reel_duration)

        # ---- Apply punch zoom to video via fl_time + resize ----
        # We apply the zoom by resizing each frame via a lambda
        def zoom_frame(get_frame, t):
            scale  = get_punch_scale(t, punch_times)
            frame  = get_frame(t)
            if scale == 1.0:
                return frame
            h, w   = frame.shape[:2]
            new_w  = int(w * scale)
            new_h  = int(h * scale)
            pil    = Image.fromarray(frame).resize((new_w, new_h), Image.BILINEAR)
            # Center crop back to W x H
            left   = (new_w - W) // 2
            top    = (new_h - H) // 2
            pil    = pil.crop((left, top, left + W, top + H))
            return np.array(pil)

        bg_clip = bg_clip.fl(zoom_frame, apply_to=["mask"])

        # ---- Top vignette overlay (dark gradient from top) ----
        vignette_arr    = np.zeros((H, W, 4), dtype=np.uint8)
        vignette_height = int(H * 0.55)
        for row in range(vignette_height):
            alpha = int(255 * (1.0 - (row / vignette_height) ** 1.6))
            vignette_arr[row, :, 3] = alpha   # only alpha, RGB stays 0 (black)

        vignette_clip = (
            ImageClip(vignette_arr)
            .set_duration(reel_duration)
        )

        # ---- Composite all layers ----
        all_layers = [bg_clip, vignette_clip] + clips

        if logo_array is not None:
            logo_clip = (
                ImageClip(logo_array)
                .set_start(0)
                .set_duration(reel_duration)
                .fadein(0.4)
            )
            all_layers.append(logo_clip)

        final_video = CompositeVideoClip(all_layers, size=(W, H))
        final_video = final_video.set_duration(reel_duration)
        final_video = final_video.fadeout(0.3)

        # ---- Audio assembly ----
        final_voice = CompositeAudioClip(audio_clips)

        if os.path.exists("music.mp3"):
            music          = AudioFileClip("music.mp3")
            music_duration = reel_duration - MUSIC_DELAY
            if music_duration > 0:
                music       = afx.audio_loop(music, duration=music_duration)
                music       = music.audio_fadein(0.8)
                music       = music.volumex(0.14)
                music       = music.set_start(MUSIC_DELAY)
                final_audio = CompositeAudioClip([music, final_voice.volumex(1.12)])
            else:
                final_audio = final_voice
        else:
            final_audio = final_voice

        final      = final_video.set_audio(final_audio)
        video_path_out = f"outputs/reel_{index+1}.mp4"

        final.write_videofile(
            video_path_out,
            fps=FPS,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            preset="fast",
        )

        title   = f"{script[0]} | INNER DISCIPLINE"
        caption = build_caption(script, category)

        with open(f"outputs/reel_{index+1}_title.txt", "w") as f:
            f.write(title)
        with open(f"outputs/reel_{index+1}_caption.txt", "w") as f:
            f.write(caption)

        print(f"  âœ… Reel {index+1} complete â†’ {video_path_out}")

    except Exception as e:
        import traceback
        print(f"  âŒ Reel {index+1} failed: {e}")
        traceback.print_exc()

    finally:
        for vf in voice_files:
            if os.path.exists(vf):
                os.remove(vf)

# ---------------- HASHTAG POOLS ----------------

HASHTAG_POOL = {
    "big":    ["#discipline", "#motivation", "#mindset", "#fitness",
               "#success", "#selfimprovement", "#gym", "#hardwork"],
    "medium": ["#selfmastery", "#selfcontrol", "#mentalstrength",
               "#consistency", "#dailymotivation", "#growthmindset",
               "#personaldevelopment", "#focus"],
    "niche":  ["#innerdiscipline", "#disciplinedmind", "#selfgrowth",
               "#dailyhabits", "#noexcuses", "#accountability",
               "#mindsetshift", "#innerwork"],
}

CHALLENGE_HASHTAGS = [
    "#30daychallenge", "#accountabilitygroup", "#disciplinechallenge",
    "#30days", "#jointhegroup", "#innerdisciplinechallenge",
    "#accountability", "#facebookgroup", "#selfimprovementchallenge",
    "#disciplinegroup",
]

PURPOSE_HASHTAGS = [
    "#legacy", "#becomelegend", "#purpose", "#becomethebestversion",
    "#growthmindset", "#levelup", "#mentalhealth", "#masculinity",
    "#selfmastery", "#innerdiscipline",
]

def pick_hashtags(category=None):
    if category == "challenge":
        selected = ["#innerdiscipline"] + random.sample(CHALLENGE_HASHTAGS, 6) + random.sample(HASHTAG_POOL["big"], 3)
        random.shuffle(selected)
        return " ".join(selected[:10])
    if category == "purpose":
        selected = ["#innerdiscipline"] + random.sample(PURPOSE_HASHTAGS, 6) + random.sample(HASHTAG_POOL["big"], 3)
        random.shuffle(selected)
        return " ".join(selected[:10])
    brand    = ["#innerdiscipline"]
    big      = random.sample(HASHTAG_POOL["big"], 3)
    medium   = random.sample(HASHTAG_POOL["medium"], 3)
    niche    = random.sample([h for h in HASHTAG_POOL["niche"] if h != "#innerdiscipline"], 3)
    selected = brand + big + medium + niche
    random.shuffle(selected)
    return " ".join(selected)

# ---------------- CAPTION TEMPLATES ----------------

CAPTION_OPENERS = [
    "Most people won't admit this to themselves.",
    "This is the part nobody talks about.",
    "Read this slowly.",
    "You needed to hear this today.",
    "Stop scrolling. This is for you.",
    "The truth nobody wants to say.",
    "Save this. You'll need it again.",
    "This is what separates them from you.",
    "Be honest with yourself for 10 seconds.",
    "The uncomfortable truth about discipline.",
]

CHALLENGE_OPENERS = [
    "You've been trying to do this alone. There's a better way.",
    "30 days of accountability. A room full of people who don't accept excuses.",
    "The Inner Discipline Challenge is open. This is your sign.",
    "Most people quit because no one is watching. We fix that.",
    "Accountability changes everything. This group proves it.",
    "You don't need more willpower. You need the right environment.",
    "30 days. Daily check-ins. Real people. Real results.",
    "The group that won't let you settle. Join us.",
]

PURPOSE_OPENERS = [
    "This one is for the men who are building in silence.",
    "Legacy is built in the moments nobody sees.",
    "Read this if you're serious about who you're becoming.",
    "The man you're meant to be is built today.",
    "This is for the ones who chose to rise.",
    "Not everyone is meant for average. This is for you.",
    "You were built for more. Here's the reminder.",
    "The world needs the man you're becoming. Don't stop.",
]

CAPTION_CLOSERS = [
    "Comment DISCIPLINE if you're locking in today.",
    "Tag someone who needs to see this.",
    "Save this for the next time you want to quit.",
    "Follow for daily discipline content.",
    "Drop a DISCIPLINE below if this hit.",
    "Share this with someone who needs the push.",
    "Follow @innerdiscipline for more.",
    "This page is for the ones who are done making excuses.",
]

CHALLENGE_CLOSERS = [
    "Link in bio. Join the Inner Discipline Challenge today.",
    "Under $20/month. Link in bio. No excuses.",
    "The group is open right now. Link in bio.",
    "30 days starts when you click the link in bio.",
    "Join us. Link in bio. Let's lock in together.",
    "Daily check-ins. Real accountability. Link in bio.",
]

PURPOSE_CLOSERS = [
    "Comment LEGEND if you're building your legacy.",
    "Tag a man who needs to hear this.",
    "Save this. Read it on the days you want to quit.",
    "Follow @innerdiscipline â€” daily content for men who are serious.",
    "Type LEGACY if this hit different.",
    "Share this with someone who is becoming great.",
]

def build_caption(script, category=None):
    if category == "challenge":
        opener = random.choice(CHALLENGE_OPENERS)
        closer = random.choice(CHALLENGE_CLOSERS)
    elif category == "purpose":
        opener = random.choice(PURPOSE_OPENERS)
        closer = random.choice(PURPOSE_CLOSERS)
    else:
        opener = random.choice(CAPTION_OPENERS)
        closer = random.choice(CAPTION_CLOSERS)

    hashtags = pick_hashtags(category)

    return "\n".join([
        opener, "",
        f'"{script[0]}"', "",
        script[1], "",
        script[2], "",
        "-",
        closer, "",
        hashtags,
    ])

# ---------------- RUN ----------------

print("ðŸŽ¬ INNER DISCIPLINE â€” 5-SET VIDEO ENGINE")
print("=" * 50)

all_videos = get_all_videos()

if not all_videos:
    raise Exception(
        "No background videos found.\n"
        "Add files named bg1.mp4, bg2.mp4 ... bg5.mp4 (minimum 5) to this folder."
    )

if len(all_videos) < REELS_PER_RUN:
    print(f"âš ï¸  Only {len(all_videos)} video(s) found â€” need {REELS_PER_RUN} for a full run.")
    print(f"   Repeats will occur. Add more bg*.mp4 files to avoid this.")
    selected_videos = [all_videos[i % len(all_videos)] for i in range(REELS_PER_RUN)]
else:
    selected_videos = random.sample(all_videos, REELS_PER_RUN)

# âœ… Build run queue â€” category determined by set_step rotation
run_queue = []
for i in range(REELS_PER_RUN):
    category = SET_ORDER[set_step % len(SET_ORDER)]
    set_step += 1
    last_category = category
    video_path    = selected_videos[i]
    run_queue.append((i, category, video_path))
    print(f"   Reel {i+1} â†’ [{category.upper()}] {video_path}")

print("=" * 50)

for reel_index, category, video_path in run_queue:
    make_reel(reel_index, category, video_path)

# âœ… Save memory state
json.dump(used_hooks,    open(HOOK_MEMORY_FILE,     "w"))
json.dump(last_category, open(CATEGORY_MEMORY_FILE, "w"))
json.dump(set_step,      open(SET_STEP_FILE,         "w"))

print("\nðŸ”¥ INNER DISCIPLINE 5-SET COMPLETE")
