import os
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

import facebook_feedback as fb


class FeedbackTests(unittest.TestCase):
    def test_retention_curve_and_record(self):
        metrics = {
            "data": [
                {"name": "fb_reels_total_plays", "values": [{"value": 1000}]},
                {"name": "post_video_avg_time_watched", "values": [{"value": 5500}]},
                {"name": "post_video_retention_graph", "values": [{"value": [100, 80, 60, 40]}]},
                {"name": "post_video_followers", "values": [{"value": 20}]},
                {"name": "post_video_likes_by_reaction_type", "values": [{"value": {"like": 100, "love": 10}}]},
                {"name": "post_video_social_actions", "values": [{"value": {"comments": 15, "shares": 25}}]},
            ]
        }
        item = {
            "video_id": "123",
            "category": "dangerous",
            "hook_family": "mirror",
            "predicted_duration": 12.0,
        }
        row = fb.build_record(item, metrics)
        self.assertEqual(row["plays"], 1000)
        self.assertAlmostEqual(row["average_watch_time"], 5.5)
        self.assertAlmostEqual(row["average_watch_pct"], 5.5 / 12.0)
        self.assertEqual(row["completion_rate"], 40.0)
        self.assertEqual(row["likes"], 110.0)
        self.assertEqual(row["social_actions"], 40.0)
        self.assertAlmostEqual(row["follow_rate"], 0.02)

    def test_fetch_uses_lifetime_and_all_reel_metrics(self):
        with patch.object(fb, "api_get", return_value={"data": []}) as mocked:
            fb.os.environ["FACEBOOK_PAGE_ACCESS_TOKEN"] = "test"
            fb.fetch_reel("123")
            args = mocked.call_args.args
            kwargs = mocked.call_args.args[1]
            self.assertEqual(args[0], "123/video_insights")
            self.assertEqual(kwargs["period"], "lifetime")
            self.assertIn("post_video_avg_time_watched", kwargs["metric"])

    def test_api_get_preserves_meta_http_error_details(self):
        payload = (
            b'{"error":{"message":"Invalid parameter","type":"OAuthException",'
            b'"code":100,"error_subcode":12345}}'
        )
        error = urllib.error.HTTPError(
            "https://graph.facebook.com/v27.0/123/video_insights",
            400,
            "Bad Request",
            {},
            None,
        )
        error.read = lambda: payload
        with patch("facebook_feedback.urllib.request.urlopen", side_effect=error):
            with self.assertRaises(fb.MetaAPIError) as raised:
                fb.api_get("123/video_insights", {"metric": "x", "period": "lifetime"})
        self.assertEqual(raised.exception.status, 400)
        self.assertEqual(raised.exception.code, 100)
        self.assertEqual(raised.exception.subcode, 12345)
        self.assertIn("Invalid parameter", str(raised.exception))

    def test_collect_preserves_history_when_reel_insight_fails(self):
        registry = [
            {"video_id": "bad", "published_at": "2026-11-20T00:00:00Z"},
            {"video_id": "good", "published_at": "2026-11-19T00:00:00Z"},
        ]
        history = [
            {"video_id": "old", "published_at": "2026-11-18T00:00:00Z"}
        ]
        metrics = {"data": [{"name": "fb_reels_total_plays", "value": 5}]}

        with tempfile.TemporaryDirectory() as tmp:
            registry_path = os.path.join(tmp, "published.json")
            history_path = os.path.join(tmp, "history.json")
            fb.save_json(registry_path, registry)
            fb.save_json(history_path, history)

            def fake_fetch(video_id):
                if video_id == "bad":
                    raise fb.MetaAPIError(
                        "Permission denied", status=400,
                        payload={"error": {"message": "Permission denied", "code": 200}},
                    )
                return metrics

            with patch.object(fb, "REGISTRY_FILE", registry_path),                  patch.object(fb, "HISTORY_FILE", history_path),                  patch.dict(fb.os.environ, {fb.TOKEN_ENV: "test"}, clear=False),                  patch.object(fb, "fetch_reel", side_effect=fake_fetch):
                fb.collect()

            saved = fb.load_json(history_path, [])
            self.assertEqual({row["video_id"] for row in saved}, {"old", "good"})


if __name__ == "__main__":
    unittest.main()
