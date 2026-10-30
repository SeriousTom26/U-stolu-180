#!/usr/bin/env python3
"""Offline check of one-photo-per-recipe state; no API call."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
recipes=json.loads((ROOT/'recipes/library.json').read_text(encoding='utf-8'))['recipes']
photos=json.loads((ROOT/'assets/photo-index.json').read_text(encoding='utf-8'))
ready=sum(r['id'] in photos and (ROOT/photos[r['id']]['image']).is_file() for r in recipes)
print(f'Vytvořené a uložené AI obrázky: {ready} / {len(recipes)}')
print(f'Chybí: {len(recipes)-ready}')
