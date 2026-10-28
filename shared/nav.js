/* Grimório + Questski — o menu principal, o mesmo nos dois sites (r31).
   Aqui ficam as secções do menu (SECS), os ícones e as páginas que um visitante sem personagem pode abrir (PUB).
   O Grimório (index.html) desenha o menu com isto e com os seus botões de página; o Questski (quests/) usa GNAV.render,
   que desenha o mesmo menu com links para o Grimório (../#hunts…) e marca "Quests" como a página aberta.
   Carrega-se no <head>, depois do shared/i18n.js. Cada entrada: [id da página, nome] ou [id, nome, endereço] (link para outro site). */
window.GNAV = (function () {
  "use strict";
  var S = function (p) { return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + p + "</svg>"; };
  var IC = {
    inicio: S('<path d="M4 13h6V4H4zM14 20h6v-9h-6zM4 20h6v-3H4zM14 7h6V4h-6z"/>'),
    novidades: S('<path d="M4 5h13v14H6a2 2 0 0 1-2-2z"/><path d="M17 9h3v8a2 2 0 0 1-2 2"/><path d="M8 9h5M8 13h5M8 17h3"/>'),
    hunts: S('<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M1 12h4M19 12h4"/>'),
    bosses: S('<path d="M4 17 3 7l5 4 4-7 4 7 5-4-1 10z"/><path d="M5 21h14"/>'),
    tarefas: S('<path d="M9 5h10M9 12h10M9 19h10"/><path d="M4 5l1 1 2-2M4 12l1 1 2-2M4 19l1 1 2-2"/>'),
    build: S('<path d="M14.5 4.5l5 5L9 20H4v-5z"/><path d="M12 7l5 5"/>'),
    rotacao: S('<path d="M20 12a8 8 0 1 1-3-6.2"/><path d="M20 4v5h-5"/>'),
    wheel: S('<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3"/><path d="M12 3v6M12 15v6M3 12h6M15 12h6"/>'),
    equip: S('<path d="M8 3l4 2 4-2 4 4-2.5 3v11h-11V10L4 7z"/>'),
    prog: S('<path d="M12 3l2.6 5.6 6 .7-4.5 4.1 1.2 6L12 16.5 6.7 19.4l1.2-6L3.4 9.3l6-.7z"/>'),
    charms: S('<path d="M12 3l2.6 5.6 6 .7-4.5 4.1 1.2 6L12 16.5 6.7 19.4l1.2-6L3.4 9.3l6-.7z"/>'),
    guias: S('<path d="M7 3h11a2 2 0 0 1 2 2v1H9M7 3a2 2 0 0 0-2 2v13a3 3 0 0 0 3 3h10a2 2 0 0 0 2-2v-1H10v1a2 2 0 0 1-4 0"/><path d="M9 8h7M9 12h7"/>'),
    wiki: S('<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 19V5"/><path d="M9 7h6M9 11h6"/>'),
    sistemas: S('<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/>'),
    itens: S('<path d="M5 8h14l-1.5 13h-11z"/><path d="M9 8c0-3.5 1.3-5 3-5s3 1.5 3 5"/>'),
    criaturas: S('<path d="M12 3c4 0 7 3 7 7 0 3-1.5 5-3 6v4H8v-4c-1.5-1-3-3-3-6 0-4 3-7 7-7z"/><circle cx="9.5" cy="10" r="1.2"/><circle cx="14.5" cy="10" r="1.2"/>'),
    feiticos: S('<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>'),
    npcs: S('<circle cx="9" cy="8" r="3.5"/><path d="M2.5 21c.9-3.8 3.4-6 6.5-6s5.6 2.2 6.5 6"/><path d="M14 3h7v5.5h-4l-2.5 2.5V8.5H14z"/>'),
    colecoes: S('<path d="M8 21h8M12 17v4M7 4h10v4a5 5 0 0 1-10 0z"/><path d="M7 6H4a3 3 0 0 0 3 4M17 6h3a3 3 0 0 1-3 4"/>'),
    mais: S('<circle cx="5" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="19" cy="12" r="1.6"/>'),
    calc: S('<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8M8 11h2M12 11h2M16 11h0M8 15h2M12 15h2M8 18h2M12 18h4"/>'),
    defesa: S('<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>'),
    ask: S('<path d="M4 5h16v11H9l-5 4z"/>'),
    perso: S('<circle cx="12" cy="8" r="4"/><path d="M4 21c1-4 4-6 8-6s7 2 8 6"/>'),
    fontes: S('<path d="M10 14a4 4 0 0 0 6 0l3-3a4 4 0 0 0-6-6l-1 1"/><path d="M14 10a4 4 0 0 0-6 0l-3 3a4 4 0 0 0 6 6l1-1"/>')
  };
  var SECS = [
    { id: "inicio", t: "Início", subs: [["inicio", "Início"], ["novidades", "Novidades"]] },
    { id: "hunts", t: "Hunts", subs: [["hunts", "Hunts"], ["bosses", "Bosses"], ["tarefas", "Tarefas"]] },
    { id: "build", t: "Build", subs: [["rotacao", "Rotação e hotkeys"], ["wheel", "Wheel"], ["equip", "Equipamento"]] },
    { id: "prog", t: "Progresso", subs: [["charms", "Charms"], ["guias", "Quests", "quests/"]] },
    { id: "wiki", t: "Wiki", subs: [["sistemas", "Sistemas novos"], ["itens", "Itens"], ["criaturas", "Criaturas"], ["feiticos", "Feitiços"], ["npcs", "NPCs"], ["colecoes", "Coleções"]] },
    { id: "mais", t: "Mais", subs: [["calc", "Calculadoras"], ["defesa", "Defesa"], ["ask", "Perguntar"], ["perso", "Personagens"], ["fontes", "Fontes"]] }
  ];
  // r3-t5: visitante sem personagem: só estas páginas abrem (as outras precisam da personagem e mostram o ecrã de entrada)
  var PUB = ["item", "criatura", "wiki2", "itens", "criaturas", "feiticos", "npcs", "colecoes", "fontes"];
  // cópia das secções (quem a recebe pode filtrar sem mexer nas originais)
  function secs() { return SECS.map(function (s) { return { id: s.id, t: s.t, subs: s.subs.map(function (x) { return x.slice(); }) }; }); }
  // o menu do visitante: Início, Quests, Wiki e Fontes, sem grupos vazios; um grupo com uma só página fica com o nome e o ícone dela
  function guest(list) {
    return list.map(function (s) {
      var subs = s.subs.filter(function (x) { return x[0] === "inicio" || x[2] || PUB.indexOf(x[0]) >= 0; }); // r31: o Questski (link) também é público
      return subs.length === 1 && subs[0][0] !== s.id ? { id: s.id, t: subs[0][1], ic: subs[0][0], subs: subs } : { id: s.id, t: s.t, subs: subs };
    }).filter(function (s) { return s.subs.length; });
  }
  // Questski: o menu do Grimório em links. o = {side, bottom, sub: elementos; base: "../"; cur: id da página aberta ("guias"); guest: sem personagem}
  function render(o) {
    var list = secs().map(function (s) { s.subs = s.subs.filter(function (x) { return x[0] !== "ask"; }); return s; }); // "Perguntar" só existe dentro do Claude
    if (o.guest) list = guest(list);
    var cur = o.cur, base = o.base || "";
    var sec = list.filter(function (s) { return s.subs.some(function (x) { return x[0] === cur; }); })[0] || list[0];
    var href = function (x) { return x[0] === cur ? "#/" : x[2] ? base + x[2] : base + "#" + x[0]; };
    var item = function (x, t) { var on = x[0] === cur; return '<a href="' + href(x) + '"' + (on ? ' aria-current="page"' : "") + ">" + (IC[x[0]] || "") + t + "</a>"; };
    if (o.side) o.side.innerHTML = list.map(function (s) {
      return s.subs.length === 1 ? "<ul><li>" + item(s.subs[0], s.t) + "</li></ul>"
        : '<div class="grp">' + s.t + "</div><ul>" + s.subs.map(function (x) { return "<li>" + item(x, x[1]) + "</li>"; }).join("") + "</ul>";
    }).join("");
    if (o.bottom) o.bottom.innerHTML = list.map(function (s) {
      var on = s === sec, go = s.subs.filter(function (x) { return !x[2]; })[0] || s.subs[0];
      return '<a href="' + (on ? "#/" : href(go)) + '"' + (on ? ' aria-current="page"' : "") + ">" + IC[s.ic || s.id] + "<span>" + s.t + "</span></a>";
    }).join("");
    if (o.sub) o.sub.innerHTML = sec.subs.length > 1 ? '<div class="gseg">' + sec.subs.map(function (x) {
      return '<a href="' + href(x) + '"' + (x[0] === cur ? ' aria-current="page"' : "") + ">" + x[1] + "</a>"; }).join("") + "</div>" : "";
  }
  return { ic: IC, secs: secs, pub: PUB, guest: guest, render: render };
})();
