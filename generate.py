import os, json, random, asyncio, math
import numpy as np
from moviepy.editor import (
    VideoFileClip, ImageClip, CompositeVideoClip,
    AudioFileClip, CompositeAudioClip
)
from moviepy.video.fx.all import resize
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ================= SETTINGS =================

VIDEO = "bg.mp4"
MUSIC = "music.mp3"
FONT_PATH = "Anton-Regular.ttf"

W, H = 1080, 1920

SAFE_TOP = 350
SAFE_BOTTOM = 450
SAFE_H = H - SAFE_TOP - SAFE_BOTTOM

MAX_SECONDS = 14.0

VOICE = "en-US-ChristopherNeural"
VOICE_RATE = "-35%"
VOICE_PITCH = "-20Hz"

MUSIC_BASE = 0.25
MUSIC_FINAL = 0.6

# ============== SCRIPT POOL ==============

LINES = [
"YOU WAIT FOR MOTIVATION",
"COMFORT IS THE ENEMY",
"NO ONE IS COMING",
"DISCIPLINE DECIDES",
"CONTROL YOURSELF",
"PROVE IT QUIETLY",
"STOP NEGOTIATING",
"DO THE HARD THING",
"FEELINGS ARE LIARS",
"STANDARDS WIN",
"SHOW UP ANYWAY",
"CONSISTENCY BUILDS POWER",
"FOCUS BUILDS CONTROL",
"RESULTS FOLLOW DISCIPLINE",
"EXCUSES KILL PROGRESS",
"YOUR HABITS DECIDE",
"SILENCE BUILDS STRENGTH",
"CONTROL YOUR INPUTS",
"STRUCTURE CREATES FREEDOM",
"REPEAT THE HARD THING",
]

HASHTAGS = [
"#discipline","#mindset","#selfcontrol",
"#consistency","#innerdiscipline",
"#focus","#growth","#mentaltoughness"
]

# ============== MEMORY (NO REPEATS) ==============

MEM = "memory.json"
used = json.load(open(MEM)) if os.path.exists(MEM) else []

pool = [l for l in LINES if l not in used]

if len(pool) < 4:
    used = []
    pool = LINES.copy()

chosen = random.sample(pool, 4)
json.dump(used + chosen, open(MEM,"w"))

# ============== AUTO FOLDER NUMBERING ==============

BASE_OUT = "outputs"
os.makedirs(BASE_OUT, exist_ok=True)

existing = [int(x) for x in os.listdir(BASE_OUT) if x.isdigit()]
next_id = str(max(existing)+1 if existing else 1).zfill(3)

OUTDIR = os.path.join(BASE_OUT, next_id)
os.makedirs(OUTDIR)

# ============== VOICE ==============

async def make_voice(line, file):
    tts = edge_tts.Communicate(
        line,
        voice=VOICE,
        rate=VOICE_RATE,
        pitch=VOICE_PITCH
    )
    await tts.save(file)

# ============== TEXT FRAME ==============

def frame(text):
    img = Image.new("RGBA",(W,H),(0,0,0,0))
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH,120)

    max_w = int(W*0.75)

    words = text.split()
    lines=[]; cur=""

    for w in words:
        test=(cur+" "+w).strip()
        box=d.textbbox((0,0),test,font=font)
        if box[2]-box[0]<=max_w:
            cur=test
        else:
            lines.append(cur); cur=w
    lines.append(cur)

    hs=[]
    for l in lines:
        b=d.textbbox((0,0),l,font=font)
        hs.append(b[3]-b[1])

    total=sum(hs)+25*(len(lines)-1)
    y=SAFE_TOP+(SAFE_H-total)//2

    for i,l in enumerate(lines):
        b=d.textbbox((0,0),l,font=font)
        x=(W-(b[2]-b[0]))//2

        d.text((x+4,y+4),l,font=font,fill=(0,0,0,200))
        d.text((x,y),l,font=font,fill="white")

        y+=hs[i]+25

    return np.array(img)

# ============== THUMBNAIL (PERFECT CENTER) ==============

def make_thumbnail(line,path):
    text=" ".join(line.split()[:2])

    img=Image.new("RGB",(1080,1920),"black")
    d=ImageDraw.Draw(img)
    font=ImageFont.truetype(FONT_PATH,200)

    box=d.textbbox((0,0),text,font=font)
    w=box[2]-box[0]
    h=box[3]-box[1]

    x=(1080-w)//2
    y=(1920-h)//2

    d.text((x+6,y+6),text,font=font,fill="black")
    d.text((x,y),text,font=font,fill="white")

    img.save(path)

# ============== CAPTION ==============

def make_caption(lines,path):
    cap=" ".join(lines[:2]).title()
    tags=" ".join(random.sample(HASHTAGS,4))

    with open(path,"w") as f:
        f.write(cap+"\n\n"+tags)

# ============== AUTO DUCK ==============

def apply_duck(music,windows):
    def duck(get_frame,t):
        speaking=any(s<=t<=e for s,e in windows)
        factor=0.25 if speaking else 1.0
        return get_frame(t)*factor
    return music.fl(duck)

# ============== MAIN ==============

def make():

    base=VideoFileClip(VIDEO).without_audio()
    base=base.fx(resize,lambda t:1+0.015*t)
    base=base.resize(height=H)

    if base.w<W:
        base=base.resize(width=W)

    base=base.crop(
        x_center=base.w/2,
        y_center=base.h/2,
        width=W,height=H
    )

    clips=[]
    audio_clips=[]
    speaking_windows=[]

    t=0

    for i,line in enumerate(chosen):

        vf=f"v{i}.mp3"
        asyncio.run(make_voice(line,vf))

        audio=AudioFileClip(vf)
        dur=audio.duration+0.4

        speaking_windows.append((t,t+audio.duration))

        img=frame(line)

        clip=(ImageClip(img)
              .set_start(t)
              .set_duration(dur)
              .fadein(0.4)
              .fadeout(0.4))

        clips.append(clip)
        audio_clips.append(audio.set_start(t))

        t+=dur

    final=CompositeVideoClip([base]+clips).subclip(0,min(t,MAX_SECONDS))

    voice_mix=CompositeAudioClip(audio_clips).volumex(2.0)

    if os.path.exists(MUSIC):
        music=(AudioFileClip(MUSIC)
               .volumex(MUSIC_BASE)
               .audio_fadein(1.2)
               .audio_fadeout(1.2)
               .subclip(0,final.duration))

        music=apply_duck(music,speaking_windows).volumex(MUSIC_FINAL)

        final_audio=CompositeAudioClip([music,voice_mix])
    else:
        final_audio=voice_mix

    final=final.set_audio(final_audio)

    # ===== EXPORTS =====

    out_video=os.path.join(OUTDIR,"reel.mp4")
    final.write_videofile(out_video,fps=30,audio_codec="aac")

    make_thumbnail(chosen[0],
                   os.path.join(OUTDIR,"thumbnail.jpg"))

    make_caption(chosen,
                 os.path.join(OUTDIR,"caption.txt"))

# ============== RUN ==============

if __name__=="__main__":
    make()
