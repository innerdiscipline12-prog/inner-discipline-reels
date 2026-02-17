import os, random, asyncio, glob
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import edge_tts

# ===== SETTINGS =====
W,H = 1080,1920
FONT_PATH="Anton-Regular.ttf"
MUSIC="music.mp3"

VOICE="en-US-ChristopherNeural"
VOICE_RATE="-30%"
VOICE_PITCH="-10Hz"

REEL_BACKGROUNDS = glob.glob("bg*.mp4")
REELS_PER_RUN = 5

REEL_MIN_SEC=7
REEL_MAX_SEC=12

# ===== COPY BANK =====
HOOK = [
"You’re not tired. You’re undisciplined.",
"Comfort is ruining your future.",
"No one is coming to save you.",
"You don’t lack time. You lack control.",
"Your habits expose you."
]

TRUTHS = [
"Comfort is expensive.",
"Discipline decides outcomes.",
"Control beats motivation.",
"Consistency builds identity.",
"Weak habits create hard lives."
]

CTA = [
"Still here?",
"Day 7. Still disciplined?",
"Comment DISCIPLINE.",
"Day 1 or Day 100?"
]

# ===== TTS =====
async def tts(text, path):
    c=edge_tts.Communicate(text,voice=VOICE,rate=VOICE_RATE,pitch=VOICE_PITCH)
    await c.save(path)

def run_tts(t,p): asyncio.run(tts(t,p))

# ===== TEXT IMAGE FIT =====
def text_img(text):
    img=Image.new("RGB",(W,H),(0,0,0))
    d=ImageDraw.Draw(img)

    size=110
    font=ImageFont.truetype(FONT_PATH,size)

    words=text.split()
    text="\n".join([" ".join(words[:len(words)//2]),
                    " ".join(words[len(words)//2:])])

    box=d.multiline_textbbox((0,0),text,font=font,spacing=10)
    x=(W-(box[2]-box[0]))//2
    y=(H-(box[3]-box[1]))//2

    d.multiline_text((x,y),text,font=font,fill="white",align="center",spacing=10)
    return np.array(img)

# ===== BUILD =====
def build_script():
    return [
        random.choice(HOOK),
        random.choice(TRUTHS),
        random.choice(CTA)
    ]

def make_reel(i):
    os.makedirs("outputs",exist_ok=True)
    script=build_script()

    bg=random.choice(REEL_BACKGROUNDS)
    base=VideoFileClip(bg).without_audio().resize(height=H).crop(width=W,height=H)

    clips=[]
    aud=[]
    t=0

    for n,line in enumerate(script):
        tmp=f"tmp{n}.mp3"
        run_tts(line,tmp)

        a=AudioFileClip(tmp)

        dur = 2.6 if n==0 else 2.2
        if n==2: dur=3.0

        img=text_img(line)
        txt=ImageClip(img).set_start(t).set_duration(dur).fadein(.15).fadeout(.15)

        clips.append(txt)
        aud.append(a.set_start(t+.1))
        t+=dur
        os.remove(tmp)

    final=CompositeVideoClip([base]+clips).subclip(0,t)

    voice=CompositeAudioClip(aud)
    if os.path.exists(MUSIC):
        m=AudioFileClip(MUSIC).audio_loop(duration=t).volumex(.1)
        final=final.set_audio(CompositeAudioClip([m,voice]))
    else:
        final=final.set_audio(voice)

    final.write_videofile(f"outputs/reel_{i}.mp4",fps=30)

for i in range(REELS_PER_RUN):
    make_reel(i)

print("✅ Reels done")
