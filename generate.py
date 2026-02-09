import os, json, random, asyncio
import numpy as np
from moviepy.editor import *
from moviepy.video.fx.all import resize
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ================= SETTINGS =================

VIDEO="bg.mp4"
MUSIC="music.mp3"
FONT_PATH="Anton-Regular.ttf"

W,H=1080,1920
MAX_SECONDS=9          # optimal retention
REELS_PER_RUN=5

VOICE="en-US-ChristopherNeural"
VOICE_RATE="-35%"
VOICE_PITCH="-20Hz"

HASHTAGS=[
"#discipline","#selfcontrol","#focus",
"#mindset","#innerdiscipline",
"#consistency","#stoic","#growth"
]

# ================= HOOK MODE =================

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
"REMOVE EXCUSES":2,
"STAY CONSISTENT":2,
"WORK IN SILENCE":2,
"BE RELENTLESS":2
}

ALL_LINES=list(LINES.keys())

# ================= MEMORY =================

MEM="memory.json"
used=json.load(open(MEM)) if os.path.exists(MEM) else []

# ================= VOICE =================

async def make_voice(text,path):
    tts=edge_tts.Communicate(
        text,
        voice=VOICE,
        rate=VOICE_RATE,
        pitch=VOICE_PITCH
    )
    await tts.save(path)

# ================= TEXT FRAME =================

def frame(text):
    img = Image.new("RGBA",(W,H),(0,0,0,0))
    d = ImageDraw.Draw(img)

    words=text.split()
    if len(words)>=2:
        mid=len(words)//2
        text=" ".join(words[:mid])+"\n"+" ".join(words[mid:])

    margin=100
    max_w=W-margin*2
    max_h=H-margin*2

    size=160

    while size>40:
        font=ImageFont.truetype(FONT_PATH,size)
        box=d.multiline_textbbox((0,0),text,font=font,spacing=20)

        tw=box[2]-box[0]
        th=box[3]-box[1]

        if tw<=max_w and th<=max_h:
            break
        size-=4

    x=(W-tw)//2
    y=int(H*0.55 - th/2)   # discipline safe zone

    d.multiline_text((x+6,y+6),text,font=font,fill=(0,0,0,180),align="center",spacing=20)
    d.multiline_text((x,y),text,font=font,fill="white",align="center",spacing=20)

    return np.array(img)

# ================= THUMBNAIL =================

def make_thumbnail(text,path):
    words=text.split()
    if len(words)>=2:
        mid=len(words)//2
        text=" ".join(words[:mid])+"\n"+" ".join(words[mid:])

    img=Image.new("RGB",(1080,1920),(0,0,0))
    d=ImageDraw.Draw(img)

    size=200

    while size>60:
        font=ImageFont.truetype(FONT_PATH,size)
        box=d.multiline_textbbox((0,0),text,font=font,spacing=30)

        tw=box[2]-box[0]
        th=box[3]-box[1]

        if tw<900 and th<1600:
            break
        size-=4

    x=(1080-tw)//2
    y=(1920-th)//2

    d.multiline_text((x+8,y+8),text,font=font,fill=(0,0,0),align="center",spacing=30)
    d.multiline_text((x,y),text,font=font,fill="white",align="center",spacing=30)

    img.save(path)

# ================= CAPTION =================

def make_caption(lines,path):
    cap=" • ".join(lines[:2]).title()
    tags=" ".join(random.sample(HASHTAGS,4))

    with open(path,"w") as f:
        f.write(cap+"\n\n"+tags)

# ================= SMART PICK =================

def pick_lines():
    global used

    pool=[l for l in ALL_LINES if l not in used]

    if len(pool)<4:
        used=[]
        pool=ALL_LINES.copy()

    weights=[LINES[l] for l in pool]
    hook=random.choices(pool,weights=weights,k=1)[0]

    remaining=[l for l in pool if l!=hook]
    others=random.sample(remaining,2)

    chosen=[hook]+others
    used+=chosen

    return chosen

# ================= REEL BUILD =================

def make_reel(idx):

    folder=f"outputs/{idx:02d}"
    os.makedirs(folder,exist_ok=True)

    chosen=pick_lines()

    text="... ".join(chosen)+"..."  # loop psychology

    voice_path=f"{folder}/voice.mp3"
    asyncio.run(make_voice(text,voice_path))

    base=VideoFileClip(VIDEO).without_audio()

    # cinematic slow zoom
    base=base.fx(resize,lambda t:1+0.008*t).resize(height=H)

    if base.w<W:
        base=base.resize(width=W)

    base=base.crop(x_center=base.w/2,y_center=base.h/2,width=W,height=H)

    clips=[]
    t=0

    for line in chosen:
        img=frame(line)

        c=(ImageClip(img)
           .set_start(t)
           .set_duration(1.6)
           .fadein(0.3)
           .fadeout(0.3))

        clips.append(c)
        t+=1.6

    final=CompositeVideoClip([base]+clips).subclip(0,MAX_SECONDS)

    # LOOP MODE ENDING
    final=final.fx(vfx.freeze,t=final.duration-0.4,freeze_duration=0.4)
    final=final.fadeout(0.6)

    voice=AudioFileClip(voice_path)

    if os.path.exists(MUSIC):
        music=AudioFileClip(MUSIC).volumex(0.1).subclip(0,MAX_SECONDS)
        final=final.set_audio(CompositeAudioClip([music,voice]))
    else:
        final=final.set_audio(voice)

    final.write_videofile(f"{folder}/reel.mp4",fps=30)

    make_thumbnail(chosen[0],f"{folder}/thumbnail.jpg")
    make_caption(chosen,f"{folder}/caption.txt")

# ================= RUN =================

os.makedirs("outputs",exist_ok=True)

for i in range(1,REELS_PER_RUN+1):
    make_reel(i)

json.dump(used,open(MEM,"w"))

print("🔥 DISCIPLINE MASTER SCRIPT COMPLETE")
