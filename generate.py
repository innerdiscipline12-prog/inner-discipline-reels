import os, random, glob, asyncio
from moviepy.editor import *
import edge_tts

W,H = 1080,1920

os.makedirs("outputs", exist_ok=True)

# -------- CONTENT BANK --------

HOOKS=[
"You're not tired. You're undisciplined.",
"Comfort is ruining your future.",
"You don't lack time. You lack control.",
"No one is coming to save you.",
"Your habits expose you.",
"Discipline is chosen.",
]

TRUTHS=[
"Control beats motivation.",
"Consistency builds identity.",
"Discipline decides outcomes.",
"Standards shape your life.",
]

QUESTIONS=[
"Still here?",
"Day 1 or Day 100?",
"Will you finish?",
]

CTAS=[
"Comment discipline.",
"Type discipline.",
]

# -------- VOICE --------

async def tts(text,file):
    com=edge_tts.Communicate(
        text,
        voice="en-US-GuyNeural",
        rate="-10%",
        pitch="-5%"
    )
    await com.save(file)

def speak(text,file):
    asyncio.run(tts(text,file))

# -------- BACKGROUNDS --------

BGS=glob.glob("bg*.mp4")

def make_script():
    return [
        random.choice(HOOKS),
        random.choice(TRUTHS),
        random.choice(QUESTIONS if random.random()<0.6 else CTAS)
    ]

for r in range(5):

    lines=make_script()
    bg=random.choice(BGS)

    clips=[]
    sounds=[]
    t=0

    for i,line in enumerate(lines):

        audio=f"tmp{i}.mp3"
        speak(line,audio)

        a=AudioFileClip(audio)

        dur=min(3,a.duration+0.4)

        txt=TextClip(
            line,
            fontsize=80,
            color="white",
            size=(900,None),
            method="caption"
        ).set_position(("center","center"))\
         .set_start(t)\
         .set_duration(dur)

        clips.append(txt)
        sounds.append(a.set_start(t))

        t+=dur

    total=max(7,min(t,11))

    bgclip=VideoFileClip(bg)\
        .subclip(0,total)\
        .resize(height=1920)\
        .set_position("center")

    final=CompositeVideoClip([bgclip]+clips)\
        .set_audio(CompositeAudioClip(sounds))

    final.write_videofile(
        f"outputs/reel_{r}.mp4",
        fps=30,
        codec="libx264",
        audio_codec="aac"
    )
