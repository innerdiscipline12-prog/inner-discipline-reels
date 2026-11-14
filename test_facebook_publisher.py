import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import facebook_publisher as publisher


class PublisherTests(unittest.TestCase):
    def test_metadata_reads_generator_sidecars(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "sample.mp4"
            video.touch()
            Path(tmp, "sample_title.txt").write_text("OWN TODAY", encoding="utf-8")
            Path(tmp, "sample_caption.txt").write_text("Keep your word.", encoding="utf-8")
            Path(tmp, "sample_retention.json").write_text(json.dumps({
                "category": "discipline", "hook_family": "mirror",
                "retention_score": 8.2, "predicted_duration": 12.5,
            }), encoding="utf-8")
            metadata = publisher.metadata_for(video)
            self.assertEqual(metadata["title"], "OWN TODAY")
            self.assertEqual(metadata["description"], "Keep your word.")
            self.assertEqual(metadata["category"], "discipline")
            self.assertEqual(metadata["hook_family"], "mirror")
            self.assertEqual(metadata["retention_score"], 8.2)
            self.assertEqual(metadata["predicted_duration"], 12.5)

    def test_find_latest_video_ignores_empty_and_non_mp4(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "empty.mp4").touch()
            (root / "notes.txt").write_text("x", encoding="utf-8")
            good = root / "reel.mp4"
            good.write_bytes(b"video")
            self.assertEqual(publisher.find_latest_video(root), good)

    def test_publish_reel_runs_start_upload_finish(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "sample.mp4"
            video.write_bytes(b"video-bytes")
            metadata = {
                "title": "OWN TODAY",
                "description": "Keep your word.",
                "category": "discipline",
                "hook_family": "mirror",
                "retention_score": 8.0,
                "predicted_duration": 12.0,
            }
            start = {"video_id": "12345", "upload_url": "https://rupload.facebook.com/upload/12345"}
            finish = {"success": True, "video_id": "12345", "post_id": "67890"}
            with (
                patch.object(publisher, "_request_json", side_effect=[start, finish]) as request_json,
                patch.object(publisher, "_upload_binary") as upload,
            ):
                result = publisher.publish_reel(video, "page-1", "secret-token", metadata)
            self.assertEqual(result["video_id"], "12345")
            self.assertEqual(result["post_id"], "67890")
            self.assertEqual(request_json.call_count, 2)
            self.assertEqual(request_json.call_args_list[0].args[1]["upload_phase"], "START")
            self.assertEqual(request_json.call_args_list[1].args[1]["upload_phase"], "FINISH")
            self.assertEqual(request_json.call_args_list[1].args[1]["video_state"], "PUBLISHED")
            upload.assert_called_once_with(start["upload_url"], video, "secret-token")

    def test_register_publication_writes_feedback_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "reel.mp4"
            video.write_bytes(b"video")
            registry = root / "published_reels.json"
            metadata = {
                "category": "discipline", "hook_family": "mirror",
                "retention_score": 8.0, "predicted_duration": 12.0,
            }
            with patch.object(publisher, "ROOT", root), patch.object(publisher, "REGISTRY_FILE", registry):
                publisher.register_publication(video, {"video_id": "987", "post_id": "654"}, metadata)
                rows = json.loads(registry.read_text(encoding="utf-8"))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["video_id"], "987")
            self.assertEqual(rows[0]["post_id"], "654")
            self.assertEqual(rows[0]["output_base"], "reel")
            self.assertEqual(rows[0]["hook_family"], "mirror")
            self.assertIn("published_at", rows[0])


if __name__ == "__main__":
    unittest.main()
