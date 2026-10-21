"""Rule-based originality gate for INNER Discipline short-form scripts."""
import random
import re

STOP = set("about after again also and are because been before being but can could did does doing each even every for from get gets got had has have having here how into its just like make made more most much must not now only our out over own same should some than that the their them then there these they this those through until very was were what when where which while who will with would you your".split())
CONCEPTS = {
 "procrastination": set("tomorrow later delay waiting postpone eventually time years deadline".split()),
 "excuses": set("excuse excuses justify justification explain explaining negotiate reason reasons".split()),
 "comfort": set("comfort comfortable easy easier hard harder pain discomfort convenient".split()),
 "standards": set("standard standards lowering lower expectation expectations quality threshold".split()),
 "consistency": set("repeat repeated repetition routine consistent consistency daily habit habits compound compounds".split()),
 "identity": set("identity become becoming character person man self reputation".split()),
 "attention": set("attention phone scroll scrolling distract distraction focus noise".split()),
 "environment": set("environment room people surroundings company influence circle".split()),
 "money": set("money spend spending save saving debt income financial finance".split()),
 "boundaries": set("boundary boundaries allow allowing accept accepting respect relationship relationships".split()),
 "recovery": set("failure failed restart recover recovery setback setbacks rebuild".split()),
 "leadership": set("lead leader leadership reliable reliability responsibility depend trust accountability".split()),
 "emotional_control": set("emotion emotions anger mood feeling feelings control react reaction reactive".split()),
 "physical_effort": set("workout training gym body physical exercise effort strength fatigue".split()),
}

def tokens(value):
    return {w for w in re.findall(r"[a-z0-9']+", str(value).lower()) if len(w) > 2 and w not in STOP}

def concept(value):
    words = tokens(value)
    ranked = [(len(words & terms), name) for name, terms in CONCEPTS.items()]
    score, name = max(ranked, default=(0, "general"))
    return name if score else "general"

def similarity(left, right):
    a, b = tokens(left), tokens(right)
    if not a or not b:
        return 1.0 if str(left).strip().lower() == str(right).strip().lower() else 0.0
    overlap = len(a & b)
    return max(overlap / len(a | b), (overlap / min(len(a), len(b))) * 0.72)

def select_novel_candidate(candidates, recent_scripts=None, recent_concepts=None):
    """Return candidate, primary concept, overlap score, and fallback flag."""
    candidates = list(candidates or [])
    if not candidates:
        raise ValueError("No script candidates were provided.")
    recent_scripts = [str(x) for x in (recent_scripts or [])]
    recent_concepts = [str(x) for x in (recent_concepts or [])]
    scored = []
    for candidate in candidates:
        topic = concept(candidate)
        overlap = max((similarity(candidate, old) for old in recent_scripts), default=0.0)
        repeated_topic = topic != "general" and topic in recent_concepts[:4]
        scored.append((candidate, topic, overlap, repeated_topic))
    fresh = [item for item in scored if item[2] < 0.48 and not item[3]]
    if fresh:
        chosen = random.choice(fresh)
        return chosen[0], chosen[1], chosen[2], False
    scored.sort(key=lambda item: (item[3], item[2]))
    best_rank = (scored[0][3], scored[0][2])
    chosen = random.choice([item for item in scored if (item[3], item[2]) == best_rank])
    return chosen[0], chosen[1], chosen[2], True
