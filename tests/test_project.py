"""Unit tests that run entirely offline and validate the meal-library contract."""
from __future__ import annotations
import collections,datetime as dt,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from generate_week import make_week, read_json

class MealAppTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.library=read_json(ROOT/'recipes/library.json')['recipes']
  cls.plan=read_json(ROOT/'plans/2026-11-02.json')
 def test_180_recipes(self):
  self.assertEqual(len(self.library),180)
  self.assertEqual(len({x['id'] for x in self.library}),180)
  self.assertEqual(len({x['title'] for x in self.library}),180)
  self.assertEqual(collections.Counter(x['category'] for x in self.library),{'breakfast':60,'lunch':60,'dinner':60})
  for cat in ('breakfast','lunch','dinner'):
   self.assertEqual(len({x['family'] for x in self.library if x['category']==cat}),20)
 def test_recipe_contract(self):
  for r in self.library:
   self.assertEqual(r['servings'],2)
   self.assertGreaterEqual(len(r['ingredients']),2)
   self.assertGreaterEqual(len(r['steps']),3)
   self.assertTrue((ROOT/r['image']).is_file(),r['image'])
   self.assertTrue(all(i['amount']>0 for i in r['ingredients']))
   self.assertTrue(all(i['unit'] in ('g','ml','ks') for i in r['ingredients']))
 def test_preferences(self):
  bans={'rajče','špenát','lilek','kysané zelí','rybí omáčka','salám','tuňák','parmazán','čokoláda','kefír','jogurt','rýžové chlebíčky'}
  for r in self.library:
   ingr={i['name'] for i in r['ingredients']}
   self.assertFalse(ingr.intersection(bans),r['title'])
   if r['category']=='breakfast':
    self.assertNotIn('kaše',r['title'].lower())
 def test_first_week(self):
  p=self.plan
  self.assertEqual(len(p['days']),7)
  self.assertEqual(p['recipe_count'],21)
  self.assertEqual(p['meat_count'],2)
  meals=[m for d in p['days'] for m in d['meals']]
  self.assertEqual(len(meals),21)
  self.assertEqual(len({m['id'] for m in meals}),21)
  self.assertEqual({m['category'] for m in p['days'][0]['meals']},{'breakfast','lunch','dinner'})
  self.assertTrue(all(len(d['meals'])==3 for d in p['days']))
 def test_shopping_sums(self):
  expected=collections.Counter()
  for d in self.plan['days']:
   for r in d['meals']:
    for i in r['ingredients']:
     expected[(i['name'],i['unit'])]+=i['amount']
  got={(i['name'],i['unit']):i['amount'] for i in self.plan['shopping']}
  self.assertEqual(expected,got)
 def test_history_rotation(self):
  hist=[];all_weeks=[]
  for i in range(10):
   w=make_week(dt.date(2026,11,2)+dt.timedelta(weeks=i),self.library,hist)
   meals=[r for d in w['days'] for r in d['meals']]
   self.assertEqual(len({r['id'] for r in meals}),21)
   self.assertEqual(w['meat_count'],2)
   for cat in ('breakfast','lunch','dinner'):
    self.assertEqual(len({r['family'] for r in meals if r['category']==cat}),7)
   if all_weeks:
    prev={r['id'] for d in all_weeks[-1]['days'] for r in d['meals']}
    self.assertTrue(prev.isdisjoint({r['id'] for r in meals}),f'repeat week {i}')
   all_weeks.append(w);hist=[w]+hist
 def test_workflow(self):
  yml=(ROOT/'.github/workflows/jidelnicek.yml').read_text(encoding='utf-8')
  self.assertIn('Europe/Prague',yml)
  self.assertIn('17 9 * * 6',yml)
  self.assertIn('actions/deploy-pages@v4',yml)
  self.assertNotIn('OPENAI_API_KEY',yml)
  self.assertNotIn('smtp',yml.lower())

if __name__=='__main__':unittest.main()
