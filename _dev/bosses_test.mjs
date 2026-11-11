// Teste do motor dos bosses (shared/bosses.js) com data/bosses.json, data/creatures.json e o dano do motor de rotações:
// todas as vocações em vários níveis, sem exceções; 'sozinho' nunca abaixo do nível da quest; quem pode a um nível continua a poder
// acima; os pontos e o bónus do Bosstiary batem com a Cyclopedia da TibiaWiki. Uso: node _dev/bosses_test.mjs
import { createRequire } from "module";
import { readFileSync } from "fs";
const require = createRequire(import.meta.url);
const R = require("../shared/rotacoes.js"), B = require("../shared/bosses.js");
const J = f => JSON.parse(readFileSync(new URL("../data/" + f, import.meta.url), "utf8"));
const D = J("rotacoes.json"), BD = J("bosses.json"), CR = J("creatures.json"), CD = J("crdmg.json");
let fails = 0, n = 0; const fail = m => { fails++; if (fails <= 30) console.log("FALHA:", m); };
const ORD = { locked: 0, later: 1, unknown: 2, team: 2, solo: 3 };
for (const voc of R.VOCS) {
  const curve = B.makeCurve(l => { const p = R.plan(D, { voc, level: l, scen: "boss" }); return p.empty ? 1 : p.econ.dps + (p.econ.autoDps || 0); });
  const mlAt = l => R.stats(voc, l).mlBase;
  for (const [k, b] of Object.entries(BD.b)) {
    let prev = null;
    for (const L of [20, 80, 150, 300, 600, 1000, 1500]) {
      let r; try { r = B.judge(b, { k, voc, level: L, cr: CR[k], curve, mlAt }); n++; } catch (e) { fail(`${voc} ${L} ${b.n}: ${e.message}`); continue; }
      if (!(r.st in ORD)) fail(`${voc} ${L} ${b.n}: estado ${r.st}`);
      if (r.st === "solo" && b.ql && L < b.ql) fail(`${voc} ${L} ${b.n}: sozinho abaixo do nível da quest ${b.ql}`);
      if (r.soloL != null && b.qr && r.soloL < b.qr) fail(`${voc} ${b.n}: sozinho a ${r.soloL}, abaixo do recomendado ${b.qr}`);
      if (r.st === "solo" && !b.hp && !(CR[k] || {}).hp) fail(`${voc} ${L} ${b.n}: sozinho sem vida conhecida`);
      if (prev && ORD[r.st] < ORD[prev.st] && !(prev.st === "unknown" && r.st === "team")) fail(`${voc} ${b.n}: ${prev.st} a ${prev.L} e ${r.st} a ${L}`);
      prev = { st: r.st, L };
    }
  }
}
// proteções da personagem (ronda 3, Q7): com b.dm (% do dano por elemento) o md passa a ser o golpe efetivo; sem opt.prot, igual
{ const voc = "knight", curve = B.makeCurve(l => { const p = R.plan(D, { voc, level: l, scen: "boss" }); return p.empty ? 1 : p.econ.dps + (p.econ.autoDps || 0); });
  const mlAt = l => R.stats(voc, l).mlBase, t = { n: "Teste", c: "b", hp: 20000, md: 3000, dm: { fire: 100 } }, o = { k: "t", voc, level: 300, cr: {}, curve, mlAt };
  const a = B.judge(t, o), p = B.judge(t, Object.assign({ prot: { fire: 50 } }, o)), e = B.judge(t, Object.assign({ prot: { ice: 50 } }, o));
  if (!(p.soloL < a.soloL) || p.md !== 1500) fail(`proteção de fogo 50%: sozinho a ${p.soloL} (sem ${a.soloL}), md ${p.md}`);
  if (JSON.stringify(e) !== JSON.stringify(a)) fail("proteção de outro elemento mudou o resultado");
  let same = 0, diff = 0;
  for (const [k, b] of Object.entries(BD.b)) for (const L of [150, 600]) {
    const x = B.judge(b, { k, voc, level: L, cr: CR[k], curve, mlAt }), y = B.judge(b, { k, voc, level: L, cr: CR[k], curve, mlAt, prot: {} });
    const z = B.judge(b, { k, voc, level: L, cr: CR[k], curve, mlAt, prot: { physical: 40, fire: 40, ice: 40, earth: 40, energy: 40, holy: 40, death: 40 } });
    if (JSON.stringify(x) !== JSON.stringify(y)) fail(`${b.n}: prot vazio mudou o resultado`);
    if (!b.dm && JSON.stringify(x) !== JSON.stringify(z)) fail(`${b.n}: sem dm e a proteção mudou o resultado`);
    if (JSON.stringify(x) === JSON.stringify(z)) same++; else diff++;
  }
  console.log(`proteções de 40% só com o b.dm (knight 150 e 600): ${diff} avaliações mudam, ${same} iguais`);
  // com o dano por elemento do crdmg.json (como o site): sem prot igual; knight 600 com 40% em tudo muda muitos bosses
  const P40 = { physical: 40, fire: 40, ice: 40, earth: 40, energy: 40, holy: 40, death: 40 };
  let ch = 0; const chn = [];
  for (const [k, b] of Object.entries(BD.b)) {
    const o = { k, voc, level: 600, cr: CR[k], curve, mlAt, d: (CD[k] || {}).d };
    const x = B.judge(b, o), y = B.judge(b, Object.assign({ prot: P40 }, o)), w = B.judge(b, { k, voc, level: 600, cr: CR[k], curve, mlAt });
    if (JSON.stringify(x) !== JSON.stringify(w)) fail(`${b.n}: o dano por elemento sem prot mudou o resultado`);
    if (y.md > x.md) fail(`${b.n}: a proteção subiu o golpe`);
    const z = B.judge(b, Object.assign({ prot: { physical: 100, fire: 100, ice: 100, earth: 100, energy: 100, holy: 100, death: 100 } }, o));
    if (b.md && !(z.md >= 1)) fail(`${b.n}: com 100% de proteção o golpe passou a «desconhecido»`);
    if (b.md && z.soloL != null && x.soloL != null && z.soloL > x.soloL) fail(`${b.n}: mais proteção e sozinho mais tarde (${x.soloL} → ${z.soloL})`);
    if (x.st !== y.st || x.soloL !== y.soloL) { ch++; if (chn.length < 5) chn.push(`${b.n} ${x.st}/${x.soloL}→${y.st}/${y.soloL}`); }
  }
  if (ch <= 50) fail(`só ${ch} bosses mudam com 40% de proteção (knight 600, crdmg.json)`);
  console.log(`crdmg.json, knight 600 com 40% em tudo: ${ch} de ${Object.keys(BD.b).length} bosses mudam o estado ou o nível sozinho (ex.: ${chn.join("; ")})`); }
// Bosstiary (Cyclopedia): 25% a 0 pontos, +1% a cada 10 até 250 (50%), +1% a cada 20 até 1250 (100%), depois 25, 30, 35… pontos por 1%
[[0, 25], [10, 26], [249, 49], [250, 50], [270, 51], [1249, 99], [1250, 100], [1274, 100], [1275, 101], [1305, 102]].forEach(([p, v]) => {
  if (B.lootBonus(p) !== v) fail(`bónus com ${p} pontos: ${B.lootBonus(p)} (esperava ${v})`); });
if (B.pointsOf(BD.pts, "b", 3) !== 50 || B.pointsOf(BD.pts, "a", 3) !== 100 || B.pointsOf(BD.pts, "n", 2) !== 40) fail("pontos por estágio");
if (B.stageOf(BD.pts, "b", 99) !== 1 || B.stageOf(BD.pts, "a", 20) !== 2 || B.stageOf(BD.pts, "n", 5) !== 3) fail("estágio pelas mortes");
// r36 bosses do dia: campo ev (TibiaWiki + _dev/bosses_eventos.json) e as funções puras do bloco «Bosses do dia»
{ const ev = { groam: "wc", furyosa: "wc", horestis: "wc", "the mutated pumpkin": "saz", zorvorax: "saz", ferumbras: "raid", barbaria: "raid",
    abyssador: undefined, "count vlarkorth": undefined, lloyd: undefined };
  for (const [k, e] of Object.entries(ev)) { if (!BD.b[k]) fail(`ev: falta o boss ${k}`); else if (BD.b[k].ev !== e) fail(`ev de ${k}: ${BD.b[k].ev} (esperava ${e})`); }
  for (const [k, b] of Object.entries(BD.b)) if (b.ev != null && !["wc", "saz", "raid"].includes(b.ev)) fail(`ev de ${k}: ${b.ev}`);
  if (typeof B.isEvent !== "function" || typeof B.cdLeft !== "function" || typeof B.dailyPicks !== "function") fail("faltam isEvent, cdLeft ou dailyPicks");
  else {
    if (B.isEvent(BD.b.groam) !== true || B.isEvent(BD.b.abyssador) !== false || B.isEvent(null) !== false) fail("isEvent");
    const H = 3600e3, T = Date.UTC(2026, 10, 11, 12, 0);
    [[T - H, 20, T, 19 * H], [T - 21 * H, 20, T, 0], [null, 20, T, 0], [undefined, null, T, 0],
     // sem cooldown: volta no server save seguinte (10:00 de Berlim; CET em novembro, CEST em julho)
     [Date.UTC(2026, 10, 11, 8, 0), null, Date.UTC(2026, 10, 11, 8, 30), 30 * 60e3],
     [Date.UTC(2026, 10, 11, 9, 30), null, Date.UTC(2026, 10, 11, 10, 0), 23 * H],
     [Date.UTC(2026, 6, 1, 7, 30), null, Date.UTC(2026, 6, 1, 7, 30), 30 * 60e3]].forEach(([ts, cd, now, v]) => {
      const x = B.cdLeft(ts, cd, now); if (x !== v) fail(`cdLeft(${ts}, ${cd}, ${now}) = ${x} (esperava ${v})`); });
    const row = (k, b, st, ttk, v, t) => ({ k, b: Object.assign({ n: k.toUpperCase() }, b), r: { st, ttk }, lo: v == null ? null : { v }, t });
    const rows = [row("a", { xp: 100 }, "solo", 50, 1000), row("b", { xp: 5000 }, "solo", 200, 10), row("c", { xp: 50 }, "solo", 10, 20),
      row("d", { xp: 9999, ev: "raid" }, "solo", 5, 99999), row("e", { xp: 9000 }, "team", 5, 99999),
      row("f", { xp: 8000, cd: 20 }, "solo", 1, 50000, T - H), row("g", { xp: 10 }, "solo", 100, 500)];
    const sig = x => (x.boost ? `${x.boost.k}:${x.boost.why}|` : "") + x.picks.map(([c, r]) => c + "=" + r.k).join(",");
    [["g", "g:null|boost=g,lucro=a,xp=b,rapido=c"], ["d", "d:ev|lucro=a,xp=b,rapido=c"], ["e", "e:st|lucro=a,xp=b,rapido=c"],
     ["f", "f:cd|lucro=a,xp=b,rapido=c"], ["zz", "zz:none|lucro=a,xp=b,rapido=c"], [null, "lucro=a,xp=b,rapido=c"]].forEach(([k, v]) => {
      const x = sig(B.dailyPicks(rows, k, T)); if (x !== v) fail(`dailyPicks(${k}): ${x} (esperava ${v})`); });
    // f fora do cooldown entra; um boss que ganha tudo aparece uma vez só
    const r2 = rows.map(r => r.k === "f" ? Object.assign({}, r, { t: T - 21 * H }) : r);
    if (sig(B.dailyPicks(r2, null, T)) !== "lucro=f,xp=b,rapido=c") fail("dailyPicks com f fora do cooldown: " + sig(B.dailyPicks(r2, null, T)));
    if (sig(B.dailyPicks([row("a", { xp: 1 }, "solo", 1, 1)], "a", T)) !== "a:null|boost=a") fail("dailyPicks repetiu o mesmo boss");
  }
  const c = { wc: 0, saz: 0, raid: 0 }; Object.values(BD.b).forEach(b => { if (b.ev) c[b.ev]++; });
  console.log(`eventos: ${c.wc} wc, ${c.saz} saz, ${c.raid} raid; ${Object.keys(BD.b).length - c.wc - c.saz - c.raid} permanentes`); }
console.log(`${n} avaliações (${Object.keys(BD.b).length} bosses × 5 vocações × 7 níveis)`);
console.log(fails ? `${fails} falhas` : "tudo certo");
process.exit(fails ? 1 : 0);
