/* Tibia Questski — modo de visualização Original / Modern, partilhado com o Grimório.
   A escolha fica em localStorage "grimorio-ui" ("modern" ou "original"), a mesma chave do Grimório,
   por isso mudar num site muda no outro. O <head> do index.html já aplica o modo antes de pintar a página;
   aqui ficam o interruptor do rodapé (botões [data-ui-set]) e a sincronização entre separadores. */
(function () {
  "use strict";
  var KEY = "grimorio-ui";
  var FONTS = "https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;500;600;700&family=Russo+One&display=swap";
  var root = document.documentElement;
  var reduce = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };

  function isModern() { return root.getAttribute("data-ui") === "modern"; }

  function loadFonts() {
    if (document.getElementById("mdFonts")) return;
    var l = document.createElement("link");
    l.rel = "stylesheet"; l.id = "mdFonts"; l.href = FONTS;
    document.head.appendChild(l);
  }

  // marca o botão do modo ativo (aria-pressed) no interruptor do rodapé
  function paint() {
    var mode = isModern() ? "modern" : "original";
    var btns = document.querySelectorAll("[data-ui-set]");
    for (var i = 0; i < btns.length; i++) btns[i].setAttribute("aria-pressed", String(btns[i].getAttribute("data-ui-set") === mode));
  }

  function setUI(mode, remember) {
    mode = mode === "modern" ? "modern" : "original";
    if (mode === "modern") { loadFonts(); root.setAttribute("data-ui", "modern"); }
    else root.removeAttribute("data-ui");
    paint();
    if (remember) { try { localStorage.setItem(KEY, mode); } catch (e) { /* sem armazenamento: fica só nesta página */ } }
  }

  function stored() {
    try { return localStorage.getItem(KEY) === "modern" ? "modern" : "original"; } catch (e) { return isModern() ? "modern" : "original"; }
  }

  document.addEventListener("click", function (e) {
    var b = e.target && e.target.closest ? e.target.closest("[data-ui-set]") : null;
    if (!b) return;
    var mode = b.getAttribute("data-ui-set") === "modern" ? "modern" : "original";
    if ((mode === "modern") === isModern()) { setUI(mode, true); return; }
    var go = function () { setUI(mode, true); };
    // transição suave entre os dois visuais (só onde o browser a suporta e sem "reduzir movimento")
    if (document.startViewTransition && !reduce.matches) { try { document.startViewTransition(go); return; } catch (err) { /* segue sem transição */ } }
    go();
  });

  // mudou noutro separador (Grimório ou Questski): aplica aqui também
  window.addEventListener("storage", function (e) {
    if (e.key === KEY || e.key === null) setUI(stored(), false);
  });
  // ao voltar com o botão "anterior" a página pode vir da cache do browser com o modo antigo
  window.addEventListener("pageshow", function (e) {
    if (e.persisted && (stored() === "modern") !== isModern()) setUI(stored(), false);
  });

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", paint);
  else paint();
})();
