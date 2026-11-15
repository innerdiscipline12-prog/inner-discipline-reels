"""Dry-run-only Facebook comment reply planner for INNER Discipline.

This version NEVER posts replies. It reads the diagnostic export, filters
eligible top-level comments, drafts concise replies, and writes a GitHub
Actions job summary for human review.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

INPUT = Path(os.getenv("COMMENT_EXPORT_FILE", "comment_read_test.json"))
SUMMARY = os.getenv("GITHUB_STEP_SUMMARY")
API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
MAX_DRAFTS = int(os.getenv("COMMENT_RESPONDER_MAX_DRAFTS", "10"))

SENSITIVE_TERMS = (
    "suicide", "kill myself", "self harm", "self-harm", "overdose",
    "cancer", "diagnosed", "depression medication", "bank account",
    "password", "my address", "rape", "abuse",
)


class ResponderError(RuntimeError):
    pass


def should_skip(comment: dict, page_replied_to: set[str]) -> str | None:
    message = str(comment.get("message") or "").strip()
    comment_id = str(comment.get("comment_id") or "")
    if not comment_id:
        return "missing comment ID"
    if comment.get("is_reply"):
        return "not a top-level comment"
    if comment.get("is_page_author"):
        return "written by the Page"
    if comment_id in page_replied_to:
        return "Page has already replied"
    if len(message) < 3 or not re.search(r"[A-Za-z0-9]", message):
        return "empty or emoji-only"
    if any(term in message.lower() for term in SENSITIVE_TERMS):
        return "sensitive personal or safety-related disclosure"
    if len(message) > 2000:
        return "unusually long comment; manual review"
    return None


def draft_reply(comment: dict) -> str:
    if not API_KEY:
        raise ResponderError(
            "OPENAI_API_KEY is not configured in GitHub Actions secrets. "
            "Add it under Settings > Secrets and variables > Actions."
        )
    prompt = (
        "Write one natural reply to this Facebook comment for INNER Discipline. "
        "Voice: direct, grounded, disciplined, masculine but respectful. "
        "Sound like a real page admin, not a motivational quote generator. "
        "Respond to the actual point; do not merely repeat the comment. "
        "One sentence, ideally under 180 characters and never over 240. "
        "No hashtags, no sales pitch, no generic 'Thanks for sharing', "
        "no insults, no medical/financial/legal advice. Return only the reply.\n\n"
        f"Post context: {str(comment.get('source_text') or '')[:1200]}\n"
        f"Comment: {str(comment.get('message') or '')[:2000]}"
    )
    body = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You write concise, context-aware community replies."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.6,
        "max_tokens": 100,
    }).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "inner-discipline-comment-responder-dry-run/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ResponderError(
            f"OpenAI API request failed (HTTP {exc.code}): {detail[:800]}"
        ) from exc
    except urllib.error.URLError as exc:
        raise ResponderError(f"Could not reach OpenAI API: {exc.reason}") from exc
    try:
        reply = str(payload["choices"][0]["message"]["content"]).strip().strip('"')
    except (KeyError, IndexError, TypeError) as exc:
        raise ResponderError("OpenAI returned an unexpected reply format.") from exc
    if not reply or len(reply) > 240 or "\n" in reply:
        raise ResponderError("Generated reply failed length/format validation.")
    return reply


def main() -> int:
    if not INPUT.exists():
        raise ResponderError(f"Comment export not found: {INPUT}")
    try:
        data = json.loads(INPUT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResponderError(f"Could not read comment export: {exc}") from exc
    comments = data.get("comments", [])
    page_replied_to = {
        str(row.get("parent_comment_id"))
        for row in comments
        if row.get("is_reply") and row.get("is_page_author") and row.get("parent_comment_id")
    }

    eligible = []
    skipped: dict[str, int] = {}
    seen: set[str] = set()
    for row in comments:
        reason = should_skip(row, page_replied_to)
        if reason:
            skipped[reason] = skipped.get(reason, 0) + 1
            continue
        cid = str(row.get("comment_id"))
        if cid in seen:
            continue
        seen.add(cid)
        eligible.append(row)
    eligible.sort(key=lambda row: str(row.get("created_time") or ""))
    eligible = eligible[:MAX_DRAFTS]

    drafts = []
    for row in eligible:
        drafts.append({
            "comment_id": row.get("comment_id"),
            "comment": str(row.get("message") or "")[:500],
            "reply": draft_reply(row),
            "source_type": row.get("source_type"),
            "created_time": row.get("created_time"),
        })

    lines = [
        "# INNER Discipline — Facebook comment reply dry run",
        "",
        "**Mode: DRY RUN ONLY — no replies were published.**",
        "",
        f"- Comments scanned: {len(comments)}",
        f"- Eligible comments drafted: {len(drafts)}",
        f"- Existing Page replies detected: {len(page_replied_to)}",
        f"- Draft limit per run: {MAX_DRAFTS}",
        "",
        "## Proposed replies",
        "",
    ]
    if not drafts:
        lines.append("No eligible new top-level comments found.")
    for index, item in enumerate(drafts, 1):
        lines.extend([
            f"### {index}. {item['source_type']} · {item['comment_id']}",
            f"> {item['comment']}",
            "",
            f"**Draft:** {item['reply']}",
            "",
        ])
    lines.extend(["## Skipped comments", ""])
    if skipped:
        for reason, count in sorted(skipped.items()):
            lines.append(f"- {reason}: {count}")
    else:
        lines.append("- None")
    summary = "\n".join(lines) + "\n"
    print(summary)
    if SUMMARY:
        with open(SUMMARY, "a", encoding="utf-8") as handle:
            handle.write(summary)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ResponderError as exc:
        print(f"COMMENT RESPONDER DRY RUN FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
