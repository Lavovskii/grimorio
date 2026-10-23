/* Grimório — motor de rotações (hotkeys de ataque por vocação, cenário, elemento da criatura, nível e orçamento).
   Dados: data/rotacoes.json (feito por _dev/build_rotacoes.py a partir do data/spells.json). Documentação: _dev/ROTACOES.md.
   Ainda não está ligado ao index.html: GrimRot.plan(D, opções) devolve um plano; GrimRot.toHK(plano) e GrimRot.toRot(plano)
   dão-no no formato de G.voc[voc].hk e G.voc[voc].rot.

   Modelo (resumo; os pormenores e as fontes estão no ROTACOES.md):
   - dano de cada lançamento = base power × alvos (geometria do cenário) × % que a criatura leva desse elemento × escala da
     família (magic, melee, dist, fist) para os stats estimados no nível (as mesmas curvas do chStats do index.html);
   - o grupo de ataque (2 s, 4 s nos feitiços de foco), os cooldowns próprios e os secundários (special, ultimate, focus,
     beams, bursts) são respeitados numa simulação; a ordem é "o que vale mais por segundo de grupo de ataque", menos λ × gold;
   - uma rotação só usa feitiços da vocação de UM elemento (linha: gelo OU terra, fogo OU energia OU morte, holy OU físico);
     runas e feitiços de outro elemento só entram se a criatura levar desse elemento pelo menos tanto como do da linha;
   - o sorcerer usa a conversão da stance (Master of X): um feitiço de outro elemento logo a seguir a um da linha sai no
     elemento da linha; o monk gasta a Harmony com 5 pontos (bónus duplica a cada ponto);
   - DoTs (não acumulam e duram minutos) abrem a luta contra bosses e não entram na rotação;
   - economia: mana pelo preço da poção mais barata que chega para a mana por segundo pedida, menos o mana leech do Void;
     runas pelo preço do NPC. Orçamento 'max' (sem limite), 'eco' (limite pelo nível) ou um número em gp/h. */
(function (root) {
  "use strict";

  var VOCS = ["knight", "paladin", "sorcerer", "druid", "monk"];
  var MELEE_VOC = { knight: 1, monk: 1 };
  var LANES = {
    knight: [{ k: "fisico", n: "Físico", el: "physical" }],
    monk: [{ k: "fisico", n: "Físico", el: "physical" }],
    paladin: [{ k: "holy", n: "Holy", el: "holy" }, { k: "fisico", n: "Físico", el: "physical" }],
    druid: [{ k: "gelo", n: "Gelo", el: "ice" }, { k: "terra", n: "Terra", el: "earth" }],
    sorcerer: [{ k: "fogo", n: "Fogo", el: "fire" }, { k: "energia", n: "Energia", el: "energy" }, { k: "morte", n: "Morte", el: "death" }]
  };
  var ELN = { physical: "físico", fire: "fogo", ice: "gelo", earth: "terra", energy: "energia", holy: "holy", death: "morte" };
  var SCN = { boss: "Boss", caixa: "Caixa (monstros colados)", espalhados: "Monstros espalhados (lure)", party: "Party" };
  var VOCK = { knight: "k", paladin: "p", sorcerer: "s", druid: "d", monk: "m" };
  // num boss os Forked só têm um alvo: o Burst (com kiting a 2–3 casas) faz mais por lançamento e fica com esse papel
  var BOSS_SKIP = { "Forked Glacier": 1, "Forked Thorns": 1 };
  var SORC_STANCE = { fire: ["Master of Flames", "uteta flam"], energy: ["Master of Thunder", "uteta vis"], death: ["Master of Decay", "uteta mort"] };

  // ---------- nível → stats (as curvas do chStats/scBase do index.html, para os números baterem com o resto do site) ----------
  function baseDmg(L) { // TibiaWiki, Formulae: "Base Damage and Healing" (até 500, nível/5; depois cresce mais devagar)
    var S = Math.floor((Math.sqrt(2 * L + 2025) + 5) / 10);
    return Math.floor((L + 1000) / S) + 50 * S - 450;
  }
  function stats(voc, L, ml, sk) {
    var mage = voc === "sorcerer" || voc === "druid", pal = voc === "paladin", lg = Math.log2(Math.max(1, L / 100));
    var skill = sk > 10 ? sk : mage ? 10 : Math.round(L <= 100 ? (pal ? 25 : 20) + 0.7 * L : (pal ? 95 : 90) + 12 * lg);
    var mlv = ml > 0 ? ml : Math.round(mage ? (L <= 100 ? 4 + 0.66 * L : 70 + 17 * Math.log(L / 100))
      : pal ? Math.min(45, 5 + L * 0.08) : voc === "monk" ? Math.min(40, 5 + L * 0.06) : Math.min(15, 3 + L * 0.02));
    var At = pal ? (L < 90 ? 40 : L < 150 ? 70 : 80) : Math.min(60, 30 + L * 0.04);
    return { L: L, B: baseDmg(L), sk: skill, ml: mlv, At: At };
  }
  // dano médio por ponto de base power (fórmulas da TibiaWiki, página Formulae; medidas antes de 2020, por isso aproximadas):
  // magic = Sudden Death (BP 150): nível + 6 × ML + 37; melee/fist = Fierce Berserk (BP 92): 2,05 × (skill + 2 × ataque);
  // dist = Ethereal Spear (BP 25): 2/3 × (skill + 25). O que conta para a ordem é a razão entre famílias da mesma vocação.
  function famScale(st, mod) {
    mod = mod || {};
    var sk = st.sk * (mod.sk || 1), ml = st.ml + (mod.ml || 0);
    return {
      magic: (st.B + 6 * ml + 37) / 150,
      magicIE: (st.B + 6 * (ml + (mod.ie || 0)) + 37) / 150,      // gelo/terra com Elemental Synthesis
      holy: (st.B + 6 * (ml + (mod.holy || 0)) + 37) / 150,       // holy do paladino com Divine Defiance
      melee: (2.05 * (sk + 2 * st.At) + st.B) / 92,
      shield: (2.05 * (sk + 2 * st.At) + st.B) / 92,
      fist: (2.05 * (sk + 2 * st.At) + st.B) / 92,
      dist: (2 / 3 * (sk + 25) + st.B) / 25,
      auto: 0.09 * st.At * sk + st.B                                   // um ataque automático (a cada 2 s)
    };
  }
  function wheelStage(L) { return L >= 1050 ? 3 : L >= 550 ? 2 : L >= 300 ? 1 : 0; } // pontos da Wheel = nível − 50
  function voidTier(L) { return L >= 250 ? 2 : L >= 100 ? 1 : 0; }                    // basic / intricate / powerful

  // ---------- kit ----------
  function kit(D, voc, o) {
    var L = o.level, out = [];
    Object.keys(D.ab).forEach(function (n) {
      var a = D.ab[n];
      if (a.v.indexOf(voc) < 0 || a.l > L) return;
      if (a.wheel && o.stage < 1) return;
      if (a.shd && !o.shield) return;
      if (a.q && o.quests === false) return;
      out.push(Object.assign({ kind: "spell", own: true, fm: a.fam[voc] }, a));
    });
    Object.keys(D.runes).forEach(function (n) {
      var r = D.runes[n];
      if (r.v.indexOf(voc) < 0 || r.l > L || r.ml > o.st.ml) return;
      out.push(Object.assign({ kind: "rune", own: false, fm: "magic", w: n, m: 0, cd: 2, gcd: 2, g2: null, cd2: 0 }, r));
    });
    return out;
  }

  // ---------- valor de um lançamento ----------
  function geoKey(voc, scen) {
    if (scen === "boss") return MELEE_VOC[voc] ? "boss_m" : "boss_r";
    if (scen === "party") return MELEE_VOC[voc] ? "party_m" : "party";
    return scen;
  }
  function mult(eff, el) { return eff && eff[el] != null ? Math.max(0, eff[el]) / 100 : 1; }
  function scaleFor(a, voc, S, stance) {
    if (a.fm === "magic") {
      if (voc === "druid" && (a.el === "ice" || a.el === "earth")) return S.magicIE;
      if (voc === "paladin" && a.el === "holy") return S.holy;
      return S.magic;
    }
    return S[a.fm] || S.melee;
  }

  // ---------- plano ----------
  function plan(D, opt) {
    var voc = opt.voc, L = Math.max(1, opt.level | 0), scen = opt.scen || "caixa";
    if (VOCS.indexOf(voc) < 0) throw new Error("vocação desconhecida: " + voc);
    var st = stats(voc, L, opt.ml, opt.skill);
    var stage = opt.wheel != null ? opt.wheel : wheelStage(L);
    var o = { level: L, st: st, stage: stage, shield: voc === "knight" ? opt.shield !== false : false, quests: opt.quests };
    var gk = geoKey(voc, scen), eff = opt.eff || null, party = scen === "party";
    var serene = voc === "monk" && !(party);    // em party, com 6+ monstros colados e aliados por perto, o monk perde o Serene
    var K = kit(D, voc, o);

    // poções disponíveis e a parte das poções que pode ir para mana
    var pots = D.pots.filter(function (p) { return p[2] <= L && p[5].indexOf(VOCK[voc]) >= 0; })
      .map(function (p) { return { k: p[0], n: p[1], l: p[2], mana: p[3], gp: p[4], gpm: p[4] / p[3] }; });
    var share = D.potShare[voc] || 1;
    var bigPot = pots.reduce(function (b, p) { return !b || p.mana > b.mana ? p : b; }, null);
    var capMax = bigPot ? bigPot.mana * share : 0;

    // stances a experimentar (cada uma muda a escala de dano)
    var stances = stanceOptions(voc, scen, st, stage, serene, opt);
    var lanes = LANES[voc].filter(function (ln) { return !opt.lane || ln.k === opt.lane; });
    var budget = opt.budget == null ? "max" : opt.budget;
    var cap = budget === "max" ? Infinity : budget === "eco" ? ecoCap(L) : +budget;

    var results = [];
    lanes.forEach(function (ln) {
      stances.forEach(function (sto) {
        if (sto.lane && sto.lane !== ln.el) return;
        var S = famScale(st, sto.mod);
        var r = solve(D, voc, K, ln, sto, S, gk, eff, scen, stage, pots, share, capMax, cap, serene, opt);
        if (r) results.push(r);
      });
    });
    results.sort(function (a, b) { return b.dps - a.dps; });
    var best = results[0];
    if (!best) return { voc: voc, level: L, scen: scen, empty: true, notes: ["Sem feitiços nem runas de ataque neste nível."] };
    var alts = [];
    results.forEach(function (r) {
      if (r === best || alts.some(function (x) { return x.lane === r.lane.k; })) return;
      if (r.lane.k === best.lane.k) return;
      alts.push({ lane: r.lane.k, n: r.lane.n, dps: Math.round(r.dps), pct: Math.round(100 * r.dps / best.dps) });
    });
    return finish(D, voc, L, scen, st, stage, best, alts, eff, budget, cap, pots, share, opt);
  }

  function ecoCap(L) { return Math.round((20000 + 180 * L) / 5000) * 5000; }

  function stanceOptions(voc, scen, st, stage, serene, opt) {
    var party = scen === "party", lod = [0, 0.02, 0.03, 0.04][stage];
    if (st.L < 20) return [{ n: "", mod: {}, none: 1 }];              // as stances vêm com a promoção (nível 20)
    if (voc === "knight") {
      if (party && opt.role !== "dps") return [{ n: "Protector", w: "utamo tempo", mod: { dmg: 0.85 }, why: "Em party és tu quem segura os monstros: −15% de dano recebido (e −15% de dano feito) vale mais do que o dano extra." }];
      return [{ n: "Blood Rage", w: "utito tempo", mod: { sk: 1.25 }, why: "+25% de skill de arma: mais dano em todos os feitiços e ataques. Recebes +15% de dano; troca para Protector se a vida não aguentar." }];
    }
    if (voc === "paladin") return [
      { n: "Sharpshooter", w: "utori con", mod: { sk: 1.32 }, why: "+32% de distance: sobe os feitiços ethereal e os ataques automáticos (a maior parte do dano do paladino)." },
      { n: "Divine Defiance", w: "utori hur", mod: { holy: 0.06 * st.sk }, why: "6% do distance passa a ML de holy (+" + Math.round(0.06 * st.sk) + " ML): sobe os feitiços divine; e 12% de esquiva contra monstros à distância." }];
    if (voc === "druid") {
      if (party && opt.role === "healer") return [{ n: "Shared Conservation", w: "utura sio", mod: {}, why: "Em party como healer: o Heal Friend e o Nature's Embrace curam também um 2.º aliado." }];
      return [{ n: "Elemental Synthesis", w: "utito dru", mod: { ie: 0.1 * st.ml }, why: "+10% do ML (+" + Math.round(0.1 * st.ml) + ") em gelo e terra: tudo o que a rotação lança sobe." }];
    }
    if (voc === "sorcerer") return ["fire", "energy", "death"].map(function (el) {
      var s = SORC_STANCE[el], bonus = el === "fire" ? 0.04 + lod : el === "energy" ? (0.04 + lod) * 0.5 : 0.1 * (0.3 + [0, 0.15, 0.225, 0.3][stage]);
      return { n: s[0], w: s[1], lane: el, el: el, bonus: bonus, mod: {},
        why: "Converte o feitiço seguinte de outro elemento em " + ELN[el] + ": a rotação inteira bate em " + ELN[el] + "." +
          (el === "fire" ? " E +" + Math.round(100 * (0.04 + lod)) + "% de base power no fogo." : el === "energy" ? " E +" + Math.round(100 * (0.04 + lod)) + "% de crítico na energia." : " E mais dano crítico na morte.") };
    });
    if (voc === "monk") {
      var j = serene ? 1.16 : 1.08, asc = [0, 0.01, 0.02, 0.03][stage];
      return [
        { n: "Virtue of Harmony", w: "utori virtu", mod: {}, harm: { base: 0.07 + (serene ? 0.06 : 0.03) + asc, refund: 1 },
          why: "Bónus base da Harmony " + Math.round(100 * (0.07 + (serene ? 0.06 : 0.03) + asc)) + "% (×16 com 5 pontos) e cada spender devolve 1 ponto." },
        { n: "Virtue of Justice", w: "utito virtu", mod: { sk: j }, harm: { base: 0.07 + asc, refund: 0 },
          why: "+" + Math.round(100 * (j - 1)) + "% de fist em todos os golpes" + (party ? " e bónus para a party (sorcerer +6% de dano, paladin +6% nos ataques automáticos)." : ".") }];
    }
    return [{ n: "", mod: {} }];
  }

  function solve(D, voc, K, ln, sto, S, gk, eff, scen, stage, pots, share, capMax, cap, serene, opt) {
    var laneMult = mult(eff, ln.el), boss = scen === "boss";
    var cand = [], opener = [], out = [];
    K.forEach(function (a) {
      var el = a.el, sameLane = el === ln.el, conv = false;
      if (a.dot) {   // DoTs: só feitiços (as runas de DoT fazem muito pouco) e só no boss, se a criatura não levar menos desse elemento
        if (boss && a.kind === "spell" && mult(eff, el) >= laneMult - 1e-9) opener.push({ a: a });
        return;
      }
      if (boss && BOSS_SKIP[a.n] && !opt.forkBoss) { out.push({ a: a, why: "boss" }); return; }
      if (a.own && !sameLane) {
        var mixOk = opt.mix && eff && mult(eff, el) >= laneMult - 1e-9;   // misturar só com a criatura conhecida e a pedido
        if (voc === "sorcerer" && !mixOk && !sto.none) conv = true;  // sai convertido no elemento da linha (com a stance)
        else if (!mixOk && LANES[voc].some(function (x) { return x.el === el; })) { out.push({ a: a, why: "lane" }); return; }
        else if (mult(eff, el) < laneMult - 1e-9) { out.push({ a: a, why: "resist" }); return; }
      }
      if (!a.own && !sameLane && mult(eff, el) < laneMult - 1e-9) { out.push({ a: a, why: "resist" }); return; }
      var effEl = conv ? ln.el : el;
      var h = a.hst && stage ? a.hst[stage - 1][gk] : a.h[gk];
      if (!h) { out.push({ a: a, why: "geo" }); return; }
      var bp = a.bp * (a.x || 1);
      var w = a.wh || {};
      if (w.bpx && stage) bp *= w.bpx[stage - 1];
      if (w.twin && stage) bp *= 1 + w.twin[stage - 1] * (boss ? 0.4 : 1);   // Twin Bursts: alvos acima de 60% de vida
      var cd = w.cd && stage ? w.cd[stage - 1] : a.cd;
      var aa = Object.assign({}, a, { cd: cd, cd2: a.g2 ? (w.cd && stage ? w.cd[stage - 1] : a.cd2) : 0 });
      var sc = scaleFor(a, voc, S) * (sto.mod.dmg || 1);
      if (sto.el && effEl === sto.el && sto.bonus) sc *= 1 + sto.bonus;
      var per = bp * sc * mult(eff, effEl);            // dano por alvo
      cand.push({ a: aa, v: per * h, per: per, hits: h, gold: 0, conv: conv, lane: sameLane && a.own, effEl: effEl });
    });
    if (!cand.length) return null;
    var harm = sto.harm ? { base: sto.harm.base, refund: sto.harm.refund, echo: (D.ab["Spiritual Outburst"].wh.echo || [0])[Math.max(0, stage - 1)] } : null;
    var mage = voc === "sorcerer" || voc === "druid";
    var tier = voidTier(opt.level), nVoid = mage ? 2 : 1, leech = D.imbs.void.v[tier] / 100 * nVoid;
    cand.forEach(function (c) { c.leech = c.per * leech * (0.1 * c.hits + 0.9); });   // mana leech (TibiaWiki, Formulae)
    // uma solução por poção (a mais barata por mana dá menos mana por segundo); fica a de mais dano e, empatadas, a mais barata
    var best = null;
    (pots.length ? pots : [null]).forEach(function (p) {
      var r = lpRates(cand, harm, p, share, cap);
      if (r && (!best || r.dps > best.dps * 1.0005 || (r.dps > best.dps * 0.9995 && r.gph < best.gph))) best = r;
    });
    if (!best) return null;
    best.sim = sequence(cand, best, harm, cap, share);
    return { lane: ln, stance: sto, cand: cand, opener: opener, out: out, lp: best, sim: best.sim, harm: harm, tier: tier, nVoid: nVoid, leech: leech, S: S, dps: best.dps };
  }

  // ---------- programação linear: as taxas ótimas (lançamentos por segundo) ----------
  // max c·x com A·x ≤ b, x ≥ 0 e b ≥ 0 (a base inicial são as folgas). Simplex com a regra de Bland (sem ciclos).
  function simplex(c, A, b) {
    var m = A.length, n = c.length, T = [], basis = [], i, j;
    for (i = 0; i < m; i++) {
      var row = A[i].slice();
      for (j = 0; j < m; j++) row.push(i === j ? 1 : 0);
      row.push(b[i]); T.push(row); basis.push(n + i);
    }
    var z = c.map(function (v) { return -v; }); for (j = 0; j < m; j++) z.push(0); z.push(0);
    for (var it = 0; it < 500; it++) {
      var e = -1;
      for (j = 0; j < n + m; j++) if (z[j] < -1e-9) { e = j; break; }
      if (e < 0) break;
      var l = -1, bestR = Infinity;
      for (i = 0; i < m; i++) if (T[i][e] > 1e-12) {
        var ratio = T[i][n + m] / T[i][e];
        if (ratio < bestR - 1e-12 || (Math.abs(ratio - bestR) <= 1e-12 && basis[i] < basis[l])) { bestR = ratio; l = i; }
      }
      if (l < 0) return null;                                   // sem limite (não acontece: o grupo de ataque limita tudo)
      var pv = T[l][e];
      for (j = 0; j <= n + m; j++) T[l][j] /= pv;
      for (i = 0; i < m; i++) if (i !== l && T[i][e]) { var f = T[i][e]; for (j = 0; j <= n + m; j++) T[i][j] -= f * T[l][j]; }
      if (z[e]) { var fz = z[e]; for (j = 0; j <= n + m; j++) z[j] -= fz * T[l][j]; }
      basis[l] = e;
    }
    var x = new Array(n).fill(0);
    for (i = 0; i < m; i++) if (basis[i] < n) x[basis[i]] = T[i][n + m];
    return { x: x, z: z[n + m] };
  }

  // variáveis: um x por feitiço/runa (spenders do monk: um por nível de Harmony 1–5) e y = mana comprada por segundo
  function lpRates(cand, harm, pot, share, cap) {
    var cols = [];
    cand.forEach(function (c) {
      if (harm && c.a.role === "S") for (var h = 1; h <= 5; h++) {
        var v = c.v * (1 + harm.base * Math.pow(2, h - 1));
        if (c.a.n === "Spiritual Outburst" && h === 5) v *= 1 + harm.echo;
        cols.push({ c: c, h: h, v: v });
      } else cols.push({ c: c, h: 0, v: c.v });
    });
    var n = cols.length, Y = n, gpm = pot ? pot.gpm : 0, A = [], b = [];
    function row() { return new Array(n + 1).fill(0); }
    var r = row(); cols.forEach(function (k, j) { r[j] = k.c.a.gcd; }); A.push(r); b.push(1);          // grupo de ataque
    var seen = {};
    cols.forEach(function (k) {                                                                      // cooldown próprio
      if (seen[k.c.a.n]) return; seen[k.c.a.n] = 1;
      var r2 = row(); cols.forEach(function (q, j) { if (q.c.a.n === k.c.a.n) r2[j] = 1; }); A.push(r2); b.push(1 / k.c.a.cd);
    });
    var groups = {};
    cols.forEach(function (k) { var g = k.c.a.g2; if (g) groups[g] = Math.max(groups[g] || 0, k.c.a.cd2 || k.c.a.cd); });
    Object.keys(groups).forEach(function (g) {                                                         // grupos secundários
      var r3 = row(); cols.forEach(function (q, j) { if (q.c.a.g2 === g) r3[j] = 1; }); A.push(r3); b.push(1 / groups[g]);
    });
    if (harm) {                                                       // Harmony gasta ≤ Harmony gerada pelos builders
      var r4 = row(); cols.forEach(function (q, j) { r4[j] = q.h ? q.h - harm.refund : (q.c.a.role === "B" ? -1 : 0); }); A.push(r4); b.push(0);
    }
    if (cols.some(function (q) { return q.c.conv; })) {               // sorcerer: cada convertido vem logo a seguir a um da linha
      var r5 = row(); cols.forEach(function (q, j) { r5[j] = q.c.conv ? 1 : q.c.lane ? -1 : 0; }); A.push(r5); b.push(0);
    }
    var r6 = row(); cols.forEach(function (q, j) { r6[j] = q.c.a.m - q.c.leech; }); r6[Y] = -1; A.push(r6); b.push(0);  // mana
    var r7 = row(); r7[Y] = 1; A.push(r7); b.push(pot ? pot.mana * share : 0);                          // poções por segundo
    if (cap < Infinity) {                                                                               // orçamento (gp/s)
      var r8 = row(); cols.forEach(function (q, j) { r8[j] = q.c.a.kind === "rune" ? q.c.a.gp : 0; }); r8[Y] = gpm; A.push(r8); b.push(cap / 3600);
    }
    var eps = 1e-4, obj = cols.map(function (q) { return q.v - eps * (q.c.a.kind === "rune" ? q.c.a.gp : 0); });
    obj.push(-eps * gpm);
    var S = simplex(obj, A, b);
    if (!S) return null;
    var x = S.x, rates = {}, hOf = {}, dps = 0, rune = 0, mana = 0, lee = 0;
    cols.forEach(function (q, j) {
      if (x[j] < 1e-7) return;
      rates[q.c.a.n] = (rates[q.c.a.n] || 0) + x[j];
      if (q.h) hOf[q.c.a.n] = Math.max(hOf[q.c.a.n] || 0, q.h);
      dps += q.v * x[j]; mana += q.c.a.m * x[j]; lee += q.c.leech * x[j];
      if (q.c.a.kind === "rune") rune += q.c.a.gp * x[j];
    });
    var y = x[Y] || 0;
    return { rates: rates, hOf: hOf, dps: dps, mps: mana, leechS: lee, need: y, pot: pot, gph: (rune + y * gpm) * 3600, runeGph: rune * 3600 };
  }

  // ---------- sequência: a rotação a jogar, com as taxas do LP (fichas por feitiço) e os cooldowns ----------
  function sequence(cand, L, harm, cap, share) {
    var gpm = L.pot ? L.pot.gpm : 0, manaCap = L.pot ? L.pot.mana * share : 0;
    var cost = function (a, c) { return (a.kind === "rune" ? a.gp : 0) + Math.max(0, a.m - c.leech) * gpm; };
    var gbank = 0, mbank = manaCap * 4, gRate = cap < Infinity ? cap / 3600 : Infinity;
    var use = cand.filter(function (c) { return L.rates[c.a.n]; });
    use.sort(function (x, y) { return y.v / y.a.gcd - x.v / x.a.gcd; });
    // enchimentos: feitiços (não runas) fora do plano, para os segundos em que os cooldowns não encaixam
    var fill = cand.filter(function (c) { return !L.rates[c.a.n] && c.a.kind !== "rune" && c.a.role !== "S"; });
    fill.sort(function (x, y) { return y.v / y.a.gcd - x.v / x.a.gcd; });
    var T = 300, t = 0, ready = {}, g2r = {}, tok = {}, H = 0, conv = false, dmg = 0, casts = {}, seq = [];
    use.forEach(function (c) { tok[c.a.n] = 1; });
    while (t < T) {
      var pick = null;
      // 1.º com fichas (as taxas do LP); se nada tiver ficha, o melhor do plano que estiver pronto; depois um enchimento
      for (var pass = 0; pass < 3 && !pick; pass++) for (var list = pass < 2 ? use : fill, i = 0; i < list.length && !pick; i++) {
        var c = list[i], a = c.a;
        if ((pass === 0 && tok[a.n] < 1 - 1e-9) || (ready[a.n] || 0) > t + 1e-9 || (a.g2 && (g2r[a.g2] || 0) > t + 1e-9)) continue;
        if (c.conv && !conv) continue;
        if (harm && a.role === "S" && H < (L.hOf[a.n] || 5)) continue;
        if (pass > 0 && gRate < Infinity && cost(a, c) > gbank + 1e-9) continue;     // enchimentos: só com orçamento
        if (a.m - c.leech > mbank + 1e-9) continue;                                   // e com mana das poções
        pick = c;
      }
      var dt = 2;
      if (pick) {
        var a2 = pick.a, v = pick.v;
        if (harm && a2.role === "S") { v *= 1 + harm.base * Math.pow(2, H - 1); if (a2.n === "Spiritual Outburst" && H === 5) v *= 1 + harm.echo; }
        if (gRate < Infinity) gbank -= cost(a2, pick);
        mbank -= Math.max(0, a2.m - pick.leech);
        dmg += v; if (a2.n in tok) tok[a2.n] = Math.max(0, tok[a2.n] - 1); casts[a2.n] = (casts[a2.n] || 0) + 1;
        if (seq.length < 12) seq.push(a2.n);
        ready[a2.n] = t + a2.cd; if (a2.g2) g2r[a2.g2] = t + (a2.cd2 || a2.cd);
        if (harm) { if (a2.role === "B") H = Math.min(5, H + 1); else if (a2.role === "S") H = harm.refund; }
        conv = !!pick.lane; dt = a2.gcd;
      } else conv = false;
      use.forEach(function (c) { tok[c.a.n] = Math.min(2, tok[c.a.n] + L.rates[c.a.n] * dt); });
      if (gRate < Infinity) gbank = Math.min(gbank + gRate * dt, gRate * 30);
      mbank = Math.min(mbank + manaCap * dt, manaCap * 8);
      t += dt;
    }
    return { dps: dmg / T, casts: casts, seq: seq, T: T };
  }

  // ---------- texto e hotkeys ----------
  function nf(x, d) { return (Math.round(x * Math.pow(10, d || 0)) / Math.pow(10, d || 0)).toLocaleString("pt-PT"); }
  function finish(D, voc, L, scen, st, stage, R, alts, eff, budget, cap, pots, share, opt) {
    var lp = R.lp, sim = R.sim, used = R.cand.filter(function (c) { return lp.rates[c.a.n] || sim.casts[c.a.n] >= sim.T / 60; });
    var vOf = function (c) {                       // dano médio de um lançamento (spenders com a Harmony com que o LP gasta)
      var h = lp.hOf[c.a.n], v = c.v;
      if (R.harm && h) { v *= 1 + R.harm.base * Math.pow(2, h - 1); if (c.a.n === "Spiritual Outburst" && h === 5) v *= 1 + R.harm.echo; }
      return v;
    };
    used.sort(function (x, y) { return (!lp.rates[x.a.n]) - (!lp.rates[y.a.n]) || vOf(y) / y.a.gcd - vOf(x) / x.a.gcd; });
    var fillerV = Math.min.apply(null, used.map(function (c) { return vOf(c) / c.a.gcd; }));
    var rot = used.map(function (c) {
      var isFill = !lp.rates[c.a.n], rate = isFill ? sim.casts[c.a.n] / sim.T : lp.rates[c.a.n], cpm = rate * 60;
      var full = !isFill && c.a.cd > c.a.gcd + 1e-9 && rate >= 0.97 / c.a.cd;
      var why = [];
      why.push(nf(c.a.bp * (c.a.x || 1)) + " de base power" + (c.hits > 1.05 ? " × " + nf(c.hits, 1) + " alvos" : ""));
      if (c.conv) why.push("sai em " + ELN[R.lane.el] + " a seguir a um feitiço de " + ELN[R.lane.el]);
      if (full) why.push("lança sempre que sair do cooldown (" + c.a.cd + " s)");
      else if (c.a.cd <= c.a.gcd && rate >= 0.3) why.push("enche os segundos em que o resto está em cooldown");
      else if (cap < Infinity) why.push("o orçamento dá para " + nf(cpm, 1) + " por minuto");
      if (c.a.kind === "rune") why.push(c.a.gp + " gp por runa");
      if (c.a.est) why.push("base power ainda não publicado: assumido igual ao do par holy");
      if (isFill) why.push("enchimento: só nos segundos em que os cooldowns do resto não encaixam");
      if (R.harm && c.a.role === "S") why.push("gasta com " + (lp.hOf[c.a.n] || 5) + " de Harmony (+" + Math.round(100 * R.harm.base * Math.pow(2, (lp.hOf[c.a.n] || 5) - 1)) + "%)");
      if (R.harm && c.a.role === "B") why.push("gera Harmony");
      return { n: c.a.n, w: c.a.w, kind: c.a.kind, cpm: +cpm.toFixed(1), share: Math.round(100 * vOf(c) * rate / Math.max(lp.dps, sim.dps)),
        perCast: Math.round(vOf(c)), full: full, fill: isFill, why: why.join("; ") };
    });
    // o que ficou de fora e porquê
    var outW = [], lanesOut = {};
    R.out.forEach(function (x) {
      var a = x.a;
      if (a.l < L * 0.5 && a.bp < 40) return;                  // feitiços de níveis baixos que já não interessam
      if (x.why === "lane") { (lanesOut[a.el] = lanesOut[a.el] || []).push(a.n); return; }
      else if (x.why === "resist") outW.push({ n: a.n, why: "a criatura leva menos " + ELN[a.el] + " do que " + ELN[R.lane.el] });
      else if (x.why === "boss") outW.push({ n: a.n, why: "num boss só tem um alvo (" + nf(a.bp) + "); com kiting o Burst faz mais por lançamento e controla a zona" });
      else if (x.why === "geo") outW.push({ n: a.n, why: a.mel ? "só bate em monstros colados a ti" : "a área não apanha nada neste cenário" });
    });
    Object.keys(lanesOut).forEach(function (el) {
      outW.unshift({ n: lanesOut[el].join(", "), why: "são de " + ELN[el] + ": ficam na rotação de " + ELN[el] + ", porque a criatura pode levar dano diferente de " + ELN[el] + " e de " + ELN[R.lane.el] });
    });
    var gpm = lp.pot ? lp.pot.gpm : 0;
    R.cand.forEach(function (c) {
      if (lp.rates[c.a.n] || sim.casts[c.a.n] || (c.a.l < L * 0.5 && c.a.bp < 40)) return;
      var per2 = c.v / c.a.gcd;
      if (per2 < fillerV * 0.5) return;                           // muito abaixo do que está na rotação: não vale a pena falar dele
      var gold = (c.a.kind === "rune" ? c.a.gp : 0) + Math.max(0, c.a.m - c.leech) * gpm;
      var r = cap < Infinity && per2 >= fillerV ? "fora do orçamento: " + nf(gold / Math.max(1, c.v) * 1000) + " gp por 1000 de dano"
        : "vale " + nf(per2) + " por segundo de grupo de ataque, menos do que o que já está na rotação";
      outW.push({ n: c.a.n, why: r });
    });
    var opener = R.opener.map(function (c) { return { n: c.a.n, w: c.a.w, why: "dano contínuo durante minutos; lança uma vez no início da luta e volta a lançar quando acabar" }; });
    var notes = [];
    if (stage >= 1 && scen === "boss") {
      var av = { knight: "Avatar of Steel", paladin: "Avatar of Light", sorcerer: "Avatar of Storm", druid: "Avatar of Nature", monk: "Avatar of Balance" }[voc];
      opener.push({ n: av, w: "", why: "todos os ataques são críticos durante o avatar (2 h de recarga): guarda-o para o boss" });
      if (voc === "paladin") opener.push({ n: "Divine Empowerment", w: "utevo grav san", why: "campo 3×3 que sobe o dano 8–12% enquanto estiveres em cima; lança-o quando fores ficar parado" });
    }
    if (scen === "boss") {
      var mages = voc === "sorcerer" || voc === "druid", st3 = famScale(st), dML = 6 * 3 / (st.B + 6 * st.ml + 37);
      if (mages) opener.push({ n: "Mastermind Potion", w: "", why: "+3 ML durante 10 min ≈ +" + nf(100 * dML, 1) + "% de dano: bebe antes do boss" });
      if (voc === "knight") opener.push({ n: "Berserk Potion", w: "", why: "+5 de skill de arma durante 10 min (−10 de shielding)" });
      if (voc === "paladin" && R.stance.n !== "Sharpshooter") opener.push({ n: "Bullseye Potion", w: "", why: "+5 de distance durante 10 min; não acumula com o Sharpshooter" });
    }
    var burst = rot.some(function (r) { return /Burst$/.test(r.n); });
    var line = rot.filter(function (r) { var a = D.ab[r.n]; return a && a.k === "wave"; }).map(function (r) { return r.n; });
    if (scen === "boss" && line.length && !MELEE_VOC[voc]) notes.push("Põe-te na mesma linha ou coluna do boss: " + line.join(", ") + " só lhe acerta assim.");
    if (scen === "boss" && burst) notes.push("Faz kiting a 2–3 casas do boss: o Burst é um anel que não apanha as casas coladas a ti.");
    if (scen === "caixa" && voc === "druid" && stage >= 1) notes.push("Com tudo colado a ti os Bursts não acertam (o anel salta as casas à volta): ficam para pulls em que os monstros chegam a 2–4 casas.");
    if (voc === "sorcerer" && rot.some(function (r) { return R.cand.some(function (c) { return c.a.n === r.n && c.conv; }); }))
      notes.push("Com " + R.stance.n + " ligado, alterna: um feitiço de " + ELN[R.lane.el] + " e logo a seguir o de outro elemento, que sai em " + ELN[R.lane.el] + ".");
    if (voc === "monk" && R.harm) notes.push("Junta 5 de Harmony antes de cada spender: o bónus duplica a cada ponto (" + Math.round(100 * R.harm.base) + "% → " + Math.round(1600 * R.harm.base) + "%)." + (scen === "party" ? " Em party, com 6+ monstros colados e aliados por perto, perdes o Serene." : ""));
    if (!MELEE_VOC[voc] && voc !== "paladin") { /* magos: a wand/rod gera mana e o dano dela é pequeno */ }
    else {
      var Sa = famScale(st, R.stance.mod || {}), auto = Sa.auto / 2 * (R.stance.mod && R.stance.mod.dmg || 1);
      notes.push("O ataque automático (" + (voc === "paladin" ? "munição" : "arma") + ") corre ao lado da rotação sem gastar o grupo de ataque: ≈ " + nf(auto) +
        " de dano por segundo num alvo, " + Math.round(100 * auto / (auto + lp.dps)) + "% do total neste cenário" + (voc === "paladin" ? "; com munição de área sobe nos grupos." : "."));
    }
    var potMana = lp.pot ? lp.pot.mana : 0;
    if (!(voc === "sorcerer" || voc === "druid") && lp.need > 0 && potMana)
      notes.push("A rotação pede " + nf(lp.need) + " de mana por segundo depois do leech: " + Math.round(100 * lp.need / potMana) + "% das poções vão para mana e o resto fica para as de vida.");
    if (lp.leechS >= lp.mps * 0.95 && lp.mps > 0) notes.push("O mana leech do Void paga toda a mana da rotação: as poções de mana ficam só para emergências.");
    var potH = lp.pot && potMana ? lp.need * 3600 / potMana : 0;
    var econ = {
      gpH: Math.round(lp.gph), runesGpH: Math.round(lp.runeGph),
      manaS: +lp.mps.toFixed(1), leechS: +lp.leechS.toFixed(1), needS: +lp.need.toFixed(1),
      potion: lp.pot ? { n: lp.pot.n, perH: Math.round(potH), gpH: Math.round(potH * lp.pot.gp) } : null,
      budget: budget, cap: cap === Infinity ? null : cap,
      dps: Math.round(lp.dps), dpsSeq: Math.round(sim.dps),
      dpsNote: "dano médio por segundo da rotação (estimativa: sem ataques automáticos, críticos nem a armadura da criatura); dpsSeq = o que a sequência simulada consegue com os cooldowns"
    };
    return {
      voc: voc, level: L, scen: scen, scenName: SCN[scen], stats: { ml: st.ml, skill: st.sk, wheel: stage },
      lane: { k: R.lane.k, n: R.lane.n, el: R.lane.el }, alts: alts,
      stance: R.stance.n ? [{ n: R.stance.n, w: R.stance.w, why: R.stance.why }] : [],
      opener: opener, rotation: rot, seq: sim.seq, out: outW.slice(0, 8), econ: econ,
      imbs: imbuements(D, voc, L, st, R, opt), notes: notes
    };
  }

  // imbuements: o que mais rende para a economia e para o dano, com números
  function imbuements(D, voc, L, st, R, opt) {
    var tier = R.tier, TN = ["Basic", "Intricate", "Powerful"], fee = D.imbFee[tier], out = [];
    var price = opt.price || function (k) { return null; };
    function cost(key) {
      var im = D.imbs[key], tot = fee, known = true, ns = [0, 1, 2].slice(0, tier + 1);
      ns.forEach(function (i) { var s = im.src[i]; if (!s) return; var p = price(s[0]); if (p == null) p = s[2]; if (p == null) known = false; else tot += p * s[1]; });
      return { gp20: Math.round(tot), perH: Math.round(tot / 20), floor: !opt.price, known: known };
    }
    var c = cost("void"), leechMana = Math.min(R.lp.leechS, R.lp.mps), gpm = R.lp.pot ? R.lp.pot.gpm : 0.79;
    var saved = leechMana * 3600 * gpm / R.nVoid;   // por imbuement de Void
    out.push({ slot: voc === "sorcerer" || voc === "druid" ? "Capacete e wand/rod" : "Capacete", n: TN[tier] + " Void", must: true,
      why: "mana leech " + D.imbs.void.v[tier] + "% do dano: ≈ " + nf(leechMana / R.nVoid, 1) + " de mana/s, ≈ " + nf(saved / 1000) + "k gp/h de poções poupadas" +
        (c.known ? " contra ≈ " + nf(c.perH / 1000, 1) + "k gp/h de custo" + (c.floor ? " (custo mínimo: materiais ao preço do NPC)" : "") : " (o custo dos materiais depende do Market)"),
      cost: c, savedH: Math.round(saved) });
    var S0 = famScale(st), mage = voc === "sorcerer" || voc === "druid";
    if (mage) {
      var e = [1, 2, 4][tier], dE = 6 * e / (st.B + 6 * st.ml + 37);
      out.push({ slot: "Capacete (2.º slot) / wand", n: TN[tier] + " Epiphany", must: true, why: "+" + e + " ML ≈ +" + nf(100 * dE, 1) + "% de dano em tudo o que a rotação lança", cost: cost("epiphany") });
      out.push({ slot: "Wand/rod (se aceitar)", n: TN[tier] + " Strike", must: false, why: "+5% de chance de crítico com +" + D.imbs.strike.v[tier] + "% de dano ≈ +" + nf(5 * D.imbs.strike.v[tier] / 100, 1) + "% de dano; só algumas wands/rods o aceitam", cost: cost("strike") });
    } else {
      var key = voc === "paladin" ? "precision" : voc === "monk" ? "punch" : "chop", sk = [1, 2, 4][tier];
      var dS = voc === "paladin" ? (2 / 3 * sk) / (2 / 3 * (st.sk + 25) + st.B) : 2.05 * sk / (2.05 * (st.sk + 2 * st.At) + st.B);
      out.push({ slot: "Capacete (2.º slot)", n: TN[tier] + " " + D.imbs[key].n, must: true, why: "+" + sk + " de skill ≈ +" + nf(100 * dS, 1) + "% de dano nos feitiços e ataques", cost: cost(key) });
      out.push({ slot: "Arma", n: TN[tier] + " Vampirism + " + TN[tier] + " Strike", must: true,
        why: "life leech " + D.imbs.vampirism.v[tier] + "%: menos poções de vida, e as poções são as mesmas da mana (exhaust de 1 s); Strike ≈ +" + nf(5 * D.imbs.strike.v[tier] / 100, 1) + "% de dano", cost: cost("vampirism") });
      out.push({ slot: "Armadura", n: TN[tier] + " Vampirism", must: false, why: "mais life leech para aguentar sem gastar a parte das poções que a mana precisa", cost: cost("vampirism") });
    }
    return out;
  }

  function toHK(P) {
    var keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"], g = [];
    if (P.stance.length) g.push({ g: "Stance", k: P.stance.map(function (s, i) { return { k: "Shift+" + (i + 1), c: [s.w], d: s.n + ": " + s.why }; }) });
    if (P.opener.length) g.push({ g: "Abrir a luta", k: P.opener.map(function (s, i) { return { k: "F" + (9 + i), c: [s.w || s.n], d: s.n + ": " + s.why }; }) });
    g.push({ g: "Atacar — " + P.scenName + " (" + P.lane.n + ")", k: P.rotation.map(function (r, i) {
      return { k: keys[i] || "Ctrl+" + (i - 9), c: [r.kind === "rune" ? r.n.replace(/ Rune$/, "") + " (runa)" : r.w], d: r.n + ": " + r.why }; }) });
    return g;
  }
  function toRot(P) {
    return { t: P.scenName + " — " + P.lane.n, seq: P.rotation.map(function (r) { return [r.kind === "rune" ? r.n.replace(/ Rune$/, "") : r.w, r.n]; }),
      why: P.rotation.slice(0, 3).map(function (r) { return r.n + ": " + r.why; }).join(" · ") };
  }

  var API = { _simplex: simplex, plan: plan, toHK: toHK, toRot: toRot, stats: stats, baseDmg: baseDmg, famScale: famScale, wheelStage: wheelStage, ecoCap: ecoCap, LANES: LANES, VOCS: VOCS };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  else root.GrimRot = API;
})(typeof window !== "undefined" ? window : this);
