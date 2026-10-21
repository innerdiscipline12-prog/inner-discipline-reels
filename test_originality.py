import unittest
from originality import select_novel_candidate

class OriginalityTests(unittest.TestCase):
    def test_avoids_recent_exact_script(self):
        repeated = "You delay the work until tomorrow | Waiting makes the cost grow"
        fresh = "Your phone steals your attention | Protect the first hour of your day"
        chosen, _, _, fallback = select_novel_candidate([repeated, fresh], recent_scripts=[repeated.lower()], recent_concepts=[])
        self.assertEqual(chosen, fresh)
        self.assertFalse(fallback)

    def test_avoids_recent_concept_when_alternative_exists(self):
        delayed = "Tomorrow keeps moving | Delay makes the cost heavier"
        attention = "Your phone steals your attention | Protect the first hour of your day"
        chosen, topic, _, fallback = select_novel_candidate([delayed, attention], recent_scripts=[], recent_concepts=["procrastination"])
        self.assertEqual(chosen, attention)
        self.assertEqual(topic, "attention")
        self.assertFalse(fallback)

    def test_empty_candidates_fail_loudly(self):
        with self.assertRaises(ValueError):
            select_novel_candidate([])

if __name__ == "__main__":
    unittest.main()
