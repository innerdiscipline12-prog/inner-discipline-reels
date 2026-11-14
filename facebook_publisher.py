"""Publish the newest generated INNER Discipline MP4 as a Facebook Page Reel."""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs"
REGISTRY_FILE = ROOT / os.getenv("PUBLISHED_REELS_FILE", "published_reels.json")
GRAPH_VERSION = os.getenv("META_GRAPH_API_VERSION", "v27.0")
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"
TOKEN_ENV = "FACEBOOK_PAGE_ACCESS_TOKEN"
PAGE_ID_ENV = "FACEBOOK_PAGE_ID"


class FacebookPublishError(RuntimeError):
    pass


def _read_json_response(response: Any) -> dict[str, Any]:
    raw = response.read()
    try:
        payload = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FacebookPublishError("Meta returned a non-JSON response.") from exc
    if not isinstance(payload, dict):
        raise FacebookPublishError("Meta returned an unexpected response.")
    if payload.get("error"):
        error = payload["error"]
        message = error.get("message", "Unknown Graph API error") if isinstance(error, dict) else str(error)
        code = error.get("code") if isinstance(error, dict) else None
        raise FacebookPublishError(f"Meta Graph API error {code or ''}: {message}".strip())
    return payload


def _request_json(url: str, fields: dict[str, str], timeout: int = 90) -> dict[str, Any]:
    body = urllib.parse.urlencode(fields).encode("utf-8")
    request = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded",
                 "User-Agent": "inner-discipline-facebook-publisher/35"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return _read_json_response(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise FacebookPublishError(f"Meta request failed (HTTP {exc.code}): {detail[:1200]}") from exc
    except urllib.error.URLError as exc:
        raise FacebookPublishError(f"Could not reach Meta: {exc.reason}") from exc


def _upload_binary(upload_url: str, video_path: Path, token: str) -> dict[str, Any]:
    size = video_path.stat().st_size
    request = urllib.request.Request(
        upload_url,
        data=video_path.read_bytes(),
        headers={
            "Authorization": f"OAuth {token}",
            "Content-Type": "application/octet-stream",
            "offset": "0",
            "file_size": str(size),
            "User-Agent": "inner-discipline-facebook-publisher/35",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            payload = _read_json_response(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise FacebookPublishError(f"Facebook video upload failed (HTTP {exc.code}): {detail[:1200]}") from exc
    except urllib.error.URLError as exc:
        raise FacebookPublishError(f"Facebook video upload connection failed: {exc.reason}") from exc
    if payload.get("success") is False:
        raise FacebookPublishError(f"Facebook rejected the video upload: {payload}")
    return payload


def _read_text(path: Path, fallback: str = "") -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return fallback


def metadata_for(video_path: Path) -> dict[str, Any]:
    base = video_path.with_suffix("")
    retention_path = Path(f"{base}_retention.json")
    try:
        retention = json.loads(retention_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        retention = {}
    except json.JSONDecodeError as exc:
        raise FacebookPublishError(f"Invalid retention metadata JSON: {retention_path}") from exc
    title = _read_text(Path(f"{base}_title.txt"), "INNER Discipline")
    caption = _read_text(Path(f"{base}_caption.txt"), title) or title
    return {
        "title": title[:100],
        "description": caption[:5000],
        "category": str(retention.get("category") or "general"),
        "hook_family": str(retention.get("hook_family") or "general"),
        "retention_score": retention.get("retention_score"),
        "predicted_duration": retention.get("predicted_duration"),
    }


def find_latest_video(output_dir: Path = OUTPUT_DIR) -> Path:
    candidates = [p for p in output_dir.glob("*.mp4") if p.is_file() and p.stat().st_size > 0]
    if not candidates:
        raise FacebookPublishError(f"No non-empty MP4 was found in {output_dir}.")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def load_registry() -> list[dict[str, Any]]:
    if not REGISTRY_FILE.exists():
        return []
    try:
        value = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FacebookPublishError(f"{REGISTRY_FILE.name} contains invalid JSON.") from exc
    if not isinstance(value, list):
        raise FacebookPublishError(f"{REGISTRY_FILE.name} must contain a JSON list.")
    return value


def publish_reel(video_path: Path, page_id: str, token: str, metadata: dict[str, Any]) -> dict[str, Any]:
    if video_path.suffix.lower() != ".mp4" or not video_path.is_file() or video_path.stat().st_size <= 0:
        raise FacebookPublishError("The selected video must be a non-empty MP4 file.")
    endpoint = f"{GRAPH_BASE}/{urllib.parse.quote(page_id, safe='')}/video_reels"
    start = _request_json(endpoint, {"upload_phase": "START", "access_token": token})
    video_id = str(start.get("video_id") or "")
    upload_url = start.get("upload_url")
    if not video_id:
        raise FacebookPublishError(f"Meta did not return a video_id when starting the upload: {start}")
    if not upload_url:
        upload_url = f"https://rupload.facebook.com/video-upload/{GRAPH_VERSION}/{video_id}"
    if not str(upload_url).startswith("https://"):
        raise FacebookPublishError("Meta returned an invalid upload URL.")
    _upload_binary(str(upload_url), video_path, token)
    finish = _request_json(endpoint, {
        "upload_phase": "FINISH",
        "video_id": video_id,
        "video_state": "PUBLISHED",
        "title": metadata["title"],
        "description": metadata["description"],
        "access_token": token,
    })
    if finish.get("success") is False:
        raise FacebookPublishError(f"Meta did not confirm Reel publication: {finish}")
    return {
        "video_id": str(finish.get("video_id") or video_id),
        "post_id": finish.get("post_id"),
        "message": finish.get("message"),
    }


def register_publication(video_path: Path, result: dict[str, Any], metadata: dict[str, Any]) -> None:
    registry = load_registry()
    relative_video = str(video_path.resolve().relative_to(ROOT))
    output_base = str(Path(relative_video).with_suffix(""))
    if any(row.get("output_base") == output_base for row in registry):
        raise FacebookPublishError("This generated video is already registered; refusing to register it twice.")
    registry.append({
        "video_id": str(result["video_id"]),
        "post_id": result.get("post_id"),
        "output_base": output_base,
        "published_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "category": metadata["category"],
        "hook_family": metadata["hook_family"],
        "retention_score": metadata["retention_score"],
        "predicted_duration": metadata["predicted_duration"],
    })
    REGISTRY_FILE.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish the newest INNER Discipline Reel to Facebook.")
    parser.add_argument("--video", help="Optional path to a specific MP4. Defaults to newest MP4 in outputs/.")
    args = parser.parse_args()
    page_id = os.getenv(PAGE_ID_ENV, "").strip()
    token = os.getenv(TOKEN_ENV, "").strip()
    if not page_id or not token:
        raise FacebookPublishError(f"Missing {PAGE_ID_ENV} or {TOKEN_ENV}. Configure both as GitHub Actions secrets.")
    video_path = Path(args.video).expanduser() if args.video else find_latest_video()
    if not video_path.is_absolute():
        video_path = (ROOT / video_path).resolve()
    metadata = metadata_for(video_path)
    relative_base = str(video_path.resolve().relative_to(ROOT).with_suffix(""))
    if any(row.get("output_base") == relative_base for row in load_registry()):
        print(f"SKIPPED: {video_path.name} is already registered as published.")
        return 0
    print(f"Publishing {video_path.name} to the configured Facebook Page...")
    result = publish_reel(video_path, page_id, token, metadata)
    register_publication(video_path, result, metadata)
    print(json.dumps({
        "status": "published", "video_id": result["video_id"],
        "post_id": result.get("post_id"), "file": video_path.name,
        "registry": REGISTRY_FILE.name,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FacebookPublishError as exc:
        print(f"FACEBOOK PUBLISH FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
