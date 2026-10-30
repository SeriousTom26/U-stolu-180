# NOVÝ REPOZITÁŘ – U stolu 180 AI

**Toto je čistý nový projekt, není určený k přepsání žádného starého repozitáře.**

## 1. Založení nového repozitáře přes GitHub Desktop

1. Ve `File > New repository` zadej název **`u-stolu-180-ai`**.
2. Po založení použij `Repository > Show in Finder`.
3. Zkopíruj **celý obsah** rozbaleného projektu do složky repozitáře, včetně skryté `.github`. Finder: `⌘ + Shift + .`.
4. Ujisti se, že `index.html` leží v kořeni repozitáře, nikoliv ve vnořené složce.
5. V GitHub Desktop potvrď `Commit to main`, potom `Publish repository`. Pro GitHub Free doporučujeme veřejný repozitář.
6. Na webu repozitáře nastav `Settings > Pages > Build and deployment > Source: GitHub Actions`.
7. V `Actions` spusť `U stolu · automatický jídelníček` s `generate_next_week=false`. Publikuje se ukázkový týden.
8. Povol `Settings > Actions > General > Workflow permissions > Read and write permissions`, pokud se bude ukládání nového týdne vracet s chybou 403.

Budoucí adresa (až po úspěšném nasazení): `https://serioustom26.github.io/u-stolu-180-ai/`.

## 2. Co už funguje
- 180 receptových variant v databázi (60/60/60), jedna porce receptu pro dvě osoby.
- Automatický výběr a záznam každé soboty v 9:17 Europe/Prague.
- Historie týdnů, přehled, detail, nákupní seznam.
- Referenční ceník Rohlík.cz k 30. 10. 2026 (není živý), cenu spotřebovaných surovin i balení.

## 3. Co se ještě musí doplnit
**180 fotorealistických AI obrázků v ChatGPT**: nejsou zatím v balíčku a budou přibývat do `assets/photos/`.
- Seznam požadavků na všech 180 obrázků: `recipes/foto-fronta-180.csv`.
- U každého vytvořeného obrázku ulož název přesně podle ID receptu, například `b-pohankove-palacinky-1.png`.
- **Nejjednodušší varianta bez Terminálu:** v GitHub Desktop otevři `Repository > Show in Finder`, do `assets/photos/` zkopíruj obrázky s těmito názvy (mohou být `.png`, `.jpg`, `.jpeg`, `.webp`) a klikni `Commit + Push`. GitHub při publikování **sám vytvoří index obrázků**.
- **Volitelná komprese do WebP na Macu:** `python3 -m pip install Pillow` a `python3 scripts/import_ai_photos.py --from-dir /cesta/k/fotkam`.
- Fotografie se přiřazují podle přesného ID. Pokud bude chybět soubor, zobrazí se dočasně původní ilustrace.

**Placené předplatné ChatGPT nelze použít jako API automaticky spouštěné z GitHub Actions.** Fotorealistické obrázky se předgenerují v ChatGPT po dávkách a poté se jednou nahrají.

## 4. Bezpečnost
- Nezadávej žádný API klíč. Tento projekt OpenAI API nepoužívá.
- Web GitHub Pages je veřejný, pokud jde o veřejný repozitář. Neukládej žádné soukromé údaje.
- Ceny Rohlíku jsou orientační; pokud cena není potvrzena, součet je označen jako neúplný.
