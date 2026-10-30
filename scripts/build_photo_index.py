#!/usr/bin/env python3
"""Index AI food images by exact recipe ID (fully offline, zero API calls)."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RECIPES=ROOT/'recipes/library.json'
PHOTO_DIR=ROOT/'assets/photos'
INDEX=ROOT/'assets/photo-index.json'
EXTENSIONS=('.webp','.jpg','.jpeg','.png')

def build():
    recipes=json.loads(RECIPES.read_text(encoding='utf-8'))['recipes']
    idx={}
    for r in recipes:
        rid=r['id']
        files=[PHOTO_DIR/(rid+ext) for ext in EXTENSIONS]
        existing=next((x for x in files if x.is_file() and x.stat().st_size>100),None)
        if existing is not None:
            idx[rid]={'image':f'assets/photos/{existing.name}', 'title':r['title'], 'kind':'ai_generated'}
    INDEX.write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'AI fotografie: {len(idx)}/{len(recipes)}')
    return len(idx)

if __name__=='__main__': build()
