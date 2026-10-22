import unittest
from originality import assert_novel, select_novel_candidate, similarity

class OriginalityTests(unittest.TestCase):
    def test_avoids_recent_exact_script(self):
        repeated = "You delay the work until tomorrow | Waiting makes the cost grow"
        fresh = "Your phone steals your attention | Protect the first hour of your day"
        chosen, _, _, fallback = select_novel_candidate(
            [repeated, fresh], recent_scripts=[repeated.lower()], recent_concepts=[]
        )
        self.assertEqual(chosen, fresh)
        self.assertFalse(fallback)

    def test_rejects_near_duplicate_script(self):
        old = "You keep delaying the hard work until tomorrow."
        near = "You keep delaying the difficult work until tomorrow."
        self.assertGreaterEqual(similarity(old, near), 0.42)
        with self.assertRaises(ValueError):
            select_novel_candidate([near], recent_scripts=[old], max_similarity_threshold=0.42)

    def test_rejects_near_duplicate_caption(self):
        old = "Comfort feels harmless until it becomes the standard."
        near = "Comfort seems harmless until it becomes your standard."
        with self.assertRaises(ValueError):
            assert_novel(near, [old], label="caption", threshold=0.42)

    def test_rejects_near_duplicate_cover(self):
        old = "YOU KEEP MOVING IT"
        near = "YOU KEEP MOVING THIS"
        with self.assertRaises(ValueError):
            assert_novel(near, [old], label="cover", threshold=0.35)

    def test_does_not_fallback_when_pool_is_exhausted(self):
        old = "Your phone steals your attention every morning."
        with self.assertRaises(ValueError):
            select_novel_candidate(
                [old, "Your phone steals your attention each morning."],
                recent_scripts=[old],
                max_similarity_threshold=0.42,
            )

    def test_five_consecutive_selections_are_distinct(self):
        pool = [
            "Stop renting your attention to every notification.",
            "Your private routine is training your future standards.",
            "The people around you can normalize your worst habits.",
            "A broken promise to yourself changes how you trust yourself.",
            "You do not need a new plan; you need proof of execution.",
            "The first hour of your day reveals who controls your focus.",
            "Avoidance protects your comfort and quietly taxes your future.",
        ]
        recent = []
        selected = []
        for _ in range(5):
            item, _, score, fallback = select_novel_candidate(
                pool, recent_scripts=recent, max_similarity_threshold=0.42
            )
            self.assertFalse(fallback)
            self.assertLess(score, 0.42)
            selected.append(item)
            recent.insert(0, item)
        self.assertEqual(len(set(selected)), 5)

if __name__ == "__main__":
    unittest.main()
