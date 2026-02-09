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

def make_thumbnail(hook):

    words=hook.split()[:2]
    text=" ".join(words)

    img=Image.new("RGB",(1080,1920),(0,0,0))
    d=ImageDraw.Draw(img)
    font=ImageFont.truetype(FONT_PATH,180)

    box=d.textbbox((0,0),text,font=font)
    w=box[2]-box[0]
    h=box[3]-box[1]

    x=(1080-w)//2
    y=900-h//2

    d.text((x+8,y+8),text,font=font,fill=(0,0,0))
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
    final=CompositeVideoClip([final,grain])

    # ---------- AUTO DUCK AUDIO MIX ----------

voice_mix = CompositeAudioClip(audio_clips).volumex(2.2)

music = (
    AudioFileClip(MUSIC)
    .volumex(0.25)
    .audio_fadein(1.5)
    .audio_fadeout(1.5)
    .subclip(0,t)
)

# AUTO DUCK
def duck(get_frame, tt):
    speaking = any(
        (tt >= a.start and tt <= a.end)
        for a in audio_clips
    )
    factor = 0.25 if speaking else 1.0
    return get_frame(tt) * factor

music = music.fl(duck)

final = final.set_audio(
    CompositeAudioClip([
        music.volumex(0.6),
        voice_mix
    ])
)


        # ---------- EXPORTS ----------
    make_thumbnail(chosen[0])
    make_caption(chosen)

    final.write_videofile(
        "reel.mp4",
        fps=30,
        codec="libx264",
        audio_codec="aac"
    )

make()

