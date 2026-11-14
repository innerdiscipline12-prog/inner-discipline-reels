import json
import os
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
