/* Grimório + Questski — publicidade e consentimento (r34).
   Um só ficheiro para os dois sites. Carrega-se no fim do <body>, depois do resto:
     Grimório:  <script src="shared/pub.js?v=…" defer></script>
     Questski:  <script src="../shared/pub.js?v=…" defer></script>
   Os espaços de anúncio são <div class="ad-slot" data-ad-slot="<nome>">, já espalhados pelas páginas
   (inicio, hunts, item, criatura, rodape, lateral no Grimório; q-guia, q-rodape no Questski).

   Como ligar os anúncios (Google AdSense):
     1. Põe o teu código de editor em CFG.client ("ca-pub-…") e o mesmo número no ads.txt da raiz.
     2. Cria no AdSense uma unidade de anúncio "de display" por espaço e põe o número de cada uma em CFG.slots.
        Um espaço sem número fica escondido.
   Enquanto CFG.client estiver vazio, não há anúncios nem aviso de cookies, e os espaços ficam escondidos.

   Consentimento (RGPD e diretiva ePrivacy):
     CFG.cmp = "proprio": o aviso do próprio site. Nenhum script da Google carrega antes de a pessoa aceitar;
       quem recusa não vê anúncios. A escolha fica em localStorage "grimorio-consent" e volta a ser pedida ao fim de 12 meses.
     CFG.cmp = "google": a mensagem de privacidade do AdSense (Privacidade e mensagens → RGPD), certificada pela Google (TCF).
       Dá anúncios personalizados na Europa, que o aviso próprio não dá. Liga-a primeiro no AdSense; depois muda aqui.
   O botão "Definições de cookies" (rodapés e política) volta a abrir a escolha nos dois modos. */
(function () {
  "use strict";
  var CFG = {
    client: "",            // ex.: "ca-pub-1234567890123456"
    cmp: "proprio",        // "proprio" | "google"
    slots: {               // número da unidade de anúncio do AdSense, por espaço
      inicio: "", hunts: "", item: "", criatura: "", rodape: "", lateral: "",
      "q-guia": "", "q-rodape": ""
    },
    politica: "privacidade.html" // relativo à raiz do site (o Questski acrescenta "../")
  };
  var KEY = "grimorio-consent", MAXAGE = 365 * 24 * 3600 * 1000;
  var me = document.currentScript;
  var BASE = me && me.src ? me.src.replace(/shared\/pub\.js(?:[?#].*)?$/, "") : "";
  var root = document.documentElement;
  var ON = /^ca-pub-\d{10,20}$/.test(CFG.client);
  var tr = function (s) { return window.I18N && I18N.tr ? I18N.tr(s) : s; };

  function readConsent() {
    try {
      var c = JSON.parse(localStorage.getItem(KEY) || "null");
      if (c && c.v === 1 && typeof c.ads === "boolean" && Date.now() - c.at < MAXAGE) return c;
    } catch (e) { /* sem armazenamento: pergunta outra vez */ }
    return null;
  }
  function saveConsent(ads) {
    try { localStorage.setItem(KEY, JSON.stringify({ v: 1, ads: ads, at: Date.now() })); } catch (e) { /* só nesta visita */ }
  }

  window.GPUB = { on: ON, cmp: CFG.cmp, consent: readConsent, prefs: openPrefs, policy: BASE + CFG.politica };

  if (!ON) { root.classList.add("pub-off"); ready(wireButtons); return; }
  root.classList.add("pub-on");

  /* ---------- AdSense ---------- */
  var loaded = false, io = null;
  function loadAds() {
    if (loaded) return;
    loaded = true;
    var s = document.createElement("script");
    s.async = true;
    s.crossOrigin = "anonymous";
    s.src = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=" + encodeURIComponent(CFG.client);
    document.head.appendChild(s);
    root.classList.add("pub-ads");
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
  function scan(el) {
    var list = el.matches && el.matches(".ad-slot") ? [el] : el.querySelectorAll ? el.querySelectorAll(".ad-slot") : [];
    Array.prototype.forEach.call(list, function (a) {
      if (a.dataset.adDone) return;
      a.dataset.adDone = "1";
      if (!CFG.slots[a.getAttribute("data-ad-slot")]) { a.classList.add("ad-none"); return; }
      if (io) io.observe(a); else fill(a);
    });
  }
  function fill(a) {
    var id = CFG.slots[a.getAttribute("data-ad-slot")];
    var side = a.classList.contains("ad-side");
    var ins = document.createElement("ins");
    ins.className = "adsbygoogle";
    ins.setAttribute("data-ad-client", CFG.client);
    ins.setAttribute("data-ad-slot", id);
    if (side) ins.style.cssText = "display:inline-block;width:160px;height:600px";
    else {
      ins.style.display = "block";
      ins.setAttribute("data-ad-format", "auto");
      ins.setAttribute("data-full-width-responsive", "true");
    }
    var sz = a.querySelector(".ad-size");
    if (sz) sz.remove(); // fica só a etiqueta "Publicidade" por cima do anúncio
    a.appendChild(ins);
    a.classList.add("ad-on");
    try { (window.adsbygoogle = window.adsbygoogle || []).push({}); } catch (e) { /* bloqueador de anúncios */ }
  }

  /* ---------- aviso de cookies próprio ---------- */
  var box = null;
  function el(tag, cls, txt) { var e = document.createElement(tag); if (cls) e.className = cls; if (txt) e.textContent = tr(txt); return e; }
  function showBanner() {
    if (box) { box.hidden = false; box.querySelector("button").focus(); return; }
    box = el("section", "pub-cc");
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-label", tr("Cookies e publicidade"));
    var h = el("h2", "pub-cc-h", "Cookies e publicidade");
    var p1 = el("p", "pub-cc-p", "O Grimório é gratuito e paga-se com publicidade. Se aceitares, a Google e os parceiros dela guardam cookies no teu aparelho para mostrar anúncios, medir quantas vezes são vistos e, fora da Europa, escolher anúncios do teu interesse.");
    var p2 = el("p", "pub-cc-p", "Se recusares, não carregamos nenhum anúncio. O site funciona igual. Podes mudar de ideias no rodapé, em Definições de cookies.");
    var row = el("div", "pub-cc-row");
    var yes = el("button", "pub-cc-b pub-cc-yes", "Aceitar");
    var no = el("button", "pub-cc-b pub-cc-no", "Recusar");
    yes.type = no.type = "button";
    var more = el("a", "pub-cc-a", "Política de privacidade");
    more.href = BASE + CFG.politica;
    yes.onclick = function () { choose(true); };
    no.onclick = function () { choose(false); };
    row.appendChild(yes); row.appendChild(no); row.appendChild(more);
    box.appendChild(h); box.appendChild(p1); box.appendChild(p2); box.appendChild(row);
    document.body.appendChild(box);
  }
  function choose(ads) {
    var before = readConsent();
    saveConsent(ads);
    if (box) box.hidden = true;
    if (ads) loadAds();
    else if (loaded || (before && before.ads)) location.reload(); // tirar os scripts da Google já carregados
    document.dispatchEvent(new CustomEvent("grimorio-consent", { detail: { ads: ads } }));
  }

  /* ---------- mensagem da Google (TCF) ---------- */
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
  function ready(fn) { if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn); else fn(); }

  ready(function () {
    wireButtons();
    if (CFG.cmp === "google") { loadAds(); return; }
    var c = readConsent();
    if (c && c.ads) loadAds();
    else if (!c) showBanner();
  });
})();
