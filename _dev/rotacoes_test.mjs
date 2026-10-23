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
        if (D.runes[r.n] && a.el !== P.lane.el && r.n !== "Sudden Death Rune") fail(id + ": runa " + r.n + " (" + a.el + ") fora da linha " + P.lane.el);
      }
      if (budget === "eco" && P.econ.gpH > P.econ.cap * 1.05) fail(id + `: ${P.econ.gpH} gp/h acima do limite ${P.econ.cap}`);
      // com um só feitiço de nível baixo (paladino 20, sem runas do elemento) o dano é 2–3 e o arredondamento manda: não conta
      const g = P.econ.dps < 20 ? 1 : P.econ.dpsSeq / Math.max(1, P.econ.dps);
      gapMin = Math.min(gapMin, g); gapMax = Math.max(gapMax, g); gapSum += g;
      if (g < 0.75 || g > 1.06) fail(id + `: sequência ${P.econ.dpsSeq} longe do ótimo ${P.econ.dps}`);
      if (budget === "max" && prev && P.econ.dps < prev * 0.95) fail(id + `: o dano desce com o nível (${prev} → ${P.econ.dps})`);
      prev = P.econ.dps;
      const hk = R.toHK(P), rt = R.toRot(P);
      if (!hk.length || !hk[hk.length - 1].k.length || !rt.seq.length) fail(id + ": toHK/toRot vazios");
    }
  }
}
// barra recomendada (layout): cada vocação e nível dá uma linha com teclas, sem teclas repetidas
let lays = 0;
for (const voc of R.VOCS) for (let L = 8; L <= 1200; L += 37) {
  const id = `layout ${voc} ${L}`; let X;
  try { X = R.layout(D, { voc, level: L }); lays++; } catch (e) { fail(id + ": exceção " + e.message); continue; }
  if (!X.rows.length || !X.rows[0].keys.length) fail(id + ": sem teclas");
  const seen = new Set();
  for (const k of X.rows.flatMap(r => r.keys).concat(X.common)) { if (seen.has(k.k)) fail(id + ": tecla " + k.k + " repetida"); seen.add(k.k);
    for (const a of k.mab ? k.mab.acts : [k.a]) { const d = D.ab[a.n] || D.runes[a.n]; if (!d || d.l > L) fail(id + ": " + a.n + " fora do nível"); } }
  X.rows.forEach(r => r.keys.forEach(k => (k.mab ? k.mab.acts : [k.a]).forEach(a => { const d = D.ab[a.n] || D.runes[a.n];
    if (d && d.el !== r.el && a.n !== "Sudden Death Rune" && voc !== "sorcerer") fail(id + ": " + a.n + " (" + d.el + ") na linha " + r.el); })));
}
// clientoptions.json sintético → readBars → review: acha o preset pelo nome, lê MAB e runa, e dá as dicas certas
const CO = { hotkeyOptions: { currentHotkeySetName: "Outro", hotkeySets: {
  Outro: { actionBarOptions: { mappings: [] }, chatOff: [] },
  Teste: { actionBarOptions: { mappings: [
    { actionBar: 1, actionButton: 1, actionsetting: { multiActions: [{ chatText: "exori dir san" }, { chatText: "exori dir moe" }, { chatText: "exevo mas san" }] } },
    { actionBar: 1, actionButton: 2, actionsetting: { chatText: "exevo mas san" } },
    { actionBar: 1, actionButton: 3, actionsetting: { useObject: 3191, useType: "UseOnTarget" } },
    { actionBar: 1, actionButton: 4, actionsetting: { useObject: 23373, useType: "UseOnYourself" } },
    { actionBar: 1, actionButton: 5, actionsetting: { useObject: 3420, useType: "Equip" } } ] },
    chatOff: [{ keysequence: "Q", actionsetting: { action: "TriggerActionButton_1.1" } }, { keysequence: "Shift+!", actionsetting: { action: "TriggerActionButton_1.2" } }] } } } };
const B = R.readBars(D, CO, "teste");
if (!B || B.set !== "Teste") fail("readBars: não escolheu o preset pelo nome");
else {
  if (B.user.length !== 4) fail("readBars: " + B.user.length + " ações (esperava 4: o Equip não conta)");
  if (B.user[0].k !== "Q" || B.user[0].acts.length !== 3) fail("readBars: MAB do Q mal lido");
  if (B.user[1].k !== "Shift+1") fail("readBars: Shift+! devia ser Shift+1");
  if (B.user[2].acts[0].item !== "Great Fireball Rune") fail("readBars: runa pelo id do cliente");
  const V = R.review(D, { voc: "paladin", level: 101 }, B.user), txt = V.tips.map(t => t.t + ":" + t.txt).join("\n");
  if (!/^warn:Q: este MAB junta/m.test(txt)) fail("review: não avisou do MAB com holy e físico");
  if (!/Divine Caldera já está no MAB Q/.test(txt)) fail("review: não viu o Caldera repetido");
  if (V.known < 3) fail("review: reconheceu só " + V.known + " feitiços");
}
if (R.readBars(D, { outra: 1 }, "x") !== null) fail("readBars: devia recusar um ficheiro sem hotkeyOptions");
console.log(`${lays} barras recomendadas e o comparador verificados`);
const ms = (Date.now() - t0) / plans;
console.log(`${plans} planos, ${ms.toFixed(1)} ms por plano; sequência/ótimo: mín ${gapMin.toFixed(2)}, máx ${gapMax.toFixed(2)}, média ${(gapSum / plans).toFixed(2)}`);
console.log(fails ? `${fails} falhas` : "tudo certo");
process.exit(fails ? 1 : 0);
