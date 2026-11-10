// Modelo das fichas (shared/fichas.js). Uso: node _dev/fichas_test.mjs
import { createRequire } from "module";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";
const require = createRequire(import.meta.url);
const F = require("../shared/fichas.js");

// vida de referência
assert.equal(F.refHp(8), 185); assert.equal(F.refHp(100), 1105); assert.equal(F.refHp(1), 185);
// golpe efetivo com as proteções do set
assert.equal(F.effHit({ d: { fire: 400, physical: 200 } }, null), 400);
assert.equal(F.effHit({ d: { fire: 400, physical: 200 } }, { fire: 60 }), 200);      // 400 × 0,4 = 160 < 200 físico
assert.equal(F.effHit({ d: {}, m: 300 }, { physical: 10 }), 270);                   // sem d: o m conta como físico
assert.equal(F.effHit({ d: { ice: 100 } }, { ice: 140 }), 0);                       // proteção acima de 100 conta como 100
assert.equal(F.effHit(null, null), null); assert.equal(F.effHit({ d: {}, m: null }, null), null);
// dificuldade das hunts (para a personagem)
assert.equal(F.huntDiff({ d: 1, hit: null, eff: 1000 }), 1);
assert.equal(F.huntDiff({ d: 1, hit: 500, eff: 1000 }), 2);    // r = 0,5
assert.equal(F.huntDiff({ d: 1, hit: 1000, eff: 1000 }), 3);   // r = 1: um golpe pode matar (+2)
assert.equal(F.huntDiff({ d: 2, hit: 100, eff: 1000 }), 2);    // r < 0,2 e d > 1
assert.equal(F.huntDiff({ d: 3, hit: 900, eff: 1000 }), 5);
assert.equal(F.huntDiff({ d: 3, hit: 300, eff: 1000, adj: 1 }), 5);
assert.equal(F.huntDiff({ d: 1, hit: null, eff: null, adj: -1 }), 1);
assert.equal(F.huntDiff({ d: 9, hit: NaN, eff: 1000 }), 4);    // d fora de 1..3 conta como 3; dano inválido = sem dano
// a mesma hunt para duas personagens: mage sem set vs knight com proteções
const B = require("../shared/bosses.js");
const dm = { d: { fire: 1300, physical: 400 } };   // mage 150: 1300 ÷ 2335 ≥ 0,5 → 4; knight 150 com 30 % de fogo: 910 ÷ 3125 → 3
const dMage = F.huntDiff({ d: 2, hit: F.effHit(dm, null), eff: B.effHP("sorcerer", 150, 0) });
const dKnight = F.huntDiff({ d: 2, hit: F.effHit(dm, { fire: 30 }), eff: B.effHP("knight", 150) });
assert(dMage > dKnight, "mage sem set tem de ser mais difícil: " + dMage + " vs " + dKnight);
// ajuste ao nível
assert.deepEqual(F.levelFactor(400, 100), { f: 1.25, ok: true });
assert.deepEqual(F.levelFactor(100, 100), { f: 1, ok: true });
assert.deepEqual(F.levelFactor(81, 100), { f: 0.9, ok: true });
assert.equal(F.levelFactor(50, 100).ok, false);
assert.deepEqual(F.levelFactor(300, null), { f: 1, ok: true });
assert.equal(F.levelFactor(200, 100, 0.3).f, Math.round(Math.pow(2, 0.3) * 100) / 100);
// calibração estragada → omissões
assert.deepEqual(F.calibOf(null), { k: 0.5, dz: {}, kz: {}, ha: {} });
assert.deepEqual(F.calibOf({ v: 9 }), { k: 0.5, dz: {}, kz: {}, ha: {} });
assert.equal(F.calibOf({ v: 1, k: 0.4, dz: { a: 1 }, kz: {}, ha: {} }).k, 0.4);
assert.equal(F.calibOf({ v: 1, k: 7, dz: {}, kz: {}, ha: {} }).k, 0.5);          // k fora de 0,1–1 é ignorado
// dificuldade dos bosses
assert.equal(F.bossDiff({ st: "solo", eff: 9000, md: 3000, ttk: 100, tmax: 300 }), 2);
assert.equal(F.bossDiff({ st: "solo", eff: 7000, md: 3000, ttk: 100, tmax: 300 }), 3);
assert.equal(F.bossDiff({ st: "solo", eff: 9000, md: 3000, ttk: 200, tmax: 300 }), 3);
assert.equal(F.bossDiff({ st: "solo", eff: null, md: null, ttk: 100, tmax: 300 }), 3);
assert.equal(F.bossDiff({ st: "team", eff: 1, md: 1, ttk: 1, tmax: 300 }), 4);
assert.equal(F.bossDiff({ st: "unknown", eff: 1, md: 1, ttk: 1, tmax: 300 }), 4);
assert.equal(F.bossDiff({ st: "later", eff: 1, md: 1, ttk: 1, tmax: 300 }), 5);
assert.equal(F.bossDiff({ st: "locked", eff: 1, md: 1, ttk: 1, tmax: 300 }), 5);
assert.equal(F.DIFF[3], "média"); assert.equal(F.DIFF.length, 6);
// preys
const M = [{ k: "a", n: "A", xp: 1000, cnt: 3, hit: 200 }, { k: "b", n: "B", xp: 2000, cnt: 1, hit: 900 },
           { k: "c", n: "C", xp: 500, cnt: 1, hit: null }, { k: "d", n: "D", xp: 100, cnt: 1, hit: 100 }];
assert.deepEqual(F.preyPicks(M, 100), [{ k: "a", n: "A", bonus: "xp" }, { k: "b", n: "B", bonus: "dmg" }, { k: "c", n: "C", bonus: "dmg" }]); // B já está: a 3.ª por XP
const M2 = [M[0], { k: "b", n: "B", xp: 2000, cnt: 1, hit: 100 }, { k: "c", n: "C", xp: 500, cnt: 1, hit: 900 }];
assert.deepEqual(F.preyPicks(M2, 100).map(x => x.k + ":" + x.bonus), ["a:xp", "b:dmg", "c:red"]);   // 900 / 1105 ≥ 0,35
assert.deepEqual(F.preyPicks([M[0]], 100), [{ k: "a", n: "A", bonus: "xp" }]);
assert.deepEqual(F.preyPicks([], 100), []);
assert.deepEqual(F.preyPicks([{ k: "z", n: "Z", xp: 0, cnt: 0, hit: null }], 100), []);              // sem XP não se recomenda
// loot
const L = [{ k: "a", n: "A", cnt: 2, loot: [{ n: "Gold Coin", pct: 100, v: 1 }, { n: "Gem", pct: 1, v: 10000 }] },
           { k: "b", n: "B", cnt: 1, loot: [{ n: "Gem", pct: 5, v: 10000 }, { n: "Lixo", pct: 50, v: 0 }] }];
assert.deepEqual(F.topLoot(L), [{ n: "Gem", pct: 5, v: 10000, from: "B" }, { n: "Gold Coin", pct: 100, v: 1, from: "A" }]);
assert.equal(F.topLoot(L, 1).length, 1); assert.deepEqual(F.topLoot([]), []);
assert.deepEqual(F.topLoot([{ k: "a", n: "A", cnt: 1 }]), []);                                        // sem lista de loot
// resistências
const R = F.resist({ physical: 100, fire: 110, ice: 96, earth: 81, energy: 99, holy: 102, death: 50, min: { fire: 105, earth: 0, death: -20 } });
assert.equal(R.length, 7); assert.equal(R[0].el, "fire"); assert.equal(R[0].pct, 110);
assert.equal(R.find(x => x.el === "earth").imm, true); assert.equal(R.find(x => x.el === "death").heal, true);
assert.equal(R.find(x => x.el === "fire").imm, false); assert.deepEqual(F.resist(null), []);
// data/caminhos.json (_dev/build_caminhos.py)
const J = p => JSON.parse(readFileSync(new URL("../" + p, import.meta.url), "utf8"));
const CAM = J("data/caminhos.json"), BOS = J("data/bosses.json"), NPC = J("data/npcs.json");
const G = JSON.parse(readFileSync(new URL("../index.html", import.meta.url), "utf8").match(/<script[^>]*id="G"[^>]*>([\s\S]*?)<\/script>/)[1]);
assert.equal(CAM.v, 1);
assert.deepEqual(Object.keys(CAM.h).sort(), Object.keys(G.places).sort());
assert.deepEqual(Object.keys(CAM.b).sort(), Object.keys(BOS.b).sort());
const okC = c => Array.isArray(c) && c.length === 3 && c[0] > 31000 && c[0] < 34500 && c[1] > 30900 && c[1] < 33100 && c[2] >= 0 && c[2] <= 15;
for (const [k, c] of [...Object.entries(CAM.h), ...Object.entries(CAM.b)]) {
  assert(["ok", "rev", "part", "none"].includes(c.st), k);
  assert(c.pos === null || okC(c.pos), k + " pos");
  assert(Array.isArray(c.pre) && Array.isArray(c.legs), k);
  for (const p of c.pre) assert(["quest", "level", "premium", "item", "text"].includes(p.k), k + " pre");
  for (const l of c.legs) { if (l.ref) continue;                              // troço por referência: os passos estão em CAM.places
    assert(l.t && l.steps.length, k + " troço vazio");
    for (const s of l.steps) { assert(typeof s.s === "string" && s.s.trim(), k + " passo vazio");
      assert(s.c === null || okC(s.c), k + " ponto"); assert(!/\(\d{5},\s*\d{5}/.test(s.s), k + " coordenada no texto: " + s.s);
      if (s.npc) { assert(NPC[s.npc.n.toLowerCase()], k + " NPC desconhecido: " + s.npc.n); assert(s.npc.say.length >= 1, k); } } }
  if (c.st === "none") assert(c.legs.length <= 1, k + " none com passos");
}
// casos conhecidos (dados de 10/11/2026)
const T = CAM.h.targuna_inf;
assert.equal(T.st, "rev"); assert.equal(T.from, "Thais");
assert(T.pre.some(p => p.k === "level" && p.n === 12));
const emi = T.legs.flatMap(l => l.steps).find(s => s.npc && s.npc.n === "Emiliana");
assert.deepEqual(emi.npc.say, ["hi", "mission", "yes"]);
const blue = T.legs.flatMap(l => l.steps).find(s => s.npc && s.npc.n === "Captain Bluebear");
assert.deepEqual(blue.npc, { n: "Captain Bluebear", say: ["hi", "targuna", "yes"], gp: 110 });
assert(T.legs.flatMap(l => l.steps).some(s => s.c && s.c.join() === "31962,31898,7"));
assert(CAM.h.werelions.pre.some(p => p.k === "quest" && /Lion's Rock/.test(p.n) && p.slug));
assert(CAM.h.werelions.pre.some(p => p.k === "premium"));
assert.equal(CAM.h.upperspike.legs[0].ref, "Upper Spike");                   // ficha de local como 1.º troço, por referência
for (const c of [...Object.values(CAM.h), ...Object.values(CAM.b)]) for (const l of c.legs) if (l.ref) assert(CAM.places[l.ref], "ref sem local: " + l.ref);
assert(readFileSync(new URL("../data/caminhos.json", import.meta.url)).length < 1024 * 1024, "caminhos.json passa de 1 MB"); // as fichas de locais sozinhas já passam de 400 KB
assert(Object.values(CAM.h).filter(c => c.st === "none").length <= 129);
assert(CAM.b.abyssador.refs.some(r => r.slug === "bigfoots-burden-quest" && r.sec === 8));
assert(Object.values(CAM.h).every(c => c.st !== "none" || c.legs.length === 1)); // a frase do p.acc fica como único passo
// huntEst (motor dos números do huntRows): uma hunt que só tem linhas de 1 vocação estima-se para outra.
// O compatFor e o avgMon vêm do index.html (node:vm, como no _dev/huntest_gold.mjs).
assert.equal(typeof F.huntEst, "function");
const H = readFileSync(new URL("../index.html", import.meta.url), "utf8"), A0 = H.indexOf("<script>\n(function(){");
const cut = (a, b) => { const s = H.indexOf(a, A0); assert(s > 0, a); return H.slice(s, H.indexOf(b, s)); };
const hctx = { G, hasKey: (o, k) => !!o && Object.prototype.hasOwnProperty.call(o, k) };
vm.createContext(hctx);
vm.runInContext([cut("const ELN = ", "\n"), cut("const HOWEL=", "/* o que bater:"), cut("const AVGXP={};", "function avgXp(")].join("\n"), hctx);
const VV = ["knight", "paladin", "sorcerer", "druid", "monk"];
const solo = Object.keys(G.places).find(k => VV.filter(v => G.hunts[v].some(r => r.c === k)).length === 1 && G.hunts[VV.find(v => G.hunts[v].some(r => r.c === k))].some(r => r.c === k && r.l >= 300));
assert(solo, "sem hunt com linhas de 1 só vocação");
const sv = VV.find(v => G.hunts[v].some(r => r.c === solo)), ov = VV.find(v => v !== sv);
const he = F.huntEst({ G, voc: ov, pid: solo, L: 1000, pl: 1000, compatFor: hctx.compatFor, avgMon: hctx.avgMon });
assert(he && he.xp !== null && he.est !== null, `huntEst ${ov} ${solo}: ${JSON.stringify(he)}`);
assert.equal(F.huntEst({ G, voc: ov, pid: "nao-existe", L: 1000, pl: 1000, compatFor: hctx.compatFor, avgMon: hctx.avgMon }), null);
// minimapa (shared/minimapa.js): enquadramento puro
const MM = require("../shared/minimapa.js");
assert.deepEqual(MM.fit([[32000, 32000, 7]], 0, 260, 173), { z: 7, on: [0], cx: 32000.5, cy: 32000.5, s: 5 });
const f2 = MM.fit([[32000, 32000, 7], [32010, 32004, 6], [32020, 32000, 7]], 0, 260, 173);  // 2 andares: só os do andar escolhido
assert.equal(f2.z, 7); assert.deepEqual(f2.on, [0, 2]); assert.equal(f2.cx, 32010.5);
assert.deepEqual(MM.fit([[32000, 32000, 7], [32010, 32004, 6]], 1, 260, 173).on, [1]);
const fFar = MM.fit([[32000, 32000, 7], [33000, 32600, 7]], 1, 260, 173);              // longe: escala mínima, centrado no escolhido
assert.equal(fFar.s, 0.6); assert.equal(fFar.cx, 33000.5); assert.equal(fFar.cy, 32600.5);
const fAll = MM.fit([[32000, 32000, 7], [33000, 32600, 6]], null, 260, 173);           // sem escolhido (Questski): todos, centro da caixa
assert.deepEqual(fAll.on, [0, 1]); assert.equal(fAll.cx, 32500.5); assert.equal(fAll.s, 0.6);
assert.equal(MM.fit([], 0, 260, 173), null); assert.equal(MM.fit(null, 0, 260, 173), null);
console.log("fichas: ok");
