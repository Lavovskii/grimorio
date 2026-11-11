// Teste da língua (r37, Playwright): a escolha pela língua do browser na 1.ª visita e o seletor curto no topo dos dois sites.
// Topo (r38): nos dois sites, com uma personagem e efeitos completos ou leves, a 320/340/360/390/1440 px nenhuma peça do topo se
// sobrepõe a outra nem sai da barra, sem scroll horizontal, toques >= 44 px (ecrãs de toque) e letra >= 12 px.
// Uso: python3 -m http.server 8765 --bind 127.0.0.1   (na raiz do repositório, noutro terminal)
//      node _dev/lingua_browser.cjs [--url http://127.0.0.1:8765/]
// Sai com 1 se algum caso falhar.
const { chromium } = require('playwright');
const i = process.argv.indexOf('--url'), URL0 = i > 0 ? process.argv[i + 1] : 'http://127.0.0.1:8765/', HOST = new URL(URL0).host;
// [navigator.languages, o que está guardado (null = nada), língua esperada]
const CASES = [[['pt-BR'], null, 'pt-BR'], [['pt-PT'], null, 'pt-PT'], [['pt'], null, 'pt-PT'], [['pt-AO', 'en'], null, 'pt-PT'],
  [['de-AT'], null, 'de'], [['sv-SE'], null, 'sv'], [['nl-BE'], null, 'nl'], [['pl'], null, 'pl'], [['es-MX'], null, 'es'],
  [['en-US'], null, 'en'], [['fr-FR'], null, 'en'], [['fr-FR', 'it', 'nl-NL', 'de'], null, 'nl'], [['de-DE'], 'pl', 'pl'],
  [['pt-BR'], 'pt-PT', 'pt-PT'], [['de-DE'], 'xx', 'en']];
(async () => {
  const b = await chromium.launch(), bad = [];
  for (const [langs, st, want] of CASES) {
    const ctx = await b.newContext({ locale: langs[0] });
    await ctx.addInitScript(([langs, st]) => {
      Object.defineProperty(navigator, 'languages', { get: () => langs });
      if (!sessionStorage.getItem('s')) { localStorage.clear(); if (st) localStorage.setItem('grimorio-lang', st); sessionStorage.setItem('s', '1'); }
    }, [langs, st]);
    await ctx.route('**/*', r => new URL(r.request().url()).host === HOST ? r.continue() : r.abort());
    const p = await ctx.newPage();
    await p.goto(URL0 + 'quests/');
    const got = await p.evaluate(() => [document.documentElement.lang, localStorage.getItem('grimorio-lang')]);
    if (got[0] !== want || got[1] !== st) bad.push(`${langs.join(',')} guardado ${st}: ${got.join(' / ')} (esperado ${want} / ${st})`);
    await ctx.close();
  }
  // o seletor do topo nos dois sites, a 1440 e a 390 px
  for (const site of ['', 'quests/']) for (const W of [1440, 390]) {
    const ctx = await b.newContext({ viewport: { width: W, height: 844 }, isMobile: W < 768, hasTouch: W < 768 });
    await ctx.addInitScript(() => { if (!sessionStorage.getItem('s')) { localStorage.clear(); localStorage.setItem('grimorio-lang', 'pt-BR'); localStorage.setItem('grimorio-ui-hint', '1'); sessionStorage.setItem('s', '1'); } });
    await ctx.route('**/*', r => new URL(r.request().url()).host === HOST ? r.continue() : r.abort());
    const p = await ctx.newPage(), errs = [];
    p.on('pageerror', e => errs.push(String(e).slice(0, 150)));
    await p.goto(URL0 + site);
    await p.waitForSelector('header .lang-top select', { timeout: 20000 });
    await p.waitForTimeout(1500);
    const m = await p.evaluate(W => {
      const l = document.querySelector('header .lang-top'), s = l.querySelector('select'), c = l.querySelector('.lang-code'), r = l.getBoundingClientRect(), sr = s.getBoundingClientRect();
      return { code: c.textContent, fs: parseFloat(getComputedStyle(c).fontSize), hit: Math.min(sr.width, sr.height), inView: r.left >= 0 && r.right <= W, label: !!s.getAttribute('aria-label'),
        n: s.options.length, foot: document.querySelectorAll('[data-lang-picker] select').length, hs: document.documentElement.scrollWidth > W + 1 };
    }, W);
    const tag = `${site || 'grimorio/'} ${W}`;
    if (m.code !== 'PT-BR' || m.fs < 12 || m.hit < 44 || !m.inView || !m.label || m.n !== 8 || m.foot < 2 || m.hs || errs.length) bad.push(tag + ': ' + JSON.stringify(m) + ' ' + errs.join(' | '));
    // escolher outra língua no topo grava e recarrega
    await Promise.all([p.waitForNavigation(), p.selectOption('header .lang-top select', 'de')]);
    const now = await p.evaluate(() => [document.documentElement.lang, localStorage.getItem('grimorio-lang')]);
    if (now.join() !== 'de,de') bad.push(tag + ': depois de escolher de → ' + now.join());
    await ctx.close();
  }
  // r38: as peças do topo (filhos de header .in e os links do .sitesw) com uma personagem, a 320–1440 px
  const now = Date.now(), CH = { id: 't1', name: 'Teste Sorc', voc: 'sorcerer', level: 570, pct: 30, ml: 106, skill: 10, world: 'Bona', syncedAt: now, done: {}, charms: {}, imb: {}, owned: {}, tasks: [],
    tib: { voc: 'x', level: 570, guild: null, status: 'Premium Account', others: [], deaths: [], houses: [], former: [], res: 'Thais' }, hs: { at: now, w: 'Bona', sk: { v: 106, r: 500 }, xp: null } };
  const ST = JSON.stringify({ v: 4, active: 't1', chars: [CH], custom: [], ui: { p: 'inicio' } });
  for (const site of ['', 'quests/']) for (const fx of ['full', 'lite']) for (const W of [320, 340, 360, 390, 1440]) {
    const touch = W < 768, ctx = await b.newContext({ viewport: { width: W, height: 800 }, isMobile: touch, hasTouch: touch });
    await ctx.addInitScript(([st, fx]) => { if (!sessionStorage.getItem('s')) { localStorage.clear(); localStorage.setItem('grimorio-tibia-v4', st); localStorage.setItem('grimorio-lang', 'pt-BR');
      localStorage.setItem('grimorio-fx', fx); localStorage.setItem('grimorio-ui-hint', '1'); sessionStorage.setItem('s', '1'); } }, [ST, fx]);
    await ctx.route('**/*', r => new URL(r.request().url()).host === HOST ? r.continue() : r.abort());
    const p = await ctx.newPage();
    await p.goto(URL0 + site);
    await p.waitForSelector(site ? 'header #qchar:not([hidden])' : 'header .csw-btn', { timeout: 20000 });
    await p.waitForTimeout(1500);
    const m = await p.evaluate(([W, touch]) => {
      const bar = document.querySelector('header .in'), vis = e => { const r = e.getBoundingClientRect(), c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && c.display !== 'none'; };
      const nm = e => e.tagName.toLowerCase() + (e.id ? '#' + e.id : e.className && typeof e.className === 'string' ? '.' + e.className.trim().split(/\s+/)[0] : '');
      // a caixa de cada peça junta a dos filhos visíveis (um botão que transborda do invólucro conta), sem o menu aberto da personagem
      const box = e => [e, ...e.querySelectorAll('*')].filter(x => vis(x) && !x.closest('.csw-pop')).map(x => x.getBoundingClientRect())
        .reduce((a, r) => ({ left: Math.min(a.left, r.left), right: Math.max(a.right, r.right), top: Math.min(a.top, r.top), bottom: Math.max(a.bottom, r.bottom) }));
      const it = [...bar.children].filter(vis).flatMap(e => e.matches('.sitesw') ? [...e.children].filter(vis) : [e]).map(e => [nm(e), box(e), e]);
      const out = [], br = bar.getBoundingClientRect(), fx = document.documentElement.classList.contains('fx-lite');
      for (const [n, r, e] of it) {
        if (r.left < Math.max(0, br.left) - .5 || r.right > Math.min(W, br.right) + .5) out.push(`${n} fora da barra (${r.left | 0}–${r.right | 0})`);
        if (e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflow !== 'visible') out.push(`${n} cortado (${e.scrollWidth} > ${e.clientWidth})`);
      }
      for (let i = 0; i < it.length; i++) for (let j = i + 1; j < it.length; j++) {
        const a = it[i][1], c = it[j][1], ox = Math.min(a.right, c.right) - Math.max(a.left, c.left), oy = Math.min(a.bottom, c.bottom) - Math.max(a.top, c.top);
        if (ox > .5 && oy > .5) out.push(`${it[i][0]} sobre ${it[j][0]} (${ox | 0} px)`);
      }
      // toque: a caixa do controlo ou a sua área ::after
      if (touch) for (let e of bar.querySelectorAll('a, button, select, input')) {
        if (!vis(e) || e.closest('.csw-pop')) continue;
        e = e.closest('label') || e;  // o campo da pesquisa toca-se pela etiqueta toda
        const r = e.getBoundingClientRect(), af = getComputedStyle(e, '::after'), aw = parseFloat(af.width) || 0, ah = parseFloat(af.height) || 0;
        const hit = Math.max(Math.min(r.width, r.height), af.content !== 'none' && af.position === 'absolute' ? Math.min(aw, ah) : 0);
        if (hit < 43.5) out.push(`${nm(e)} toque ${hit | 0} px`);
      }
      for (const e of bar.querySelectorAll('*')) if (vis(e) && [...e.childNodes].some(t => t.nodeType === 3 && t.textContent.trim()) && parseFloat(getComputedStyle(e).fontSize) < 12) out.push(`${nm(e)} letra ${getComputedStyle(e).fontSize}`);
      if (document.documentElement.scrollWidth > W + 1) out.push('scroll horizontal ' + document.documentElement.scrollWidth);
      return { out, fx, n: it.length, items: it.map(([n, r]) => `${n}:${r.left | 0}-${r.right | 0}`).join(' ') };
    }, [W, touch]);
    if (m.fx !== (fx === 'lite')) m.out.push('fx-lite ' + m.fx);
    const tag = `topo ${site || 'grimorio/'} ${fx} ${W}`;
    console.log(`${tag}: ${m.out.length ? 'FALHA' : 'ok'} | ${m.items}`);
    if (m.out.length) bad.push(tag + ': ' + m.out.join('; '));
    if (W === 320 && process.env.SHOTS && fx === 'full') await p.screenshot({ path: `${process.env.SHOTS}/topo-${site ? 'questski' : 'grimorio'}-320-${process.env.SHOT_TAG || 'x'}.png`, clip: { x: 0, y: 0, width: 320, height: 140 } });
    await ctx.close();
  }
  await b.close();
  console.log(bad.length ? bad.join('\n') : 'ok');
  process.exit(bad.length ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
