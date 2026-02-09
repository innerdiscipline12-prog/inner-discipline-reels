import random, json, os, asyncio
import numpy as np
from moviepy.editor import *
from moviepy.video.fx.all import resize
from PIL import Image, ImageDraw, ImageFont
import edge_tts

VIDEO="bg.mp4"
MUSIC="music.mp3"
FONT_PATH="Anton-Regular.ttf"

W,H=1080,1920

SAFE_TOP=350
SAFE_BOTTOM=450
SAFE_H=H-SAFE_TOP-SAFE_BOTTOM

LINES=[
"YOU WAIT FOR MOTIVATION",
"COMFORT IS THE ENEMY",
"NO ONE IS COMING",
"DISCIPLINE DECIDES",
"CONTROL YOURSELF",
"PROVE IT QUIETLY",
"STOP NEGOTIATING",
"DO THE HARD THING"
]

# ---------- MEMORY ----------

MEM="memory.json"
used=json.load(open(MEM)) if os.path.exists(MEM) else []

pool=[l for l in LINES if l not in used]
if len(pool)<4:
    used=[]
    pool=LINES.copy()

chosen=random.sample(pool,4)
json.dump(used+chosen,open(MEM,"w"))

# ---------- VOICE ----------
import edge_tts
import asyncio

async def make_voice():

    # EXACT SAME lines as video
    text = ""

    for line in chosen:
        text += line + "... "

    communicate = edge_tts.Communicate(
        text,
        voice="en-US-ChristopherNeural",
        rate="-35%",
        pitch="-20Hz"
    )

    await communicate.save("voice.mp3")

asyncio.run(make_voice())





# ---------- TEXT ----------

def frame(text):
    img=Image.new("RGBA",(W,H),(0,0,0,0))
    d=ImageDraw.Draw(img)
    font=ImageFont.truetype(FONT_PATH,120)

    max_w=int(W*0.75)

    words=text.split()
    lines=[]; cur=""

    for w in words:
        test=(cur+" "+w).strip()
        box=d.textbbox((0,0),test,font=font)
        if box[2]-box[0]<=max_w:
            cur=test
        else:
            lines.append(cur); cur=w
    lines.append(cur)

    if len(lines)>2:
        lines=[lines[0]," ".join(lines[1:])]

    hs=[]
    for l in lines:
        b=d.textbbox((0,0),l,font=font)
        hs.append(b[3]-b[1])

    total=sum(hs)+25*(len(lines)-1)
    y=SAFE_TOP+(SAFE_H-total)//2+40

    for i,l in enumerate(lines):
        b=d.textbbox((0,0),l,font=font)
        x=(W-(b[2]-b[0]))//2

        d.text((x+4,y+4),l,font=font,fill=(0,0,0,200))
        d.text((x,y),l,font=font,fill="white")

        y+=hs[i]+25

    return np.array(img)

# ---------- VIDEO ----------

def make():

    base=VideoFileClip(VIDEO).without_audio()
    base=base.fx(resize,lambda t:1+0.015*t)
    base=base.resize(height=H)

    if base.w<W:
        base=base.resize(width=W)

    base=base.crop(x_center=base.w/2,y_center=base.h/2,width=W,height=H)

    clips=[]; t=0

    for line in chosen:
        img=frame(line)
        c=(ImageClip(img)
           .set_start(t)
           .set_duration(3.5)
           .fadein(0.3)
           .fadeout(0.3))
        clips.append(c)
        t+=3.5

    final=CompositeVideoClip([base]+clips).subclip(0,14)

    noise=np.random.randint(0,15,(H,W,3)).astype("uint8")
    grain=ImageClip(noise).set_duration(14).set_opacity(0.03)

    final=CompositeVideoClip([final,grain])

    voice=AudioFileClip("voice.mp3")
    music=AudioFileClip(MUSIC).volumex(0.15).subclip(0,14)

    final=final.set_audio(CompositeAudioClip([music,voice]))

    final.write_videofile("reel.mp4",fps=30)

make()
