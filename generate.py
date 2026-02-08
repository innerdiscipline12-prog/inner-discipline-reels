import random, json, os
import numpy as np
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont

VIDEO="bg.mp4"
FONT_PATH="Anton-Regular.ttf"

W,H=1080,1920

# slightly below center
TEXT_Y=int(H*0.60)

LINES=[
"YOU WAIT FOR MOTIVATION",
"COMFORT IS THE ENEMY",
"NO ONE IS COMING",
"DISCIPLINE DECIDES",
"PROVE IT QUIETLY",
"CONTROL YOURSELF",
"STOP NEGOTIATING",
"DO THE HARD THING"
]

# -------- MEMORY --------
MEM="memory.json"
used=json.load(open(MEM)) if os.path.exists(MEM) else []

pool=[l for l in LINES if l not in used]
if len(pool)<4:
    used=[]
    pool=LINES.copy()

chosen=random.sample(pool,4)
json.dump(used+chosen,open(MEM,"w"))

# -------- TEXT FRAME --------
def frame(text):
    img=Image.new("RGBA",(W,H),(0,0,0,0))
    d=ImageDraw.Draw(img)

    font=ImageFont.truetype(FONT_PATH,130)

    max_w=int(W*0.75)

    words=text.split()
    lines=[]
    cur=""

    for w in words:
        test=(cur+" "+w).strip()
        box=d.textbbox((0,0),test,font=font)

        if box[2]-box[0]<=max_w:
            cur=test
        else:
            lines.append(cur)
            cur=w
    lines.append(cur)

    if len(lines)>2:
        lines=[lines[0]," ".join(lines[1:])]

    hs=[]
    for l in lines:
        b=d.textbbox((0,0),l,font=font)
        hs.append(b[3]-b[1])

    total=sum(hs)+30*(len(lines)-1)
    y=TEXT_Y-total//2

    for i,l in enumerate(lines):
        b=d.textbbox((0,0),l,font=font)
        tw=b[2]-b[0]
        x=(W-tw)//2

        # STRONG SHADOW
        d.text((x+6,y+6),l,font=font,fill=(0,0,0,220))

        # MAIN TEXT
        d.text((x,y),l,font=font,fill=(255,255,255,255))

        y+=hs[i]+30

    return np.array(img)

# -------- GENERATOR --------
def make():

    base=VideoFileClip(VIDEO).without_audio()

    base=base.resize(height=H)
    if base.w<W:
        base=base.resize(width=W)

    base=base.crop(x_center=base.w/2,y_center=base.h/2,width=W,height=H)

    clips=[]
    t=0

    for line in chosen:
        img=frame(line)

        c=ImageClip(img)\
            .set_start(t)\
            .set_duration(3.5)\
            .fadein(0.3)\
            .fadeout(0.3)

        clips.append(c)
        t+=3.5

    final=CompositeVideoClip([base]+clips).subclip(0,t)

    final.write_videofile("reel.mp4",fps=30)

make()
