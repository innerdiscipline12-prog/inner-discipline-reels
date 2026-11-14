# INNER Discipline Facebook Publisher — V35

This is a separate publishing adapter. It does not edit generate.py or the V34 feedback collector.

## Flow

1. The existing Inner Discipline workflow generates an MP4 and uploads the outputs artifact.
2. After a successful main-branch push run, this workflow downloads that exact artifact.
3. facebook_publisher.py reads the generated title, caption and retention JSON sidecars.
4. It initializes a Page Reel upload, transfers the MP4 binary to Meta's upload URL, and finishes the upload with video_state=PUBLISHED.
5. Only after Meta confirms publication, the returned video_id and generation metadata are appended to published_reels.json.
6. The existing V34 feedback workflow can then collect insights for that video ID.

## Required GitHub Actions secrets

- FACEBOOK_PAGE_ID
- FACEBOOK_PAGE_ACCESS_TOKEN

Never put either value in source code, workflow YAML, logs, or chat.

## Meta API

Uses Graph API v27.0 and the Page Reels publishing endpoint /{page-id}/video_reels with START, binary upload, and FINISH phases. The local binary upload includes the required file_size and offset headers.

## Safety and retry behavior

- The existing generation workflow and V34 feedback workflow are not modified.
- Publisher tests run before every publishing attempt.
- The workflow only automatically publishes after a successful push event on main; pull-request builds do not publish.
- A video already present in published_reels.json is skipped to prevent duplicate publication on workflow retries.
- A failed upload or publish does not register a video ID.
- The registry commit is ignored by the existing generator workflow's paths-ignore rule, preventing a publish/commit loop.

## Manual run

workflow_dispatch is available for a repository-relative MP4 already present on main; supply video_path. Normal automatic operation uses the generator artifact and requires no manual path.

## Note on insights permissions

The publisher needs the Reels publishing permissions documented by Meta: pages_show_list, pages_read_engagement, and pages_manage_posts. The existing V34 insights collector separately documents pages_manage_engagement and read_insights; those must be granted for performance collection and are not required by this upload adapter.
