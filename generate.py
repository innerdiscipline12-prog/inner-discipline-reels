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
REELS_PER_RUN=5

VOICE="en-US-ChristopherNeural"
VOICE_RATE="-35%"
VOICE_PITCH="-20Hz"

LONG_MODE=True
LONG_SECONDS=300

HASHTAGS=[
"#discipline","#selfcontrol","#focus",
"#mindset","#innerdiscipline",
"#consistency","#stoic","#growth"
]

YT_TITLE_TEMPLATES=[
"Discipline Will Change Your Life",
"Watch This If You Lack Discipline",
"5 Minutes That Will Make You Disciplined",
"Build Self Control With This Video",
"Focus & Discipline Motivation"
]

# ================= LINES =================

LINES={
"NO ONE IS COMING":5,
"COMFORT IS THE ENEMY":5,
"STOP NEGOTIATING":5,
"DO THE HARD THING":5,
"DISCIPLINE IS LONELY":5,
"DISCIPLINE DECIDES":4,
"CONTROL YOURSELF":4,
"PROVE IT QUIETLY":4,
"STANDARDS STAY":4,
"BUILD SILENT HABITS":3,
"RESULTS NEED STANDARDS":3,
"FOCUS BUILDS POWER":3,
"REMOVE EXCUSES":3,
"STAY CONSISTENT":3,
"EXECUTE DAILY":2,
"BE RELENTLESS":2,
"STAY FOCUSED":2,
"KEEP GOING":2
}

ALL_LINES=list(LINES.keys())

LONG_LINES=[
"Discipline is built quietly.",
"No one applauds the repetition.",
"But results remember.",
"",
"Motivation fades.",
"Standards stay.",
"",
"You fall to your systems.",
"",
"Comfort is expensive.",
"Growth is earned.",
"",
"Control your inputs.",
"Control your life.",
"",
"Daily discipline compounds."
]

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
    img=Image.new("RGBA",(W,H),(0,0,0,0))
    d=ImageDraw.Draw(img)

    words=text.split()
    if len(words)>=2:
        mid=len(words)//2
        text=" ".join(words[:mid])+"\n"+" ".join(words[mid:])

    font=ImageFont.truetype(FONT_PATH,140)

    box=d.multiline_textbbox((0,0),text,font=font,spacing=20)
    tw=box[2]-box[0]
    th=box[3]-box[1]

    x=(W-tw)//2
    y=int(H*0.55 - th/2)

    d.multiline_text((x+6,y+6),text,font=font,fill=(0,0,0,180),align="center",spacing=20)
    d.multiline_text((x,y),text,font=font,fill="white",align="center",spacing=20)

    return np.array(img)

# ================= THUMBNAIL =================

def make_thumbnail(text,path):
    img=Image.new("RGB",(1080,1920),(0,0,0))
    d=ImageDraw.Draw(img)

    words=text.split()
    if len(words)>=2:
        text=words[0]+"\n"+words[1]

    font=ImageFont.truetype(FONT_PATH,200)

    box=d.multiline_textbbox((0,0),text,font=font,spacing=30)
    x=(1080-(box[2]-box[0]))//2
    y=(1920-(box[3]-box[1]))//2

    d.multiline_text((x+8,y+8),text,font=font,fill=(0,0,0))
    d.multiline_text((x,y),text,font=font,fill="white")

    img.save(path)

# ================= CAPTION =================

def make_caption(lines,path):
    cap=" • ".join(lines[:2]).title()
    tags=" ".join(random.sample(HASHTAGS,4))
    with open(path,"w") as f:
        f.write(cap+"\n\n"+tags)

# ================= YOUTUBE SEO =================

def make_youtube_metadata(folder):

    title=random.choice(YT_TITLE_TEMPLATES)

    desc=f"""
Discipline is built daily.

If you want stronger habits, focus and self-control — start now.

INNER DISCIPLINE

{ ' '.join(HASHTAGS) }
"""

    with open(f"{folder}/youtube_title.txt","w") as f:
        f.write(title)

    with open(f"{folder}/youtube_description.txt","w") as f:
        f.write(desc.strip())

# ================= PICK LINES =================

def pick_lines():
    global used

    pool=[l for l in ALL_LINES if l not in used]

    if len(pool)<3:
        used=[]
        pool=ALL_LINES.copy()

    weights=[LINES[l] for l in pool]
    chosen=random.choices(pool,weights=weights,k=3)

    used+=chosen
    return chosen

# ================= BUILD REEL =================

def make_reel(idx):

    folder=f"outputs/{idx:02d}"
    os.makedirs(folder,exist_ok=True)

    chosen=pick_lines()

    base=VideoFileClip(VIDEO).without_audio()
    base=base.fx(resize,lambda t:1+0.008*t).resize(height=H)

    if base.w<W:
        base=base.resize(width=W)

    base=base.crop(x_center=base.w/2,y_center=base.h/2,width=W,height=H)

    clips=[]
    audio_clips=[]
    t=0

    for i,line in enumerate(chosen):

        vp=f"{folder}/line{i}.mp3"
        asyncio.run(make_voice(line,vp))

        a=AudioFileClip(vp)
        dur=a.duration+0.4

        txt=(ImageClip(frame(line))
             .set_start(t)
             .set_duration(dur)
             .fadein(0.3)
             .fadeout(0.3))

        clips.append(txt)
        audio_clips.append(a.set_start(t+0.25))

        t+=dur

    final=CompositeVideoClip([base]+clips).subclip(0,t)

    voice_mix=CompositeAudioClip(audio_clips)

    if os.path.exists(MUSIC):
        music=AudioFileClip(MUSIC).volumex(0.1).subclip(0,t)
        final=final.set_audio(CompositeAudioClip([music,voice_mix]))
    else:
        final=final.set_audio(voice_mix)

    final.write_videofile(f"{folder}/reel.mp4",fps=30)

    make_thumbnail(chosen[0],f"{folder}/thumbnail.jpg")
    make_caption(chosen,f"{folder}/caption.txt")

# ================= LONG VIDEO =================

def make_long_video():

    folder="outputs/long"
    os.makedirs(folder,exist_ok=True)

    base=VideoFileClip(VIDEO).loop(duration=LONG_SECONDS).without_audio()

    t=0
    clips=[]
    audio=[]

    for i,line in enumerate(LONG_LINES):

        if not line.strip():
            t+=1
            continue

        vp=f"{folder}/long{i}.mp3"
        asyncio.run(make_voice(line,vp))

        a=AudioFileClip(vp)
        dur=a.duration+0.5

        txt=(ImageClip(frame(line))
             .set_start(t)
             .set_duration(dur)
             .fadein(0.5)
             .fadeout(0.5))

        clips.append(txt)
        audio.append(a.set_start(t))

        t+=dur
        if t>=LONG_SECONDS:
            break

    final=CompositeVideoClip([base]+clips)

    voice=CompositeAudioClip(audio).volumex(1.5)

    if os.path.exists(MUSIC):
        music=AudioFileClip(MUSIC).volumex(0.12).subclip(0,LONG_SECONDS)
        final=final.set_audio(CompositeAudioClip([music,voice]))
    else:
        final=final.set_audio(voice)

    final.write_videofile(f"{folder}/long_video.mp4",fps=30)

    make_youtube_metadata(folder)

# ================= RUN =================

os.makedirs("outputs",exist_ok=True)

for i in range(1,REELS_PER_RUN+1):
    make_reel(i)

if LONG_MODE:
    make_long_video()

json.dump(used,open(MEM,"w"))

print("🔥 ULTRA SYSTEM COMPLETE")
