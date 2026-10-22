"""Strict near-duplicate rejection for INNER Discipline reel assets.

This is intentionally conservative: it never returns a fallback that violates
the novelty threshold. When a pool is exhausted, generation must expand the
pool or fail visibly rather than silently recycle copy.
"""
import difflib
import re

STOP = set("""
a an and are as at be been before being but by can could did do does doing
for from had has have he her here hers him his how i if in into is it its
just me more most my no not of on once or our out over she so some than
that the their them then there these they this those through to too until
up us very was we were what when where which who why will with would you
your yours
""".split())

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

def normalize(value):
    value = str(value or "").lower().replace("’", "'")
    value = re.sub(r"[^a-z0-9']+", " ", value)
    return " ".join(value.split())

def tokens(value):
    return {w for w in normalize(value).split() if len(w) > 2 and w not in STOP}

def concept(value):
    words = tokens(value)
    ranked = [(len(words & terms), name) for name, terms in CONCEPTS.items()]
    score, name = max(ranked, default=(0, "general"))
    return name if score else "general"

def similarity(left, right):
    """Return a conservative 0..1 lexical similarity score."""
    a_norm, b_norm = normalize(left), normalize(right)
    if not a_norm or not b_norm:
        return 1.0 if a_norm == b_norm else 0.0
    if a_norm == b_norm:
        return 1.0
    a, b = tokens(a_norm), tokens(b_norm)
    if not a or not b:
        return difflib.SequenceMatcher(None, a_norm, b_norm).ratio()
    overlap = len(a & b)
    jaccard = overlap / len(a | b)
    containment = overlap / min(len(a), len(b))
    sequence = difflib.SequenceMatcher(None, a_norm, b_norm).ratio()
    return max(jaccard, containment * 0.72, sequence * 0.72)

def max_similarity(candidate, recent):
    return max((similarity(candidate, old) for old in (recent or [])), default=0.0)

def assert_novel(candidate, recent=None, label="content", threshold=0.42):
    score = max_similarity(candidate, recent)
    if score >= threshold:
        raise ValueError(
            f"{label} rejected as a near-duplicate (similarity={score:.3f}, "
            f"threshold={threshold:.3f}). Expand or select a genuinely different candidate."
        )
    return score

def select_novel_candidate(candidates, recent_scripts=None, recent_concepts=None,
                           max_similarity_threshold=0.42, concept_window=3):
    """Choose only candidates under the similarity threshold; never fall back."""
    candidates = list(candidates or [])
    if not candidates:
        raise ValueError("No candidates were provided.")
    recent_scripts = [str(x) for x in (recent_scripts or [])]
    recent_concepts = [str(x) for x in (recent_concepts or [])]
    scored = []
    for candidate in candidates:
        topic = concept(candidate)
        overlap = max_similarity(candidate, recent_scripts)
        if overlap < max_similarity_threshold:
            repeated_topic = topic != "general" and topic in recent_concepts[:concept_window]
            scored.append((candidate, topic, overlap, repeated_topic))
    if not scored:
        best = min((max_similarity(c, recent_scripts), str(c)) for c in candidates)
        raise ValueError(
            f"No novel candidate available: best similarity={best[0]:.3f}, "
            f"threshold={max_similarity_threshold:.3f}. Refusing repetition."
        )
    # Prefer a fresh concept when possible, but don't reject an otherwise original
    # idea solely because a broad topic appeared recently.
    fresh_topic = [item for item in scored if not item[3]]
    pool = fresh_topic or scored
    pool.sort(key=lambda item: item[2])
    best_score = pool[0][2]
    best = [item for item in pool if item[2] <= best_score + 0.08]
    import random
    chosen = random.choice(best)
    return chosen[0], chosen[1], chosen[2], False
