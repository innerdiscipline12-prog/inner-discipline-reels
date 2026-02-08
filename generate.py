import random
import numpy as np
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont

VIDEO="bg.mp4"

W,H=1080,1920

SAFE_TOP=300
SAFE_BOTTOM=500
SAFE_H=H-SAFE_TOP-SAFE_BOTTOM

LINES=[
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

def frame(text):
    img = Image.new("RGBA",(W,H),(0,0,0,0))
    d = ImageDraw.Draw(img)

    font = ImageFont.truetype("Anton-Regular.ttf",95)

    max_width = int(W*0.8)

    # -------- AUTO WRAP (2 lines max) --------
    words = text.split()
    lines=[]
    current=""

    for word in words:
        test = current+" "+word if current else word
        box = d.textbbox((0,0),test,font=font)
        w = box[2]-box[0]

        if w <= max_width:
            current = test
        else:
            lines.append(current)
            current = word

    lines.append(current)

    if len(lines)>2:
        lines=[lines[0]," ".join(lines[1:])]

    # -------- MEASURE HEIGHT --------
    line_heights=[]
    for l in lines:
        b=d.textbbox((0,0),l,font=font)
        line_heights.append(b[3]-b[1])

    total_h=sum(line_heights)+20*(len(lines)-1)
    y=SAFE_TOP+(SAFE_H-total_h)//2

    # -------- DRAW TEXT --------
    for i,l in enumerate(lines):
        b=d.textbbox((0,0),l,font=font)
        tw=b[2]-b[0]
        x=(W-tw)//2

        # SHADOW
        d.text((x+4,y+4),l,font=font,fill=(0,0,0,160))

        # SOFT GLOW
        for g in range(1,6):
            d.text((x-g,y),l,font=font,fill=(255,255,255,30))
            d.text((x+g,y),l,font=font,fill=(255,255,255,30))
            d.text((x,y-g),l,font=font,fill=(255,255,255,30))
            d.text((x,y+g),l,font=font,fill=(255,255,255,30))

        # MAIN TEXT
        d.text((x,y),l,font=font,fill=(255,255,255,255))

        y+=line_heights[i]+20

    return np.array(img)




def make():
    base=VideoFileClip(VIDEO).resize((W,H)).without_audio()

    clips=[]
    t=0

    for line in random.sample(LINES,5):
        img=frame(line)

        c=ImageClip(img).set_start(t).set_duration(3)
        c=c.fadein(0.5).fadeout(0.5)

        clips.append(c)
        t+=3

    final=CompositeVideoClip([base]+clips).subclip(0,t)

    # film grain
    noise=np.random.randint(0,25,(H,W,3)).astype("uint8")
    grain=ImageClip(noise).set_duration(t).set_opacity(0.06)

    final=CompositeVideoClip([final,grain])

    final.write_videofile("reel.mp4",fps=30)

make()
