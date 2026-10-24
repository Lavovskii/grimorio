// Teste do motor dos bosses (shared/bosses.js) com data/bosses.json, data/creatures.json e o dano do motor de rotações:
// todas as vocações em vários níveis, sem exceções; 'sozinho' nunca abaixo do nível da quest; quem pode a um nível continua a poder
// acima; os pontos e o bónus do Bosstiary batem com a Cyclopedia da TibiaWiki. Uso: node _dev/bosses_test.mjs
import { createRequire } from "module";
import { readFileSync } from "fs";
const require = createRequire(import.meta.url);
const R = require("../shared/rotacoes.js"), B = require("../shared/bosses.js");
const J = f => JSON.parse(readFileSync(new URL("../data/" + f, import.meta.url), "utf8"));
const D = J("rotacoes.json"), BD = J("bosses.json"), CR = J("creatures.json");
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
// Bosstiary (Cyclopedia): 25% a 0 pontos, +1% a cada 10 até 250 (50%), +1% a cada 20 até 1250 (100%), depois 25, 30, 35… pontos por 1%
[[0, 25], [10, 26], [249, 49], [250, 50], [270, 51], [1249, 99], [1250, 100], [1274, 100], [1275, 101], [1305, 102]].forEach(([p, v]) => {
  if (B.lootBonus(p) !== v) fail(`bónus com ${p} pontos: ${B.lootBonus(p)} (esperava ${v})`); });
if (B.pointsOf(BD.pts, "b", 3) !== 50 || B.pointsOf(BD.pts, "a", 3) !== 100 || B.pointsOf(BD.pts, "n", 2) !== 40) fail("pontos por estágio");
if (B.stageOf(BD.pts, "b", 99) !== 1 || B.stageOf(BD.pts, "a", 20) !== 2 || B.stageOf(BD.pts, "n", 5) !== 3) fail("estágio pelas mortes");
console.log(`${n} avaliações (${Object.keys(BD.b).length} bosses × 5 vocações × 7 níveis)`);
console.log(fails ? `${fails} falhas` : "tudo certo");
process.exit(fails ? 1 : 0);
