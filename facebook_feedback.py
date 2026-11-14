"""Facebook Reels performance feedback collector for INNER Discipline.

Reads published_reels.json, fetches lifetime Reel insights from Meta Graph API,
updates performance_history_v33.json in-place, and emits a compact summary.

The publisher is responsible for registering each successful Facebook publish:
{
  "video_id": "...",
  "output_base": "outputs/reel_v33_...",
  "published_at": "...",
  "category": "dangerous",
  "hook_family": "mirror",
  "retention_score": 8.5,
  "predicted_duration": 12.4
}

Meta currently documents Reel video insights on:
GET /v27.0/{video-id}/video_insights
with metrics including average watch time, replay count, retention graph,
followers, likes, social actions and play counts.
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

GRAPH_API_VERSION = os.getenv("META_GRAPH_API_VERSION", "v27.0")
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
TOKEN_ENV = "FACEBOOK_PAGE_ACCESS_TOKEN"
REGISTRY_FILE = os.getenv("PUBLISHED_REELS_FILE", "published_reels.json")
HISTORY_FILE = os.getenv("PERFORMANCE_HISTORY_FILE", "performance_history_v33.json")

REEL_METRICS = [
    "blue_reels_play_count",
    "fb_reels_replay_count",
    "fb_reels_total_plays",
    "post_impressions_unique",
    "post_video_avg_time_watched",
    "post_video_followers",
    "post_video_likes_by_reaction_type",
    "post_video_retention_graph",
    "post_video_social_actions",
    "post_video_view_time",
]


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, type(default)) else default


def save_json(path, value):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)


def api_get(path, params):
    query = urllib.parse.urlencode(params)
    url = f"{GRAPH_BASE}/{path.lstrip('/')}?{query}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "inner-discipline-retention-engine/34"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def extract_metric(data, name):
    for item in data.get("data", []):
        if item.get("name") != name:
            continue
        if "value" in item:
            return item["value"]
        values = item.get("values") or []
        if values:
            return values[-1].get("value")
    return None


def flatten_reaction_likes(value):
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        return float(sum(v for v in value.values() if isinstance(v, (int, float))))
    return None


def flatten_social_actions(value):
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        return float(sum(v for v in value.values() if isinstance(v, (int, float))))
    return None


def retention_curve(value):
    if not isinstance(value, list):
        return None
    curve = []
    for item in value:
        if isinstance(item, dict):
            raw = item.get("value")
        else:
            raw = item
        try:
            curve.append(float(raw))
        except (TypeError, ValueError):
            continue
    return curve or None


def build_record(item, metrics):
    avg_ms = extract_metric(metrics, "post_video_avg_time_watched")
    view_time_ms = extract_metric(metrics, "post_video_view_time")
    plays = extract_metric(metrics, "fb_reels_total_plays")
    starts = extract_metric(metrics, "blue_reels_play_count")
    replays = extract_metric(metrics, "fb_reels_replay_count")
    impressions = extract_metric(metrics, "post_impressions_unique")
    followers = extract_metric(metrics, "post_video_followers")
    likes = flatten_reaction_likes(
        extract_metric(metrics, "post_video_likes_by_reaction_type")
    )
    social = flatten_social_actions(
        extract_metric(metrics, "post_video_social_actions")
    )
    curve = retention_curve(
        extract_metric(metrics, "post_video_retention_graph")
    )

    duration = item.get("predicted_duration")
    try:
        duration = float(duration)
    except (TypeError, ValueError):
        duration = None

    try:
        avg_watch = float(avg_ms) / 1000.0 if avg_ms is not None else None
    except (TypeError, ValueError):
        avg_watch = None

    completion_rate = None
    if curve:
        # Meta's Reel retention graph contains 40 timestamp segments.
        # The last segment is our completion proxy.
        completion_rate = curve[-1]

    avg_watch_pct = None
    if avg_watch is not None and duration and duration > 0:
        avg_watch_pct = avg_watch / duration

    def rate(numerator, denominator):
        try:
            if denominator and float(denominator) > 0:
                return float(numerator) / float(denominator)
        except (TypeError, ValueError):
            pass
        return None

    return {
        "video_id": str(item["video_id"]),
        "output_base": item.get("output_base", ""),
        "published_at": item.get("published_at"),
        "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "category": item.get("category", "general"),
        "hook_family": item.get("hook_family", "general"),
        "retention_score": item.get("retention_score"),
        "predicted_duration": duration,
        "plays": plays,
        "starts": starts,
        "replays": replays,
        "unique_impressions": impressions,
        "average_watch_time": avg_watch,
        "average_watch_pct": avg_watch_pct,
        "completion_rate": completion_rate,
        "retention_curve": curve,
        "view_time_seconds": (
            float(view_time_ms) / 1000.0
            if isinstance(view_time_ms, (int, float))
            else None
        ),
        "followers": followers,
        "likes": likes,
        "social_actions": social,
        "share_comment_rate": rate(social, plays),
        "follow_rate": rate(followers, plays),
        "like_rate": rate(likes, plays),
    }


def fetch_reel(video_id):
    response = api_get(
        f"{video_id}/video_insights",
        {
            "metric": ",".join(REEL_METRICS),
            "period": "lifetime",
            "access_token": os.environ[TOKEN_ENV],
        },
    )
    if "error" in response:
        raise RuntimeError(response["error"])
    return response


def collect():
    token = os.getenv(TOKEN_ENV)
    if not token:
        raise RuntimeError(
            f"{TOKEN_ENV} is not set. Add a Page access token as a GitHub Actions secret."
        )

    registry = load_json(REGISTRY_FILE, [])
    history = load_json(HISTORY_FILE, [])
    if not isinstance(registry, list):
        raise RuntimeError(f"{REGISTRY_FILE} must contain a JSON list.")
    if not isinstance(history, list):
        raise RuntimeError(f"{HISTORY_FILE} must contain a JSON list.")

    by_video = {str(row.get("video_id")): row for row in history if row.get("video_id")}
    collected = 0
    skipped = 0
    failures = []

    for item in registry:
        video_id = item.get("video_id")
        if not video_id:
            skipped += 1
            continue

        try:
            metrics = fetch_reel(str(video_id))
            by_video[str(video_id)] = build_record(item, metrics)
            collected += 1
        except Exception as exc:
            failures.append({"video_id": str(video_id), "error": str(exc)})

    updated = sorted(
        by_video.values(),
        key=lambda row: row.get("published_at") or "",
        reverse=True,
    )
    save_json(HISTORY_FILE, updated)

    summary = {
        "collected": collected,
        "skipped": skipped,
        "failures": failures,
        "history_records": len(updated),
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if failures:
        raise RuntimeError(f"{len(failures)} Reel insight request(s) failed.")


if __name__ == "__main__":
    collect()
