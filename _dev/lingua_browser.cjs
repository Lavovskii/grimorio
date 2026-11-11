// Teste da língua (r37, Playwright): a escolha pela língua do browser na 1.ª visita e o seletor curto no topo dos dois sites.
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
  await b.close();
  console.log(bad.length ? bad.join('\n') : 'ok');
  process.exit(bad.length ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
