"""V33 retention optimization for INNER Discipline reels.

The engine is intentionally deterministic and conservative:
- reject predictable swipe-risk openings
- score hook, tension, payoff and overall retention potential
- preserve V32 originality gates
- optionally learn from imported performance_history_v33.json
"""

import random
import re
from collections import defaultdict

from originality import max_similarity, similarity


GENERIC_OPENERS = (
    "discipline is ",
    "success is ",
    "success requires",
    "you need to ",
    "you should ",
    "never give up",
    "always remember",
    "believe in yourself",
    "greatness ",
    "hard work ",
    "stay consistent",
    "keep going",
    "the key to ",
    "here's the truth",
    "this is how ",
    "this is why ",
)

WEAK_HOOK_PATTERNS = (
    r"^today (?:i|we) ",
    r"^let me tell you",
    r"^in this video",
    r"^if you want",
    r"^remember that",
    r"^you can do",
)

TENSION_TERMS = {
    "cost", "price", "warning", "regret", "delay", "tomorrow", "break",
    "crack", "slip", "drift", "normal", "quietly", "familiar", "proof",
    "consequence", "trade", "signal", "pattern", "compromise", "exception",
}

# The opening must create an immediate psychological/emotional reason to keep watching.
# This is stricter than the generic swipe-risk filter: a hook can be original
# and still be too emotionally flat for the first seconds of a Reel.
OPENING_TENSION_TERMS = {
    "cost", "price", "warning", "regret", "delay", "tomorrow", "break",
    "crack", "slip", "drift", "normal", "quietly", "familiar", "proof",
    "consequence", "trade", "signal", "pattern", "compromise", "exception",
    "waste", "wasted", "lose", "losing", "lost", "disappear", "danger",
    "dangerous", "shame", "embarrassing", "weak", "failure", "excuse",
    "excuses", "comfortable", "comfort", "stuck", "leaking", "ignored",
}

OPENING_CONTRAST_TERMS = {
    "but", "not", "instead", "still", "already", "same", "lower", "higher",
    "different", "yet", "without", "before", "after", "until",
}

OPENING_SCORE_MIN = 4.5

PAYOFF_TERMS = {
    "that is", "this is", "the cost", "the lesson", "the truth", "correct",
    "discipline begins", "standard", "proof", "nothing changed", "that is why",
}

HOOK_FAMILIES = {
    "mirror": ("you ", "your ", "you’re ", "you're ", "you keep", "you know"),
    "warning": ("warning", "signal", "felt", "saw it coming", "first crack", "noticed"),
    "consequence": ("cost", "price", "regret", "years", "bill", "consequence"),
    "curiosity": ("why ", "what ", "who ", "where ", "the moment", "the part"),
    "contrast": ("but ", "not ", "instead", "looks ", "feels ", "actually"),
    "decision": ("choose", "decide", "stop ", "start ", "correct", "obey"),
}


def normalize(text):
    return " ".join(re.sub(r"[^a-z0-9'!?]+", " ", str(text or "").lower()).split())


def hook_family(text):
    value = normalize(text)
    for family, needles in HOOK_FAMILIES.items():
        if any(needle in value for needle in needles):
            return family
    return "general"


def is_swipe_risk_hook(text):
    value = normalize(text)
    if not value:
        return True
    if any(value.startswith(prefix) for prefix in GENERIC_OPENERS):
        return True
    if any(re.search(pattern, value) for pattern in WEAK_HOOK_PATTERNS):
        return True
    words = value.replace("?", "").replace("!", "").split()
    if len(words) < 3:
        return True
    return False


def opening_score(lines):
    """Score the first seconds for emotional/psychological stopping power."""
    values = [normalize(x) for x in (lines or []) if normalize(x)]
    if not values:
        return -100.0

    first = values[0]
    first_words = first.replace("?", "").replace("!", "").split()
    first_two = " ".join(values[:2])
    score = hook_score(first)

    if any(word in first_words for word in ("you", "your", "men", "man")):
        score += 1.0

    if any(term in first for term in OPENING_TENSION_TERMS):
        score += 1.5
    if any(term in first_two for term in OPENING_CONTRAST_TERMS):
        score += 1.0
    if "?" in first:
        score += 1.0

    if 3 <= len(first_words) <= 8:
        score += 1.0
    elif len(first_words) > 11:
        score -= 2.0

    return round(score, 4)


def hook_score(text):
    value = normalize(text)
    words = value.replace("?", "").replace("!", "").split()
    score = 0.0

    if is_swipe_risk_hook(text):
        return -8.0

    if "you" in words or "your" in words:
        score += 2.0
    if 3 <= len(words) <= 8:
        score += 2.0
    elif len(words) <= 11:
        score += 0.8

    if "?" in str(text):
        score += 2.5

    if any(term in value for term in TENSION_TERMS):
        score += 2.0

    if value.startswith(("the moment", "the part", "the warning", "you ", "your ")):
        score += 1.0

    if value.endswith((".", "!", "?")):
        score += 0.5

    return score


def tension_score(lines):
    middle = " ".join(str(x) for x in list(lines)[1:-1])
    value = normalize(middle)
    score = min(5.0, sum(1.0 for term in TENSION_TERMS if term in value))
    if len(list(lines)) >= 4:
        score += 1.0
    return min(score, 6.0)


def payoff_score(lines):
    if not lines:
        return 0.0
    final = normalize(lines[-1])
    score = 0.0

    if len(final.split()) >= 4:
        score += 1.5
    if any(term in final for term in PAYOFF_TERMS):
        score += 2.0
    if final.endswith((".", "!", "?")):
        score += 0.5
    if final in {"every time", "quietly", "for real", "at a time", "then again"}:
        score -= 5.0
    return min(score, 4.0)


"""V34 impact/completion layer: reward narrative movement without changing the restrained voice."""

PROGRESSION_TERMS = {
    "because", "but", "until", "before", "after", "then", "which means",
    "that means", "so", "instead", "yet", "therefore", "eventually",
}
OPEN_LOOP_TERMS = {
    "why", "what", "until", "before", "after", "the moment", "the part",
    "the cost", "the reason", "what happens", "what changed", "eventually",
}
PAYOFF_SPECIFIC_TERMS = {
    "standard", "routine", "choice", "decision", "habit", "proof", "control",
    "discipline", "consequence", "respect", "time", "future", "identity",
}
FLAT_ENDINGS = {
    "keep going", "stay strong", "you can do it", "never quit",
    "believe in yourself", "just start", "make it happen",
}


def completion_structure_score(lines):
    """Score HOOK -> TENSION -> OPEN LOOP -> ESCALATION -> PAYOFF movement."""
    values = [normalize(x) for x in (lines or []) if normalize(x)]
    if len(values) < 3:
        return -4.0
    first, middle, final = values[0], " ".join(values[1:-1]), values[-1]
    score = 0.0
    if "?" in first:
        score += 1.5
    if any(term in first for term in OPENING_TENSION_TERMS):
        score += 1.0
    if any(term in first for term in OPEN_LOOP_TERMS):
        score += 0.7
    transitions = sum(1 for term in PROGRESSION_TERMS if term in middle)
    score += min(1.5, transitions * 0.5)
    if any(term in middle for term in TENSION_TERMS):
        score += 1.0
    if any(term in middle for term in ("cost", "consequence", "regret", "years", "identity", "respect")):
        score += 0.8
    if any(term in final for term in PAYOFF_SPECIFIC_TERMS):
        score += 1.2
    if len(final.split()) >= 4:
        score += 0.5
    if final in FLAT_ENDINGS:
        score -= 2.5
    first_tokens = set(first.split())
    middle_tokens = set(middle.split())
    if first_tokens and len(first_tokens & middle_tokens) / max(1, len(first_tokens)) > 0.70:
        score -= 1.0
    return round(max(-4.0, min(6.0, score)), 4)


def line_rhythm_score(lines):
    """Reward a readable short/medium/short rhythm for controlled narration."""
    lengths = [len(normalize(x).split()) for x in (lines or []) if normalize(x)]
    if len(lengths) < 3:
        return -2.0
    score = 0.0
    if 3 <= lengths[0] <= 8:
        score += 0.7
    if any(4 <= n <= 9 for n in lengths[1:-1]):
        score += 0.5
    if 3 <= lengths[-1] <= 10:
        score += 0.7
    if max(lengths) - min(lengths) >= 2:
        score += 0.4
    if any(n > 12 for n in lengths):
        score -= 1.0
    return round(score, 4)


def retention_candidate_score(lines_or_text, category="general", performance_profile=None):
    if isinstance(lines_or_text, str):
        lines = [x.strip() for x in lines_or_text.split("|") if x.strip()]
    else:
        lines = [str(x).strip() for x in (lines_or_text or []) if str(x).strip()]

    if not lines:
        return -100.0

    score = hook_score(lines[0])
    score += tension_score(lines)
    score += payoff_score(lines)
    score += completion_structure_score(lines)
    score += line_rhythm_score(lines)

    word_count = sum(len(x.split()) for x in lines)
    if 16 <= word_count <= 27:
        score += 1.5
    elif word_count > 30:
        score -= 2.0

    if len(lines) >= 4:
        score += 0.5

    profile = performance_profile or {}
    category_boost = profile.get("category_boosts", {}).get(str(category), 0.0)
    hook_boost = profile.get("hook_family_boosts", {}).get(hook_family(lines[0]), 0.0)
    score += category_boost + hook_boost

    return round(score, 4)


def build_performance_profile(history):
    """Turn imported Facebook metrics into small ranking boosts.

    Expected records may contain:
      category, hook_family, average_watch_time, retention_rate, views,
      shares, comments, follows.

    The profile remains neutral until there are enough observations.
    """
    rows = [row for row in (history or []) if isinstance(row, dict)]
    if len(rows) < 5:
        return {"category_boosts": {}, "hook_family_boosts": {}, "samples": len(rows)}

    category_values = defaultdict(list)
    hook_values = defaultdict(list)

    for row in rows:
        try:
            watch = float(row.get("average_watch_time", 0) or 0)
            watch_pct = float(row.get("average_watch_pct", 0) or 0)
            completion = float(row.get("completion_rate", row.get("retention_rate", 0)) or 0)
            engagement = (
                float(row.get("share_comment_rate", 0) or 0) * 100.0
                + float(row.get("follow_rate", 0) or 0) * 100.0
            )
            # Normalize the mixed signals so no single Facebook metric
            # overwhelms the learning profile.
            signal = (
                min(watch, 15.0) * 0.45
                + min(watch_pct, 1.5) * 4.0
                + min(max(completion, 0.0), 100.0) / 20.0
                + min(max(engagement, 0.0), 20.0) * 0.10
            )
        except (TypeError, ValueError):
            continue

        category = str(row.get("category", "general"))
        family = str(row.get("hook_family", "general"))
        category_values[category].append(signal)
        hook_values[family].append(signal)

    def boosts(groups):
        means = {key: sum(values) / len(values) for key, values in groups.items() if values}
        if not means:
            return {}
        baseline = sum(means.values()) / len(means)
        return {
            key: round(max(-2.0, min(2.0, (value - baseline) * 0.25)), 3)
            for key, value in means.items()
        }

    return {
        "category_boosts": boosts(category_values),
        "hook_family_boosts": boosts(hook_values),
        "samples": len(rows),
    }


def select_retention_candidate(
    candidates,
    recent_scripts=None,
    recent_concepts=None,
    category="general",
    performance_profile=None,
    max_candidates=5,
    similarity_threshold=0.42,
):
    """Evaluate up to max_candidates fresh candidates and return the strongest.

    Returns (candidate, concept, novelty_score, retention_score, hook_family).
    No fallback may bypass the originality or swipe-risk gates.
    """
    pool = list(candidates or [])
    if not pool:
        raise ValueError("No retention candidates were provided.")

    random.shuffle(pool)
    recent_scripts = [str(x) for x in (recent_scripts or [])]

    evaluated = []
    for candidate in pool:
        if len(evaluated) >= max_candidates:
            break

        lines = candidate if isinstance(candidate, list) else str(candidate).split("|")
        lines = [str(x).strip() for x in lines if str(x).strip()]
        if not lines or is_swipe_risk_hook(lines[0]):
            continue

        novelty = max_similarity(" | ".join(lines), recent_scripts)
        if novelty >= similarity_threshold:
            continue

        score = retention_candidate_score(lines, category, performance_profile)
        evaluated.append((score, novelty, lines))

    if not evaluated:
        raise ValueError(
            "No retention candidate survived the swipe-risk and originality gates."
        )

    evaluated.sort(key=lambda item: (item[0], -item[1]), reverse=True)
    score, novelty, lines = evaluated[0]

    from originality import concept
    concept_name = concept(" | ".join(lines))

    return lines, concept_name, novelty, score, hook_family(lines[0])
