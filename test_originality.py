import ast
import random
import unittest
from pathlib import Path
from originality import assert_novel, retention_hook_score, select_novel_candidate, similarity

def _assignment_value(node, name):
    for item in ast.walk(node):
        if isinstance(item, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == name for t in item.targets):
                return ast.literal_eval(item.value)
    raise AssertionError(f"Could not find literal assignment for {name}")

def _real_candidate_banks():
    source = Path(__file__).with_name("generate.py").read_text(encoding="utf-8")
    tree = ast.parse(source, filename="generate.py")
    viral_bank = _assignment_value(tree, "VIRAL_RETENTION_BANK")
    caption_fn = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "build_caption"
    )
    caption_bank = _assignment_value(caption_fn, "bank")
    return viral_bank, caption_bank

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

    def test_hook_ranker_prefers_direct_tension_over_vague_openers(self):
        direct = retention_hook_score("YOU KNOW WHAT THIS IS.")
        consequence = retention_hook_score("DELAY GETS EXPENSIVE.")
        vague = retention_hook_score("THE QUIET TRUTH.")
        self.assertGreater(direct, vague)
        self.assertGreater(consequence, vague)

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
        random.seed(2026)
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

    def test_five_consecutive_reels_use_distinct_real_bank_assets(self):
        viral_bank, caption_bank = _real_candidate_banks()
        script_pool = [
            " | ".join(lines)
            for category in viral_bank.values()
            for lines in category["scripts"]
        ]
        cover_pool = [
            cover
            for category in viral_bank.values()
            for cover in category["covers"]
        ]
        caption_pool = [
            caption
            for captions in caption_bank.values()
            for caption in captions
        ]
        self.assertGreaterEqual(len(script_pool), 30)
        self.assertGreaterEqual(len(cover_pool), 30)
        self.assertGreaterEqual(len(caption_pool), 30)

        random.seed(20261022)
        recent_scripts, recent_covers, recent_captions = [], [], []
        picked_scripts, picked_covers, picked_captions = [], [], []
        for _ in range(5):
            script, _, script_score, _ = select_novel_candidate(
                script_pool, recent_scripts=recent_scripts,
                max_similarity_threshold=0.42
            )
            cover, _, cover_score, _ = select_novel_candidate(
                cover_pool, recent_scripts=recent_covers,
                max_similarity_threshold=0.35
            )
            caption, _, caption_score, _ = select_novel_candidate(
                caption_pool, recent_scripts=recent_captions,
                max_similarity_threshold=0.42
            )
            self.assertLess(script_score, 0.42)
            self.assertLess(cover_score, 0.35)
            self.assertLess(caption_score, 0.42)
            picked_scripts.append(script)
            picked_covers.append(cover)
            picked_captions.append(caption)
            recent_scripts.insert(0, script)
            recent_covers.insert(0, cover)
            recent_captions.insert(0, caption)

        self.assertEqual(len(set(picked_scripts)), 5)
        self.assertEqual(len(set(picked_covers)), 5)
        self.assertEqual(len(set(picked_captions)), 5)


    def test_all_thumbnail_hooks_are_two_or_three_words(self):
        viral_bank, _ = _real_candidate_banks()
        covers = [
            cover
            for category in viral_bank.values()
            for cover in category["covers"]
        ]
        self.assertGreaterEqual(len(covers), 60)
        for cover in covers:
            with self.subTest(cover=cover):
                words = cover.split()
                self.assertGreaterEqual(len(words), 2)
                self.assertLessEqual(len(words), 3)
        self.assertEqual(len(covers), len(set(covers)), "Thumbnail hooks must be unique across banks")


if __name__ == "__main__":
    unittest.main()
