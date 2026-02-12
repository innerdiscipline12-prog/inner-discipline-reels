import os, json, random, asyncio, glob
import numpy as np
from moviepy.editor import *
from moviepy.video.fx.all import resize
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ================= SETTINGS =================

# ===== AUTO DETECT BACKGROUNDS =====

REEL_BACKGROUNDS = glob.glob("bg*.mp4")
LONG_BACKGROUNDS = glob.glob("bg_long*.mp4")

if not REEL_BACKGROUNDS:
    raise Exception("No reel backgrounds found (bg*.mp4)")

if not LONG_BACKGROUNDS:
    raise Exception("No long backgrounds found (bg_long*.mp4)")

VIDEO = random.choice(REEL_BACKGROUNDS)
LONG_VIDEO = random.choice(LONG_BACKGROUNDS)

MUSIC="music.mp3"   # optional
FONT_PATH="Anton-Regular.ttf"

W,H=1080,1920
REELS_PER_RUN=5

VOICE="en-US-ChristopherNeural"
VOICE_RATE="-35%"
VOICE_PITCH="-20Hz"

HASHTAGS=[
"#discipline","#selfcontrol","#focus",
"#mindset","#innerdiscipline",
"#consistency","#stoic","#growth"
]

# ================= LINES =================

LINES={
"NO ONE CARES ABOUT EXCUSES":3,
"COMFORT IS A TRAP":3,
"YOU AVOID HARD TRUTH":3,
"DISCIPLINE FEELS LONELY":3,
"WEAKNESS SEEKS COMFORT":3,
"YOU DELAY YOUR LIFE":3,
"COMFORT IS COSTLY":3,
"YOU KNOW YOU SHOULD":3,
"DISCIPLINE HURTS FIRST":3,
"COMFORT HURTS LONGER":3,

"YOU CHOOSE EASY":3,
"EFFORT REVEALS YOU":3,
"YOU HIDE IN COMFORT":3,
"YOUR HABITS EXPOSE YOU":3,
"EXCUSES ARE DECISIONS":3,
"YOU KNOW THE PROBLEM":3,
"DISCIPLINE DEMANDS SILENCE":3,
"NO ONE OWES YOU":3,
"YOU WASTE TIME":3,
"YOU AVOID EFFORT":3,

"DISCIPLINE IS ISOLATING":3,
"COMFORT BUILDS REGRET":3,
"YOU LACK STRUCTURE":3,
"YOU CHOOSE DISTRACTION":3,
"YOUR ACTIONS SHOW":3,
"COMFORT IS ADDICTIVE":3,
"YOU FEAR DISCOMFORT":3,
"DISCIPLINE IS SACRIFICE":3,
"YOU RESIST GROWTH":3,
"WEAK HABITS SHOW":3,

"YOU KNOW BETTER":3,
"DISCIPLINE REQUIRES LOSS":3,
"COMFORT KILLS PROGRESS":3,
"YOU CHOOSE SHORTCUTS":3,
"YOU BREAK PROMISES":3,
"YOU LIE TO YOURSELF":3,
"RESULTS SEE TRUTH":3,
"YOU LACK CONTROL":3,
"DISCIPLINE DEMANDS MORE":3,
"COMFORT IS WEAKNESS":3,

"YOU ESCAPE EFFORT":3,
"YOUR STANDARD IS LOW":3,
"YOU AVOID PAIN":3,
"DISCIPLINE IS HARD":3,
"YOU SEEK EASY":3,
"COMFORT IS A LIE":3,
"YOU KNOW THE WORK":3,
"DISCIPLINE ISN'T FUN":3,
"YOU WANT EASY WINS":3,
"COMFORT FEELS SAFE":3,

"YOU DELAY CHANGE":3,
"DISCIPLINE IS TRUTH":3,
"YOU HIDE FROM WORK":3,
"YOUR ROUTINE SHOWS":3,
"YOU CHOOSE SOFT":3,
"DISCIPLINE BUILDS PRESSURE":3,
"COMFORT BUILDS WEAKNESS":3,
"YOU AVOID REALITY":3,
"YOU KNOW THE COST":3,
"DISCIPLINE FEELS COLD":3,

"YOU RESIST ORDER":3,
"COMFORT IS SEDUCTIVE":3,
"YOU BREAK STRUCTURE":3,
"DISCIPLINE IS DEMANDING":3,
"YOU SEEK RELIEF":3,
"COMFORT DELAYS SUCCESS":3,
"YOU KNOW THE TRUTH":3,
"DISCIPLINE REVEALS CHARACTER":3,
"YOU LACK CONSISTENCY":3,
"COMFORT LOVES YOU":3,

"YOU AVOID DISCIPLINE":3,
"YOUR FOCUS IS WEAK":3,
"DISCIPLINE NEEDS SACRIFICE":3,
"YOU CHOOSE PLEASURE":3,
"COMFORT BUILDS LAZINESS":3,
"YOU DODGE EFFORT":3,
"DISCIPLINE DEMANDS ACTION":3,
"YOU KNOW YOU'RE SLIPPING":3,
"COMFORT IS A CAGE":3,
"YOU LACK STANDARDS":3,

"DISCIPLINE IS UNCOMFORTABLE":3,
"YOU WANT SHORTCUTS":3,
"COMFORT DELAYS GROWTH":3,
"YOU HIDE FROM HARD":3,
"DISCIPLINE IS STRICT":3,
"YOU AVOID STRUCTURE":3,
"COMFORT IS TEMPTATION":3,
"YOU BREAK ROUTINE":3,
"DISCIPLINE BUILDS EDGE":3,
"YOU CHOOSE DISTRACTION":3

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

    d.multiline_text((x,y),text,font=font,fill="white",align="center",spacing=30)

    img.save(path)

# ================= CAPTION =================

def make_caption(lines,path):
    cap=" • ".join(lines[:2]).title()
    tags=" ".join(random.sample(HASHTAGS,4))
    with open(path,"w") as f:
        f.write(cap+"\n\n"+tags)

# ================= PICK LINES =================

def pick_lines():
    global used

    pool=[l for l in ALL_LINES if l not in used]

    if len(pool)<3:
        used=[]
        pool=ALL_LINES.copy()

    weights=[LINES[l] for l in pool]
    hook=random.choices(pool,weights=weights,k=1)[0]

    remaining=[l for l in pool if l!=hook]
    others=random.sample(remaining,2)

    chosen=[hook]+others
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

        voice_path=f"{folder}/line{i}.mp3"
        asyncio.run(make_voice(line,voice_path))

        a=AudioFileClip(voice_path)
        dur=a.duration+0.4

        img=frame(line)

        txt=(ImageClip(img)
             .set_start(t)
             .set_duration(dur)
             .fadein(0.3)
             .fadeout(0.3))

        clips.append(txt)

        audio_clips.append(a.set_start(t+0.25))

        t+=dur

    final=CompositeVideoClip([base]+clips).subclip(0,t)

    # LOOP MODE
    final=final.fx(vfx.freeze,t=final.duration-0.4,freeze_duration=0.4)
    final=final.fadeout(0.6)

    voice_mix=CompositeAudioClip(audio_clips)

    # ===== CRASH-PROOF MUSIC =====
    if os.path.exists(MUSIC):
        music = (
            AudioFileClip(MUSIC)
            .audio_loop(duration=t)
            .volumex(0.1)
            .audio_fadeout(1.0)
        )
        final=final.set_audio(CompositeAudioClip([music,voice_mix]))
    else:
        final=final.set_audio(voice_mix)

    final.write_videofile(f"{folder}/reel.mp4",fps=30)

    make_thumbnail(chosen[0],f"{folder}/thumbnail.jpg")
    make_caption(chosen,f"{folder}/caption.txt")
    
# ================= SMART FLOW MASTER LONG VIDEO =================

def make_long_video():

    print("🔥 SMART FLOW — Generating 10-minute deep talk...")

    os.makedirs("outputs", exist_ok=True)

    target_len = 600  # 10 minutes

    # --------- SMART FLOW CATEGORIES ---------
    pain = [l for l in ALL_LINES if "PAIN" in l or "HARD" in l or "STRUGGLE" in l]
    control = [l for l in ALL_LINES if "CONTROL" in l]
    focus = [l for l in ALL_LINES if "FOCUS" in l]
    discipline = [l for l in ALL_LINES if "DISCIPLINE" in l]
    identity = [l for l in ALL_LINES if "IDENTITY" in l or "SELF" in l]

    def pick(pool, n):
        if len(pool) >= n:
            return random.sample(pool, n)
        return random.sample(ALL_LINES, n)

    # --------- SCRIPT FLOW ---------
    hook = random.choice([
        "Discipline is doing what you avoid.",
        "Your comfort is costing your future.",
        "No one is coming to save you.",
        "Your habits decide your life."
    ])

    lines = (
        [hook] +
        pick(pain,5) +
        pick(focus,5) +
        pick(control,5) +
        pick(discipline,5) +
        pick(identity,5)
    )

    # --------- BASE VIDEO ---------
    base = VideoFileClip(LONG_VIDEO).without_audio()
    # ===== LONG VIDEO LANDSCAPE SIZE =====
LW, LH = 1280, 720

base = base.fx(resize, lambda t:1+0.002*t).resize(height=LH)

if base.w < LW:
    base = base.resize(width=LW)

base = base.crop(
    x_center=base.w/2,
    y_center=base.h/2,
    width=LW,
    height=LH
)


clips = []
audio = []
timestamps = []
t = 0
idx = 0


    # --------- BUILD TIMELINE ---------
    while t < target_len:

    line = random.choice(lines)

    vp=f"outputs/long_{idx}.mp3"
    asyncio.run(make_voice(line, vp))

    a=AudioFileClip(vp)

    dur=max(6, a.duration+1.2)

    timestamps.append(
        f"{int(t//60)}:{int(t%60):02d} {line.title()}"
    )

    img=frame(line)

    txt=(
        ImageClip(img)
        .set_start(t)
        .set_duration(dur)
        .fadein(0.8)
        .fadeout(0.8)
    )

    clips.append(txt)
    audio.append(a.set_start(t+0.4))

    t+=dur
    idx+=1


    final=CompositeVideoClip([base]+clips).subclip(0,t)

    voice_mix=CompositeAudioClip(audio)

    # --------- MUSIC ---------
    if os.path.exists(MUSIC):
        music=(
            AudioFileClip(MUSIC)
            .audio_loop(duration=t)
            .volumex(0.05)
            .audio_fadeout(3)
        )
        final=final.set_audio(
            CompositeAudioClip([music,voice_mix])
        )
    else:
        final=final.set_audio(voice_mix)

    # --------- EXPORT VIDEO ---------
    final.write_videofile(
        "outputs/long_video.mp4",
        fps=30
    )

    # --------- SEO TITLE ---------
    title=random.choice([
        "10 Minutes to Build Discipline",
        "Deep Discipline Talk for Focus",
        "Control Your Mind — Discipline Talk",
        "Build Self-Control & Focus (10 Min)"
    ])

    open("outputs/long_title.txt","w").write(title)

    # --------- SEO DESCRIPTION ---------
    desc=f"""
Build discipline, self-control and focus.

This deep 10-minute talk trains your mindset
to develop structure, habits and standards.

Discipline is built daily.

CHAPTERS:
{chr(10).join(timestamps)}

#discipline #selfcontrol #focus #mindset
"""

    open("outputs/long_description.txt","w").write(desc)

    # --------- YOUTUBE THUMBNAIL ---------
    thumb=Image.new("RGB",(1280,720),(0,0,0))
    d=ImageDraw.Draw(thumb)

    text=random.choice([
        "DISCIPLINE\nBUILDS YOU",
        "CONTROL\nYOURSELF",
        "NO EXCUSES\nONLY WORK",
        "BUILD\nSELF CONTROL"
    ])

    font=ImageFont.truetype(FONT_PATH,120)

    box=d.multiline_textbbox((0,0),text,font=font,spacing=20)

    x=(1280-(box[2]-box[0]))//2
    y=(720-(box[3]-box[1]))//2

    d.multiline_text(
        (x,y),
        text,
        font=font,
        fill="white",
        align="center",
        spacing=20
    )

    thumb.save("outputs/long_thumbnail.jpg")

    print("✅ SMART FLOW LONG VIDEO COMPLETE")

# ================= RUN =================

os.makedirs("outputs",exist_ok=True)

for i in range(1,REELS_PER_RUN+1):
    make_reel(i)
    
make_long_video()

json.dump(used,open(MEM,"w"))

print("🔥 MASTER V6 COMPLETE")
