/* Grimório + Questski — línguas.
   O código e os dados continuam escritos em PT-PT (a língua de origem). Este ficheiro traduz o que aparece no ecrã:
   - a interface (textos fixos, botões, títulos), pelo dicionário i18n/ui.<língua>.js — chaves exatas e modelos com {0}, {1}…;
   - o conteúdo do Grimório (notas, rotas, descrições), frase a frase, pelo dicionário i18n/content.en.js (só inglês;
     as outras línguas mostram o conteúdo em inglês e o PT-BR fica com o PT-PT);
   - os dados do Questski (guias, fichas de locais), por sobreposições em i18n/en/q/… aplicadas quando o JSON chega.
   Nada na lógica dos sites muda: os dados ficam em PT-PT na memória e só o DOM (texto e title/placeholder/aria-label/alt) é traduzido.
   A língua fica em localStorage "grimorio-lang" (a mesma nos dois sites). Por omissão: inglês.
   Carrega-se no <head>, antes de tudo: <script src="shared/i18n.js" data-c></script> (data-c = dicionário de conteúdo do Grimório,
   data-q = sobreposições do Questski). Ferramenta: _dev/i18n.py (extrair, construir, ver o que falta). */
(function () {
  "use strict";
  var KEY = "grimorio-lang", SRC = "pt-PT", DEF = "en";
  // [código, nome na própria língua, locale para números e datas]
  var LANGS = [
    ["en", "English", "en-GB"],
    ["pt-PT", "Português (Portugal)", "pt-PT"],
    ["pt-BR", "Português (Brasil)", "pt-BR"],
    ["pl", "Polski", "pl-PL"],
    ["es", "Español", "es-ES"],
    ["de", "Deutsch", "de-DE"],
    ["sv", "Svenska", "sv-SE"],
    ["nl", "Nederlands", "nl-NL"]
  ];
  var BYCODE = {};
  LANGS.forEach(function (l) { BYCODE[l[0]] = l; });

  var me = document.currentScript;
  var BASE = me && me.src ? me.src.replace(/shared\/i18n\.js(?:[?#].*)?$/, "") : "";
  var lang = DEF;
  try { var st = localStorage.getItem(KEY); if (st && BYCODE[st]) lang = st; } catch (e) { /* sem armazenamento: inglês */ }
  var ON = lang !== SRC;                                  // traduzir a interface?
  // línguas do conteúdo, por ordem: a escolhida e o inglês de reserva (o PT-BR cai no original PT-PT)
  var CLS = lang === SRC ? [] : lang === "pt-BR" ? ["pt-BR"] : lang === "en" ? ["en"] : [lang, "en"];
  var CL = CLS[0] || null;
  var LOC = BYCODE[lang][2];

  var root = document.documentElement;
  root.setAttribute("lang", lang);

  var I18N = window.I18N = {
    lang: lang, locale: LOC, contentLang: CL, contentLangs: CLS, langs: LANGS, base: BASE, on: ON,
    tr: function (s) { return s; }, now: function () {}, overlay: function (url, d) { return Promise.resolve(d); },
    set: setLang, pickerHTML: pickerHTML
  };

  if (ON) {
    // a página fica escondida até à primeira passagem (sem piscar o português); nunca mais de 2,5 s
    root.classList.add("i18n-hold");
    var hs = document.createElement("style");
    hs.textContent = "html.i18n-hold body{visibility:hidden}";
    document.head.appendChild(hs);
    setTimeout(release, 2500);
    // DV: muda quando os dicionários mudam (i18n/*.js não têm cabeçalho de cache; sem isto o browser podia ficar com os antigos)
    var DV = "?v=20261025b";
    document.write('<script src="' + BASE + "i18n/ui." + lang + '.js' + DV + '"><\/script>');
    CLS.forEach(function (l) {
      if (me && me.hasAttribute("data-c")) document.write('<script src="' + BASE + "i18n/content." + l + '.js' + DV + '"><\/script>');
      if (me && me.hasAttribute("data-q")) document.write('<script src="' + BASE + "i18n/q." + l + '.js' + DV + '"><\/script>');
    });
  }

  function release() { root.classList.remove("i18n-hold"); }

  /* ---------------------------------------------------------------- dicionários */
  var X = null, PATS = null, BUCKET = null, SHORT = [], CONT = null, OUT = new Set();
  var HAS_LETTER = /[A-Za-zÀ-ÖØ-öø-ÿ]/;
  var MARK = /\{(\d+)\}/g;

  function norm(s) { return String(s).replace(/[\s  ]+/g, " ").trim(); }
  function reEsc(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }

  function ready() {
    if (X) return true;
    var d = window.I18N_UI;
    if (!d) return false;
    X = new Map();
    var xs = d.x || {};
    for (var k in xs) if (Object.prototype.hasOwnProperty.call(xs, k)) X.set(k, xs[k]);
    PATS = []; BUCKET = new Map(); SHORT = [];
    (d.p || []).forEach(function (pt) {
      var src = pt[0], parts = src.split(/\{(\d+)\}/), re = "^", slots = [], stat = "";
      // dois valores seguidos (ex.: "Market de {0}{1}", em que {1} é um acrescento opcional): o primeiro fica com tudo e o
      // segundo com o que sobrar (antes ficava "B" + "ona" → "B Marketona")
      for (var i = 0, opt = false; i < parts.length; i++) {
        if (i % 2) {
          var glued = parts[i + 1] === "" && i + 2 < parts.length;
          // um valor logo antes de pontuação (ou no fim) pode vir vazio: é um acrescento opcional (ex.: "…atual{1}. ")
          var optEnd = !glued && /^(?:[.;:,!?)]|$)/.test(parts[i + 1] || "");
          re += opt || optEnd ? "(.*?)" : glued ? "(.+)" : "(.+?)"; slots.push(+parts[i]); opt = glued;
        }
        else { re += reEsc(parts[i]); stat += parts[i]; }
      }
      var words = stat.match(/[A-Za-zÀ-ÖØ-öø-ÿ]{3,}/g);
      var p = { re: new RegExp(re + "$"), slots: slots, t: pt[1], len: stat.length };
      // sem palavras de 3+ letras (ex.: "{0} em {1}" → "{0} in {1}"): vão para uma lista à parte, só para textos curtos
      if (!words) { if (/[A-Za-zÀ-ÖØ-öø-ÿ]/.test(stat)) { p.nw = (stat.match(/[A-Za-zÀ-ÖØ-öø-ÿ]+/g) || []).length; SHORT.push(p); } return; }
      var anchor = words.reduce(function (a, b) { return b.length > a.length ? b : a; });
      PATS.push(p);
      var b = BUCKET.get(anchor); if (!b) BUCKET.set(anchor, b = []); b.push(p);
    });
    X.forEach(function (v) { OUT.add(norm(v)); });
    conts();
    return true;
  }

  // a mesma função de dispersão que _dev/i18n.py (FNV-1a de 32 bits + djb2, sobre as unidades UTF-16)
  function hkey(s) {
    var a = 2166136261, b = 5381;
    for (var i = 0; i < s.length; i++) {
      var c = s.charCodeAt(i);
      a ^= c; a = Math.imul(a, 16777619) >>> 0;
      b = (Math.imul(b, 33) + c) >>> 0;
    }
    return ("0000000" + a.toString(16)).slice(-8) + ("0000000" + b.toString(16)).slice(-8);
  }

  function exact(k) { var v = X.get(k); return v === undefined ? null : v; }

  // um valor que já é inglês (um nome do jogo ou um texto que já vem traduzido) não conta como português, mesmo com " a " ou " as ":
  // "Marcar 20 Years a Cook como feita", "Slab with a Hyaena — abrir na wiki", "Dá acesso a: Trades with A Sweaty Cyclops (…)"
  // (só com "a"/"as" como palavras que também podiam ser portuguesas: "Entrar no Temple of the Snakes" continua a ser português)
  function enVal(s) {
    if (/[ãõçáéíóúâêôà]/i.test(s)) return false;
    if (!((" " + s + " ").match(PT_FN) || []).every(function (x) { return /^\s(?:a|as)$/i.test(x); })) return false;
    if (/\b(?:the|and|of|with|from|for|to|in|on|at|by|is|are|your)\b|\bas an?\b/i.test(s)) return true;
    var w = s.match(/[A-Za-zÀ-ÖØ-öø-ÿ]{3,}/g);
    return !!w && w.every(function (x) { return /^[A-Z]/.test(x); });
  }
  var PT_FN = /\s(?:de|do|da|dos|das|que|para|com|em|no|na|nos|nas|ao|aos|um|uma|por|pelo|pela|se|os|as|e|a|o|à|é|não|mais|só)(?=\s)/gi;
  function pattern(k, depth) {
    depth = depth || 0;
    var words = k.match(/[A-Za-zÀ-ÖØ-öø-ÿ]{3,}/g);
    if (!words) return null;
    var seen = new Set(), best = null, bm = null;
    for (var i = 0; i < words.length; i++) {
      var b = BUCKET.get(words[i]);
      if (!b) continue;
      for (var j = 0; j < b.length; j++) {
        var p = b[j];
        if (seen.has(p)) continue;
        seen.add(p);
        if (best && p.len <= best.len) continue;
        var m = p.re.exec(k);
        if (m) { best = p; bm = m; }
      }
    }
    if (!best) return null;
    var by = {};
    for (var n = 0; n < best.slots.length; n++) {
      var cap = bm[n + 1], mk = /\{\d+\}/.test(cap), t = mk ? null : exact(cap);
      // um valor que no dicionário só existe com o separador à frente (ex.: "podes usar" de "· podes usar")
      // (ou com o separador já no valor: " · podes usar" em "{0} · nível {1}+{2}")
      if (t == null && !mk) {
        var pre = /^\s*(?:·\s*)?/.exec(cap)[0], core = cap.slice(pre.length), td = exact("· " + core);
        if (td != null) td = td.replace(/^·\s*/, ""); else if (pre) td = exact(core);
        if (td != null) t = pre + td;
      }
      if (t == null) {
        // um valor nunca passa o fim de uma frase (ex.: "{0} por {1}" em "Compra na Loja por 870 Tibia Coins. Não tem addons."),
        // nem várias partes separadas por " · " (ex.: "Market de {0}" em "Market de Bona · média do mês · 36 vendidos"),
        // nem é uma frase portuguesa comprida (ex.: "… menos cooldown por cada alvo …" em "{0} por {1}"): o modelo não serve
        if (/[.!?…]\s+\S/.test(cap) && !/[.!?…]\s/.test(best.t)) return null;
        if (cap.indexOf(" · ") >= 0) {
          // um valor com várias partes só serve se cada parte tiver tradução ("80+ · podes usar"); num modelo sem " · ",
          // também ("Criaturas, pela parte do XP: {0}" com "Mágicos 65% · Mortos-vivos 35%")
          var ps = cap.split(" · ").map(function (x, i) {
            if (!/[A-Za-zÀ-ÖØ-öø-ÿ]{2}/.test(x)) return x;
            var v = exact(x);
            if (v == null && i > 0) { v = exact("· " + x); if (v == null && depth < 3) v = pattern("· " + x, depth + 1); if (v != null) v = v.replace(/^·\s*/, ""); }
            if (v == null && depth < 3) v = pattern(x, depth + 1);
            // (uma lista "Dragões, Demónios" ou um nome do jogo, ex.: a cidade em "Até ao meu nível · Thais · Todas")
            if (v == null) v = commas(x);
            if (v == null && enVal(x)) v = x;
            return v;
          });
          if (!ps.some(function (v) { return v == null; })) t = ps.join(" · ");
          else if (best.t.indexOf(" · ") < 0) return null;
        }
      }
      if (t == null) {
        // (num modelo comprido e específico — 40+ letras fixas — o valor pode ser uma frase, desde que se traduza por inteiro:
        // "; com mais 1 exalted core o risco desce para 50%" na frase da fusão da Forge)
        // (só depois de o tentar traduzir: "ao NPC {0} (hoje em Ankrahmun) por 90,000 gp" em "Vende {0}. Sem dados do Market de {1} agora.")
        var longPT = cap.length > 30 && (cap.match(PT_FN) || []).length >= 2 && best.len < 40 && !enVal(cap);
        // o valor também se procura no conteúdo e nos modelos (ex.: "podes usar" em "Para {0} · level {1}+ · {2}"), mesmo com
        // marcas de elementos (ex.: "ao NPC {0} (hoje em Port Hope) por 1,500 gp"); uma lista "fogo, energia, veneno" traduz-se item a item
        if (cap.length <= 90 && /[A-Za-zÀ-ÖØ-öø-ÿ]{3}/.test(cap)) {
          // (sem o espaço da frente: um acrescento opcional, ex.: " ≈ 15 linhas de loot sem preço." em "…do mapa.{1}")
          var sp = /^\s*/.exec(cap)[0], cr = cap.slice(sp.length);
          if (!mk && conts()) t = cget(hkey(cr));
          if (t == null && depth < 3) t = pattern(cr, depth + 1);
          if (t != null) t = sp + t;
          if (t == null && !mk && cap.indexOf(", ") > 0) {
            var it = cap.split(", "), tr = it.map(function (x) { return exact(x); });
            if (tr.every(function (y) { return y != null; })) t = tr.join(", ");
          }
        }
        if (t == null && longPT) return null;
        // um valor que fica por traduzir e é português (ex.: "Até ao meu" em "{0} nível · {1}"): o modelo não serve
        // (também com marcas de elementos: "41{0}Clique: equipamento · botão direito: trocar item" em "{0} itens · armadura {1}")
        if (t == null && !enVal(cap.replace(MARK, " ")) && (/[ãõçâêô]/i.test(cap) || (cap.replace(MARK, " ").match(PT_FN) || []).length)) return null;
        // num modelo quase só de valores (ex.: "{0} por {1}"), uma palavra minúscula por traduzir é português
        // ("Hunts por cidade{0}" dava "Hunts for cidade")
        if (t == null && best.len <= 6 && !enVal(cap) && /(^|[\s(])[a-zà-ÿ]{3,}/.test(cap.replace(MARK, " "))) return null;
      }
      by[best.slots[n]] = t == null ? cap : t;
    }
    return best.t.replace(/\{(\d+)(!?)\}/g, function (m0, s, hide) { return hide ? "" : by[s] !== undefined ? by[s] : m0; });
  }

  // modelos curtos (só palavras de 1–2 letras, ex.: "{0} em {1}"): só em textos curtos e com valores que não sejam frases
  // portuguesas — um nome ("King"), um número, uma marca de elemento ({0}) ou algo com tradução exata
  function short(k, minw) {
    if (k.length > 60) return null;
    for (var i = 0; i < SHORT.length; i++) {
      var p = SHORT[i];
      if (minw && p.nw < minw) continue;
      var m = p.re.exec(k);
      if (!m) continue;
      var by = {}, ok = true;
      for (var n = 0; n < p.slots.length && ok; n++) {
        var cap = m[n + 1], t = /^\{\d+\}$/.test(cap) ? null : exact(cap);
        // (uma palavra minúscula de 3+ letras que não seja de um nome inglês — "Isle of the Kings" — é português: "Os macacos")
        if (t == null && !/^\{\d+\}$/.test(cap) && !/^[\d\s.,%+\-–×#]+$/.test(cap) && ((" " + cap).match(PT_FN) || cap.length > 30 || /^[a-zà-ÿ]/.test(cap) ||
          (cap.replace(MARK, " ").match(/(^|\s)[a-zà-ÿ]{3,}/g) || []).some(function (w) { return !/^\s?(?:the|and|for|from|with)$/.test(w); }))) ok = false;
        by[p.slots[n]] = t == null ? cap : t;
      }
      if (ok) return p.t.replace(/\{(\d+)(!?)\}/g, function (m0, s, hide) { return hide ? "" : by[s] !== undefined ? by[s] : m0; });
    }
    return null;
  }

  // interface: chave exata, depois modelos
  // (os modelos curtos só entram em textos com marcas de elementos, ex.: "King em {0}" de "King em <b>Hill</b>"; num texto
  // simples, "{0} de {1}" apanharia tudo — "Grimório de Tibia" passava a "Grimório of Tibia")
  function ui(k) { var t = exact(k); if (t == null) t = pattern(k); if (t == null && /\{\d+\}/.test(k)) t = short(k); return t; }

  // conteúdo (só inglês): o texto inteiro, senão frase a frase (as frases que faltam ficam em PT-PT).
  // Devolve {t, map}: map = [início, fim] de cada frase na origem e na tradução (para voltar a pôr os ícones no sítio).
  function SENT(s) { return s.split(/(?<=[.!?…:;])\s+(?=\S)/); }
  // dicionários de conteúdo: carregam depois do da interface (o observador pode arrancar entre os dois), por isso vê-se outra vez até chegarem
  function conts() {
    if (CONT || !CLS.length) return CONT;
    var cm = window.I18N_C || {}, ms = CLS.map(function (l) { return cm[l]; }).filter(Boolean);
    if (ms.length < CLS.length && document.readyState === "loading") return null;
    if (!ms.length) return null;
    CONT = ms;
    CONT.forEach(function (m) { for (var h in m) OUT.add(m[h]); });
    return CONT;
  }
  function cget(h) { for (var i = 0; i < CONT.length; i++) { var v = CONT[i][h]; if (v != null) return v; } return null; }
  function content(p) {
    if (!conts()) return null;
    var t = cget(hkey(p));
    if (t != null) return { t: t, map: [[0, p.length, 0, t.length]], full: true };
    var ss = SENT(p);
    if (ss.length < 2) return null;
    var hit = 0, out = "", map = [], pos = 0;
    for (var i = 0; i < ss.length; i++) {
      var s = ss[i], at = p.indexOf(s, pos), v = cget(hkey(s));
      pos = at + s.length;
      if (v == null && !OUT.has(s)) v = ui(s);
      if (v != null) hit++; else { miss(s); v = s; }
      if (out) out += " ";
      map.push([at, at + s.length, out.length, out.length + v.length]);
      out += v;
    }
    return hit ? { t: out, map: map, full: hit === ss.length } : null;
  }

  // lista curta separada por vírgulas (ex.: "Imune a paralisia, invisível"): só se cada item tiver tradução
  function commas(k) {
    if (k.indexOf(", ") < 0 || k.length > 120) return null;
    var it = k.split(", ");
    if (it.some(function (x) { return x.length > 40 || /[.;:!?]/.test(x); })) return null;
    var tr = it.map(function (x) { var v = OUT.has(x) ? x : exact(x); if (v == null) v = pattern(x); return v; });
    return tr.every(function (v) { return v != null; }) ? tr.join(", ") : null;
  }

  // partes ligadas por " + " (ex.: as gemas "Resistência a terra + Vida + Fierce Berserk: dano base"): só se cada uma tiver tradução
  function pluses(k) {
    if (k.indexOf(" + ") < 0 || k.length > 200) return null;
    var tr = k.split(" + ").map(function (x) {
      if (!/[A-Za-zÀ-ÖØ-öø-ÿ]{2}/.test(x) || OUT.has(x)) return x;
      var v = exact(x); if (v == null) v = pattern(x);
      return v == null && enVal(x) ? x : v;
    });
    return tr.every(function (v) { return v != null; }) ? tr.join(" + ") : null;
  }

  // partes separadas por " · " (ex.: "Amuleto · todas as vocações"): cada uma à parte
  function dots(k) {
    var parts = k.split(" · ");
    if (parts.length < 2) return null;
    // várias partes seguidas podem estar juntas no dicionário (ex.: "Piso 0 · térreo" em "32849, 32136, 7 · Piso 0 · térreo"):
    // essas ficam já traduzidas (pre[i]) e as outras traduzem-se uma a uma
    var units = [], pre = [];
    for (var a = 0; a < parts.length; a++) {
      var got = null, z;
      for (z = Math.min(parts.length - 1, a + 3); z > a && got == null; z--) {
        if (a === 0 && z === parts.length - 1) continue;
        var g = parts.slice(a, z + 1).join(" · ");
        if (!OUT.has(g)) got = exact(g);
        if (got != null) { units.push(got); pre[units.length - 1] = true; a = z; }
      }
      if (got == null) units.push(parts[a]);
    }
    var hit = 0, out = units.map(function (p, i) {
      if (pre[i]) { hit++; return p; }
      var v = OUT.has(p) ? null : ui(p);
      // as partes do meio/fim também podem estar no dicionário com o separador à frente (ex.: "· podes usar")
      if (v == null && i > 0) { var vd = ui("· " + p); if (vd != null) v = vd.replace(/^·\s*/, ""); }
      if (v == null) { var c = content(p); v = c && c.t; }
      if (v != null) { hit++; return v; }
      return p;
    });
    return hit ? out.join(" · ") : null;
  }

  // um texto sem marcas → tradução ou null: interface, conteúdo, partes com " · "
  function text(k) {
    if (OUT.has(k)) return null;
    // a frase inteira no dicionário do conteúdo vem antes dos modelos (um modelo curto como "{0} por {1}" estragava-a)
    var t = exact(k);
    if (t != null) return t;
    // com maiúscula à frente de uma chave em minúsculas (ex.: "Dreno de mana" de "dreno de mana")
    if (k.length <= 40 && /^[A-ZÀ-Ö]/.test(k)) {
      t = exact(k.charAt(0).toLowerCase() + k.slice(1));
      if (t != null) return t.charAt(0).toUpperCase() + t.slice(1);
    }
    if (conts()) { var cf = cget(hkey(k)); if (cf != null) return cf; }
    t = ui(k);
    if (t != null) return t;
    var c = content(k);
    // (só em parte, num texto com " · ": as partes traduzem-se melhor à parte — "ligação elemental: energia · def 20 · +2 ML"
    // partia-se no ":" e ficava "elemental bond: energia · …")
    if (c && (c.full || k.indexOf(" · ") < 0)) return c.t;
    // num texto simples só os modelos curtos com 2+ palavras fixas (ex.: "Só as de {0} ({1})"), nunca "{0} de {1}"
    t = short(k, 2);
    if (t == null) t = dots(k);
    if (t == null && c) return c.t;
    if (t == null) t = commas(k);
    if (t == null) t = pluses(k);
    return t != null ? t : edgeSep(k);
  }

  // um separador nas pontas (ex.: "neutro · " antes de um <span>, "· podes usar", "Desbloqueia:"): traduz-se o miolo
  function edgeSep(k) {
    var m = /^([·:;,–—(]\s*)?(.*?)(\s*[·:;,–—)])?$/.exec(k);
    if (!m || (!m[1] && !m[3]) || !/[A-Za-zÀ-ÖØ-öø-ÿ]{3}/.test(m[2])) return null;
    var v = OUT.has(m[2]) ? null : text(m[2]);
    return v == null ? null : (m[1] || "") + v + (m[3] || "");
  }

  function edges(orig, t) {
    var a = /^[\s ]*/.exec(orig)[0], z = /[\s ]*$/.exec(orig)[0];
    return (a ? " " : "") + t + (z && orig.trim() ? " " : "");
  }

  // texto simples (atributos, alert/confirm, chamadas do código)
  function tr(s) {
    if (!ON || s == null) return s;
    s = String(s);
    if (!HAS_LETTER.test(s) || !ready()) return s;
    var k = norm(s);
    if (OUT.has(k)) return s;
    var t = text(k);
    if (t == null) { miss(k); return s; }
    return edges(s, t);
  }

  /* ---------------------------------------------------------------- DOM */
  // sem filhos para traduzir (os atributos, ex. o placeholder de um <input>, traduzem-se na mesma)
  var SKIP = { SCRIPT: 1, STYLE: 1, NOSCRIPT: 1, TEXTAREA: 1, TEMPLATE: 1, INPUT: 1 };
  var INLINE = { A: 1, B: 1, STRONG: 1, I: 1, EM: 1, SPAN: 1, SMALL: 1, KBD: 1, SUP: 1, SUB: 1, ABBR: 1, MARK: 1, U: 1, S: 1, TIME: 1, Q: 1, CITE: 1, CODE: 1, BR: 1, IMG: 1, SVG: 1, VAR: 1, DATA: 1 };
  var BLOCKSEL = "div,p,ul,ol,li,table,section,article,header,footer,nav,aside,h1,h2,h3,h4,h5,h6,details,summary,form,fieldset,dl,dt,dd,figure,blockquote,pre,hr,input,select,textarea,button,label";
  var ATTRS = ["title", "placeholder", "aria-label", "alt", "data-copied"];
  var DONEA = new WeakMap();
  // nós de texto que nós próprios escrevemos (traduzidos) e os que já se tentou sem sucesso: não voltam a ser vistos
  // enquanto o texto for o mesmo (o código pode mudá-lo e aí traduz-se outra vez)
  var MINE = new WeakMap(), TRIED = new WeakMap();
  function mine(n) { return MINE.get(n) === n.data; }
  function tried(n) { return TRIED.get(n) === n.data; }
  function mkText(s) { var t = document.createTextNode(s); MINE.set(t, s); return t; }

  function tag(n) { return n.nodeName.toUpperCase(); }
  // translate="no", .notranslate e campos editáveis: nada lá dentro se traduz (nem os atributos)
  function noTr(el) {
    return el.getAttribute("translate") === "no" || (el.classList && el.classList.contains("notranslate")) || el.isContentEditable;
  }
  function skipEl(el) { return SKIP[tag(el)] === 1 || noTr(el); }
  function inlineEl(c) { return INLINE[tag(c)] === 1 && !noTr(c) && !(c.querySelector && c.querySelector(BLOCKSEL)); }
  function transparent(c) {
    if (c.nodeType === 3) return !/\S/.test(c.data);
    if (c.nodeType !== 1) return true;
    var t = tag(c);
    return t === "SVG" || t === "IMG";
  }

  function attrs(el) {
    for (var i = 0; i < ATTRS.length; i++) {
      var a = ATTRS[i], v = el.getAttribute(a);
      if (!v || !HAS_LETTER.test(v)) continue;
      var d = DONEA.get(el);
      if (d && d[a] === v) continue;
      var t = OUT.has(norm(v)) ? v : tr(v);
      if (!d) DONEA.set(el, d = {});
      d[a] = t;
      if (t !== v) el.setAttribute(a, t);
    }
  }

  function textNode(n, quiet) {
    var s = n.data;
    if (s.length < 2 || !HAS_LETTER.test(s) || mine(n) || tried(n)) return false;
    var k = norm(s), t = text(k);
    if (t == null) { if (!quiet && !OUT.has(k)) miss(k); TRIED.set(n, s); return false; }
    var out = edges(s, t);
    n.data = out;
    MINE.set(n, out);
    return true;
  }

  /* Uma "frase" = texto e elementos em linha seguidos (ex.: "Fala com o <a>NPC</a> em <b>Thais</b>."), entre elementos de bloco.
     1) a interface com {0}, {1}… no lugar dos elementos (que ficam os mesmos: links, chips, ícones);
     2) o conteúdo com o texto dos elementos lá dentro (os elementos voltam a entrar onde aparece o seu texto;
        os ícones sem texto, no início ou no fim da frase onde estavam);
     3) cada pedaço de texto entre elementos, sozinho. */
  function run(el, kids, a, z, inner) {
    while (a <= z && transparent(kids[a])) a++;
    while (z >= a && transparent(kids[z])) z--;
    if (a > z) return;
    var raw = "", plain = "", els = [], offs = [], txt = [], fresh = false;
    for (var i = a; i <= z; i++) {
      var c = kids[i];
      if (c.nodeType === 3) {
        raw += c.data;
        plain = joinN(plain, c.data);
        if (HAS_LETTER.test(c.data)) { txt.push(c); if (!mine(c) && !tried(c)) fresh = true; }
      } else if (c.nodeType === 1) {
        raw += "{" + els.length + "}";
        offs.push(plain.length);
        plain = joinN(plain, c.textContent);
        els.push(c);
      }
    }
    if (!txt.length || !fresh) return;
    if (!els.length) { for (var q = 0; q < txt.length; q++) textNode(txt[q]); return; }
    var k = norm(raw);
    if (OUT.has(k)) return;
    var lead = plain.length - plain.replace(/^ +/, "").length;
    plain = plain.trim();
    // a frase inteira no dicionário do conteúdo passa à frente dos modelos curtos ("Os macacos de {0}." apanhado por "{0} de {1}")
    var t = exact(k), frag = document.createDocumentFragment(), used = [], ct0 = null;
    if (t == null) t = pattern(k);
    if (t == null) { ct0 = conts() ? content(plain) : null; if (ct0 && !ct0.full) ct0 = null; if (!ct0) t = short(k); }
    if (t != null) {
      // {n!} = elemento que esta língua não mostra (ex.: o "s" do plural português): sai da frase
      var bits = t.split(/\{(\d+)(!?)\}/);
      for (var j = 0; j < bits.length; j += 3) {
        if (bits[j]) frag.appendChild(mkText(bits[j]));
        if (j + 1 < bits.length) { var n0 = +bits[j + 1], e = els[n0]; if (e && !used[n0]) { used[n0] = 1; if (!bits[j + 2]) frag.appendChild(e); else e.remove(); } }
      }
    } else {
      // num bloco com elementos, o conteúdo só serve se traduzir todas as frases (senão ficava meia frase em português,
      // ex.: "Dano pelo escudo; corta 50%…" junto ao custo em mana); se não, cada pedaço traduz-se à parte
      var ct = ct0;
      if (!ct) {
        // sem os elementos das pontas (ex.: uma descrição em <span> colada ao fim da frase): só o troço entre o 1.º e o último texto
        if (!inner) {
          var a2 = kids.indexOf(txt[0]), z2 = kids.indexOf(txt[txt.length - 1]);
          if (a2 > a || z2 < z) { var tried0 = txt.map(function (n) { return n.data; }); run(el, kids, a2, z2, true); if (txt.some(function (n, x) { return !n.parentNode || n.data !== tried0[x]; })) return; }
        }
        var any = false;
        for (var w = 0; w < txt.length; w++) if (textNode(txt[w], true)) any = true;
        if (!any) miss(k);
        return;
      }
      // onde entra cada elemento na tradução
      var ins = [], cur = 0;
      els.forEach(function (e, n) {
        var et = norm(e.textContent);
        if (et) {
          var at = ct.t.indexOf(et, cur);
          if (at < 0) { var alt = ui(et); if (alt) { at = ct.t.indexOf(alt, cur); if (at >= 0) et = alt; } }
          if (at >= 0) { ins.push([at, et.length, e, n]); cur = at + et.length; }
          return;
        }
        var o = Math.max(0, offs[n] - lead), pos = ct.t.length;
        for (var m = 0; m < ct.map.length; m++) {
          var mp = ct.map[m];
          if (o <= mp[0]) { pos = mp[2]; break; }
          if (o < mp[1]) { pos = mp[2] + Math.round((o - mp[0]) / Math.max(1, mp[1] - mp[0]) * (mp[3] - mp[2])); break; }
          if (o === mp[1]) { pos = mp[3]; break; }
        }
        ins.push([pos, 0, e, n]);
      });
      ins.sort(function (x, y) { return x[0] - y[0] || x[3] - y[3]; });
      var p0 = 0;
      ins.forEach(function (it) {
        if (it[0] < p0) it[0] = p0;
        if (it[0] > p0) frag.appendChild(mkText(ct.t.slice(p0, it[0])));
        frag.appendChild(it[2]); used[it[3]] = 1;
        p0 = it[0] + it[1];
      });
      if (p0 < ct.t.length) frag.appendChild(mkText(ct.t.slice(p0)));
    }
    els.forEach(function (e, n) { if (!used[n]) { frag.appendChild(mkText(" ")); frag.appendChild(e); } });
    if (/^[\s ]/.test(raw)) frag.insertBefore(mkText(" "), frag.firstChild);
    if (/[\s ]$/.test(raw)) frag.appendChild(mkText(" "));
    var after = kids[z + 1] || null;
    for (var r = a; r <= z; r++) if (kids[r].parentNode === el) el.removeChild(kids[r]);
    el.insertBefore(frag, after && after.parentNode === el ? after : null);
  }
  // junta texto já com os espaços normalizados (um só espaço entre palavras)
  function joinN(acc, s) {
    s = String(s).replace(/[\s  ]+/g, " ");
    return / $/.test(acc) || !acc ? acc + s.replace(/^ /, acc ? "" : " ") : acc + s;
  }

  // as frases diretas deste elemento (os filhos que são blocos tratam-se à parte)
  function runs(el) {
    var kids = Array.prototype.slice.call(el.childNodes), a = 0;
    for (var i = 0; i <= kids.length; i++) {
      var c = kids[i];
      if (i === kids.length || (c.nodeType === 1 && !inlineEl(c))) { if (i > a) run(el, kids, a, i - 1); a = i + 1; }
    }
  }
  function shallow(el) { if (!skipEl(el)) runs(el); }
  // o elemento e tudo o que tem dentro (primeiro as frases dele, depois os filhos: o texto dos elementos em linha
  // ainda está na língua de origem quando se procura a frase inteira)
  function walk(el) {
    if (el.nodeType !== 1 || noTr(el)) return;
    attrs(el);
    if (SKIP[tag(el)] === 1) return;
    runs(el);
    for (var c = el.firstChild; c; c = c.nextSibling) if (c.nodeType === 1) walk(c);
  }

  function blocked(el) {
    for (var e = el; e && e.nodeType === 1; e = e.parentNode) if (skipEl(e)) return true;
    return false;
  }

  // traduzir já (o código chama-o antes de ler o texto de um elemento, ex. os títulos letra a letra do Modern)
  function now(el) {
    if (!ON || !ready()) return;
    el = el || document.documentElement;
    if (el.nodeType === 3) el = el.parentNode;
    if (el && !blocked(el)) walk(el);
  }

  var mo = null;
  function onMut(recs) {
    if (!ready()) return;
    var deep = new Set(), flat = new Set();
    for (var i = 0; i < recs.length; i++) {
      var r = recs[i];
      if (r.type === "attributes") { if (!blocked(r.target)) attrs(r.target); continue; }
      if (r.type === "characterData") { if (r.target.parentNode) flat.add(r.target.parentNode); continue; }
      flat.add(r.target);
      for (var j = 0; j < r.addedNodes.length; j++) if (r.addedNodes[j].nodeType === 1) deep.add(r.addedNodes[j]);
    }
    flat.forEach(function (el) { if (el.nodeType === 1 && el.isConnected && !blocked(el)) shallow(el); });
    deep.forEach(function (el) { if (el.isConnected && !blocked(el)) walk(el); });
    mo.takeRecords();
  }

  function start() {
    if (!ON) return;
    mo = new MutationObserver(onMut);
    mo.observe(root, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ATTRS });
    var go = function () {
      if (ready()) { walk(root); mo.takeRecords(); }
      mountPickers();
      release();
    };
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", go); else go();
    // alert/confirm/prompt do código
    ["alert", "confirm", "prompt"].forEach(function (fn) {
      var o = window[fn];
      if (typeof o !== "function") return;
      window[fn] = function (m) { var a = Array.prototype.slice.call(arguments); a[0] = tr(m); return o.apply(window, a); };
    });
  }

  /* ---------------------------------------------------------------- sobreposições do Questski (JSON) */
  function overlay(url, d) {
    if (!CLS.length) return Promise.resolve(d);
    var qf = window.I18N_QF || {}, rel = String(url).replace(/^\.\//, "").split("?")[0];
    return CLS.reduce(function (pr, l) {
      return pr.then(function () {
        if (!qf[l] || !qf[l][rel]) return;
        return fetch(BASE + "i18n/" + l + "/q/" + rel, { cache: "no-cache" }).then(function (r) { return r.ok ? r.json() : []; }).then(function (ov) {
          for (var i = 0; i < ov.length; i++) {
            var path = ov[i][0], o = d;
            for (var j = 0; j < path.length - 1 && o != null; j++) o = o[path[j]];
            var last = path[path.length - 1];
            if (o != null && typeof o[last] === "string" && hkey(o[last]) === ov[i][1]) o[last] = ov[i][2];
          }
        }).catch(function () {});
      });
    }, Promise.resolve()).then(function () { return d; });
  }

  /* ---------------------------------------------------------------- escolher a língua (rodapé) */
  function pickerHTML() {
    var opts = LANGS.map(function (l) { return '<option value="' + l[0] + '"' + (l[0] === lang ? " selected" : "") + ">" + l[1] + "</option>"; }).join("");
    return '<label class="lang-pick" translate="no"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.6 2.6 3.9 5.6 3.9 9s-1.3 6.4-3.9 9c-2.6-2.6-3.9-5.6-3.9-9S9.4 5.6 12 3z"/></svg>' +
      '<span class="lang-lab">Language</span><select data-lang-set aria-label="Language / Língua / Język / Idioma / Sprache / Språk / Taal">' + opts + "</select></label>";
  }
  function mountPickers() {
    var hosts = document.querySelectorAll("[data-lang-picker]");
    for (var i = 0; i < hosts.length; i++) if (!hosts[i].firstChild) hosts[i].innerHTML = pickerHTML();
  }
  function setLang(l) {
    if (!BYCODE[l] || l === lang) return;
    try { localStorage.setItem(KEY, l); } catch (e) { /* fica só nesta página */ }
    location.reload();
  }
  document.addEventListener("change", function (e) {
    var s = e.target;
    if (s && s.matches && s.matches("[data-lang-set]")) setLang(s.value);
  });
  // mudou noutro separador (Grimório ou Questski): segue
  window.addEventListener("storage", function (e) {
    if (e.key !== KEY) return;
    var l = e.newValue && BYCODE[e.newValue] ? e.newValue : DEF;
    if (l !== lang) location.reload();
  });

  /* ---------------------------------------------------------------- frases em falta (só para quem traduz) */
  var HARV = false, MISS = null, sendT = 0;
  try { HARV = localStorage.getItem("grimorio-i18n-harvest") === "1"; } catch (e) { /* nada */ }
  function miss(k) {
    if (!HARV || !k || k.length < 3) return;
    if (!MISS) MISS = window.__i18nMiss = new Map();
    if (MISS.has(k)) { MISS.get(k).n++; return; }
    MISS.set(k, { n: 1, page: location.pathname + location.hash });
    if (!sendT) sendT = setTimeout(flush, 1500);
  }
  function flush() {
    sendT = 0;
    if (!MISS || !MISS.size) return;
    var rows = []; MISS.forEach(function (v, k) { if (!v.sent) { v.sent = 1; rows.push([k, v.page]); } });
    if (!rows.length) return;
    try { fetch(BASE + "__i18n/miss", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ lang: lang, rows: rows }) }).catch(function () {}); } catch (e) { /* só no servidor local */ }
  }

  I18N.tr = tr; I18N.now = now; I18N.overlay = overlay; I18N.hkey = hkey; I18N.norm = norm;
  // para quem traduz: de onde vem a tradução de um texto (na consola: I18N.why("…"))
  I18N.why = function (s) { if (!ready()) return null; var k = norm(s); return { out: OUT.has(k), exact: exact(k), pattern: pattern(k), content: content(k), text: text(k) }; };
  if (!ON) { if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mountPickers); else mountPickers(); }
  start();
})();
