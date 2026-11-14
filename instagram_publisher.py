"""Publish an INNER Discipline Reel to the linked Instagram professional account."""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs"
REGISTRY_FILE = ROOT / "published_instagram_reels.json"
GRAPH_VERSION = os.getenv("META_GRAPH_API_VERSION", "v27.0")
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"
TOKEN_ENV = "INSTAGRAM_ACCESS_TOKEN"
ACCOUNT_ENV = "INSTAGRAM_USER_ID"


class InstagramPublishError(RuntimeError):
    pass


def _json_response(response: Any) -> dict[str, Any]:
    raw = response.read()
    try:
        payload = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InstagramPublishError("Meta returned a non-JSON response.") from exc
    if not isinstance(payload, dict):
        raise InstagramPublishError("Meta returned an unexpected response.")
    if payload.get("error"):
        error = payload["error"]
        message = error.get("message", "Unknown Graph API error") if isinstance(error, dict) else str(error)
        code = error.get("code") if isinstance(error, dict) else None
        raise InstagramPublishError(f"Meta Graph API error {code or ''}: {message}".strip())
    return payload


def _post(url: str, fields: dict[str, str], timeout: int = 90) -> dict[str, Any]:
    body = urllib.parse.urlencode(fields).encode("utf-8")
    request = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded",
                 "User-Agent": "inner-discipline-instagram-publisher/1"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return _json_response(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise InstagramPublishError(f"Instagram request failed (HTTP {exc.code}): {detail[:1200]}") from exc
    except urllib.error.URLError as exc:
        raise InstagramPublishError(f"Could not reach Meta: {exc.reason}") from exc


def _get(url: str, fields: dict[str, str], timeout: int = 60) -> dict[str, Any]:
    request_url = url + "?" + urllib.parse.urlencode(fields)
    request = urllib.request.Request(request_url, headers={"User-Agent": "inner-discipline-instagram-publisher/1"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return _json_response(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise InstagramPublishError(f"Instagram status request failed (HTTP {exc.code}): {detail[:1200]}") from exc
    except urllib.error.URLError as exc:
        raise InstagramPublishError(f"Could not reach Meta: {exc.reason}") from exc


def metadata_for(video_path: Path) -> dict[str, str]:
    base = video_path.with_suffix("")
    title_path = Path(f"{base}_title.txt")
    caption_path = Path(f"{base}_caption.txt")
    title = title_path.read_text(encoding="utf-8").strip() if title_path.exists() else "INNER Discipline"
    caption = caption_path.read_text(encoding="utf-8").strip() if caption_path.exists() else title
    return {"title": title[:100], "caption": (caption or title)[:2200]}


def find_latest_video(output_dir: Path = OUTPUT_DIR) -> Path:
    candidates = [p for p in output_dir.glob("*.mp4") if p.is_file() and p.stat().st_size > 0]
    if not candidates:
        raise InstagramPublishError(f"No non-empty MP4 was found in {output_dir}.")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def load_registry() -> list[dict[str, Any]]:
    if not REGISTRY_FILE.exists():
        return []
    try:
        data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InstagramPublishError(f"{REGISTRY_FILE.name} contains invalid JSON.") from exc
    if not isinstance(data, list):
        raise InstagramPublishError(f"{REGISTRY_FILE.name} must contain a JSON list.")
    return data


def upload_binary(upload_uri: str, video_path: Path, token: str) -> dict[str, Any]:
    size = video_path.stat().st_size
    request = urllib.request.Request(
        upload_uri,
        data=video_path.read_bytes(),
        headers={
            "Authorization": f"OAuth {token}",
            "Content-Type": "application/octet-stream",
            "offset": "0",
            "file_size": str(size),
            "User-Agent": "inner-discipline-instagram-publisher/1",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            payload = _json_response(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise InstagramPublishError(f"Instagram video upload failed (HTTP {exc.code}): {detail[:1200]}") from exc
    except urllib.error.URLError as exc:
        raise InstagramPublishError(f"Instagram video upload connection failed: {exc.reason}") from exc
    if payload.get("success") is False:
        raise InstagramPublishError(f"Instagram rejected the video upload: {payload}")
    return payload


def publish_reel(video_path: Path, account_id: str, token: str, caption: str) -> dict[str, Any]:
    if video_path.suffix.lower() != ".mp4" or not video_path.is_file() or video_path.stat().st_size <= 0:
        raise InstagramPublishError("The selected video must be a non-empty MP4 file.")

    container = _post(f"{GRAPH_BASE}/{urllib.parse.quote(account_id, safe='')}/media", {
        "media_type": "REELS",
        "upload_type": "resumable",
        "caption": caption,
        "share_to_feed": "true",
        "access_token": token,
    })
    container_id = str(container.get("id") or "")
    if not container_id:
        raise InstagramPublishError(f"Meta did not return a media container ID: {container}")
    upload_uri = str(container.get("uri") or f"https://rupload.facebook.com/ig-api-upload/{container_id}")
    if not upload_uri.startswith("https://rupload.facebook.com/"):
        raise InstagramPublishError("Meta returned an unexpected Instagram upload URI.")

    upload_binary(upload_uri, video_path, token)

    status_url = f"{GRAPH_BASE}/{urllib.parse.quote(container_id, safe='')}"
    status = {}
    for attempt in range(20):
        status = _get(status_url, {"fields": "status_code,status", "access_token": token})
        code = str(status.get("status_code") or "").upper()
        if code == "FINISHED":
            break
        if code in {"ERROR", "EXPIRED"}:
            raise InstagramPublishError(f"Instagram Reel processing failed: {status.get('status') or code}")
        time.sleep(15)
    else:
        raise InstagramPublishError(f"Instagram Reel did not finish processing in time: {status}")

    published = _post(f"{GRAPH_BASE}/{urllib.parse.quote(account_id, safe='')}/media_publish", {
        "creation_id": container_id,
        "access_token": token,
    })
    media_id = str(published.get("id") or "")
    if not media_id:
        raise InstagramPublishError(f"Meta did not confirm Instagram publication: {published}")

    permalink = None
    try:
        details = _get(f"{GRAPH_BASE}/{urllib.parse.quote(media_id, safe='')}", {
            "fields": "permalink,media_product_type",
            "access_token": token,
        })
        permalink = details.get("permalink")
    except InstagramPublishError:
        pass

    return {"media_id": media_id, "container_id": container_id, "permalink": permalink}


def register_publication(video_path: Path, result: dict[str, Any]) -> None:
    registry = load_registry()
    relative_video = str(video_path.resolve().relative_to(ROOT))
    output_base = str(Path(relative_video).with_suffix(""))
    if any(row.get("output_base") == output_base for row in registry):
        raise InstagramPublishError("This generated video is already registered as published on Instagram.")
    registry.append({
        "media_id": str(result["media_id"]),
        "container_id": str(result["container_id"]),
        "permalink": result.get("permalink"),
        "output_base": output_base,
        "published_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    REGISTRY_FILE.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    token = os.getenv(TOKEN_ENV, "").strip()
    account_id = os.getenv(ACCOUNT_ENV, "").strip()
    if not token or not account_id:
        raise InstagramPublishError(f"Missing {TOKEN_ENV} or {ACCOUNT_ENV}. Configure both in GitHub Actions.")
    video_path = find_latest_video()
    relative_base = str(video_path.resolve().relative_to(ROOT).with_suffix(""))
    if any(row.get("output_base") == relative_base for row in load_registry()):
        print(f"SKIPPED: {video_path.name} is already registered as published on Instagram.")
        return 0
    metadata = metadata_for(video_path)
    print(f"Publishing {video_path.name} to Instagram...")
    result = publish_reel(video_path, account_id, token, metadata["caption"])
    register_publication(video_path, result)
    print(json.dumps({
        "status": "published",
        "instagram_media_id": result["media_id"],
        "permalink": result.get("permalink"),
        "file": video_path.name,
        "registry": REGISTRY_FILE.name,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InstagramPublishError as exc:
        print(f"INSTAGRAM PUBLISH FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
