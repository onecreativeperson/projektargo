/* Projekt Argo – floating "A" button on engine pages (projektargo.com/<slug>/).
   The GitHub Action (.github/motory_sync.py) adds <script src="/argo-nav.js" defer></script> before </body> of every engine page.
   Everything lives in a shadow root, so the page's own design and CSS stay untouched.
   Menu: home · all engines · another engine for the same market · this page in another language · contact.
   Engine list: /engines.json (written by the main site build) + public.engine_room_motors() for engines added since. */
(() => {
  if (window.__argoNav || !document.body || !document.querySelector('meta[name="generator"][content="projektargo-motor"]')) return;
  window.__argoNav = 1;
  const SITE = 'https://projektargo.com/';
  const RPC = 'https://asnpyrrdeauhkskkkmuc.supabase.co/rest/v1/rpc/engine_room_motors';
  const KEY = 'sb_publishable_9Nwzk4Ql2WH1PCQZbNe5BQ_-8eVhBve';   /* public key, the same as on the main site */
  const SKIP = /poriadok|agel|zapo|sedne/i;   /* never suggested on engine pages (other audience or not to be mentioned there) */
  const ORD = ['run', 'warm', 'park', 'parts'], SITE_LANGS = ['en', 'sk', 'zh', 'hi', 'es', 'fr', 'ar', 'ru', 'de', 'it', 'pl'];
  const TX = {
    en: ['Projekt Argo – home', 'All engines', 'Same market', 'This page', 'Contact', 'Projekt Argo menu'],
    sk: ['Projekt Argo – úvod', 'Všetky motory', 'Rovnaký trh', 'Táto stránka', 'Kontakt', 'Menu Projekt Argo'],
    cs: ['Projekt Argo – úvod', 'Všechny motory', 'Stejný trh', 'Tato stránka', 'Kontakt', 'Menu Projekt Argo'],
    de: ['Projekt Argo – Start', 'Alle Motoren', 'Gleicher Markt', 'Diese Seite', 'Kontakt', 'Menü Projekt Argo'],
    el: ['Projekt Argo – αρχική', 'Όλες οι μηχανές', 'Ίδια αγορά', 'Αυτή η σελίδα', 'Επικοινωνία', 'Μενού Projekt Argo'],
    pl: ['Projekt Argo – start', 'Wszystkie silniki', 'Ten sam rynek', 'Ta strona', 'Kontakt', 'Menu Projekt Argo'],
    fr: ['Projekt Argo – accueil', 'Tous les moteurs', 'Même marché', 'Cette page', 'Contact', 'Menu Projekt Argo'],
    es: ['Projekt Argo – inicio', 'Todos los motores', 'Mismo mercado', 'Esta página', 'Contacto', 'Menú de Projekt Argo'],
    it: ['Projekt Argo – home', 'Tutti i motori', 'Stesso mercato', 'Questa pagina', 'Contatti', 'Menu Projekt Argo']
  };
  const lang = (document.documentElement.lang || 'en').toLowerCase().split('-')[0];
  const [tHome, tAll, tSame, tPage, tContact, tMenu] = TX[lang] || TX.en;
  const home = SITE + (SITE_LANGS.includes(lang) && lang !== 'en' ? lang + '/' : '');
  const rtl = getComputedStyle(document.documentElement).direction === 'rtl';
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const slug = (location.pathname.split('/').filter(Boolean)[0] || '').toLowerCase();
  /* the Projekt Argo favicon (static/favicon.svg): blue tile, two sails forming an A, hull; k keeps gradient ids unique in the shadow root */
  const FAV = k => `<svg class="f" viewBox="0 0 1024 1024" aria-hidden="true" focusable="false"><defs><linearGradient id="${k}t" x1=".1" y1="0" x2=".9" y2="1"><stop offset="0" stop-color="#5A9DFF"/><stop offset=".5" stop-color="#2A66EA"/><stop offset="1" stop-color="#4636D2"/></linearGradient><radialGradient id="${k}h" cx=".3" cy="0" r=".9"><stop offset="0" stop-color="#fff" stop-opacity=".45"/><stop offset=".55" stop-color="#fff" stop-opacity="0"/></radialGradient></defs><rect width="1024" height="1024" rx="232" fill="url(#${k}t) #2A66EA"/><rect width="1024" height="1024" rx="232" fill="url(#${k}h) none"/><g transform="translate(512 512) scale(.74) translate(-512 -496)" fill="#fff" stroke="#fff" stroke-linejoin="round"><path d="M512 150 178 660H400L512 290Z" fill-opacity=".78" stroke-opacity=".78" stroke-width="14"/><path d="M512 150 846 660H624L512 290Z" stroke-width="14"/><path d="M420 538H604V586H420Z" stroke-width="12"/><path d="M180 716H844L762 820H262Z" stroke-width="20"/></g></svg>`;
  const CHEV = '<svg class="c" viewBox="0 0 16 16" aria-hidden="true"><path d="M6 3l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';

  const host = document.createElement('argo-nav');
  const pos = (b) => `position:fixed!important;z-index:2147483000!important;${rtl ? 'left' : 'right'}:16px!important;${rtl ? 'right' : 'left'}:auto!important;top:auto!important;bottom:calc(${b}px + env(safe-area-inset-bottom, 0px))!important;margin:0!important;padding:0!important;width:56px!important;height:56px!important;display:block!important;transform:none!important`;
  host.setAttribute('style', pos(16));
  const root = host.attachShadow({mode: 'open'});
  root.innerHTML = `<style>
:host{all:initial}
*{box-sizing:border-box}
.b{position:relative;width:56px;height:56px;margin:0;padding:0;border:0;border-radius:12.7px;background:#2A66EA;box-shadow:0 14px 30px -12px rgba(30,64,190,.7),0 3px 8px -2px rgba(0,0,0,.3);display:block;overflow:hidden;cursor:pointer;-webkit-tap-highlight-color:transparent;transition:transform .35s cubic-bezier(.2,.9,.25,1.05)}
.b:active{transform:scale(.94)}
.b:focus-visible,.i:focus-visible{outline:2px solid #8FB2FF;outline-offset:2px}
.b .f{display:block;width:56px;height:56px}
.s{position:fixed;inset:0;background:rgba(4,8,14,.38)}
.p{position:absolute;${rtl ? 'left' : 'right'}:0;bottom:68px;width:300px;max-width:calc(100vw - 32px);max-height:calc(100vh - 110px);overflow:auto;overscroll-behavior:contain;padding:8px;border-radius:24px;background:rgba(28,28,34,.95);border:1px solid rgba(255,255,255,.14);box-shadow:0 24px 60px -20px rgba(0,0,0,.85);color:#F5F5F7;font:500 15px/1.3 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,"Noto Sans",sans-serif;text-align:start;direction:${rtl ? 'rtl' : 'ltr'};transform-origin:${rtl ? 'bottom left' : 'bottom right'}}
.h{margin:0;padding:8px 12px 6px;font-size:11px;font-weight:600;line-height:1.3;letter-spacing:.08em;text-transform:uppercase;color:#A1A1AA}
.l{list-style:none;margin:0;padding:0;display:grid;gap:2px}
.i{display:flex;align-items:center;gap:12px;min-height:46px;padding:6px 10px 6px 8px;border-radius:14px;color:#F5F5F7;text-decoration:none}
.i:hover{background:rgba(255,255,255,.08)}
.g{flex:none;width:30px;height:30px;border-radius:9px;background:rgba(255,255,255,.09);display:inline-grid;place-items:center;font-size:12px;font-weight:700;line-height:1;color:#D4D4DC;overflow:hidden}
.g svg{width:20px;height:20px}
.g .f{width:30px;height:30px}
.g:has(.f){background:none;border-radius:0}
.t{flex:1;min-width:0;display:grid;gap:1px}
.t b{font-weight:500;overflow-wrap:anywhere}
.t small{font-size:12px;color:#A1A1AA}
.n{flex:none;min-width:24px;padding:2px 7px;border-radius:999px;background:rgba(255,255,255,.12);font-size:12px;font-weight:600;line-height:1.3;text-align:center;font-variant-numeric:tabular-nums}
.c{flex:none;width:14px;height:14px;color:#8E8E96}
${rtl ? '.c{transform:scaleX(-1)}' : ''}
[hidden]{display:none!important}
@media (prefers-reduced-motion:no-preference){.p:not([hidden]){animation:in .28s cubic-bezier(.2,.9,.25,1.05)}@keyframes in{from{opacity:0;transform:scale(.92) translateY(8px)}}}
@media print{.b,.p,.s{display:none!important}}
</style><div class="s" hidden></div><nav class="p" id="argo-menu" aria-label="Projekt Argo" hidden><p class="h">Projekt Argo</p><ul class="l"></ul></nav><button class="b" type="button" aria-expanded="false" aria-controls="argo-menu" aria-label="${esc(tMenu)}">${FAV('ab')}</button>`;
  const btn = root.querySelector('.b'), panel = root.querySelector('.p'), scrim = root.querySelector('.s'), ul = root.querySelector('.l');

  let data = null, loading = null;
  function load(){
    if (loading) return loading;
    const get = (url, opt) => fetch(url, opt).then(r => r.ok ? r.json() : null).catch(() => null);
    loading = Promise.all([get('/engines.json', {cache: 'no-cache'}), get(RPC, {headers: {apikey: KEY}})]).then(([built, db]) => {
      let list = (built && Array.isArray(built.engines) ? built.engines : []).filter(e => e && e.id && ORD.includes(e.status)).map(e => Object.assign({}, e));
      if (Array.isArray(db) && db.length) {   /* same rules as the engine room: the database moves engines and adds new ones */
        const seen = new Set();
        db.forEach(m => {
          if (!m || !/^[a-z0-9][a-z0-9-]{1,59}$/.test(m.slug) || !ORD.includes(m.status)) return;
          seen.add(m.slug);
          const e = list.find(x => x.id === m.slug);
          if (e) { e.status = m.status; if (e.db && Array.isArray(m.region)) e.region = m.region; }
          else list.push({id: m.slug, name: String(m.name || m.slug).slice(0, 40), status: m.status, region: Array.isArray(m.region) ? m.region : [], link: SITE + m.slug + '/', db: true});
        });
        list = list.filter(e => !e.db || seen.has(e.id));
      }
      data = list;
      return list;
    });
    return loading;
  }
  function item(href, glyph, label, sub, extra, attrs){
    return `<li><a class="i" href="${esc(href)}"${attrs || ''}><span class="g" aria-hidden="true">${glyph}</span><span class="t"><b>${esc(label)}</b>${sub ? `<small>${esc(sub)}</small>` : ''}</span>${extra || ''}${CHEV}</a></li>`;
  }
  function langName(code){
    try { const n = new Intl.DisplayNames([code], {type: 'language'}).of(code); return n.charAt(0).toLocaleUpperCase(code) + n.slice(1); } catch (e) { return code.toUpperCase(); }
  }
  function render(){
    const list = data || [];
    const at = s => list.find(e => e.id === s || (e.link || '').replace(/[?#].*$/, '').replace(/\/$/, '').split('/').pop() === s);   /* by id or by its page address */
    const me = at(slug) || at(slug.replace(/-[a-z]{2}$/, ''));
    const n = list.length ? `<span class="n">${list.length}</span>` : '';
    let h = item(home, FAV('am'), tHome) + item(home + '#motory', '<svg viewBox="0 0 20 20" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="2.5" y="2.5" width="6" height="6" rx="1.6"/><rect x="11.5" y="2.5" width="6" height="6" rx="1.6"/><rect x="2.5" y="11.5" width="6" height="6" rx="1.6"/><rect x="11.5" y="11.5" width="6" height="6" rx="1.6"/></svg>', tAll, '', n);
    if (me && (me.region || []).length) {
      list.filter(e => e !== me && e.link && !SKIP.test(e.id + ' ' + e.name) && (e.status === 'run' || e.status === 'warm') && (e.region || []).some(r => me.region.includes(r))).slice(0, 2).forEach(e => {
        const ini = esc(e.name.replace(/[^A-Za-z0-9 ]/g, '').split(' ').filter(Boolean).map(w => w[0]).join('').slice(0, 2).toUpperCase() || e.name.slice(0, 1));
        h += item(e.link, ini, e.name, tSame);
      });
    }
    const here = location.href.split(/[?#]/)[0];
    [...document.querySelectorAll('link[rel="alternate"][hreflang]')].forEach(l => {
      const code = (l.getAttribute('hreflang') || '').toLowerCase(), href = l.href;
      if (!code || code === 'x-default' || code.split('-')[0] === lang || !href || href.split(/[?#]/)[0] === here) return;
      h += item(href, esc(code === 'el' ? 'ΕΛ' : code.slice(0, 2).toUpperCase()), langName(code), tPage, '', ` hreflang="${esc(code)}" lang="${esc(code)}"`);
    });
    h += item(home + '#kontakt', '@', tContact);
    ul.innerHTML = h;
  }
  function open(){
    render();
    panel.style.maxHeight = Math.max(180, Math.round(host.getBoundingClientRect().top) - 28) + 'px';   /* room above the button */
    panel.hidden = false; scrim.hidden = false; btn.setAttribute('aria-expanded', 'true');
    const a = ul.querySelector('a'); if (a) a.focus({preventScroll: true});
    load().then(() => { if (!panel.hidden) { const f = root.activeElement && [...ul.querySelectorAll('a')].indexOf(root.activeElement); render(); const all = ul.querySelectorAll('a'); if (f >= 0 && all[f]) all[f].focus({preventScroll: true}); } });
  }
  function close(focus){
    if (panel.hidden) return;
    panel.hidden = true; scrim.hidden = true; btn.setAttribute('aria-expanded', 'false');
    if (focus) btn.focus({preventScroll: true});
  }
  btn.addEventListener('click', () => panel.hidden ? open() : close(true));
  btn.addEventListener('pointerenter', load, {once: true});
  btn.addEventListener('focus', load, {once: true});
  scrim.addEventListener('click', () => close(false));
  root.addEventListener('keydown', e => {
    if (e.key === 'Escape') { e.preventDefault(); close(true); return; }
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      const all = [...ul.querySelectorAll('a')], i = all.indexOf(root.activeElement);
      if (i < 0) return;
      e.preventDefault(); all[(i + (e.key === 'ArrowDown' ? 1 : all.length - 1)) % all.length].focus();
    }
  });
  document.addEventListener('click', e => { if (!panel.hidden && !e.composedPath().includes(host)) close(false); });

  /* stay clear of the page's own fixed bars at the bottom (e.g. a sticky call to action on phones) */
  let fixed = [], raf = 0;
  const watch = 'MutationObserver' in window ? new MutationObserver(() => queue()) : null;   /* a bar that slides in when a class changes */
  function scan(){
    fixed = [];
    if (watch) watch.disconnect();
    for (const el of document.body.getElementsByTagName('*')) {
      if (el === host) continue;
      const p = getComputedStyle(el).position;
      if (p === 'fixed' || p === 'sticky') { fixed.push(el); if (watch) watch.observe(el, {attributes: true, attributeFilter: ['class', 'style', 'hidden']}); }
    }
  }
  function lift(){
    raf = 0;
    const left = rtl ? 16 : innerWidth - 72, right = left + 56;
    let b = 16;
    for (const el of fixed) {
      if (!el.isConnected) continue;
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity < .1 || cs.pointerEvents === 'none' && +cs.opacity < .5) continue;
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height || r.top >= innerHeight || r.bottom < innerHeight - 160 || r.right <= left || r.left >= right) continue;
      if (r.height > innerHeight * .5) continue;   /* a full-height panel is not a bottom bar */
      b = Math.max(b, Math.ceil(innerHeight - r.top + 12));
    }
    host.setAttribute('style', pos(b));
  }
  const queue = () => { if (!raf) raf = requestAnimationFrame(lift); };
  let st = 0;
  const rescan = () => { clearTimeout(st); st = setTimeout(() => { scan(); queue(); }, 120); };
  addEventListener('scroll', queue, {passive: true});
  addEventListener('resize', rescan);
  document.addEventListener('transitionend', queue, true);
  document.addEventListener('animationend', queue, true);
  if ('MutationObserver' in window) new MutationObserver(rescan).observe(document.body, {childList: true});
  document.body.appendChild(host);
  scan(); lift();
  setTimeout(() => { scan(); queue(); }, 1500);
  setInterval(() => { if (!document.hidden && fixed.length) queue(); }, 1000);   /* safety net for bars moved by script without a class change */
})();
