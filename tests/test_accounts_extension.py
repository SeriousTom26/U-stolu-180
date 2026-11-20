"""Offline smoke checks for optional account-backed recipe expansion."""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
from unittest import TestCase, mock
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('generate_week',ROOT/'scripts/generate_week.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class AccountExtensionTests(TestCase):
    def test_account_js_has_no_privileged_key(self):
        js=(ROOT/'assets/accounts.js').read_text(encoding='utf-8')
        config=(ROOT/'assets/backend-config.js').read_text(encoding='utf-8')
        self.assertNotIn('sb_secret_',js)
        self.assertNotIn('sb_secret_',config)
        self.assertIn('persistSession: true',js)
        self.assertIn('toggleFavorite',js)
        self.assertIn(".from('admin_users')",js)
    def test_admin_changes_are_row_level_protected(self):
        sql=(ROOT/'supabase/setup.sql').read_text(encoding='utf-8')
        for tbl in ('admin_users','favorites','recipes'):
            self.assertIn(f'alter table public.{tbl} enable row level security',sql)
        self.assertIn('User adds own favorites',sql)
        self.assertIn('Admin updates recipes',sql)
        self.assertIn("bucket_id = 'recipe-images'",sql)
        self.assertIn('revoke all on public.admin_users from anon, authenticated',sql)
        self.assertNotIn('grant insert on public.admin_users to authenticated',sql)
    def test_online_recipe_override_retains_unspecified_fields(self):
        original=json.loads((ROOT/'recipes/library.json').read_text(encoding='utf-8'))['recipes']
        first=original[0]
        changed=dict(first,title='Nové palačinky')
        response=[{'id':first['id'],'body':changed,'image_url':'https://example.com/pancake.png'},
                  {'id':'vlastni-recept-181','body':dict(first,id='vlastni-recept-181',title='Nový recept',family='vlastni-recept-181'),'image_url':None}]
        class FakeResponse:
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def read(self):return json.dumps(response).encode('utf-8')
        with mock.patch.dict(os.environ,{
            'USTOLU_SUPABASE_URL':'https://example.supabase.co',
            'USTOLU_SUPABASE_PUBLISHABLE_KEY':'sb_publishable_test'
        }),mock.patch.object(mod.urllib.request,'urlopen',return_value=FakeResponse()):
            library=mod.load_online_recipes(original)
        self.assertEqual(len(library),len(original)+1)
        changed_result=next(r for r in library if r['id']==first['id'])
        self.assertEqual(changed_result['title'],'Nové palačinky')
        self.assertEqual(changed_result['remote_image'],'https://example.com/pancake.png')
    def test_offline_fallback(self):
        with mock.patch.dict(os.environ,{'USTOLU_SUPABASE_URL':'','USTOLU_SUPABASE_PUBLISHABLE_KEY':''}):
            rows=[{'id':'example'}]
            self.assertIs(mod.load_online_recipes(rows),rows)
