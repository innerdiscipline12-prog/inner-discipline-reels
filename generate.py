import random
import numpy as np
import json
import os

from moviepy.editor import *
from moviepy.video.fx.all import resize
from PIL import Image, ImageDraw, ImageFont

# ---------- SETTINGS ----------

VIDEO = "bg.mp4"

W, H = 1080, 1920

SAFE_TOP = 350
SAFE_BOTTOM = 450
SAFE_H = H - SAFE_TOP - SAFE_BOTTOM

FONT_PATH = "Anton-Regular.ttf"
FONT_SIZE = 95

MEMORY_FILE = "memory.json"

LINES = [
"YOU WAIT FOR MOTIVATION",
"YOU SAY YOU ARE TIRED",
"YOU BLAME YOUR MOOD",
"YOU WANT CHANGE WITHOUT PAIN",
"COMFORT IS THE ENEMY",
"NO ONE IS COMING",
"DISCIPLINE DECIDES",
"CONTROL YOURSELF",
"YOUR HABITS SHOW",
"PROVE IT QUIETLY",
"YOUR ROUTINE EXPOSES YOU",
"STOP NEGOTIATING",
"DO THE HARD THING",
"CONSISTENCY BUILDS POWER",
"THIS IS DISCIPLINE"
]

# ---------- SCRIPT MEMORY ----------

if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE,"r") as f:
        used=json.load(f)
else:
    used=[]

available=[l for l in LINES if l not in used]

if len(available)<4:
    used=[]
    available=LINES.copy()

chosen=random.sample(available,4)

used+=chosen
with open(MEMORY_FILE,"w") as f:
    json.dump(used,f)

# ---------- TEXT FRAME ----------

def frame(text):

    img = Image.new("RGBA", (W,H), (0,0,0,0))
    d = ImageDraw.Draw(img)

    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    max_width = int(W*0.8)

    words = text.split()
    lines=[]
    current=""

    for word in words:
        test = current+" "+word if current else word
        box = d.textbbox((0,0), test, font=font)
        w = box[2]-box[0]

        if w <= max_width:
            current = test
        else:
            lines.append(current)
            current = word

    lines.append(current)

    if len(lines)>2:
        lines=[lines[0], " ".join(lines[1:])]

    heights=[]
    for l in lines:
        b=d.textbbox((0,0),l,font=font)
        heights.append(b[3]-b[1])

    total_h=sum(heights)+20*(len(lines)-1)

    y = SAFE_TOP + (SAFE_H-total_h)//2 + 40

    for i,l in enumerate(lines):

        b=d.textbbox((0,0),l,font=font)
        w=b[2]-b[0]

        x=(W-w)//2

        # shadow
        d.text((x+4,y+4),l,font=font,fill=(0,0,0,180))

        # glow (soft)
        d.text((x-2,y-2),l,font=font,fill=(255,255,255,60))

        # main
        d.text((x,y),l,font=font,fill=(255,255,255,255))

        y+=heights[i]+20

    return np.array(img)

# ---------- GENERATOR ----------

def make():

    base=VideoFileClip(VIDEO).without_audio()

    base=base.fx(resize, lambda t:1+0.015*t)

    base=base.resize(height=H)
    if base.w < W:
        base=base.resize(width=W)

    base=base.crop(x_center=base.w/2,y_center=base.h/2,width=W,height=H)

    clips=[]
    t=0

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

    # subtle grain
    noise=np.random.randint(0,15,(H,W,3)).astype("uint8")
    grain=(ImageClip(noise)
           .set_duration(final.duration)
           .set_opacity(0.03))

    final=CompositeVideoClip([final,grain])

    # ultra-loop fade
    final=final.crossfadeout(0.5)

    final.write_videofile("reel.mp4",fps=30)

    # captions export
    with open("captions.txt","w") as f:
        f.write("\n".join(chosen))

make()
