"""Read-only collector for INNER Discipline Facebook Page comments.

This diagnostic never posts, edits, hides, or deletes anything. It reads Page
posts and comments on Facebook Reels already registered by our publisher.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

VERSION = os.getenv("META_GRAPH_API_VERSION", "v27.0")
BASE = f"https://graph.facebook.com/{VERSION}"
PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "").strip()
TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip()
OUTPUT = Path(os.getenv("COMMENT_EXPORT_FILE", "comment_read_test.json"))
REGISTRY = Path(os.getenv("PUBLISHED_REELS_FILE", "published_reels.json"))
MAX_POSTS = int(os.getenv("COMMENT_TEST_MAX_POSTS", "25"))
MAX_REELS = int(os.getenv("COMMENT_TEST_MAX_REELS", "100"))
MAX_COMMENTS_PER_OBJECT = int(os.getenv("COMMENT_TEST_MAX_COMMENTS", "100"))
MAX_REPLIES_PER_COMMENT = int(os.getenv("COMMENT_TEST_MAX_REPLIES", "20"))


class MetaReadError(RuntimeError):
    pass


def get_json(path_or_url: str, params: dict | None = None) -> dict:
    if path_or_url.startswith("https://"):
        url = path_or_url
    else:
        query = dict(params or {})
        query["access_token"] = TOKEN
        url = f"{BASE}/{path_or_url.lstrip('/')}?{urllib.parse.urlencode(query)}"
    request = urllib.request.Request(
        url, headers={"User-Agent": "inner-discipline-comment-reader/1.0"}
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            error = payload.get("error", {})
            message = error.get("message", "Meta API request failed")
            code = error.get("code")
            subcode = error.get("error_subcode")
            raise MetaReadError(
                f"Meta Graph API error (HTTP {exc.code}, code {code}, "
                f"subcode {subcode}): {message}"
            ) from exc
        except (ValueError, json.JSONDecodeError):
            raise MetaReadError(f"Meta Graph API HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise MetaReadError(f"Could not connect to Meta Graph API: {exc.reason}") from exc
    if not isinstance(data, dict):
        raise MetaReadError("Meta returned an unexpected response format")
    if data.get("error"):
        error = data["error"]
        raise MetaReadError(
            f"Meta Graph API error (code {error.get('code')}): "
            f"{error.get('message', 'unknown error')}"
        )
    return data


def pages(path: str, params: dict, max_items: int):
    url = None
    first = True
    yielded = 0
    while yielded < max_items:
        payload = get_json(path, params) if first else get_json(url)
        first = False
        batch = payload.get("data", [])
        if not isinstance(batch, list):
            raise MetaReadError("Meta returned an invalid data collection")
        for item in batch:
            if yielded >= max_items:
                break
            yielded += 1
            yield item
        url = (payload.get("paging") or {}).get("next")
        if not url:
            break


def normalize_comment(comment: dict, source_id: str, source_type: str,
                      source_text: str, is_reply: bool = False) -> dict:
    author = comment.get("from") or {}
    parent = comment.get("parent") or {}
    return {
        "source_type": source_type,
        "source_id": source_id,
        "source_text": source_text,
        "comment_id": comment.get("id"),
        "parent_comment_id": parent.get("id") if is_reply else None,
        "is_reply": is_reply,
        "author_name": author.get("name"),
        "author_id": author.get("id"),
        "message": comment.get("message", ""),
        "created_time": comment.get("created_time"),
        "like_count": comment.get("like_count", 0),
        "reply_count": comment.get("comment_count", 0),
    }


def read_comments(object_id: str, source_type: str, source_text: str,
                  output: list, stats: dict) -> None:
    comments = list(pages(
        f"{object_id}/comments",
        {"fields": "id,message,created_time,from{id,name},like_count,comment_count,parent",
         "filter": "stream", "limit": 100},
        MAX_COMMENTS_PER_OBJECT,
    ))
    stats["objects_with_comments_checked"] += 1
    stats["top_level_comments_read"] += len(comments)
    for comment in comments:
        output.append(normalize_comment(comment, object_id, source_type, source_text))
        reply_count = int(comment.get("comment_count") or 0)
        if reply_count <= 0:
            continue
        try:
            replies = list(pages(
                f"{comment['id']}/comments",
                {"fields": "id,message,created_time,from{id,name},like_count,comment_count,parent",
                 "filter": "stream", "limit": 100},
                MAX_REPLIES_PER_COMMENT,
            ))
        except MetaReadError as exc:
            stats["reply_read_errors"] += 1
            stats["limited_errors"].append(
                {"object_id": object_id, "comment_id": comment.get("id"),
                 "error": str(exc)[:400]}
            )
            continue
        stats["replies_read"] += len(replies)
        for reply in replies:
            output.append(normalize_comment(
                reply, object_id, source_type, source_text, is_reply=True
            ))


def main() -> int:
    if not PAGE_ID or not TOKEN:
        raise MetaReadError("FACEBOOK_PAGE_ID and FACEBOOK_PAGE_ACCESS_TOKEN must be configured")
    # First verify the token can see the configured Page.
    page = get_json(PAGE_ID, {"fields": "id,name"})
    if str(page.get("id")) != PAGE_ID:
        raise MetaReadError("The token did not return the configured Page ID")

    comments = []
    stats = {
        "page_name": page.get("name"),
        "page_posts_checked": 0,
        "registered_reels_checked": 0,
        "objects_with_comments_checked": 0,
        "top_level_comments_read": 0,
        "replies_read": 0,
        "reply_read_errors": 0,
        "limited_errors": [],
    }

    # Page /posts is read-only and returns posts published by this Page.
    posts = list(pages(
        f"{PAGE_ID}/posts",
        {"fields": "id,message,created_time,permalink_url",
         "limit": min(MAX_POSTS, 100)},
        MAX_POSTS,
    ))
    stats["page_posts_checked"] = len(posts)
    for post in posts:
        read_comments(
            str(post["id"]), "facebook_post",
            post.get("message", ""), comments, stats
        )

    # The publisher registry contains the authoritative IDs for our published Reels.
    registry = []
    if REGISTRY.exists():
        try:
            registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise MetaReadError(f"Could not read {REGISTRY.name}: {exc}") from exc
    if not isinstance(registry, list):
        raise MetaReadError(f"{REGISTRY.name} must contain a JSON list")

    seen = set()
    for row in registry:
        video_id = str(row.get("video_id") or "")
        if not video_id or video_id in seen:
            continue
        seen.add(video_id)
        if stats["registered_reels_checked"] >= MAX_REELS:
            break
        stats["registered_reels_checked"] += 1
        try:
            read_comments(
                video_id, "facebook_reel",
                str(row.get("output_base") or ""), comments, stats
            )
        except MetaReadError as exc:
            stats["limited_errors"].append(
                {"object_id": video_id, "error": str(exc)[:400]}
            )

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": "READ_ONLY_NO_REPLIES_OR_MUTATIONS",
        "limits": {
            "max_posts": MAX_POSTS,
            "max_registered_reels": MAX_REELS,
            "max_comments_per_object": MAX_COMMENTS_PER_OBJECT,
            "max_replies_per_comment": MAX_REPLIES_PER_COMMENT,
        },
        "stats": stats,
        "comments": comments,
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(json.dumps({
        "status": "success",
        "mode": result["mode"],
        "page_name": stats["page_name"],
        "page_posts_checked": stats["page_posts_checked"],
        "registered_reels_checked": stats["registered_reels_checked"],
        "top_level_comments_read": stats["top_level_comments_read"],
        "replies_read": stats["replies_read"],
        "total_comment_records": len(comments),
        "read_errors": len(stats["limited_errors"]),
        "output_file": str(OUTPUT),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MetaReadError as exc:
        print(f"COMMENT READ TEST FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
