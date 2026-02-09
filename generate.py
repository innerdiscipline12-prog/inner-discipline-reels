import os, json, random, asyncio
import numpy as np
from moviepy.editor import *
from moviepy.video.fx.all import resize
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ---------- SETTINGS ----------

VIDEO="bg.mp4"
MUSIC="music.mp3"
FONT_PATH="Anton-Regular.ttf"

W,H=1080,1920

VOICE="en-US-ChristopherNeural"
VOICE_RATE="-35%"
VOICE_PITCH="-20Hz"

REELS_PER_RUN=5
MAX_SECONDS=14

HASHTAGS=[
"#discipline","#selfcontrol","#focus",
"#mindset","#innerdiscipline","#consistency",
"#growth","#success","#motivation"
]

# ---------- VIRAL WEIGHTED LINES ----------

LINES={
"NO ONE IS COMING":5,
"COMFORT IS THE ENEMY":5,
"STOP NEGOTIATING":5,
"DO THE HARD THING":5,
"DISCIPLINE DECIDES":4,
"CONTROL YOURSELF":4,
"PROVE IT QUIETLY":4,
"YOU WAIT FOR MOTIVATION":3,
"BUILD SILENT HABITS":3,
"RESULTS NEED STANDARDS":3,
"EXECUTE DAILY":2,
"FOCUS BUILDS POWER":2,
"SMALL WINS MATTER":2,
"REMOVE EXCUSES":2,
"STAY CONSISTENT":2,
"SELF CONTROL WINS":2,
"WORK IN SILENCE":2,
"BE RELENTLESS":2
}

ALL_LINES=list(LINES.keys())

# ---------- MEMORY ----------

MEM="memory.json"
used=json.load(open(MEM)) if os.path.exists(MEM) else []

# ---------- VOICE ----------

async def make_voice(text,path):
    tts=edge_tts.Communicate(
        text,
        voice=VOICE,
        rate=VOICE_RATE,
        pitch=VOICE_PITCH
    )
    await tts.save(path)

# ---------- TEXT FRAME ----------

def frame(text):
    img=Image.new("RGBA",(W,H),(0,0,0,0))
    d=ImageDraw.Draw(img)
    font=ImageFont.truetype(FONT_PATH,120)

    box=d.textbbox((0,0),text,font=font)
    w=box[2]-box[0]
    h=box[3]-box[1]

    x=(W-w)//2
    y=(H-h)//2

    d.text((x+6,y+6),text,font=font,fill=(0,0,0,180))
    d.text((x,y),text,font=font,fill="white")

    return np.array(img)

# ---------- THUMBNAIL ----------

def make_thumbnail(text,path):
    words=" ".join(text.split()[:2])

    img=Image.new("RGB",(1080,1920),(0,0,0))
    d=ImageDraw.Draw(img)
    font=ImageFont.truetype(FONT_PATH,180)

    box=d.textbbox((0,0),words,font=font)
    w=box[2]-box[0]
    h=box[3]-box[1]

    x=(1080-w)//2
    y=(1920-h)//2

    d.text((x+8,y+8),words,font=font,fill=(0,0,0))
    d.text((x,y),words,font=font,fill="white")

    img.save(path)

# ---------- CAPTION ----------

def make_caption(lines,path):
    cap=" ".join(lines[:2]).title()
    tags=" ".join(random.sample(HASHTAGS,4))

    with open(path,"w") as f:
        f.write(cap+"\n\n"+tags)

# ---------- SMART PICK ----------

def pick_lines():
    global used

    pool=[l for l in ALL_LINES if l not in used]
    if len(pool)<4:
        used=[]
        pool=ALL_LINES.copy()

    # weighted hook
    weights=[LINES[l] for l in pool]
    hook=random.choices(pool,weights=weights,k=1)[0]

    remaining=[l for l in pool if l!=hook]
    others=random.sample(remaining,3)

    chosen=[hook]+others
    used+=chosen

    return chosen

# ---------- REEL ----------

def make_reel(idx):

    folder=f"outputs/{idx:02d}"
    os.makedirs(folder,exist_ok=True)

    chosen=pick_lines()

    text="... ".join(chosen)

    voice_path=f"{folder}/voice.mp3"
    asyncio.run(make_voice(text,voice_path))

    base=VideoFileClip(VIDEO).without_audio()
    base=base.fx(resize,lambda t:1+0.02*t).resize(height=H)

    if base.w<W:
        base=base.resize(width=W)

    base=base.crop(x_center=base.w/2,y_center=base.h/2,width=W,height=H)

    clips=[]
    t=0

    for line in chosen:
        img=frame(line)
        c=(ImageClip(img)
           .set_start(t)
           .set_duration(3.5)
           .fadein(0.25)
           .fadeout(0.25))
        clips.append(c)
        t+=3.5

    final=CompositeVideoClip([base]+clips).subclip(0,MAX_SECONDS)

    voice=AudioFileClip(voice_path)

    if os.path.exists(MUSIC):
        music=AudioFileClip(MUSIC).volumex(0.08).subclip(0,MAX_SECONDS)
        final=final.set_audio(CompositeAudioClip([music,voice]))
    else:
        final=final.set_audio(voice)

    final.write_videofile(f"{folder}/reel.mp4",fps=30)

    make_thumbnail(chosen[0],f"{folder}/thumbnail.jpg")
    make_caption(chosen,f"{folder}/caption.txt")

# ---------- RUN ----------

os.makedirs("outputs",exist_ok=True)

for i in range(1,REELS_PER_RUN+1):
    make_reel(i)

json.dump(used,open(MEM,"w"))

print("✅ PRO V3.5 batch ready.")
