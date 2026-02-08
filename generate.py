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
    img = Image.new("RGB",(W,H),(0,0,0))
    d = ImageDraw.Draw(img)

    font = ImageFont.truetype("DejaVuSans-Bold.ttf",90)

    box = d.textbbox((0,0),text,font=font)
    tw,th = box[2]-box[0], box[3]-box[1]

    x=(W-tw)//2
    y=SAFE_TOP+(SAFE_H-th)//2

    # shadow
    d.text((x+4,y+4),text,font=font,fill=(40,40,40))

    # main text
    d.text((x,y),text,font=font,fill="white")

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
