import os, random, asyncio, glob
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import edge_tts

# ===== SETTINGS =====
LW,LH=1280,720
FONT_PATH="Anton-Regular.ttf"
MUSIC="music.mp3"

VOICE="en-US-ChristopherNeural"
VOICE_RATE="-25%"
VOICE_PITCH="-5Hz"

LONG_BACKGROUNDS=glob.glob("bg_long*.mp4")

TARGET=600

# ===== COPY =====
LINES=[
"Discipline is built in silence.",
"You become what you repeat.",
"Comfort delays your future.",
"Control your inputs.",
"Your habits decide your life.",
"Small wins build identity.",
"Consistency beats intensity.",
"Focus creates freedom.",
"Standards create strength.",
"You already know what to do."
]

# ===== TTS =====
async def tts(t,p):
    c=edge_tts.Communicate(t,voice=VOICE,rate=VOICE_RATE,pitch=VOICE_PITCH)
    await c.save(p)

def run_tts(t,p): asyncio.run(tts(t,p))

# ===== TEXT IMAGE =====
def txtimg(text):
    img=Image.new("RGB",(LW,LH),(0,0,0))
    d=ImageDraw.Draw(img)
    font=ImageFont.truetype(FONT_PATH,70)

    box=d.textbbox((0,0),text,font=font)
    x=(LW-(box[2]-box[0]))//2
    y=(LH-(box[3]-box[1]))//2

    d.text((x,y),text,font=font,fill="white")
    return np.array(img)

# ===== BUILD =====
bg=random.choice(LONG_BACKGROUNDS)
base=VideoFileClip(bg).without_audio().fx(vfx.loop,duration=TARGET).resize((LW,LH))

clips=[]
aud=[]
t=0
i=0

while t<TARGET:
    line=random.choice(LINES)
    tmp=f"long{i}.mp3"
    run_tts(line,tmp)

    a=AudioFileClip(tmp)

    dur=6.0
    img=txtimg(line)

    txt=ImageClip(img).set_start(t).set_duration(dur).fadein(.5).fadeout(.5)

    clips.append(txt)
    aud.append(a.set_start(t+.3))
    t+=dur
    i+=1
    os.remove(tmp)

final=CompositeVideoClip([base]+clips).subclip(0,TARGET)

voice=CompositeAudioClip(aud)

if os.path.exists(MUSIC):
    m=AudioFileClip(MUSIC).audio_loop(duration=TARGET).volumex(.05)
    final=final.set_audio(CompositeAudioClip([m,voice]))
else:
    final=final.set_audio(voice)

final.write_videofile("long_video.mp4",fps=30)

print("✅ 10-minute hybrid done")
