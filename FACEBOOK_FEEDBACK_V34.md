# INNER Discipline Facebook Feedback Loop — V34

## What this does

The feedback loop connects published INNER Discipline Reels to the Meta Graph API and feeds the observed performance back into the V33 retention engine.

Flow:

`generate.py`
→ Reel metadata
→ Facebook publisher registers `video_id`
→ `published_reels.json`
→ `facebook_feedback.py`
→ Meta Reel Insights
→ `performance_history_v33.json`
→ `retention_engine.py`
→ future Reel selection

## Facebook data collected

For each registered Reel, the collector requests lifetime Reel insights including:

- Reel plays and replays
- unique impressions
- average watch time
- average watch percentage against the generated duration
- retention curve
- followers attributed to the Reel
- likes
- comments/shares social actions
- view time
- share/comment rate
- follow rate

Meta documents these Reel metrics on the Video Insights endpoint.

## GitHub secret

Add this repository secret:

`FACEBOOK_PAGE_ACCESS_TOKEN`

The token must be a Page access token for a person who can perform the Page's ANALYZE task. Meta currently documents `pages_manage_engagement` and `read_insights` as required for Video Insights.

No access token is stored in the repository.

## Publisher contract

After a Reel is successfully published, the Facebook posting engine must append a record like:

```json
{
  "video_id": "1234567890",
  "output_base": "outputs/reel_v33_...",
  "published_at": "2026-11-14T04:00:00+03:00",
  "category": "dangerous",
  "hook_family": "mirror",
  "retention_score": 8.5,
  "predicted_duration": 12.4
}
```

The collector uses `video_id` as the authoritative Facebook identity. This avoids trying to guess which Facebook Reel corresponds to which generated file.

## Learning behavior

The collector updates one record per Facebook video instead of appending duplicate daily copies.

The retention engine stays neutral until at least five observed Reels are available. After that, it learns small category and hook-family boosts from:

- average watch time
- average watch percentage
- completion/retention signal
- engagement rate
- follow rate

The learning boost is deliberately capped so Facebook noise cannot suddenly destroy the existing originality and retention rules.

## Schedule

The GitHub workflow runs once daily at 06:30 UTC, after Meta's normal insight update window, and can also be run manually.

No Facebook posting automation is enabled by this change.
