import os, random, asyncio, glob
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import edge_tts

# ===== SETTINGS =====
LW,LH = 1280,720
FONT="Anton-Regular.ttf"
MUSIC="music.mp3"

VOICE="en-US-ChristopherNeural"

BACKGROUNDS = glob.glob("bg_long*.mp4")

TARGET_LEN = 600  # 10 minutes

# ===== COPY BANK =====
LINES = [
"Discipline is built daily.",
"Comfort delays your future.",
"You already know what to do.",
"Consistency creates identity.",
"Control your inputs.",
"Focus is a skill.",
"Your habits decide your life.",
"Standards create discipline.",
"Still here?",
"Day 7. Still disciplined?",
]

# ===== TTS =====
async def tts(text,path):
    c=edge_tts.Communicate(text,voice=VOICE)
    await c.save(path)

def run_tts(t,p):
    asyncio.run(tts(t,p))

# ===== TEXT FRAME =====
def frame(text):
    img=Image.new("RGB",(LW,LH),(0,0,0))
    d=ImageDraw.Draw(img)

    font=ImageFont.truetype(FONT,70)

    words=text.split()
    mid=len(words)//2
    text=" ".join(words[:mid])+"\n"+" ".join(words[mid:])

    box=d.multiline_textbbox((0,0),text,font=font,spacing=10)

    x=(LW-(box[2]-box[0]))//2
    y=(LH-(box[3]-box[1]))//2

    d.multiline_text((x,y),text,font=font,fill="white",
                     align="center",spacing=10)

    return np.array(img)

# ===== RANDOM BG LOOP =====
def random_bg(duration):
    bg=random.choice(BACKGROUNDS)
    clip=VideoFileClip(bg).without_audio()

    if clip.duration < duration:
        clip=clip.loop(duration=duration)
    else:
        start=random.uniform(0,clip.duration-duration)
        clip=clip.subclip(start,start+duration)

    clip=clip.resize(height=LH)

    return clip.crop(width=LW,height=LH)

# ===== BUILD LONG VIDEO =====
def build():

    os.makedirs("outputs",exist_ok=True)

    audio=[]
    visuals=[]

    t=0
    i=0

    while t < TARGET_LEN:

        line=random.choice(LINES)

        tmp=f"tmp{i}.mp3"
        run_tts(line,tmp)

        a=AudioFileClip(tmp)

        # question pause feels like a question
        if "?" in line:
            dur=a.duration+1.2
        else:
            dur=a.duration+0.6

        img=frame(line)

        txt=(ImageClip(img)
            .set_start(t)
            .set_duration(dur)
            .fadein(.5)
            .fadeout(.5))

        visuals.append(txt)
        audio.append(a.set_start(t+.2))

        t+=dur
        os.remove(tmp)
        i+=1

    base=random_bg(TARGET_LEN)

    final=CompositeVideoClip([base]+visuals).subclip(0,TARGET_LEN)

    voice=CompositeAudioClip(audio)

    if os.path.exists(MUSIC):
        m=AudioFileClip(MUSIC).audio_loop(duration=TARGET_LEN).volumex(.05)
        final=final.set_audio(CompositeAudioClip([m,voice]))
    else:
        final=final.set_audio(voice)

    final.write_videofile(
        "outputs/long_video.mp4",
        fps=24,
        preset="ultrafast"
    )

build()

print("✅ LONG VIDEO DONE")
