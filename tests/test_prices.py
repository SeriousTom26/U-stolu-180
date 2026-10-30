"""Price-catalog tests; no paid API required."""
import json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class PricingTests(unittest.TestCase):
 def setUp(self):
  self.catalog=json.loads((ROOT/'prices/rohlik.json').read_text(encoding='utf-8'))
  self.recipes=json.loads((ROOT/'recipes/library.json').read_text(encoding='utf-8'))['recipes']
  self.week=json.loads((ROOT/'plans/2026-11-02.json').read_text(encoding='utf-8'))
 def test_all_recipe_ingredients_mapped(self):
  names={i['name'] for r in self.recipes for i in r['ingredients']}
  self.assertEqual(names,set(self.catalog['items']))
 def test_prices_are_positive_or_explicitly_unavailable(self):
  for name,item in self.catalog['items'].items():
   if item['package_price'] is not None:
    self.assertGreater(item['package_price'],0,name)
    self.assertGreater(item['package_amount'],0,name)
    self.assertTrue(item['url'].startswith('https://www.rohlik.cz/'),name)
   else:
    self.assertIsNone(item['url'])
 def test_meal_ingredients_match_weekly_basket(self):
  quantities={}
  for day in self.week['days']:
   for meal in day['meals']:
    for i in meal['ingredients']:
     key=(i['name'],i['unit'])
     quantities[key]=quantities.get(key,0)+i['amount']
  basket={(i['name'],i['unit']):i['amount'] for i in self.week['shopping']}
  self.assertEqual(quantities,basket)
 def test_realistic_weekly_cart_is_higher_than_used_ingredients(self):
  used=0;cart=0
  for i in self.week['shopping']:
   item=self.catalog['items'][i['name']]
   if item['package_price'] is None:continue
   import math
   used+=i['amount']/item['package_amount']*item['package_price']
   cart+=math.ceil(i['amount']/item['package_amount'])*item['package_price']
  self.assertGreaterEqual(cart,used)
  self.assertGreater(used,100)
  print(f'SAMPLE week: {used:.0f} CZK consumed, {cart:.0f} CZK full packages')
if __name__=='__main__':unittest.main()
