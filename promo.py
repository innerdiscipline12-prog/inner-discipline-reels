import os, asyncio, subprocess
import numpy as np
from moviepy.editor import (
    VideoFileClip, VideoClip, CompositeAudioClip, AudioFileClip
)
from moviepy.audio.fx import all as afx
from moviepy.video.fx import all as vfx
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ================================================================
# INNER DISCIPLINE â€” PROMO VIDEO GENERATOR
# Output: outputs/promo.mp4
# Spec:   Vertical 1080x1920, 30FPS, 30-60 seconds
#         Sells the 30 Day Challenge Facebook group subscription
# ================================================================

W, H   = 1080, 1920
FPS    = 30

FONT_PATH          = "Anton-Regular.ttf"
LOGO_PATH          = "logo.png"
LOGO_OPACITY       = 0.60
LOGO_SIZE          = 150
LOGO_BOTTOM_MARGIN = 120

VOICE  = "en-US-GuyNeural"
VOLUME = "+0%"

os.makedirs("outputs", exist_ok=True)

# ================================================================
# PROMO SCRIPT
# 6 lines â€” direct hard sell.
# Pacing: confrontation for impact lines, build for the offer.
# ================================================================

PROMO_LINES = [
    # (text, rate, pitch, chunk_size)
    # Lines 1-2: Hit the pain hard
    (
        "You have been trying to build discipline alone. It is not working.",
        "-15%", "-42Hz", 3
    ),
    (
        "Every time you restart there is nobody watching. No consequence. No standard.",
        "-18%", "-42Hz", 3
    ),
    # Lines 3-4: Present the solution â€” slower, weighted
    (
        "That is exactly what the Inner Discipline 30 Day Challenge fixes.",
        "-28%", "-50Hz", 4
    ),
    (
        "A private Facebook group. Daily check-ins. Real accountability. Men who will not let you quit.",
        "-28%", "-50Hz", 4
    ),
    # Lines 5-6: Close hard â€” fast and direct
    (
        "30 days. Under 20 dollars. One decision.",
        "-12%", "-42Hz", 2
    ),
    (
        "The group is open right now. Link in bio. Join today.",
        "-12%", "-42Hz", 2
    ),
]

# ================================================================
# TTS
# ================================================================

async def tts_async(text, filename, rate, pitch):
    communicate = edge_tts.Communicate(text, VOICE, rate=rate, pitch=pitch, volume=VOLUME)
    await communicate.save(filename)

def generate_voice(text, filename, rate, pitch):
    asyncio.run(tts_async(text, filename, rate, pitch))

# ================================================================
# TEXT RENDERER â€” orange first word, white rest, black stroke
# ================================================================

def make_text_frame(text):
    text = text.replace("\u2014", "-").replace("\u2013", "-")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.upper()

    img  = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_size = 92
    font      = ImageFont.truetype(FONT_PATH, font_size)
    max_width = W - 240

    words, lines, current = text.split(), [], ""
    for word in words:
        test = (current + " " + word).strip()
        if draw.textlength(test, font=font) <= max_width:
            current = test
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)

    total_h          = len(lines) * (font_size + 22)
    y                = int(H * 0.62) - total_h // 2
    first_word_drawn = False
    ORANGE           = (255, 140, 0)
    WHITE            = (255, 255, 255)

    for line in lines:
        lw   = draw.textlength(line, font=font)
        x    = (W - lw) // 2
        for idx, word in enumerate(line.split()):
            ww = draw.textlength(word, font=font)
            sw = draw.textlength(" ", font=font) if idx < len(line.split()) - 1 else 0
            color            = ORANGE if not first_word_drawn else WHITE
            first_word_drawn = True
            draw.text((x, y), word, font=font, fill=color, stroke_width=5, stroke_fill=(0, 0, 0))
            x += ww + sw
        y += font_size + 22

    return np.array(img)

# ================================================================
# LOGO RENDERER
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
    bg     = Image.new("RGB", (W, H), (0, 0, 0))
    bg.paste(canvas.convert("RGB"), (0, 0), canvas.split()[3])
    return np.array(bg)

# ================================================================
# VIGNETTE
# ================================================================

def make_vignette_mask():
    mask = np.ones((H, W), dtype=np.float32)
    vh   = int(H * 0.55)
    for row in range(vh):
        mask[row, :] = (row / vh) ** 1.6
    return mask

# ================================================================
# CHUNK SPLITTER
# ================================================================

def split_into_chunks(text, chunk_size):
    words  = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        c = " ".join(words[i:i + chunk_size]).strip()
        if c:
            chunks.append(c)
    return chunks or [text]

# ================================================================
# MAIN BUILD
# ================================================================

def build_promo():
    print("\nðŸŽ¬ INNER DISCIPLINE â€” PROMO VIDEO")
    print("=" * 48)

    voice_files = []

    try:
        # ---- Step 1: Generate voice files and measure durations ----
        print("ðŸŽ™ï¸  Generating voice lines...")
        voice_data = []   # (file, duration, text, rate, pitch, chunk_size)

        for i, (text, rate, pitch, chunk_size) in enumerate(PROMO_LINES):
            vf = f"promo_v{i}.mp3"
            voice_files.append(vf)
            generate_voice(text, vf, rate, pitch)
            audio    = AudioFileClip(vf)
            duration = audio.duration
            audio.close()
            voice_data.append((vf, duration, text, rate, pitch, chunk_size))
            print(f"   Line {i+1}: {duration:.2f}s â€” {text[:50]}...")

        # ---- Step 2: Build exact timeline ----
        FADE_DUR  = 0.15
        LINE_GAP  = 0.30   # slightly longer gap for promo pacing
        lead      = 0.8    # longer lead-in for promo

        line_starts = []
        cursor      = lead
        for i, (vf, dur, *_) in enumerate(voice_data):
            line_starts.append(cursor)
            cursor += dur + (LINE_GAP if i < len(voice_data) - 1 else FADE_DUR)

        total_duration = float(cursor)
        print(f"\nâ±ï¸  Total duration: {total_duration:.2f}s")

        if total_duration > 60:
            print("âš ï¸  Over 60s â€” consider shortening lines.")
        elif total_duration < 25:
            print("âš ï¸  Under 25s â€” consider adding lines.")
        else:
            print("âœ… Duration is within 30-60s target.")

        # ---- Step 3: Build text events and audio clips ----
        text_events = []   # (rendered_frame, t_start, t_end)
        audio_clips = []

        for i, (vf, voice_dur, text, rate, pitch, chunk_size) in enumerate(voice_data):
            line_t = line_starts[i]
            audio  = AudioFileClip(vf)
            audio_clips.append(audio.set_start(line_t))

            chunks         = split_into_chunks(text, chunk_size)
            num_chunks     = len(chunks)
            chunk_dur      = voice_dur / num_chunks

            for j, chunk in enumerate(chunks):
                t_start = line_t + j * chunk_dur
                if j == num_chunks - 1:
                    t_end = line_t + voice_dur + FADE_DUR
                else:
                    t_end = t_start + chunk_dur + FADE_DUR * 0.5
                t_end = min(t_end, total_duration)
                text_events.append((make_text_frame(chunk), t_start, t_end))

        print(f"ðŸ–¼ï¸  Text events: {len(text_events)}")

        # ---- Step 4: Load background video ----
        import glob
        bg_files = glob.glob("bg*.mp4") + glob.glob("bg*.mov") + glob.glob("bg*.MP4")
        if not bg_files:
            raise Exception("No background video found. Add bg1.mp4 to this folder.")

        bg_path  = bg_files[0]
        print(f"ðŸŽ¬  Background: {bg_path}")

        bg_clip      = VideoFileClip(bg_path)
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
        if bg_clip.duration < total_duration:
            bg_clip = vfx.loop(bg_clip, duration=total_duration)
        bg_clip = bg_clip.subclip(0, total_duration)
        bg_clip = bg_clip.fx(vfx.colorx, 0.88)

        # ---- Step 5: Precompute vignette + logo ----
        vignette_mask = make_vignette_mask()
        logo_frame    = make_logo_frame()

        # ---- Step 6: make_frame â€” numpy compositing ----
        def make_frame(t):
            bg = bg_clip.get_frame(t).astype(np.float32)
            bg[:, :, 0] *= vignette_mask
            bg[:, :, 1] *= vignette_mask
            bg[:, :, 2] *= vignette_mask
            bg = np.clip(bg, 0, 255).astype(np.uint8)

            for text_frame, t_start, t_end in text_events:
                if t_start <= t < t_end:
                    if t - t_start < FADE_DUR:
                        alpha = (t - t_start) / FADE_DUR
                    elif t_end - t < FADE_DUR:
                        alpha = (t_end - t) / FADE_DUR
                    else:
                        alpha = 1.0
                    alpha  = float(np.clip(alpha, 0.0, 1.0))
                    mask   = np.any(text_frame > 20, axis=2)
                    bg_f   = bg.astype(np.float32)
                    txt_f  = text_frame.astype(np.float32)
                    bg_f[mask] = bg_f[mask] * (1.0 - alpha) + txt_f[mask] * alpha
                    bg     = np.clip(bg_f, 0, 255).astype(np.uint8)

            if logo_frame is not None:
                logo_mask = np.any(logo_frame > 10, axis=2)
                bg_f      = bg.astype(np.float32)
                logo_f    = logo_frame.astype(np.float32)
                bg_f[logo_mask] = (
                    bg_f[logo_mask] * (1.0 - LOGO_OPACITY) +
                    logo_f[logo_mask] * LOGO_OPACITY
                )
                bg = np.clip(bg_f, 0, 255).astype(np.uint8)

            return bg

        # ---- Step 7: Render ----
        final_video = VideoClip(make_frame, duration=total_duration).set_fps(FPS)
        final_video = final_video.fadein(0.4).fadeout(0.4)

        final_voice = CompositeAudioClip(audio_clips)

        if os.path.exists("music.mp3"):
            music = AudioFileClip("music.mp3")
            if music.duration < total_duration:
                music = afx.audio_loop(music, duration=total_duration)
            music       = music.subclip(0, total_duration)
            music       = music.audio_fadein(0.8).audio_fadeout(0.8).volumex(0.12)
            final_audio = CompositeAudioClip([music, final_voice.volumex(1.1)])
        else:
            final_audio = final_voice

        final      = final_video.set_audio(final_audio)
        output     = "outputs/promo.mp4"

        print(f"\nðŸ“¼  Rendering â†’ {output}")
        final.write_videofile(
            output, fps=FPS,
            codec="libx264", audio_codec="aac",
            threads=4, preset="fast",
            logger=None
        )

        # Hard trim to 60s max just in case
        trimmed = "outputs/promo_trim.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-i", output,
            "-t", "60",
            "-c", "copy", trimmed
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(trimmed):
            os.replace(trimmed, output)

        bg_clip.close()

        print(f"\n{'=' * 48}")
        print(f"âœ… PROMO COMPLETE â†’ {output}")
        print(f"   Duration: {total_duration:.1f}s | Resolution: {W}x{H} | FPS: {FPS}")
        print(f"{'=' * 48}")

    except Exception as e:
        import traceback
        print(f"âŒ Failed: {e}")
        traceback.print_exc()

    finally:
        for vf in voice_files:
            if os.path.exists(vf):
                os.remove(vf)


# ================================================================
# RUN
# ================================================================

build_promo()
