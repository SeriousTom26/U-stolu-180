#!/usr/bin/env python3
"""Add AI-generated PNG/JPG/WEBP per recipe ID, convert and build static index.

Usage:
    python scripts/import_ai_photos.py --from-dir /path/to/photos
File names must exactly match recipe IDs, for example:
    b-pohankove-palacinky-1.png
Requires: pip install pillow  (only for this local import, NOT for GitHub Actions)

No calls to OpenAI or any external service occur.
"""
from __future__ import annotations
import argparse, json, sys
from datetime import date
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'assets/photos'
INDEX=ROOT/'assets/photo-index.json'
LIBRARY=ROOT/'recipes/library.json'
EXTS={'.png','.jpg','.jpeg','.webp'}


def run(source:Path):
    try:
        from PIL import Image, ImageOps
    except ImportError:
        raise SystemExit('Nainstaluj Pillow: python3 -m pip install Pillow')
    if not source.is_dir():
        raise SystemExit(f'Složka neexistuje: {source}')
    recs={r['id']:r for r in json.loads(LIBRARY.read_text(encoding='utf-8'))['recipes']}
    index=json.loads(INDEX.read_text(encoding='utf-8')) if INDEX.exists() else {}
    OUTPUT.mkdir(exist_ok=True,parents=True)
    new=0
    ignored=[]
    for item in sorted(source.iterdir()):
        if not item.is_file() or item.suffix.lower() not in EXTS:
            continue
        if item.stem not in recs:
            ignored.append(item.name)
            continue
        outfile=OUTPUT/(item.stem+'.webp')
        with Image.open(item) as im:
            im=ImageOps.exif_transpose(im).convert('RGB')
            im.thumbnail((1600,1200),Image.Resampling.LANCZOS)
            im.save(outfile,'WEBP',quality=85,method=6)
        index[item.stem]={
            'image':f'assets/photos/{item.stem}.webp',
            'kind':'ai_generated',
            'title':recs[item.stem]['title'],
            'imported_on':date.today().isoformat()
        }
        new+=1
    INDEX.write_text(json.dumps(dict(sorted(index.items())),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'Přidáno nebo aktualizováno: {new}. Celkový počet AI obrázků: {len(index)} / 180.')
    if ignored: print('Přeskočeno (ID není v databázi): '+', '.join(ignored),file=sys.stderr)
    return new

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--from-dir',required=True)
    args=p.parse_args()
    run(Path(args.from_dir).expanduser())
