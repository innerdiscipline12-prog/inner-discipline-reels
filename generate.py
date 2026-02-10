import os, json, random, asyncio
import numpy as np
from moviepy.editor import *
from moviepy.video.fx.all import resize
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ================= SETTINGS =================

VIDEO="bg.mp4"
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

# ================= HOOK LINES =================

LINES={

# ====== TOP HOOKS (5) ======
"NO ONE IS COMING":5,
"COMFORT IS THE ENEMY":5,
"STOP NEGOTIATING":5,
"DO THE HARD THING":5,
"DISCIPLINE IS LONELY":5,
"YOU KNOW THE ANSWER":5,
"YOU ARE DELAYING":5,
"EXCUSES ARE COMFORT":5,
"COMMIT OR QUIT":5,
"DECIDE AND MOVE":5,
"THIS IS ON YOU":5,
"OWN YOUR LIFE":5,
"YOU CHOSE EASY":5,
"NO RESCUE IS COMING":5,
"YOU WANT COMFORT":5,
"STOP HIDING":5,
"ACT NOW":5,
"YOU FEAR EFFORT":5,
"YOU KNOW BETTER":5,
"THIS IS YOUR FAULT":5,

# ====== STRONG AUTHORITY (4) ======
"DISCIPLINE DECIDES":4,
"CONTROL YOURSELF":4,
"PROVE IT QUIETLY":4,
"STANDARDS STAY":4,
"CONSISTENCY BUILDS POWER":4,
"CONTROL THE MOMENT":4,
"EXECUTION BUILDS RESPECT":4,
"SILENCE BUILDS STRENGTH":4,
"SHOW UP TIRED":4,
"WORK WITHOUT DRAMA":4,
"HOLD YOUR STANDARD":4,
"OWN YOUR ACTIONS":4,
"CONTROL THE DAY":4,
"BE RELIABLE":4,
"DISCIPLINE BUILDS YOU":4,
"RESULTS SHOW TRUTH":4,
"NO COMFORT GROWTH":4,
"DISCIPLINE IS POWER":4,
"STAND FIRM":4,
"DO THE REPS":4,
"SHOW CONTROL":4,
"OWN THE PROCESS":4,
"CONTROL YOUR URGE":4,
"DISCIPLINE OVER FEELINGS":4,
"STRUCTURE CREATES FREEDOM":4,
"FOCUS ON EXECUTION":4,
"STANDARDS OVER MOOD":4,
"NO SHORTCUTS HERE":4,
"MASTER YOURSELF":4,
"LEAD YOURSELF":4,
"OWN YOUR CHOICES":4,
"DISCIPLINE FIRST":4,
"KEEP CONTROL":4,
"BE INTENTIONAL":4,
"CONTROL YOUR TIME":4,
"BUILD QUIETLY":4,
"OWN THE PROCESS DAILY":4,
"NO EXCUSE LEFT":4,
"DISCIPLINE ALWAYS WINS":4,
"CONTROL BEATS EMOTION":4,

# ====== SOLID CORE (3) ======
"BUILD SILENT HABITS":3,
"RESULTS NEED STANDARDS":3,
"FOCUS BUILDS POWER":3,
"REMOVE EXCUSES":3,
"STAY CONSISTENT":3,
"WORK IN SILENCE":3,
"TRAIN YOUR MIND":3,
"REPEAT THE HARD THING":3,
"DISCIPLINE IS A CHOICE":3,
"CONTROL YOUR INPUTS":3,
"WIN THE BORING DAYS":3,
"YOUR ROUTINE EXPOSES YOU":3,
"SMALL WINS MATTER":3,
"BUILD SELF CONTROL":3,
"HABITS DEFINE YOU":3,
"YOUR ACTIONS SPEAK":3,
"DISCIPLINE IS DAILY":3,
"CONTROL YOUR FOCUS":3,
"BE PATIENT":3,
"RESPECT THE PROCESS":3,
"STAY LOCKED IN":3,
"EXECUTE THE PLAN":3,
"DO THE BASICS":3,
"WIN TODAY":3,
"SHOW CHARACTER":3,
"BUILD GRIT":3,
"BE STRUCTURED":3,
"OWN THE MOMENT":3,
"CHOOSE HARD":3,
"RESPECT EFFORT":3,
"DISCIPLINE TAKES TIME":3,
"CONTROL REACTION":3,
"FOCUS ON HABITS":3,
"STAY DELIBERATE":3,
"CONTROL DISTRACTIONS":3,
"BUILD ROUTINE":3,
"TRAIN CONSISTENTLY":3,
"SHOW DISCIPLINE":3,
"OWN STANDARD":3,
"WORK WITH INTENT":3,

# ====== SUPPORT (2) ======
"EXECUTE DAILY":2,
"BE RELENTLESS":2,
"STAY FOCUSED":2,
"KEEP GOING":2,
"MOVE WITH PURPOSE":2,
"OWN YOUR DAY":2,
"NO COMPLAINTS":2,
"TRAIN DAILY":2,
"DO THE WORK":2,
"HOLD THE LINE":2,
"SELF CONTROL WINS":2,
"IGNORE DISTRACTIONS":2,
"KEEP STANDARDS HIGH":2,
"STAY SHARP":2,
"LOCK IN":2,
"BE CONSISTENT":2,
"KEEP MOVING":2,
"WORK QUIETLY":2,
"BE PRESENT":2,
"TRUST THE WORK":2,
"CONTROL RESPONSE":2,
"BUILD FOCUS":2,
"STAY STEADY":2,
"BE COMPOSED":2,
"STAY READY":2,
"WORK HARD":2,
"KEEP PUSHING":2,
"OWN RESULTS":2,
"SHOW UP":2,
"BUILD DAILY":2,
"CONTROL HABITS":2,
"TRAIN FOCUS":2,
"BE SERIOUS":2,
"CONTROL MIND":2,
"STAY DISCIPLINED":2,
"OWN IT":2,
"DO BETTER":2,
"BE STRONG":2,
"STAY ON TASK":2,
"CONTROL DAY":2,
"OWN CONTROL":2,
"BUILD HABITS":2,
"STAY COMMITTED":2,
"KEEP STRUCTURE":2,
"OWN DECISIONS":2,
"STAY STRUCTURED":2,
"WORK STEADY":2,
"CONTROL SELF":2,
"BUILD STRENGTH":2,
"WORK SILENT":2,
"DISCIPLINE DAILY":2,
"OWN PROGRESS":2,
"BUILD PATIENCE":2,
"SHOW COMMITMENT":2
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

    d.multiline_text((x+8,y+8),text,font=font,fill=(0,0,0),align="center",spacing=30)
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

    if os.path.exists(MUSIC):
        music=AudioFileClip(MUSIC).volumex(0.1).subclip(0,t)
        final=final.set_audio(CompositeAudioClip([music,voice_mix]))
    else:
        final=final.set_audio(voice_mix)

    final.write_videofile(f"{folder}/reel.mp4",fps=30)

    make_thumbnail(chosen[0],f"{folder}/thumbnail.jpg")
    make_caption(chosen,f"{folder}/caption.txt")

# ================= RUN =================

os.makedirs("outputs",exist_ok=True)

for i in range(1,REELS_PER_RUN+1):
    make_reel(i)

json.dump(used,open(MEM,"w"))

print("🔥 ULTRA SYNC COMPLETE")
