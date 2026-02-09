import os, json, random, asyncio
import numpy as np

from moviepy.editor import (
    VideoFileClip, ImageClip, CompositeVideoClip,
    AudioFileClip, CompositeAudioClip
)
from moviepy.video.fx.all import resize

from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ==============================
# SETTINGS
# ==============================

VIDEO = "bg.mp4"
MUSIC = "music.mp3"
FONT_PATH = "Anton-Regular.ttf"

W,H = 1080,1920

SAFE_TOP = 350
SAFE_BOTTOM = 450
SAFE_H = H-SAFE_TOP-SAFE_BOTTOM

MAX_SECONDS = 14.0

VOICE = "en-US-ChristopherNeural"
VOICE_RATE = "-35%"
VOICE_PITCH = "-20Hz"
VOICE_VOLUME = 2.0

MUSIC_BASE = 0.25
MUSIC_DUCK = 0.25
MUSIC_FINAL = 0.7

OUTROOT = "outputs"

# ==============================
# SCRIPT POOL
# ==============================

LINES = [
"YOU WAIT FOR MOTIVATION",
"COMFORT IS THE ENEMY",
"NO ONE IS COMING",
"DISCIPLINE DECIDES",
"CONTROL YOURSELF",
"PROVE IT QUIETLY",
"STOP NEGOTIATING",
"DO THE HARD THING",
"FEELINGS ARE TEMPORARY",
"STANDARDS STAY",
"RESULTS REQUIRE CONTROL",
"NO EXCUSES LEFT",
"BUILD SILENT POWER",
"WIN THE MORNING",
"CONTROL YOUR HABITS",
"FOCUS BUILDS DISCIPLINE",
"CONSISTENCY WINS",
"SHOW UP ANYWAY",
"STOP WAITING",
"EXECUTE DAILY"
]

HASHTAGS = [
"#discipline","#selfcontrol","#mindset",
"#consistency","#innerdiscipline",
"#focus","#growth","#standards"
]

# ==============================
# MEMORY (NO REPEATS)
# ==============================

MEM="memory.json"
used=json.load(open(MEM)) if os.path.exists(MEM) else []

pool=[l for l in LINES if l not in used]

if len(pool)<4:
    used=[]
    pool=LINES.copy()

chosen=random.sample(pool,4)
json.dump(used+chosen,open(MEM,"w"))

# ==============================
# OUTPUT FOLDER AUTO NUMBER
# ==============================

os.makedirs(OUTROOT,exist_ok=True)

n=1
while os.path.exists(f"{OUTROOT}/{n}"):
    n+=1

OUTDIR=f"{OUTROOT}/{n}"
os.makedirs(OUTDIR)

# ==============================
# VOICE
# ==============================

async def make_voice(lines):
    files=[]
    windows=[]
    t=0

    for i,line in enumerate(lines):
        file=f"{OUTDIR}/v{i}.mp3"

        tts=edge_tts.Communicate(
            line,
            voice=VOICE,
            rate=VOICE_RATE,
            pitch=VOICE_PITCH
        )
        await tts.save(file)

        a=AudioFileClip(file)
        dur=a.duration+0.4

        windows.append((t,t+dur))
        t+=dur
        files.append((file,dur))

    return files,windows,t

voice_files,speaking_windows,final_len = asyncio.run(make_voice(chosen))

# ==============================
# TEXT FRAME
# ==============================

def frame(text):
    img=Image.new("RGBA",(W,H),(0,0,0,0))
    d=ImageDraw.Draw(img)
    font=ImageFont.truetype(FONT_PATH,120)

    max_w=int(W*0.75)

    words=text.split()
    lines=[]; cur=""

    for w in words:
        test=(cur+" "+w).strip()
        box=d.textbbox((0,0),test,font=font)
        if box[2]-box[0]<=max_w:
            cur=test
        else:
            lines.append(cur); cur=w
    lines.append(cur)

    hs=[d.textbbox((0,0),l,font=font)[3] for l in lines]
    total=sum(hs)+25*(len(lines)-1)

    y=SAFE_TOP+(SAFE_H-total)//2

    for i,l in enumerate(lines):
        box=d.textbbox((0,0),l,font=font)
        x=(W-(box[2]-box[0]))//2

        d.text((x+4,y+4),l,font=font,fill=(0,0,0,180))
        d.text((x,y),l,font=font,fill="white")

        y+=hs[i]+25

    return np.array(img)

# ==============================
# DUCKING
# ==============================

def apply_duck(music,windows):
    def duck(get_frame,t):
        speaking=any(s<=t<=e for s,e in windows)
        factor=MUSIC_DUCK if speaking else 1.0
        return get_frame(t)*factor
    return music.fl(duck)

# ==============================
# VIDEO BUILD
# ==============================

def make():

    base=VideoFileClip(VIDEO).without_audio()
    base=base.fx(resize,lambda t:1+0.015*t)
    base=base.resize(height=H)

    if base.w<W:
        base=base.resize(width=W)

    base=base.crop(x_center=base.w/2,y_center=base.h/2,width=W,height=H)

    clips=[]
    audio_clips=[]
    t=0

    for i,(file,dur) in enumerate(voice_files):
        img=frame(chosen[i])

        clip=(ImageClip(img)
              .set_start(t)
              .set_duration(dur)
              .fadein(0.3)
              .fadeout(0.3))

        clips.append(clip)

        a=AudioFileClip(file).set_start(t)
        audio_clips.append(a)

        t+=dur

    final=CompositeVideoClip([base]+clips).subclip(0,min(t,MAX_SECONDS))

    # grain
    noise=np.random.randint(0,15,(H,W,3)).astype("uint8")
    grain=ImageClip(noise).set_duration(final.duration).set_opacity(0.03)
    final=CompositeVideoClip([final,grain])

    # audio
    voice_mix=CompositeAudioClip(audio_clips).volumex(VOICE_VOLUME)

    if os.path.exists(MUSIC):

        music=(AudioFileClip(MUSIC)
               .volumex(MUSIC_BASE)
               .audio_fadein(1.5)
               .audio_fadeout(1.5)
               .subclip(0,final.duration))

        music=apply_duck(music,speaking_windows).volumex(MUSIC_FINAL)

        final_audio=CompositeAudioClip([music,voice_mix])

    else:
        final_audio=voice_mix

    final=final.set_audio(final_audio)

    # export video
    final.write_videofile(f"{OUTDIR}/reel.mp4",fps=30,audio_codec="aac")

    # thumbnail
    make_thumbnail(chosen[0],f"{OUTDIR}/thumbnail.jpg")

    # caption
    make_caption(chosen,f"{OUTDIR}/caption.txt")

# ==============================
# THUMBNAIL
# ==============================

def make_thumbnail(line,path):
    text=" ".join(line.split()[:2])

    img=Image.new("RGB",(1080,1920),(0,0,0))
    d=ImageDraw.Draw(img)
    font=ImageFont.truetype(FONT_PATH,200)

    box=d.textbbox((0,0),text,font=font)
    x=(1080-(box[2]-box[0]))//2
    y=(1920-(box[3]-box[1]))//2

    d.text((x+6,y+6),text,font=font,fill=(0,0,0))
    d.text((x,y),text,font=font,fill="white")

    img.save(path)

# ==============================
# CAPTION
# ==============================

def make_caption(lines,path):
    cap=" • ".join(lines[:2]).title()
    tags=" ".join(random.sample(HASHTAGS,4))

    with open(path,"w") as f:
        f.write(cap+"\n\n"+tags)

# ==============================
# RUN
# ==============================

if __name__=="__main__":
    make()
