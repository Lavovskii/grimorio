// Teste do motor de rotações (shared/rotacoes.js + data/rotacoes.json). Uso, na raiz do clone: node _dev/rotacoes_test.mjs
// Corre todas as vocações × cenários × orçamentos × níveis e verifica as regras; sai com 1 se alguma falhar.
import { createRequire } from "module";
import { fileURLToPath } from "url";
import path from "path";
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const R = require(path.join(ROOT, "shared/rotacoes.js"));
const D = require(path.join(ROOT, "data/rotacoes.json"));

const LV = [8, 20, 35, 50, 80, 100, 150, 200, 250, 300, 400, 550, 800, 1100, 1500];
const SC = ["boss", "caixa", "espalhados", "party"], BU = ["max", "eco"];
const BOSS_SKIP = new Set(["Forked Glacier", "Forked Thorns"]);
let fails = 0, plans = 0, gapMin = 9, gapMax = 0, gapSum = 0, t0 = Date.now();
const fail = (m) => { fails++; if (fails <= 40) console.log("FALHA:", m); };

// 1) simplex: um problema com solução conhecida (max 3x + 2y; x + y ≤ 4; x + 3y ≤ 6; x ≤ 3 → z = 11)
const sx = R._simplex([3, 2], [[1, 1], [1, 3], [1, 0]], [4, 6, 3]);
if (!sx || Math.abs(sx.z - 11) > 1e-9) fail("simplex: z = " + (sx && sx.z) + " (esperado 11)");

for (const voc of R.VOCS) {
  const lanesEl = R.LANES[voc].map((l) => l.el);
  for (const scen of SC) for (const budget of BU) {
    let prev = null;
    for (const L of LV) {
      const id = `${voc} ${L} ${scen} ${budget}`;
      let P;
      try { P = R.plan(D, { voc, level: L, scen, budget }); } catch (e) { fail(id + ": exceção " + e.message); continue; }
      plans++;
      if (P.empty) { if (L >= 8) fail(id + ": sem rotação"); continue; }
      if (!P.rotation.length) fail(id + ": rotação vazia");
      for (const r of P.rotation) {
        const a = D.ab[r.n] || D.runes[r.n];
        if (!a) { fail(id + ": " + r.n + " não existe nos dados"); continue; }
        if (a.l > L) fail(id + ": " + r.n + " é do nível " + a.l);
        if (a.v.indexOf(voc) < 0) fail(id + ": " + r.n + " não é desta vocação");
        if (a.dot) fail(id + ": DoT na rotação (" + r.n + ")");
        if (scen === "boss" && BOSS_SKIP.has(r.n)) fail(id + ": Forked no boss");
        if (a.wheel && P.stats.wheel < 1) fail(id + ": feitiço da Wheel sem estágio");
        // uma linha de elemento: feitiços próprios de outra linha só convertidos (sorcerer)
        if (D.ab[r.n] && a.el !== P.lane.el && lanesEl.includes(a.el) && !/^.*sai em /.test(r.why)) fail(id + ": " + r.n + " (" + a.el + ") fora da linha " + P.lane.el);
      }
      if (budget === "eco" && P.econ.gpH > P.econ.cap * 1.05) fail(id + `: ${P.econ.gpH} gp/h acima do limite ${P.econ.cap}`);
      const g = P.econ.dpsSeq / Math.max(1, P.econ.dps);
      gapMin = Math.min(gapMin, g); gapMax = Math.max(gapMax, g); gapSum += g;
      if (g < 0.75 || g > 1.06) fail(id + `: sequência ${P.econ.dpsSeq} longe do ótimo ${P.econ.dps}`);
      if (budget === "max" && prev && P.econ.dps < prev * 0.95) fail(id + `: o dano desce com o nível (${prev} → ${P.econ.dps})`);
      prev = P.econ.dps;
      const hk = R.toHK(P), rt = R.toRot(P);
      if (!hk.length || !hk[hk.length - 1].k.length || !rt.seq.length) fail(id + ": toHK/toRot vazios");
    }
  }
}
const ms = (Date.now() - t0) / plans;
console.log(`${plans} planos, ${ms.toFixed(1)} ms por plano; sequência/ótimo: mín ${gapMin.toFixed(2)}, máx ${gapMax.toFixed(2)}, média ${(gapSum / plans).toFixed(2)}`);
console.log(fails ? `${fails} falhas` : "tudo certo");
process.exit(fails ? 1 : 0);
