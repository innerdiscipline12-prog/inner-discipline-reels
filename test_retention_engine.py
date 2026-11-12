import json
import tempfile
import unittest
from pathlib import Path

import retention_engine as re


class RetentionEngineTests(unittest.TestCase):
    def test_generic_openings_are_rejected(self):
        self.assertTrue(re.is_swipe_risk_hook("Discipline is important."))
        self.assertTrue(re.is_swipe_risk_hook("You need to stay consistent."))
        self.assertFalse(re.is_swipe_risk_hook("YOU KEEP LOWERING THE STANDARD."))

    def test_retention_score_rewards_hook_tension_and_payoff(self):
        strong = [
            "YOU KEEP LOWERING THE STANDARD.",
            "The mood changes.",
            "The excuse sounds reasonable.",
            "Then the result looks familiar.",
        ]
        weak = [
            "Discipline is important.",
            "Keep going.",
            "Never give up.",
        ]
        self.assertGreater(re.retention_candidate_score(strong), re.retention_candidate_score(weak))

    def test_candidate_selection_never_bypasses_novelty_gate(self):
        candidates = [
            ["YOU KEEP LOWERING THE STANDARD.", "The mood changes.", "Then the result looks familiar."],
            ["YOU KEEP EXPLAINING.", "The excuse sounds intelligent.", "The routine still knows."],
        ]
        selected = re.select_retention_candidate(
            candidates,
            recent_scripts=["YOU KEEP LOWERING THE STANDARD. | The mood changes. | Then the result looks familiar."],
            max_candidates=5,
        )
        self.assertNotIn("YOU KEEP LOWERING THE STANDARD.", selected[0][0])

    def test_performance_profile_stays_neutral_with_too_few_samples(self):
        profile = re.build_performance_profile([
            {"category": "mirror", "average_watch_time": 12.0},
            {"category": "consequence", "average_watch_time": 13.0},
        ])
        self.assertEqual(profile["samples"], 2)
        self.assertEqual(profile["category_boosts"], {})


if __name__ == "__main__":
    unittest.main()
