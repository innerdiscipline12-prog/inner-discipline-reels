import os, random, glob
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# ========= SETTINGS =========

W,H = 1080,1920
FONT_PATH="Anton-Regular.ttf"

HOOK_DUR=2.8
MID_DUR=2.2
END_DUR=2.8

FADE=0.15

# ========= CONTENT BANK =========

HOOKS=[
"You're not tired. You're undisciplined.",
"Comfort is ruining your future.",
"Your habits expose you.",
"You don't lack time. You lack control.",
"No one is coming to save you.",
"You are negotiating with weakness.",
]

TRUTHS=[
"Comfort is expensive.",
"Discipline decides outcomes.",
"Control beats motivation.",
"Consistency builds identity.",
"Action creates clarity.",
]

RELATABLE=[
"You get distracted easily.",
"You delay what matters.",
"You know what to do.",
"You just don't do it.",
]

QUESTIONS=[
"Still here?",
"Day 1 or Day 100?",
"Will you finish?",
"Can you stay consistent?",
]

CTAS=[
"Comment DISCIPLINE.",
"Type DISCIPLINE.",
]

# ========= BACKGROUNDS =========

BG_VIDEOS=glob.glob("bg*.mp4")

def pick_bg(total_len):
    vid=VideoFileClip(random.choice(BG_VIDEOS)).without_audio()
    
    if vid.duration<=total_len:
        clip=vid.loop(duration=total_len)
    else:
        start=random.uniform(0,vid.duration-total_len)
        clip=vid.subclip(start,start+total_len)
        
    # cinematic slow zoom
    clip=clip.resize((W,H)).fx(vfx.resize, lambda t:1+0.04*t)
    
    return clip

# ========= TEXT IMAGE =========

def text_img(txt):
    img=Image.new("RGBA",(W,H),(0,0,0,0))
    d=ImageDraw.Draw(img)

    font_size=110
    font=ImageFont.truetype(FONT_PATH,font_size)

    # wrap
    words=txt.split()
    lines=[]
    cur=""
    for w in words:
        if len(cur+w)<18:
            cur+=w+" "
        else:
            lines.append(cur)
            cur=w+" "
    lines.append(cur)

    text="\n".join(lines)

    box=d.multiline_textbbox((0,0),text,font=font,spacing=10)
    tw,th=box[2]-box[0],box[3]-box[1]

    x=(W-tw)//2
    y=int(H*0.62)

    # shadow
    d.multiline_text((x+4,y+4),text,font=font,fill=(0,0,0,200),align="center")
    d.multiline_text((x,y),text,font=font,fill="white",align="center")

    return np.array(img)

# ========= SCRIPT BUILDER =========

def build_script(idx):
    
    script=[
        random.choice(HOOKS),
        random.choice(RELATABLE),
        random.choice(TRUTHS),
    ]
    
    # 2 of 5 reels get CTA
    if idx%5 in [0,1]:
        script.append(random.choice(CTAS))
    else:
        script.append(random.choice(QUESTIONS))
        
    return script

# ========= MAIN =========

os.makedirs("outputs",exist_ok=True)

for idx in range(1,6):
    
    lines=build_script(idx)
    
    t=0
    clips=[]
    
    for i,line in enumerate(lines):
        
        if i==0: dur=HOOK_DUR
        elif i==len(lines)-1: dur=END_DUR
        else: dur=MID_DUR
        
        img=text_img(line)
        
        txt=(ImageClip(img)
             .set_start(t)
             .set_duration(dur)
             .fadein(FADE)
             .fadeout(FADE))
             
        clips.append(txt)
        t+=dur
    
    bg=pick_bg(t)
    
    final=CompositeVideoClip([bg]+clips,size=(W,H))
    
    final.write_videofile(
        f"outputs/reel_{idx}.mp4",
        fps=30,
        codec="libx264"
    )

print("DONE.")
