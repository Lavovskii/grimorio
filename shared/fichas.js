/* Tibia Grimoire — contas das fichas de hunts e bosses (window.GrimFicha; em node, module.exports).
   Funções puras: dificuldade 1–5 para a personagem (golpe efetivo com as proteções do set ÷ vida efetiva do
   GrimBoss.effHP), XP/lucro de uma hunt (huntEst, o motor do huntRows) e ajuste ao nível, validação do data/calib.json, preys,
   loot principal e resistências.
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

  /* ---------- números de uma hunt (o motor que estava no huntRows do index.html, r6-t2) ---------- */
  var VOCS = ["knight", "paladin", "sorcerer", "druid", "monk"];
  var EST_ORDER = { druid: ["sorcerer", "paladin", "knight", "monk"], sorcerer: ["druid", "paladin", "knight", "monk"], knight: ["paladin", "monk", "sorcerer", "druid"], paladin: ["knight", "sorcerer", "druid", "monk"], monk: ["knight", "paladin", "sorcerer", "druid"] };
  function hk(o, k) { return !!o && Object.prototype.hasOwnProperty.call(o, k); }
  function medOf(a) { var b = a.slice().sort(function (x, y) { return x - y; }), m = b.length >> 1; return b.length % 2 ? b[m] : (b[m - 1] + b[m]) / 2; }
  function r1k(x) { return Math.round(x / 1000) * 1000; }

  // variante de uma zona do TibiaPal até ao teto L: a de mais XP com l ≤ L; sem XP, a de nível mais baixo (das que cabem, senão de todas)
  function pickRow(g, L) {
    if (!g || !g.length) return null;
    var ok = g.filter(function (x) { return x.l <= L; }), low = function (a) { return a.reduce(function (b, x) { return x.l < b.l ? x : b; }, a[0]); };
    return ok.filter(function (x) { return x.xp != null; }).sort(function (a, b) { return b.xp - a.xp; })[0] || low(ok.length ? ok : g);
  }

  // XP/h e lucro/h de uma hunt (pid) para uma vocação, antes do ajuste ao nível. ctx = {G, voc, pid, L (teto da variante),
  // pl (nível do jogador), compatFor(voc, place, how), avgMon(pid), r (opcional: a variante já escolhida)}. Sem linha da
  // vocação, parte do nível da variante da 1.ª vocação do EST_ORDER que tem a zona. src: 'tp' | 'old' | 'est' | 'ha' | 'hao' |
  // 'mx' | null; Lm = nível da medição usada (null no 'mx' e sem número). Devolve também o cmp (compatFor, com a exceção 'meh').
  function huntEst(c) {
    var G = c.G, voc = c.voc, pid = c.pid, L = c.L, pl = c.pl, compatFor = c.compatFor;
    var mine = function (v) { return (G.hunts[v] || []).filter(function (x) { return x.c === pid; }); };
    var r = c.r || pickRow(mine(voc), L);
    if (!r) { for (var i = 0; i < EST_ORDER[voc].length && !r; i++) { var b = pickRow(mine(EST_ORDER[voc][i]), L); if (b) r = { c: pid, place: b.place, l: b.l, xp: null, lo: null, how: "" }; } }
    if (!r) return null;
    var p = r.c ? G.places[r.c] : null, cmp = compatFor(voc, p, r.how);
    // r4-t3: a XP que o TibiaPal mediu para esta vocação já conta com a resistência: no máximo 'resiste um pouco'
    // r6-t2: menos nos números do TibiaPal de antes do rebalance de junho de 2026 (o:1), que já não são uma medição atual
    if (r.xp != null && !r.f && !r.w && !r.o && cmp.cls === "bad") { cmp.cls = "meh"; cmp.txt += " (o TibiaPal mediu esta hunt para a tua vocação)"; }
    var xp = r.xp, lo = r.lo, est = r.o ? "old" : null, estx = null, Lm = r.xp != null ? r.l : null;
    var estMax = Math.max(r.l + 20, Math.round(r.l * 1.25));
    // outra vocação → esta: dano (0,5–1,15) × G.vr
    var fOf = function (ov, oc) { return ((cmp.v > 0 && oc.v > 0) ? Math.max(0.5, Math.min(1.15, cmp.v / oc.v)) : 1) * (((G.vr || {})[voc] || {})[ov] || 1); };
    // r6-t2: as linhas o:1 das outras vocações só contam quando nenhuma linha atual serve (2.ª volta)
    if (xp == null && r.c) {
      for (var old = 0; old < 2 && xp == null; old++) for (var j = 0; j < EST_ORDER[voc].length; j++) { var ov = EST_ORDER[voc][j];
        var o = (G.hunts[ov] || []).filter(function (x) { return x.c === r.c && x.xp != null && !!x.o === !!old && x.l <= estMax && x.l >= Math.round(r.l * 0.6); }).sort(function (a, b) { return b.xp - a.xp; })[0];
        if (o) { var f = fOf(ov, compatFor(ov, p, o.how));
          xp = r1k(o.xp * f); lo = o.lo == null ? null : r1k(o.lo * (o.lo > 0 ? f : 1)); est = ov; Lm = o.l; if (old) estx = { o: 1 }; break; } }
    }
    var ha = r.c && G.ha && hk(G.ha, r.c) && G.ha[r.c].v[voc], src = r.xp != null ? (r.o ? "old" : "tp") : est ? "est" : null;
    // sessões reais só contam quando o teto L chega a 3/4 do nível mediano dessas sessões (r6-t2: e ganham a um número de antes do rebalance)
    var haOk = ha && ha[0] >= 3 && L >= Math.round(ha[2] * 0.75);
    if ((r.xp == null || r.o) && haOk) { xp = ha[3]; lo = ha[4] != null ? r1k(ha[4]) : (r.o ? null : lo); est = null; estx = null; src = "ha"; Lm = ha[2]; }
    // r6-t2: ainda sem número: (a) sessões reais de outras vocações (3+ sessões e pl a 3/4 do nível mediano delas), com o mesmo fator;
    // (b) nas hunts 300+, K mortes por hora × XP média por morte × dano (K = 1000 abaixo do 600, 1400 a partir do 850, linear no meio),
    //     sem passar de 18 000 × nível de vida por hora (o dano por hora mais alto das sessões reais: Podzilla, sorcerer 925, 32 sessões)
    //     nem do ritmo medido nesta zona (linhas atuais do TibiaPal de outras vocações e sessões reais, com nível ≥ 0,6 × o da linha)
    if (xp == null && r.c) {
      var hv = G.ha && hk(G.ha, r.c) ? G.ha[r.c].v : null, xs = [], ls = [], vs = [], lv = [], n = 0;
      if (hv) VOCS.forEach(function (ov) { var a = ov !== voc && hk(hv, ov) ? hv[ov] : null; if (!a || a[0] < 3 || pl < Math.round(a[2] * 0.75)) return;
        var o = (G.hunts[ov] || []).find(function (x) { return x.c === r.c; }), f = fOf(ov, compatFor(ov, p, o ? o.how : ""));
        xs.push(a[3] * f); if (a[4] != null && a[4] > 0) ls.push(a[4] * f); vs.push(ov); lv.push(a[2]); n += a[0]; });
      if (xs.length) { xp = r1k(medOf(xs)); lo = ls.length ? r1k(medOf(ls)) : null; est = src = "hao"; estx = { n: n, v: vs, m: Math.round(medOf(lv)) }; Lm = estx.m; }
      else if (r.l >= 300) { var am = c.avgMon(r.c), a = am && am[0], lmin = Math.round(r.l * 0.6), kz = [];
        if (a) VOCS.forEach(function (ov) { if (ov !== voc) (G.hunts[ov] || []).forEach(function (y) { if (y.c === r.c && y.xp != null && !y.o && !y.f && !y.w && y.l >= lmin) kz.push(y.xp / a); });
          var z = hv && hk(hv, ov) ? hv[ov] : null; if (z && z[2] >= lmin) kz.push(z[3] / a); });
        var K0 = pl < 600 ? 1000 : pl >= 850 ? 1400 : 1000 + (pl - 600) * 1.6, K1 = kz.length ? Math.min(K0, medOf(kz)) : K0, K = am && am[1] > 0 ? Math.min(K1, 18000 * pl / am[1]) : K1;
        var x = a ? r1k(K * a * Math.min(1.1, Math.max(0.6, cmp.v != null ? cmp.v / 100 : 1))) : 0;
        if (x > 0) { xp = x; lo = null; est = src = "mx"; estx = { k: K, z: kz.length }; Lm = null; } }
    }
    if (xp == null) Lm = null;
    return { xp: xp, lo: lo, l: r.l, src: src, est: est, estx: estx, Lm: Lm, cmp: cmp };
  }

  return { refHp: refHp, effHit: effHit, huntDiff: huntDiff, bossDiff: bossDiff, levelFactor: levelFactor, calibOf: calibOf,
    DIFF: DIFF, PREY: PREY, preyPicks: preyPicks, topLoot: topLoot, resist: resist, pickRow: pickRow, huntEst: huntEst };
});
