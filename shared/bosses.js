/* Tibia Grimoire — que bosses uma personagem aguenta no seu nível (window.GrimBoss; em node, module.exports).
   Dados: data/bosses.json (_dev/build_bosses.py, TibiaWiki) + data/creatures.json (resistências e loot) + o dano de boss do
   motor de rotações (GrimRot.plan, cenário 'boss'). Modelo e limites: _dev/BOSSES.md.
   Para cada boss, três perguntas, com a vocação e o nível:
   - acesso: o nível mínimo da quest (ql); abaixo dele não entras;
   - aguentar: a vida efetiva (vida × mitigação da vocação; magos: vida + Magic Shield) chega para 2 golpes do dano máximo
     por turno (md) sozinho, ou 1,3 em equipa (há quem cure e quem bloqueie);
   - matar: vida do boss ÷ 70 % do dano por segundo da rotação (movimento, curas, kiting; no elemento a que o boss é mais
     fraco, entre as linhas da vocação) cabe no tempo da categoria: Bane 2,5 min, Archfoe 5 min, Nemesis 10 min (em equipa,
     1,5 vezes isso) com o dano de 4 personagens iguais;
   - nunca abaixo do nível recomendado da quest (qr): as fases, curas e mecânicas dos bosses de quest não entram nas contas.
   Sem vida conhecida não há 'sozinho' (só equipa, pelo dano máximo e pelo qr); sem dano máximo, só bosses até 20 000 de vida.
   Proteções (opt.prot, {elemento: %} do set da personagem): com o dano por elemento (opt.d, do data/crdmg.json; senão as % do
   b.dm), o md passa a ser o golpe efetivo; sem opt.prot, igual. */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.GrimBoss = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";
  var VOC = { // vida por nível (como G.voc) e a mitigação/defesa média aproximada da vocação contra o dano do boss
    knight: { hp: 15, mit: 1.35 }, paladin: { hp: 10, mit: 1.15 }, monk: { hp: 10, mit: 1.25 }, sorcerer: { hp: 5, mit: 1 }, druid: { hp: 5, mit: 1 } };
  var MAGE = { sorcerer: 1, druid: 1 };
  var LANES = { knight: ["physical"], monk: ["physical"], paladin: ["holy", "physical"], sorcerer: ["fire", "energy", "death"], druid: ["ice", "earth"] };
  var TMAX = { b: 150, a: 300, n: 600 }, TTEAM = 1.5; // segundos para matar sozinho (em equipa, × TTEAM)
  var SURV = { solo: 2, team: 1.3 }, TEAM = 4, UPTIME = 0.7, SOLO_NOMD = 20000;
  var CLS = { b: "Bane", a: "Archfoe", n: "Nemesis" };
  // níveis onde o dano de boss do motor é medido (o resto interpola-se)
  var ANCHORS = [8, 20, 35, 50, 75, 100, 130, 160, 200, 250, 300, 400, 500, 600, 700, 800, 1000, 1200, 1500, 2000, 2500];

  function hpAt(voc, L) { return 185 + VOC[voc].hp * (L - 8); }
  // Magic Shield (utamo vita) como no site: 7 × ML + 7,6 × nível + máx(300, 0,4 × nível); ML pelo nível se faltar
  function shieldAt(L, ml) { return Math.round(7 * ml + 7.6 * L + Math.max(300, 0.4 * L)); }
  function effHP(voc, L, ml) {   // ml: o magic level nesse nível (os magos somam o Magic Shield)
    var h = hpAt(voc, L);
    return MAGE[voc] ? h + shieldAt(L, ml || 0) : h * VOC[voc].mit;
  }

  // golpe efetivo: o pior elemento de d[el] × (1 − prot[el]/100) (a regra do GrimFicha.effHit, copiada para não ligar os ficheiros)
  function effHit(d, prot) {
    var best = 0;
    for (var e in d) { var p = prot && +prot[e] > 0 ? Math.min(100, +prot[e]) : 0, v = (+d[e] || 0) * (1 - p / 100); if (v > best) best = v; }
    return best;
  }

  // curva de dano por segundo: [[nível, dps]] → dps em qualquer nível (linear entre âncoras; acima da última, proporcional ao nível)
  function curveAt(curve, L) {
    if (!curve || !curve.length) return 0;
    if (L <= curve[0][0]) return curve[0][1] * L / curve[0][0];
    for (var i = 1; i < curve.length; i++) if (L <= curve[i][0]) {
      var a = curve[i - 1], b = curve[i], f = (L - a[0]) / (b[0] - a[0]); return a[1] + (b[1] - a[1]) * f;
    }
    var z = curve[curve.length - 1]; return z[1] * L / z[0];
  }
  // dps(L): plan(L) dá o dps do cenário boss (neutro). Opcional: o dps real da personagem no seu nível (com equipamento e
  // skills) dá a escala da curva inteira.
  function makeCurve(plan, Lc, dpsReal) {
    var c = ANCHORS.map(function (L) { return [L, Math.max(1, plan(L))]; });
    if (Lc && dpsReal > 0) { var k = dpsReal / Math.max(1, curveAt(c, Lc)); if (k > 0.3 && k < 3) c = c.map(function (x) { return [x[0], x[1] * k]; }); }
    return c;
  }
  // multiplicador de dano contra o boss: o melhor elemento das linhas da vocação (el = % de dano que o boss leva, 100 = neutro)
  function laneMult(voc, el) {
    if (!el) return 1;
    var best = 0; LANES[voc].forEach(function (e) { var v = el[e] != null ? +el[e] : 100; if (v > best) best = v; });
    return Math.max(0.05, best / 100);
  }
  function bestEl(voc, el) {
    var b = LANES[voc][0], bv = -1; LANES[voc].forEach(function (e) { var v = el && el[e] != null ? +el[e] : 100; if (v > bv) { bv = v; b = e; } });
    return b;
  }

  // o nível mais baixo (8–2500) em que fn(L) é verdade, ou null
  function minLevel(fn, from) {
    var L0 = Math.max(8, from || 8);
    if (fn(2500) === false) return null;
    var lo = L0, hi = 2500; if (fn(lo)) return lo;
    while (hi - lo > 1) { var m = (lo + hi) >> 1; if (fn(m)) hi = m; else lo = m; }
    return hi;
  }

  // avaliação de um boss para uma personagem: {k, st ('solo'|'team'|'later'|'locked'|'unknown'), soloL, teamL, ttk (s, sozinho),
  // ttkT (em equipa), dps, eff, md, need (vida efetiva pedida sozinho), el (melhor elemento), why}
  function judge(b, opt) {
    var voc = opt.voc, L = opt.level, cr = opt.cr || {}, mult = laneMult(voc, cr.el), hp = b.hp || cr.hp || 0, md = b.md || 0;
    // dano por elemento (valores do crdmg.json ou as % do b.dm): o golpe máximo escala pela parte que as proteções deixam
    // passar no pior elemento (uma razão, por isso serve para valores e para %)
    var dd = opt.d && Object.keys(opt.d).length ? opt.d : b.dm;
    if (md && dd && opt.prot) { var d0 = effHit(dd); if (d0 > 0) md = Math.max(1, Math.round(md * effHit(dd, opt.prot) / d0)); } // 0 seria «dano desconhecido»
    var dpsAt = function (l) { return curveAt(opt.curve, l) * mult * UPTIME; };
    var mlAt = opt.mlAt || function () { return 0; };
    var eff = function (l) { return effHP(voc, l, l === L && opt.ml > 0 ? opt.ml : mlAt(l)); };
    var floor = b.ql || 8, rec = Math.max(floor, b.qr || 0), t = TMAX[b.c] || 300;
    // sem dano máximo conhecido, 'sozinho' só para bosses pequenos (até SOLO_NOMD de vida)
    var okSolo = function (l) { return !!hp && (md ? eff(l) >= SURV.solo * md : hp <= SOLO_NOMD) && hp / Math.max(1, dpsAt(l)) <= t; };
    var okTeam = function (l) { return (!md || eff(l) >= SURV.team * md) && (!hp || hp / Math.max(1, dpsAt(l) * TEAM) <= t * TTEAM); };
    var r = { k: opt.k, c: b.c, md: md, hp: hp, el: bestEl(voc, cr.el), mult: mult, dps: Math.round(dpsAt(L)), eff: Math.round(eff(L)) };
    r.ttk = hp ? Math.round(hp / Math.max(1, dpsAt(L))) : null; r.ttkT = hp ? Math.round(hp / Math.max(1, dpsAt(L) * TEAM)) : null;
    if (!hp && !md) {
      r.soloL = null; r.teamL = b.qr || b.ql || null;
      r.st = L < floor ? "locked" : r.teamL && L >= r.teamL ? "unknown" : "later";
      return r;
    }
    r.soloL = minLevel(okSolo, rec); r.teamL = minLevel(okTeam, rec);
    r.st = L < floor ? "locked" : r.soloL != null && L >= r.soloL ? "solo" : r.teamL != null && L >= r.teamL ? "team" : "later";
    return r;
  }

  // Bosstiary: estágio pelas mortes, pontos de cada boss e bónus de loot (Cyclopedia, TibiaWiki)
  function stageOf(pts, c, kills) { var s = 0; (pts[c] || []).forEach(function (x, i) { if (kills >= x[0]) s = i + 1; }); return s; }
  function pointsOf(pts, c, stage) { var p = 0; (pts[c] || []).slice(0, stage).forEach(function (x) { p += x[1]; }); return p; }
  function lootBonus(P) {
    if (P < 250) return 25 + Math.floor(P / 10);
    if (P < 1250) return 50 + Math.floor((P - 250) / 20);
    return Math.floor(100 + (Math.sqrt(8 * (P - 1250) / 5 + 81) - 9) / 2);
  }
  function cdText(h) {
    if (h == null) return "";
    // (um só valor por frase: o tradutor do site, shared/i18n.js, troca cada valor uma vez)
    if (h < 1) return "a cada " + Math.round(h * 60) + " min";
    if (h < 20) return "a cada " + h + " h";
    if (h <= 24) return "1 vez por dia (" + h + " h)";
    if (h < 120) return "a cada " + Math.round(h / 24 * 10) / 10 + " dias";
    return "a cada " + Math.round(h / 24) + " dias";
  }
  // r36 bosses do dia. Evento = b.ev ('wc' world change, 'saz' sazonal, 'raid'); sem ev = permanente.
  function isEvent(b) { return !!(b && b.ev); }
  // hora de Berlim (0–23) de um instante (o server save é às 10:00 de Berlim, CET ou CEST)
  function berlinH(t) { return +new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/Berlin", hour: "numeric", hourCycle: "h23" }).format(new Date(t)); }
  // o 1.º server save depois de t (ms)
  function nextSS(t) {
    for (var d = 0; d < 3; d++) for (var off = 1; off <= 2; off++) {
      var x = new Date(t), s = Date.UTC(x.getUTCFullYear(), x.getUTCMonth(), x.getUTCDate() + d, 10 - off);
      if (s > t && berlinH(s) === 10) return s;
    }
    return t + 864e5;
  }
  // ms até o boss voltar, marcado como feito em ts: ts + cd horas; sem cd, o server save seguinte. 0 = já voltou (ou sem ts)
  function cdLeft(ts, cdH, now) {
    if (!ts) return 0;
    var end = cdH > 0 ? ts + cdH * 3600e3 : nextSS(ts);
    return Math.max(0, end - now);
  }
  // rows: [{k, b, r (GrimBoss.judge), lo (lootPerKill), t (feito em, ms)}]. Até 4 bosses permanentes, sozinho, fora do cooldown,
  // sem repetir: o boss em destaque (boostedKey), o melhor lucro (lo.v), mais XP (b.xp) e o mais rápido (r.ttk).
  // → {boost: {k, why: null (entrou) | 'ev' | 'st' (não é sozinho) | 'cd' | 'none' (não está na lista)} | null, picks: [[cat, row]]}
  function dailyPicks(rows, boostedKey, now) {
    var ok = function (x) { return !isEvent(x.b) && x.r && x.r.st === "solo" && !cdLeft(x.t, x.b.cd, now); };
    var used = {}, picks = [], boost = null;
    if (boostedKey) {
      var bx = rows.filter(function (x) { return x.k === boostedKey; })[0];
      boost = { k: boostedKey, why: !bx ? "none" : isEvent(bx.b) ? "ev" : !bx.r || bx.r.st !== "solo" ? "st" : !ok(bx) ? "cd" : null };
      if (bx && !boost.why) { picks.push(["boost", bx]); used[bx.k] = 1; }
    }
    [["lucro", function (x) { return x.lo && !x.lo.nodata && x.lo.v > 0 ? x.lo.v : null; }],
     ["xp", function (x) { return x.b.xp > 0 ? x.b.xp : null; }],
     ["rapido", function (x) { return x.r.ttk > 0 ? -x.r.ttk : null; }]].forEach(function (c) {
      var best = null, bv = null;
      rows.forEach(function (x) { if (used[x.k] || !ok(x)) return; var v = c[1](x); if (v != null && (bv == null || v > bv)) { best = x; bv = v; } });
      if (best) { picks.push([c[0], best]); used[best.k] = 1; }
    });
    return { boost: boost, picks: picks };
  }
  return { judge: judge, makeCurve: makeCurve, curveAt: curveAt, effHP: effHP, laneMult: laneMult, stageOf: stageOf, pointsOf: pointsOf,
    lootBonus: lootBonus, cdText: cdText, isEvent: isEvent, cdLeft: cdLeft, dailyPicks: dailyPicks, ANCHORS: ANCHORS, CLS: CLS, TMAX: TMAX };
});
