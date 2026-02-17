# =========================
# V13 — RETENTION ENGINE
# =========================
# ✅ A/B/C content rotation (Authority / Relatable / Challenge)
# ✅ Micro-story reels (auto, 1–2 per week style)
# ✅ Different background per reel + random segment (no same clip all reel)
# ✅ Smart pacing (extra pause on questions / ellipses)
# ✅ Smart text fitting (no cutoff, auto wrap + auto font shrink)
# ✅ No temp-audio spam (deletes mp3s)
# ✅ Long video: avoids repeating lines (recent-history guard)
#
# Files expected in repo:
# - bg1.mp4 ... bg8.mp4 (or bg*.mp4)
# - bg_long1.mp4 ... bg_long5.mp4 (or bg_long*.mp4)
# - Anton-Regular.ttf
# - music.mp3 (optional)

import os, glob, random, asyncio, textwrap
from collections import deque
import numpy as np
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip,
    CompositeAudioClip, ImageClip
)
from moviepy.video.fx import all as vfx
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ================= SETTINGS =================

REEL_BACKGROUNDS = sorted(glob.glob("bg*.mp4"))
LONG_BACKGROUNDS = sorted(glob.glob("bg_long*.mp4"))

if not REEL_BACKGROUNDS:
    raise Exception("No reel backgrounds found (bg*.mp4)")
if not LONG_BACKGROUNDS:
    raise Exception("No long backgrounds found (bg_long*.mp4)")

MUSIC = "music.mp3"
FONT_PATH = "Anton-Regular.ttf"

W, H = 1080, 1920
LW, LH = 1280, 720

REELS_PER_RUN = 5
REEL_MIN_SEC = 8
REEL_MAX_SEC = 12

LONG_TARGET_SEC = 600  # 10 min

VOICE = "en-US-ChristopherNeural"
VOICE_RATE = "-30%"
VOICE_PITCH = "-20Hz"

HASHTAGS = [
    "#discipline","#selfcontrol","#focus",
    "#mindset","#innerdiscipline",
    "#consistency","#stoic","#growth"
]

# ================= COPY BANK (ALGORITHM OPTIMIZED) =================

# ===== HOOKS (SCROLL STOPPERS) =====
HOOK = [
"You’re not tired. You’re undisciplined.",
"Comfort is ruining your future.",
"Nobody is coming to save you.",
"Your habits are exposing you.",
"You don’t lack time. You lack control.",
"You’re choosing easy over growth.",
"Weak standards create hard lives.",
"You know better. You just don’t do better.",
"Your comfort zone is expensive.",
"You break promises to yourself.",
"You quit when it gets boring.",
"You delay what could change you.",
"You negotiate with weakness daily.",
"Results hate comfort.",
"Your future is watching your habits.",
"You want change without sacrifice.",
"Self-control is your real problem.",
"You avoid what would change you.",
"You’re addicted to comfort.",
"Discipline is your missing skill."
]

# ===== AUTHORITY (COLD TRUTHS) =====
AUTHORITY = [
"Discipline is a daily decision.",
"Control beats emotion.",
"Standards create results.",
"Consistency builds identity.",
"Structure creates freedom.",
"Repetition builds power.",
"Discipline compounds quietly.",
"Focus is trained.",
"Self-control is a skill.",
"Hard choices build easy lives.",
"Discipline outlasts motivation.",
"Routine builds strength.",
"Delayed gratification wins.",
"Discipline builds respect.",
"Control creates peace.",
"Standards change outcomes.",
"Effort builds confidence.",
"Action creates clarity.",
"Pain teaches control.",
"Standards decide your future."
]

# ===== RELATABLE (HUMAN TRUTHS) =====
RELATABLE = [
"Some days you don’t feel like it.",
"You get distracted easily.",
"You delay what matters.",
"You know what to do.",
"Your phone owns your attention.",
"You scroll instead of executing.",
"You wait for motivation.",
"You start but don’t finish.",
"You break your own rules.",
"You choose comfort at night.",
"You lose focus quickly.",
"You avoid boring work.",
"You want fast results.",
"You rely on feelings.",
"You skip the hard part.",
"You quit quietly.",
"You avoid discipline.",
"You want easy progress.",
"You protect bad habits.",
"You wait for the perfect time."
]

# ===== CHALLENGE (ENGAGEMENT TRIGGERS) =====
CHALLENGE = [
"Day 7... Still disciplined...?",
"Still here...?",
"Will you finish... what you start...?",
"Day 1... or Day 100...?",
"Can you stay consistent...?",
"Will you keep your word...?",
"Are you serious...?",
"Do you really want change...?",
"Still choosing comfort...?",
"Will you execute today...?"
]

# ===== CTA ROTATION (COMMENT DRIVERS) =====
CTA_ROTATE = [
"Comment DISCIPLINE.",
"Comment DISCIPLINE if you're serious.",
"Choose discipline.",
"Start today.",
"Do the hard thing.",
"Stay consistent.",
"Hold your standard.",
"Execute quietly.",
"Prove it to yourself.",
"Stay sharp."
]

# ===== MICRO-STORY ARCS (HIGH RETENTION) =====
STORY_ARCS = [
    [
        "You said you wanted change.",
        "Then you chose comfort again.",
        "Control is a decision.",
        "Not a mood.",
        "Day 7. Still disciplined?",
    ],
    [
        "You start strong.",
        "Then distractions win.",
        "Cut the noise.",
        "Keep the standard.",
        "Still here?",
    ],
    [
        "You want results.",
        "But protect bad habits.",
        "Remove the easy option.",
        "Discipline stays.",
        "Comment DISCIPLINE.",
    ],
    [
        "You know what to do.",
        "But you delay.",
        "Discipline is doing it anyway.",
        "Standards stay.",
        "Still here?",
    ],
]

ALL_LINES = HOOK + AUTHORITY + RELATABLE + CHALLENGE

# ================= HELPERS =================

def ensure_outputs():
    os.makedirs("outputs", exist_ok=True)

def pick_hashtags(n=4):
    return " ".join(random.sample(HASHTAGS, min(n, len(HASHTAGS))))

def punctuation_pause(text: str) -> float:
    t = text.strip()
    pause = 0.35
    if "?" in t:
        pause += 0.70
    if "..." in t or "…" in t:
        pause += 0.35
    if t.endswith("."):
        pause += 0.20
    return pause

def safe_remove(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

async def make_voice_async(text, path):
    tts = edge_tts.Communicate(text, voice=VOICE, rate=VOICE_RATE, pitch=VOICE_PITCH)
    await tts.save(path)

def run_tts(text, path):
    asyncio.run(make_voice_async(text, path))

def wrap_to_width(draw, text, font, max_width_px):
    words = text.split()
    lines = []
    line = ""
    for w in words:
        test = (line + " " + w).strip()
        bbox = draw.textbbox((0,0), test, font=font)
        if (bbox[2] - bbox[0]) <= max_width_px:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return "\n".join(lines)

def fit_text_image(text, w, h, font_path, max_size, min_size, margin_px, shadow=True):
    """
    Creates an RGBA overlay image with centered text that ALWAYS fits.
    """
    img = Image.new("RGBA", (w, h), (0,0,0,0))
    d = ImageDraw.Draw(img)

    max_w = w - 2*margin_px
    max_h = h - 2*margin_px

    for size in range(max_size, min_size - 1, -4):
        font = ImageFont.truetype(font_path, size)

        wrapped = wrap_to_width(d, text, font, max_w)
        bbox = d.multiline_textbbox((0,0), wrapped, font=font, spacing=int(size*0.20), align="center")
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        if tw <= max_w and th <= max_h:
            x = (w - tw)//2
            y = (h - th)//2

            spacing = int(size*0.20)

            if shadow:
                d.multiline_text((x+6, y+6), wrapped, font=font, fill=(0,0,0,170),
                                 align="center", spacing=spacing)
                d.multiline_text((x+2, y+2), wrapped, font=font, fill=(0,0,0,110),
                                 align="center", spacing=spacing)

            d.multiline_text((x, y), wrapped, font=font, fill=(255,255,255,255),
                             align="center", spacing=spacing)
            return np.array(img)

    # fallback: tiny
    font = ImageFont.truetype(font_path, min_size)
    wrapped = textwrap.fill(text, 14)
    bbox = d.multiline_textbbox((0,0), wrapped, font=font, spacing=int(min_size*0.20), align="center")
    x = (w - (bbox[2]-bbox[0]))//2
    y = (h - (bbox[3]-bbox[1]))//2
    d.multiline_text((x, y), wrapped, font=font, fill=(255,255,255,255), align="center")
    return np.array(img)

def make_thumbnail(text, path, w=1080, h=1920):
    # solid black background + smart-fit big text
    bg = Image.new("RGB", (w, h), (0,0,0))
    overlay = fit_text_image(text, w, h, FONT_PATH, max_size=190, min_size=80, margin_px=140, shadow=False)
    ov = Image.fromarray(overlay).convert("RGBA")
    out = Image.alpha_composite(bg.convert("RGBA"), ov).convert("RGB")
    out.save(path)

def pick_background_segment(video_path, target_sec, out_w, out_h):
    clip = VideoFileClip(video_path).without_audio()

    # if short, loop to target
    if clip.duration < target_sec + 0.5:
        clip = clip.fx(vfx.loop, duration=target_sec + 0.5)

    # pick random segment
    max_start = max(0.0, clip.duration - target_sec - 0.1)
    start = random.uniform(0.0, max_start) if max_start > 0 else 0.0
    base = clip.subclip(start, start + target_sec)

    # resize/crop to vertical
    base = base.resize(height=out_h)
    if base.w < out_w:
        base = base.resize(width=out_w)
    base = base.crop(x_center=base.w/2, y_center=base.h/2, width=out_w, height=out_h)

    # subtle motion
    base = base.fx(vfx.resize, lambda t: 1 + 0.010*t)
    return base

# ================= SCRIPT ENGINE (A/B/C + MICRO-STORY) =================

def build_reel_script(idx):
    """
    Returns list of lines for one reel (4–5 lines).
    Rotation:
      idx%3==1 -> Authority
      idx%3==2 -> Relatable
      idx%3==0 -> Challenge
    Micro-story: ~25% chance (feel like 1–2/week if posting daily)
    """
    # micro-story sometimes
    if random.random() < 0.25:
        arc = random.choice(STORY_ARCS)
        # keep final line as a question/cta
        return arc

    hook = random.choice(HOOK)

    mode = idx % 3
    if mode == 1:  # Authority
        body = [
            random.choice(AUTHORITY),
            random.choice(AUTHORITY),
        ]
        end = random.choice(CTA_ROTATE)
    elif mode == 2:  # Relatable
        body = [
            random.choice(RELATABLE),
            random.choice(AUTHORITY),
        ]
        end = random.choice(CTA_ROTATE)
    else:  # Challenge
        body = [
            random.choice(AUTHORITY),
            random.choice(CHALLENGE),
        ]
        end = random.choice(CTA_ROTATE)

    # 4 lines total (fast, loopable)
    return [hook] + body + [end]

# ================= REEL BUILDER =================

def make_reel(idx):
    folder = f"outputs/{idx:02d}"
    os.makedirs(folder, exist_ok=True)

    script = build_reel_script(idx)

    # total target reel length (keeps reels tight)
    target_len = random.uniform(REEL_MIN_SEC, REEL_MAX_SEC)

    # choose background per reel + random segment
    bg_path = random.choice(REEL_BACKGROUNDS)

    # we'll estimate timing from audio; if it exceeds target_len, we compress pauses
    # but we still keep it clean.
    audio_clips = []
    text_clips = []
    t = 0.0

    # create background after we know final t (or at least target_len)
    # first pass: build audio + overlays
    for i, line in enumerate(script):
        tmp = f"{folder}/tmp_{i}.mp3"
        run_tts(line, tmp)

        a = AudioFileClip(tmp)

# --- TIMING ENGINE (V12 RETENTION PACING) ---
if i == 0:
    dur = 2.8  # hook
elif i == len(script) - 1:
    dur = 3.0  # punch/question
else:
    dur = 2.4  # middle truths



                # text overlay (safe margins)
        overlay = fit_text_image(
            line, W, H, FONT_PATH,
            max_size=130,
            min_size=70,
            margin_px=140,
            shadow=True
        )

        txt = (ImageClip(overlay, ismask=False)
               .set_start(t)
               .set_duration(dur)
               .fadein(0.12)
               .fadeout(0.12)

        text_clips.append(txt)
        audio_clips.append(a.set_start(t + 0.15))

        t += dur
        safe_remove(tmp)

    # if too long, tighten by trimming end pauses a bit (simple + stable)
    final_len = max(6.0, min(t, 15.0))
    # make background segment slightly longer than final for safety
    base = pick_background_segment(bg_path, final_len + 0.2, W, H).subclip(0, final_len)

    voice_mix = CompositeAudioClip(audio_clips)

    if os.path.exists(MUSIC):
        music = AudioFileClip(MUSIC).audio_loop(duration=final_len).volumex(0.07)
        audio_mix = CompositeAudioClip([music, voice_mix])
    else:
        audio_mix = voice_mix

    final = CompositeVideoClip([base] + text_clips).subclip(0, final_len).set_audio(audio_mix)

    final.write_videofile(f"{folder}/reel.mp4", fps=30, audio_codec="aac")

    # thumbnail = hook line only (clean, clickable)
    make_thumbnail(script[0], f"{folder}/thumb.jpg")

    caption = f"{script[0]}\n\n{pick_hashtags(5)}"
    with open(f"{folder}/caption.txt", "w", encoding="utf-8") as f:
        f.write(caption)

# ================= LONG VIDEO BUILDER =================

def make_long_video():
    print("🔥 Generating LONG video (V13)...")

    bg_path = random.choice(LONG_BACKGROUNDS)

    # background looped to full duration
    base = VideoFileClip(bg_path).without_audio()
    base = base.fx(vfx.loop, duration=LONG_TARGET_SEC + 1.0)
    base = base.resize(height=LH)
    if base.w < LW:
        base = base.resize(width=LW)
    base = base.crop(x_center=base.w/2, y_center=base.h/2, width=LW, height=LH)
    base = base.subclip(0, LONG_TARGET_SEC)

    recent = deque(maxlen=35)
    t = 0.0
    idx = 0
    audio_clips = []
    text_clips = []
    chapters = []

    while t < LONG_TARGET_SEC:
        pool = [x for x in ALL_LINES if x not in recent]
        if not pool:
            recent.clear()
            pool = ALL_LINES[:]
        line = random.choice(pool)
        recent.append(line)

        tmp = f"outputs/longtmp_{idx}.mp3"
        run_tts(line, tmp)

        a = AudioFileClip(tmp)
        dur = max(6.0, a.duration + 1.2)

        # keep text inside safe box
        overlay = fit_text_image(line, LW, LH, FONT_PATH, max_size=92, min_size=48, margin_px=90, shadow=True)
        txt = (ImageClip(overlay, ismask=False)
               .set_start(t)
               .set_duration(dur)
               .fadein(0.6)
               .fadeout(0.6))

        text_clips.append(txt)
        audio_clips.append(a.set_start(t + 0.25))

        mm = int(t // 60)
        ss = int(t % 60)
        chapters.append(f"{mm}:{ss:02d} {line}")

        t += dur
        idx += 1
        safe_remove(tmp)

    voice_mix = CompositeAudioClip(audio_clips)

    if os.path.exists(MUSIC):
        music = AudioFileClip(MUSIC).audio_loop(duration=LONG_TARGET_SEC).volumex(0.045)
        audio_mix = CompositeAudioClip([music, voice_mix])
    else:
        audio_mix = voice_mix

    final = CompositeVideoClip([base] + text_clips).subclip(0, LONG_TARGET_SEC).set_audio(audio_mix)

    final.write_videofile("outputs/long_video.mp4", fps=30, audio_codec="aac")

    with open("outputs/long_description.txt", "w", encoding="utf-8") as f:
        f.write(
            "Build discipline, self-control and focus.\n\nCHAPTERS:\n" +
            "\n".join(chapters) +
            "\n\n#discipline #focus #mindset\n"
        )

    make_thumbnail("DISCIPLINE\nBUILDS YOU", "outputs/long_thumb.jpg", w=1280, h=720)

    print("✅ LONG VIDEO COMPLETE")

# ================= RUN =================

def main():
    ensure_outputs()

    for i in range(1, REELS_PER_RUN + 1):
        make_reel(i)

    make_long_video()

    print("🔥 V13 COMPLETE")

if __name__ == "__main__":
    main()
