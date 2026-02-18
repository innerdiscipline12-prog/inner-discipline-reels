import os, random, glob, asyncio
import numpy as np
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ---------------- SETTINGS ----------------

W, H = 1080, 1920
FPS = 30

VOICE = "en-US-ChristopherNeural"

RATE = "-15%"
PITCH = "-10Hz"
VOLUME = "+0%"

os.makedirs("outputs", exist_ok=True)

# ================= V4 VIRAL BANK =================

HOOKS=[
"You’re not tired. You’re avoiding effort.",
"Your comfort is lying to you.",
"Nobody ruined your life. You did.",
"You know the answer. You avoid it.",
"Your future is watching you waste time.",
"Comfort is killing your potential.",
"You don’t need motivation. You need rules.",
"You’re not busy. You’re distracted.",
"Your excuses are well practiced.",
"Most people choose easy. Daily.",
"Your habits expose your priorities.",
"You want change without sacrifice.",
"You fear discipline more than failure.",
"Your comfort zone owns you.",
"You delay what could change your life.",
"You already know what to fix.",
"You waste energy on avoidance.",
"You want results without structure.",
"You’re addicted to easy dopamine.",
"You’re negotiating with weakness.",
]

TRUTHS=[
"Discipline is a decision.",
"Control creates freedom.",
"Structure beats emotion.",
"Action builds clarity.",
"Habits shape identity.",
"Consistency builds power.",
"Standards define outcomes.",
"Focus is trained.",
"Effort reveals truth.",
"Repetition builds strength.",
"Execution builds confidence.",
"Order removes chaos.",
"Discipline compounds.",
"Control is a skill.",
"Momentum is earned.",
"Structure protects focus.",
"Daily effort wins.",
"Routine creates results.",
"Self-control builds respect.",
"Action ends doubt.",
]

QUESTIONS=[
"Still choosing easy?",
"Still delaying?",
"Still distracted?",
"Still comfortable?",
"Still avoiding effort?",
"Still restarting?",
"Still negotiating?",
"Still scrolling?",
"Still unfocused?",
"Still inconsistent?",
"Still waiting?",
"Still escaping?",
"Still blaming mood?",
"Still weak on standards?",
"Still here?",
]

CTAS=[
"Comment discipline.",
"Type discipline.",
"Only disciplined comment.",
"Discipline or regret. Choose.",
"Prove discipline. Comment.",
"Show commitment. Comment discipline.",
"Serious? Comment discipline.",
"Earn it. Comment discipline.",
"Discipline starts now. Comment.",
"Standards begin here. Comment discipline.",
]

# ---------------- TEXT RENDER ----------------

def make_text(text):
    img = Image.new("RGBA",(W,H),(0,0,0,0))
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype("Anton-Regular.ttf", 90)

    words=text.split()
    lines=[]
    cur=""

    for w in words:
        test=cur+" "+w
        if draw.textlength(test,font=font)<900:
            cur=test
        else:
            lines.append(cur)
            cur=w
    lines.append(cur)

    y=H//2 - 100*len(lines)//2

    for line in lines:
        tw=draw.textlength(line,font=font)
        x=(W-tw)//2

        draw.text(
            (x,y),
            line,
            font=font,
            fill="white",
            stroke_width=4,
            stroke_fill="black"
        )
        y+=110

    return np.array(img)

# ---------------- TTS ----------------

async def tts(text,file):
    com=edge_tts.Communicate(
        text,
        VOICE,
        rate=RATE,
        pitch=PITCH,
        volume=VOLUME
    )
    await com.save(file)

def make_voice(text,file):
    asyncio.run(tts(text,file))

# ---------------- BUILD REEL ----------------

def build_script(with_cta=True):
    script=[
        random.choice(HOOKS),
        random.choice(TRUTHS),
    ]
    if with_cta:
        script.append(random.choice(CTAS))
    else:
        script.append(random.choice(QUESTIONS))
    return script

def make_reel(idx,with_cta):
    script=build_script(with_cta)

    bg=random.choice(glob.glob("bg*.mp4"))
    base=VideoFileClip(bg).resize(height=H).crop(x_center=540,y_center=960,width=W,height=H)

    clips=[]
    audios=[]
    t=0

    for i,line in enumerate(script):
        mp3=f"tmp_{idx}_{i}.mp3"
        make_voice(line,mp3)

        a=AudioFileClip(mp3)
        dur=max(2.5,a.duration+0.4)

        img=make_text(line)

        txt=(ImageClip(img)
             .set_start(t)
             .set_duration(dur)
             .fadein(0.2)
             .fadeout(0.2))

        clips.append(txt)
        audios.append(a.set_start(t))

        t+=dur

    video=CompositeVideoClip([base]+clips).set_duration(t)
    audio=CompositeAudioClip(audios)

    final=video.set_audio(audio)
    final.write_videofile(
        f"outputs/reel_{idx}.mp4",
        fps=FPS,
        codec="libx264",
        audio_codec="aac"
    )

# ---------------- RUN ----------------

for i in range(5):
    make_reel(i,with_cta=(i<2))

print("DONE")
