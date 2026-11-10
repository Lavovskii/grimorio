// Ponte do _dev/calibrar.py para o motor das hunts (o huntEst não se duplica em Python). Lê JSON do stdin:
//   {k, q: [{pid, voc, pl, noha}]}  → k = o k do ajuste ao nível; pl = nível do jogador (teto da variante = pl + 5, como o huntRows);
//   noha = conta sem as sessões reais dessa vocação nessa hunt (G.ha), para comparar a estimativa com elas.
// Escreve {k, avg: {pid: [XP, vida]} (avgMon de todas as hunts), r: [{xp, lo, src, Lm, below} | null]} (o huntEst + estAdj, como o site).
import vm from "node:vm";
import { huntVm } from "./hunt_vm.mjs";
const inp = JSON.parse(await new Promise(r => { let s = ""; process.stdin.setEncoding("utf8"); process.stdin.on("data", d => s += d); process.stdin.on("end", () => r(s)); }));
const ctx = huntVm(), G = ctx.G;
ctx.KIN = inp.k;
vm.runInContext(`CALIB = GrimFicha.calibOf({v: 1, k: KIN});
  var calibOne = q => { const e = GrimFicha.huntEst({G, voc: q.voc, pid: q.pid, L: q.pl + 5, pl: q.pl, compatFor, avgMon});
    if (!e) return null; const a = estAdj(e, q.pl); return {xp: a.xp, lo: a.lo, src: e.src, Lm: e.Lm, below: a.below}; };`, ctx);
const run = q => {
  const save = ctx.hasKey(G.ha, q.pid) ? G.ha[q.pid] : null;
  if (q.noha && save) { const v = { ...save.v }; delete v[q.voc]; G.ha[q.pid] = { ...save, v }; }
  try { ctx.LV = q.pl; return ctx.calibOne(q); } finally { if (save) G.ha[q.pid] = save; }
};
const avg = {}; Object.keys(G.places).forEach(p => { avg[p] = ctx.avgMon(p); });
process.stdout.write(JSON.stringify({ k: vm.runInContext("CALIB.k", ctx), avg, r: (inp.q || []).map(run) }));
