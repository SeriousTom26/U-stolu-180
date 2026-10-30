#!/usr/bin/env python3
"""Copy the completely static project into _site for GitHub Pages."""
from pathlib import Path
import shutil
from build_photo_index import build as build_photo_index
ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'_site'
build_photo_index()
if SITE.exists():shutil.rmtree(SITE)
SITE.mkdir(parents=True)
shutil.copy2(ROOT/'index.html',SITE/'index.html')
for sub in ('assets','plans','recipes','prices'):
    shutil.copytree(ROOT/sub,SITE/sub)
(SITE/'.nojekyll').write_text('',encoding='utf-8')
print('Site created at',SITE)
