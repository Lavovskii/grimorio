// Teste das fichas no browser (Playwright): Hunts em pt-PT, en e de, a 1440 e a 390 px.
// Uso: python3 -m http.server 8765 --bind 127.0.0.1   (na raiz do repositório, noutro terminal)
//      node _dev/fichas_browser.cjs [--url http://127.0.0.1:8765/]
// Por página: errs (pageerror e erros de consola), hscroll (a página sai para o lado), small (texto visível com letra < 12 px),
// tiny (botões e ligações visíveis do #sheet com menos de 44 px de altura). Sai com 1 se alguma lista não estiver vazia.
// As tarefas 4 e 5 acrescentam os passos de abrir as fichas.
const { chromium } = require('playwright');
const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const URL0 = arg('--url', 'http://127.0.0.1:8765/'), HOST = new URL(URL0).host;

// personagens de teste do _dev/smoke.mjs, já "sincronizadas" (a app não vai ao TibiaData)
function seed() {
  const now = Date.now();
  const mk = (id, name, voc, level, world, ml, skill) => ({ id, tasks: [], name, voc, level, pct: 30, ml, skill, wtype: '', done: {}, charms: {}, imb: {}, owned: {}, target: 0, bonus: '1.5', prey: false, hunt: null, world, syncedAt: now, tib: { voc: 'x', level, guild: null, status: 'Premium Account', others: [], deaths: [], houses: [], former: [], res: 'Thais' }, hs: { at: now, w: world, sk: { v: (voc === 'sorcerer' || voc === 'druid') ? ml : skill, r: 500, k: voc === 'knight' ? 'sword' : undefined }, xp: null } });
  const CH = { sorcerer: mk('t1', 'Teste Sorc', 'sorcerer', 570, 'Bona', 106, 10), knight: mk('t2', 'Teste Knight', 'knight', 812, 'Antica', 12, 121), paladin: mk('t3', 'Teste Pally', 'paladin', 455, 'Secura', 30, 118), druid: mk('t4', 'Teste Druid', 'druid', 300, 'Bona', 85, 10), monk: mk('t5', 'Teste Monk', 'monk', 250, 'Antica', 8, 100) };
  return { v: 4, active: 't1', chars: Object.values(CH), custom: [], ui: { p: 'hunts', band: null, cat: 'all', qf: 'avail', eq: {} } };
}

// corre dentro da página
function audit() {
  const vis = el => { const r = el.getBoundingClientRect(), cs = getComputedStyle(el); return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && +cs.opacity > 0; };
  const W = window.__W, small = [], tiny = [];
  for (const el of document.querySelectorAll('body *')) {
    if (el.closest('.sr-only,.lvl-shield small,script,style,[aria-hidden="true"]')) continue;
    if (![...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) continue;
    if (!vis(el)) continue;
    const fs = parseFloat(getComputedStyle(el).fontSize);
    if (fs < 12) small.push(`${el.tagName.toLowerCase()}.${String(el.className).split(' ')[0]} ${fs}px «${el.textContent.trim().slice(0, 30)}»`);
  }
  for (const el of document.querySelectorAll('#sheet.on button, #sheet.on a[href]')) {
    if (!vis(el)) continue;
    const h = el.getBoundingClientRect().height;
    if (h < 44) tiny.push(`${el.tagName.toLowerCase()}.${String(el.className).split(' ')[0]} ${Math.round(h)}px «${el.textContent.trim().slice(0, 30)}»`);
  }
  return { hscroll: document.documentElement.scrollWidth > W + 1, small: small.slice(0, 10), tiny: tiny.slice(0, 10) };
}

(async () => {
  const b = await chromium.launch();
  let bad = 0;
  for (const lang of ['pt-PT', 'en', 'de']) for (const W of [1440, 390]) {
    const ctx = await b.newContext({ viewport: { width: W, height: W > 800 ? 900 : 844 }, isMobile: W < 768, hasTouch: W < 768 });
    const st = JSON.stringify(seed());
    await ctx.addInitScript(([st, lang]) => {
      if (sessionStorage.getItem('fb-seeded')) return;      // só na 1.ª carga: a página pode gravar o estado depois
      localStorage.clear(); localStorage.setItem('grimorio-tibia-v4', st); localStorage.setItem('grimorio-lang', lang);
      localStorage.setItem('grimorio-ui-hint', '1'); sessionStorage.setItem('fb-seeded', '1');
    }, [st, lang]);
    // só o servidor local: AdSense, TibiaData e outros ficam de fora
    await ctx.route('**/*', r => new URL(r.request().url()).host === HOST ? r.continue() : r.abort());
    const p = await ctx.newPage(), errs = [];
    p.on('pageerror', e => errs.push('pageerror: ' + String(e).slice(0, 200)));
    p.on('console', m => {
      if (m.type() !== 'error') return;
      const u = (m.location() && m.location().url) || '', t = m.text();
      if (u && new URL(u, URL0).host !== HOST) return;                                 // pedidos de fora, abortados de propósito
      if (/Failed to load resource/.test(t) && (/api\/stats\.php/.test(u) || /501/.test(t))) return; // o http.server não aceita o POST das estatísticas
      if (/net::ERR_FAILED/.test(t)) return;
      errs.push('console: ' + t.slice(0, 200) + (u ? ' ' + u : ''));
    });
    await p.goto(URL0 + '#hunts');
    await p.waitForFunction(() => [...document.querySelectorAll('[data-pid]')].some(e => e.getClientRects().length && e.getBoundingClientRect().width > 0), null, { timeout: 30000 });
    await p.waitForTimeout(1200);
    await p.evaluate(W => { window.__W = W; }, W);
    const r = Object.assign({ errs }, await p.evaluate(audit));
    const ok = !r.errs.length && !r.hscroll && !r.small.length && !r.tiny.length;
    if (!ok) bad++;
    console.log(`${lang} ${W}: ${ok ? 'ok' : JSON.stringify(r)}`);
    await ctx.close();
  }
  await b.close();
  process.exit(bad ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
