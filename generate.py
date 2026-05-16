import os
import random
import glob
import asyncio
import json
import shutil
import subprocess
from datetime import datetime
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    CompositeAudioClip,
    VideoClip,
)
from moviepy.audio.fx import all as afx
from moviepy.video.fx import all as vfx

import edge_tts


# ================================================================
# INNER DISCIPLINE â€” RETENTION ENGINE v2
# Purpose:
#   Generate Reels/Facebook Reels that are built for:
#   1. violent first-second hooks
#   2. faster pacing
#   3. emotional escalation
#   4. less repetitive visuals
#   5. stronger comment/follow conversion
#
# Required files in same folder:
#   - bg1.mp4 / bg2.mp4 / bg3.mp4 ... OR .mov files
#   - Anton-Regular.ttf
#   - logo.png
#   - optional: music.mp3
#
# Run:
#   python generate.py
# ================================================================


# ================================================================
# SETTINGS
# ================================================================

W, H = 1080, 1920
FPS = 30

REEL_SECONDS = 18.0          # 15â€“22 sec is stronger than forcing exactly 15
LONG_VIDEO_SECS = 300

FONT_PATH = "Anton-Regular.ttf"
LOGO_PATH = "logo.png"
MUSIC_PATH = "music.mp3"

VOICE = "en-US-GuyNeural"
VOLUME = "+0%"

OUTPUT_DIR = "outputs"
TEMP_DIR = "temp_segments"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


# ================================================================
# VISUAL SETTINGS
# ================================================================

ORANGE = (255, 126, 0)
WHITE = (255, 255, 255)
RED = (255, 45, 45)
BLACK = (0, 0, 0)

LOGO_OPACITY = 0.42
LOGO_SIZE = 115
LOGO_BOTTOM_MARGIN = 105

# stronger than old code: bigger readable text and higher placement
TEXT_Y_REEL = 0.56
TEXT_Y_HOOK = 0.49
TEXT_MAX_WIDTH = 890

# prevent visual sameness
ZOOM_STRENGTH = 0.055
SHAKE_STRENGTH = 4


# ================================================================
# PACING MODES
# ================================================================

PACING_MODES = {
    # faster than old generator; old pacing was too cinematic/slow
    "attack": {"rate": "-6%", "pitch": "-35Hz", "chunk_size": 2, "music_volume": 0.16},
    "story": {"rate": "-12%", "pitch": "-40Hz", "chunk_size": 3, "music_volume": 0.12},
    "cold": {"rate": "-16%", "pitch": "-45Hz", "chunk_size": 3, "music_volume": 0.10},
}


# ================================================================
# MEMORY FILES
# ================================================================

USED_LINES_FILE = "used_lines_v2.json"
SET_STEP_FILE = "set_step_v2.json"

used_lines = json.load(open(USED_LINES_FILE, "r", encoding="utf-8")) if os.path.exists(USED_LINES_FILE) else []
set_step = json.load(open(SET_STEP_FILE, "r", encoding="utf-8")) if os.path.exists(SET_STEP_FILE) else 0
if not isinstance(set_step, int):
    set_step = 0


# ================================================================
# CONTENT SYSTEM
# Each reel is no longer random quote + truth + question.
# It is structured as:
#   HOOK -> PROBLEM -> MIRROR -> CONSEQUENCE -> COMMAND/CTA
# This creates emotional escalation.
# ================================================================

CONTENT_BANK = {
    "wasted_potential": {
        "covers": [
            "YOU DRIFT",
            "STILL WEAK",
            "WASTED TIME",
            "NO STANDARD",
            "YOU LOST",
        ],
        "hooks": [
            "You are not behind because life is hard.",
            "You are losing to the version of you that keeps negotiating.",
            "You keep calling it a phase. It is becoming your identity.",
            "You are not stuck. You are undisciplined and comfortable.",
            "Every day you delay, the weaker version of you gets stronger.",
        ],
        "problem": [
            "You wake up with plans and go to sleep with excuses.",
            "You know what to do, but you keep choosing the easiest option.",
            "You lowered your standards so many times they no longer feel low.",
            "You are not failing from lack of information. You are failing from lack of execution.",
            "Your life is not falling apart loudly. It is drifting quietly.",
        ],
        "mirror": [
            "And the worst part is, you can feel it.",
            "Nobody has to tell you. You already know.",
            "That little shame you feel is not random. It is your standard trying to come back.",
            "The mirror is not lying. Your habits are showing.",
            "Deep down, you know this version of you is not enough.",
        ],
        "consequence": [
            "If you keep moving like this, five years will disappear and nothing will change.",
            "Comfort is charging you interest every single day.",
            "The future you want will not survive the habits you protect.",
            "Every weak decision becomes a vote for the man you hate becoming.",
            "You are not just wasting time. You are training weakness.",
        ],
        "cta": [
            "Today, kill one excuse. Comment DISCIPLINE.",
            "No speech. One action today. Comment LOCKED.",
            "Restart now. Not Monday. Comment DISCIPLINE.",
            "If this hit too close, comment RESET.",
            "Follow if you are done restarting.",
        ],
    },

    "morning_discipline": {
        "covers": [
            "OWN MORNING",
            "WAKE UP",
            "FIRST BATTLE",
            "NO SNOOZE",
            "WIN EARLY",
        ],
        "hooks": [
            "Your day is already losing before you touch the floor.",
            "The first battle is not the gym. It is the bed.",
            "You keep losing the morning and expecting to win the life.",
            "The snooze button is teaching you to betray yourself.",
            "Your morning routine is exposing your real standard.",
        ],
        "problem": [
            "You wake up late, rush everything, and call the day stressful.",
            "You give your best energy to comfort, then give leftovers to your goals.",
            "You start the day reactive, then wonder why your mind is weak.",
            "The phone gets your first attention. Your future gets whatever is left.",
            "You do not need a better life first. You need a better first hour.",
        ],
        "mirror": [
            "That is not a small habit. That is identity training.",
            "Every morning tells the truth before your mouth can lie.",
            "The man you become is built before the world sees you.",
            "Nobody claps for the morning win. That is why it matters.",
            "Discipline is decided when nobody is watching.",
        ],
        "consequence": [
            "Win the first hour and the rest of the day has to respect you.",
            "Lose the morning long enough and weakness starts feeling normal.",
            "The life you want is being blocked by the routine you defend.",
            "You cannot build a hard life with soft mornings.",
            "Your future is not waiting for motivation. It is waiting for structure.",
        ],
        "cta": [
            "Tomorrow, no snooze. Comment 5AM.",
            "Win the first hour. Comment LOCKED.",
            "Set the alarm now. Comment DISCIPLINE.",
            "Your reset starts tomorrow morning. Comment RESET.",
            "Follow for the 30 day discipline build.",
        ],
    },

    "masculine_standard": {
        "covers": [
            "BE THE MAN",
            "RAISE STANDARD",
            "NO EXCUSES",
            "LEAD YOURSELF",
            "REAL MAN",
        ],
        "hooks": [
            "A man who cannot lead himself should stop talking about leading anything else.",
            "You want respect, but your habits do not respect you.",
            "Masculinity is not volume. It is self-control under pressure.",
            "Nobody is coming to make you a man.",
            "Your household does not need your potential. It needs your presence.",
        ],
        "problem": [
            "You keep demanding from life what you have not earned through consistency.",
            "You say you want to lead, but you cannot even keep a promise to yourself.",
            "You confuse anger with strength and comfort with peace.",
            "You are physically present but mentally absent where it matters.",
            "You want the title of a man without the private discipline of one.",
        ],
        "mirror": [
            "Your actions are your real reputation.",
            "The people watching you are learning from what you tolerate.",
            "Your word to yourself is either building you or destroying you.",
            "A standard is not what you post. It is what you refuse to break.",
            "Every man is measured by what he does when it is inconvenient.",
        ],
        "consequence": [
            "If you cannot govern yourself, the world will govern you.",
            "A weak standard does not stay private. It leaks into everything.",
            "The man you become will either protect your future or ruin it.",
            "Discipline is the price of being trusted.",
            "You do not rise by talking harder. You rise by living cleaner.",
        ],
        "cta": [
            "Raise one standard today. Comment STANDARD.",
            "Lead yourself first. Comment DISCIPLINE.",
            "No more fake standards. Comment LOCKED.",
            "Follow if you are rebuilding the man.",
            "Thirty days. New standard. Link in bio.",
        ],
    },

    "accountability_challenge": {
        "covers": [
            "STOP ALONE",
            "30 DAYS",
            "JOIN NOW",
            "REAL ACCOUNTABILITY",
            "NO HIDING",
        ],
        "hooks": [
            "You keep restarting because nobody sees you quit.",
            "Doing it alone is not strength if it keeps failing.",
            "You do not need more motivation. You need accountability.",
            "Private promises are easy to break.",
            "The reason you keep quitting is simple. No consequence.",
        ],
        "problem": [
            "You start strong, disappear quietly, then promise yourself next week will be different.",
            "You keep relying on willpower, and willpower keeps running out.",
            "Your environment accepts your excuses, so your standard never rises.",
            "Nobody checks in. Nobody notices. Nobody challenges the drift.",
            "Alone, you negotiate. Around disciplined people, you execute.",
        ],
        "mirror": [
            "That is why structure matters.",
            "That is why the right room changes behavior.",
            "People show up differently when the standard is visible.",
            "Accountability exposes the excuses you hide from yourself.",
            "You do not need hype. You need pressure that makes you better.",
        ],
        "consequence": [
            "Thirty days of daily check-ins can do what three years of private promises could not.",
            "The group gives you one thing comfort never will: consequence.",
            "You either build with people who push you or stay alone with excuses.",
            "The standard rises when the room refuses to let you disappear.",
            "Your next level needs structure, not another motivational video.",
        ],
        "cta": [
            "Join the Inner Discipline Challenge. Link in bio.",
            "Thirty days. Daily check-ins. Link in bio.",
            "Stop doing it alone. Link in bio.",
            "The group is open. Link in bio.",
            "Under twenty dollars. Real accountability. Link in bio.",
        ],
    },
}

CATEGORY_ORDER = list(CONTENT_BANK.keys())


# ================================================================
# UTILITIES
# ================================================================

def clean_text(text):
    replacements = {
        "\u2014": "-",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.strip()


def get_all_videos():
    files = []
    for pattern in ["bg*.mp4", "bg*.mov", "bg*.MP4", "bg*.MOV"]:
        files.extend(glob.glob(pattern))
    return files


def save_memory():
    json.dump(used_lines, open(USED_LINES_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(set_step, open(SET_STEP_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def pick_unique(pool):
    available = [x for x in pool if x not in used_lines]
    if not available:
        available = pool[:]
    choice = random.choice(available)
    used_lines.append(choice)
    return choice


def next_category():
    global set_step
    category = CATEGORY_ORDER[set_step % len(CATEGORY_ORDER)]
    set_step += 1
    return category


@dataclass
class ReelScript:
    category: str
    cover: str
    pacing: str
    lines: list


def build_reel_script():
    category = next_category()
    bank = CONTENT_BANK[category]

    pacing = random.choices(
        ["attack", "story", "cold"],
        weights=[0.56, 0.30, 0.14],
        k=1
    )[0]

    lines = [
        pick_unique(bank["hooks"]),
        pick_unique(bank["problem"]),
        pick_unique(bank["mirror"]),
        pick_unique(bank["consequence"]),
        pick_unique(bank["cta"]),
    ]

    cover = random.choice(bank["covers"])
    return ReelScript(category=category, cover=cover, pacing=pacing, lines=lines)


def split_into_chunks(text, chunk_size):
    words = clean_text(text).split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks if chunks else [text]


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
    mode = PACING_MODES[pacing]
    asyncio.run(tts_async(text, filename, mode["rate"], mode["pitch"]))


# ================================================================
# TEXT RENDERING
# ================================================================

def load_font(size):
    if not os.path.exists(FONT_PATH):
        raise FileNotFoundError(f"Missing font file: {FONT_PATH}")
    return ImageFont.truetype(FONT_PATH, size)


def draw_centered_multiline(draw, lines, font, y, colors, stroke=6):
    line_gap = int(font.size * 0.22)
    total_height = len(lines) * font.size + (len(lines) - 1) * line_gap
    start_y = int(y - total_height / 2)

    for line_index, line_words in enumerate(lines):
        widths = [draw.textlength(word, font=font) for word in line_words]
        space = draw.textlength(" ", font=font)
        line_width = sum(widths) + space * max(0, len(line_words) - 1)
        x = int((W - line_width) / 2)
        yy = start_y + line_index * (font.size + line_gap)

        for i, word in enumerate(line_words):
            color = colors(word, line_index, i)
            draw.text(
                (x, yy),
                word,
                font=font,
                fill=color,
                stroke_width=stroke,
                stroke_fill=BLACK,
            )
            x += int(widths[i] + space)


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


def make_text_frame(text, mode="normal"):
    img = Image.new("RGB", (W, H), BLACK)
    draw = ImageDraw.Draw(img)

    word_count = len(clean_text(text).split())
    if mode == "hook":
        font_size = 142 if word_count <= 3 else 118
        y = H * TEXT_Y_HOOK
    elif word_count <= 2:
        font_size = 142
        y = H * TEXT_Y_REEL
    elif word_count <= 5:
        font_size = 112
        y = H * TEXT_Y_REEL
    else:
        font_size = 92
        y = H * TEXT_Y_REEL

    font = load_font(font_size)
    lines = wrap_words(draw, text, font, TEXT_MAX_WIDTH)

    hot_words = {
        "WEAK", "LOSING", "FAIL", "FAILED", "KILL", "EXCUSE", "EXCUSES",
        "DISCIPLINE", "STANDARD", "STANDARDS", "RESET", "LOCKED",
        "ALONE", "QUIT", "QUITTING", "DRIFT", "DRIFTING", "WASTING",
        "MAN", "MORNING", "SNOOZE", "NOW", "TODAY",
    }

    first_drawn = {"done": False}

    def color_fn(word, line_index, word_index):
        raw = word.replace(".", "").replace(",", "").replace("?", "").replace("!", "")
        if mode == "hook":
            return ORANGE if not first_drawn["done"] else WHITE
        if raw in hot_words:
            return ORANGE
        if not first_drawn["done"]:
            first_drawn["done"] = True
            return ORANGE
        return WHITE

    draw_centered_multiline(draw, lines, font, y, color_fn, stroke=7)
    return np.array(img)


def make_cover_frame(cover_text):
    img = Image.new("RGB", (W, H), BLACK)
    draw = ImageDraw.Draw(img)

    # subtle center glow block, text only; real bg is composited behind it
    font = load_font(168 if len(cover_text.split()) <= 2 else 132)
    lines = wrap_words(draw, cover_text, font, 940)

    def color_fn(word, line_index, word_index):
        return ORANGE if word_index == 0 else WHITE

    draw_centered_multiline(draw, lines, font, H * 0.54, color_fn, stroke=8)
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
# BACKGROUND LOOK
# ================================================================

def prepare_background(video_path, duration):
    bg = VideoFileClip(video_path)

    clip_ratio = bg.w / bg.h
    target_ratio = W / H

    if clip_ratio > target_ratio:
        bg = bg.resize(height=H)
    else:
        bg = bg.resize(width=W)

    bg = bg.crop(
        x_center=bg.w / 2,
        y_center=bg.h / 2,
        width=W,
        height=H,
    )

    if bg.duration < duration:
        bg = vfx.loop(bg, duration=duration)

    # random start point prevents every output feeling identical
    max_start = max(0, bg.duration - duration - 0.1)
    start = random.uniform(0, max_start) if max_start > 1 else 0
    bg = bg.subclip(start, start + duration)

    return bg


def make_vignette_mask():
    y = np.linspace(0, 1, H).reshape(H, 1)
    x = np.linspace(-1, 1, W).reshape(1, W)
    radial = 1 - 0.36 * np.clip((x ** 2 + (y - 0.45) ** 2), 0, 1)
    top = np.ones((H, W), dtype=np.float32)
    top[: int(H * 0.42), :] *= np.linspace(0.47, 1, int(H * 0.42)).reshape(-1, 1)
    mask = radial * top
    return np.clip(mask, 0.34, 1.0).astype(np.float32)


def apply_contrast(frame):
    f = frame.astype(np.float32)
    f = (f - 128) * 1.12 + 128
    f = np.clip(f + 4, 0, 255)
    return f.astype(np.uint8)


def composite_rgb(base, overlay, opacity=1.0):
    mask = np.any(overlay > 18, axis=2)
    if not np.any(mask):
        return base
    b = base.astype(np.float32)
    o = overlay.astype(np.float32)
    b[mask] = b[mask] * (1.0 - opacity) + o[mask] * opacity
    return np.clip(b, 0, 255).astype(np.uint8)


# ================================================================
# VIDEO BUILDER
# ================================================================

def build_video(script: ReelScript, video_path, output_path):
    voice_files = []
    audio_clips = []

    try:
        print(f"  Category: {script.category.upper()} | Pacing: {script.pacing}")
        print(f"  Cover: {script.cover}")
        print("  Generating voice...")

        voice_data = []
        for i, line in enumerate(script.lines):
            vf = os.path.join(TEMP_DIR, f"v2_{datetime.now().strftime('%H%M%S')}_{i}.mp3")
            voice_files.append(vf)
            generate_voice(line, vf, script.pacing)
            audio = AudioFileClip(vf)
            voice_data.append({
                "file": vf,
                "duration": float(audio.duration),
                "line": line,
                "chunk_size": PACING_MODES[script.pacing]["chunk_size"],
            })
            audio.close()

        # timeline
        lead = 0.30
        line_gap = 0.16 if script.pacing == "attack" else 0.22
        fade = 0.11

        cursor = lead
        line_starts = []
        for i, item in enumerate(voice_data):
            line_starts.append(cursor)
            cursor += item["duration"] + (line_gap if i < len(voice_data) - 1 else 0.20)

        duration = min(cursor, REEL_SECONDS)

        # build text events
        text_events = []

        # cover blast in first 0.85s
        cover_frame = make_cover_frame(script.cover)
        text_events.append({
            "frame": cover_frame,
            "start": 0.02,
            "end": min(0.88, duration),
            "type": "cover",
        })

        for i, item in enumerate(voice_data):
            start = line_starts[i]
            if start >= duration:
                continue

            audio = AudioFileClip(item["file"]).set_start(start)
            audio_clips.append(audio)

            chunks = split_into_chunks(item["line"], item["chunk_size"])
            chunk_duration = item["duration"] / max(1, len(chunks))

            for j, chunk in enumerate(chunks):
                t_start = start + j * chunk_duration
                t_end = start + (j + 1) * chunk_duration + fade
                if t_start >= duration:
                    continue

                frame = make_text_frame(chunk, mode="hook" if i == 0 and j == 0 else "normal")
                text_events.append({
                    "frame": frame,
                    "start": t_start,
                    "end": min(t_end, duration),
                    "type": "text",
                })

        print(f"  Duration: {duration:.2f}s | Events: {len(text_events)}")

        logo_frame = make_logo_frame()
        bg_clip = prepare_background(video_path, duration)
        vignette = make_vignette_mask()

        def make_frame(t):
            frame = bg_clip.get_frame(t).astype(np.uint8)

            # slow zoom punch
            zoom = 1.0 + ZOOM_STRENGTH * (t / max(duration, 0.01))
            if zoom > 1.001:
                new_w = int(W / zoom)
                new_h = int(H / zoom)
                x1 = (W - new_w) // 2
                y1 = (H - new_h) // 2
                pil = Image.fromarray(frame)
                pil = pil.crop((x1, y1, x1 + new_w, y1 + new_h)).resize((W, H), Image.LANCZOS)
                frame = np.array(pil)

            # tiny hook shake first second
            if t < 0.82:
                dx = int(np.sin(t * 90) * SHAKE_STRENGTH)
                dy = int(np.cos(t * 75) * SHAKE_STRENGTH)
                frame = np.roll(frame, shift=(dy, dx), axis=(0, 1))

            frame = apply_contrast(frame)

            f = frame.astype(np.float32)
            f[:, :, 0] *= vignette
            f[:, :, 1] *= vignette
            f[:, :, 2] *= vignette
            frame = np.clip(f, 0, 255).astype(np.uint8)

            # dark text readability band
            band = frame.astype(np.float32)
            y1 = int(H * 0.36)
            y2 = int(H * 0.72)
            band[y1:y2, :, :] *= 0.78
            frame = np.clip(band, 0, 255).astype(np.uint8)

            for event in text_events:
                if event["start"] <= t < event["end"]:
                    event_duration = event["end"] - event["start"]
                    local = t - event["start"]

                    # sharper pop for cover; softer for normal text
                    fd = 0.08 if event["type"] == "cover" else fade

                    if local < fd:
                        alpha = local / fd
                    elif event["end"] - t < fd:
                        alpha = (event["end"] - t) / fd
                    else:
                        alpha = 1.0

                    alpha = float(np.clip(alpha, 0.0, 1.0))
                    frame = composite_rgb(frame, event["frame"], opacity=alpha)

            if logo_frame is not None:
                frame = composite_rgb(frame, logo_frame, opacity=LOGO_OPACITY)

            return frame

        final_video = VideoClip(make_frame, duration=duration).set_fps(FPS)
        final_voice = CompositeAudioClip(audio_clips)

        if os.path.exists(MUSIC_PATH):
            music = AudioFileClip(MUSIC_PATH)
            music = afx.audio_loop(music, duration=duration)
            music = music.audio_fadein(0.45).audio_fadeout(0.45)
            music = music.volumex(PACING_MODES[script.pacing]["music_volume"]).set_start(0)
            final_audio = CompositeAudioClip([music, final_voice.volumex(1.20)])
        else:
            final_audio = final_voice

        final = final_video.set_audio(final_audio).fadeout(0.22)

        print(f"  Rendering: {output_path}")
        final.write_videofile(
            output_path,
            fps=FPS,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            preset="fast",
            logger=None,
        )

        bg_clip.close()
        final_video.close()
        final.close()

        print(f"  Done: {output_path}")
        return True

    except Exception as e:
        import traceback
        print(f"  FAILED: {e}")
        traceback.print_exc()
        return False

    finally:
        for clip in audio_clips:
            try:
                clip.close()
            except Exception:
                pass

        for vf in voice_files:
            if os.path.exists(vf):
                try:
                    os.remove(vf)
                except Exception:
                    pass


# ================================================================
# CAPTION + TITLE SYSTEM
# ================================================================

def build_caption(script: ReelScript):
    opener_by_category = {
        "wasted_potential": "Most men do not fail loudly. They drift quietly.",
        "morning_discipline": "Win the morning before the world gets access to you.",
        "masculine_standard": "Your standard is not what you say. It is what you repeat.",
        "accountability_challenge": "Discipline gets easier when the room refuses your excuses.",
    }

    hashtags_by_category = {
        "wasted_potential": "#discipline #selfimprovement #mindset #noexcuses #selfmastery #growthmindset #mentalstrength #innerdiscipline #accountability #hardwork",
        "morning_discipline": "#morningroutine #discipline #5amclub #selfimprovement #mindset #consistency #focus #innerdiscipline #noexcuses #growthmindset",
        "masculine_standard": "#masculinity #discipline #selfmastery #menwithstandards #mindset #noexcuses #leadership #innerdiscipline #growthmindset #accountability",
        "accountability_challenge": "#30daychallenge #accountability #discipline #innerdisciplinechallenge #selfimprovement #mindset #facebookgroup #consistency #noexcuses #hardwork",
    }

    return "\n".join([
        opener_by_category.get(script.category, "Read this twice."),
        "",
        f'"{script.lines[0]}"',
        "",
        script.lines[2],
        "",
        "-",
        script.lines[-1],
        "",
        hashtags_by_category.get(script.category, hashtags_by_category["wasted_potential"]),
    ])


def write_metadata(script: ReelScript, video_path):
    base = os.path.splitext(video_path)[0]
    title = f"{script.cover} | INNER DISCIPLINE"
    caption = build_caption(script)

    with open(f"{base}_title.txt", "w", encoding="utf-8") as f:
        f.write(title)

    with open(f"{base}_caption.txt", "w", encoding="utf-8") as f:
        f.write(caption)

    with open(f"{base}_script.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(script.lines))


# ================================================================
# OPTIONAL: CREATE THUMBNAIL IMAGE FROM SAME COVER TEXT
# ================================================================

def export_cover_image(script: ReelScript, video_path):
    base = os.path.splitext(video_path)[0]
    out = f"{base}_cover.png"

    # standalone black cover for manual upload fallback
    img = Image.new("RGB", (W, H), BLACK)
    draw = ImageDraw.Draw(img)

    font = load_font(170 if len(script.cover.split()) <= 2 else 132)
    lines = wrap_words(draw, script.cover, font, 940)

    def color_fn(word, line_index, word_index):
        return ORANGE if word_index == 0 else WHITE

    draw_centered_multiline(draw, lines, font, H * 0.54, color_fn, stroke=8)

    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH).convert("RGBA")
        aspect = logo.height / max(1, logo.width)
        new_w = LOGO_SIZE
        new_h = int(LOGO_SIZE * aspect)
        logo = logo.resize((new_w, new_h), Image.LANCZOS)
        img_rgba = img.convert("RGBA")
        img_rgba.paste(logo, ((W - new_w) // 2, H - new_h - LOGO_BOTTOM_MARGIN), logo)
        img = img_rgba.convert("RGB")

    img.save(out, quality=95)
    return out


# ================================================================
# RUN
# ================================================================

def main():
    print("\nINNER DISCIPLINE â€” RETENTION ENGINE v2")
    print("=" * 58)

    all_videos = get_all_videos()
    if not all_videos:
        raise Exception("No background videos found. Add bg1.mp4, bg2.mp4, etc.")

    script = build_reel_script()
    video_path = random.choice(all_videos)

    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(OUTPUT_DIR, f"reel_v2_{script.category}_{date_str}.mp4")

    print(f"Background: {video_path}")
    ok = build_video(script, video_path, out_path)

    if ok:
        write_metadata(script, out_path)
        cover_path = export_cover_image(script, out_path)
        print(f"Title: {os.path.splitext(out_path)[0]}_title.txt")
        print(f"Caption: {os.path.splitext(out_path)[0]}_caption.txt")
        print(f"Script: {os.path.splitext(out_path)[0]}_script.txt")
        print(f"Cover: {cover_path}")

    save_memory()

    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)

    print("=" * 58)
    print("COMPLETE")


if __name__ == "__main__":
    main()
