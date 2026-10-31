"""Import a batch of 10 generated food photographs into U-stolu-180.

Designed for GitHub Actions, which has Internet access to the signed photo URLs.
The chat environment may display a photo but not be able to download its bytes.
Keep image files unchanged until all downloads pass validation.
Future batches only require replacing scripts/ai_photo_import.tsv.
"""
from __future__ import annotations

import csv
from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import tempfile
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import zipfile

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "ai_photo_import.tsv"
DEST = ROOT / "assets" / "photos"
BATCH_SIZE = 10
MAX_FILE_BYTES = 20 * 1024 * 1024
ALLOWED_IMAGE_HOSTS = {"dnznrvs05pmza.cloudfront.net"}


def recipe_db() -> tuple[list[str], dict]:
    queue = json.loads((ROOT / "recipes/foto-fronta-180.json").read_text(encoding="utf-8"))
    recipes = json.loads((ROOT / "recipes/library.json").read_text(encoding="utf-8"))["recipes"]
    ids = [q["id"] for q in queue]
    return ids, {r["id"]: r for r in recipes}


def source_list() -> tuple[list[tuple[str, str]], int, int, dict]:
    with SOURCE.open(encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    if len(rows) != BATCH_SIZE or any(len(row) != 2 for row in rows):
        raise ValueError(f"Soubor musí mít právě {BATCH_SIZE} řádků ve tvaru ID<TAB>URL")
    queue, library = recipe_db()
    ids = [r[0] for r in rows]
    if any(i not in library for i in ids) or len(set(ids)) != BATCH_SIZE:
        raise ValueError("Neznámé nebo duplicitní ID receptu v seznamu")
    start = queue.index(ids[0])
    if ids != queue[start : start + BATCH_SIZE]:
        raise ValueError("ID musí odpovídat 10 sousedním receptům v původním pořadí")
    for recipe_id, url in rows:
        local_source = f"assets/photos/{recipe_id}.png"
        if url == local_source:
            # Offline-local source bundled into the same git push (no expiring URL).
            continue
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_IMAGE_HOSTS or "_jwt=" not in parsed.query:
            raise ValueError(f"Chybný odkaz nebo cesta pro {recipe_id}")
    return [(r[0], r[1]) for r in rows], start + 1, start + BATCH_SIZE, library


def download_checked(recipe_id: str, url: str, output: Path) -> tuple[int, int]:
    if url == f"assets/photos/{recipe_id}.png":
        # A fully offline import mode: PNG file already present in the upload.
        # Only exact known filenames from assets/photos are allowed.
        source_file = ROOT / url
        with source_file.open("rb") as f:
            image_bytes = f.read(MAX_FILE_BYTES + 1)
    else:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (U-stolu-180-photo-import)"})
        with urlopen(req, timeout=90) as res:
            image_bytes = res.read(MAX_FILE_BYTES + 1)
    if not 2000 <= len(image_bytes) <= MAX_FILE_BYTES:
        raise ValueError(f"{recipe_id}: neplatná velikost obrázku")
    with Image.open(BytesIO(image_bytes)) as check:
        check.verify()
    with Image.open(BytesIO(image_bytes)) as opened:
        img = ImageOps.exif_transpose(opened).convert("RGB")
        if min(img.size) < 700:
            raise ValueError(f"{recipe_id}: obrázek je moc malý, rozlišení {img.size}")
        resolution = img.size
        img.save(output, format="PNG", optimize=True)
    with Image.open(output) as final:
        final.verify()
    return resolution


def emit_output(name: str, value: str) -> None:
    print(f"{name}: {value}")
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{name}={value}\n")


def main() -> None:
    entries, start, end, library = source_list()
    batch = f"{start:02d}_{end:02d}"
    archive_name = f"U_STOLU_FOTKY_{batch}_GITHUB_READY.zip"
    archive_path = ROOT / archive_name

    with tempfile.TemporaryDirectory(prefix="u_stolu_photo_import_") as folder:
        temp = Path(folder)
        for pos, (recipe_id, url) in enumerate(entries, start):
            print(f"[{pos}/{end}] Stahuji foto: {recipe_id}", flush=True)
            try:
                size = download_checked(recipe_id, url, temp / f"{recipe_id}.png")
            except Exception as exc:
                raise RuntimeError(
                    f"Fotografie {recipe_id} se nepodařila stáhnout a ověřit: {exc}. "
                    "Žádný již zveřejněný obrázek nebyl změněn. "
                    "Zkontroluj, zda není podepsaný odkaz expirovaný."
                ) from exc
            print(f"  OK {size[0]}x{size[1]}", flush=True)

        DEST.mkdir(parents=True, exist_ok=True)
        for recipe_id, _ in entries:
            shutil.copy2(temp / f"{recipe_id}.png", DEST / f"{recipe_id}.png")

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=5) as z:
        for recipe_id, _ in entries:
            image = DEST / f"{recipe_id}.png"
            z.write(image, arcname=f"assets/photos/{image.name}")
        mapfile = BytesIO()
        import io
        file_str = io.StringIO(newline="")
        writer = csv.writer(file_str)
        writer.writerow(["poradi", "id", "soubor", "recept"])
        for pos, (recipe_id, _) in enumerate(entries, start):
            writer.writerow([pos, recipe_id, f"{recipe_id}.png", library[recipe_id]["title"]])
        z.writestr("MAPOVANI_RECEPTU.csv", "\ufeff" + file_str.getvalue())

    with zipfile.ZipFile(archive_path) as z:
        names = z.namelist()
        if z.testzip() or len([n for n in names if n.startswith("assets/photos/") and n.endswith(".png")]) != 10:
            raise ValueError("Výsledný ZIP neprošel testem integrity nebo počtu PNG")
    emit_output("archive_name", archive_name)
    emit_output("batch_label", f"{start}-{end}")
    print("Hotovo: všech 10 fotografií podle stabilních ID, ZIP ověřen.")


if __name__ == "__main__":
    main()
