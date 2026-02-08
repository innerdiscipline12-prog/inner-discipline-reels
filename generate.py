import random
import json
import os
import numpy as np

from moviepy.editor import *
from moviepy.video.fx import all as vfx

from PIL import Image, ImageDraw, ImageFont

# ---------------- SETTINGS ----------------

VIDEO = "bg.mp4"
FONT_PATH = "Anton-Regular.ttf"

W, H = 1080, 1920

SAFE_TOP = 300
SAFE_BOTTOM = 500
SAFE_H = H - SAFE_TOP - SAFE_BOTTOM

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

# ---------------- MEMORY SYSTEM ----------------

MEMORY_FILE = "memory.json"

if os.path.exists(MEMORY_FILE):
    used = json.load(open(MEMORY_FILE))
else:
    used = []

available = [l for l in LINES if l not in used]

if len(available) < 5:
    used = []
    available = LINES.copy()

chosen = random.sample(available, 5)

json.dump(used + chosen, open(MEMORY_FILE, "w"))

# ---------------- TEXT FRAME ----------------

def frame(text):

    img = Image.new("RGBA", (W, H), (0,0,0,0))
    d = ImageDraw.Draw(img)

    font = ImageFont.truetype(FONT_PATH, 95)

    max_width = int(W * 0.8)

    words = text.split()
    lines=[]
    current=""

    # AUTO WRAP (2 lines max)
    for word in words:
        test = current + " " + word if current else word
        box = d.textbbox((0,0), test, font=font)
        w = box[2]-box[0]

        if w <= max_width:
            current = test
        else:
            lines.append(current)
            current = word

    lines.append(current)

    if len(lines) > 2:
        lines = [lines[0], " ".join(lines[1:])]

    # HEIGHT CENTERING
    heights=[]
    for l in lines:
        b = d.textbbox((0,0), l, font=font)
        heights.append(b[3]-b[1])

    total_h = sum(heights) + 20*(len(lines)-1)

    y = SAFE_TOP + (SAFE_H - total_h)//2

    # DRAW TEXT
    for i,l in enumerate(lines):
        b = d.textbbox((0,0), l, font=font)
        tw = b[2]-b[0]

        x = (W - tw)//2

        d.text((x,y), l, font=font, fill="white")

        y += heights[i] + 20

    return np.array(img)

# ---------------- MAIN GENERATOR ----------------

def make():

    base = VideoFileClip(VIDEO).without_audio()

    # slow cinematic zoom
    base = base.fx(vfx.resize, lambda t: 1 + 0.04*t)
    base = base.set_position("center").resize((W,H))

    clips=[]
    t=0

    # WORD BY WORD REVEAL
    for line in chosen:

        words = line.split()

        for i in range(len(words)):
            img = frame(" ".join(words[:i+1]))

            c = ImageClip(img)\
                .set_start(t + i*0.35)\
                .set_duration(2)

            clips.append(c)

        t += len(words)*0.35 + 1.5

    final = CompositeVideoClip([base] + clips).subclip(0,t)

    # FILM GRAIN
    noise = np.random.randint(0,25,(H,W,3)).astype("uint8")
    grain = ImageClip(noise)\
        .set_duration(final.duration)\
        .set_opacity(0.06)

    final = CompositeVideoClip([final, grain])

    # LOOP ENDING
    loop = final.subclip(final.duration-1, final.duration)
    final = concatenate_videoclips([final, loop])

    final.write_videofile("reel.mp4", fps=30)

make()
