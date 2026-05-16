import os
import glob
import random
import asyncio
import json
import shutil
import math
from datetime import datetime

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from moviepy.editor import VideoFileClip, VideoClip, CompositeAudioClip, AudioFileClip
from moviepy.audio.fx import all as afx
from moviepy.video.fx import all as vfx

import edge_tts

# ================================================================
# INNER DISCIPLINE â€” PROMO ENGINE v2
# Output: outputs/promo.mp4
# Uses background folders OR old bg1.mp4/bg2.mp4 files.
# ================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
TEMP_DIR = os.path.join(BASE_DIR, "temp_promo")
BG_ROOT = os.path.join(BASE_DIR, "backgrounds")

FONT_PATH = os.path.join(BASE_DIR, "Anton-Regular.ttf")
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")
MUSIC_PATH = os.path.join(BASE_DIR, "music.mp3")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

W, H = 1080, 1920
FPS = 30
VOICE = "en-US-GuyNeural"
VOLUME = "+0%"

ORANGE = (255, 126, 0)
WHITE = (255, 255, 255)
RED = (255, 42, 42)
BLACK = (0, 0, 0)

LOGO_OPACITY = 0.42
LOGO_SIZE = 112
LOGO_BOTTOM_MARGIN = 100
TEXT_MAX_WIDTH = 900
TEXT_CENTER_Y = 0.555
TEXT_HOOK_Y = 0.49
ZOOM_STRENGTH = 0.07
SHAKE_STRENGTH = 5
COVER_LOGO_SIZE = 92
COVER_DARKEN = 0.34
COVER_BLUR_RADIUS = 18

PROMO_VARIANTS = [
    {
        "name": "same_cycle",
        "cover": "SAME CYCLE",
        "title": "SAME CYCLE | INNER DISCIPLINE 30 DAY CHALLENGE",
        "mood_sequence": ["broken", "broken", "dangerous", "challenge", "rebuild", "challenge", "dangerous"],
        "lines": [
            ("You promised yourself this year would be different.", "-7%", "-36Hz", 3, "hook"),
            ("Then you repeated the same week again.", "-8%", "-38Hz", 3, "pain"),
            ("Same excuses. Same habits. Same quiet disappointment.", "-10%", "-40Hz", 2, "impact"),
            ("The Inner Discipline 30 Day Challenge was built to break that cycle.", "-18%", "-46Hz", 4, "offer"),
            ("Private Facebook group. Daily check-ins. Real accountability.", "-20%", "-48Hz", 3, "proof"),
            ("Not motivation. Pressure. Structure. Consequence.", "-12%", "-42Hz", 2, "impact"),
            ("Join today. Link in bio.", "-5%", "-36Hz", 2, "cta"),
        ],
    },
    {
        "name": "trying_alone",
        "cover": "STOP ALONE",
        "title": "STOP ALONE | INNER DISCIPLINE 30 DAY CHALLENGE",
        "mood_sequence": ["broken", "challenge", "broken", "challenge", "dangerous", "rebuild", "challenge"],
        "lines": [
            ("Doing it alone sounds strong until you keep failing alone.", "-7%", "-36Hz", 3, "hook"),
            ("You start. You drift. Nobody notices. So you quit quietly.", "-9%", "-39Hz", 3, "pain"),
            ("That is not discipline. That is isolation with excuses.", "-10%", "-41Hz", 3, "impact"),
            ("The 30 Day Challenge gives you a room where your excuses get exposed.", "-18%", "-46Hz", 4, "offer"),
            ("Daily check-ins. Accountability. Men rebuilding their standard.", "-20%", "-48Hz", 3, "proof"),
            ("If you are tired of restarting, stop hiding.", "-10%", "-40Hz", 3, "impact"),
            ("The group is open. Link in bio.", "-5%", "-36Hz", 2, "cta"),
        ],
    },
    {
        "name": "no_consequence",
        "cover": "NO CONSEQUENCE",
        "title": "NO CONSEQUENCE | INNER DISCIPLINE 30 DAY CHALLENGE",
        "mood_sequence": ["broken", "broken", "challenge", "dangerous", "challenge", "rebuild", "challenge"],
        "lines": [
            ("The reason you keep quitting is simple.", "-7%", "-36Hz", 3, "hook"),
            ("There is no consequence when you disappear.", "-8%", "-39Hz", 3, "pain"),
            ("No one checks in. No one calls it out. No one raises the standard.", "-10%", "-41Hz", 3, "mirror"),
            ("That changes inside the Inner Discipline 30 Day Challenge.", "-18%", "-46Hz", 4, "offer"),
            ("Every day you check in. Every day the standard stays visible.", "-20%", "-48Hz", 4, "proof"),
            ("Thirty days. Under twenty dollars. No more private promises.", "-10%", "-40Hz", 3, "impact"),
            ("Join now. Link in bio.", "-5%", "-36Hz", 2, "cta"),
        ],
    },
    {
        "name": "another_year",
        "cover": "ANOTHER YEAR",
        "title": "ANOTHER YEAR | INNER DISCIPLINE 30 DAY CHALLENGE",
        "mood_sequence": ["broken", "broken", "morning", "challenge", "rebuild", "dangerous", "challenge"],
        "lines": [
            ("Another year will disappear if you keep moving like this.", "-7%", "-36Hz", 3, "hook"),
            ("You already know the pattern.", "-8%", "-39Hz", 3, "mirror"),
            ("High emotion. Strong start. Slow drift. Quiet failure.", "-10%", "-41Hz", 2, "impact"),
            ("The 30 Day Challenge gives you structure before motivation dies.", "-18%", "-46Hz", 4, "offer"),
            ("Daily check-ins keep the standard in front of you.", "-20%", "-48Hz", 4, "proof"),
            ("You do not need another promise. You need accountability.", "-10%", "-40Hz", 3, "impact"),
            ("Join today. Link in bio.", "-5%", "-36Hz", 2, "cta"),
        ],
    },
]

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
    pool = []
    if mood:
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

def choose_background(mood=None):
    pool = get_background_pool(mood)
    print("BASE DIR:", BASE_DIR)
    print("BG ROOT:", BG_ROOT)
    print("REQUESTED MOOD:", mood)
    print("BACKGROUND POOL FOUND:", pool)
    if not pool:
        raise Exception("No background videos found. Add videos to backgrounds folders OR bg1.mp4 in repo root.")
    return random.choice(pool)

async def tts_async(text, filename, rate, pitch):
    communicate = edge_tts.Communicate(text, VOICE, rate=rate, pitch=pitch, volume=VOLUME)
    await communicate.save(filename)

def generate_voice(text, filename, rate, pitch):
    asyncio.run(tts_async(text, filename, rate, pitch))

HOT_WORDS = {"WEAK", "WEAKNESS", "LOSING", "FAIL", "FAILED", "KILL", "EXCUSE", "EXCUSES", "DISCIPLINE", "STANDARD", "STANDARDS", "RESET", "LOCKED", "ALONE", "QUIT", "QUITTING", "DRIFT", "DRIFTING", "WASTING", "MAN", "MORNING", "SNOOZE", "NOW", "TODAY", "DONE", "DAY", "NO", "STOP", "HARD", "COMFORT", "CONTROL", "ACCOUNTABILITY", "CONSEQUENCE", "FIRST", "BATTLE", "FUTURE", "PRIVATE", "PROMISES", "PRESSURE", "STRUCTURE", "CYCLE", "YEAR", "JOIN", "LINK"}
DANGER_WORDS = {"WEAK", "WEAKNESS", "FAIL", "FAILED", "QUIT", "QUITTING", "EXCUSE", "EXCUSES", "WASTING", "DRIFT", "DRIFTING", "COMFORT", "BETRAYAL", "DISAPPEAR"}

def clean_text(text):
    for old, new in {"\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2026": "..."}.items():
        text = text.replace(old, new)
    return text.strip()

def load_font(size):
    if not os.path.exists(FONT_PATH):
        raise FileNotFoundError("Missing Anton-Regular.ttf in repo root.")
    return ImageFont.truetype(FONT_PATH, size)

def wrap_words(draw, text, font, max_width):
    words = clean_text(text).upper().split()
    lines, current = [], []
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
            draw.text((x + 4, y + 5), word, font=font, fill=(0, 0, 0), stroke_width=8, stroke_fill=(0, 0, 0))
            draw.text((x, y), word, font=font, fill=color, stroke_width=7, stroke_fill=BLACK)
            x += int(widths[wi] + space)

def make_text_frame(text, level="normal"):
    img = Image.new("RGB", (W, H), BLACK)
    draw = ImageDraw.Draw(img)
    wc = len(clean_text(text).split())
    if level == "cover":
        font_size, y = (170 if wc <= 2 else 132), H * 0.53
    elif level == "hook":
        font_size, y = (132 if wc <= 5 else 108), H * 0.49
    elif wc <= 2:
        font_size, y = 140, H * TEXT_CENTER_Y
    elif wc <= 5:
        font_size, y = 110, H * TEXT_CENTER_Y
    else:
        font_size, y = 88, H * TEXT_CENTER_Y
    font = load_font(font_size)
    lines = wrap_words(draw, text, font, TEXT_MAX_WIDTH)
    draw_multiline(draw, lines, font, y, style="cover" if level == "cover" else "normal")
    return np.array(img)

def make_logo_frame():
    if not os.path.exists(LOGO_PATH):
        return None
    logo = Image.open(LOGO_PATH).convert("RGBA")
    aspect = logo.height / max(1, logo.width)
    new_w, new_h = LOGO_SIZE, int(LOGO_SIZE * aspect)
    logo = logo.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    canvas.paste(logo, ((W - new_w) // 2, H - new_h - LOGO_BOTTOM_MARGIN), logo)
    bg = Image.new("RGB", (W, H), BLACK)
    bg.paste(canvas.convert("RGB"), (0, 0), canvas.split()[3])
    return np.array(bg)

def prepare_background(video_path, duration):
    bg = VideoFileClip(video_path)
    ratio, target = bg.w / bg.h, W / H
    bg = bg.resize(height=H) if ratio > target else bg.resize(width=W)
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
    f = (f - 128) * 1.13 + 128
    f += 4
    return np.clip(f, 0, 255).astype(np.uint8)

def composite_rgb(base, overlay, opacity=1.0, offset_y=0, scale=1.0):
    if scale != 1.0:
        pil = Image.fromarray(overlay)
        nw, nh = max(1, int(W * scale)), max(1, int(H * scale))
        pil = pil.resize((nw, nh), Image.LANCZOS)
        canvas = Image.new("RGB", (W, H), BLACK)
        canvas.paste(pil, ((W - nw) // 2, (H - nh) // 2 + int(offset_y)))
        overlay = np.array(canvas)
    elif offset_y != 0:
        overlay = np.roll(overlay, int(offset_y), axis=0)
    mask = np.any(overlay > 18, axis=2)
    if not np.any(mask):
        return base
    b, o = base.astype(np.float32), overlay.astype(np.float32)
    b[mask] = b[mask] * (1 - opacity) + o[mask] * opacity
    return np.clip(b, 0, 255).astype(np.uint8)

def subtitle_animation_values(t, start, end, event_type):
    local = t - start
    fd = 0.08 if event_type in ["cover", "impact", "cta"] else 0.11
    if local < fd:
        alpha = local / fd
    elif end - t < fd:
        alpha = (end - t) / fd
    else:
        alpha = 1.0
    alpha = float(np.clip(alpha, 0.0, 1.0))
    scale = 1.0 + (0.065 * (1 - local / 0.12)) if local < 0.12 else 1.0
    offset_y = math.sin(local * 34) * 5 if event_type in ["impact", "cta"] and local < 0.18 else 0
    return alpha, offset_y, scale

def split_chunks(text, chunk_size):
    words = clean_text(text).split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        c = " ".join(words[i:i + chunk_size]).strip()
        if c:
            chunks.append(c)
    return chunks or [text]

def make_text_events(variant, voice_data, total_duration):
    events = [{"frame": make_text_frame(variant["cover"], "cover"), "start": 0.01, "end": min(0.90, total_duration), "type": "cover"}]
    for i, item in enumerate(voice_data):
        chunks = split_chunks(item["text"], item["chunk_size"])
        chunk_dur = item["duration"] / max(1, len(chunks))
        for j, chunk in enumerate(chunks):
            start = item["start"] + j * chunk_dur
            end = item["start"] + (j + 1) * chunk_dur + 0.10
            if start >= total_duration:
                continue
            level = "hook" if i == 0 and j == 0 else "normal"
            raw = chunk.upper()
            event_type = "impact" if any(w in raw for w in ["WEAK", "FAIL", "NO ", "STOP", "QUIT", "CYCLE", "YEAR", "ALONE"]) else item["kind"]
            events.append({"frame": make_text_frame(chunk, level), "start": start, "end": min(end, total_duration), "type": event_type})
    if total_duration > 18:
        t = min(total_duration - 4.0, max(9.0, total_duration * 0.50))
        flash = random.choice(["NO EXCUSES", "STOP HIDING", "JOIN NOW", "BREAK THE CYCLE"])
        events.append({"frame": make_text_frame(flash, "cover"), "start": t, "end": min(t + 0.46, total_duration), "type": "impact"})
    return events

def make_cinematic_cover_background(bg_path):
    try:
        clip = VideoFileClip(bg_path)
        t = min(max(0.15, clip.duration * 0.28), max(0, clip.duration - 0.10))
        frame = clip.get_frame(t).astype(np.uint8)
        clip.close()
        img = Image.fromarray(frame).convert("RGB")
        ratio, target = img.width / img.height, W / H
        if ratio > target:
            img = img.resize((int(H * ratio), H), Image.LANCZOS)
        else:
            img = img.resize((W, int(W / ratio)), Image.LANCZOS)
        left, top = (img.width - W) // 2, (img.height - H) // 2
        img = img.crop((left, top, left + W, top + H))
        small = img.resize((max(1, W // COVER_BLUR_RADIUS), max(1, H // COVER_BLUR_RADIUS)), Image.BILINEAR)
        img = small.resize((W, H), Image.BICUBIC)
        arr = np.array(img).astype(np.float32)
        arr = (arr - 128) * 1.12 + 128
        arr *= COVER_DARKEN
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGB")
    except Exception as e:
        print(f"Cover background failed, using black fallback: {e}")
        return Image.new("RGB", (W, H), BLACK)

def draw_cover_text_on_image(img, cover_text):
    img_rgba = img.convert("RGBA")
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(band).rectangle((0, int(H * 0.34), W, int(H * 0.70)), fill=(0, 0, 0, 92))
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
        x, y = int((W - line_w) / 2), y0 + li * (font.size + line_gap)
        for wi, word in enumerate(words):
            raw = word.strip(".,?!:;\"'").upper()
            color = RED if raw in DANGER_WORDS else (ORANGE if wi == 0 else WHITE)
            draw.text((x + 5, y + 6), word, font=font, fill=(0, 0, 0, 210))
            draw.text((x, y), word, font=font, fill=color + (255,), stroke_width=8, stroke_fill=(0, 0, 0, 255))
            x += int(widths[wi] + space)
    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH).convert("RGBA")
        aspect = logo.height / max(1, logo.width)
        new_w, new_h = COVER_LOGO_SIZE, int(COVER_LOGO_SIZE * aspect)
        logo = logo.resize((new_w, new_h), Image.LANCZOS)
        logo.putalpha(150)
        img_rgba.paste(logo, ((W - new_w) // 2, H - new_h - LOGO_BOTTOM_MARGIN), logo)
    return img_rgba.convert("RGB")

def export_cover(variant, bg_path):
    out = os.path.join(OUTPUT_DIR, "promo_cover.png")
    img = make_cinematic_cover_background(bg_path)
    img = draw_cover_text_on_image(img, variant["cover"])
    img.save(out, quality=95)
    return out

def build_caption(variant):
    return "\n".join(["You do not need another promise.", "You need pressure, structure, and accountability.", "", "The Inner Discipline 30 Day Challenge is open.", "Private Facebook group. Daily check-ins. Real accountability.", "", "Join through the link in bio.", "", "#discipline #30daychallenge #accountability #innerdiscipline #selfimprovement #mindset #noexcuses #consistency #growthmindset #hardwork"])

def write_metadata(variant):
    with open(os.path.join(OUTPUT_DIR, "promo_title.txt"), "w", encoding="utf-8") as f:
        f.write(variant["title"])
    with open(os.path.join(OUTPUT_DIR, "promo_caption.txt"), "w", encoding="utf-8") as f:
        f.write(build_caption(variant))
    with open(os.path.join(OUTPUT_DIR, "promo_script.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join([line[0] for line in variant["lines"]]))

def build_promo():
    print("\nINNER DISCIPLINE â€” PROMO ENGINE v2")
    print("=" * 64)
    voice_files, audio_clips, bg_clip = [], [], None
    try:
        variant = random.choice(PROMO_VARIANTS)
        print("VARIANT:", variant["name"])
        print("COVER:", variant["cover"])
        primary_mood = variant["mood_sequence"][0] if variant.get("mood_sequence") else "challenge"
        bg_path = choose_background(primary_mood)
        print("SELECTED BACKGROUND:", bg_path)
        voice_data = []
        cursor = 0.55
        print("Generating voice...")
        for i, (text, rate, pitch, chunk_size, kind) in enumerate(variant["lines"]):
            vf = os.path.join(TEMP_DIR, f"promo_voice_{i}_{random.randint(1000,9999)}.mp3")
            voice_files.append(vf)
            generate_voice(text, vf, rate, pitch)
            audio_probe = AudioFileClip(vf)
            dur = float(audio_probe.duration)
            audio_probe.close()
            voice_data.append({"file": vf, "text": text, "duration": dur, "start": cursor, "chunk_size": chunk_size, "kind": kind})
            gap = 0.22 if kind in ["hook", "impact", "cta"] else 0.30
            cursor += dur + (gap if i < len(variant["lines"]) - 1 else 0.35)
        total_duration = float(cursor)
        print(f"Duration: {total_duration:.2f}s")
        for item in voice_data:
            audio_clips.append(AudioFileClip(item["file"]).set_start(item["start"]))
        text_events = make_text_events(variant, voice_data, total_duration)
        logo_frame = make_logo_frame()
        vignette = make_vignette()
        bg_clip = prepare_background(bg_path, total_duration)
        def make_frame(t):
            frame = bg_clip.get_frame(t).astype(np.uint8)
            zoom = 1.0 + ZOOM_STRENGTH * (t / max(total_duration, 0.001))
            if zoom > 1.001:
                new_w, new_h = int(W / zoom), int(H / zoom)
                x1, y1 = (W - new_w) // 2, (H - new_h) // 2
                pil = Image.fromarray(frame)
                pil = pil.crop((x1, y1, x1 + new_w, y1 + new_h)).resize((W, H), Image.LANCZOS)
                frame = np.array(pil)
            if t < 0.85:
                dx, dy = int(math.sin(t * 95) * SHAKE_STRENGTH), int(math.cos(t * 85) * SHAKE_STRENGTH)
                frame = np.roll(frame, shift=(dy, dx), axis=(0, 1))
            frame = apply_contrast(frame)
            f = frame.astype(np.float32)
            f[:, :, 0] *= vignette
            f[:, :, 1] *= vignette
            f[:, :, 2] *= vignette
            frame = np.clip(f, 0, 255).astype(np.uint8)
            band = frame.astype(np.float32)
            band[int(H * 0.34):int(H * 0.72), :, :] *= 0.72
            frame = np.clip(band, 0, 255).astype(np.uint8)
            for ev in text_events:
                if ev["start"] <= t < ev["end"]:
                    alpha, offset_y, scale = subtitle_animation_values(t, ev["start"], ev["end"], ev["type"])
                    frame = composite_rgb(frame, ev["frame"], opacity=alpha, offset_y=offset_y, scale=scale)
            if logo_frame is not None:
                frame = composite_rgb(frame, logo_frame, opacity=LOGO_OPACITY)
            return frame
        final_video = VideoClip(make_frame, duration=total_duration).set_fps(FPS).fadein(0.25).fadeout(0.35)
        final_voice = CompositeAudioClip(audio_clips)
        if os.path.exists(MUSIC_PATH):
            music = AudioFileClip(MUSIC_PATH)
            music = afx.audio_loop(music, duration=total_duration)
            music = music.audio_fadein(0.55).audio_fadeout(0.75).volumex(0.13).set_start(0)
            final_audio = CompositeAudioClip([music, final_voice.volumex(1.18)])
        else:
            final_audio = final_voice
        final = final_video.set_audio(final_audio)
        out = os.path.join(OUTPUT_DIR, "promo.mp4")
        print("Rendering:", out)
        final.write_videofile(out, fps=FPS, codec="libx264", audio_codec="aac", threads=4, preset="fast", logger=None)
        cover = export_cover(variant, bg_path)
        write_metadata(variant)
        print("\nOUTPUTS")
        print("Video:", out)
        print("Cover:", cover)
        print("Title:", os.path.join(OUTPUT_DIR, "promo_title.txt"))
        print("Caption:", os.path.join(OUTPUT_DIR, "promo_caption.txt"))
        print("Script:", os.path.join(OUTPUT_DIR, "promo_script.txt"))
        try:
            final.close(); final_video.close(); final_audio.close()
        except Exception:
            pass
        if bg_clip:
            bg_clip.close()
    except Exception as e:
        import traceback
        print("FAILED:", e)
        traceback.print_exc()
        raise
    finally:
        for clip in audio_clips:
            try: clip.close()
            except Exception: pass
        if bg_clip:
            try: bg_clip.close()
            except Exception: pass
        for vf in voice_files:
            if os.path.exists(vf):
                try: os.remove(vf)
                except Exception: pass
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
        os.makedirs(TEMP_DIR, exist_ok=True)

if __name__ == "__main__":
    build_promo()
