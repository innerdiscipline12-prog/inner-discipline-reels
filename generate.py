import random, json, os
import numpy as np
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont, ImageFilter

VIDEO="bg.mp4"
FONT_PATH="Anton-Regular.ttf"

W,H=1080,1920

# Slightly lower than center (your request)
TEXT_Y = int(H*0.58)

LINES=[
"YOU WAIT FOR MOTIVATION",
"YOU SAY YOU ARE TIRED",
"COMFORT IS THE ENEMY",
"NO ONE IS COMING",
"DISCIPLINE DECIDES",
"CONTROL YOURSELF",
"PROVE IT QUIETLY",
"STOP NEGOTIATING",
"DO THE HARD THING",
"THIS IS DISCIPLINE"
]

# -------- MEMORY --------
MEM="memory.json"
used=json.load(open(MEM)) if os.path.exists(MEM) else []

pool=[l for l in LINES if l not in used]
if len(pool)<5:
    used=[]
    pool=LINES.copy()

chosen=random.sample(pool,5)
json.dump(used+chosen,open(MEM,"w"))

# -------- TEXT IMAGE --------
def frame(text):
    img=Image.new("RGBA",(W,H),(0,0,0,0))
    d=ImageDraw.Draw(img)

    font=ImageFont.truetype(FONT_PATH,120)

    # wrap to 2 lines
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

    # height calc
    hs=[]
    for l in lines:
        b=d.textbbox((0,0),l,font=font)
        hs.append(b[3]-b[1])

    total=sum(hs)+25*(len(lines)-1)

    y=TEXT_Y-total//2

    for i,l in enumerate(lines):
        b=d.textbbox((0,0),l,font=font)
        tw=b[2]-b[0]
        x=(W-tw)//2

        # soft glow
        glow=Image.new("RGBA",(W,H),(0,0,0,0))
        gd=ImageDraw.Draw(glow)
        gd.text((x,y),l,font=font,fill=(255,255,255,160))
        glow=glow.filter(ImageFilter.GaussianBlur(6))
        img=Image.alpha_composite(img,glow)

        # main text
        d.text((x,y),l,font=font,fill=(255,255,255,255))

        y+=hs[i]+25

    return np.array(img)

# -------- GENERATOR --------
def make():

    base=VideoFileClip(VIDEO).without_audio()

    # correct scaling
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
            .set_duration(4)\
            .fadein(0.4)\
            .fadeout(0.4)

        clips.append(c)
        t+=4

    final=CompositeVideoClip([base]+clips).subclip(0,t)

    # subtle grain
    noise=np.random.randint(0,20,(H,W,3)).astype("uint8")
    grain=ImageClip(noise).set_duration(final.duration).set_opacity(0.04)

    final=CompositeVideoClip([final,grain])

    final.write_videofile("reel.mp4",fps=30)

make()
