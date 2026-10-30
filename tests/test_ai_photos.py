import json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class PhotosTests(unittest.TestCase):
 def test_photo_queue_matches_library(self):
  recs=json.loads((ROOT/'recipes/library.json').read_text(encoding='utf-8'))['recipes']
  queue=json.loads((ROOT/'recipes/foto-fronta-180.json').read_text(encoding='utf-8'))
  self.assertEqual({r['id'] for r in recs},{q['id'] for q in queue})
  self.assertEqual(len(queue),180)
  self.assertTrue(all(q['file']==q['id']+'.png' for q in queue))
 def test_photo_index_consistency(self):
  recs=json.loads((ROOT/'recipes/library.json').read_text(encoding='utf-8'))['recipes']
  index=json.loads((ROOT/'assets/photo-index.json').read_text(encoding='utf-8'))
  self.assertTrue(set(index).issubset({r['id'] for r in recs}))
  for rid, entry in index.items():
   self.assertEqual(entry['image'],f'assets/photos/{rid}.webp')
   self.assertTrue((ROOT/entry['image']).is_file())
if __name__=='__main__': unittest.main()
