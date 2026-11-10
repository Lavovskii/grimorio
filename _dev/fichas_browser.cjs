// Teste das fichas no browser (Playwright): Hunts em pt-PT, en e de, a 1440 e a 390 px.
// Uso: python3 -m http.server 8765 --bind 127.0.0.1   (na raiz do repositório, noutro terminal)
//      node _dev/fichas_browser.cjs [--url http://127.0.0.1:8765/]
// Por página: errs (pageerror e erros de consola), hscroll (a página sai para o lado), small (texto visível com letra < 12 px),
// tiny (botões e ligações visíveis do #sheet com menos de 44 px de altura; conta como 44 o ::after de 44 px que o site dá às
// ligações no meio do texto nos ecrãs de toque e, sem toque (1440 px), um elemento a que uma regra @media do site para toque ou
// ecrã estreito dá 44 px). Sai com 1 se alguma lista não estiver vazia.
// Task 4: abre a ficha da 1.ª hunt em cada combinação (estrutura fixa) e, em pt-PT, a ficha de uma hunt com lucro negativo,
// o mapa de um troço, uma hunt «por documentar», uma hunt de outra vocação pela pesquisa (número estimado), os preços do
// Market (resposta fixa, 503 e sem mundo), a dificuldade do sorcerer sem set e do knight com set guardado, e o comparar hunts.
// Task 5: abre a ficha do 1.º boss da lista em cada combinação (a mesma estrutura, sem charms e preys; o botão do Bosstiary
// continua na linha) e, em pt-PT, um boss de alavanca com guias, um de raid e um sem posição, e a nota do set do knight.
// Task 6: em en e de, a ficha da 1.ª hunt, a da Forgotten Crypt (troço de um local), a do 1.º boss e a do boss de alavanca não
// podem ter nenhuma das frases pt-PT escritas à mão para as fichas (i18n/src/ui-extra.json, contexto «à mão (r35)»).
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
// frases pt-PT da Task 6 (as fixas inteiras; dos modelos, as partes fixas com 6+ letras)
const PT35 = Object.entries(JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'i18n', 'src', 'ui-extra.json'), 'utf8')))
  .filter(([, v]) => /^à mão \(r35\)/.test(v.c))
  .flatMap(([k, v]) => v.k === 'x' ? [k] : k.split(/\{\d+\}/).map(x => x.trim()).filter(x => x.replace(/[^\p{L}]/gu, '').length >= 6));
// corre dentro da página: as frases da lista que aparecem no texto da ficha (palavras inteiras)
function ptLeft(list) {
  const t = document.querySelector('#sheetBody').innerText;
  return list.filter(k => new RegExp('(?<![\\p{L}])' + k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '(?![\\p{L}])', 'u').test(t));
}
const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const URL0 = arg('--url', 'http://127.0.0.1:8765/'), HOST = new URL(URL0).host;
// hunt em que o sorcerer 570 sem set e o knight 812 com o set «Proteção» têm dificuldades diferentes
const DIFF_PID = 'jadedroots';
// set do knight com proteções (ids reais do G.items): Might ring, Stone skin amulet, Spiritthorn armor, Sanguine legs,
// Pair of soulwalkers, Soulbastion
const KSET = { id: 'k1', name: 'Proteção', mode: 'combat', prot: '', slots: { ring: { id: 3048 }, amulet: { id: 3081 }, armor: { id: 39147 }, legs: { id: 43876 }, boots: { id: 34097 }, shield: { id: 34099 } } };

// personagens de teste do _dev/smoke.mjs, já "sincronizadas" (a app não vai ao TibiaData); o knight tem um set guardado
function seed() {
  const now = Date.now();
  const mk = (id, name, voc, level, world, ml, skill) => ({ id, tasks: [], name, voc, level, pct: 30, ml, skill, wtype: '', done: {}, charms: {}, imb: {}, owned: {}, target: 0, bonus: '1.5', prey: false, hunt: null, world, syncedAt: now, tib: { voc: 'x', level, guild: null, status: 'Premium Account', others: [], deaths: [], houses: [], former: [], res: 'Thais' }, hs: { at: now, w: world, sk: { v: (voc === 'sorcerer' || voc === 'druid') ? ml : skill, r: 500, k: voc === 'knight' ? 'sword' : undefined }, xp: null } });
  const CH = { sorcerer: mk('t1', 'Teste Sorc', 'sorcerer', 570, 'Bona', 106, 10), knight: mk('t2', 'Teste Knight', 'knight', 812, 'Antica', 12, 121), paladin: mk('t3', 'Teste Pally', 'paladin', 455, 'Secura', 30, 118), druid: mk('t4', 'Teste Druid', 'druid', 300, 'Bona', 85, 10), monk: mk('t5', 'Teste Monk', 'monk', 250, 'Antica', 8, 100) };
  Object.assign(CH.knight, { sets: [KSET], aset: 'k1', hset: 'mine' });
  return { v: 4, active: 't1', chars: Object.values(CH), custom: [], ui: { p: 'hunts', band: null, cat: 'all', qf: 'avail', eq: {} } };
}

// corre dentro da página
function audit() {
  const vis = el => { const r = el.getBoundingClientRect(), cs = getComputedStyle(el); return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && +cs.opacity > 0; };
  const W = window.__W, small = [], tiny = [], touch = matchMedia('(pointer:coarse)').matches, big = [];
  // seletores com 44 px dentro de @media (pointer:coarse) ou (max-width:…): o tratamento de toque do site
  const walk = (rules, inM) => { for (const r of rules) { if (r.cssRules && r.conditionText !== undefined) walk(r.cssRules, inM || /pointer:\s*coarse|max-width/.test(r.conditionText));
    else if (inM && r.selectorText && r.style && [r.style.minHeight, r.style.height].some(v => parseFloat(v) >= 44)) big.push(...r.selectorText.split(',').map(x => x.replace(/::after/g, '').trim())); } };
  for (const sh of document.styleSheets) { try { walk(sh.cssRules, false); } catch (e) {} }
  const fits = el => big.some(x => { try { return el.matches(x); } catch (e) { return false; } });
  for (const el of document.querySelectorAll('body *')) {
    if (el.closest('.sr-only,.lvl-shield small,script,style,[aria-hidden="true"]')) continue;
    if (![...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) continue;
    if (!vis(el)) continue;
    const fs = parseFloat(getComputedStyle(el).fontSize);
    if (fs < 12) small.push(`${el.tagName.toLowerCase()}.${String(el.className).split(' ')[0]} ${fs}px «${el.textContent.trim().slice(0, 30)}»`);
  }
  for (const el of document.querySelectorAll('#sheet.on button, #sheet.on a[href]')) {
    if (!vis(el)) continue;
    const h = el.getBoundingClientRect().height, af = getComputedStyle(el, '::after');
    if (h >= 44 || (af.content !== 'none' && af.position === 'absolute' && parseFloat(af.height) >= 44) || (!touch && fits(el))) continue;
    tiny.push(`${el.tagName.toLowerCase()}.${String(el.className).split(' ')[0]} ${Math.round(h)}px «${el.textContent.trim().slice(0, 30)}»`);
  }
  return { hscroll: document.documentElement.scrollWidth > W + 1, small: small.slice(0, 10), tiny: tiny.slice(0, 10) };
}

// estrutura fixa da ficha (Task 4; com boss, a da Task 5: sem .fx-tips); devolve a lista de problemas
function fxCheck(a) {
  const W = a.W || a, boss = !!a.boss, B = document.querySelector('#sheetBody'), out = [], q = s => B.querySelector(s);
  const top = q('.fx-top');
  if (!top) return ['.fx-top não existe'];
  const ch = [...top.children].map(x => x.className.split(' ')[0]);
  if (ch.join() !== 'fx-map,fx-cam') out.push('.fx-top: ' + ch.join());
  else {
    const a = top.children[0].getBoundingClientRect(), b = top.children[1].getBoundingClientRect();
    if (W >= 760 && Math.abs(a.top - b.top) > 4) out.push(`mapa e caminho não estão lado a lado (${a.top}/${b.top})`);
    if (W < 760 && a.bottom > b.top + 4) out.push('a 390 px o mapa não está por cima do caminho');
  }
  const st = [...B.querySelectorAll('.fx-stats > .fx-s')].map(x => x.dataset.fxs);
  if (st.join() !== 'xp,lo,lv,res,dif') out.push('.fx-stats: ' + st.join());
  const order = ['.fx-top', '.fx-stats', '[data-campre]', '.fx-mons', '.fx-loot', ...(boss ? [] : ['.fx-tips'])].map(s => [s, q(s)]);
  if (boss) {
    if (q('.fx-tips')) out.push('boss com .fx-tips');
    const L = [...B.querySelectorAll('.fx-stats > .fx-s > .fx-l')].map(x => x.textContent.trim());
    if (document.documentElement.lang === 'pt-PT' && L.join() !== 'XP por kill,valor por kill,nível recomendado,resistências,dificuldade') out.push('rótulos do boss: ' + L.join());
    const d = q('[data-fxs="dif"]');
    if (!d || !/\d\/5/.test(d.textContent)) out.push('boss sem dificuldade N/5');
    else if (document.documentElement.lang === 'pt-PT' && (!/para o teu nível/.test(d.textContent) || !/^Contas com o /.test((d.querySelector('.fx-pl') || {}).textContent || ''))) out.push('dificuldade do boss sem «para o teu nível» ou sem a nota do set: ' + d.textContent);
    if (document.querySelector('details.bs-d')) out.push('ainda existe details.bs-d');
  }
  order.forEach(([s, e]) => { if (!e) out.push('falta ' + s); });
  for (let i = 1; i < order.length; i++) { const a = order[i - 1][1], b = order[i][1];
    if (a && b && !(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING)) out.push(`${order[i][0]} antes de ${order[i - 1][0]}`); }
  ['.tabs', '.whatb', '[data-hwheel]', '.hsets', '[data-kstat]', '[data-lootp]'].forEach(s => { if (q(s)) out.push('ainda existe ' + s); });
  const tips = q('.fx-tips');
  if (tips) {
    if (!tips.querySelector('.fx-charms')) out.push('.fx-tips sem charms');
    if (!tips.querySelector('.fx-preys')) out.push('.fx-tips sem preys');
    tips.querySelectorAll('.fx-prey li').forEach(li => { if (!li.querySelector('a') || !li.querySelector('a').textContent.trim()) out.push('prey sem criatura');
      const t = (li.querySelector('.tag') || {}).textContent || '';
      if (!t.trim() || (document.documentElement.lang === 'pt-PT' && !['Bónus de XP', 'Bónus de dano', 'Redução de dano'].includes(t.trim()))) out.push('prey sem bónus: ' + t); });
  }
  if (/NaN|undefined/.test(B.innerText)) out.push('NaN ou undefined no texto');
  return out;
}

// Task 5: bosses. Em cada combinação: o 1.º boss da lista e o botão do Bosstiary; em pt-PT, três bosses escolhidos
const BOSS_LEVER = 'count vlarkorth', BOSS_RAID = 'barbaria', BOSS_NOPOS = 'abyssador';
// boss em que o knight 812 com o set «Proteção» e com o best set dá outro nível sozinho (o golpe com as proteções, crdmg.json)
const BOSS_PROT = 'ghazbaran';
// espera pelo data/crdmg.json (o renderBosses desenha outra vez quando chega)
const crdWait = p => p.waitForFunction(() => performance.getEntriesByType('resource').some(e => /data\/crdmg\.json/.test(e.name) && e.responseEnd > 0), null, { timeout: 30000 }).then(() => sleep(800));
const lvOf = async (p, k) => { await openBoss(p, k); const t = await p.evaluate(() => (document.querySelector('#sheetBody [data-fxs="lv"] .fx-v') || {}).textContent || ''); await closeSheet(p); return t.trim(); };
async function openBoss(p, k) {
  await p.evaluate(k => { const x = document.createElement('button'); x.dataset.boss = k; document.body.appendChild(x); x.click(); x.remove(); }, k);
  await waitSheet(p);
}
async function bosses(p, W, lang, r, fails) {
  await p.evaluate(() => { location.hash = '#bosses'; });
  await p.waitForSelector('.bs-r [data-boss]', { timeout: 60000 });
  await sleep(500);
  if (await p.evaluate(() => !!document.querySelector('details.bs-d'))) fails.push('a lista ainda tem details.bs-d');
  // o Bosstiary roda o estágio na linha (4 toques = volta ao início)
  const k0 = await p.evaluate(() => document.querySelector('.bs-r [data-bstier]').dataset.bstier);
  const tier = () => p.evaluate(k => { const b = document.querySelector(`.bs-r [data-bstier="${CSS.escape(k)}"]`); return b ? (b.className.match(/\bs(\d)\b/) || [])[1] : null; }, k0);
  const t0 = await tier();
  await p.click(`.bs-r [data-bstier="${k0}"]`); const t1 = await tier();
  for (let i = 0; i < 3; i++) await p.click(`.bs-r [data-bstier="${k0}"]`);
  const t4 = await tier();
  if (t0 !== '0' || t1 !== '1' || t4 !== '0') fails.push(`Bosstiary de ${k0}: ${t0} → ${t1} → ${t4}`);
  await p.locator('.bs-r [data-boss]:visible').first().click();
  await waitSheet(p);
  fails.push(...(await p.evaluate(fxCheck, { W, boss: true })).map(x => 'boss: ' + x));
  const a = await p.evaluate(audit); r.hscroll = r.hscroll || a.hscroll; r.small.push(...a.small); r.tiny.push(...a.tiny);
  if (lang !== 'pt-PT') { const pt = await p.evaluate(ptLeft, PT35); if (pt.length) fails.push('boss com pt-PT: ' + pt.join(' | ')); }
  await closeSheet(p);
  if (lang !== 'pt-PT') { await openBoss(p, BOSS_LEVER); const pt = await p.evaluate(ptLeft, PT35); if (pt.length) fails.push(`${BOSS_LEVER} com pt-PT: ` + pt.join(' | ')); await closeSheet(p); return; }
  const one = async (k, f) => { await openBoss(p, k);
    const s = await p.evaluate(fxCheck, { W, boss: true }); if (s.length) fails.push(`${k}: ${s.join('; ')}`);
    const x = await p.evaluate(() => { const B = document.querySelector('#sheetBody');
      return { map: B.querySelector('.fx-map').textContent, cv: !!B.querySelector('.fx-map canvas.qpos'), mons: B.querySelector('.fx-mons').textContent, refs: B.querySelectorAll('.cam-refs li').length,
        pre: B.querySelectorAll('[data-campre] li').length, note: (B.querySelector('[data-fxs="dif"] .fx-pl') || {}).textContent || '' }; });
    f(x); const a = await p.evaluate(audit); r.hscroll = r.hscroll || a.hscroll; r.small.push(...a.small); r.tiny.push(...a.tiny); await closeSheet(p); };
  await one(BOSS_LEVER, x => { if (!x.refs) fails.push(`${BOSS_LEVER}: sem as ligações aos guias`); if (!x.pre) fails.push(`${BOSS_LEVER}: sem pré-requisitos`);
    if (!/Sala com alavanca/.test(x.mons)) fails.push(`${BOSS_LEVER}: sem «Sala com alavanca»`); if (!x.cv || !/zona aproximada/.test(x.map)) fails.push(`${BOSS_LEVER}: mapa sem o ponto ou sem «zona aproximada»`);
    if (!/best set do nível 570/.test(x.note)) fails.push(`${BOSS_LEVER}: nota do sorcerer: ${x.note}`); });
  await one(BOSS_RAID, x => { if (!/Aparece em raids/.test(x.mons)) fails.push(`${BOSS_RAID}: sem «Aparece em raids»`); if (!x.cv) fails.push(`${BOSS_RAID}: sem mapa`); });
  await one(BOSS_NOPOS, x => { if (x.cv || !/Posição por confirmar/.test(x.map)) fails.push(`${BOSS_NOPOS}: sem «Posição por confirmar»`); });
  // o knight com o set «Proteção»: a nota diz o nome do set
  await p.evaluate(() => { const s = JSON.parse(localStorage.getItem('grimorio-tibia-v4')); s.active = 't2'; localStorage.setItem('grimorio-tibia-v4', JSON.stringify(s)); });
  await p.reload(); await p.waitForSelector('.bs-r [data-boss]', { timeout: 60000 }); await crdWait(p);
  await openBoss(p, BOSS_LEVER);
  const kn = await p.evaluate(() => (document.querySelector('#sheetBody [data-fxs="dif"] .fx-pl') || {}).textContent || '');
  if (!/Proteção/.test(kn)) fails.push('boss com o knight: nota sem o nome do set: ' + kn);
  await closeSheet(p);
  // as proteções contam: o mesmo knight com o set «Proteção» e com o best set do nível
  const lm = await lvOf(p, BOSS_PROT);
  await p.evaluate(() => { const s = JSON.parse(localStorage.getItem('grimorio-tibia-v4')); s.chars.find(c => c.id === 't2').hset = 'bis'; localStorage.setItem('grimorio-tibia-v4', JSON.stringify(s)); });
  await p.reload(); await p.waitForSelector('.bs-r [data-boss]', { timeout: 60000 }); await crdWait(p);
  const lb = await lvOf(p, BOSS_PROT);
  console.log(`  ${BOSS_PROT}, knight 812: set «Proteção» «${lm}», best set «${lb}»`);
  if (!lm || lm === lb) fails.push(`${BOSS_PROT}: o set «Proteção» e o best set dão o mesmo nível (${lm})`);
  await p.evaluate(() => { const s = JSON.parse(localStorage.getItem('grimorio-tibia-v4')); s.active = 't1'; s.chars.find(c => c.id === 't2').hset = 'mine'; localStorage.setItem('grimorio-tibia-v4', JSON.stringify(s)); });
}

const sleep = ms => new Promise(r => setTimeout(r, ms));
async function waitSheet(p) {
  await p.waitForSelector('#sheet.on #sheetBody', { timeout: 10000 });
  await p.waitForSelector('#sheet.on #sheetBody .fx [data-cam] .cam, #sheet.on #sheetBody .fx [data-camretry]', { timeout: 20000 }).catch(() => {});
  await p.waitForFunction(() => !document.querySelector('#sheet.on [data-fxloot] .fx-lwait'), null, { timeout: 15000 }).catch(() => {});
  await sleep(300);
}
async function closeSheet(p) {
  await p.evaluate(() => { const x = document.querySelector('#sheetX'); if (x && document.querySelector('#sheet.on')) x.click(); });
  await p.waitForFunction(() => !document.querySelector('#sheet.on'), null, { timeout: 5000 }).catch(() => {});
  await sleep(300);
}
// abre a ficha de uma hunt como a pesquisa geral (data-gs="h:<pid>")
async function openPid(p, pid) {
  await p.evaluate(pid => { const x = document.createElement('button'); x.dataset.gs = 'h:' + pid; document.body.appendChild(x); x.click(); x.remove(); }, pid);
  await waitSheet(p);
}
async function setState(p, f) {
  await p.evaluate(f => { const s = JSON.parse(localStorage.getItem('grimorio-tibia-v4')); new Function('s', f)(s); localStorage.setItem('grimorio-tibia-v4', JSON.stringify(s)); }, f);
  await p.reload();
  await p.waitForFunction(() => [...document.querySelectorAll('[data-pid]')].some(e => e.getClientRects().length && e.getBoundingClientRect().width > 0), null, { timeout: 30000 });
  await sleep(800);
}
const diffOf = p => p.evaluate(async () => {
  for (let i = 0; i < 50 && !document.querySelector('#sheet.on [data-fxs="dif"] [data-fxdok]'); i++) await new Promise(r => setTimeout(r, 100));
  const d = document.querySelector('#sheet.on [data-fxs="dif"]');
  return d ? { n: (/(\d)\/5/.exec(d.textContent) || [])[1], note: (d.querySelector('.fx-pl') || {}).textContent || '', ok: !!d.querySelector('[data-fxdok]') } : null;
});

// passos só em pt-PT: devolve a lista de problemas
async function deep(p, W, fails, MK) {
  const G = await p.evaluate(() => { const g = JSON.parse(document.getElementById('G').textContent); return { hunts: g.hunts, places: Object.fromEntries(Object.entries(g.places).map(([k, v]) => [k, v.n])), items: g.items.map(x => [x.n.toLowerCase(), x.id]) }; });
  const cam = await p.evaluate(() => fetch('data/caminhos.json').then(r => r.json()));
  const rows = G.hunts.sorcerer, has = new Set(rows.map(r => r.c));
  // (a) lucro negativo
  const neg = rows.filter(r => r.lo != null && r.lo < 0 && r.l <= 575 && r.c && rows.filter(x => x.c === r.c).length === 1).pop();
  if (neg) { await openPid(p, neg.c); if (!(await p.evaluate(() => !!document.querySelector('#sheetBody [data-fxs="lo"] .warnt')))) fails.push(`lucro negativo de ${neg.c} sem .warnt`); await closeSheet(p); }
  else console.log('  (sem hunt de lucro negativo: salta)');
  // (b) mapa do troço: a 1.ª hunt do sorcerer com um passo com ponto
  const pin = rows.map(r => r.c).find(c => c && cam.h[c] && (cam.h[c].legs || []).some(l => (l.steps || []).some(s => s.c)));
  await openPid(p, pin);
  await p.click('#sheetBody .cam-pin');
  await p.waitForFunction(() => { const d = document.querySelector('#sheetBody details.cam-map[open]'), cv = d && d.querySelector('canvas'); if (!cv || !cv.width) return false;
    const g = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data; for (let i = 0; i < g.length; i += 4) if (g[i] || g[i + 1] || g[i + 2]) return true; return false; }, null, { timeout: 10000 })
    .catch(() => fails.push(`o mapa do troço de ${pin} ficou preto ou fechado`));
  await closeSheet(p);
  // (c) hunt por documentar (a 1.ª nos cartões)
  const none = await p.evaluate(h => [...document.querySelectorAll('[data-hunt][data-pid]')].filter(b => b.getClientRects().length).map(b => b.dataset.pid).find(k => h[k] && h[k].st === 'none'), cam.h);
  if (none) { await p.locator(`[data-hunt][data-pid="${none}"]:visible`).first().click(); await waitSheet(p);
    const r = await p.evaluate(() => ({ t: document.querySelector('#sheetBody .fx-cam').textContent, map: !!document.querySelector('#sheetBody .fx-map .hmap') }));
    if (!/por documentar/.test(r.t)) fails.push(`${none}: sem «por documentar»`); if (!r.map) fails.push(`${none}: sem o mapa da zona`);
    const s = await p.evaluate(fxCheck, W); if (s.length) fails.push(`${none}: ${s.join('; ')}`); await closeSheet(p); }
  else fails.push('nenhum cartão com caminho «none»');
  // (d) hunt de outra vocação, aberta pela pesquisa geral: mesma estrutura e XP estimado
  const oth = ['knight', 'paladin', 'druid', 'monk'].flatMap(v => G.hunts[v]).find(r => r.c && !has.has(r.c) && r.xp != null && !r.o && !r.f && !r.w && r.l <= 570);
  await p.evaluate(() => document.querySelector('#gsBtn').click());
  await p.waitForSelector('#gsQ', { timeout: 5000 });
  await p.fill('#gsQ', G.places[oth.c]);
  await p.waitForSelector(`#gsList [data-gs="h:${oth.c}"]`, { timeout: 10000 });
  await p.click(`#gsList [data-gs="h:${oth.c}"]`);
  await waitSheet(p);
  { const s = await p.evaluate(fxCheck, W); if (s.length) fails.push(`${oth.c} (pesquisa): ${s.join('; ')}`);
    const e = await p.evaluate(() => { const x = document.querySelector('#sheetBody [data-fxs="xp"]'), t = x && x.querySelector('[title]'); return { txt: x ? x.textContent : '', title: t ? t.title : '' }; });
    if (!/≈/.test(e.txt) || !e.title) fails.push(`${oth.c}: XP/h sem «≈» ou sem a origem no title (${e.txt})`); }
  await closeSheet(p);
  // (e) dificuldade: sorcerer sem set, knight com o set «Proteção», e o knight com o best set
  await openPid(p, DIFF_PID); const ds = await diffOf(p); await closeSheet(p);
  await setState(p, 's.active="t2";');
  await openPid(p, DIFF_PID); const dk = await diffOf(p); await closeSheet(p);
  await setState(p, 's.chars.find(c=>c.id==="t2").hset="bis";');
  await openPid(p, DIFF_PID); const db = await diffOf(p); await closeSheet(p);
  await setState(p, 's.active="t1"; s.chars.find(c=>c.id==="t2").hset="mine";');
  console.log(`  dificuldade em ${DIFF_PID}: sorcerer ${ds && ds.n} («${ds && ds.note}»), knight com set ${dk && dk.n} («${dk && dk.note}»), knight best set ${db && db.n}`);
  if (!ds || !dk || !db || !ds.ok || !dk.ok || !db.ok) fails.push('dificuldade sem o dano das criaturas');
  else { if (ds.n === dk.n) fails.push(`sorcerer e knight com a mesma dificuldade em ${DIFF_PID}`);
    if (!/best set/.test(ds.note)) fails.push('nota do sorcerer sem «best set»: ' + ds.note);
    if (!/Proteção/.test(dk.note)) fails.push('nota do knight sem o nome do set: ' + dk.note);
    if (!/best set/.test(db.note)) fails.push('nota do knight com hset "bis" sem «best set»: ' + db.note); }
  // (f) comparar hunts: a coluna da dificuldade mostra o mesmo N/5 da ficha
  const two = rows.filter(r => r.c && r.l <= 575 && r.l >= 400).map(r => r.c).filter((c, i, a) => a.indexOf(c) === i).slice(0, 2);
  const nf = {};
  for (const c of two) { await openPid(p, c); nf[c] = (await diffOf(p) || {}).n; await p.click('#sheetBody [data-hcmp]'); await closeSheet(p); }
  await p.click('[data-hcmpopen]');
  await p.waitForSelector('#sheet.on table.hcmp', { timeout: 10000 }); await sleep(800);
  const cmp = await p.evaluate(() => { const tr = [...document.querySelectorAll('#sheetBody table.hcmp tbody tr')].find(r => /Dificuldade/.test(r.querySelector('th').textContent));
    return tr ? [...tr.querySelectorAll('td')].map(td => (/(\d)\/5/.exec(td.textContent) || [])[1]) : null; });
  if (!cmp) fails.push('comparar hunts sem a linha «Dificuldade»');
  else if (cmp.join() !== two.map(c => nf[c]).join()) fails.push(`comparar: ${cmp.join()} ≠ fichas ${two.map(c => nf[c]).join()}`);
  await closeSheet(p);
  await p.evaluate(() => { const b = document.querySelector('[data-hcmpclr]'); if (b) b.click(); });
  // (h) hunt abaixo do nível da medição (druid 300 na Issavi Sewers, medida no nível 600): o cartão e a ficha dizem-no no lugar dos números
  await setState(p, 's.active="t4"; s.ui.band=11;');
  { const card = await p.evaluate(() => { const b = document.querySelector('[data-hunt][data-pid="issavisewers"] .hc-n'); return b ? b.textContent : null; });
    if (!card || !/abaixo do nível da medição/.test(card)) fails.push('cartão abaixo do nível sem a frase: ' + card);
    await openPid(p, 'issavisewers');
    const t = await p.evaluate(() => ['xp', 'lo'].map(k => (document.querySelector(`#sheetBody [data-fxs="${k}"]`) || {}).textContent || ''));
    if (!t.every(x => /abaixo do nível da medição/.test(x))) fails.push('ficha abaixo do nível: ' + t.join(' | '));
    await closeSheet(p); }
  await setState(p, 's.active="t1"; s.ui.band=null;');
  // (g) preços do Market (só a 1440): 503 → NPC; resposta fixa → «Market» e o valor; sem mundo → escolher o mundo
  if (W > 800) {
    const first = await p.evaluate(() => [...document.querySelectorAll('[data-hunt][data-pid]')].find(b => b.getClientRects().length).dataset.pid);
    MK.mode = 503;
    await openPid(p, first);
    const a = await p.evaluate(() => ({ note: (document.querySelector('#sheetBody .fx-lnote') || {}).textContent || '', src: [...document.querySelectorAll('#sheetBody .fx-lsrc')].map(x => x.textContent), n: (document.querySelector('#sheetBody .fx-lt li') || { dataset: {} }).dataset.fxln }));
    if (!/o Market não respondeu/.test(a.note)) fails.push('Market 503 sem «o Market não respondeu»: ' + a.note);
    if (a.src.some(s => s === 'Market')) fails.push('Market 503 e ainda assim preço do Market');
    await closeSheet(p);
    if (!a.n) fails.push('loot sem itens');
    else {
      const items = await p.evaluate(() => fetch('data/items.json').then(r => r.json()));
      const ids = [...new Set([...G.items.filter(x => x[0] === a.n).map(x => String(x[1])), ...((items[a.n] || {}).ids || []).map(String)])];
      MK.mode = 'ok'; MK.json = { world: 'Bona', updated: Math.floor(Date.now() / 1000) - 3600, fetched: Math.floor(Date.now() / 1000), stale: false, items: Object.fromEntries(ids.map(id => [id, [9900000, 0, 9876543, 0, 0, 0, 50, 0]])) };
      await setState(p, '');
      await openPid(p, first);
      const b = await p.evaluate(n => { const li = [...document.querySelectorAll('#sheetBody .fx-lt li')].find(x => x.dataset.fxln === n);
        return { note: (document.querySelector('#sheetBody .fx-lnote') || {}).textContent || '', src: li ? li.querySelector('.fx-lsrc').textContent : '', v: li ? li.querySelector('.fx-lv b').textContent.replace(/\D/g, '') : '' }; }, a.n);
      if (b.src !== 'Market' || !/^9[6-8]\d{5}$/.test(b.v)) fails.push(`Market: ${a.n} com «${b.src}» ${b.v}`); // 9 876 543 menos a taxa do Market
      if (!/Bona/.test(b.note)) fails.push('nota do Market sem o mundo: ' + b.note);
      await closeSheet(p);
    }
    await setState(p, 's.chars.find(c=>c.id==="t1").world="";');
    await openPid(p, first);
    const c = await p.evaluate(() => (document.querySelector('#sheetBody .fx-lnote') || {}).textContent || '');
    if (!/Escolhe o mundo/.test(c)) fails.push('sem mundo e sem a frase de escolher o mundo: ' + c);
    await closeSheet(p);
    await setState(p, 's.chars.find(c=>c.id==="t1").world="Bona";');
  }
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
    // só o servidor local: AdSense, TibiaData e outros ficam de fora; o Market responde o que o teste quiser (503 por omissão)
    const MK = { mode: 503, json: null };
    await ctx.route('**/*', r => new URL(r.request().url()).host === HOST ? r.continue() : r.abort());
    await ctx.route('**/api/market.php*', r => MK.mode === 'ok' ? r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MK.json) }) : r.fulfill({ status: 503, body: '' }));
    const p = await ctx.newPage(), errs = [], fails = [];
    p.on('pageerror', e => errs.push('pageerror: ' + String(e).slice(0, 200)));
    p.on('console', m => {
      if (m.type() !== 'error') return;
      const u = (m.location() && m.location().url) || '', t = m.text();
      if (u && new URL(u, URL0).host !== HOST) return;                                 // pedidos de fora, abortados de propósito
      if (/Failed to load resource/.test(t) && (/api\/stats\.php/.test(u) || /501/.test(t))) return; // o http.server não aceita o POST das estatísticas
      if (/Failed to load resource/.test(t) && /api\/market\.php/.test(u) && /503/.test(t)) return;  // o Market em baixo, de propósito
      if (/net::ERR_FAILED/.test(t)) return;
      errs.push('console: ' + t.slice(0, 200) + (u ? ' ' + u : ''));
    });
    await p.goto(URL0 + '#hunts');
    await p.waitForFunction(() => [...document.querySelectorAll('[data-pid]')].some(e => e.getClientRects().length && e.getBoundingClientRect().width > 0), null, { timeout: 30000 });
    await p.waitForTimeout(1200);
    await p.evaluate(W => { window.__W = W; }, W);
    const r = Object.assign({ errs }, await p.evaluate(audit));
    // Task 4: os cartões dizem a dificuldade da personagem («dificuldade N/5», a mesma do diffFor)
    const nd = await p.evaluate(() => [...document.querySelectorAll('[data-hunt][data-pid]')].filter(b => b.getClientRects().length && !/\d\/5/.test((b.querySelector('[data-fxd]') || {}).textContent || '')).length);
    if (nd) fails.push(`${nd} cartões sem a dificuldade N/5`);
    // Task 4: a ficha da 1.ª hunt
    try {
      await p.locator('[data-hunt][data-pid]:visible').first().click();
      await waitSheet(p);
      fails.push(...await p.evaluate(fxCheck, W));
      const a = await p.evaluate(audit); r.hscroll = r.hscroll || a.hscroll; r.small.push(...a.small); r.tiny.push(...a.tiny);
      if (lang !== 'pt-PT') { const pt = await p.evaluate(ptLeft, PT35); if (pt.length) fails.push('hunt com pt-PT: ' + pt.join(' | ')); }
      await closeSheet(p);
      if (lang !== 'pt-PT') { await openPid(p, 'forgottencrypt'); const pt = await p.evaluate(ptLeft, PT35); if (pt.length) fails.push('forgottencrypt com pt-PT: ' + pt.join(' | ')); await closeSheet(p); }
      if (lang === 'pt-PT') await deep(p, W, fails, MK);
      await bosses(p, W, lang, r, fails);
    } catch (e) { fails.push('erro: ' + String(e).split('\n')[0].slice(0, 200)); }
    r.fails = fails;
    const ok = !r.errs.length && !r.hscroll && !r.small.length && !r.tiny.length && !fails.length;
    if (!ok) bad++;
    console.log(`${lang} ${W}: ${ok ? 'ok' : JSON.stringify(r)}`);
    await ctx.close();
  }
  await b.close();
  process.exit(bad ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
