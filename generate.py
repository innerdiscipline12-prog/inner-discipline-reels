import random, json, os, asyncio
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

SAFE_TOP=350
SAFE_BOTTOM=450
SAFE_H=H-SAFE_TOP-SAFE_BOTTOM

# ---------- SCRIPT BANK ----------

LINES=[
"YOU WAIT FOR MOTIVATION",
"COMFORT IS THE ENEMY",
"NO ONE IS COMING",
"DISCIPLINE DECIDES",
"CONTROL YOURSELF",
"PROVE IT QUIETLY",
"STOP NEGOTIATING",
"DO THE HARD THING",
"EXECUTE ANYWAY",
"CONSISTENCY BUILDS POWER",
"SHOW UP AGAIN",
"FOCUS IS A DECISION",
"COMFORT LIES",
"PAIN TEACHES",
"SILENCE BUILDS STRENGTH",
"EXECUTION WINS",
"HARD BUILDS YOU",
"DISCIPLINE IS IDENTITY",
"SELF CONTROL IS POWER",
"RESULTS NEED STANDARDS",
"WORK WITHOUT MOOD",
"PROVE IT DAILY",
"THIS IS DISCIPLINE"
]

HOOKS=[
"NO ONE IS COMING",
"MOST QUIT EARLY",
"YOUR COMFORT COSTS",
"YOU KNOW THE TRUTH",
"THIS IS DISCIPLINE"
]

HASHTAGS=[
"#discipline",
"#selfcontrol",
"#consistency",
"#innerdiscipline",
"#mentaltoughness",
"#focus",
"#successmindset",
"#personaldevelopment"
]

# ---------- WEIGHTS ----------

weights={
"DISCIPLINE DECIDES":3,
"CONTROL YOURSELF":3,
"PROVE IT QUIETLY":3,
"COMFORT IS THE ENEMY":2,
"STOP NEGOTIATING":2,
"DO THE HARD THING":2
}

# ---------- MEMORY ----------

weighted_pool=[]
for line in LINES:
    w=weights.get(line,1)
    weighted_pool.extend([line]*w)

MEM="memory.json"

if os.path.exists(MEM):
    used=json.load(open(MEM))
else:
    used=[]

available=[l for l in weighted_pool if l not in used]

if len(available)<4:
    used=[]
    available=weighted_pool.copy()

chosen=random.sample(available,4)

# force strong hook
chosen[0]=random.choice(HOOKS)

used+=chosen
json.dump(used,open(MEM,"w"))

# ---------- TEXT RENDER ----------

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

    if len(lines)>2:
        lines=[lines[0]," ".join(lines[1:])]

    hs=[]
    for l in lines:
        b=d.textbbox((0,0),l,font=font)
        hs.append(b[3]-b[1])

    total=sum(hs)+25*(len(lines)-1)
    y=SAFE_TOP+(SAFE_H-total)//2+40

    for i,l in enumerate(lines):
        b=d.textbbox((0,0),l,font=font)
        x=(W-(b[2]-b[0]))//2

        d.text((x+4,y+4),l,font=font,fill=(0,0,0,200))
        d.text((x,y),l,font=font,fill="white")

        y+=hs[i]+25

    return np.array(img)

# ---------- THUMBNAIL (2-WORD HOOK) ----------

def make_thumbnail(text):

    words = text.split()[:2]
    text = " ".join(words)

    img = Image.new("RGB",(1080,1920),(0,0,0))
    d = ImageDraw.Draw(img)

    font = ImageFont.truetype(FONT_PATH,180)

    MAX_W = int(1080*0.85)

    # auto fit size
    while True:
        box = d.textbbox((0,0),text,font=font)
        w = box[2]-box[0]
        h = box[3]-box[1]

        if w <= MAX_W:
            break
        font = ImageFont.truetype(FONT_PATH,font.size-5)

    x = (1080-w)//2
    y = (1920-h)//2

    # shadow
    d.text((x+10,y+10),text,font=font,fill=(0,0,0))

    # main text
    d.text((x,y),text,font=font,fill="white")

    img.save("thumbnail.jpg")


# ---------- CAPTION ----------

def make_caption(lines):

    cap=" ".join(lines[:2]).title()+". Stay disciplined."
    tags=" ".join(random.sample(HASHTAGS,4))

    with open("caption.txt","w") as f:
        f.write(cap+"\n\n"+tags)

# ---------- VIDEO ----------

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

    async def make_line_voice(line,file):
        communicate=edge_tts.Communicate(
            line,
            voice="en-US-ChristopherNeural",
rate="-45%",
pitch="-30Hz"

        )
        await communicate.save(file)

    for i,line in enumerate(chosen):

        vf=f"v{i}.mp3"
        asyncio.run(make_line_voice(line,vf))

        audio=AudioFileClip(vf)
        dur=audio.duration+0.5

        img=frame(line)

        clip=(ImageClip(img)
              .set_start(t)
              .set_duration(dur)
              .fadein(0.3)
              .fadeout(0.3))

        clips.append(clip)
        audio_clips.append(audio.set_start(t))

        t+=dur

    final=CompositeVideoClip([base]+clips).subclip(0,t)

    noise=np.random.randint(0,15,(H,W,3)).astype("uint8")
    grain=ImageClip(noise).set_duration(t).set_opacity(0.03)
import random, json, os, asyncio
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

SAFE_TOP=350
SAFE_BOTTOM=450
SAFE_H=H-SAFE_TOP-SAFE_BOTTOM

# ---------- SCRIPT POOL ----------

LINES=[
"YOU WAIT FOR MOTIVATION",
"COMFORT IS THE ENEMY",
"NO ONE IS COMING",
"DISCIPLINE DECIDES",
"CONTROL YOURSELF",
"PROVE IT QUIETLY",
"STOP NEGOTIATING",
"DO THE HARD THING",
"CONSISTENCY BUILDS POWER",
"YOUR HABITS EXPOSE YOU",
"STANDARDS OVER FEELINGS",
"SILENT WORK WINS",
"CONTROL YOUR IMPULSES",
"EXECUTION BUILDS RESPECT",
"THIS IS DISCIPLINE"
]

HASHTAGS=[
"#discipline","#selfcontrol","#mindset",
"#consistency","#innerdiscipline",
"#focus","#mentalstrength"
]

# ---------- MEMORY ----------

MEM="memory.json"
used=json.load(open(MEM)) if os.path.exists(MEM) else []

pool=[l for l in LINES if l not in used]
if len(pool)<4:
    used=[]
    pool=LINES.copy()

chosen=random.sample(pool,4)
json.dump(used+chosen,open(MEM,"w"))

# ---------- VOICE ----------

async def make_voice():
    text="... ".join(chosen)+"..."
    tts=edge_tts.Communicate(
        text,
        voice="en-US-ChristopherNeural",
        rate="-30%",
        pitch="-15Hz"
    )
    await tts.save("voice.mp3")

asyncio.run(make_voice())

# ---------- TEXT FRAME ----------

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

    if len(lines)>2:
        lines=[lines[0]," ".join(lines[1:])]

    hs=[]
    for l in lines:
        b=d.textbbox((0,0),l,font=font)
        hs.append(b[3]-b[1])

    total=sum(hs)+25*(len(lines)-1)
    y=SAFE_TOP+(SAFE_H-total)//2+40

    for i,l in enumerate(lines):
        b=d.textbbox((0,0),l,font=font)
        x=(W-(b[2]-b[0]))//2
        d.text((x+4,y+4),l,font=font,fill=(0,0,0,200))
        d.text((x,y),l,font=font,fill="white")
        y+=hs[i]+25

    return np.array(img)

# ---------- THUMBNAIL ----------

def make_thumbnail(text):
    words=text.split()[:2]
    text=" ".join(words)

    img=Image.new("RGB",(1080,1920),(0,0,0))
    d=ImageDraw.Draw(img)
    font=ImageFont.truetype(FONT_PATH,200)

    box=d.textbbox((0,0),text,font=font)
    w=box[2]-box[0]
    h=box[3]-box[1]

    x=(1080-w)//2
    y=(1920-h)//2

    d.text((x+8,y+8),text,font=font,fill=(0,0,0))
    d.text((x,y),text,font=font,fill="white")

    img.save("thumbnail.jpg")

# ---------- CAPTION ----------

def make_caption(lines):
    cap=" ".join(lines[:2]).title()
    tags=" ".join(random.sample(HASHTAGS,4))
    with open("caption.txt","w") as f:
        f.write(cap+"\n\n"+tags)

# ---------- VIDEO ----------

def make():

    base=VideoFileClip(VIDEO).without_audio()
    base=base.fx(resize,lambda t:1+0.015*t)
    base=base.resize(height=H)

    if base.w<W:
        base=base.resize(width=W)

    base=base.crop(x_center=base.w/2,y_center=base.h/2,width=W,height=H)

    clips=[]; t=0

    for line in chosen:
        img=frame(line)
        c=(ImageClip(img)
           .set_start(t)
           .set_duration(3.5)
           .fadein(0.3)
           .fadeout(0.3))
        clips.append(c)
        t+=3.5

    final=CompositeVideoClip([base]+clips).subclip(0,14)

    # grain
    noise=np.random.randint(0,15,(H,W,3)).astype("uint8")
    grain=ImageClip(noise).set_duration(14).set_opacity(0.03)
    final=CompositeVideoClip([final,grain])

    # audio
    voice=AudioFileClip("voice.mp3").volumex(1.8)
    music=AudioFileClip(MUSIC).volumex(0.08).subclip(0,14)

    final=final.set_audio(CompositeAudioClip([music,voice]))

    final.write_videofile("reel.mp4",fps=30)

    make_thumbnail(chosen[0])
    make_caption(chosen)

make()

