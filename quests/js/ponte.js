/* Ponte entre o Questski e o Grimório. Os dois sites estão no mesmo endereço e partilham o localStorage:
   - personagem ativa do Grimório (nome, vocação, nível) para o filtro "O meu nível";
   - quests concluídas: uma quest do Questski com par no Grimório (../data/guias.json, q2s) fica feita nos dois,
     na personagem ativa;
   - ligações da wiki do Questski para as páginas do Grimório (itens, criaturas, NPCs, feitiços, conquistas),
     só quando a página existe lá (../data/search.json, o índice da pesquisa do Grimório). */
window.QPonte = (() => {
  "use strict";
  // o pouco CSS da ponte vem com ela (personagem no filtro, link para o Grimório na wiki)
  try { const st = document.createElement("style"); st.id = "ponteCss";
    st.textContent = ".gp-char{display:flex;flex-wrap:wrap;align-items:center;gap:4px 8px;font-size:13px;padding:6px 9px;border-radius:9px;background:color-mix(in srgb,currentColor 7%,transparent)}"
      + ".gp-char a{color:inherit;text-decoration:underline}.gp-voc{font-size:10.5px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:1px 7px;border-radius:999px;border:1px solid currentColor;opacity:.75}"
      + ".gp-nm{min-width:0}.gp-on{font-size:12px}.chip-grim[hidden]{display:none!important}";
    document.head.appendChild(st); } catch (e) { /* sem DOM */ }
  const LS = "grimorio-tibia-v4"; // estado do Grimório (versão 4: {v, active, chars:[{id,name,voc,level,done,...}]})
  const VN = { knight: "Knight", paladin: "Paladin", sorcerer: "Sorcerer", druid: "Druid", monk: "Monk" };
  const GK = { item: ["i", "item"], creature: ["c", "criatura"], npc: ["n", "npc"], spell: ["s", "feitico"], achievement: ["a", "conquista"] };
  const s2q = {};
  let ready = null, SXP = null, SX = null;
  const slug = (s) => String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  const read = () => { try { const d = JSON.parse(localStorage.getItem(LS) || "null"); return d && d.v === 4 && Array.isArray(d.chars) ? d : null; } catch (e) { return null; } };
  const activeOf = (d) => (d && (d.chars.find((c) => c.id === d.active) || d.chars[0])) || null;
  // carrega a ligação quest ↔ guia antes do primeiro desenho (52 KB)
  const load = () => ready || (ready = fetch("../data/guias.json", { cache: "no-cache" }).then((r) => (r.ok ? r.json() : {}))
    .then((g) => { Object.entries((g && g.q2s) || {}).forEach(([id, s]) => { s2q[s] = id; }); }).catch(() => {}));
  function char() { const c = activeOf(read()); return c ? { name: c.name || "", voc: c.voc, vn: VN[c.voc] || c.voc || "", level: +c.level || 0 } : null; }
  function grimDone(sl) { const id = s2q[sl], c = id && activeOf(read()); return !!(c && c.done && c.done[id]); }
  function setGrimDone(sl, v) { const id = s2q[sl], d = read(), c = activeOf(d); if (!id || !c) return false;
    c.done = c.done || {}; if (v) c.done[id] = true; else delete c.done[id];
    try { localStorage.setItem(LS, JSON.stringify(d)); return true; } catch (e) { return false; } }
  const sx = () => SXP || (SXP = fetch("../data/search.json").then((r) => (r.ok ? r.json() : null))
    .then((d) => { SX = {}; ((d && d.e) || []).forEach((e) => { if (Array.isArray(e)) SX[e[0] + "|" + e[1]] = e[2]; }); return SX; }).catch(() => (SX = {})));
  // link para a página do Grimório (ou null se o Grimório não a tem); kind = tipo da página da wiki do Questski
  async function grimHref(kind, title) { const k = GK[kind]; if (!k) return null; await sx(); const n = SX[k[0] + "|" + String(title || "").trim().toLowerCase()];
    return n ? `../#${k[1]}/${slug(n)}` : null; }
  return { load, char, grimDone, setGrimDone, grimHref, paired: (sl) => !!s2q[sl] };
})();
