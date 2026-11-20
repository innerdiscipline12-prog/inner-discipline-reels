"""Integration smoke test: generate twenty consecutive reel scripts without rendering video."""
import random
import tempfile
import unittest
from pathlib import Path

class ConsecutiveGeneratorTests(unittest.TestCase):
    def test_quality_preflight_retries_after_a_low_score_candidate(self):
        try:
            import generate as gen
        except Exception as exc:
            self.fail(f"Could not import the actual reel generator: {exc}")

        from unittest.mock import patch
        accepted = object()
        with patch.object(
            gen,
            "build_script",
            side_effect=[ValueError("V33 RETENTION SCORE TOO LOW"), accepted],
        ) as mocked:
            result = gen.build_script_with_quality_retries(max_attempts=3)

        self.assertIs(result, accepted)
        self.assertEqual(mocked.call_count, 2)

    def test_quality_preflight_fails_clearly_after_exhausting_retries(self):
        try:
            import generate as gen
        except Exception as exc:
            self.fail(f"Could not import the actual reel generator: {exc}")

        from unittest.mock import patch
        with patch.object(
            gen,
            "build_script",
            side_effect=ValueError("V33 RETENTION SCORE TOO LOW"),
        ) as mocked:
            with self.assertRaisesRegex(RuntimeError, "SCRIPT QUALITY PREFLIGHT FAILED"):
                gen.build_script_with_quality_retries(max_attempts=3)

        self.assertEqual(mocked.call_count, 3)

    def test_twenty_consecutive_generated_reels_have_distinct_assets_and_valid_duration(self):
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
            for index in range(20):
                script = gen.build_script_with_quality_retries()
                caption_full = gen.build_caption(script)
                caption = caption_full.split("\n\n", 1)[0]
                duration = float(getattr(script, "smart_duration", 0))

                self.assertGreaterEqual(duration, 12.0, f"reel {index + 1} is shorter than 12s")
                self.assertLessEqual(duration, 15.0, f"reel {index + 1} exceeds 15s")
                self.assertTrue(script.lines, f"reel {index + 1} has no spoken lines")
                self.assertGreaterEqual(len(script.lines), 3, f"reel {index + 1} has fewer than three voice lines")
                self.assertLessEqual(len(script.lines), 4, f"reel {index + 1} has more than four voice lines")
                self.assertLessEqual(
                    sum(len(line.split()) for line in script.lines), 21,
                    f"reel {index + 1} exceeds the 21-word narration budget"
                )
                for line_number, line in enumerate(script.lines, start=1):
                    self.assertLessEqual(
                        len(line.split()), 11,
                        f"reel {index + 1}, line {line_number} exceeds eleven words"
                    )
                self.assertEqual(
                    script.lines[-1], script.source_payoff,
                    f"reel {index + 1} lost the original payoff during shortening"
                )
                self.assertNotIn(
                    script.lines[-1].strip().lower().strip(" .!?"),
                    {"every time", "quietly", "for real", "not forever", "before it hurts",
                     "at a time", "not before", "until it hurts", "then again"},
                    f"reel {index + 1} ends on a dangling fragment"
                )
                broken_fragments = {
                    "is not starting", "is not motivation", "is not the goal",
                    "is the part that changes you", "with excuses",
                    "that sound reasonable", "but still cost you", "at a time",
                    "and no mood is helping", "for it to matter", "for it to count",
                }
                normalized_lines = {
                    line.strip().lower().strip(" .!?")
                    for line in script.lines
                }
                for fragment in broken_fragments:
                    self.assertNotIn(
                        fragment, normalized_lines,
                        f"reel {index + 1} contains a standalone broken fragment: {fragment}"
                    )
                self.assertTrue(script.cover.strip(), f"reel {index + 1} has no cover")
                self.assertTrue(caption.strip(), f"reel {index + 1} has no caption")

                self.assertGreaterEqual(
                    float(getattr(script, "v33_retention_score", 0)),
                    gen.RETENTION_SCORE_MIN,
                    f"reel {index + 1} failed the V33 retention score gate",
                )
                from retention_engine import is_swipe_risk_hook, opening_score, OPENING_SCORE_MIN
                self.assertFalse(
                    is_swipe_risk_hook(script.lines[0]),
                    f"reel {index + 1} starts with a swipe-risk hook",
                )
                self.assertGreaterEqual(
                    opening_score(script.lines),
                    OPENING_SCORE_MIN,
                    f"reel {index + 1} does not have a strong psychological/emotional opening",
                )

                scripts.append(" | ".join(script.lines))
                covers.append(script.cover)
                captions.append(caption)

            from originality import similarity
            for asset_name, assets, threshold in (
                ("spoken script", scripts, 0.42),
                ("cover", covers, 0.35),
                ("caption", captions, 0.42),
            ):
                self.assertEqual(len(set(assets)), 20, f"{asset_name} repeated across the twenty reels")
                for i in range(len(assets)):
                    for j in range(i):
                        score = similarity(assets[i], assets[j])
                        self.assertLess(
                            score, threshold,
                            f"{asset_name} near-duplicate between reels {j + 1} and {i + 1}: {score:.3f}"
                        )

if __name__ == "__main__":
    unittest.main()
