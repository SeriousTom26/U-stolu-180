# U stolu – 180 receptů + 180 AI fotografií (připravovaná knihovna)

Nová samostatná aplikace pro **GitHub Pages**, bez OpenAI API a bez API kreditu.

## Funkce aplikace

- 180 receptových variant, 60 snídaní, 60 obědů, 60 večeří, vždy pro 2 osoby.
- Nízkohistaminový výběr respektující běžné uživatelské preference: bez snídaňových kaší a rýžových chlebíčků, pouze dvě masová hlavní jídla týdně, čerstvé suroviny podle tolerance.
- Interaktivní sedmidenní dashboard, detail receptu, knihovna všech 180 receptů, vyhledávání, historie.
- Přesné součty surovin na týden, CSV/TXT export, odškrtávání, orientační ceny z referenčního ceníku Rohlík.cz k 30. 10. 2026. Je zobrazena **poměrná cena spotřebovaného množství** i **nákupní cena celých balení**.
- Sobotní GitHub Actions v 9:17 Europe/Prague vytvoří další týden a uloží jej do historie.
- **Jeden fotorealistický AI obrázek na recept** po postupném doplnění. Knihovna fotografií je nyní prázdná; do té doby aplikace zobrazuje původní SVG ilustrace.

## Nezbytný první postup
Přečti `START_ZDE.md`.

## Jak se doplňuje fotografická knihovna
1. V ChatGPT vygeneruj fotografii odpovídající přesně jednomu receptu podle zadání z `recipes/foto-fronta-180.csv`.
2. Ulož obrázek pod názvem daného receptového ID (např. `b-pohankove-palacinky-1.png`).
3. Zkopíruj obrázky přímo do `assets/photos/` v GitHub repozitáři (PNG/JPG/WEBP).
4. Proveď `Commit + Push`. Při nasazení GitHub automaticky spustí `scripts/build_photo_index.py`, takže **nepotřebuješ Terminál**.
5. Volitelně můžeš zmenšit obrázky převodem na WebP: `python3 scripts/import_ai_photos.py --from-dir /cesta/k/fotkam` (vyžaduje Pillow).

Pro přehled počtu dokončených obrázků spouštěj `python3 scripts/photo_status.py`.

## Jak se chová automat
Bez API vznikají další týdny jako nové kombinace ze 180 připravených receptů. Nezískává se živý ceník Rohlíku a negenerují se další nové recepty ani fotografie. Všechny generované týdny zůstávají uložené v `plans/`.

## Testování
```bash
python3 -m unittest discover -s tests -v
python3 scripts/photo_status.py
python3 scripts/build_site.py
python3 -m http.server 8000 -d _site
```

## Struktura

- `.github/workflows/jidelnicek.yml` – sobotní automat a publikace
- `recipes/library.json` – 180 receptů
- `recipes/foto-fronta-180.csv` – 180 konkrétních obrazových zadání
- `assets/photos/` – sem se uloží WebP obrázky
- `assets/photo-index.json` – přiřazení podle ID receptu
- `assets/img/` – záložní kreslené ilustrace před vytvořením fotografií
- `prices/rohlik.json` – referenční cenový katalog
- `plans/` – trvalá historie týdnů
- `scripts/import_ai_photos.py` – import fotografií

Upozornění: AI obrázky jsou realistické vizualizace, nikoliv důkaz skutečného vzhledu konkrétně připraveného jídla. Recepty nejsou individuální zdravotní doporučení.
