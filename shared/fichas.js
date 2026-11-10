/* Tibia Grimoire — contas das fichas de hunts e bosses (window.GrimFicha; em node, module.exports).
   Funções puras: dificuldade 1–5 para a personagem (golpe efetivo com as proteções do set ÷ vida efetiva do
   GrimBoss.effHP), ajuste do XP/lucro ao nível, validação do data/calib.json, preys, loot principal e resistências.
   Regras: docs/superpowers/specs/2026-11-10-fichas-hunts-bosses-design.md (rondas 2 a 4, Q6 e Q7). Teste: node _dev/fichas_test.mjs */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.GrimFicha = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";
  var ELS = ["physical", "fire", "ice", "earth", "energy", "holy", "death"];
  var DIFF = ["", "muito fácil", "fácil", "média", "difícil", "muito difícil"];
  var PREY = { xp: "Bónus de XP", dmg: "Bónus de dano", red: "Redução de dano" };

  function num(x) { return typeof x === "number" && isFinite(x); }
  function obj(x) { return !!x && typeof x === "object" && !Array.isArray(x); }
  function clamp(x, a, b) { return Math.max(a, Math.min(b, x)); }

  // vida de referência (vocação com 10 de vida por nível) no nível L
  function refHp(L) { return 185 + 10 * (Math.max(8, L) - 8); }

  // golpe efetivo: o pior elemento de d[el] × (1 − prot[el]/100); sem d, o m conta como físico
  function effHit(dm, prot) {
    if (!dm) return null;
    var d = {}, any = false, best = null;
    ELS.forEach(function (e) { if (dm.d && num(dm.d[e])) { d[e] = dm.d[e]; any = true; } });
    if (!any) { if (!num(dm.m)) return null; d.physical = dm.m; }
    for (var e in d) {
      var p = prot && num(prot[e]) ? clamp(prot[e], 0, 100) : 0, v = d[e] * (1 - p / 100);
      if (best === null || v > best) best = v;
    }
    return Math.round(best);
  }

  // dificuldade da hunt: base pelo d curado, ajustada pela razão golpe ÷ vida efetiva e pelo calib.dz (adj)
  function huntDiff(o) {
    var x = [1, 3, 4][o.d - 1] || 4;
    if (num(o.hit) && num(o.eff) && o.eff > 0) {
      var r = o.hit / o.eff;
      if (r >= 1) x += 2; else if (r >= 0.5) x += 1; else if (r < 0.2 && x > 1) x -= 1;
    }
    if (num(o.adj)) x += o.adj;
    return clamp(x, 1, 5);
  }

  // dificuldade do boss pelo estado do GrimBoss.judge
  function bossDiff(o) {
    if (o.st === "solo") return num(o.eff) && num(o.md) && num(o.ttk) && o.eff >= 3 * o.md && o.ttk <= o.tmax / 2 ? 2 : 3;
    return o.st === "team" || o.st === "unknown" ? 4 : 5;
  }

  // ajuste do XP/lucro ao nível: (L/Lm)^k entre 0,7 e 1,25; abaixo de 0,6 × Lm não se estima
  function levelFactor(L, Lm, k) {
    if (!num(Lm) || Lm <= 0) return { f: 1, ok: true };
    var f = clamp(Math.pow(L / Lm, num(k) ? k : 0.5), 0.7, 1.25);
    return { f: Math.round(f * 100) / 100, ok: L >= 0.6 * Lm };
  }

  // data/calib.json validado; estragado ou em falta → omissões
  function calibOf(x) {
    if (!obj(x) || x.v !== 1) return { k: 0.5, dz: {}, kz: {}, ha: {} };
    return { k: num(x.k) && x.k >= 0.1 && x.k <= 1 ? x.k : 0.5,
      dz: obj(x.dz) ? x.dz : {}, kz: obj(x.kz) ? x.kz : {}, ha: obj(x.ha) ? x.ha : {} };
  }

  // preys: 1.ª por XP × quantidade = XP, 2.ª = dano; 3.ª = redução se a que bate mais forte tira ≥ 35 % da vida de referência
  function preyPicks(mons, L) {
    var m = (mons || []).filter(function (c) { return c.xp * c.cnt > 0; })
      .sort(function (a, b) { return b.xp * b.cnt - a.xp * a.cnt; });
    var out = m.slice(0, 2).map(function (c, i) { return { k: c.k, n: c.n, bonus: i ? "dmg" : "xp" }; });
    var rest = m.slice(2);
    if (!rest.length) return out;
    var hard = null;
    rest.forEach(function (c) { if (num(c.hit) && (!hard || c.hit > hard.hit)) hard = c; });
    if (hard && hard.hit / refHp(L) >= 0.35) out.push({ k: hard.k, n: hard.n, bonus: "red" });
    else out.push({ k: rest[0].k, n: rest[0].n, bonus: "dmg" });
    return out;
  }

  // loot principal: valor × probabilidade × quantidade; um item por nome, com a criatura que mais o dá
  function topLoot(mons, max) {
    var by = {};
    (mons || []).forEach(function (c) {
      (c.loot || []).forEach(function (it) {
        if (!(it.v > 0)) return;
        var s = it.v * it.pct / 100 * c.cnt;
        if (!by[it.n] || s > by[it.n].s) by[it.n] = { s: s, x: { n: it.n, pct: it.pct, v: it.v, from: c.n } };
      });
    });
    return Object.keys(by).map(function (n) { return by[n]; })
      .sort(function (a, b) { return b.s - a.s; }).slice(0, max || 8).map(function (y) { return y.x; });
  }

  // resistências: % de dano que levam (100 = neutro), do mais fraco para o mais resistente; min 0 = imune, < 0 = cura
  function resist(eff) {
    if (!eff) return [];
    var mn = eff.min || {};
    return ELS.map(function (e) {
      return { el: e, pct: num(eff[e]) ? eff[e] : 100, imm: mn[e] === 0, heal: mn[e] < 0 };
    }).sort(function (a, b) { return b.pct - a.pct; });
  }

  return { refHp: refHp, effHit: effHit, huntDiff: huntDiff, bossDiff: bossDiff, levelFactor: levelFactor, calibOf: calibOf,
    DIFF: DIFF, PREY: PREY, preyPicks: preyPicks, topLoot: topLoot, resist: resist };
});
