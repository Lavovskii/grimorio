// Teste de ouro do huntRows (Task 2b do plano das fichas). Corre o huntRows do index.html num node:vm, sem browser.
// Uso: node _dev/huntest_gold.mjs [--save] [--k0] [--nivel]
//   --save   grava _dev/huntest_gold.json = {"voc|L": [[c, xp, lo, l, src], ...]} (5 vocações × L 50, 150, 300, 600, 1000)
//   (nada)   recalcula e compara com o ficheiro: "0 diferenças" ou a lista
//   --k0     sem o ajuste ao nível (levelFactor dá sempre f = 1, ok = true): tem de dar 0 diferenças
//   --nivel  com o ajuste (k = 0,5): só xp/lo mudam, dentro de 0,7–1,25 × o antigo (± 500 do arredondamento ao milhar),
//            e as linhas com pl < 0,6 × Lm ficam sem número
// Chaves "voc|L": huntRows(voc, L, L) com C() = {level: L}. Chaves "voc|La": huntRows(voc) sem L nem pl (o caminho de
// omissão: teto = nível + 5, pl = nível), também com C() = {level: L}.
import fs from "node:fs";
import { huntVm, Fichas as F } from "./hunt_vm.mjs";
const arg = k => process.argv.includes("--" + k);
const OUT = new URL("huntest_gold.json", import.meta.url);
const GF = arg("k0") ? { ...F, levelFactor: () => ({ f: 1, ok: true }) } : F;
const ctx = huntVm(GF);

const VOCS = ["knight", "paladin", "sorcerer", "druid", "monk"], LS = [50, 150, 300, 600, 1000];
const run = () => { const o = {}, full = {};
  for (const v of VOCS) for (const L of LS) { ctx.LV = L;
    for (const [k, hs, pl] of [[`${v}|${L}`, ctx.huntRows(v, L, L), L], [`${v}|${L}a`, ctx.huntRows(v), L]]) {
      o[k] = hs.map(h => [h.r.c, h.xp, h.lo, h.l, h.src]); full[k] = hs.map(h => ({ pl, Lm: h.Lm, xp: h.xp, lo: h.lo })); } }
  return { o, full }; };
const { o: now, full } = run();

if (arg("save")) {
  const keys = Object.keys(now).sort();
  fs.writeFileSync(OUT, "{\n" + keys.map(k => JSON.stringify(k) + ": " + JSON.stringify(now[k])).join(",\n") + "\n}\n");
  console.log(`gravado: ${keys.length} chaves, ${keys.reduce((s, k) => s + now[k].length, 0)} linhas`);
  process.exit(0);
}
const gold = JSON.parse(fs.readFileSync(OUT, "utf8"));
const diffs = [], bad = [], ch = [];
for (const k of Object.keys(gold).sort()) {
  const a = gold[k], b = now[k] || [];
  if (a.length !== b.length) { diffs.push(`${k}: ${a.length} linhas → ${b.length}`); continue; }
  a.forEach((x, i) => { const y = b[i];
    if (JSON.stringify(x) === JSON.stringify(y)) return;
    diffs.push(`${k} ${x[0]}: ${JSON.stringify(x.slice(1))} → ${JSON.stringify(y.slice(1))}`);
    if (!arg("nivel")) return;
    const f = full[k][i];
    if (x[0] !== y[0] || x[3] !== y[3] || x[4] !== y[4]) bad.push(`${k} ${x[0]}: muda mais do que xp/lo`);
    for (const j of [1, 2]) { if (x[j] === y[j] || y[j] === null) continue;
      const lo = Math.min(0.7 * x[j], 1.25 * x[j]) - 500, hi = Math.max(0.7 * x[j], 1.25 * x[j]) + 500;
      if (x[j] === null || y[j] < lo || y[j] > hi) bad.push(`${k} ${x[0]}: ${j === 1 ? "xp" : "lo"} ${x[j]} → ${y[j]} fora de 0,7–1,25`);
      if (j === 1) ch.push([k, x[0], x[1], y[1]]); }
    if (y[1] === null && x[1] !== null && !(f.Lm != null && f.pl < 0.6 * f.Lm)) bad.push(`${k} ${x[0]}: perdeu o número sem estar abaixo do nível da medição`);
  });
}
if (arg("nivel")) for (const k of Object.keys(full)) full[k].forEach((f, i) => {
  if (f.Lm != null && f.pl < 0.6 * f.Lm && (f.xp !== null || f.lo !== null)) bad.push(`${k} ${now[k][i][0]}: pl ${f.pl} < 0,6 × ${f.Lm} e tem número`); });
if (!arg("nivel")) { console.log(diffs.length ? diffs.slice(0, 40).join("\n") + `\n${diffs.length} diferenças` : "0 diferenças"); process.exit(diffs.length ? 1 : 0); }
console.log(`${diffs.length} linhas mudaram: ${ch.length} com o XP ajustado, ${diffs.filter(d => /→ \[null,null/.test(d)).length} sem número (abaixo do nível da medição)`);
console.log("10 maiores mudanças de XP:\n" + ch.sort((p, q) => Math.abs(q[3] - q[2]) - Math.abs(p[3] - p[2])).slice(0, 10)
  .map(([k, c, a, b]) => `  ${k} ${c}: ${a} → ${b} (×${(b / a).toFixed(2)})`).join("\n"));
console.log(bad.length ? bad.slice(0, 40).join("\n") + `\n${bad.length} falhas` : "nível: ok");
process.exit(bad.length ? 1 : 0);
