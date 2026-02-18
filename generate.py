import os, random, glob, pyttsx3
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# ========= SETTINGS =========

W,H=1080,1920
FONT_PATH="Anton-Regular.ttf"

HOOK_DUR=2.8
MID_DUR=2.2
END_DUR=2.8
FADE=0.15

# ========= VOICE =========

engine=pyttsx3.init()
engine.setProperty('rate',150)   # slower
engine.setProperty('volume',1.0)

voices=engine.getProperty('voices')
if len(voices)>1:
    engine.setProperty('voice',voices[1].id)

def tts(text,filename):
    engine.save_to_file(text,filename)
    engine.runAndWait()

# ========= CONTENT BANK =========

HOOKS=[
"You're not tired. You're undisciplined.",
"Comfort is ruining your future.",
"You don't lack time. You lack control.",
"No one is coming to save you.",
]

TRUTHS=[
"Discipline decides outcomes.",
"Control beats motivation.",
"Consistency builds identity.",
]

RELATABLE=[
"You get distracted easily.",
"You delay what matters.",
"You know what to do.",
]

QUESTIONS=[
"Still here?",
"Day 1 or Day 100?",
"Will you finish?",
]

CTAS=[
"Comment discipline.",
"Type discipline.",
]

# ========= BACKGROUNDS =========

BG_VIDEOS=glob.glob("bg*.mp4")

def pick_bg(total):
    v=VideoFileClip(random.choice(BG_VIDEOS)).without_audio()
    
    if v.duration<total:
        v=v.loop(duration=total)
    else:
        s=random.uniform(0,v.duration-total)
        v=v.subclip(s,s+total)
        
    return v.resize((W,H)).fx(vfx.resize,lambda t:1+0.04*t)

# ========= TEXT =========

def text_img(txt):
    img=Image.new("RGBA",(W,H),(0,0,0,0))
    d=ImageDraw.Draw(img)
    f=ImageFont.truetype(FONT_PATH,110)

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

    txt="\n".join(lines)
    box=d.multiline_textbbox((0,0),txt,font=f,spacing=10)
    tw,th=box[2]-box[0],box[3]-box[1]

    x=(W-tw)//2
    y=int(H*0.62)

    d.multiline_text((x+4,y+4),txt,font=f,fill=(0,0,0,200))
    d.multiline_text((x,y),txt,font=f,fill="white")

    return np.array(img)

# ========= SCRIPT =========

def build_script(i):
    s=[
        random.choice(HOOKS),
        random.choice(RELATABLE),
        random.choice(TRUTHS)
    ]
    
    if i%5 in [0,1]:
        s.append(random.choice(CTAS))
    else:
        s.append(random.choice(QUESTIONS))
        
    return s

# ========= MAIN =========

os.makedirs("outputs",exist_ok=True)

for i in range(1,6):
    
    lines=build_script(i)
    
    t=0
    txt_clips=[]
    aud_clips=[]
    
    for j,line in enumerate(lines):
        
        if j==0: dur=HOOK_DUR
        elif j==len(lines)-1: dur=END_DUR
        else: dur=MID_DUR
        
        # voice
        tmp=f"v{i}_{j}.wav"
        tts(line,tmp)
        a=AudioFileClip(tmp)
        
        img=text_img(line)
        
        txt=(ImageClip(img)
             .set_start(t)
             .set_duration(dur)
             .fadein(FADE)
             .fadeout(FADE))
             
        txt_clips.append(txt)
        aud_clips.append(a.set_start(t))
        
        t+=dur
        
    bg=pick_bg(t)
    
    final=CompositeVideoClip([bg]+txt_clips,size=(W,H))
    audio=CompositeAudioClip(aud_clips)
    
    final=final.set_audio(audio)
    
    final.write_videofile(
        f"outputs/reel_{i}.mp4",
        fps=30,
        codec="libx264"
    )

print("DONE")
