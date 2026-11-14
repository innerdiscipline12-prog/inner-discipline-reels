import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import instagram_publisher as publisher


class InstagramPublisherTests(unittest.TestCase):
    def test_metadata_reads_generator_caption(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "sample.mp4"
            video.touch()
            Path(tmp, "sample_title.txt").write_text("OWN TODAY", encoding="utf-8")
            Path(tmp, "sample_caption.txt").write_text("Keep your word.", encoding="utf-8")
            self.assertEqual(publisher.metadata_for(video)["caption"], "Keep your word.")

    def test_publish_reel_runs_resumable_upload_status_and_publish(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "sample.mp4"
            video.write_bytes(b"video-bytes")
            container = {"id": "container-123", "uri": "https://rupload.facebook.com/ig-api-upload/container-123"}
            published = {"id": "media-456"}
            status = {"status_code": "FINISHED", "status": "Finished"}
            details = {"permalink": "https://www.instagram.com/reel/example/"}
            with (
                patch.object(publisher, "_post", side_effect=[container, published]) as post,
                patch.object(publisher, "upload_binary") as upload,
                patch.object(publisher, "_get", side_effect=[status, details]),
            ):
                result = publisher.publish_reel(video, "ig-user-1", "secret-token", "Caption")
            self.assertEqual(result["media_id"], "media-456")
            self.assertEqual(result["permalink"], details["permalink"])
            self.assertEqual(post.call_count, 2)
            self.assertEqual(post.call_args_list[0].args[1]["media_type"], "REELS")
            self.assertEqual(post.call_args_list[0].args[1]["upload_type"], "resumable")
            self.assertEqual(post.call_args_list[1].args[1]["creation_id"], "container-123")
            upload.assert_called_once_with(container["uri"], video, "secret-token")

    def test_register_publication_writes_idempotency_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "reel.mp4"
            video.write_bytes(b"video")
            registry = root / "published_instagram_reels.json"
            with patch.object(publisher, "ROOT", root), patch.object(publisher, "REGISTRY_FILE", registry):
                publisher.register_publication(video, {
                    "media_id": "media-1", "container_id": "container-1",
                    "permalink": "https://www.instagram.com/reel/example/",
                })
                rows = json.loads(registry.read_text(encoding="utf-8"))
            self.assertEqual(rows[0]["media_id"], "media-1")
            self.assertEqual(rows[0]["output_base"], "reel")
            self.assertIn("published_at", rows[0])


if __name__ == "__main__":
    unittest.main()
