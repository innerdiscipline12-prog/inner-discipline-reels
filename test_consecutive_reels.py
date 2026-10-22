"""Integration smoke test: generate five consecutive reel scripts without rendering video."""
import random
import tempfile
import unittest
from pathlib import Path

class ConsecutiveGeneratorTests(unittest.TestCase):
    def test_five_consecutive_generated_reels_have_distinct_assets_and_valid_duration(self):
        try:
            import generate as gen
        except Exception as exc:
            self.fail(f"Could not import the actual reel generator: {exc}")

        with tempfile.TemporaryDirectory(prefix="inner-discipline-test-") as temp:
            temp_path = Path(temp)
            # Isolate rotation memory from repository state and from production history.
            gen.ROTATION_STATE_FILE = str(temp_path / "rotation_state.json")
            gen.HOOK_STATE_FILE = str(temp_path / "hook_state.json")
            gen.SERIES_STATE_FILE = str(temp_path / "series_state.json")
            gen.random.seed(20261022)

            scripts, covers, captions = [], [], []
            for index in range(5):
                script = gen.build_retention_reel_script()
                caption_full = gen.build_caption(script)
                caption = caption_full.split("\n\n", 1)[0]
                duration = float(getattr(script, "smart_duration", 0))

                self.assertGreaterEqual(duration, 12.0, f"reel {index + 1} is shorter than 12s")
                self.assertLessEqual(duration, 15.0, f"reel {index + 1} exceeds 15s")
                self.assertTrue(script.lines, f"reel {index + 1} has no spoken lines")
                self.assertEqual(
                    script.lines[-1], script.source_payoff,
                    f"reel {index + 1} lost the original payoff during shortening"
                )
                self.assertTrue(script.cover.strip(), f"reel {index + 1} has no cover")
                self.assertTrue(caption.strip(), f"reel {index + 1} has no caption")

                scripts.append(" | ".join(script.lines))
                covers.append(script.cover)
                captions.append(caption)

            from originality import similarity
            for asset_name, assets, threshold in (
                ("spoken script", scripts, 0.42),
                ("cover", covers, 0.35),
                ("caption", captions, 0.42),
            ):
                self.assertEqual(len(set(assets)), 5, f"{asset_name} repeated across the five reels")
                for i in range(len(assets)):
                    for j in range(i):
                        score = similarity(assets[i], assets[j])
                        self.assertLess(
                            score, threshold,
                            f"{asset_name} near-duplicate between reels {j + 1} and {i + 1}: {score:.3f}"
                        )

if __name__ == "__main__":
    unittest.main()
