import os, json, random, asyncio, glob, textwrap
import numpy as np
from moviepy.editor import *
from moviepy.video.fx.all import resize
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ========= SETTINGS =========

REEL_BACKGROUNDS = glob.glob("bg*.mp4")
LONG_BACKGROUNDS = glob.glob("bg_long*.mp4")

MUSIC="music.mp3"
FONT_PATH="Anton-Regular.ttf"

W,H=1080,1920
LW,LH=1280,720

REELS_PER_RUN=5

VOICE="en-US-ChristopherNeural"
VOICE_RATE="-30%"
VOICE_PITCH="-10Hz"

# ========= LINES =========

HOOK=[
"You're not tired. You're undisciplined.",
"Comfort is ruining your future.",
"Your habits expose you.",
"No one is coming to save you."
]

AUTHORITY=[
"Comfort is expensive.",
"Control beats motivation.",
"Discipline decides outcomes."
]

RELATABLE=[
"Some days you don't feel like it.",
"You delay what matters."
]

CHALLENGE=[
"Day 7. Still disciplined?",
"Still here?"
]

# ========= VOICE =========

async def tts(text,path):
    await edge_tts.Communicate(
        text,
        voice=VOICE,
        rate=VOICE_RATE,
        pitch=VOICE_PITCH
    ).save(path)

def run_tts(text,path):
    asyncio.run(tts(text,path))

# ========= TEXT FRAME =========

def frame(text,w,h,size):

    margin=80
    wrap_width=15

    text="\n".join(textwrap.wrap(text,wrap_width))

    img=Image.new("RGBA",(w,h),(0,0,0,0))
    d=ImageDraw.Draw(img)
    font=ImageFont.truetype(FONT_PATH,size)

    box=d.multiline_textbbox((0,0),text,font=font,spacing=15)

    x=(w-(box[2]-box[0]))//2
    y=(h-(box[3]-box[1]))//2

    y=max(margin,y)

    d.multiline_text((x+4,y+4),text,font=font,fill=(0,0,0,180),align="center",spacing=15)
    d.multiline_text((x,y),text,font=font,fill="white",align="center",spacing=15)

    return np.array(img)

# ========= STORY PICK =========

def pick_story():
    return [
        random.choice(HOOK),
        random.choice(RELATABLE),
        random.choice(AUTHORITY),
        random.choice(CHALLENGE)
    ]

# ========= REEL =========

def make_reel(i):

    folder=f"outputs/{i}"
    os.makedirs(folder,exist_ok=True)

    bg=random.choice(REEL_BACKGROUNDS)
    base=VideoFileClip(bg).without_audio()
    base=base.resize(height=H)

    if base.w<W:
        base=base.resize(width=W)

    base=base.crop(x_center=base.w/2,y_center=base.h/2,width=W,height=H)

    lines=pick_story()

    clips=[]
    audios=[]
    t=0

    for idx,line in enumerate(lines):

        vp=f"{folder}/v{idx}.mp3"
        run_tts(line,vp)

        a=AudioFileClip(vp)

        extra=1.2 if "?" in line else 0.6
        dur=a.duration+extra

        img=frame(line,W,H,110)

        txt=(ImageClip(img)
             .set_start(t)
             .set_duration(dur)
             .fadein(0.3)
             .fadeout(0.3))

        clips.append(txt)
        audios.append(a.set_start(t+0.2))

        t+=dur

        os.remove(vp)

    final=CompositeVideoClip([base]+clips).subclip(0,t)

    voice=CompositeAudioClip(audios)

    if os.path.exists(MUSIC):
        music=AudioFileClip(MUSIC).audio_loop(duration=t).volumex(0.1)
        final=final.set_audio(CompositeAudioClip([music,voice]))
    else:
        final=final.set_audio(voice)

    final.write_videofile(f"{folder}/reel.mp4",fps=30)

    thumb=frame(lines[0],1080,1920,140)
    Image.fromarray(thumb).save(f"{folder}/thumb.jpg")

# ========= LONG VIDEO =========

def make_long():

    base=VideoFileClip(random.choice(LONG_BACKGROUNDS)).without_audio()
    base=base.resize(height=LH)

    if base.w<LW:
        base=base.resize(width=LW)

    base=base.crop(x_center=base.w/2,y_center=base.h/2,width=LW,height=LH)

    target=600
    used=set()

    clips=[]
    audios=[]
    t=0
    idx=0

    pool=HOOK+AUTHORITY+RELATABLE+CHALLENGE

    while t<target:

        line=random.choice(pool)

        if line in used:
            continue

        used.add(line)

        vp=f"outputs/long{idx}.mp3"
        run_tts(line,vp)

        a=AudioFileClip(vp)
        dur=a.duration+1.5

        img=frame(line,LW,LH,90)

        txt=(ImageClip(img)
             .set_start(t)
             .set_duration(dur)
             .fadein(0.5)
             .fadeout(0.5))

        clips.append(txt)
        audios.append(a.set_start(t+0.3))

        t+=dur
        idx+=1

        os.remove(vp)

    base=base.loop(duration=t)

    final=CompositeVideoClip([base]+clips)

    voice=CompositeAudioClip(audios)

    if os.path.exists(MUSIC):
        music=AudioFileClip(MUSIC).audio_loop(duration=t).volumex(0.05)
        final=final.set_audio(CompositeAudioClip([music,voice]))
    else:
        final=final.set_audio(voice)

    final.write_videofile("outputs/long.mp4",fps=30)

# ========= RUN =========

os.makedirs("outputs",exist_ok=True)

for i in range(REELS_PER_RUN):
    make_reel(i)

make_long()

print("🔥 DONE")
