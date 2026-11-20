/* U stolu: user accounts + server-enforced role access via Supabase Auth and RLS.
 * This file never contains a service key or privileged credential. */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const cfg = window.USTOLU_BACKEND || {};
  const configured = /^https:\/\/[a-z0-9-]+\.supabase\.co\/?$/i.test(cfg.supabaseUrl || '')
    && typeof cfg.supabasePublishableKey === 'string' && cfg.supabasePublishableKey.length > 15;
  const client = configured && window.supabase?.createClient
    ? window.supabase.createClient(cfg.supabaseUrl.replace(/\/$/, ''), cfg.supabasePublishableKey, {
      auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true }
    }) : null;
  let user = null;
  let admin = false;
  let favorites = new Set();
  let overrides = [];
  let mode = 'login';
  let authGeneration = 0;
  let recoveryMode = false;
  let editorImageUrl = null;

  function message(elementId, text, isSuccess = false) {
    const el = $(elementId); if (!el) return;
    el.textContent = text;
    el.classList.toggle('success', Boolean(isSuccess));
  }
  function friendly(error) {
    const msg = String(error?.message || error || 'Neznámá chyba');
    if (/Invalid login credentials/i.test(msg)) return 'Neplatný e-mail nebo heslo.';
    if (/Email not confirmed/i.test(msg)) return 'Nejprve potvrď e-mail pomocí odkazu, který ti přišel.';
    if (/User already registered/i.test(msg)) return 'Tento e-mail už je zaregistrovaný.';
    if (/rate limit/i.test(msg)) return 'Příliš mnoho pokusů. Zkus přihlášení později.';
    if (/row-level security|permission denied|not allowed/i.test(msg)) return 'K této akci nemáš oprávnění. Zkontroluj administrátorský účet.';
    return msg;
  }
  function showDialog() {
    if (!$('accountDialog').open) $('accountDialog').showModal();
    if (!client) message('accountStatus', 'Registrace a přihlášení se zpřístupní po propojení aplikace se Supabase podle návodu.');
  }
  function setMode(next) {
    mode = next;
    $('accountForm').hidden = Boolean(user) && next !== 'recovery';
    $('loggedInPanel').hidden = !user || next === 'recovery';
    $('accountSwitch').hidden = Boolean(user) || next === 'recovery';
    $('accountEmailRow').hidden = next === 'recovery';
    $('accountEmail').required = next !== 'recovery';
    $('accountPassword').required = next !== 'forgot';
    $('accountPassword').autocomplete = next === 'signup' || next === 'recovery' ? 'new-password' : 'current-password';
    $('accountHeading').textContent = ({ login: 'Přihlášení', signup: 'Vytvořit účet', forgot: 'Obnovit heslo', recovery: 'Nastavit nové heslo' })[next];
    $('accountHelp').textContent = ({login:'Přihlas se, aby se oblíbené recepty synchronizovaly mezi zařízeními.',signup:'Vytvoř si vlastní účet. Dostaneš e-mail k potvrzení registrace.',forgot:'Pošleme ti odkaz pro nastavení nového hesla.',recovery:'Zadej nové heslo (alespoň 8 znaků).' })[next];
    $('accountSubmit').textContent = ({ login: 'Přihlásit se', signup: 'Vytvořit účet', forgot: 'Odeslat obnovovací e-mail', recovery: 'Uložit nové heslo' })[next];
    $('accountPassword').parentElement.hidden = next === 'forgot';
    message('accountStatus', '');
  }
  function setAccountUi() {
    $('accountButton').textContent = user ? `Můj účet · ${user.email || 'přihlášen'}` : 'Přihlásit se / Registrace';
    $('loggedInEmail').textContent = user?.email || '';
    $('loggedInRole').textContent = admin ? 'Administrátor · může upravovat recepty' : 'Běžný účet · oblíbené recepty';
    $('adminNav').hidden = !admin;
    if (!admin && document.querySelector('#view-admin:not([hidden])')) window.UStoluApp?.navigate('catalog');
    if (!recoveryMode) setMode(user ? 'login' : 'login');
    refreshFavoritesUi();
  }
  function decorateFavoriteButton(button, recipeId) {
    if (!button || !recipeId) return;
    const saved = favorites.has(recipeId);
    button.setAttribute('aria-pressed', String(saved));
    button.textContent = saved ? '♥ V oblíbených' : '♡ Uložit do oblíbených';
    button.title = saved ? 'Odebrat z oblíbených' : 'Přidat do oblíbených';
  }
  function refreshFavoritesUi() {
    document.querySelectorAll('.favorite-button[data-recipe-id]').forEach(button => decorateFavoriteButton(button, button.dataset.recipeId));
    window.UStoluApp?.refreshFavorites();
  }
  async function toggleFavorite(recipeId) {
    if (!recipeId) return;
    if (!user) { setMode('login'); showDialog(); return; }
    if (!client) { showDialog(); return; }
    const wasSaved = favorites.has(recipeId);
    const result = wasSaved
      ? await client.from('favorites').delete().eq('user_id', user.id).eq('recipe_id', recipeId)
      : await client.from('favorites').insert({user_id: user.id, recipe_id: recipeId});
    if (result.error) { message('accountStatus', friendly(result.error)); showDialog(); return; }
    if (wasSaved) favorites.delete(recipeId); else favorites.add(recipeId);
    refreshFavoritesUi();
  }
  async function updateSession(session) {
    const ticket = ++authGeneration;
    user = session?.user || null;
    admin = false;
    favorites = new Set();
    setAccountUi();
    if (!user || !client) return;
    const [role, saved] = await Promise.all([
      client.from('admin_users').select('user_id').eq('user_id', user.id).maybeSingle(),
      client.from('favorites').select('recipe_id').eq('user_id', user.id).limit(1000)
    ]);
    if (ticket !== authGeneration) return;
    if (role.error) message('accountStatus', 'Nepodařilo se ověřit roli: ' + friendly(role.error));
    else admin = Boolean(role.data);
    if (saved.error) message('accountStatus', 'Nepodařilo se načíst oblíbené: ' + friendly(saved.error));
    else favorites = new Set((saved.data || []).map(entry => entry.recipe_id));
    setAccountUi();
    if (admin) renderAdminChoices();
  }
  async function loadOverrides() {
    if (!client) return;
    try {
      const rows = [];
      for (let from = 0; from < 10000; from += 500) {
        const {data, error} = await client.from('recipes').select('id,body,image_url').order('id').range(from, from + 499);
        if (error) throw error;
        rows.push(...(data || []));
        if (!data || data.length < 500) break;
      }
      overrides = rows;
      window.UStoluApp?.applyRemoteRecipes(overrides);
    } catch (error) {
      message('accountStatus', 'Některé online recepty se nepodařilo načíst: ' + friendly(error));
    }
  }
  function imageFor(recipe) {
    return recipe?.remote_image || recipe?.image || 'assets/placeholder.svg';
  }
  function editorStatus(text, ok = false) { message('adminStatus', text, ok); }
  function renderAdminChoices(search = '') {
    if (!admin) return;
    const select = $('adminRecipeSelect');
    const oldValue = select.value;
    const list = (window.UStoluApp?.getRecipes() || []).filter(r => r.title.toLocaleLowerCase('cs').includes(search.toLocaleLowerCase('cs')) || r.id.includes(search.toLowerCase()));
    select.replaceChildren();
    for (const r of list) {
      const option = document.createElement('option');
      option.value = r.id;
      option.textContent = `${r.title} · ${r.id}`;
      select.append(option);
    }
    if (list.some(r => r.id === oldValue)) select.value = oldValue;
  }
  function setPreview(src) {
    if (editorImageUrl) URL.revokeObjectURL(editorImageUrl);
    editorImageUrl = null;
    $('adminPreview').src = src || 'assets/placeholder.svg';
  }
  function fillEditor(recipe) {
    if (!admin) return;
    $('adminForm').reset();
    $('adminId').value = recipe?.id || '';
    $('adminId').readOnly = Boolean(recipe);
    $('adminCategory').value = recipe?.category || 'dinner';
    $('adminTitle').value = recipe?.title || '';
    $('adminDescription').value = recipe?.description || '';
    $('adminMinutes').value = recipe?.minutes || 30;
    $('adminProtein').value = recipe?.protein || 'vegetarian';
    $('adminFamily').value = recipe?.family || '';
    $('adminMethod').value = recipe?.method || 'bake';
    $('adminAllergens').value = (recipe?.allergens || []).join(', ');
    $('adminIngredients').value = (recipe?.ingredients || []).map(i => `${i.name} | ${i.amount} | ${i.unit} | ${i.section}`).join('\n');
    $('adminSteps').value = (recipe?.steps || []).join('\n');
    setPreview(imageFor(recipe));
    editorStatus(recipe ? 'Upravuješ existující recept.' : 'Nový recept: vyplň formulář a ulož.');
  }
  function validateAndBuildRecipe() {
    const id = $('adminId').value.trim();
    if (!/^[a-z0-9][a-z0-9-]{2,79}$/.test(id)) throw new Error('ID smí obsahovat jen malá písmena, číslice a pomlčky (3–80 znaků).');
    const title = $('adminTitle').value.trim();
    if (!title || title.length > 160) throw new Error('Vyplň název receptu (max. 160 znaků).');
    const minutes = Number($('adminMinutes').value);
    if (!Number.isInteger(minutes) || minutes < 1 || minutes > 600) throw new Error('Doba přípravy musí být celé číslo 1–600 minut.');
    const ingredients = $('adminIngredients').value.split('\n').map(s => s.trim()).filter(Boolean).map((line, idx) => {
      const parts = line.split('|').map(v => v.trim());
      if (parts.length !== 4 || !parts[0] || !parts[3]) throw new Error(`Surovina na řádku ${idx + 1}: použij název | množství | g/ml/ks | kategorie.`);
      const amount = Number(parts[1].replace(',', '.'));
      if (!Number.isFinite(amount) || amount <= 0 || !['g','ml','ks'].includes(parts[2])) throw new Error(`Surovina na řádku ${idx + 1}: neplatné množství nebo jednotka.`);
      return {name: parts[0], amount, unit: parts[2], section: parts[3]};
    });
    if (ingredients.length < 2) throw new Error('Recept musí obsahovat nejméně dvě suroviny.');
    const steps = $('adminSteps').value.split('\n').map(s => s.trim()).filter(Boolean);
    if (steps.length < 3) throw new Error('Přidej nejméně tři kroky přípravy.');
    const existing = window.UStoluApp.getRecipes().find(r => r.id === id);
    const family = $('adminFamily').value.trim() || existing?.family || `vlastni-${id}`;
    const recipe = {
      ...(existing || {}), id, title, category: $('adminCategory').value,
      description: $('adminDescription').value.trim(), minutes, servings: 2,
      protein: $('adminProtein').value, family, method: $('adminMethod').value,
      season: existing?.season || ['all'],
      ingredients, steps,
      allergens: $('adminAllergens').value.split(',').map(s => s.trim()).filter(Boolean),
      image: existing?.image || 'assets/placeholder.svg',
      image_kind: existing?.image_kind || 'fotografie / ilustrace'
    };
    delete recipe.remote_image;
    return recipe;
  }
  function uploadInfo(file) {
    if (!file) return null;
    const allowed = {'image/png': 'png','image/jpeg':'jpg','image/webp':'webp'};
    const extension = allowed[file.type];
    if (!extension) throw new Error('Fotografie musí být PNG, JPG nebo WebP.');
    if (file.size > 6 * 1024 * 1024) throw new Error('Fotografie musí mít méně než 6 MB.');
    return extension;
  }
  async function saveRecipe(event) {
    event.preventDefault();
    if (!user || !admin || !client) { editorStatus('Jen administrátor může ukládat recepty.'); return; }
    const save = $('adminSave');
    try {
      const recipe = validateAndBuildRecipe();
      const file = $('adminPhoto').files[0];
      const extension = uploadInfo(file);
      const prior = overrides.find(x => x.id === recipe.id);
      let imageUrl = prior?.image_url || null;
      save.disabled = true;
      editorStatus('Ukládám recept…');
      if (file) {
        const name = `${recipe.id}/${crypto.randomUUID()}.${extension}`;
        const {data, error} = await client.storage.from('recipe-images').upload(name, file, {contentType: file.type, upsert: false, cacheControl: '31536000'});
        if (error) throw error;
        imageUrl = client.storage.from('recipe-images').getPublicUrl(data.path).data.publicUrl;
      }
      const {error} = await client.from('recipes').upsert({id:recipe.id,body:recipe,image_url:imageUrl}, {onConflict:'id'});
      if (error) throw error;
      await loadOverrides();
      renderAdminChoices($('adminRecipeSearch').value.trim());
      $('adminRecipeSelect').value = recipe.id;
      const savedRecipe = window.UStoluApp.getRecipes().find(r => r.id === recipe.id);
      fillEditor(savedRecipe);
      editorStatus('Recept byl uložen a je dostupný ve veřejné knihovně.', true);
    } catch (err) {
      editorStatus('Nepodařilo se uložit: ' + friendly(err));
    } finally { save.disabled = false; }
  }
  async function submitAuth(event) {
    event.preventDefault();
    if (!client) { message('accountStatus', 'Nejdřív propoj aplikaci se Supabase podle instalačního návodu.'); return; }
    const email = $('accountEmail').value.trim();
    const password = $('accountPassword').value;
    if (mode !== 'forgot' && password.length < 8) { message('accountStatus','Heslo musí mít alespoň 8 znaků.'); return; }
    const button = $('accountSubmit'); button.disabled = true;
    try {
      let result;
      if (mode === 'signup') {
        result = await client.auth.signUp({email, password, options: {emailRedirectTo: location.origin + location.pathname}});
        if (result.error) throw result.error;
        if (result.data?.session) { $('accountDialog').close(); await updateSession(result.data.session); }
        else message('accountStatus', 'Registrace přijata. Potvrď svou e-mailovou adresu přes odkaz v e-mailu.', true);
      } else if (mode === 'login') {
        result = await client.auth.signInWithPassword({email,password});
        if (result.error) throw result.error;
        $('accountDialog').close();
        await updateSession(result.data.session);
      } else if (mode === 'forgot') {
        result = await client.auth.resetPasswordForEmail(email,{redirectTo: location.origin + location.pathname});
        if (result.error) throw result.error;
        message('accountStatus', 'Pokud účet existuje, obdržíš e-mail s odkazem pro obnovení hesla.', true);
      } else if (mode === 'recovery') {
        result = await client.auth.updateUser({password});
        if (result.error) throw result.error;
        recoveryMode = false;
        setMode('login');
        message('accountStatus', 'Heslo bylo změněno.', true);
      }
    } catch (error) { message('accountStatus', friendly(error)); }
    finally { button.disabled = false; }
  }
  function wire() {
    $('accountButton').addEventListener('click', () => { setMode('login'); showDialog(); });
    $('closeAccount').addEventListener('click', () => $('accountDialog').close());
    $('accountDialog').addEventListener('click', e => { if (e.target === $('accountDialog')) $('accountDialog').close(); });
    $('accountForm').addEventListener('submit', submitAuth);
    document.querySelectorAll('[data-account-mode]').forEach(button => button.addEventListener('click', () => setMode(button.dataset.accountMode)));
    $('accountLogout').addEventListener('click', async () => {
      if (!client) return;
      const result = await client.auth.signOut();
      if (result.error) message('accountStatus', friendly(result.error));
      else { $('accountDialog').close(); await updateSession(null); }
    });
    $('adminNew').addEventListener('click', () => { $('adminRecipeSelect').selectedIndex = -1; fillEditor(null); });
    $('adminRecipeSelect').addEventListener('change', () => {
      const r = window.UStoluApp?.getRecipes().find(r => r.id === $('adminRecipeSelect').value);
      if (r) fillEditor(r);
    });
    $('adminRecipeSearch').addEventListener('input', () => renderAdminChoices($('adminRecipeSearch').value));
    $('adminPhoto').addEventListener('change', () => {
      const file = $('adminPhoto').files[0];
      try {
        if (!file) return;
        uploadInfo(file);
        setPreview('assets/placeholder.svg');
        editorImageUrl = URL.createObjectURL(file);
        $('adminPreview').src = editorImageUrl;
      } catch(error) { $('adminPhoto').value = ''; editorStatus(friendly(error)); }
    });
    $('adminForm').addEventListener('submit', saveRecipe);
    window.addEventListener('ustolu:loaded', () => window.UStoluApp?.applyRemoteRecipes(overrides));
    window.addEventListener('ustolu:recipes-updated', () => renderAdminChoices($('adminRecipeSearch').value));
  }
  async function boot() {
    wire(); setAccountUi();
    if (!client) return;
    client.auth.onAuthStateChange((event, session) => {
      if (event === 'PASSWORD_RECOVERY') {
        recoveryMode = true;
        setMode('recovery');
        showDialog();
      }
      // Do not await database calls within the auth callback (avoids auth lock deadlocks).
      setTimeout(() => updateSession(session).catch(error => message('accountStatus', friendly(error))), 0);
    });
    const {data, error} = await client.auth.getSession();
    if (!error) await updateSession(data.session);
    await loadOverrides();
  }
  window.UStoluAccounts = {
    isLoggedIn: () => Boolean(user),
    isAdmin: () => admin,
    isFavorite: id => favorites.has(id),
    toggleFavorite,
    decorateFavoriteButton,
    openLogin: showDialog
  };
  document.addEventListener('DOMContentLoaded', () => boot().catch(e => message('accountStatus', friendly(e))));
})();
