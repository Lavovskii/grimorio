// Modelo das fichas (shared/fichas.js). Uso: node _dev/fichas_test.mjs
import { createRequire } from "module";
import assert from "node:assert/strict";
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
console.log("fichas: ok");
