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
VOICE_RATE="-25%"
VOICE_PITCH="-5Hz"

REEL_BACKGROUNDS = glob.glob("bg*.mp4")
REELS_PER_RUN = 5

# ===== COPY BANK =====
HOOK = [
"You’re not tired. You’re undisciplined.",
"No one is coming to save you.",
"You don’t lack time. You lack control.",
"Comfort is ruining your future.",
"Your habits expose you."
]

TRUTH = [
"Discipline decides outcomes.",
"Control beats motivation.",
"Consistency builds identity.",
"Comfort is expensive.",
"Weak habits create hard lives."
]

CTA = [
"Still here?",
"Day 7. Still disciplined?",
"Comment DISCIPLINE.",
"Day 1 or Day 100?"
]

# ===== TTS =====
async def tts(text,path):
    c=edge_tts.Communicate(text,voice=VOICE,rate=VOICE_RATE,pitch=VOICE_PITCH)
    await c.save(path)

def run_tts(t,p):
    asyncio.run(tts(t,p))

# ===== TEXT IMAGE =====
def text_img(text):
    img=Image.new("RGB",(W,H),(0,0,0))
    d=ImageDraw.Draw(img)

    size=110
    font=ImageFont.truetype(FONT_PATH,size)

    words=text.split()
    mid=len(words)//2
    text=" ".join(words[:mid])+"\n"+" ".join(words[mid:])

    box=d.multiline_textbbox((0,0),text,font=font,spacing=12)
    x=(W-(box[2]-box[0]))//2
    y=(H-(box[3]-box[1]))//2

    d.multiline_text((x,y),text,font=font,fill="white",align="center",spacing=12)

    return np.array(img)

# ===== SCRIPT BUILDER =====
def build_script():
    return [
        random.choice(HOOK),
        random.choice(TRUTH),
        random.choice(CTA)
    ]

# ===== RANDOM BACKGROUND SEGMENT =====
def random_bg(duration):
    bg=random.choice(REEL_BACKGROUNDS)
    clip=VideoFileClip(bg).without_audio()

    if clip.duration > duration+1:
        start=random.uniform(0, clip.duration-duration-0.5)
    else:
        start=0

    clip=clip.subclip(start,start+duration)
    clip=clip.resize(height=H).crop(width=W,height=H)

    return clip

# ===== BUILD REEL =====
def make_reel(i):

    os.makedirs("outputs",exist_ok=True)

    script=build_script()

    audio=[]
    text_clips=[]
    t=0

    # ---- FIRST PASS: AUDIO + TEXT ----
    for n,line in enumerate(script):

        tmp=f"tmp{n}.mp3"
        run_tts(line,tmp)

        a=AudioFileClip(tmp)

        dur=a.duration+0.4   # <<< KEY FIX

        img=text_img(line)

        txt=(ImageClip(img)
             .set_start(t)
             .set_duration(dur)
             .fadein(.15)
             .fadeout(.15))

        text_clips.append(txt)
        audio.append(a.set_start(t+.1))

        t+=dur
        os.remove(tmp)

    final_len=max(7,min(t,12))  # keep 7–12s

    base=random_bg(final_len)

    final=CompositeVideoClip([base]+text_clips).subclip(0,final_len)

    voice=CompositeAudioClip(audio)

    if os.path.exists(MUSIC):
        m=AudioFileClip(MUSIC).audio_loop(duration=final_len).volumex(.08)
        final=final.set_audio(CompositeAudioClip([m,voice]))
    else:
        final=final.set_audio(voice)

    final.write_videofile(f"outputs/reel_{i}.mp4",fps=30)

# ===== RUN =====
for i in range(REELS_PER_RUN):
    make_reel(i)

print("✅ REEL MASTER COMPLETE")
