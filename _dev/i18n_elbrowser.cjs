// Elementos repetidos no fim das frases dos caminhos, no browser (Playwright), e palavras pt-PT que ficaram por traduzir.
// Uso: python3 -m http.server 8790 --bind 127.0.0.1   (na raiz, noutro terminal)
//      node _dev/i18n_elbrowser.cjs [--url http://127.0.0.1:8790/] [--langs en,pt-BR,es,de] [--hunts a,b] [--bosses a,b] [--shots <pasta>]
// Em cada língua (a 390 px) abre as fichas das hunts (por omissão bashmu, forgottencrypt, werecrocs e w_carlin_graveyard) e
// dos bosses (Count Vlarkorth). Falha com: erros da página; um negrito/link/<kbd> juntado no fim de um pedaço do caminho (o que o
// shared/i18n.js faz quando não acha o elemento na frase traduzida: texto acabado em «. » ou «( » seguido só de elementos);
// palavras pt-PT no texto da ficha (en/es/de/pl/sv/nl: palavras que só existem em português; pt-BR: o «tu» do pt-PT).
// --shots grava <pasta>/junta-<língua>-forgottencrypt-390.png. Sai com 1 se houver falhas. Ver _dev/i18n_elcheck.py.
const { chromium } = require('playwright');
const path = require('path');
const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const URL0 = arg('--url', 'http://127.0.0.1:8790/'), HOST = new URL(URL0).host, SHOTS = arg('--shots', '');
const LANGS = arg('--langs', 'en,pt-BR,es,de').split(',');
const HUNTS = arg('--hunts', 'bashmu,forgottencrypt,werecrocs,w_carlin_graveyard').split(','), BOSSES = arg('--bosses', 'count vlarkorth').split(',');
// palavras que só existem em português (o espanhol tem «norte», «oeste», «piso», «entradas»…; ficam de fora)
const PT = /(?<![\p{L}])(não|então|também|até|à|às|pela|pelas|sobe|desce|leste|noite|sozinho|gratuita|jangadas|seguintes|devagar|escadas|andares|caminha|chegas|vais|tens|podes|teu|tua|você)(?![\p{L}])/giu;
const PTPT = /(?<![\p{L}])(tens|podes|estás|fazes|vais|teu|tua|teus|tuas|contigo|chegas)(?![\p{L}])/giu;
const sleep = ms => new Promise(r => setTimeout(r, ms));

// corre na página: os pedaços (entre botões e elementos de bloco) dos textos dos caminhos com elementos juntados no fim
function dupScan() {
  const out = [], BLK = /^(BUTTON|DIV|P|LI|OL|UL|DETAILS|SUMMARY|H\d|SECTION|BR)$/;
  for (const box of document.querySelectorAll('#sheetBody .cam-tx, #sheetBody ol.route > li, #sheetBody ul.small > li, #sheetBody .qwarn, #sheetBody [data-campre] li')) {
    let run = [];
    const flush = () => {
      let j = run.length;
      while (j > 0 && (run[j - 1].nodeType === 1 || !/\S/.test(run[j - 1].data))) j--;   // os elementos do fim (e espaços)
      const f = run.findIndex((n, i) => i >= j && n.nodeType === 1), tail = run.slice(j).filter(n => n.nodeType === 1);
      const before = run.slice(0, f < 0 ? j : f).map(n => n.textContent).join('');   // com o espaço que o i18n.js põe antes
      if (tail.length && /[.!?:;(]\s$/.test(before)) out.push((before.slice(-60) + '⟨' + tail.map(n => n.textContent).join('|') + '⟩').replace(/\s+/g, ' '));
      run = [];
    };
    for (const n of box.childNodes) { if (n.nodeType === 1 && BLK.test(n.tagName)) flush(); else run.push(n); }
    flush();
  }
  return out;
}

(async () => {
  const b = await chromium.launch();
  let bad = 0;
  for (const lang of LANGS) {
    const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
    // a mesma personagem do _dev/fichas_browser.cjs (sorcerer 570, já sincronizada: a app não vai ao TibiaData)
    const now = Date.now(), ch = { id: 't1', tasks: [], name: 'Teste Sorc', voc: 'sorcerer', level: 570, pct: 30, ml: 106, skill: 10, wtype: '', done: {}, charms: {}, imb: {}, owned: {}, target: 0, bonus: '1.5', prey: false, hunt: null, world: 'Bona', syncedAt: now,
      tib: { voc: 'x', level: 570, guild: null, status: 'Premium Account', others: [], deaths: [], houses: [], former: [], res: 'Thais' }, hs: { at: now, w: 'Bona', sk: { v: 106, r: 500 }, xp: null } };
    const st = JSON.stringify({ v: 4, active: 't1', chars: [ch], custom: [], ui: { p: 'hunts', band: null, cat: 'all', qf: 'avail', eq: {} } });
    await ctx.addInitScript(([st, lang]) => {
      if (sessionStorage.getItem('eb-seeded')) return;
      localStorage.clear(); localStorage.setItem('grimorio-tibia-v4', st); localStorage.setItem('grimorio-lang', lang);
      localStorage.setItem('grimorio-ui-hint', '1'); sessionStorage.setItem('eb-seeded', '1');
    }, [st, lang]);
    await ctx.route('**/*', r => new URL(r.request().url()).host === HOST ? r.continue() : r.abort());   // AdSense, TibiaData…
    await ctx.route('**/api/market.php*', r => r.fulfill({ status: 503, body: '' }));
    const p = await ctx.newPage(), errs = [], fails = [];
    p.on('pageerror', e => errs.push('pageerror: ' + String(e).slice(0, 200)));
    p.on('console', m => { const u = (m.location() && m.location().url) || '', t = m.text();
      if (m.type() === 'error' && !/Failed to load resource|net::ERR_FAILED/.test(t) && (!u || new URL(u, URL0).host === HOST)) errs.push('console: ' + t.slice(0, 200)); });
    await p.goto(URL0 + '#hunts');
    await p.waitForFunction(() => document.querySelector('[data-pid]'), null, { timeout: 30000 });
    const sheet = async (name, open, a) => {
      await p.evaluate(open, a);
      await p.waitForSelector('#sheet.on #sheetBody', { timeout: 10000 });
      await p.waitForSelector('#sheet.on #sheetBody .fx [data-cam] .cam, #sheet.on #sheetBody .fx [data-camretry]', { timeout: 20000 }).catch(() => {});
      await sleep(1500);
      const r = await p.evaluate(dupScan), txt = await p.evaluate(() => document.querySelector('#sheetBody').textContent);
      const pt = [...new Set((txt.match(lang === 'pt-BR' ? PTPT : PT) || []).map(x => x.toLowerCase()))];
      const nst = await p.evaluate(() => document.querySelectorAll('#sheetBody .cam-tx').length);
      console.log(`  ${lang} ${name}: ${nst} passos, ${r.length} repetidos, pt-PT: ${pt.join(', ') || '-'}`);
      // DUMP=<texto>: o HTML dos passos com esse texto (para ver o que o tradutor fez)
      if (process.env.DUMP) console.log(await p.evaluate(w => [...document.querySelectorAll('#sheetBody .cam-tx, #sheetBody li, #sheetBody p')].filter(e => e.textContent.includes(w)).map(e => '    ' + e.innerHTML).join('\n'), process.env.DUMP));
      r.forEach(x => fails.push(`${name}: repetido: ${x}`));
      if (pt.length) fails.push(`${name}: pt-PT: ${pt.join(', ')}`);
      if (SHOTS && name === 'forgottencrypt') await p.screenshot({ path: path.join(SHOTS, `junta-${lang}-forgottencrypt-390.png`), fullPage: true });
      await p.evaluate(() => { const x = document.querySelector('#sheetX'); if (x) x.click(); });
      await p.waitForFunction(() => !document.querySelector('#sheet.on'), null, { timeout: 5000 }).catch(() => {});
      await sleep(300);
    };
    for (const pid of HUNTS) await sheet(pid, pid => { const x = document.createElement('button'); x.dataset.gs = 'h:' + pid; document.body.appendChild(x); x.click(); x.remove(); }, pid).catch(e => fails.push(`${pid}: ${e.message.split('\n')[0]}`));
    await p.evaluate(() => { location.hash = '#bosses'; });
    await p.waitForSelector('.bs-r [data-boss]', { timeout: 60000 });
    for (const k of BOSSES) await sheet(k, k => { const x = document.createElement('button'); x.dataset.boss = k; document.body.appendChild(x); x.click(); x.remove(); }, k).catch(e => fails.push(`${k}: ${e.message.split('\n')[0]}`));
    const all = errs.concat(fails);
    console.log(`${lang}: ${all.length ? 'FALHA' : 'ok'}`);
    all.forEach(x => console.log('    ' + x));
    if (all.length) bad++;
    await ctx.close();
  }
  await b.close();
  process.exit(bad ? 1 : 0);
})();
