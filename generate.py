import os, json, random, asyncio, glob
import numpy as np
from moviepy.editor import *
from moviepy.video.fx.all import resize
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ================= SETTINGS =================

REEL_BACKGROUNDS = glob.glob("bg*.mp4")
LONG_BACKGROUNDS = glob.glob("bg_long*.mp4")

if not REEL_BACKGROUNDS:
    raise Exception("No reel backgrounds found (bg*.mp4)")
if not LONG_BACKGROUNDS:
    raise Exception("No long backgrounds found (bg_long*.mp4)")

VIDEO = random.choice(REEL_BACKGROUNDS)
LONG_VIDEO = random.choice(LONG_BACKGROUNDS)

MUSIC="music.mp3"
FONT_PATH="Anton-Regular.ttf"

W,H=1080,1920
LW,LH=1280,720

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

ALL_LINES=[
HOOK = [
"NO ONE COMING",
"START NOW",
"YOUR MOVE",
"WAKE UP",
"OWN TODAY",
"DECIDE NOW",
"YOUR LIFE",
"YOUR CHOICE",
"NO RESCUE",
"STOP WAITING",
"LOOK WITHIN",
"YOUR STANDARD",
"YOUR HABITS",
"YOUR FUTURE",
"CHECK YOURSELF",
"BE HONEST",
"OWN IT",
"ACT NOW",
"BEGIN TODAY",
"NO EXCUSES",
"SEE TRUTH",
"FACE REALITY",
"LOOK CLOSER",
"THIS MATTERS",
"YOUR TIME",
"YOUR PATH",
"YOUR TURN",
"OWN CHANGE",
"START SMALL",
"JUST BEGIN",
"SHOW UP",
"STAND UP",
"YOUR STORY",
"OWN ACTION",
"OWN RESULTS",
"YOUR DIRECTION",
"YOUR PRIORITIES",
"FOCUS NOW",
"THIS LIFE",
"YOUR CONTROL",
"TAKE CONTROL",
"OWN CONTROL",
"YOUR RESPONSIBILITY",
"OWN RESPONSIBILITY",
"NO DELAY",
"STOP HIDING",
"CHOOSE HARD",
"STEP FORWARD",
"MOVE FIRST",
"YOUR DECISION",
"OWN DECISIONS",
"OWN FUTURE",
"YOUR DISCIPLINE",
"DISCIPLINE FIRST",
"DISCIPLINE NOW",
"BEGIN AGAIN",
"RESET TODAY",
"OWN TODAY",
"YOUR REALITY",
"SEE CLEARLY",
"FACE YOURSELF",
"CHECK HABITS",
"OWN HABITS",
"YOUR PATTERNS",
"CHANGE PATTERNS",
"BREAK PATTERNS",
"YOUR TRUTH",
"LIVE HONEST",
"ACT HONEST",
"REAL EFFORT",
"TRUE EFFORT",
"YOUR EFFORT",
"SHOW EFFORT",
"OWN EFFORT",
"BUILD NOW",
"BUILD DAILY",
"BUILD SELF",
"BUILD HABITS",
"BUILD ROUTINE",
"BUILD CONTROL",
"BUILD FOCUS",
"YOUR FOCUS",
"PROTECT FOCUS",
"GUARD FOCUS",
"YOUR ENERGY",
"PROTECT ENERGY",
"USE ENERGY",
"YOUR ATTENTION",
"CONTROL ATTENTION",
"YOUR INPUTS",
"FIX INPUTS",
"CHECK INPUTS",
"OWN INPUTS",
"YOUR DIRECTION",
"CHOOSE DIRECTION",
"SET DIRECTION",
"YOUR TARGET",
"AIM CLEAR",
"MOVE INTENTIONAL",
"LIVE INTENTIONAL"
]
REALITY = [
"COMFORT COSTS",
"COMFORT SELLS",
"COMFORT TRAPS",
"COMFORT WEAKENS",
"EASY DISTRACTS",
"EASY SELLS",
"EASY LIES",
"EASY TEMPTS",
"SCREENS DISTRACT",
"SCREENS STEAL",
"TIME MOVES",
"TIME GONE",
"TIME WASTED",
"TIME MATTERS",
"EFFORT RARE",
"CONSISTENCY RARE",
"DISCIPLINE RARE",
"FOCUS RARE",
"PATTERNS REPEAT",
"HABITS REPEAT",
"RESULTS SHOW",
"ACTIONS SHOW",
"CHOICES SHOW",
"PRIORITIES SHOW",
"EXCUSES COMMON",
"COMPLAINTS COMMON",
"QUITTING EASY",
"STARTING EASY",
"STAYING HARD",
"EFFORT HARD",
"STRUCTURE HARD",
"TRUTH HARD",
"COMFORT LOUD",
"DISCIPLINE QUIET",
"LAZINESS GROWS",
"LAZINESS BUILDS",
"DISTRACTION EVERYWHERE",
"TEMPTATION EVERYWHERE",
"NO SHORTCUTS",
"NO MAGIC",
"NO SECRETS",
"PROCESS MATTERS",
"ROUTINE MATTERS",
"STRUCTURE MATTERS",
"STANDARDS MATTER",
"INPUTS MATTER",
"CHOICES MATTER",
"DAILY MATTERS",
"SMALL MATTERS",
"DETAILS MATTER",
"HABITS DECIDE",
"ACTIONS DECIDE",
"STANDARDS DECIDE",
"FOCUS DECIDES",
"ROUTINE DECIDES",
"INPUTS DECIDE",
"DISCIPLINE DECIDES",
"CONSISTENCY DECIDES",
"PATTERNS DECIDE",
"ENVIRONMENT SHAPES",
"ENVIRONMENT INFLUENCES",
"PEOPLE INFLUENCE",
"COMPANY SHAPES",
"HABITS SHAPE",
"CHOICES SHAPE",
"DISCIPLINE SHAPES",
"ROUTINE SHAPES",
"TIME REVEALS",
"LIFE REVEALS",
"PRESSURE REVEALS",
"ACTIONS REVEAL",
"HABITS REVEAL",
"STANDARDS REVEAL",
"CHARACTER REVEALS",
"TRUTH REVEALS",
"RESULTS REVEAL",
"REALITY CHECKS",
"REALITY HITS",
"REALITY TEACHES",
"LIFE TEACHES",
"TIME TEACHES",
"PAIN TEACHES",
"FAILURE TEACHES",
"LOSS TEACHES",
"WORK TEACHES",
"EFFORT TEACHES",
"NOISE DISTRACTS",
"NOISE MISLEADS",
"NOISE CONFUSES",
"SILENCE CLARIFIES",
"SILENCE BUILDS",
"SILENCE TEACHES",
"CALM BUILDS",
"CALM FOCUSES",
"CALM WINS",
"STILLNESS BUILDS"
]
STRUGGLE = [
"DISCIPLINE HURTS",
"EFFORT HURTS",
"GROWTH HURTS",
"CHANGE HURTS",
"SACRIFICE HURTS",
"PROGRESS SLOW",
"RESULTS SLOW",
"CHANGE SLOW",
"GROWTH SLOW",
"WORK REPETITIVE",
"WORK BORING",
"WORK HARD",
"WORK QUIET",
"WORK DAILY",
"RESISTANCE COMES",
"RESISTANCE BUILDS",
"TEMPTATION CALLS",
"COMFORT CALLS",
"OLD HABITS",
"OLD PATTERNS",
"OLD COMFORT",
"MIND RESISTS",
"BRAIN SEEKS EASY",
"EMOTIONS SHIFT",
"MOOD CHANGES",
"ENERGY LOW",
"FEELING LOW",
"MOTIVATION FADES",
"MOTIVATION LIES",
"URGES COME",
"URGES RETURN",
"DOUBT COMES",
"DOUBT SPEAKS",
"FEAR SPEAKS",
"PRESSURE BUILDS",
"STRESS BUILDS",
"FATIGUE BUILDS",
"TIRED STILL",
"TIRED WORK",
"TIRED MOVE",
"LONELY PATH",
"LONELY WORK",
"QUIET STRUGGLE",
"HIDDEN STRUGGLE",
"INTERNAL BATTLE",
"INNER BATTLE",
"MENTAL BATTLE",
"HARD DAYS",
"LONG DAYS",
"ROUGH DAYS",
"TOUGH DAYS",
"DISCIPLINE TESTS",
"PATENCE TESTED",
"WILL TESTED",
"FOCUS TESTED",
"LIMITS TESTED",
"LIMITS PUSHED",
"BOUNDARIES PUSHED",
"COMFORT PULLS",
"EASY PULLS",
"DISTRACTIONS PULL",
"HABITS PULL",
"OLD SELF",
"OLD YOU",
"WEAK MOMENTS",
"HARD MOMENTS",
"SLOW MOMENTS",
"LOW MOMENTS",
"QUIET MOMENTS",
"HEAVY DAYS",
"HEAVY MIND",
"HEAVY HEART",
"PUSH THROUGH",
"MOVE THROUGH",
"WORK THROUGH",
"BREATHE THROUGH",
"STAY STEADY",
"STAY PRESENT",
"STAY MOVING",
"KEEP GOING",
"KEEP MOVING",
"HOLD LINE",
"HOLD STANDARD",
"HOLD FOCUS",
"HOLD CONTROL",
"HOLD STEADY",
"STAY CALM",
"STAY DISCIPLINED",
"STAY STRUCTURED",
"STAY INTENTIONAL",
"STAY SHARP",
"STAY SERIOUS",
"STAY HONEST",
"STAY COMMITTED",
"STAY STRONG"
]
IDENTITY = [
"YOU BECOME",
"YOU BUILD",
"YOU DECIDE",
"YOU SHAPE",
"YOU DEFINE",
"YOU CREATE",
"YOU DESIGN",
"YOU FORM",
"YOU GROW",
"YOU CHANGE",
"IDENTITY BUILDS",
"IDENTITY FORMS",
"IDENTITY GROWS",
"IDENTITY SHIFTS",
"CHARACTER BUILDS",
"CHARACTER SHOWS",
"CHARACTER GROWS",
"CHARACTER FORMS",
"SELF BUILT",
"SELF SHAPED",
"SELF MADE",
"SELF CONTROLLED",
"SELF DISCIPLINED",
"SELF AWARE",
"SELF HONEST",
"SELF DIRECTED",
"SELF DRIVEN",
"SELF GUIDED",
"SELF MANAGED",
"SELF TRAINED",
"HABITS DEFINE",
"ACTIONS DEFINE",
"STANDARDS DEFINE",
"CHOICES DEFINE",
"PATTERNS DEFINE",
"ROUTINE DEFINES",
"DISCIPLINE DEFINES",
"CONSISTENCY DEFINES",
"EFFORT DEFINES",
"REPETITION BUILDS",
"REPETITION SHAPES",
"REPETITION FORMS",
"REPETITION TRAINS",
"REPETITION DEFINES",
"DAILY ACTIONS",
"DAILY HABITS",
"DAILY CHOICES",
"DAILY STANDARDS",
"DAILY ROUTINE",
"FUTURE SELF",
"BETTER SELF",
"STRONGER SELF",
"CALMER SELF",
"FOCUSED SELF",
"DISCIPLINED SELF",
"CONTROLLED SELF",
"BUILT SELF",
"TRAINED SELF",
"SHARP SELF",
"YOU EVOLVE",
"YOU IMPROVE",
"YOU DEVELOP",
"YOU MATURE",
"YOU STRENGTHEN",
"YOU HARDEN",
"YOU FOCUS",
"YOU ADAPT",
"YOU LEARN",
"YOU ADVANCE",
"PERSON YOU",
"NEW YOU",
"REAL YOU",
"TRUE YOU",
"STRONG YOU",
"FOCUSED YOU",
"DISCIPLINED YOU",
"CONTROLLED YOU",
"SHARP YOU",
"BUILT YOU",
"IDENTITY FIRST",
"CHARACTER FIRST",
"STANDARDS FIRST",
"DISCIPLINE FIRST",
"FOCUS FIRST",
"STRUCTURE FIRST",
"ROUTINE FIRST",
"EFFORT FIRST",
"PROCESS FIRST",
"CONSISTENCY FIRST",
"OWN IDENTITY",
"BUILD IDENTITY",
"PROTECT IDENTITY",
"SHAPE IDENTITY",
"TRAIN IDENTITY",
"STRENGTHEN IDENTITY",
"DEFINE IDENTITY",
"CREATE IDENTITY",
"FORM IDENTITY",
"LIVE IDENTITY"
]
RESOLUTION = [
"SMALL STEPS",
"SMALL WINS",
"SMALL ACTIONS",
"SMALL DAILY",
"DAILY WORK",
"DAILY FOCUS",
"DAILY STRUCTURE",
"DAILY DISCIPLINE",
"DAILY ROUTINE",
"DAILY EFFORT",
"BUILD DAILY",
"BUILD SLOW",
"BUILD STEADY",
"BUILD CALM",
"BUILD QUIET",
"BUILD STRONG",
"BUILD FOCUS",
"BUILD CONTROL",
"BUILD HABITS",
"BUILD ROUTINE",
"STAY CALM",
"STAY STEADY",
"STAY FOCUSED",
"STAY STRUCTURED",
"STAY CONSISTENT",
"STAY DISCIPLINED",
"STAY PRESENT",
"STAY INTENTIONAL",
"STAY SHARP",
"STAY HONEST",
"KEEP GOING",
"KEEP MOVING",
"KEEP BUILDING",
"KEEP FOCUS",
"KEEP STRUCTURE",
"KEEP DISCIPLINE",
"KEEP CONTROL",
"KEEP EFFORT",
"KEEP WORKING",
"KEEP STEADY",
"CALM MIND",
"CLEAR MIND",
"QUIET MIND",
"FOCUSED MIND",
"DISCIPLINED MIND",
"CONTROLLED MIND",
"SHARP MIND",
"TRAINED MIND",
"STRONG MIND",
"STABLE MIND",
"CONTROL INPUTS",
"CONTROL HABITS",
"CONTROL TIME",
"CONTROL FOCUS",
"CONTROL ENERGY",
"CONTROL ACTIONS",
"CONTROL PATTERNS",
"CONTROL ROUTINE",
"CONTROL SELF",
"CONTROL DAILY",
"CONSISTENCY WINS",
"DISCIPLINE WINS",
"FOCUS WINS",
"EFFORT WINS",
"STRUCTURE WINS",
"ROUTINE WINS",
"STANDARDS WIN",
"HABITS WIN",
"PROCESS WINS",
"CONTROL WINS",
"PEACE BUILDS",
"CLARITY BUILDS",
"STRENGTH BUILDS",
"CONFIDENCE BUILDS",
"POWER BUILDS",
"MOMENTUM BUILDS",
"DISCIPLINE BUILDS",
"FOCUS BUILDS",
"ROUTINE BUILDS",
"CONTROL BUILDS",
"ONE DAY",
"NEXT STEP",
"NEXT ACTION",
"NEXT MOVE",
"NEXT HABIT",
"NEXT REP",
"NEXT WIN",
"NEXT BUILD",
"NEXT FOCUS",
"NEXT LEVEL",
"QUIET PROGRESS",
"QUIET BUILD",
"QUIET POWER",
"QUIET GROWTH",
"QUIET STRENGTH",
"QUIET FOCUS",
"QUIET DISCIPLINE",
"QUIET CONTROL",
"QUIET CONSISTENCY",
"QUIET CONFIDENCE"
]

ALL_LINES = HOOK + REALITY + STRUGGLE + IDENTITY + RESOLUTION
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

def frame(text,w=W,h=H,size=140):
    img=Image.new("RGBA",(w,h),(0,0,0,0))
    d=ImageDraw.Draw(img)

    words=text.split()
    if len(words)>=2:
        mid=len(words)//2
        text=" ".join(words[:mid])+"\n"+" ".join(words[mid:])

    font=ImageFont.truetype(FONT_PATH,size)

    box=d.multiline_textbbox((0,0),text,font=font,spacing=20)
    x=(w-(box[2]-box[0]))//2
    y=(h-(box[3]-box[1]))//2

    d.multiline_text((x+6,y+6),text,font=font,fill=(0,0,0,180),align="center",spacing=20)
    d.multiline_text((x,y),text,font=font,fill="white",align="center",spacing=20)

    return np.array(img)

# ================= THUMBNAIL =================

def make_thumbnail(text,path):
    img=Image.new("RGB",(1080,1920),(0,0,0))
    d=ImageDraw.Draw(img)

    font=ImageFont.truetype(FONT_PATH,200)

    box=d.multiline_textbbox((0,0),text,font=font)
    x=(1080-(box[2]-box[0]))//2
    y=(1920-(box[3]-box[1]))//2

    d.multiline_text((x,y),text,font=font,fill="white",align="center")
    img.save(path)

# ================= CAPTION =================

def make_caption(lines,path):
    cap=" • ".join(lines[:2]).title()
    tags=" ".join(random.sample(HASHTAGS,4))
    open(path,"w").write(cap+"\n\n"+tags)

# ================= PICK LINES =================

def pick_lines():
    global used

    pool=[l for l in ALL_LINES if l not in used]
    if len(pool)<3:
        used=[]
        pool=ALL_LINES.copy()

    chosen=random.sample(pool,3)
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
    audio=[]
    t=0

    for i,line in enumerate(chosen):

        vp=f"{folder}/line{i}.mp3"
        asyncio.run(make_voice(line,vp))

        a=AudioFileClip(vp)
        dur=a.duration+0.4

        img=frame(line)

        txt=(ImageClip(img)
             .set_start(t)
             .set_duration(dur)
             .fadein(0.3)
             .fadeout(0.3))

        clips.append(txt)
        audio.append(a.set_start(t+0.25))
        t+=dur

    final=CompositeVideoClip([base]+clips).subclip(0,t)

    voice_mix=CompositeAudioClip(audio)

    if os.path.exists(MUSIC):
        music=AudioFileClip(MUSIC).audio_loop(duration=t).volumex(0.1)
        final=final.set_audio(CompositeAudioClip([music,voice_mix]))
    else:
        final=final.set_audio(voice_mix)

    final.write_videofile(f"{folder}/reel.mp4",fps=30)

    make_thumbnail(chosen[0],f"{folder}/thumbnail.jpg")
    make_caption(chosen,f"{folder}/caption.txt")

# ================= SMART FLOW LONG VIDEO =================

def make_long_video():

    print("🔥 Generating SMART FLOW 10-minute video...")

    target_len=600
    timestamps=[]

    base=VideoFileClip(LONG_VIDEO).without_audio()
    base=base.fx(vfx.loop,duration=target_len)
    base=base.resize(height=LH)

    if base.w<LW:
        base=base.resize(width=LW)

    base=base.crop(x_center=base.w/2,y_center=base.h/2,width=LW,height=LH)

    clips=[]
    audio=[]
    t=0
    idx=0

    while t<target_len:

        line=random.choice(ALL_LINES)

        vp=f"outputs/long_{idx}.mp3"
        asyncio.run(make_voice(line,vp))

        a=AudioFileClip(vp)
        dur=max(6,a.duration+1.2)

        timestamps.append(f"{int(t//60)}:{int(t%60):02d} {line.title()}")

        img=frame(line,LW,LH,90)

        txt=(ImageClip(img)
             .set_start(t)
             .set_duration(dur)
             .fadein(0.8)
             .fadeout(0.8))

        clips.append(txt)
        audio.append(a.set_start(t+0.4))

        t+=dur
        idx+=1

    final=CompositeVideoClip([base]+clips).subclip(0,target_len)

    voice_mix=CompositeAudioClip(audio)

    if os.path.exists(MUSIC):
        music=AudioFileClip(MUSIC).audio_loop(duration=target_len).volumex(0.05)
        final=final.set_audio(CompositeAudioClip([music,voice_mix]))
    else:
        final=final.set_audio(voice_mix)

    final.write_videofile("outputs/long_video.mp4",fps=30)

    title="10 Minutes to Build Discipline"
    open("outputs/long_title.txt","w").write(title)

    desc=f"""
Build discipline, self-control and focus.

CHAPTERS:
{chr(10).join(timestamps)}

#discipline #focus #mindset
"""
    open("outputs/long_description.txt","w").write(desc)

    thumb=Image.new("RGB",(1280,720),(0,0,0))
    d=ImageDraw.Draw(thumb)
    font=ImageFont.truetype(FONT_PATH,120)

    text="DISCIPLINE\nBUILDS YOU"
    box=d.multiline_textbbox((0,0),text,font=font)

    x=(1280-(box[2]-box[0]))//2
    y=(720-(box[3]-box[1]))//2

    d.multiline_text((x,y),text,font=font,fill="white",align="center")
    thumb.save("outputs/long_thumbnail.jpg")

    print("✅ LONG VIDEO COMPLETE")

# ================= RUN =================

os.makedirs("outputs",exist_ok=True)

for i in range(1,REELS_PER_RUN+1):
    make_reel(i)

make_long_video()

json.dump(used,open(MEM,"w"))

print("🔥 MASTER V10.5 COMPLETE")
