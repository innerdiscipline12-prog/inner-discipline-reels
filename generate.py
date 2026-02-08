import numpy as np
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont

VIDEO="bg.mp4"

W,H=1080,1920

SAFE_TOP=300
SAFE_BOTTOM=500
SAFE_H=H-SAFE_TOP-SAFE_BOTTOM

LINES=[
"YOU NEED DISCIPLINE",
"COMFORT IS THE ENEMY",
"NO ONE IS COMING",
"CONTROL YOURSELF",
"PROVE IT QUIETLY"
]

def frame(text):
    img=Image.new("RGB",(W,H),(0,0,0))
    d=ImageDraw.Draw(img)

    font=ImageFont.truetype("DejaVuSans-Bold.ttf",90)

    box=d.textbbox((0,0),text,font=font)
    tw,th=box[2]-box[0],box[3]-box[1]

    x=(W-tw)//2
    y=SAFE_TOP+(SAFE_H-th)//2

    d.text((x,y),text,font=font,fill="white")

    return np.array(img)

def make():
    base=VideoFileClip(VIDEO).resize((W,H)).without_audio()

    clips=[]
    t=0

    for line in LINES:
        img=frame(line)

        c=ImageClip(img).set_start(t).set_duration(3)
        c=c.fadein(0.5).fadeout(0.5)

        clips.append(c)
        t+=3

    final=CompositeVideoClip([base]+clips).subclip(0,t)

    final.write_videofile("reel.mp4",fps=30)

make()
