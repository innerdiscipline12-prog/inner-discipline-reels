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
MAX_REEL_LENGTH = 15.0   # Hard ceiling â€” never exceed this

VOICE = "en-US-GuyNeural"
RATE = "-10%"    # âœ… Much faster â€” was -38% which added 4-6s per reel
PITCH = "-45Hz"
VOLUME = "+0%"

FONT_PATH = "Anton-Regular.ttf"
LOGO_PATH = "logo.png"           # âœ… Your Inner Discipline logo file
LOGO_OPACITY = 0.72              # âœ… Semi-transparent (0.0 = invisible, 1.0 = fully visible)
LOGO_SIZE = 160                  # âœ… Logo width in pixels (height scales automatically)
LOGO_BOTTOM_MARGIN = 90          # âœ… Distance from bottom of frame

REELS_PER_RUN = 3

# ---------------- RETENTION SETTINGS ----------------

STILL_FRAME_DURATION = 1.0      # âœ… Tightened from 1.6s â€” saves 0.6s per reel
STILL_ZOOM_END = 1.06
MUSIC_DELAY = 1.5               # âœ… Tightened from 2.0s
SUBTITLE_DELAY = 0.0

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
        "You made weakness routine."
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
        "You didn't go far enough."
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
        "You did nothing again."
    ]
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
    "That's your default setting."
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
    "Or are you done?"
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
    "This is your moment."
]

# ---------------- LOGO OVERLAY ----------------

def make_logo_overlay():
    """
    Loads logo.png, resizes it, applies opacity, 
    and positions it bottom-center on a transparent canvas.
    Returns a numpy RGBA array ready for ImageClip.
    """
    if not os.path.exists(LOGO_PATH):
        print(f"âš ï¸  Logo not found at '{LOGO_PATH}' â€” skipping logo overlay.")
        return None

    logo = Image.open(LOGO_PATH).convert("RGBA")

    # Scale logo maintaining aspect ratio
    aspect = logo.height / logo.width
    new_w = LOGO_SIZE
    new_h = int(LOGO_SIZE * aspect)
    logo = logo.resize((new_w, new_h), Image.LANCZOS)

    # Apply opacity to alpha channel only
    r, g, b, a = logo.split()
    a = a.point(lambda p: int(p * LOGO_OPACITY))
    logo = Image.merge("RGBA", (r, g, b, a))

    # Composite onto full-frame transparent canvas
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x = (W - new_w) // 2
    y = H - new_h - LOGO_BOTTOM_MARGIN
    canvas.paste(logo, (x, y), logo)

    return np.array(canvas)

# ---------------- TEXT ENGINE ----------------

def make_text(text):
    # âœ… FIX: Strip special chars that break Anton font (em dash, smart quotes etc)
    text = text.replace("\u2014", "-").replace("\u2013", "-")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2026", "...")
    text = text.upper()  # ALL CAPS â€” Inner Discipline brand
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if not os.path.exists(FONT_PATH):
        raise FileNotFoundError(
            f"Font not found: '{FONT_PATH}'. "
            "Download Anton-Regular.ttf from Google Fonts and place it in this directory."
        )

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

SET_ORDER = ["identity", "comfort", "time"]

def get_set_category():
    global set_step
    cat = SET_ORDER[set_step % len(SET_ORDER)]
    set_step += 1
    last_category = cat  # âœ… Fixed: actually update last_category
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
    voice_files = []

    try:
        backgrounds = glob.glob("bg*.mp4")
        if not backgrounds:
            raise Exception("No bg*.mp4 files found in current directory.")

        bg_path = random.choice(backgrounds)
        raw_video = VideoFileClip(bg_path).without_audio()

        # âœ… FIX: Scale to FILL full 1080x1920 â€” no black bars
        # Strategy: scale so BOTH dimensions meet or exceed W x H, then crop center
        clip_ratio = raw_video.w / raw_video.h
        target_ratio = W / H

        if clip_ratio > target_ratio:
            # Video is wider than target â€” fit height, crop sides
            raw_video = raw_video.resize(height=H)
        else:
            # Video is taller/narrower than target â€” fit width, crop top/bottom
            raw_video = raw_video.resize(width=W)

        # Crop to exact frame â€” always center
        raw_video = raw_video.crop(
            x_center=raw_video.w / 2,
            y_center=raw_video.h / 2,
            width=W,
            height=H
        )

        raw_video = raw_video.fx(vfx.colorx, 1.05)

        # âœ… RETENTION UPGRADE 1: Still image / slow zoom for first STILL_FRAME_DURATION seconds
        # Grab the very first frame and turn it into a zooming still
        first_frame = raw_video.get_frame(0)
        still_clip = (
            ImageClip(first_frame)
            .set_duration(STILL_FRAME_DURATION)
            .fx(vfx.resize, lambda t: 1 + (STILL_ZOOM_END - 1) * (t / STILL_FRAME_DURATION))
        )
        # Crop still_clip to keep it W x H during zoom
        still_clip = still_clip.crop(
            x_center=W / 2,
            y_center=H / 2,
            width=W,
            height=H
        )

        # Main video plays after the still frame, with continuing slow zoom
        main_video = raw_video.fx(vfx.resize, lambda t: STILL_ZOOM_END + 0.02 * t)
        main_video = main_video.set_start(STILL_FRAME_DURATION)

        # Stitch still + main video as base
        base = concatenate_videoclips([still_clip, main_video])

        # âœ… Build logo overlay clip (persistent across full reel duration)
        logo_array = make_logo_overlay()

        clips = []
        audio_clips = []

        # âœ… RETENTION UPGRADE 3: Subtitles start AFTER the still frame pause
        timeline = STILL_FRAME_DURATION + 0.1

        is_last = lambda i: i == len(script) - 1

        for i, line in enumerate(script):

            voice_file = f"voice_{index}_{i}.mp3"
            voice_files.append(voice_file)
            generate_voice(line, voice_file)

            audio = AudioFileClip(voice_file)
            voice_duration = audio.duration

            # Tight gaps â€” every second counts
            FADE_OUT = 0.15
            if is_last(i):
                duration = voice_duration + FADE_OUT        # ends right after voice
            else:
                duration = voice_duration + FADE_OUT + 0.1  # minimal gap between lines

            text_img = make_text(line)
            text_clip = (
                ImageClip(text_img)
                .set_start(timeline)
                .set_duration(duration)
                .fadein(0.12)
                .fadeout(FADE_OUT)   # fadeout happens AFTER voice ends, not during
            )

            clips.append(text_clip)
            audio_clips.append(audio.set_start(timeline))
            timeline += duration

        # âœ… FIX: NEVER cut mid-voice. Timeline is set by actual content length.
        # MAX_REEL_LENGTH is only a safety net â€” log a warning if exceeded, don't cut.
        if timeline > MAX_REEL_LENGTH:
            print(f"âš ï¸  Reel {index+1} is {timeline:.1f}s â€” consider shorter scripts.")
        # No clamping â€” voice and text always play fully

        # âœ… Add logo as top layer â€” visible entire reel duration
        all_layers = [base] + clips
        if logo_array is not None:
            logo_clip = (
                ImageClip(logo_array)
                .set_start(0)
                .set_duration(timeline)
                .fadein(0.4)
            )
            all_layers.append(logo_clip)

        final_video = CompositeVideoClip(all_layers)
        final_video = final_video.set_duration(timeline)
        final_video = final_video.fadeout(0.25)

        # âœ… Let voice play its full natural length â€” no subclip cut
        final_voice = CompositeAudioClip(audio_clips)

        # âœ… RETENTION UPGRADE 2: Music delayed by MUSIC_DELAY seconds
        # First 2 seconds = silence = viewer leans in, algorithm sees watch time spike
        if os.path.exists("music.mp3"):
            music = AudioFileClip("music.mp3")
            music_duration = timeline - MUSIC_DELAY
            if music_duration > 0:
                music = afx.audio_loop(music, duration=music_duration)
                music = music.audio_fadein(0.8)
                music = music.volumex(0.14)
                music = music.set_start(MUSIC_DELAY)
                final_audio = CompositeAudioClip([music, final_voice.volumex(1.12)])
            else:
                final_audio = final_voice
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
        caption = build_caption(script)

        with open(f"outputs/reel_{index+1}_title.txt", "w") as f:
            f.write(title)

        with open(f"outputs/reel_{index+1}_caption.txt", "w") as f:
            f.write(caption)

        print(f"âœ… Reel {index+1} complete â†’ {video_path}")

    except Exception as e:
        print(f"âŒ Reel {index+1} failed: {e}")

    finally:
        # âœ… Clean up voice temp files regardless of success/failure
        for vf in voice_files:
            if os.path.exists(vf):
                os.remove(vf)

# ---------------- HASHTAG POOLS (rotates to avoid repetition) ----------------

HASHTAG_POOL = {
    "big": [        # 1M+ posts â€” broad reach
        "#discipline", "#motivation", "#mindset", "#fitness",
        "#success", "#selfimprovement", "#gym", "#hardwork",
    ],
    "medium": [     # 100Kâ€“1M posts â€” targeted reach
        "#selfmastery", "#selfcontrol", "#mentalstrength",
        "#consistency", "#dailymotivation", "#growthmindset",
        "#personaldevelopment", "#focus",
    ],
    "niche": [      # Under 100K â€” high relevance, low competition
        "#innerdiscipline", "#disciplinedmind", "#selfgrowth",
        "#dailyhabits", "#noexcuses", "#accountability",
        "#mindsetshift", "#innerwork",
    ],
}

def pick_hashtags():
    """
    Safe 10-tag strategy:
    - 1 brand tag (always)
    - 3 big tags
    - 3 medium tags
    - 3 niche tags
    Total: 10 â€” relevant, varied, not spammy
    """
    brand = ["#innerdiscipline"]
    big = random.sample(HASHTAG_POOL["big"], 3)
    medium = random.sample(HASHTAG_POOL["medium"], 3)
    niche = random.sample([h for h in HASHTAG_POOL["niche"] if h != "#innerdiscipline"], 3)
    selected = brand + big + medium + niche
    random.shuffle(selected)
    return " ".join(selected)

# ---------------- CAPTION TEMPLATES (rotates for variety) ----------------

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

def build_caption(script):
    opener = random.choice(CAPTION_OPENERS)
    closer = random.choice(CAPTION_CLOSERS)
    hashtags = pick_hashtags()

    caption = "\n".join([
        opener,
        "",
        f'"{script[0]}"',
        "",
        script[1],
        "",
        script[2],
        "",
        "â€”",
        closer,
        "",
        hashtags,
    ])
    return caption

for i in range(REELS_PER_RUN):
    make_reel(i)

# âœ… Save memory state after all reels complete
json.dump(used_hooks, open(HOOK_MEMORY_FILE, "w"))
json.dump(last_category, open(CATEGORY_MEMORY_FILE, "w"))
json.dump(set_step, open(SET_STEP_FILE, "w"))

print("ðŸ”¥ INNER DISCIPLINE SET-OF-3 COMPLETE")
