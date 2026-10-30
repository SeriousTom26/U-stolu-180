"""Check photo-to-recipe mapping for images in PNG, WebP, or JPEG formats."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_EXTENSIONS = {'.png', '.webp', '.jpg', '.jpeg'}

class PhotosTests(unittest.TestCase):
    def test_photo_queue_matches_library(self):
        recipes = json.loads((ROOT / 'recipes/library.json').read_text(encoding='utf-8'))['recipes']
        queue = json.loads((ROOT / 'recipes/foto-fronta-180.json').read_text(encoding='utf-8'))
        self.assertEqual({r['id'] for r in recipes}, {q['id'] for q in queue})
        self.assertEqual(len(queue), 180)
        self.assertTrue(all(q['file'] == q['id'] + '.png' for q in queue))

    def test_photo_index_consistency(self):
        recipes = json.loads((ROOT / 'recipes/library.json').read_text(encoding='utf-8'))['recipes']
        valid_ids = {r['id'] for r in recipes}
        index = json.loads((ROOT / 'assets/photo-index.json').read_text(encoding='utf-8'))
        self.assertTrue(set(index).issubset(valid_ids))
        for rid, entry in index.items():
            image_path = Path(entry['image'])
            self.assertEqual(image_path.parent.as_posix(), 'assets/photos')
            self.assertEqual(image_path.stem, rid)
            self.assertIn(image_path.suffix.lower(), ALLOWED_EXTENSIONS)
            self.assertTrue((ROOT / image_path).is_file())
            self.assertGreater((ROOT / image_path).stat().st_size, 100)

if __name__ == '__main__':
    unittest.main()
