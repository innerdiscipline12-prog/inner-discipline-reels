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

# ---------------- CONTENT BANK ----------------

HOOKS=[
"You're not tired. You're undisciplined.",
"Comfort is ruining your future.",
"You don't lack time. You lack control.",
"No one is coming to save you.",
"Your habits expose you.",
"Discipline is chosen.",
"Your future is built daily.",
"Comfort is the enemy.",
]

TRUTHS=[
"Control beats motivation.",
"Consistency builds identity.",
"Discipline decides outcomes.",
"Standards shape your life.",
"Small actions define you.",
"Routine builds power.",
]

QUESTIONS=[
"Still here?",
"Day 1 or Day 100?",
"Will you finish?",
"Are you serious?",
]

CTAS=[
"Comment discipline.",
"Type discipline.",
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
