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
RATE = "-10%"
PITCH = "-45Hz"
VOLUME = "+0%"

FONT_PATH = "Anton-Regular.ttf"
LOGO_PATH = "logo.png"
LOGO_OPACITY = 0.38
LOGO_SIZE = 160
LOGO_BOTTOM_MARGIN = 90

REELS_PER_RUN = 4  # âœ… Now 4 â€” one full rotation per run

# ---------------- RETENTION SETTINGS ----------------

STILL_FRAME_DURATION = 1.0
STILL_ZOOM_END = 1.06
MUSIC_DELAY = 1.5
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
    ],
    # âœ… NEW â€” every 4th reel sells the Inner Discipline Challenge group
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

# âœ… NEW â€” truths specific to challenge reels
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

# âœ… NEW â€” CTAs that drive clicks to the paid Facebook group
CHALLENGE_CTAS = [
    "Join the Inner Discipline Challenge. DM DISCIPLINE.",
    "30 days. Facebook group. Under $10. DM DISCIPLINE.",
    "The group is open. DM DISCIPLINE.",
    "Join 30 days of accountability. DM DISCIPLINE.",
    "Stop doing it alone. DM DISCIPLINE.",
    "Daily check-ins. Real accountability. DM DISCIPLINE.",
    "Your 30-day standard starts here. DM DISCIPLINE.",
    "The group won't wait. DM DISCIPLINE.",
    "Lock in for 30 days. DM DISCIPLINE.",
    "Join the challenge. DM DISCIPLINE.",
]

# ---------------- LOGO OVERLAY ----------------

def make_logo_overlay():
    if not os.path.exists(LOGO_PATH):
        print(f"âš ï¸  Logo not found at '{LOGO_PATH}' â€” skipping logo overlay.")
        return None

    logo = Image.open(LOGO_PATH).convert("RGBA")

    aspect = logo.height / logo.width
    new_w = LOGO_SIZE
    new_h = int(LOGO_SIZE * aspect)
    logo = logo.resize((new_w, new_h), Image.LANCZOS)

    r, g, b, a = logo.split()
    a = a.point(lambda p: int(p * LOGO_OPACITY))
    logo = Image.merge("RGBA", (r, g, b, a))

    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x = (W - new_w) // 2
    y = H - new_h - LOGO_BOTTOM_MARGIN
    canvas.paste(logo, (x, y), logo)

    return np.array(canvas)

# ---------------- TEXT ENGINE ----------------

def make_text(text, highlight_first_word=True):
    # ================================================================
    # âœ… ORANGE FIRST-WORD HIGHLIGHT ENGINE
    # First word of every chunk renders in orange â€” stops the scroll.
    # Remaining words render in white. Same stroke on both.
    # Matches the Wisdom Uncle style that drives 21kâ€“56k views.
    # ================================================================
    text = text.replace("\u2014", "-").replace("\u2013", "-")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2026", "...")
    text = text.upper()

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

    # Word wrap â€” same as before
    words = text.split()
    lines = []
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

    # âœ… Track whether we've drawn the first word yet
    first_word_drawn = False

    ORANGE = (255, 140, 0, 255)   # âœ… Bold orange â€” matches Wisdom Uncle style
    WHITE  = (255, 255, 255, 255)

    for line in lines:
        line_words = line.split()
        if not line_words:
            y += font_size + 22
            continue

        # Measure full line width for centering
        line_width = draw.textlength(line, font=font)
        x = (W - line_width) // 2

        for i, word in enumerate(line_words):
            word_width = draw.textlength(word, font=font)
            space_width = draw.textlength(" ", font=font) if i < len(line_words) - 1 else 0

            # âœ… First word of the entire chunk = orange, rest = white
            if highlight_first_word and not first_word_drawn:
                color = ORANGE
                first_word_drawn = True
            else:
                color = WHITE

            draw.text(
                (x, y),
                word,
                font=font,
                fill=color,
                stroke_width=5,
                stroke_fill="black"
            )
            x += word_width + space_width

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

# âœ… challenge added â€” every 4th reel converts to paid group
SET_ORDER = ["identity", "comfort", "time", "challenge"]

def get_set_category():
    global set_step, last_category  # âœ… BUG 1 FIX â€” last_category is global
    cat = SET_ORDER[set_step % len(SET_ORDER)]
    set_step += 1
    last_category = cat
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
    # âœ… Challenge reels use targeted truths and conversion CTAs
    truth = random.choice(CHALLENGE_TRUTHS if category == "challenge" else TRUTHS)
    question = random.choice(QUESTIONS)
    cta = random.choice(CHALLENGE_CTAS if category == "challenge" else CTAS)
    return [hook, truth, question, cta], category

# ---------------- REEL ENGINE ----------------

def make_reel(index, bg_path):

    script_data = build_script()
    script, category = script_data
    voice_files = []

    try:
        print(f"ðŸ–¼ï¸  Reel {index+1} | Category: {category} | Background: {bg_path}")

        bg_img = Image.open(bg_path).convert("RGB")

        img_ratio = bg_img.width / bg_img.height
        target_ratio = W / H

        if img_ratio > target_ratio:
            new_h = H
            new_w = int(H * img_ratio)
        else:
            new_w = W
            new_h = int(W / img_ratio)

        bg_img = bg_img.resize((new_w, new_h), Image.LANCZOS)

        left = (new_w - W) // 2
        top = (new_h - H) // 2
        bg_img = bg_img.crop((left, top, left + W, top + H))

        from PIL import ImageEnhance, ImageFilter

        bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=1.4))
        bg_img = ImageEnhance.Brightness(bg_img).enhance(0.72)
        bg_img = ImageEnhance.Contrast(bg_img).enhance(1.25)

        bg_array_float = np.array(bg_img, dtype=np.float32)

        gradient = np.ones((H, W), dtype=np.float32)
        vignette_height = int(H * 0.55)
        for row in range(vignette_height):
            gradient[row, :] = (row / vignette_height) ** 1.6

        gradient_3ch = np.stack([gradient] * 3, axis=-1)
        bg_array_float = bg_array_float * gradient_3ch
        bg_img = Image.fromarray(np.clip(bg_array_float, 0, 255).astype(np.uint8))
        bg_array = np.array(bg_img)

        ZOOM_START = 1.0
        ZOOM_END   = 1.08

        EFFECTS = ["rain", "embers", "dust", "fog", "lightning"]

        # âœ… Effect matched to category â€” intentional mood, not random
        CATEGORY_EFFECTS = {
            "identity":  ["embers", "lightning"],  # burning self image + harsh wake-up
            "comfort":   ["fog", "rain"],           # hidden in comfort + being rained on
            "time":      ["dust", "rain"],          # fading away + time slipping through
            "challenge": ["embers", "fog"],         # transformation + mystery of what's inside
        }
        effect_pool = CATEGORY_EFFECTS.get(category, EFFECTS)
        chosen_effect = random.choice(effect_pool)
        print(f"âœ¨ Reel {index+1} | Effect: {chosen_effect}")

        rng = np.random.default_rng(seed=index * 7 + 13)

        NUM_PARTICLES = 160

        rain_x       = rng.integers(0, W,   size=NUM_PARTICLES).astype(float)
        rain_y       = rng.integers(0, H,   size=NUM_PARTICLES).astype(float)
        rain_len     = rng.integers(18, 55, size=NUM_PARTICLES).astype(float)
        rain_speed   = rng.uniform(18, 38,  size=NUM_PARTICLES)
        rain_opacity = rng.uniform(55, 130, size=NUM_PARTICLES).astype(int)
        rain_angle   = 0.18

        ember_x       = rng.integers(0, W,   size=NUM_PARTICLES).astype(float)
        ember_y       = rng.integers(0, H,   size=NUM_PARTICLES).astype(float)
        ember_speed   = rng.uniform(0.4, 1.8, size=NUM_PARTICLES)
        ember_drift   = rng.uniform(-0.3, 0.3, size=NUM_PARTICLES)
        ember_size    = rng.integers(2, 5,   size=NUM_PARTICLES)
        ember_opacity = rng.integers(120, 220, size=NUM_PARTICLES)

        dust_x       = rng.integers(0, W,   size=NUM_PARTICLES).astype(float)
        dust_y       = rng.integers(0, H,   size=NUM_PARTICLES).astype(float)
        dust_speed   = rng.uniform(0.2, 0.8, size=NUM_PARTICLES)
        dust_size    = rng.integers(1, 4,   size=NUM_PARTICLES)
        dust_opacity = rng.integers(30, 90, size=NUM_PARTICLES)

        fog_y       = rng.integers(0, H, size=40).astype(float)
        fog_speed   = rng.uniform(0.05, 0.2, size=40)
        fog_opacity = rng.integers(15, 45, size=40)
        fog_height  = rng.integers(60, 180, size=40)

        total_frames_est = int(MAX_REEL_LENGTH * FPS)
        lightning_frames = sorted(rng.integers(
            int(FPS * 3), total_frames_est,
            size=rng.integers(2, 5)
        ).tolist())

        # âœ… BUG 3 FIX â€” bake once, index per frame â€” no recalculation
        def bake_shake(total_frames, intensity=3):
            t = np.linspace(0, total_frames / FPS, total_frames)
            dx = (intensity * np.sin(2.3 * t + 0.5)
                + intensity * 0.5 * np.sin(5.1 * t + 1.2)).astype(int)
            dy = (intensity * np.sin(1.7 * t + 0.9)
                + intensity * 0.4 * np.sin(4.3 * t + 2.1)).astype(int)
            return dx, dy

        reel_total_frames = int(MAX_REEL_LENGTH * FPS) + 10
        baked_dx, baked_dy = bake_shake(reel_total_frames)

        def make_cinematic_frame(t, total_duration):
            frame_idx = int(t * FPS)

            scale = ZOOM_START + (ZOOM_END - ZOOM_START) * (t / max(total_duration, 0.001))
            new_w = int(W * scale)
            new_h = int(H * scale)
            zoomed = Image.fromarray(bg_array).resize((new_w, new_h), Image.BILINEAR)

            idx = min(frame_idx, len(baked_dx) - 1)
            cx  = max(0, min((new_w - W) // 2 + int(baked_dx[idx]), new_w - W))
            cy  = max(0, min((new_h - H) // 2 + int(baked_dy[idx]), new_h - H))
            frame_arr = np.array(zoomed.crop((cx, cy, cx + W, cy + H)), dtype=np.uint8)

            fx_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            fx_draw  = ImageDraw.Draw(fx_layer)

            if chosen_effect == "rain":
                for i in range(NUM_PARTICLES):
                    yp = (rain_y[i] + rain_speed[i] * t * FPS * 0.5) % H
                    xp = (rain_x[i] + yp * np.tan(rain_angle)) % W
                    xe = xp - rain_len[i] * np.sin(rain_angle)
                    ye = yp - rain_len[i] * np.cos(rain_angle)
                    fx_draw.line(
                        [(int(xp), int(yp)), (int(xe), int(ye))],
                        fill=(200, 220, 255, int(rain_opacity[i])), width=1
                    )

            elif chosen_effect == "embers":
                for i in range(NUM_PARTICLES):
                    yp = (ember_y[i] - ember_speed[i] * t * 60) % H
                    xp = (ember_x[i] + ember_drift[i] * t * 60) % W
                    r  = int(ember_size[i])
                    fx_draw.ellipse(
                        [(int(xp)-r, int(yp)-r), (int(xp)+r, int(yp)+r)],
                        fill=(255, random.randint(80, 160), 20, int(ember_opacity[i]))
                    )

            elif chosen_effect == "dust":
                for i in range(NUM_PARTICLES):
                    xp = (dust_x[i] + dust_speed[i] * t * 60) % W
                    yp = dust_y[i]
                    r  = int(dust_size[i])
                    fx_draw.ellipse(
                        [(int(xp)-r, int(yp)-r), (int(xp)+r, int(yp)+r)],
                        fill=(210, 190, 150, int(dust_opacity[i]))
                    )

            elif chosen_effect == "fog":
                for i in range(40):
                    xp = (-W + (fog_speed[i] * t * 60)) % (W * 2) - W
                    yp = int(fog_y[i])
                    fh = int(fog_height[i])
                    fog_rect = Image.new("RGBA", (W * 2, fh),
                        (200, 210, 220, int(fog_opacity[i])))
                    fx_layer.paste(fog_rect, (int(xp), yp), fog_rect)

            elif chosen_effect == "lightning":
                near = [f for f in lightning_frames if abs(frame_idx - f) <= 2]
                if near:
                    dist     = abs(frame_idx - near[0])
                    strength = max(0, 60 - dist * 25)
                    flash    = Image.new("RGBA", (W, H), (255, 255, 255, strength))
                    fx_layer = Image.alpha_composite(fx_layer, flash)

            frame_pil = Image.fromarray(frame_arr).convert("RGBA")
            frame_pil = Image.alpha_composite(frame_pil, fx_layer)
            return np.array(frame_pil.convert("RGB"))

        # ================================================================
        # âœ… CHUNK TEXT ENGINE
        # ================================================================

        def split_into_chunks(line, chunk_size=3):
            words = line.split()
            chunks = []
            for i in range(0, len(words), chunk_size):
                chunks.append(" ".join(words[i:i + chunk_size]))
            return chunks

        logo_array = make_logo_overlay()

        clips = []
        audio_clips = []

        timeline = STILL_FRAME_DURATION + 0.1

        is_last_line = lambda i: i == len(script) - 1

        FADE_OUT = 0.12

        for i, line in enumerate(script):

            voice_file = f"voice_{index}_{i}.mp3"
            voice_files.append(voice_file)
            generate_voice(line, voice_file)

            audio = AudioFileClip(voice_file)
            voice_duration = audio.duration

            chunks = split_into_chunks(line, chunk_size=3)
            num_chunks = len(chunks)

            # âœ… Exact even slice â€” no drift
            chunk_duration = voice_duration / num_chunks

            audio_clips.append(audio.set_start(timeline))

            # âœ… BUG 2 FIX â€” exact positioning, last chunk absorbs remainder
            for j, chunk in enumerate(chunks):
                chunk_start = timeline + j * chunk_duration

                if j == num_chunks - 1:
                    text_duration = (voice_duration - j * chunk_duration) + FADE_OUT
                else:
                    text_duration = chunk_duration

                text_img = make_text(chunk)
                text_clip = (
                    ImageClip(text_img)
                    .set_start(chunk_start)
                    .set_duration(text_duration)
                    .fadein(0.08)
                    .fadeout(FADE_OUT)
                )
                clips.append(text_clip)

            if is_last_line(i):
                timeline += voice_duration + FADE_OUT
            else:
                timeline += voice_duration + FADE_OUT + 0.15

        if timeline > MAX_REEL_LENGTH:
            print(f"âš ï¸  Reel {index+1} is {timeline:.1f}s â€” consider shorter scripts.")

        reel_duration = float(timeline)

        def make_frame(t):
            return make_cinematic_frame(t, reel_duration)

        base = VideoClip(make_frame, duration=reel_duration).set_fps(FPS)

        all_layers = [base] + clips
        if logo_array is not None:
            logo_clip = (
                ImageClip(logo_array)
                .set_start(0)
                .set_duration(reel_duration)
                .fadein(0.4)
            )
            all_layers.append(logo_clip)

        final_video = CompositeVideoClip(all_layers)
        final_video = final_video.set_duration(reel_duration)
        final_video = final_video.fadeout(0.25)

        final_voice = CompositeAudioClip(audio_clips)

        if os.path.exists("music.mp3"):
            music = AudioFileClip("music.mp3")
            music_duration = reel_duration - MUSIC_DELAY
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
        caption = build_caption(script, category)

        with open(f"outputs/reel_{index+1}_title.txt", "w") as f:
            f.write(title)

        with open(f"outputs/reel_{index+1}_caption.txt", "w") as f:
            f.write(caption)

        print(f"âœ… Reel {index+1} complete â†’ {video_path}")

    except Exception as e:
        print(f"âŒ Reel {index+1} failed: {e}")

    finally:
        for vf in voice_files:
            if os.path.exists(vf):
                os.remove(vf)

# ---------------- HASHTAG POOLS ----------------

HASHTAG_POOL = {
    "big": [
        "#discipline", "#motivation", "#mindset", "#fitness",
        "#success", "#selfimprovement", "#gym", "#hardwork",
    ],
    "medium": [
        "#selfmastery", "#selfcontrol", "#mentalstrength",
        "#consistency", "#dailymotivation", "#growthmindset",
        "#personaldevelopment", "#focus",
    ],
    "niche": [
        "#innerdiscipline", "#disciplinedmind", "#selfgrowth",
        "#dailyhabits", "#noexcuses", "#accountability",
        "#mindsetshift", "#innerwork",
    ],
}

# âœ… Challenge-specific hashtags â€” maximise group discovery
CHALLENGE_HASHTAGS = [
    "#30daychallenge", "#accountabilitygroup", "#disciplinechallenge",
    "#30days", "#jointhegroup", "#innerdisciplinechallenge",
    "#accountability", "#facebookgroup", "#selfimprovementchallenge",
    "#disciplinegroup"
]

def pick_hashtags(category=None):
    if category == "challenge":
        selected = ["#innerdiscipline"] + random.sample(CHALLENGE_HASHTAGS, 6) + random.sample(HASHTAG_POOL["big"], 3)
        random.shuffle(selected)
        return " ".join(selected[:10])

    brand = ["#innerdiscipline"]
    big = random.sample(HASHTAG_POOL["big"], 3)
    medium = random.sample(HASHTAG_POOL["medium"], 3)
    niche = random.sample([h for h in HASHTAG_POOL["niche"] if h != "#innerdiscipline"], 3)
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

# âœ… Challenge-specific caption openers â€” sell the group
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

# âœ… Challenge closers â€” direct link conversion
CHALLENGE_CLOSERS = [
    "Link in bio. Join the Inner Discipline Challenge today.",
    "Under $10/month. DM DISCIPLINE. No excuses.",
    "The group is open right now. DM DISCIPLINE.",
    "30 days starts when you DM DISCIPLINE.",
    "Join us. DM DISCIPLINE. Let's lock in together.",
    "Daily check-ins. Real accountability. DM DISCIPLINE.",
]

def build_caption(script, category=None):
    is_challenge = category == "challenge"

    opener = random.choice(CHALLENGE_OPENERS if is_challenge else CAPTION_OPENERS)
    closer = random.choice(CHALLENGE_CLOSERS if is_challenge else CAPTION_CLOSERS)
    hashtags = pick_hashtags(category)

    caption = "\n".join([
        opener,
        "",
        f'"{script[0]}"',
        "",
        script[1],
        "",
        script[2],
        "",
        "-",
        closer,
        "",
        hashtags,
    ])
    return caption

# ---------------- RUN ----------------

all_backgrounds = glob.glob("bg*.png") + glob.glob("bg*.jpg") + glob.glob("bg*.jpeg")

if not all_backgrounds:
    raise Exception("No background images found. Add bg1.png, bg2.jpg etc to this folder.")

if len(all_backgrounds) < REELS_PER_RUN:
    print(f"âš ï¸  Only {len(all_backgrounds)} images found for {REELS_PER_RUN} reels.")
    print(f"âš ï¸  Add more bg images to avoid repeats. Using what's available.")
    selected_backgrounds = random.sample(all_backgrounds, len(all_backgrounds))
    while len(selected_backgrounds) < REELS_PER_RUN:
        selected_backgrounds.append(random.choice(all_backgrounds))
else:
    selected_backgrounds = random.sample(all_backgrounds, REELS_PER_RUN)

print(f"ðŸŽ¬ Selected backgrounds for this run:")
for idx, bg in enumerate(selected_backgrounds):
    print(f"   Reel {idx+1} â†’ {bg}")

for i in range(REELS_PER_RUN):
    make_reel(i, selected_backgrounds[i])

# âœ… Save memory state after all reels complete
json.dump(used_hooks, open(HOOK_MEMORY_FILE, "w"))
json.dump(last_category, open(CATEGORY_MEMORY_FILE, "w"))
json.dump(set_step, open(SET_STEP_FILE, "w"))

print("ðŸ”¥ INNER DISCIPLINE SET-OF-4 COMPLETE")
