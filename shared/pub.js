/* Grimório + Questski — publicidade, consentimento e estatísticas (r34).
   Um só ficheiro para os dois sites e para a política. Carrega-se no fim do <body>:
     Grimório:  <script src="shared/pub.js?v=…" defer></script>
     Questski:  <script src="../shared/pub.js?v=…" defer></script>
   Os espaços de anúncio são <div class="ad-slot" data-ad-slot="<nome>"> (inicio, hunts, item, criatura, rodape,
   lateral no Grimório; q-inicio, q-guia, q-rodape no Questski).

   O site vive dos anúncios: TODA a gente vê anúncios. A escolha de cada pessoa é só o tipo:
     personalizados (cookies da Google para escolher anúncios do interesse dela) ou não personalizados/limitados.
   Não há "entrar sem anúncios" nem "sem aceitar não entras": na UE um site não pode exigir cookies para deixar entrar
   (EDPB, diretrizes 05/2020 sobre consentimento), mas pode mostrar anúncios não personalizados a quem não aceita.

   Como ligar (Google AdSense):
     1. CFG.client = o teu código de editor ("ca-pub-…"); o mesmo número no ads.txt da raiz.
     2. CFG.slots = o número de cada unidade de anúncio "de display" que criares no AdSense (uma por espaço).
        Um espaço sem número fica escondido. Enquanto CFG.client estiver vazio, não há anúncios nem aviso.
     3. Consentimento:
        CFG.cmp = "google" (recomendado): no AdSense, Privacidade e mensagens → Regulamentos europeus → mensagem com
          "Consentir" e "Gerir opções", e em Controlo de marca → Publicação de anúncios os "anúncios limitados" ligados.
          É uma mensagem certificada pela Google (TCF): quem consente vê anúncios personalizados; quem não consente vê
          anúncios limitados ou não personalizados. O nosso aviso não aparece.
        CFG.cmp = "proprio": o aviso do próprio site, com "Anúncios personalizados" e "Anúncios não personalizados".
          Os anúncios carregam logo, não personalizados até a pessoa escolher personalizados. Serve enquanto a mensagem
          da Google não está pronta; na Europa a Google pode dar menos anúncios sem a mensagem certificada.
     4. CFG.recuperar = true: mensagem da Google para quem usa bloqueador de anúncios (Privacidade e mensagens →
        Recuperação de bloqueios de anúncios; lá escolhes se a pessoa pode fechar a mensagem ou tem de desbloquear).
   Sem o script da Google (bloqueador, rede), cada espaço mostra um pedido curto para abrir uma exceção ao site.
   A escolha fica em localStorage "grimorio-consent" ({v:2, personal, at}) e volta a ser pedida ao fim de 12 meses.
   O botão "Definições de cookies" (rodapés e política) volta a abrir a escolha nos dois modos.

   Estatísticas: cada página aberta manda ao api/stats.php a rota, o domínio de onde a pessoa veio, a língua e se é
   telemóvel. Sem cookies e sem guardar o IP (ver o cabeçalho do stats.php). Lê-se com _dev/estatisticas.py. */
(function () {
  "use strict";
  var CFG = {
    client: "",            // ex.: "ca-pub-1234567890123456"
    cmp: "google",         // "google" | "proprio"
    recuperar: false,      // mensagem da Google para bloqueadores (ligar também no AdSense)
    slots: {               // número da unidade de anúncio do AdSense, por espaço
      inicio: "", hunts: "", item: "", criatura: "", rodape: "", lateral: "",
      "q-inicio": "", "q-guia": "", "q-rodape": ""
    },
    stats: true,           // contar visitas no api/stats.php
    politica: "privacidade.html" // relativo à raiz do site (o Questski acrescenta "../")
  };
  var KEY = "grimorio-consent", MAXAGE = 365 * 24 * 3600 * 1000;
  var me = document.currentScript;
  var BASE = me && me.src ? me.src.replace(/shared\/pub\.js(?:[?#].*)?$/, "") : "";
  var root = document.documentElement;
  var ON = /^ca-pub-\d{10,20}$/.test(CFG.client);
  var tr = function (s) { return window.I18N && I18N.tr ? I18N.tr(s) : s; };
  function ready(fn) { if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn); else fn(); }

  /* ---------- estatísticas (sem cookies) ---------- */
  if (CFG.stats && navigator.sendBeacon && location.protocol !== "file:") {
    var site = /\/quests\//.test(location.pathname) ? "q" : /privacidade/.test(location.pathname) ? "p" : "g";
    var refHost = "";
    try { var ru = document.referrer && new URL(document.referrer); if (ru && ru.host !== location.host) refHost = ru.hostname; } catch (e) { }
    var mob = matchMedia("(pointer:coarse)").matches && Math.min(screen.width, screen.height) < 820;
    var last = null, firstHit = true;
    var hit = function () {
      // a rota: o que vem depois do #, só as duas primeiras partes (#/quest/<nome>/guia → quest/<nome>)
      var p = location.hash.replace(/^#\/?/, "").split(/[?&]/)[0].split("/").slice(0, 2).join("/");
      if (p === last) return;
      last = p;
      var body = JSON.stringify({ s: site, p: p, r: firstHit ? refHost : "", l: (window.I18N && I18N.lang) || root.lang || "", m: mob ? "m" : "d", f: firstHit ? 1 : 0 });
      firstHit = false;
      try { navigator.sendBeacon(BASE + "api/stats.php", new Blob([body], { type: "text/plain" })); } catch (e) { }
    };
    ready(function () { setTimeout(hit, 1500); }); // depois do primeiro desenho (e das rotas que o site corrige)
    addEventListener("hashchange", function () { setTimeout(hit, 300); });
  }

  /* ---------- escolha ---------- */
  function readConsent() {
    try {
      var c = JSON.parse(localStorage.getItem(KEY) || "null");
      if (c && c.v === 2 && typeof c.personal === "boolean" && Date.now() - c.at < MAXAGE) return c;
    } catch (e) { /* sem armazenamento: pergunta outra vez */ }
    return null;
  }
  function saveConsent(personal) {
    try { localStorage.setItem(KEY, JSON.stringify({ v: 2, personal: personal, at: Date.now() })); } catch (e) { /* só nesta visita */ }
  }

  window.GPUB = { on: ON, cmp: CFG.cmp, consent: readConsent, prefs: openPrefs, policy: BASE + CFG.politica };

  if (!ON) { root.classList.add("pub-off"); ready(wireButtons); return; }
  root.classList.add("pub-on", "pub-ads");

  /* ---------- AdSense ---------- */
  var loaded = false, io = null, blocked = false;
  function loadAds(personal) {
    if (loaded) return;
    loaded = true;
    var q = window.adsbygoogle = window.adsbygoogle || [];
    // modo próprio sem consentimento: anúncios não personalizados (tem de ser antes do primeiro pedido)
    if (CFG.cmp === "proprio" && !personal) q.requestNonPersonalizedAds = 1;
    var s = document.createElement("script");
    s.async = true;
    s.crossOrigin = "anonymous";
    s.src = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=" + encodeURIComponent(CFG.client);
    s.onerror = function () { blocked = true; root.classList.add("pub-blocked"); markBlocked(document); };
    document.head.appendChild(s);
    if (CFG.recuperar) loadRecovery();
    if ("IntersectionObserver" in window) {
      // só pede o anúncio quando o espaço está visível ou perto (poupa os PCs lentos e não pede anúncios escondidos)
      io = new IntersectionObserver(function (es) {
        es.forEach(function (e) { if (e.isIntersecting && e.target.offsetWidth > 0) { io.unobserve(e.target); fill(e.target); } });
      }, { rootMargin: "300px 0px" });
    }
    scan(document);
    new MutationObserver(function (ms) {
      ms.forEach(function (m) { m.addedNodes.forEach(function (n) { if (n.nodeType === 1) scan(n); }); });
    }).observe(document.body, { childList: true, subtree: true });
  }
  function slotsIn(el) {
    return el.matches && el.matches(".ad-slot") ? [el] : el.querySelectorAll ? Array.prototype.slice.call(el.querySelectorAll(".ad-slot")) : [];
  }
  function scan(el) {
    slotsIn(el).forEach(function (a) {
      if (a.dataset.adDone) return;
      a.dataset.adDone = "1";
      if (!CFG.slots[a.getAttribute("data-ad-slot")]) { a.classList.add("ad-none"); return; }
      if (blocked) return markBlocked(a);
      if (io) io.observe(a); else fill(a);
    });
  }
  function fill(a) {
    if (blocked) return markBlocked(a);
    var id = CFG.slots[a.getAttribute("data-ad-slot")];
    var ins = document.createElement("ins");
    ins.className = "adsbygoogle";
    ins.setAttribute("data-ad-client", CFG.client);
    ins.setAttribute("data-ad-slot", id);
    if (a.classList.contains("ad-side")) ins.style.cssText = "display:inline-block;width:160px;height:600px";
    else {
      ins.style.display = "block";
      ins.setAttribute("data-ad-format", "auto");
      ins.setAttribute("data-full-width-responsive", "true");
    }
    var sz = a.querySelector(".ad-size");
    if (sz) sz.remove(); // fica só a etiqueta "Publicidade" por cima do anúncio
    a.appendChild(ins);
    a.classList.add("ad-on");
    try { (window.adsbygoogle = window.adsbygoogle || []).push({}); } catch (e) { /* bloqueador */ }
  }
  // o script da Google não chegou (bloqueador): um pedido simples no lugar do anúncio, sem impedir a leitura
  function markBlocked(el) {
    slotsIn(el.nodeType ? el : document).forEach(function (a) {
      if (a.classList.contains("ad-none") || a.classList.contains("ad-blk")) return;
      a.classList.remove("ad-on");
      a.classList.add("ad-blk");
      a.textContent = "";
      var p = document.createElement("p");
      p.className = "ad-blk-t";
      p.textContent = tr("Os anúncios pagam o servidor do Grimório. Se usas um bloqueador de anúncios, abre uma exceção para este site.");
      a.appendChild(p);
    });
  }
  // a mensagem de recuperação de bloqueios da Google (o código que o AdSense dá, escrito aqui)
  function loadRecovery() {
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://fundingchoicesmessages.google.com/i/" + CFG.client.replace(/^ca-/, "") + "?ers=1";
    document.head.appendChild(s);
    (function signal() {
      if (window.frames.googlefcPresent) return;
      if (!document.body) return setTimeout(signal, 0);
      var f = document.createElement("iframe");
      f.style.cssText = "width:0;height:0;border:none;z-index:-1000;left:-1000px;top:-1000px;display:none";
      f.name = "googlefcPresent";
      document.body.appendChild(f);
    })();
  }

  /* ---------- aviso próprio (CFG.cmp = "proprio") ---------- */
  var box = null;
  function el(tag, cls, txt) { var e = document.createElement(tag); if (cls) e.className = cls; if (txt) e.textContent = tr(txt); return e; }
  function showBanner() {
    if (box) { box.hidden = false; box.querySelector("button").focus(); return; }
    box = el("section", "pub-cc");
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-label", tr("Cookies e publicidade"));
    var h = el("h2", "pub-cc-h", "Cookies e publicidade");
    var p1 = el("p", "pub-cc-p", "O Grimório é gratuito e o servidor paga-se com anúncios, por isso há sempre anúncios. Tu escolhes o tipo.");
    var p2 = el("p", "pub-cc-p", "Personalizados: a Google e os parceiros dela usam cookies para escolher anúncios do teu interesse. Não personalizados: os anúncios dependem só da página que estás a ver.");
    var p3 = el("p", "pub-cc-p", "Podes mudar quando quiseres em Definições de cookies, no rodapé.");
    var row = el("div", "pub-cc-row");
    var yes = el("button", "pub-cc-b pub-cc-yes", "Anúncios personalizados");
    var no = el("button", "pub-cc-b pub-cc-no", "Anúncios não personalizados");
    yes.type = no.type = "button";
    var more = el("a", "pub-cc-a", "Política de privacidade");
    more.href = BASE + CFG.politica;
    yes.onclick = function () { choose(true); };
    no.onclick = function () { choose(false); };
    row.appendChild(yes); row.appendChild(no); row.appendChild(more);
    box.appendChild(h); box.appendChild(p1); box.appendChild(p2); box.appendChild(p3); box.appendChild(row);
    document.body.appendChild(box);
  }
  function choose(personal) {
    var before = readConsent();
    saveConsent(personal);
    if (box) box.hidden = true;
    // os anúncios já pedidos ficaram com o tipo antigo: recarregar aplica o novo a todos
    if (loaded && (before ? before.personal : false) !== personal) location.reload();
    document.dispatchEvent(new CustomEvent("grimorio-consent", { detail: { personal: personal } }));
  }

  /* ---------- mensagem da Google (CFG.cmp = "google") ---------- */
  function googlePrefs() {
    window.googlefc = window.googlefc || {};
    googlefc.callbackQueue = googlefc.callbackQueue || [];
    googlefc.callbackQueue.push({ CONSENT_DATA_READY: function () { googlefc.showRevocationMessage(); } });
  }

  function openPrefs() {
    if (!ON) { location.href = BASE + CFG.politica; return; }
    if (CFG.cmp === "google") googlePrefs(); else showBanner();
  }
  function wireButtons() {
    document.addEventListener("click", function (e) {
      var b = e.target.closest && e.target.closest("[data-pub-prefs]");
      if (b) { e.preventDefault(); openPrefs(); }
    });
    if (!ON) Array.prototype.forEach.call(document.querySelectorAll("[data-pub-prefs]"), function (b) { b.hidden = true; });
  }

  ready(function () {
    wireButtons();
    var c = readConsent();
    loadAds(CFG.cmp === "proprio" && !!(c && c.personal)); // toda a gente vê anúncios, logo à entrada
    if (CFG.cmp === "proprio" && !c) showBanner();
  });
})();
