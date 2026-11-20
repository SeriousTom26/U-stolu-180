# U stolu – uživatelské účty, oblíbené recepty a zabezpečená administrace

## Co nová aktualizace přidává

- Každý návštěvník si může vytvořit vlastní účet pomocí e-mailu a hesla, potvrdit e-mail, přihlásit se a obnovit heslo.
- Přihlášený návštěvník si ukládá oblíbené recepty kliknutím na ♡. Jeho seznam se synchronizuje mezi zařízeními.
- **Pouze tebou výslovně určený administrátor** uvidí sekci „Správa receptů“ a může přidávat recepty, upravovat suroviny, názvy, postupy nebo fotografie.
- Aplikace dál běží na GitHub Pages. Uživatelské účty, oblíbené a úpravy receptů ukládá Supabase.
- Původních 180 receptů a všechny fotografie v `assets/photos/` zůstanou beze změny.
- V aplikaci uvidíš úpravy okamžitě po uložení. Týdenní automat využije nové recepty, pokud nastavíš také GitHub Actions variables (viz bod 6).

**Pozor:** Samotné nakopírování souborů nestačí k zapnutí přihlášení. Kvůli bezpečnosti je nutné nejdřív vytvořit vlastní Supabase projekt a nastavit ho podle těchto kroků. Bez konfigurace běží původní aplikace dál; registrace je vypnutá.

## 1. Nahraj aktualizaci na GitHub

1. Rozbal `U_STOLU_UCTY_OBLIBENE_ADMIN_AKTUALIZACE.zip`.
2. V GitHub Desktop otevři repozitář **u-stolu-180-ai** → `Repository → Show in Explorer` (nebo Finder na Macu).
3. **Zkopíruj obsah ZIPu do hlavní složky repozitáře** (tam, kde je `index.html`). Potvrď nahrazení pouze souborů, které ZIP skutečně obsahuje.
4. **Nemaž** své složky `assets/photos/`, `plans/` ani `recipes/library.json`.
5. Proveď `Commit to main` → `Push origin`. Původní aplikace zatím stále funguje.

## 2. Založ databázi Supabase

1. Na [supabase.com](https://supabase.com/) vytvoř svůj vlastní projekt (doporučeno vybrat region EU).
2. V panelu projektu otevři **SQL Editor → New query**.
3. Otevři soubor `supabase/setup.sql` z tohoto ZIPu a vlož jeho celý obsah do SQL Editoru.
4. Klikni na **Run**. Tím vytvoříš tabulky `recipes`, `favorites`, `admin_users`, úložiště fotek a bezpečnostní pravidla **Row Level Security (RLS)**.
5. V **Authentication → Providers → Email** ponech zapnuté potvrzování e-mailové adresy (Confirm email). Zkontroluj, že jsou povolené e-mailové registrace.
6. V **Authentication → URL Configuration** nastav:
   - **Site URL:** `https://serioustom26.github.io/u-stolu-180-ai/` (pokud tvá aplikace používá právě tuto adresu, jinak vlož svou aktuální URL).
   - **Redirect URLs:** stejnou URL včetně koncového `/`.
   Potvrzovací a obnovovací e-maily se pak budou vracet do tvé aplikace.

## 3. Propoj aplikaci s databází

1. V Supabase otevři **Connect** nebo **Project Settings → API Keys**.
2. Zkopíruj **Project URL** (např. `https://abcdef.supabase.co`) a **publishable key** (začíná `sb_publishable_`).
3. Otevři v GitHub repozitáři soubor `assets/backend-config.js` a vyplň **jen tyto dvě hodnoty**:

   ```js
   window.USTOLU_BACKEND = {
     supabaseUrl: "https://abcdef.supabase.co",
     supabasePublishableKey: "sb_publishable_SEM_VLOZ_SVUJ_VEREJNY_KLIC"
   };
   ```

4. `Commit + Push`. Pak otevři aplikaci a zvol **Přihlásit se / Registrace**.

**Bezpečnost:** URL a *publishable key* jsou veřejné údaje určené pro browser a mohou být v repozitáři; přístup k datům chrání RLS. **Nikdy sem ani do GitHubu nedávej `service_role`, `sb_secret_…`, heslo do Supabase ani privátní JWT.**

## 4. Vytvoř svůj účet a nastav si admin roli

1. Ve webové aplikaci U stolu klikni **Přihlásit se / Registrace → Registrace**.
2. Vyplň svůj e-mail a bezpečné heslo, potvrď registraci z e-mailu a následně se přihlas.
3. Vrať se do Supabase → **SQL Editor** a spusť tento příkaz (do uvozovek dosaď e-mail **svého ověřeného účtu**):

   ```sql
   insert into public.admin_users (user_id)
   select id from auth.users
   where email = 'TVUJ-EMAIL@DOMENA.CZ'
     and email_confirmed_at is not null
   on conflict (user_id) do nothing;
   ```

4. Ověř, že příkaz vložil jeden řádek. Odhlas se a znovu přihlas, případně obnov stránku.
5. V levém menu se **pouze adminovi** objeví „Správa receptů“.

**Běžní uživatelé se jako admin nemohou sami označit.** Tabulka `admin_users` je chráněná a administrátora jmenuješ pouze ty přes SQL Editor projektu. Nestačí si v prohlížeči změnit obsah stránky nebo uživatelská metadata.

## 5. Co kdo může dělat

| Funkce | Bez přihlášení | Běžný účet | Admin |
|---|---:|---:|---:|
| Prohlížet všechny recepty | Ano | Ano | Ano |
| Ukládat oblíbené recepty | Ne | Ano – vlastní | Ano – vlastní |
| Upravit názvy, postupy a suroviny | Ne | Ne | Ano |
| Přidat nový recept | Ne | Ne | Ano |
| Nahrát či vyměnit fotografii | Ne | Ne | Ano |

**Úpravy se neprovádějí v GitHub repozitáři:** administrace ukládá nová/změněná data do `public.recipes` v Supabase. Původní recepty v `recipes/library.json` fungují jako výchozí záloha. Fotografie se ukládají do veřejného úložiště Supabase; nahrávat do něj smí jen admin.

## 6. Aby nové recepty používal i sobotní automat

Základní web zobrazuje nové recepty ihned. Pro automatické generování **budoucích** týdenních jídelníčků je navíc potřeba nastavit dvě veřejné proměnné v repozitáři GitHub:

1. Otevři **Settings → Secrets and variables → Actions → Variables**.
2. Přidej:
   - `USTOLU_SUPABASE_URL`: URL tvého projektu `https://abcdef.supabase.co`
   - `USTOLU_SUPABASE_PUBLISHABLE_KEY`: stejný publishable key jako v `assets/backend-config.js`
3. Tím si plánovač před každým novým týdnem načte veřejnou knihovnu včetně nových receptů od administrátora.

Když tyto dvě proměnné nenastavíš, sobotní plánovač bude dál používat jen původní soubor se 180 recepty, i když návštěvníci v knihovně nové recepty uvidí. Jestli je nastavíš, ale Supabase nebude dostupné, generování se bezpečně zastaví místo toho, aby bez upozornění vytvořilo jídelníček ze zastaralých údajů.

**Existující jídelníčky se zpětně nepřepisují.** Nákupní seznam uloženého starého týdne vychází z údajů platných při vygenerování plánu; proto se po editaci receptu nemusí shodovat s aktuálně zobrazeným postupem. Nové týdny už použijí upravené suroviny.

## 7. Doporučení pro veřejný provoz

- Zapni **email verification** a omezení přihlášení/registrací (rate limits). Pro větší množství uživatelů zvaž vlastní SMTP pro transakční e-maily; výchozí limit je nízký.
- Používej silné heslo k administrátorskému účtu a zapni MFA alespoň pro svůj účet v Supabase/GitHub, kde to služba umožňuje.
- Pokud chceš administrátorovi odebrat přístup, v Supabase spusť: `delete from public.admin_users where user_id = 'JEHO-UUID';` (pouze v SQL Editoru).
- V Supabase můžeš spravovat uživatelské účty v Authentication → Users; aplikace ukládá oblíbené do samostatné tabulky RLS.
- Upozorni uživatele v zásadách ochrany osobních údajů, že účet používá e-mail a že jejich oblíbené recepty jsou ukládány do služby Supabase.

## Řešení problémů

- **„Registrace není dostupná“:** není vyplněný `assets/backend-config.js`, nebo selhalo načtení knihovny Supabase z CDN.
- **Po registraci se nepřihlásím:** zkontroluj potvrzení e-mailu a nastavení Auth Redirect URL.
- **Admin menu se nezobrazuje:** ověř, že SQL příkaz vložil správného ověřeného uživatele; pak se znovu přihlas.
- **Nemohu nahrát fotografii:** soubor musí být PNG/JPG/WebP do 6 MB; ověř SQL pravidla pro `recipe-images`.
- **Nový recept není v sobotním plánu:** zkontroluj proměnné GitHub Actions podle bodu 6 a výsledek akce.
