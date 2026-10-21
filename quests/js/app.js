/* Tibia Questski — single page app (vanilla JS, hash routing). */
(() => {
  "use strict";

  // ---------------------------------------------------------------- constants
  const MAP = { x0: 31744, y0: 30976, w: 2560, h: 2048 };
  const BANDS = [
    [1, 9, "Nível 1–9", "Primeiros passos"], [10, 19, "Nível 10–19", ""], [20, 29, "Nível 20–29", ""],
    [30, 39, "Nível 30–39", ""], [40, 49, "Nível 40–49", ""], [50, 59, "Nível 50–59", ""],
    [60, 69, "Nível 60–69", ""], [70, 79, "Nível 70–79", ""], [80, 89, "Nível 80–89", ""],
    [90, 100, "Nível 90–100", ""],
    [101, 150, "Rec. 101–150", "Sem requisito acima de 100, mas recomendadas para nível 101–150"],
    [151, 200, "Rec. 151–200", "Sem requisito acima de 100, mas recomendadas para nível 151–200"],
    [201, 99999, "Rec. 200+", "Podes começá-las cedo, mas são para níveis altos"],
  ];
  const CATS = {
    historia: { label: "História", icon: "scroll" },
    tesouro: { label: "Tesouro", icon: "chest" },
    outfit: { label: "Outfit / Addon", icon: "shirt" },
    acesso: { label: "Acesso", icon: "key" },
    tarefas: { label: "Tarefas", icon: "swords" },
    troca: { label: "Troca", icon: "swap" },
    "world-change": { label: "World Change", icon: "globe" },
    evento: { label: "Evento", icon: "spark" },
    tutorial: { label: "Tutorial", icon: "book" },
  };
  const QTABS = [
    ["guia", "Guia passo-a-passo", "scroll"],
    ["preparacao", "Preparação", "bag"],
    ["recompensas", "Recompensas", "gift"],
    ["mapa", "Mapa", "map"],
  ];

  const P = (d) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${d}</svg>`;
  const F = (d) => `<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">${d}</svg>`;
  const ICONS = {
    search: P('<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>'),
    sun: P('<circle cx="12" cy="12" r="4.5"/><path d="M12 2v2.5M12 19.5V22M4.2 4.2l1.8 1.8M18 18l1.8 1.8M2 12h2.5M19.5 12H22M4.2 19.8 6 18M18 6l1.8-1.8"/>'),
    moon: P('<path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5z"/>'),
    menu: P('<path d="M4 6h16M4 12h16M4 18h16"/>'),
    close: P('<path d="M6 6l12 12M18 6 6 18"/>'),
    pin: F('<path d="M12 2a7 7 0 0 0-7 7c0 5.2 7 13 7 13s7-7.8 7-13a7 7 0 0 0-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z"/>'),
    ext: P('<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>'),
    copy: P('<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a1 1 0 0 1 1-1h10"/>'),
    check: P('<path d="m5 12.5 4.5 4.5L19 7.5"/>'),
    checkCircle: F('<path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm-1.3 14.6-4.4-4.4 1.4-1.4 3 3 6-6 1.4 1.4z"/>'),
    circle: P('<circle cx="12" cy="12" r="8.5"/>'),
    lock: P('<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>'),
    skull: F('<path d="M12 2C7 2 3.5 5.6 3.5 10.2c0 2.6 1.1 4.6 3 5.9V19a1 1 0 0 0 1 1h1.6v-2h1.8v2h2.2v-2h1.8v2h1.6a1 1 0 0 0 1-1v-2.9c1.9-1.3 3-3.3 3-5.9C20.5 5.6 17 2 12 2zM8.7 13.6a2 2 0 1 1 0-4 2 2 0 0 1 0 4zm6.6 0a2 2 0 1 1 0-4 2 2 0 0 1 0 4z"/>'),
    star: F('<path d="m12 2.5 2.9 6 6.6.8-4.9 4.6 1.3 6.6L12 17.3l-5.9 3.2 1.3-6.6-4.9-4.6 6.6-.8z"/>'),
    scroll: P('<path d="M7 3h11a2 2 0 0 1 2 2v1H9M7 3a2 2 0 0 0-2 2v13a3 3 0 0 0 3 3h10a2 2 0 0 0 2-2v-1H10v1a2 2 0 0 1-4 0"/><path d="M9 8h7M9 12h7"/>'),
    chest: P('<path d="M3 10h18v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1zM3 10V8a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4v2"/><rect x="10" y="9" width="4" height="5" rx="1"/>'),
    shirt: P('<path d="M8 3 3 6l2 4 2-1v12h10V9l2 1 2-4-5-3c0 1.7-1.3 3-4 3S8 4.7 8 3z"/>'),
    key: P('<circle cx="8" cy="15" r="4"/><path d="m11 12 9-9M16 7l3 3M14 9l2 2"/>'),
    swords: P('<path d="M14.5 17.5 3 6V3h3l11.5 11.5M13 19l6-6M16 16l4 4M19 21l2-2M9.5 6.5 13 3h3v3l-3.5 3.5M5 14l-2 2 2 2 2-2"/>'),
    swap: P('<path d="M4 8h14l-3-3M20 16H6l3 3"/>'),
    globe: P('<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.5 3.8 5.5 3.8 9s-1.3 6.5-3.8 9c-2.5-2.5-3.8-5.5-3.8-9S9.5 5.5 12 3z"/>'),
    spark: F('<path d="M12 2l1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8zM19 15l.9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9z"/>'),
    book: P('<path d="M4 4.5A1.5 1.5 0 0 1 5.5 3H20v15H5.5A1.5 1.5 0 0 0 4 19.5zM4 19.5A1.5 1.5 0 0 0 5.5 21H20"/>'),
    home: P('<path d="M3 11 12 3l9 8M5 9.5V20h5v-6h4v6h5V9.5"/>'),
    map: P('<path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2zM9 4v14M15 6v14"/>'),
    gift: P('<rect x="3" y="8" width="18" height="4" rx="1"/><path d="M5 12v9h14v-9M12 8v13M12 8S9.5 3 7.5 4.5 9 8 12 8zm0 0s2.5-5 4.5-3.5S15 8 12 8z"/>'),
    bag: P('<path d="M5 8h14l-1 13H6zM9 8V6a3 3 0 0 1 6 0v2"/>'),
    warn: P('<path d="M12 3 2 20h20zM12 10v4M12 17.5v.5"/>'),
    bulb: P('<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2V16h5v-.1c0-.8.4-1.5 1-2A6 6 0 0 0 12 3z"/>'),
    trophy: P('<path d="M8 4h8v5a4 4 0 0 1-8 0zM8 6H4a3 3 0 0 0 4 4M16 6h4a3 3 0 0 1-4 4M12 13v4M8 21h8M9 21l1-4h4l1 4"/>'),
    users: P('<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 4.5a3.5 3.5 0 0 1 0 7M18 14a6 6 0 0 1 3.5 6"/>'),
    flag: P('<path d="M5 21V4M5 4h11l-2 4 2 4H5"/>'),
    clock: P('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>'),
    hash: P('<path d="M5 9h14M5 15h14M10 3 8 21M16 3l-2 18"/>'),
    list: P('<path d="M9 6h11M9 12h11M9 18h11M4 6h.5M4 12h.5M4 18h.5"/>'),
    layers: P('<path d="m12 3 9 5-9 5-9-5zM3 13l9 5 9-5"/>'),
    dice: P('<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8" cy="8" r="1"/><circle cx="16" cy="16" r="1"/><circle cx="12" cy="12" r="1"/>'),
    upload: P('<path d="M12 16V4M7 9l5-5 5 5M4 20h16"/>'),
    download: P('<path d="M12 4v12M7 11l5 5 5-5M4 20h16"/>'),
    trash: P('<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>'),
  };
  const icon = (name, cls = "") => `<span class="ico ${cls}">${ICONS[name] || ""}</span>`;

  // ---------------------------------------------------------------- helpers
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const norm = (s) => String(s || "").replace(/[​-‏‪-‮⁠﻿]/g, "").replace(/_/g, " ").trim().toLowerCase();
  const fold = (s) => String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const floorUrl = (z) => `assets/map/floor-${String(z).padStart(2, "0")}-map.png`;
  const floorLabel = (z) => (z === 7 ? "Piso 0 · térreo" : z < 7 ? `Piso +${7 - z}` : `Piso −${z - 7} · subsolo`);

  function load(key, def) {
    try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : def; } catch (e) { return def; }
  }
  function save(key, val) {
    try { localStorage.setItem(key, JSON.stringify(val)); } catch (e) { /* storage unavailable */ }
  }
  let toastTimer;
  function toast(msg) {
    const t = $("#toast");
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove("show"), 1900);
  }
  function copy(text, label) {
    const done = () => toast(label || `Copiado: ${text}`);
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(done, done);
    else {
      const ta = document.createElement("textarea");
      ta.value = text; document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy"); } catch (e) { /* ignore */ }
      ta.remove(); done();
    }
  }

  // ---------------------------------------------------------------- state
  const S = {
    quests: [], bySlug: {}, images: {}, npcs: {}, details: {}, generated: "",
    wiki: { pages: [], byLower: {}, alias: {}, cache: {} }, questByName: {},
    places: {}, placeAlias: {},
    regions: [],
    filters: Object.assign({ q: "", level: null, onlyAvail: false, prem: "all", cats: [], region: "", regionMain: true, hideDone: false, sort: "rec", open: true },
      load("tq-filters", {}), { q: "" }),
    progress: load("tq-progress", {}),
    tabs: load("tq-tabs", []),
    route: { name: "home", args: [] },
  };
  const saveFilters = () => { const f = Object.assign({}, S.filters); delete f.q; save("tq-filters", f); };
  // ponte com o Grimório (js/ponte.js): personagem ativa, quests concluídas nos dois sites, links para as páginas de lá
  const QP = window.QPonte || { load: () => Promise.resolve(), char: () => null, grimDone: () => false, setGrimDone: () => false, grimHref: async () => null, paired: () => false };

  // internal wiki ------------------------------------------------------------
  function wikiEntry(title) {
    if (!title) return null;
    const low = String(title).trim().toLowerCase();
    const canon = S.wiki.byLower[low] || S.wiki.byLower[(S.wiki.alias[low] || "").toLowerCase()];
    return canon || null;
  }
  /** Internal route for a wiki title: our own quest guide if it is a quest, else the wiki page, else null. */
  function wikiHref(title) {
    const low = String(title || "").trim().toLowerCase();
    const q = S.questByName[low] || S.questByName["the " + low];
    if (q) return `#/quest/${q}`;
    const e = wikiEntry(title);
    return e ? `#/wiki/${encodeURIComponent(e.t)}` : null;
  }

  // travel cards for places ------------------------------------------------------
  function placeFor(name) {
    const low = String(name || "").trim().toLowerCase();
    if (!low) return null;
    if (S.places[low]) return S.places[low];
    const a = S.placeAlias[low];
    if (a && S.places[a.toLowerCase()]) return S.places[a.toLowerCase()];
    const e = wikiEntry(name);
    return e ? S.places[e.t.toLowerCase()] || null : null;
  }
  /** Places mentioned in a step: {wiki:Place} tokens and **Place** in bold. */
  function placesInStep(st) {
    const text = [st.title, st.text, st.tip, st.warning].filter(Boolean).join(" ");
    const names = [];
    text.replace(/\{wiki:([^{}|]+)(?:\|[^{}]*)?\}/g, (m, n) => names.push(n));
    text.replace(/\*\*([^*{}]{3,60})\*\*/g, (m, n) => names.push(n));
    const out = [];
    names.forEach((n) => { const p = placeFor(n); if (p && !out.includes(p)) out.push(p); });
    return out;
  }
  function travelBody(p, opts = {}) {
    const list = (arr) => `<ol class="travel-steps">${arr.map((s) => `<li>${rich(s)}</li>`).join("")}</ol>`;
    const imgs = (p.images || []).map((im) => imageFor(im.file) ? { im, f: imageFor(im.file) } : null).filter(Boolean);
    const by = accessBy(p.title);
    return `
      ${p.summary ? `<p class="travel-summary">${rich(p.summary)}</p>` : ""}
      ${by.length ? `<div class="callout reward">${icon("key")}<div><b class="k">Acesso dado por</b>${by.slice(0, 6).map(({ u, q }) => `<a href="#/quest/${q.slug}">${esc(q.name)}</a>${u.when ? ` — ${rich(u.when)}` : ""}`).join("<br>")}</div></div>` : ""}
      ${(p.requirements || []).length ? `<div class="callout tip">${icon("key")}<div><b class="k">Requisitos</b>${p.requirements.map(rich).join("<br>")}</div></div>` : ""}
      <div class="travel-cols">
        <div><h5>${icon("flag")}Como chegar</h5>${list(p.arrive || [])}</div>
        <div><h5>${icon("ext")}Como sair</h5>${list(p.leave || [])}</div>
      </div>
      ${(p.items || []).length ? `<p class="travel-items"><b>Leva:</b> ${p.items.map((i) => renderToken("item", i)).join(", ")}</p>` : ""}
      ${(p.warnings || []).length ? `<div class="callout warn">${icon("warn")}<div><b class="k">Atenção</b>${p.warnings.map(rich).join("<br>")}</div></div>` : ""}
      ${p.entrance || (p.coords || []).length ? `<div class="coords">${[p.entrance ? Object.assign({ main: true }, p.entrance) : null, ...(p.coords || [])].filter(Boolean).slice(0, opts.maxCoords || 4)
        .map((c) => `<div class="coord-card">${minimapHTML(c.x, c.y, c.z, null, c.label)}<div class="coord-info"><span class="label">${rich(c.label || p.title)}</span><span class="xyz">${c.x}, ${c.y}, ${c.z} · ${floorLabel(c.z)}</span>${coordActions(c.x, c.y, c.z, c.label)}</div></div>`).join("")}</div>` : ""}
      ${imgs.length ? `<div class="shots">${imgs.map(({ im, f }) => `<figure class="shot"><img src="${f.src}" alt="${esc(im.caption || im.file)}" loading="lazy">${im.caption ? `<figcaption>${rich(im.caption)}</figcaption>` : ""}</figure>`).join("")}</div>` : ""}`;
  }
  function travelCard(p) {
    const href = wikiHref(p.title);
    return `<details class="travel"><summary>${icon("map")}<span>Como chegar e sair: <b>${esc(p.title)}</b>${p.near ? ` <span class="muted">· perto de ${esc(p.near)}</span>` : ""}</span></summary>
      <div class="travel-body">${travelBody(p, { maxCoords: 3 })}${href ? `<p><a href="${href}">${icon("book")} Página de ${esc(p.title)} na wiki</a></p>` : ""}</div></details>`;
  }

  const sprite = (name) => S.images[norm(name + ".gif")];
  const imageFor = (file) => S.images[norm(file)];
  const spriteImg = (name, cls = "sprite") => {
    const im = sprite(name);
    return im ? `<img class="${cls}" src="${im.src}" alt="" loading="lazy" width="32" height="32">` : "";
  };

  const keyLevel = (q) => (S.filters.sort === "min" ? (q.lvl || 1) : (q.rec || q.lvl || 1));
  const bandIndex = (lv) => Math.max(0, BANDS.findIndex(([a, b]) => lv >= a && lv <= b));
  const bandColor = (i) => `var(--band-${i + 1})`;
  const lvlShield = (q, cls = "") => {
    const lv = q.lvl || 0;
    const i = bandIndex(q.rec || lv || 1);
    const main = lv > 0 ? lv : (q.rec || 1);
    const sub = lv > 0 ? "MÍN" : "REC";
    return `<span class="lvl-shield ${cls}" style="--c:${bandColor(i)}" title="Nível mínimo: ${lv || "—"} · recomendado: ${esc(q.rec_raw || q.rec || "—")}"><span class="lv">${main}<small>${sub}</small></span></span>`;
  };
  const skulls = (n) => n ? `<span class="skulls" title="Dificuldade ${n}/5">${[1, 2, 3, 4, 5].map((i) => icon("skull", i <= n ? "on" : "")).join("")}</span>` : "";
  const premChip = (p) => p === true ? `<span class="chip chip-premium">${icon("star")}Premium</span>` : p === false ? `<span class="chip chip-free">Free</span>` : "";
  const catChip = (c) => CATS[c] ? `<span class="chip chip-cat">${icon(CATS[c].icon)}${CATS[c].label}</span>` : "";

  // progress -----------------------------------------------------------------
  const prog = (slug) => S.progress[slug] || { s: {}, done: false };
  function setProg(slug, p) {
    p.t = Date.now();
    S.progress[slug] = p;
    save("tq-progress", S.progress);
  }
  const stepsDone = (slug) => Object.keys(prog(slug).s || {}).length;
  const isDone = (slug) => !!prog(slug).done || QP.grimDone(slug);
  const pct = (q) => isDone(q.slug) ? 100 : q.steps ? Math.round((stepsDone(q.slug) / q.steps) * 100) : 0;

  // ---------------------------------------------------------------- rich text
  const TOKEN = /\{(npc|item|creature|spell|wiki|key|coord):([^{}]+)\}/g;
  function renderToken(kind, val) {
    const [rawName, shownRaw] = val.split("|");
    const name = rawName.trim();
    const shown = esc((shownRaw || name).trim());
    const href = kind !== "key" && kind !== "coord" ? wikiHref(name) : null;
    const open = (cls, title) => href ? `<a class="${cls}" href="${href}" title="${esc(title)}">` : `<span class="${cls}">`;
    const close = href ? "</a>" : "</span>";
    switch (kind) {
      case "item": case "creature": case "spell":
        return `${open(`ent ent-${kind}`, name + " — abrir na wiki")}${spriteImg(name)}${shown}${close}`;
      case "npc": {
        const pos = S.npcs[name] && S.npcs[name].x != null;
        return `${open("ent ent-npc", name + " — abrir na wiki")}${spriteImg(name)}${shown}${pos ? icon("pin", "pin") : ""}${close}`;
      }
      case "wiki":
        return href ? `<a href="${href}">${shown}</a>` : shown;
      case "key":
        return `<kbd class="say" data-say="${esc(name)}" title="Clica para copiar">${esc(name)}</kbd>`;
      case "coord": {
        const [x, y, z] = name.split(",").map((n) => parseInt(n, 10));
        return `<a class="coord-link" data-coord="${x},${y},${z}" title="Ver no mapa">${icon("pin")} ${x}, ${y}, ${z}</a>`;
      }
    }
    return shown;
  }
  function rich(s) {
    if (s == null || s === "") return "";
    const store = [];
    let out = String(s).replace(TOKEN, (m, kind, val) => { store.push(renderToken(kind, val)); return `\u0000${store.length - 1}\u0000`; });
    out = esc(out)
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|[^*\w])\*(?=\S)(.+?)\*(?!\*)/g, "$1<em>$2</em>")
      .replace(/\n/g, "<br>");
    return out.replace(/\u0000(\d+)\u0000/g, (m, i) => store[+i]);
  }
  const plainText = (s) => String(s || "").replace(TOKEN, (m, k, v) => (v.split("|")[1] || v.split("|")[0]).trim()).replace(/\*/g, "");

  // ---------------------------------------------------------------- data
  async function getJSON(url) {
    const r = await fetch(url, { cache: "no-cache" });
    if (!r.ok) throw new Error(url + " " + r.status);
    return r.json();
  }
  async function loadQuest(slug) {
    if (!S.details[slug]) S.details[slug] = getJSON(`data/quests/${slug}.json`);
    return S.details[slug];
  }

  // ---------------------------------------------------------------- filters
  /** Is the quest about this city? mainOnly = it is the quest's main region; otherwise also quests that pass through it. */
  const inRegion = (q, city, mainOnly) => (mainOnly ? q.region === city : q.region === city || (q.regions || []).includes(city));
  function setRegion(city, mainOnly) {
    S.filters.region = city || "";
    if (mainOnly != null) S.filters.regionMain = !!mainOnly;
    if (!city) S.filters.regionMain = true;
    saveFilters();
    renderFilters();
  }

  function matches(q) {
    const f = S.filters;
    if (f.prem === "free" && q.premium !== false) return false;
    if (f.prem === "premium" && q.premium !== true) return false;
    if (f.cats.length && !f.cats.includes(q.category)) return false;
    if (f.region && !inRegion(q, f.region, f.regionMain)) return false;
    if (f.hideDone && isDone(q.slug)) return false;
    if (f.onlyAvail && f.level && ((q.lvl || 0) > f.level || (q.rec || 0) > f.level + 30)) return false;
    if (f.q) {
      const hay = q._hay || (q._hay = fold([q.name, q.aka.join(" "), q.location, q.region, (q.regions || []).join(" "), (q.unlocks || []).map((u) => plainText(u.what) + " " + (u.place || "")).join(" "), (q.npcs || []).join(" "), (q.rewards || []).join(" "), plainText(q.summary), CATS[q.category]?.label].join(" ")));
      return fold(f.q).split(/\s+/).filter(Boolean).every((w) => hay.includes(w));
    }
    return true;
  }
  const filtered = () => S.quests.filter(matches).sort((a, b) => keyLevel(a) - keyLevel(b) || (a.lvl || 0) - (b.lvl || 0) || a.name.localeCompare(b.name));
  const locked = (q) => S.filters.level && (q.lvl || 0) > S.filters.level;
  function grouped(list) {
    const groups = BANDS.map(() => []);
    list.forEach((q) => groups[bandIndex(keyLevel(q))].push(q));
    return groups;
  }

  function renderFilters() {
    const f = S.filters;
    const regions = S.regions.slice().sort((a, b) => a.name.localeCompare(b.name));
    $("#sidebarFilters").innerHTML = `
      <details class="filters" ${f.open ? "open" : ""}>
        <summary class="filter-summary"><span><b id="fcount"></b></span><span class="link-btn">Filtros</span></summary>
        <div style="margin-top:10px">
          ${(() => { const ch = QP.char(); return ch ? `<div class="filter-row gp-char"><span class="gp-voc">${esc(ch.vn)}</span><span class="gp-nm"><b>${esc(ch.name)}</b> · nível ${ch.level}</span>${f.level === ch.level && f.lvlChar ? `<span class="muted gp-on">nível da tua personagem</span>` : `<button class="link-btn" data-gpchar>usar este nível</button>`}</div>`
            : `<div class="filter-row gp-char muted">Junta a tua personagem no <a href="../#inicio">Grimório</a> e o nível dela entra aqui sozinho.</div>`; })()}
          <div class="filter-row">
            <span class="filter-label">O meu nível</span>
            <input class="input level-input" id="fLevel" type="number" min="1" max="2000" placeholder="ex. 45" value="${f.level || ""}">
            <label class="check" title="Esconde as quests com nível mínimo acima do teu ou recomendadas para mais de 30 níveis acima"><input type="checkbox" id="fAvail" ${f.onlyAvail ? "checked" : ""}> só para o meu nível</label>
          </div>
          <div class="filter-row">
            <div class="seg" role="group" aria-label="Conta">
              ${[["all", "Todas"], ["free", "Free"], ["premium", "Premium"]].map(([v, l]) => `<button data-prem="${v}" class="${f.prem === v ? "on" : ""}">${l}</button>`).join("")}
            </div>
            <div class="seg" role="group" aria-label="Ordenar por">
              <button data-sort="rec" class="${f.sort === "rec" ? "on" : ""}" title="Ordenar pelo nível recomendado">Rec.</button>
              <button data-sort="min" class="${f.sort === "min" ? "on" : ""}" title="Ordenar pelo nível mínimo">Mín.</button>
            </div>
          </div>
          <div class="filter-row cat-pills">
            ${Object.entries(CATS).map(([k, c]) => `<button class="cat-pill ${f.cats.includes(k) ? "on" : ""}" data-cat="${k}">${icon(c.icon)}${c.label}</button>`).join("")}
          </div>
          <div class="filter-row">
            <span class="filter-label">Região</span>
            <select class="input region-select ${f.region ? "on" : ""}" id="fRegion" aria-label="Filtrar por região (cidade)"><option value="">Todas as cidades</option>${regions.map((r) => `<option value="${esc(r.name)}" ${f.region === r.name ? "selected" : ""}>${esc(r.name)} (${f.regionMain ? r.main : r.total})</option>`).join("")}</select>
            ${f.region ? `<button class="link-btn" data-region-clear title="Tirar o filtro de região">✕</button>` : ""}
          </div>
          ${f.region ? `<div class="filter-row"><label class="check" title="Junta as quests de outras regiões que têm passos em ${esc(f.region)} ou nos arredores"><input type="checkbox" id="fRegionAll" ${f.regionMain ? "" : "checked"}> incluir as que só passam por ${esc(f.region)}</label></div>` : ""}
          <div class="filter-row">
            <label class="check"><input type="checkbox" id="fHide" ${f.hideDone ? "checked" : ""}> esconder concluídas</label>
          </div>
          <div class="filter-row filter-summary"><span class="muted">Ordenado por nível ${f.sort === "rec" ? "recomendado" : "mínimo"}</span><button class="link-btn" id="fReset">Limpar filtros</button></div>
        </div>
      </details>`;
  }
  function bindFilters() {
    const box = $("#sidebarFilters");
    box.addEventListener("toggle", (e) => { if (e.target.matches("details")) { S.filters.open = e.target.open; saveFilters(); } }, true);
    box.addEventListener("click", (e) => {
      const b = e.target.closest("button");
      if (!b) return;
      if (b.dataset.prem) S.filters.prem = b.dataset.prem;
      else if (b.dataset.sort) S.filters.sort = b.dataset.sort;
      else if (b.dataset.cat) {
        const c = b.dataset.cat, cats = S.filters.cats;
        S.filters.cats = cats.includes(c) ? cats.filter((x) => x !== c) : cats.concat(c);
      } else if (b.id === "fReset") {
        Object.assign(S.filters, { q: "", level: null, lvlChar: false, onlyAvail: false, prem: "all", cats: [], region: "", regionMain: true, hideDone: false, sort: "rec" });
        $("#search").value = "";
      } else if ("gpchar" in b.dataset) {
        const ch = QP.char(); if (ch && ch.level) { S.filters.level = ch.level; S.filters.lvlChar = true; }
      } else if ("regionClear" in b.dataset) {
        S.filters.region = ""; S.filters.regionMain = true;
      } else return;
      filtersChanged(true);
    });
    box.addEventListener("input", (e) => {
      if (e.target.id === "fLevel") { const v = parseInt(e.target.value, 10); S.filters.level = v > 0 ? v : null; S.filters.lvlChar = false; filtersChanged(false); }
    });
    box.addEventListener("change", (e) => {
      if (e.target.id === "fAvail") S.filters.onlyAvail = e.target.checked;
      else if (e.target.id === "fHide") S.filters.hideDone = e.target.checked;
      else if (e.target.id === "fRegion") { S.filters.region = e.target.value; if (!e.target.value) S.filters.regionMain = true; filtersChanged(true); return; }
      else if (e.target.id === "fRegionAll") { S.filters.regionMain = !e.target.checked; filtersChanged(true); return; }
      else return;
      filtersChanged(false);
    });
  }
  function filtersChanged(rerenderFilterUI) {
    saveFilters();
    if (rerenderFilterUI) renderFilters();
    renderList();
    if (S.route.name === "quests") renderQuestsPage();
    if (S.route.name === "home") renderHome();
  }

  // ---------------------------------------------------------------- sidebar list
  function renderList() {
    const list = filtered();
    $("#fcount") && ($("#fcount").textContent = `${list.length} de ${S.quests.length} quests`);
    const active = S.route.name === "quest" ? S.route.args[0] : null;
    const groups = grouped(list);
    let html = "";
    groups.forEach((g, i) => {
      if (!g.length) return;
      html += `<div class="band-head" style="--c:${bandColor(i)}"><span class="band-dot"></span>${BANDS[i][2]}<span class="count">${g.length}</span></div>`;
      html += g.map((q) => {
        const p = pct(q);
        const sub = [q.region, q.rec_raw ? `rec. ${q.rec_raw}` : null].filter(Boolean).join(" · ");
        return `<a class="qitem ${q.slug === active ? "active" : ""} ${locked(q) ? "locked" : ""}" href="#/quest/${q.slug}" data-slug="${q.slug}">
          ${lvlShield(q)}
          <span class="qi-main"><span class="qi-name">${esc(q.name)}</span><span class="qi-sub">${esc(sub)}</span></span>
          <span class="qi-flags">${(q.unlocks || []).length ? `<span class="key" title="Dá acesso a: ${esc(q.unlocks.map((u) => plainText(u.what)).join(", "))}">${icon("key")}</span>` : ""}${locked(q) ? icon("lock") : ""}${q.premium ? `<span class="prem" title="Premium">${icon("star")}</span>` : ""}${isDone(q.slug) ? `<span class="done" title="Concluída">${icon("checkCircle")}</span>` : ""}</span>
          ${p > 0 && p < 100 ? `<span class="qi-progress"><i style="width:${p}%"></i></span>` : ""}
        </a>`;
      }).join("");
    });
    $("#questList").innerHTML = html || `<div class="empty-list">Nenhuma quest corresponde aos filtros.<br><button class="link-btn" id="fReset2">Limpar filtros</button></div>`;
    const r2 = $("#fReset2");
    if (r2) r2.onclick = () => { $("#fReset")?.click(); };
    const act = $(".qitem.active", $("#questList"));
    if (act) {
      const box = $("#questList"), top = act.offsetTop, h = box.clientHeight;
      if (top < box.scrollTop + 30 || top > box.scrollTop + h - 50) box.scrollTop = top - h / 3;
    }
  }

  // ---------------------------------------------------------------- tabs
  function openTab(slug) {
    if (!S.tabs.includes(slug)) {
      S.tabs.push(slug);
      while (S.tabs.length > 12) S.tabs.splice(S.tabs.findIndex((s) => s !== slug), 1);
      save("tq-tabs", S.tabs);
    }
  }
  function closeTab(slug) {
    const i = S.tabs.indexOf(slug);
    if (i < 0) return;
    S.tabs.splice(i, 1);
    save("tq-tabs", S.tabs);
    if (S.route.name === "quest" && S.route.args[0] === slug) {
      const next = S.tabs[i] || S.tabs[i - 1];
      location.hash = next ? `#/quest/${next}` : "#/";
    } else renderTabs();
  }
  function renderTabs() {
    const active = S.route.name === "quest" ? S.route.args[0] : null;
    const tabs = S.tabs.filter((s) => S.bySlug[s]);
    $("#tabstrip").innerHTML =
      `<a class="tab tab-home ${S.route.name === "home" ? "active" : ""}" href="#/" title="Início">${icon("home")}</a>` +
      `<a class="tab ${S.route.name === "quests" ? "active" : ""}" href="#/quests" title="Todas as quests">${icon("list")}<span class="tab-name">Quests</span></a>` +
      `<a class="tab ${S.route.name === "mapa" ? "active" : ""}" href="#/mapa" title="Mapa">${icon("map")}<span class="tab-name">Mapa</span></a>` +
      `<a class="tab ${S.route.name === "acessos" ? "active" : ""}" href="#/acessos" title="Que quests dão acesso a quê">${icon("key")}<span class="tab-name">Acessos</span></a>` +
      `<a class="tab ${S.route.name === "wiki" ? "active" : ""}" href="#/wiki" title="Wiki">${icon("book")}<span class="tab-name">Wiki</span></a>` +
      tabs.map((s) => {
        const q = S.bySlug[s];
        return `<a class="tab ${s === active ? "active" : ""}" href="#/quest/${s}" data-tab="${s}" role="tab" aria-selected="${s === active}" title="${esc(q.name)}">
          <span class="tab-lvl" style="--c:${bandColor(bandIndex(q.rec || q.lvl || 1))}">${q.lvl || q.rec || 1}</span>
          <span class="tab-name">${esc(q.name.replace(/ Quest$/, ""))}</span>
          <button class="tab-x" data-close-tab="${s}" aria-label="Fechar ${esc(q.name)}">${icon("close")}</button></a>`;
      }).join("") +
      (tabs.length > 1 ? `<button class="link-btn tabs-clear" id="tabsClear">Fechar todas</button>` : "");
    const act = $(".tab.active", $("#tabstrip"));
    if (act) act.scrollIntoView({ block: "nearest", inline: "nearest" });
  }

  // ---------------------------------------------------------------- minimaps (canvas crop of the floor PNG)
  const floorImgs = {};
  function floorImage(z) {
    if (!floorImgs[z]) floorImgs[z] = new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = floorUrl(z); });
    return floorImgs[z];
  }
  function minimapHTML(x, y, z, marks, title) {
    const data = esc(JSON.stringify({ x, y, z, marks: marks || null }));
    return `<div class="minimap" data-mm="${data}" role="button" tabindex="0" title="${esc(title || "Abrir no mapa")}">
      <canvas></canvas><span class="mm-floor">${floorLabel(z)}</span><span class="mm-zoom">${icon("map")} abrir mapa</span></div>`;
  }
  const mmObserver = "IntersectionObserver" in window ? new IntersectionObserver((entries) => {
    entries.forEach((e) => { if (e.isIntersecting) { mmObserver.unobserve(e.target); drawMinimap(e.target); } });
  }, { rootMargin: "300px" }) : null;
  function hydrateMinimaps(root) {
    $$(".minimap[data-mm]", root).forEach((el) => (mmObserver ? mmObserver.observe(el) : drawMinimap(el)));
  }
  async function drawMinimap(el) {
    const d = JSON.parse(el.dataset.mm);
    let img;
    try { img = await floorImage(d.z); } catch (e) { return; }
    const cw = el.clientWidth || 260, ch = el.clientHeight || 173;
    let cx = d.x - MAP.x0 + 0.5, cy = d.y - MAP.y0 + 0.5, s = d.s || 5;
    const pts = (d.marks || []).map((m) => ({ x: m.x - MAP.x0 + 0.5, y: m.y - MAP.y0 + 0.5, z: m.z ?? d.z, label: m.label }));
    if (pts.length) {
      const xs = pts.map((p) => p.x).concat(cx), ys = pts.map((p) => p.y).concat(cy);
      const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
      cx = (minX + maxX) / 2; cy = (minY + maxY) / 2;
      s = Math.max(0.6, Math.min(5, cw / (maxX - minX + 12), ch / (maxY - minY + 12)));
    }
    const dpr = window.devicePixelRatio || 1;
    const cv = $("canvas", el);
    cv.width = Math.round(cw * dpr); cv.height = Math.round(ch * dpr);
    cv.style.width = cw + "px"; cv.style.height = ch + "px";
    const ctx = cv.getContext("2d");
    ctx.imageSmoothingEnabled = false;
    const sw = cw / s, sh = ch / s, sx = cx - sw / 2, sy = cy - sh / 2;
    ctx.fillStyle = "#000"; ctx.fillRect(0, 0, cv.width, cv.height);
    ctx.drawImage(img, sx, sy, sw, sh, 0, 0, cv.width, cv.height);
    const place = (px, py, cls, n) => {
      const m = document.createElement("span");
      m.className = "mm-mark " + cls;
      m.style.left = (px - sx) * s + "px"; m.style.top = (py - sy) * s + "px";
      if (n) m.dataset.n = n;
      el.appendChild(m);
    };
    if (pts.length) pts.forEach((p, i) => place(p.x, p.y, "small", i + 1));
    else if (!d.nomark) place(d.x - MAP.x0 + 0.5, d.y - MAP.y0 + 0.5, "");
  }

  // ---------------------------------------------------------------- leaflet map
  function TibiaMap(host, opts = {}) {
    const toLL = (x, y) => L.latLng(-(y - MAP.y0) - 0.5, x - MAP.x0 + 0.5);
    const fromLL = (ll) => ({ x: Math.floor(ll.lng) + MAP.x0, y: Math.floor(-ll.lat) + MAP.y0 });
    const map = L.map(host, {
      crs: L.CRS.Simple, minZoom: -3, maxZoom: 4, zoomSnap: 0.25, zoomDelta: 0.5, attributionControl: false,
      maxBounds: [[-MAP.h - 300, -300], [300, MAP.w + 300]], wheelPxPerZoomLevel: 90,
    });
    let floor = 7;
    const overlay = L.imageOverlay(floorUrl(floor), [[-MAP.h, 0], [0, MAP.w]]).addTo(map);
    const questLayer = L.layerGroup().addTo(map);
    const pointLayer = L.layerGroup().addTo(map);
    const focusLayer = L.layerGroup().addTo(map);
    let points = [], focus = null, showQuests = !!opts.quests;

    const fc = document.createElement("div");
    fc.className = "leaflet-overlay-floor";
    fc.innerHTML = `<button data-f="-1" title="Subir (PageUp)">▲</button><span></span><button data-f="1" title="Descer (PageDown)">▼</button>`;
    host.appendChild(fc);
    L.DomEvent.disableClickPropagation(fc);
    fc.addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) setFloor(floor + +b.dataset.f); });
    const pos = document.createElement("div");
    pos.className = "leaflet-overlay-pos";
    host.appendChild(pos);
    map.on("mousemove", (e) => { const p = fromLL(e.latlng); pos.textContent = `${p.x}, ${p.y}, ${floor}`; });
    map.on("click", (e) => {
      const p = fromLL(e.latlng);
      L.popup().setLatLng(e.latlng).setContent(`<b>${p.x}, ${p.y}, ${floor}</b><br>${floorLabel(floor)}<br>
        <a href="#" data-copy="${p.x},${p.y},${floor}">Copiar coordenadas</a>`).openOn(map);
    });
    host.addEventListener("keydown", (e) => {
      if (e.key === "PageUp") { setFloor(floor - 1); e.preventDefault(); }
      if (e.key === "PageDown") { setFloor(floor + 1); e.preventDefault(); }
    });

    function drawQuests() {
      questLayer.clearLayers();
      if (!showQuests) return;
      S.quests.forEach((q) => {
        const p = q.pin;
        if (!p || p.z !== floor || !matches(q)) return;
        const i = bandIndex(q.rec || q.lvl || 1);
        const ic = L.divIcon({ className: "qmarker-wrap", html: `<div class="qmarker" style="--c:${bandColor(i)}">${q.lvl || q.rec || 1}</div>`, iconSize: [26, 30], iconAnchor: [13, 30], popupAnchor: [0, -28] });
        L.marker(toLL(p.x, p.y), { icon: ic, title: q.name, riseOnHover: true }).addTo(questLayer)
          .bindPopup(`<b>${esc(q.name)}</b><br>Nível ${q.lvl || "—"} · rec. ${esc(q.rec_raw || q.rec || "—")}<br><span class="muted">${esc(p.label || q.region || "")}</span><br><a href="#/quest/${q.slug}">Abrir guia →</a>`);
      });
    }
    function drawPoints() {
      pointLayer.clearLayers();
      points.forEach((p, i) => {
        if (p.z !== floor) return;
        const ic = L.divIcon({ className: "", html: `<div class="pt-marker"><b>${i + 1}${p.label ? ". " + esc(plainText(p.label)).slice(0, 40) : ""}</b></div>`, iconSize: [14, 14], iconAnchor: [7, 7] });
        L.marker(toLL(p.x, p.y), { icon: ic }).addTo(pointLayer).bindPopup(`<b>${i + 1}. ${esc(plainText(p.label || ""))}</b><br>${p.x}, ${p.y}, ${p.z} · ${floorLabel(p.z)}<br><a href="#" data-copy="${p.x},${p.y},${p.z}">Copiar coordenadas</a>`);
      });
    }
    function drawFocus() {
      focusLayer.clearLayers();
      if (!focus || focus.z !== floor) return;
      const ic = L.divIcon({ className: "", html: `<div class="focus-marker"></div>`, iconSize: [22, 22], iconAnchor: [11, 11] });
      const m = L.marker(toLL(focus.x, focus.y), { icon: ic, zIndexOffset: 1000 }).addTo(focusLayer);
      if (focus.label) m.bindTooltip(esc(plainText(focus.label)), { direction: "top", offset: [0, -12], permanent: true });
    }
    function setFloor(z) {
      z = Math.max(0, Math.min(15, z));
      floor = z;
      overlay.setUrl(floorUrl(z));
      $("span", fc).textContent = z === 7 ? "0" : z < 7 ? `+${7 - z}` : `−${z - 7}`;
      $("span", fc).title = floorLabel(z);
      drawQuests(); drawPoints(); drawFocus();
      if (opts.onFloor) opts.onFloor(z);
    }
    setFloor(7);
    map.setView(toLL(32369, 32241), 0);
    return {
      map,
      setFloor, get floor() { return floor; },
      focusOn(x, y, z, label, zoom = 2) { focus = { x, y, z, label }; setFloor(z); map.setView(toLL(x, y), zoom); },
      clearFocus() { focus = null; drawFocus(); },
      setPoints(list) {
        points = list || [];
        if (points.length) {
          const z0 = points[0].z;
          setFloor(z0);
          const same = points.filter((p) => p.z === z0);
          map.fitBounds(L.latLngBounds(same.map((p) => toLL(p.x, p.y))).pad(0.4), { maxZoom: 2 });
        } else drawPoints();
      },
      setShowQuests(v) { showQuests = v; drawQuests(); },
      refreshQuests: drawQuests,
      invalidate() { map.invalidateSize(); },
    };
  }

  let modalMap = null;
  function openMap(x, y, z, label, extra) {
    const modal = $("#mapModal");
    modal.hidden = false;
    $("#mapModalTitle").textContent = (label ? plainText(label) + " — " : "") + `${x}, ${y}, ${z} (${floorLabel(z)})`;
    $("#mapModalActions").innerHTML = `${extra || ""}<button data-copy="${x},${y},${z}">Copiar coordenadas</button>`;
    if (!modalMap) modalMap = TibiaMap($("#mapModalHost"), { quests: false });
    requestAnimationFrame(() => { modalMap.invalidate(); modalMap.focusOn(x, y, z, label, 2.5); });
  }
  function openNpc(name) {
    const n = S.npcs[name];
    const href = wikiHref(name);
    if (!n || n.x == null) { if (href) location.hash = href; return; }
    openMap(n.x, n.y, n.z, name + (n.city ? ` (${n.city})` : ""), href ? `<a href="${href}" data-close>Página de ${esc(name)}</a>` : "");
  }
  const closeModal = () => { $("#mapModal").hidden = true; };

  // ---------------------------------------------------------------- lightbox
  let lbList = [], lbIndex = 0;
  function openLightbox(fig) {
    lbList = $$(".shot", $("#view"));
    lbIndex = Math.max(0, lbList.indexOf(fig));
    showLb();
    $("#lightbox").hidden = false;
  }
  function showLb() {
    const f = lbList[lbIndex];
    if (!f) return;
    $("#lbImg").src = $("img", f).src;
    $("#lbCap").textContent = $("figcaption", f)?.textContent || "";
  }
  const lbStep = (d) => { if (!lbList.length) return; lbIndex = (lbIndex + d + lbList.length) % lbList.length; showLb(); };

  // ---------------------------------------------------------------- views
  const view = () => $("#view");

  function questCard(q) {
    const p = pct(q);
    const icons = (q.rewards || []).map((r) => sprite(r)).filter(Boolean).slice(0, 4);
    return `<a class="qcard ${isDone(q.slug) ? "done" : ""} ${locked(q) ? "locked" : ""}" href="#/quest/${q.slug}">
      <div class="qcard-top">${lvlShield(q)}
        <div style="min-width:0"><h3>${esc(q.name)}</h3>
          <div class="meta">${premChip(q.premium)}${catChip(q.category)}${(q.unlocks || []).length ? `<span class="chip chip-key" title="Dá acesso a: ${esc(q.unlocks.map((u) => plainText(u.what)).join(", "))}">${icon("key")}Acesso</span>` : ""}${isDone(q.slug) ? `<span class="chip chip-done">${icon("check")}Feita</span>` : ""}${locked(q) ? `<span class="chip chip-locked">${icon("lock")}Nível ${q.lvl}</span>` : ""}</div>
        </div></div>
      <p>${esc(plainText(q.summary)) || `<span class="muted">${esc(q.location)}</span>`}</p>
      ${p > 0 && p < 100 ? `<div class="progress-mini"><i style="width:${p}%"></i></div>` : ""}
      <div class="qcard-foot">${q.region ? `${icon("pin")} ${esc(q.region)}` : ""}${S.filters.region && q.region !== S.filters.region ? ` <span class="chip chip-pass" title="A região principal desta quest é ${esc(q.region || "várias")}, mas tem passos em ${esc(S.filters.region)}">passa por ${esc(S.filters.region)}</span>` : ""} ${skulls(q.difficulty)}
        <span class="reward-icons">${icons.map((im) => `<img src="${im.src}" alt="" loading="lazy">`).join("")}</span></div>
    </a>`;
  }

  function renderHome() {
    const total = S.quests.length;
    const free = S.quests.filter((q) => q.premium === false).length;
    const steps = S.quests.reduce((a, q) => a + (q.steps || 0), 0);
    const done = S.quests.filter((q) => isDone(q.slug)).length;
    const inProg = S.quests.filter((q) => !isDone(q.slug) && stepsDone(q.slug) > 0)
      .sort((a, b) => (prog(b.slug).t || 0) - (prog(a.slug).t || 0)).slice(0, 6);
    const lvl = S.filters.level;
    const sugg = lvl ? S.quests.filter((q) => !isDone(q.slug) && (q.lvl || 0) <= lvl && (q.rec || q.lvl || 1) <= lvl + 5)
      .sort((a, b) => (b.rec || b.lvl || 0) - (a.rec || a.lvl || 0)).slice(0, 6) : [];
    const groups = grouped(S.quests);
    const catCounts = Object.keys(CATS).map((k) => [k, S.quests.filter((q) => q.category === k).length]).filter(([, n]) => n);

    view().innerHTML = `
      <section class="hero">
        <img class="hero-logo" src="assets/logo-full.webp" alt="Tibia Questski — feiticeira num jetski">
        <div>
          <h1>Guia de Quests</h1>
          <p>Todas as quests que podes começar <b>até ao nível 100</b>, explicadas passo a passo, com coordenadas, mini-mapas, capturas de ecrã, diálogos dos NPCs e progresso guardado.</p>
          <form class="hero-form" id="heroForm">
            <label for="heroLevel">O meu nível</label>
            <input class="input" id="heroLevel" type="number" min="1" max="2000" placeholder="ex. 30" value="${lvl || ""}">
            <button class="btn" type="submit">${icon("search")}Ver quests para mim</button>
            <a class="btn btn-ghost" href="#/quest/${S.quests[Math.floor(Math.random() * S.quests.length)]?.slug}" id="randomQuest">${icon("dice")}Quest aleatória</a>
          </form>
        </div>
      </section>

      <div class="stats">
        <div class="stat"><b>${total}</b><span>quests</span></div>
        <div class="stat"><b>${steps.toLocaleString("pt-PT")}</b><span>passos guiados</span></div>
        <div class="stat"><b>${free}</b><span>free account</span></div>
        <div class="stat"><b>${total - free}</b><span>premium / outras</span></div>
        <div class="stat"><b>${done}</b><span>concluídas por ti</span></div>
      </div>

      ${inProg.length ? `<section class="box"><h2 class="box-caption">${icon("clock")}Continua onde ficaste</h2><div class="box-body"><div class="qgrid">${inProg.map(questCard).join("")}</div></div></section>` : ""}
      ${sugg.length ? `<section class="box"><h2 class="box-caption">${icon("flag")}Sugestões para o nível ${lvl}<span class="cap-extra"><a href="#/quests" style="color:inherit">ver todas →</a></span></h2><div class="box-body"><div class="qgrid">${sugg.map(questCard).join("")}</div></div></section>` : ""}

      <section class="box">
        <h2 class="box-caption">${icon("layers")}Quests por nível<span class="cap-extra">ordenadas do mais baixo para o mais alto</span></h2>
        <div class="box-body"><div class="band-grid">
          ${groups.map((g, i) => g.length ? `<a class="band-card" style="--c:${bandColor(i)}" href="#/quests/${i}">
            <b>${BANDS[i][2]}</b><span>${g.length} quests · ${g.filter((q) => isDone(q.slug)).length} feitas</span>
            <span class="bar"><i style="width:${Math.round(g.filter((q) => isDone(q.slug)).length / g.length * 100)}%"></i></span></a>` : "").join("")}
        </div></div>
      </section>

      <section class="box">
        <h2 class="box-caption">${icon("map")}Quests por região<span class="cap-extra">escolhe uma cidade para ver só as quests de lá</span></h2>
        <div class="box-body"><div class="region-grid">${regionCards()}</div></div>
      </section>

      <section class="box">
        <h2 class="box-caption">${icon("list")}Tipos de quest</h2>
        <div class="box-body"><div class="cat-grid">
          ${catCounts.map(([k, n]) => `<button class="cat-card" data-gocat="${k}">${icon(CATS[k].icon)}<div><b>${CATS[k].label}</b><span>${n} quests</span></div></button>`).join("")}
        </div></div>
      </section>

      <section class="box">
        <h2 class="box-caption">${icon("bulb")}Como usar</h2>
        <div class="box-body split">
          <div><b>Abas:</b> cada quest abre numa aba própria no topo — podes ter várias abertas e saltar entre elas.<br>
          <b>Progresso:</b> marca cada passo como feito; fica guardado neste navegador.</div>
          <div><b>Mapas:</b> clica num mini-mapa ou coordenada para abrir o mapa interativo (▲▼ mudam de piso). <b>Região:</b> filtra as quests por cidade na barra lateral ou nos cartões de região.<br>
          <b>Falar com NPCs:</b> clica numa palavra <kbd class="say">hi</kbd> para a copiar.</div>
        </div>
      </section>
      <p class="muted" style="font-size:14px">Dados gerados a ${esc(S.generated)} a partir da TibiaWiki.</p>`;

    $("#heroForm").onsubmit = (e) => {
      e.preventDefault();
      const v = parseInt($("#heroLevel").value, 10);
      S.filters.level = v > 0 ? v : null;
      S.filters.lvlChar = false;
      S.filters.onlyAvail = !!S.filters.level;
      saveFilters(); renderFilters(); renderList();
      location.hash = "#/quests";
    };
    $$("[data-gocat]").forEach((b) => (b.onclick = () => { S.filters.cats = [b.dataset.gocat]; saveFilters(); renderFilters(); renderList(); location.hash = "#/quests"; }));
    hydrateMinimaps(view());
  }

  /** Region cards: a small map of the city, its name and how many quests are about it. */
  function regionCards() {
    return S.regions.map((r) => {
      const mine = S.quests.filter((q) => inRegion(q, r.name, false));
      const done = mine.filter((q) => isDone(q.slug)).length;
      const mm = esc(JSON.stringify({ x: r.x, y: r.y, z: 7, s: 1.6, nomark: true }));
      return `<a class="region-card ${S.filters.region === r.name ? "on" : ""}" href="#/quests/regiao/${encodeURIComponent(r.name)}" data-goregion>
        <div class="minimap region-thumb" data-mm="${mm}"><canvas></canvas></div>
        <div class="region-info"><b>${esc(r.name)}</b><span>${r.main} da região · ${r.total} no total</span>
          <span class="bar"><i style="width:${mine.length ? Math.round(done / mine.length * 100) : 0}%"></i></span></div></a>`;
    }).join("");
  }

  function renderQuestsPage() {
    const list = filtered();
    const groups = grouped(list);
    const f = S.filters;
    const reg = S.regions.find((r) => r.name === f.region);
    view().innerHTML = `
      <div class="region-bar">
        <button class="cat-pill ${!f.region ? "on" : ""}" data-setregion="">${icon("globe")}Todas as regiões</button>
        ${S.regions.map((r) => `<button class="cat-pill ${f.region === r.name ? "on" : ""}" data-setregion="${esc(r.name)}">${esc(r.name)} <span class="muted">${f.regionMain ? r.main : r.total}</span></button>`).join("")}
      </div>
      ${reg ? `<div class="region-head box"><div class="box-body">
          <div class="minimap region-thumb lg" data-mm="${esc(JSON.stringify({ x: reg.x, y: reg.y, z: 7, s: 2, nomark: true }))}"><canvas></canvas></div>
          <div><h2>${icon("pin")} Quests de ${esc(reg.name)}</h2>
            <p class="muted">${reg.main} quests são de ${esc(reg.name)} e arredores; outras ${reg.total - reg.main} são de outras regiões mas têm passos por lá.</p>
            <div class="seg">${[[true, `Só as de ${esc(reg.name)} (${reg.main})`], [false, `+ as que passam por lá (${reg.total})`]].map(([v, l]) => `<button data-regionmain="${v}" class="${!!f.regionMain === v ? "on" : ""}">${l}</button>`).join("")}</div>
            <a class="btn btn-ghost btn-sm" href="#/mapa/${reg.x},${reg.y},7" style="margin-left:8px">${icon("map")}Ver no mapa</a>
          </div></div></div>` : ""}
      <div class="toolbar">
        <h1>${reg ? `Quests de ${esc(reg.name)}` : "Todas as quests"} <span class="muted" style="font-size:18px">(${list.length})</span></h1>
        <div class="seg">${[["rec", "Nível recomendado"], ["min", "Nível mínimo"]].map(([v, l]) => `<button data-sort2="${v}" class="${f.sort === v ? "on" : ""}">${l}</button>`).join("")}</div>
        ${f.q || f.cats.length || f.region || f.prem !== "all" || f.hideDone || f.onlyAvail ? `<button class="btn btn-ghost btn-sm" id="clearF">Limpar filtros</button>` : ""}
      </div>
      ${groups.map((g, i) => g.length ? `<section class="grid-band" id="band-${i}"><h2><span class="band-dot" style="--c:${bandColor(i)}"></span>${BANDS[i][2]}<small>${BANDS[i][3] ? BANDS[i][3] + " · " : ""}${g.length} quests</small></h2>
        <div class="qgrid">${g.map(questCard).join("")}</div></section>` : "").join("") || `<div class="note-box">Nenhuma quest corresponde aos filtros.</div>`}`;
    $$("[data-sort2]").forEach((b) => (b.onclick = () => { S.filters.sort = b.dataset.sort2; filtersChanged(true); }));
    $$("[data-setregion]").forEach((b) => (b.onclick = () => { location.hash = b.dataset.setregion ? `#/quests/regiao/${encodeURIComponent(b.dataset.setregion)}` : "#/quests/regiao"; }));
    $$("[data-regionmain]").forEach((b) => (b.onclick = () => { S.filters.regionMain = b.dataset.regionmain === "true"; filtersChanged(true); }));
    hydrateMinimaps(view());
    const c = $("#clearF");
    if (c) c.onclick = () => $("#fReset").click();
    const band = S.route.args[0];
    if (band != null && /^\d+$/.test(band) && $("#band-" + band)) $("#band-" + band).scrollIntoView();
    const bar = $(".region-bar"), act = $(".region-bar .cat-pill.on");
    if (bar && act) bar.scrollLeft = act.offsetLeft - bar.offsetLeft - bar.clientWidth / 2 + act.clientWidth / 2;
  }

  // ---------- quest page
  function collectPoints(d) {
    const pts = [];
    const push = (c, label) => { if (c && Number.isInteger(c.x) && Number.isInteger(c.y)) pts.push({ x: c.x, y: c.y, z: c.z ?? 7, label: c.label || label || "" }); };
    if (d.start) push(d.start, d.start.label || "Início");
    (d.sections || []).forEach((sec) => sec.steps.forEach((st) => {
      if (st.npc && S.npcs[st.npc] && S.npcs[st.npc].x != null) push(S.npcs[st.npc], st.npc);
      (st.coords || []).forEach((c) => push(c, st.title));
      if (st.map) (st.map.marks || []).forEach((m) => push(Object.assign({ z: st.map.z }, m), st.title));
    }));
    const seen = new Set();
    return pts.filter((p) => { const k = `${p.x},${p.y},${p.z}`; if (seen.has(k)) return false; seen.add(k); return true; });
  }

  function entCard(name, kind, extra, qty) {
    const im = sprite(name);
    const slot = im ? `<img src="${im.src}" alt="" loading="lazy">` : icon(kind === "creature" ? "skull" : kind === "npc" ? "users" : "gift");
    const href = wikiHref(name);
    const tag = href ? `a class="ent-card" href="${href}"` : `div class="ent-card"`;
    return `<${tag}>
      <span class="slot">${slot}</span><span style="min-width:0"><b>${qty ? `<span class="qty">${qty}× </span>` : ""}${esc(name)}</b>${extra ? `<span>${extra}</span>` : ""}</span></${href ? "a" : "div"}>`;
  }

  const TRAVEL_STEP = /^(chegar|entrar|ir|sair|voltar|viajar|subir|descer)\b/i;
  /** Travel cards to show under a step: places it mentions that were not covered yet in this section. */
  function travelCardsFor(st, shown) {
    const title = (st.title || "").toLowerCase();
    const cards = [];
    placesInStep(st).forEach((p) => {
      const key = p.title.toLowerCase();
      if (shown.has(key) || p.type === "cidade") return;
      if (TRAVEL_STEP.test(title) && title.includes(key)) return;  // this step is the travel step itself
      shown.add(key);
      cards.push(travelCard(p));
    });
    return cards.slice(0, 3).join("");
  }

  function stepHTML(slug, st, id, n, extra = "") {
    const p = prog(slug);
    const checked = !!(p.s && p.s[id]);
    let html = `<div class="step ${checked ? "checked" : ""}" id="step-${id}" data-step="${id}">
      <label class="step-check"><input type="checkbox" ${checked ? "checked" : ""} data-check="${id}" aria-label="Marcar passo ${n} como feito"><span class="step-num">${checked ? "✓" : n}</span><span class="tick">${checked ? "feito" : "marcar"}</span></label>
      <div class="step-body">
        <div class="step-head">${st.title ? `<h4>${rich(st.title)}</h4>` : `<h4>Passo ${n}</h4>`}<a class="step-link" href="#/quest/${slug}/guia/${id}" title="Link para este passo">${icon("hash")}</a></div>
        <div class="step-text">${rich(st.text)}</div>`;
    if (st.npc) {
      const npc = S.npcs[st.npc];
      html += `<div class="npc-card">${spriteImg(st.npc, "") || icon("users")}<div class="npc-info"><b>${esc(st.npc)}</b><span>${npc ? [npc.job, npc.city, npc.x != null ? `${npc.x}, ${npc.y}, ${npc.z} · ${floorLabel(npc.z)}` : null].filter(Boolean).map(esc).join(" · ") : "Posição não indicada"}</span></div>
        ${npc && npc.x != null ? `<button class="btn btn-ghost btn-sm" data-npc="${esc(st.npc)}">${icon("pin")}Onde está?</button>` : ""}</div>`;
    }
    if (st.dialogue && st.dialogue.length) {
      html += `<div class="chat"><div class="chat-head"><span>${esc(st.npc || "Conversa")} · NPCs</span><span>clica nas tuas falas para copiar</span></div>` +
        st.dialogue.map((d) => d.you != null
          ? `<div class="chat-line you" data-say="${esc(plainText(d.you))}"><span class="who">Tu:</span>${esc(plainText(d.you))}</div>`
          : `<div class="chat-line npc"><span class="who">${esc(st.npc || "NPC")}:</span>${esc(plainText(d.npc))}</div>`).join("") + `</div>`;
    }
    if (st.table && st.table.rows) {
      html += `<div class="tbl-wrap"><table class="tbl">${st.table.head ? `<thead><tr>${st.table.head.map((h) => `<th>${rich(h)}</th>`).join("")}</tr></thead>` : ""}<tbody>${st.table.rows.map((r) => `<tr>${r.map((c) => `<td>${rich(String(c))}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
    }
    const shots = (st.images || []).filter((im) => imageFor(im.file));
    if (shots.length) {
      html += `<div class="shots ${shots.length === 1 ? "single" : ""}">` + shots.map((im) => {
        const f = imageFor(im.file);
        const small = f.w && f.w <= 120;
        return `<figure class="shot ${small ? "pixel" : ""}"><img src="${f.src}" alt="${esc(im.caption || im.file)}" loading="lazy" ${f.w ? `width="${f.w}" height="${f.h}"` : ""}>${im.caption ? `<figcaption>${rich(im.caption)}</figcaption>` : ""}</figure>`;
      }).join("") + `</div>`;
    }
    const coords = st.coords || [];
    if (coords.length || st.map) {
      html += `<div class="coords">`;
      if (st.map) {
        const marks = (st.map.marks || []).map((m) => Object.assign({ z: st.map.z }, m));
        html += `<div class="coord-card">${minimapHTML(st.map.x, st.map.y, st.map.z, marks.length ? marks : null, "Abrir no mapa")}
          <div class="coord-info"><span class="label">${marks.length ? `${marks.length} pontos marcados` : "Mapa da zona"}</span>
          ${marks.length ? `<ol class="mark-legend">${marks.map((m) => `<li><a class="coord-link" data-coord="${m.x},${m.y},${m.z}" data-label="${esc(m.label || "")}">${esc(plainText(m.label) || `${m.x}, ${m.y}, ${m.z}`)}</a></li>`).join("")}</ol>` : ""}
          ${coordActions(st.map.x, st.map.y, st.map.z, st.title)}</div></div>`;
      }
      html += coords.map((c) => `<div class="coord-card">${minimapHTML(c.x, c.y, c.z, null, c.label)}
        <div class="coord-info"><span class="label">${rich(c.label || "Local")}</span><span class="xyz">${c.x}, ${c.y}, ${c.z} · ${floorLabel(c.z)}</span>${coordActions(c.x, c.y, c.z, c.label)}</div></div>`).join("");
      html += `</div>`;
    }
    if (st.warning) html += `<div class="callout warn">${icon("warn")}<div><b class="k">Atenção</b>${rich(st.warning)}</div></div>`;
    if (st.tip) html += `<div class="callout tip">${icon("bulb")}<div><b class="k">Dica</b>${rich(st.tip)}</div></div>`;
    if (st.reward) html += `<div class="callout reward">${icon("gift")}<div><b class="k">Recebes</b>${rich(st.reward)}</div></div>`;
    return html + extra + `</div></div>`;
  }
  const coordActions = (x, y, z, label) => `<div class="coord-actions">
      <button data-coord="${x},${y},${z}" data-label="${esc(plainText(label || ""))}">${icon("map")}Mapa</button>
      <button data-copy="${x},${y},${z}">${icon("copy")}Copiar</button></div>`;

  function guideTab(d) {
    if (!d.has_guide || !(d.sections || []).length) {
      return `<div class="note-box">O guia detalhado desta quest ainda está a ser preparado.</div>`;
    }
    let n = 0;
    const p = prog(d.slug);
    const secs = d.sections.map((sec, si) => {
      const ids = sec.steps.map((_, ti) => `${si}-${ti}`);
      const doneCount = ids.filter((id) => p.s && p.s[id]).length;
      const shown = new Set();
      return `<section class="section" id="sec-${si}">
        <div class="section-head"><h2>${rich(sec.title)}</h2><span class="sec-count" data-sec-count="${si}">${doneCount}/${ids.length}</span></div>
        ${sec.intro ? `<p class="section-intro">${rich(sec.intro)}</p>` : ""}
        ${sec.steps.map((st, ti) => stepHTML(d.slug, st, `${si}-${ti}`, ++n, travelCardsFor(st, shown))).join("")}
      </section>`;
    }).join("");
    const before = [];
    if ((d.requirements || []).length) before.push(`<h4>Requisitos</h4><ul class="list-clean">${d.requirements.map((r) => `<li>${icon("check")}<span>${rich(r)}</span></li>`).join("")}</ul>`);
    if ((d.items_needed || []).length) before.push(`<h4>Leva contigo</h4><ul class="list-clean">${d.items_needed.map((it) => `<li>${icon("bag")}<span>${it.item ? `${it.qty ? `<span class="qty">${it.qty}× </span>` : ""}${renderToken("item", it.item + (it.label ? "|" + it.label : ""))}` : rich(it.text)}${it.note ? ` <span class="note">— ${rich(it.note)}</span>` : ""}</span></li>`).join("")}</ul>`);
    const notes = (d.notes || []).length ? `<section class="box"><h2 class="box-caption">${icon("book")}Notas e perguntas frequentes</h2><div class="box-body"><ul class="notes-list">${d.notes.map((x) => `<li>${rich(x)}</li>`).join("")}</ul></div></section>` : "";
    const toc = d.sections.map((sec, si) => {
      const total = sec.steps.length;
      const dc = sec.steps.filter((_, ti) => p.s && p.s[`${si}-${ti}`]).length;
      return `<a href="#/quest/${d.slug}/guia/sec-${si}" data-toc="${si}" class="${dc === total ? "complete" : ""}">${icon(dc === total ? "checkCircle" : "circle")}<span>${esc(plainText(sec.title))}</span><span class="toc-n">${dc}/${total}</span></a>`;
    }).join("");
    return `<div class="guide-layout"><div>
        ${before.length ? `<section class="box"><h2 class="box-caption">${icon("flag")}Antes de começares<span class="cap-extra"><a style="color:inherit" href="#/quest/${d.slug}/preparacao">preparação completa →</a></span></h2><div class="box-body prep">${before.map((b) => `<div>${b}</div>`).join("")}</div></section>` : ""}
        ${secs}${rewardScroll(d)}${notes}
      </div>
      <aside class="toc"><section class="box"><h2 class="box-caption">${icon("list")}Índice</h2><div class="box-body">${toc}</div></section></aside></div>`;
  }

  function prepTab(d) {
    const parts = [];
    if ((d.requirements || []).length) parts.push(`<section class="box"><h2 class="box-caption">${icon("flag")}Requisitos</h2><div class="box-body"><ul class="list-clean">${d.requirements.map((r) => `<li>${icon("check")}<span>${rich(r)}</span></li>`).join("")}</ul></div></section>`);
    if ((d.items_needed || []).length) parts.push(`<section class="box"><h2 class="box-caption">${icon("bag")}Itens necessários</h2><div class="box-body"><div class="ent-grid">${d.items_needed.map((it) => it.item ? entCard(it.item, "item", it.note ? esc(plainText(it.note)) : "", it.qty) : `<div class="text-reward">${rich(it.text)}${it.note ? ` — ${rich(it.note)}` : ""}</div>`).join("")}</div></div></section>`);
    if ((d.dangers || []).length) parts.push(`<section class="box"><h2 class="box-caption">${icon("skull")}Perigos (criaturas)</h2><div class="box-body"><div class="ent-grid">${d.dangers.map((c) => entCard(c, "creature")).join("")}</div></div></section>`);
    else if (d.dangers_raw) parts.push(`<section class="box"><h2 class="box-caption">${icon("skull")}Perigos</h2><div class="box-body">${esc(d.dangers_raw)}</div></section>`);
    if ((d.npcs || []).length) parts.push(`<section class="box"><h2 class="box-caption">${icon("users")}NPCs envolvidos</h2><div class="box-body"><div class="ent-grid">${d.npcs.map((n) => { const p = S.npcs[n]; return entCard(n, "npc", p ? esc([p.city, p.x != null ? `${p.x}, ${p.y}, ${p.z}` : ""].filter(Boolean).join(" · ")) : ""); }).join("")}</div><p class="muted" style="margin:10px 0 0;font-size:14px">Clica num NPC para abrir a página dele na wiki, com a localização no mapa.</p></div></section>`);
    if ((d.tips || []).length) parts.push(`<section class="box"><h2 class="box-caption">${icon("bulb")}Dicas antes de começar</h2><div class="box-body"><ul class="notes-list">${d.tips.map((t) => `<li>${rich(t)}</li>`).join("")}</ul></div></section>`);
    return parts.join("") || `<div class="note-box">Sem requisitos especiais registados.</div>`;
  }

  /** "Quest complete!" reward scroll (RuneScape-wiki style) shown at the end of every guide. */
  const UNROLLED = new Set(); // scrolls already unrolled this session stay open across re-renders
  function rewardScroll(d) {
    const items = (d.rewards || []).filter((r) => r.item);
    const ach = d.achievements || [];
    // achievements already get their own block: drop "Achievement X" text rewards that repeat them
    const texts = (d.rewards || []).filter((r) => !r.item && !(/^\W*achievements?\b/i.test(plainText(r.text || "")) && ach.some((a) => plainText(r.text).toLowerCase().includes(a.toLowerCase()))));
    const unl = d.unlocks || [];
    if (!items.length && !texts.length && !ach.length && !unl.length && !d.reward_raw) return "";
    const heroItem = items.find((r) => sprite(r.item));
    const hero = heroItem ? sprite(heroItem.item) : null;
    const done = isDone(d.slug);
    const itemRow = (r) => {
      const href = wikiHref(r.item);
      const name = `${r.qty ? `<span class="qs-qty">${r.qty}×</span> ` : ""}${esc(r.item)}`;
      return `<li><span class="qs-slot">${spriteImg(r.item, "") || icon("gift")}</span><span>${href ? `<a href="${href}">${name}</a>` : `<b>${name}</b>`}${r.note ? `<small>${rich(r.note)}</small>` : ""}</span></li>`;
    };
    const block = (title, ic, body) => body ? `<div class="qs-block"><h4>${icon(ic)}${title}</h4>${body}</div>` : "";
    return `
      <section class="quest-scroll ${UNROLLED.has(d.slug) ? "open unrolled" : ""}" data-slug="${d.slug}" aria-label="Recompensas da quest">
        <div class="qs-roll"></div>
        <div class="qs-paper"><div class="qs-inner">
          <div class="qs-head">
            <span class="qs-kicker">Quest concluída!</span>
            <h3>Parabéns!</h3>
            <p>Completaste a <b>${esc(d.name)}</b> e recebes:</p>
          </div>
          <div class="qs-body">
            <div class="qs-hero">${hero
              ? `<div class="qs-glow"><img src="${hero.src}" alt="${esc(heroItem.item)}"></div><span>${esc(heroItem.item)}</span>`
              : `<div class="qs-glow qs-glow-ico">${icon(unl.length ? "key" : ach.length ? "trophy" : "chest")}</div><span>${unl.length ? `${unl.length} ${unl.length === 1 ? "acesso" : "acessos"}` : ach.length ? `${ach.length} ${ach.length === 1 ? "achievement" : "achievements"}` : "Recompensa"}</span>`}</div>
            <div class="qs-lists">
              ${block("Recompensas", "gift", (items.length || texts.length) ? `${items.length ? `<ul class="qs-items ${items.length > 3 ? "many" : ""}">${items.map(itemRow).join("")}</ul>` : ""}${texts.length ? `<ul class="qs-items">${texts.map((t) => `<li><span class="qs-slot">${icon("star")}</span><span>${rich(t.text)}${t.note ? `<small>${rich(t.note)}</small>` : ""}</span></li>`).join("")}</ul>` : ""}` : (d.reward_raw ? `<p class="qs-raw">${esc(d.reward_raw)}</p>` : ""))}
              ${block("Achievements", "trophy", ach.length ? `<ul class="qs-tags">${ach.map((a) => { const h = wikiHref(a); return `<li>${icon("trophy")}${h ? `<a href="${h}">${esc(a)}</a>` : esc(a)}</li>`; }).join("")}</ul>` : "")}
              ${block("Desbloqueias", "key", unl.length ? `<ul class="qs-tags qs-unlocks">${unl.map((u) => { const h = u.place ? wikiHref(u.place) : null; return `<li title="${esc(plainText(u.when || ""))}">${icon((UNLOCK_KINDS[u.kind] || UNLOCK_KINDS.zona)[1])}${h ? `<a href="${h}">${esc(plainText(u.what))}</a>` : `<span>${rich(u.what)}</span>`}</li>`; }).join("")}</ul><a class="qs-more" href="#/quest/${d.slug}/recompensas">Quando e como recebes cada acesso →</a>` : "")}
            </div>
          </div>
          <div class="qs-foot">
            <button class="btn ${done ? "btn-ok" : ""}" data-mark-done>${icon("check")}${done ? "Quest concluída!" : "Marcar como concluída"}</button>
          </div>
          <span class="qs-seal" aria-hidden="true">${icon("star")}</span>
        </div></div>
        <div class="qs-roll"></div>
      </section>`;
  }

  function rewardsTab(d) {
    const parts = [rewardScroll(d)];
    if ((d.unlocks || []).length) parts.push(`<section class="box"><h2 class="box-caption">${icon("key")}Dá acesso a (detalhes)</h2><div class="box-body"><ul class="list-clean unlock-list">${d.unlocks.map(unlockLi).join("")}</ul></div></section>`);
    const rewardSteps = [];
    (d.sections || []).forEach((sec, si) => sec.steps.forEach((st, ti) => { if (st.reward) rewardSteps.push(`<li><a href="#/quest/${d.slug}/guia/${si}-${ti}">${esc(plainText(st.title || sec.title))}</a>: ${rich(st.reward)}</li>`); }));
    if (rewardSteps.length) parts.push(`<section class="box"><h2 class="box-caption">${icon("list")}Onde recebes cada coisa</h2><div class="box-body"><ul class="notes-list">${rewardSteps.join("")}</ul></div></section>`);
    if (d.reward_raw) parts.push(`<p class="muted" style="font-size:14.5px"><b>Resumo da TibiaWiki:</b> ${esc(d.reward_raw)}</p>`);
    return parts.join("") || `<div class="note-box">Sem recompensas registadas.</div>`;
  }

  let questMap = null;
  function mapTab(d) {
    const pts = collectPoints(d);
    if (!pts.length) return `<div class="note-box">Esta quest não tem coordenadas registadas. Usa o <a href="#/mapa">mapa geral</a> para explorar.</div>`;
    return `<div class="map-split">
      <div class="map-host" id="questMapHost" tabindex="0"></div>
      <section class="box map-points"><h2 class="box-caption">${icon("pin")}${pts.length} pontos</h2><div class="box-body">
        <ol class="notes-list" style="padding-left:24px">${pts.map((p, i) => `<li><a class="coord-link" data-qpt="${i}" style="font-family:inherit">${esc(plainText(p.label) || "Ponto")}</a><br><span class="muted" style="font-size:13px;font-family:var(--font-mono)">${p.x}, ${p.y}, ${p.z} · ${floorLabel(p.z)}</span></li>`).join("")}</ol>
      </div></section></div>`;
  }

  async function renderQuest(slug, tab, anchor) {
    const meta = S.bySlug[slug];
    if (!meta) { view().innerHTML = `<div class="note-box">Quest não encontrada. <a href="#/quests">Ver todas</a></div>`; return; }
    openTab(slug);
    renderTabs();
    tab = QTABS.some(([k]) => k === tab) ? tab : "guia";
    const same = view().dataset.slug === slug;
    if (!same) view().innerHTML = `<div class="loading">A abrir o pergaminho…</div>`;
    const d = await loadQuest(slug);
    if (S.route.name !== "quest" || S.route.args[0] !== slug) return;
    document.title = `${d.name} · Tibia Questski`;
    const p = prog(slug);
    const total = meta.steps;
    const nDone = Object.keys(p.s || {}).length;
    const facts = [
      ["Nível mínimo", d.lvl ? d.lvl : "Sem requisito"],
      ["Recomendado", d.rec_raw || d.rec || "—"],
      ["Conta", d.premium === true ? "Premium" : d.premium === false ? "Free" : "—"],
      ["Duração", d.duration || "—"],
      ["Região", d.region || "—"],
      ["Localização", d.location || "—"],
    ];
    const counts = { guia: total, recompensas: (d.rewards || []).length, mapa: collectPoints(d).length, preparacao: (d.items_needed || []).length + (d.requirements || []).length };
    view().dataset.slug = slug;
    view().innerHTML = `
      <article class="quest">
        <header class="box quest-hero">
          <div class="hero-inner">
            ${lvlShield(d, "lg")}
            <div style="min-width:0">
              <div class="meta">${premChip(d.premium)}${catChip(d.category)}${skulls(d.difficulty)}${d.implemented ? `<span class="chip">Versão ${esc(d.implemented)}</span>` : ""}${isDone(slug) ? `<span class="chip chip-done">${icon("check")}Concluída</span>` : ""}${locked(d) ? `<span class="chip chip-locked">${icon("lock")}Precisas de nível ${d.lvl}</span>` : ""}</div>
              <h1>${esc(d.name)}</h1>
              ${d.aka && d.aka.length ? `<div class="aka">Também conhecida como: ${d.aka.map(esc).join(", ")}</div>` : ""}
              ${d.summary ? `<p class="summary">${rich(d.summary)}</p>` : ""}
              ${(d.unlocks || []).length ? `<div class="unlock-strip">${icon("key")}<b>Dá acesso a:</b> ${d.unlocks.map((u) => `<a class="unlock-chip" href="${u.place && wikiHref(u.place) ? wikiHref(u.place) : `#/acessos/${encodeURIComponent(plainText(u.what))}`}" title="${esc(plainText(u.when || ""))}">${rich(u.what)}</a>`).join("")}<a class="unlock-more" href="#/quest/${d.slug}/recompensas">detalhes →</a></div>` : ""}
              ${d.legend ? `<blockquote class="legend">“${esc(d.legend)}”${d.legend_pt ? `<span class="pt">${rich(d.legend_pt)}</span>` : ""}</blockquote>` : ""}
              <div class="hero-actions">
                <button class="btn ${isDone(slug) ? "btn-ok" : ""}" id="toggleDone">${icon("check")}${isDone(slug) ? "Concluída!" : "Marcar como concluída"}</button>
                ${d.start ? `<button class="btn btn-ghost" data-coord="${d.start.x},${d.start.y},${d.start.z}" data-label="${esc(plainText(d.start.label || "Início"))}">${icon("flag")}Onde começa</button>` : ""}
                ${nDone ? `<button class="btn btn-ghost" id="resetSteps">${icon("trash")}Recomeçar</button>` : ""}
              </div>
            </div>
          </div>
          <dl class="facts">${facts.map(([k, v]) => `<div class="fact"><dt>${k}</dt><dd>${esc(v)}</dd></div>`).join("")}</dl>
          ${total ? `<div class="quest-progress"><span>Progresso</span><span class="bar-lg"><i id="qbar" style="width:${isDone(slug) ? 100 : Math.round(nDone / total * 100)}%"></i></span><span id="qcount">${nDone}/${total} passos</span></div>` : ""}
        </header>
        <nav class="qtabs" role="tablist">
          ${QTABS.map(([k, l, ic]) => `<a class="qtab ${k === tab ? "active" : ""}" href="#/quest/${slug}/${k}" role="tab" aria-selected="${k === tab}">${icon(ic)}${l}${counts[k] ? `<span class="n">${counts[k]}</span>` : ""}</a>`).join("")}
        </nav>
        <div class="qtab-body" id="qtabBody">${tab === "guia" ? guideTab(d) : tab === "preparacao" ? prepTab(d) : tab === "recompensas" ? rewardsTab(d) : mapTab(d)}</div>
      </article>`;
    hydrateMinimaps(view());
    $("#toggleDone").onclick = () => { const pp = prog(slug), v = !isDone(slug); pp.done = v; setProg(slug, pp); const g = QP.setGrimDone(slug, v); toast(v ? (g ? "Quest concluída, também no Grimório!" : "Quest marcada como concluída!") : "Quest desmarcada"); rerenderQuest(); };
    $$("[data-mark-done]").forEach((b) => (b.onclick = () => $("#toggleDone").click()));
    // unroll the reward scroll when it comes into view
    $$(".quest-scroll:not(.unrolled)").forEach((el) => {
      const paper = el.querySelector(".qs-paper");
      const unroll = () => {
        UNROLLED.add(el.dataset.slug);
        paper.style.maxHeight = paper.scrollHeight + "px";
        el.classList.add("open");
        setTimeout(() => el.classList.add("unrolled"), 1400);
      };
      if (!("IntersectionObserver" in window) || matchMedia("(prefers-reduced-motion: reduce)").matches) return el.classList.add("open", "unrolled");
      const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { io.disconnect(); unroll(); } }), { rootMargin: "0px 0px -10% 0px" });
      io.observe(el);
    });
    const rs = $("#resetSteps");
    if (rs) rs.onclick = () => { if (confirm("Apagar o progresso desta quest?")) { setProg(slug, { s: {}, done: false }); rerenderQuest(); } };
    if (tab === "mapa") {
      const host = $("#questMapHost");
      if (host) {
        questMap = TibiaMap(host, { quests: false });
        const pts = collectPoints(d);
        questMap.setPoints(pts);
        $$("[data-qpt]").forEach((a) => (a.onclick = () => { const pt = pts[+a.dataset.qpt]; questMap.focusOn(pt.x, pt.y, pt.z, pt.label, 2.5); }));
      }
    }
    if (anchor) {
      const el = document.getElementById(anchor.startsWith("sec-") ? anchor : "step-" + anchor);
      if (el) setTimeout(() => el.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
    } else if (!same) window.scrollTo(0, 0);
    setupTocSpy();
    renderList();
  }
  function rerenderQuest() {
    const [slug, tab, anchor] = S.route.args;
    const y = window.scrollY;
    renderQuest(slug, tab, null).then(() => window.scrollTo(0, y));
    void anchor;
  }

  let tocObserver = null;
  function setupTocSpy() {
    if (tocObserver) tocObserver.disconnect();
    const secs = $$(".section[id^=sec-]");
    if (!secs.length || !("IntersectionObserver" in window)) return;
    tocObserver = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          const i = e.target.id.slice(4);
          $$(".toc a").forEach((a) => a.classList.toggle("current", a.dataset.toc === i));
        }
      });
    }, { rootMargin: "-30% 0px -60% 0px" });
    secs.forEach((s) => tocObserver.observe(s));
  }

  function toggleStep(id, on) {
    const slug = S.route.args[0];
    const meta = S.bySlug[slug];
    const p = prog(slug);
    p.s = p.s || {};
    if (on) p.s[id] = 1; else delete p.s[id];
    const n = Object.keys(p.s).length;
    const wasDone = p.done;
    if (meta.steps && n >= meta.steps) p.done = true;
    setProg(slug, p);
    if (p.done && !wasDone) QP.setGrimDone(slug, true);
    const el = $(`[data-step="${id}"]`);
    if (el) {
      el.classList.toggle("checked", on);
      $(".step-num", el).textContent = on ? "✓" : $$(".step").indexOf(el) + 1;
      $(".tick", el).textContent = on ? "feito" : "marcar";
    }
    $("#qbar") && ($("#qbar").style.width = (p.done ? 100 : Math.round(n / meta.steps * 100)) + "%");
    $("#qcount") && ($("#qcount").textContent = `${n}/${meta.steps} passos`);
    const si = id.split("-")[0];
    const sec = $(`#sec-${si}`);
    if (sec) {
      const all = $$(".step", sec), dc = all.filter((s) => s.classList.contains("checked")).length;
      $(`[data-sec-count="${si}"]`).textContent = `${dc}/${all.length}`;
      const a = $(`.toc a[data-toc="${si}"]`);
      if (a) { a.classList.toggle("complete", dc === all.length); a.querySelector(".ico").innerHTML = ICONS[dc === all.length ? "checkCircle" : "circle"]; a.querySelector(".toc-n").textContent = `${dc}/${all.length}`; }
    }
    if (p.done && !wasDone) { toast("Quest concluída! Parabéns, aventureiro!"); rerenderQuest(); }
    renderList();
  }

  // ---------- internal wiki
  const WIKI_KINDS = {
    item: ["Itens", "bag"], creature: ["Criaturas", "skull"], npc: ["NPCs", "users"], spell: ["Feitiços", "spark"],
    achievement: ["Achievements", "trophy"], local: ["Locais", "map"], quest: ["Quests", "scroll"], outro: ["Outros", "book"],
  };
  const WIKI_LABELS = {
    "general properties": "Propriedades gerais", "classification": "Classificação", "pickupable": "Pode ser apanhado",
    "weight": "Peso", "trade properties": "Comércio", "marketable": "Vende-se no Market", "value": "Valor",
    "sold for": "NPCs compram por", "bought for": "NPCs vendem por", "field properties": "No chão", "blocking": "Bloqueia passagem",
    "other properties": "Outras propriedades", "version": "Versão", "notes": "Notas", "dropped by": "Largado por",
    "trade details": "Comércio com NPCs", "buy from": "Comprar a", "sell to": "Vender a", "related pages": "Páginas relacionadas",
    "location": "Localização", "loot": "Loot", "abilities": "Habilidades", "behaviour": "Comportamento", "behavior": "Comportamento",
    "strategy": "Estratégia", "damage taken from elements": "Dano recebido por elemento", "combat properties": "Combate",
    "hit points": "Vida", "experience points": "Experiência", "armor": "Armadura", "speed": "Velocidade", "description": "Descrição",
    "grade": "Grau", "points": "Pontos", "secret": "Secreto", "job": "Profissão", "city": "Cidade", "sells": "Vende", "buys": "Compra",
    "trivia": "Curiosidades", "price": "Preço", "creature": "Criatura", "attack": "Ataque", "defense": "Defesa", "level": "Nível",
    "required level": "Nível necessário", "vocation": "Vocação", "vocations": "Vocações", "words": "Palavras", "element": "Elemento",
    "effect": "Efeito", "implemented": "Implementado", "spoiler": "Spoiler", "related achievements": "Achievements relacionados",
    "general": "Geral", "caution": "Cuidado", "creatures": "Criaturas", "npcs": "NPCs", "items": "Itens", "quests": "Quests",
    "transcripts": "Transcrições", "properties": "Propriedades", "resistances": "Resistências", "immunities": "Imunidades",
    "bosses": "Bosses", "map": "Mapa", "history": "História", "requirements": "Requisitos", "reward": "Recompensa", "rewards": "Recompensas",
    "status": "Estado", "type": "Tipo", "premium": "Premium", "mana": "Mana", "soul points": "Soul points", "cooldown": "Cooldown",
    "group": "Grupo", "magic level": "Magic level", "spell id": "ID do feitiço", "price for vocations": "Preço",
    "summon/convince": "Invocar/convencer", "summon": "Invocar", "convince": "Convencer", "illusionable": "Pode ser ilusão",
    "pushable": "Pode ser empurrado", "push objects": "Empurra objetos", "sense invisible": "Deteta invisíveis",
    "paralysable": "Pode ser paralisado", "see also": "Ver também", "gallery": "Galeria", "buildings": "Edifícios",
    "streets": "Ruas", "attributes": "Atributos", "imbuement slots": "Slots de imbuement", "upgrade classification": "Classe de upgrade",
    "resist": "Resistência", "protection": "Proteção", "charges": "Cargas", "duration": "Duração", "slot": "Slot",
    "sounds": "Sons", "flavor text": "Texto", "book text": "Texto do livro", "contents": "Conteúdo",
  };
  function translateWiki(root) {
    $$("h2, h3, h4, th, .pi-data-label, .mw-headline", root).forEach((el) => {
      if (el.children.length > 1) return;
      const t = el.textContent.trim().toLowerCase();
      if (WIKI_LABELS[t]) {
        const target = el.querySelector(".mw-headline") || el;
        target.textContent = WIKI_LABELS[t];
      }
    });
  }

  let wikiQuery = "", wikiKind = "", wikiLimit = 120;
  function renderWikiHome() {
    const counts = {};
    S.wiki.pages.forEach((p) => (counts[p.k] = (counts[p.k] || 0) + 1));
    view().innerHTML = `
      <div class="toolbar"><h1>Wiki do Questski <span class="muted" style="font-size:18px">(${S.wiki.pages.length.toLocaleString("pt-PT")} páginas)</span></h1></div>
      <p class="muted" style="margin-top:-8px">Todos os itens, criaturas, NPCs, feitiços, locais e achievements referidos nos guias — com onde se compram, quem os larga, localização e muito mais.</p>
      <div class="wiki-search box"><div class="box-body">
        <input class="input" id="wikiQ" type="search" placeholder="Procurar na wiki: ex. Songs of the Forest, Dwarven Armor, Orc Warrior…" value="${esc(wikiQuery)}" autocomplete="off">
        <div class="cat-pills" style="margin-top:10px">
          <button class="cat-pill ${!wikiKind ? "on" : ""}" data-wk="">Tudo</button>
          ${Object.entries(WIKI_KINDS).filter(([k]) => counts[k]).map(([k, [l, ic]]) => `<button class="cat-pill ${wikiKind === k ? "on" : ""}" data-wk="${k}">${icon(ic)}${l} <span class="muted">${counts[k]}</span></button>`).join("")}
        </div></div></div>
      <div id="wikiResults"></div>`;
    const draw = () => {
      const words = fold(wikiQuery).split(/\s+/).filter(Boolean);
      let list = S.wiki.pages.filter((p) => (!wikiKind || p.k === wikiKind) && (!words.length || words.every((w) => (p._f || (p._f = fold(p.t))).includes(w))));
      if (words.length) {
        const aliasHits = Object.entries(S.wiki.alias).filter(([a]) => words.every((w) => fold(a).includes(w))).map(([, c]) => S.wiki.byLower[c.toLowerCase()]).filter(Boolean);
        list = [...new Set(list.concat(aliasHits))];
        const q = fold(wikiQuery);
        list.sort((a, b) => (fold(b.t) === q) - (fold(a.t) === q) || (fold(b.t).startsWith(q)) - (fold(a.t).startsWith(q)) || (b.q || 0) - (a.q || 0) || a.t.localeCompare(b.t));
      } else list.sort((a, b) => (b.q || 0) - (a.q || 0) || a.t.localeCompare(b.t));
      const shown = list.slice(0, wikiLimit);
      $("#wikiResults").innerHTML = `<p class="muted">${list.length.toLocaleString("pt-PT")} resultados${!words.length ? " · ordenados pelos mais usados nos guias" : ""}</p>
        <div class="ent-grid">${shown.map((p) => `<a class="ent-card" href="#/wiki/${encodeURIComponent(p.t)}"><span class="slot">${p.i ? `<img src="${p.i}" alt="" loading="lazy">` : icon(WIKI_KINDS[p.k]?.[1] || "book")}</span>
          <span style="min-width:0"><b>${esc(p.t)}</b><span>${WIKI_KINDS[p.k]?.[0] || ""}${p.q ? ` · em ${p.q} guia${p.q > 1 ? "s" : ""}` : ""}</span></span></a>`).join("")}</div>
        ${list.length > shown.length ? `<p style="text-align:center;margin-top:16px"><button class="btn btn-ghost" id="wikiMore">Mostrar mais (${list.length - shown.length})</button></p>` : ""}`;
      const more = $("#wikiMore");
      if (more) more.onclick = () => { wikiLimit += 240; draw(); };
    };
    draw();
    const input = $("#wikiQ");
    input.addEventListener("input", () => { wikiQuery = input.value; wikiLimit = 120; draw(); });
    if (!matchMedia("(hover: none)").matches) input.focus();
    $$("[data-wk]").forEach((b) => (b.onclick = () => { wikiKind = b.dataset.wk; wikiLimit = 120; $$("[data-wk]").forEach((x) => x.classList.toggle("on", x === b)); draw(); }));
  }

  const fmtPrice = (p) => (typeof p === "number" ? `${p.toLocaleString("pt-PT")} gp` : esc(p));
  const wikiSprite = (name) => { const e = wikiEntry(name); return e && e.i ? `<img src="${e.i}" alt="" loading="lazy">` : ""; };
  const linkOrText = (href, text) => (href ? `<a href="${href}">${esc(text)}</a>` : `<b>${esc(text)}</b>`);
  const miniCoord = (c, label) => `<div class="coord-card">${minimapHTML(c.x, c.y, c.z, null, label || "")}
      <div class="coord-info">${label ? `<span class="label">${esc(label)}</span>` : ""}<span class="xyz">${c.x}, ${c.y}, ${c.z} · ${floorLabel(c.z)}</span>${coordActions(c.x, c.y, c.z, label)}</div></div>`;

  function howtoHTML(p) {
    const h = p.howto;
    if (!h) return "";
    const parts = [];
    const summary = [];
    if (h.quests && h.quests.some((q) => q.kind === "reward")) summary.push("recompensa de quest");
    if (h.buy && h.buy.length) summary.push(`compra-se a ${h.buy.length} NPC${h.buy.length > 1 ? "s" : ""}`);
    if (h.drops && h.drops.length) summary.push(`largado por ${h.drops.length} criatura${h.drops.length > 1 ? "s" : ""}`);
    if (h.spots && h.spots.length) summary.push(`${h.spots.length} local${h.spots.length > 1 ? "is" : ""} assinalado${h.spots.length > 1 ? "s" : ""} no mapa`);

    if (h.quests && h.quests.length) {
      const label = { reward: "Recebes como recompensa", needed: "Precisas dele", mention: "Aparece no passo" };
      parts.push(`<div class="howto-block"><h3>${icon("scroll")}Nas quests do Questski</h3><ul class="howto-list">${h.quests.map((q) => {
        const href = q.step ? `#/quest/${q.slug}/guia/${q.step}` : `#/quest/${q.slug}`;
        const coords = (q.coords || []).map((c) => `<a class="coord-link" data-coord="${c.x},${c.y},${c.z}" data-label="${esc(c.label || q.title || "")}">${icon("pin")} ${c.x}, ${c.y}, ${c.z}${c.label ? ` — ${esc(plainText(c.label))}` : ""}</a>`).join(" ");
        return `<li><span class="howto-tag tag-${q.kind}">${label[q.kind]}</span> <a href="${href}"><b>${esc(q.quest)}</b>${q.step ? ` — passo ${q.n}: ${esc(plainText(q.title))}` : ""}</a>${q.qty ? ` (${q.qty}×)` : ""}${coords ? `<div class="howto-coords">${coords}</div>` : ""}</li>`;
      }).join("")}</ul></div>`);
    }
    if (h.buy && h.buy.length) {
      parts.push(`<div class="howto-block"><h3>${icon("bag")}Comprar a NPCs</h3><div class="tbl-wrap"><table class="tbl"><thead><tr><th>NPC</th><th>Onde</th><th>Preço</th><th>Mapa</th></tr></thead><tbody>
        ${h.buy.map((r) => `<tr><td>${wikiSprite(r.npc)} ${linkOrText(r.href, r.npc)}</td><td>${esc(r.where)}</td><td><b>${fmtPrice(r.price)}</b></td><td>${r.pos ? `<button class="btn btn-ghost btn-sm" data-coord="${r.pos.x},${r.pos.y},${r.pos.z}" data-label="${esc(r.npc)}">${icon("pin")}Ver</button>` : ""}</td></tr>`).join("")}
        </tbody></table></div></div>`);
    }
    if (h.drops && h.drops.length) {
      parts.push(`<div class="howto-block"><h3>${icon("skull")}Criaturas que o largam</h3><div class="drop-list">${h.drops.map((d) => {
        const places = (d.places || []).map((pl) => `<a class="coord-link" data-coord="${pl.x},${pl.y},${pl.z}" data-label="${esc(pl.name)}">${icon("pin")} ${esc(pl.name)}</a>`).join(" ");
        const spots = (d.spots || []).map((s) => `<a class="coord-link" data-coord="${s.x},${s.y},${s.z}" data-label="${esc(d.creature)}">${icon("pin")} ${s.x}, ${s.y}, ${s.z}</a>`).join(" ");
        return `<div class="drop-card">
          <div class="drop-head"><span class="slot">${wikiSprite(d.creature) || icon("skull")}</span>
            <div><div class="drop-name">${linkOrText(d.href, d.creature)}</div>
            <div class="drop-stats">${d.hp ? `${icon("checkCircle")} ${esc(d.hp)} HP` : ""}${d.exp ? ` · ${esc(d.exp)} XP` : ""}</div></div>
            ${d.pct != null ? `<span class="drop-pct ${d.rarity ? "r-" + d.rarity.replace(/ /g, "-") : ""}" title="Probabilidade de drop">${d.pct < 1 ? d.pct.toFixed(2) : d.pct.toFixed(1)}%${d.qty && d.qty !== "1" ? ` · ${esc(d.qty)}` : ""}<small>${esc(d.rarity || "")}</small></span>` : `<span class="drop-pct"><small>sem estatística</small></span>`}
          </div>
          ${d.loc ? `<p class="drop-loc"><b>Onde vive:</b> ${esc(d.loc)}</p>` : ""}
          ${places || spots ? `<div class="howto-coords">${places} ${spots}</div>` : ""}
        </div>`;
      }).join("")}</div></div>`);
    }
    if (h.spots && h.spots.length) {
      parts.push(`<div class="howto-block"><h3>${icon("pin")}Locais exatos indicados na wiki</h3><div class="coords">${h.spots.map((s) => miniCoord(s, s.text)).join("")}</div></div>`);
    }
    if (h.sell && h.sell.length) {
      parts.push(`<div class="howto-block"><h3>${icon("gift")}Vender a NPCs</h3><div class="tbl-wrap"><table class="tbl"><thead><tr><th>NPC</th><th>Onde</th><th>Paga</th><th>Mapa</th></tr></thead><tbody>
        ${h.sell.map((r) => `<tr><td>${wikiSprite(r.npc)} ${linkOrText(r.href, r.npc)}</td><td>${esc(r.where)}</td><td><b>${fmtPrice(r.price)}</b></td><td>${r.pos ? `<button class="btn btn-ghost btn-sm" data-coord="${r.pos.x},${r.pos.y},${r.pos.z}" data-label="${esc(r.npc)}">${icon("pin")}Ver</button>` : ""}</td></tr>`).join("")}
        </tbody></table></div></div>`);
    }
    if (!parts.length) return "";
    return `<section class="box howto"><h2 class="box-caption">${icon("flag")}Como obter${summary.length ? `<span class="cap-extra">${summary.join(" · ")}</span>` : ""}</h2><div class="box-body">${parts.join("")}</div></section>`;
  }

  async function renderWikiPage(title) {
    const e = wikiEntry(title);
    if (!e) {
      view().innerHTML = `<div class="note-box">Não há nenhuma página "${esc(title)}" na wiki do Questski. <a href="#/wiki">Procurar na wiki</a></div>`;
      return;
    }
    view().innerHTML = `<div class="loading">A abrir a página…</div>`;
    if (!S.wiki.cache[e.s]) S.wiki.cache[e.s] = getJSON(`data/wiki/${e.s}.json`);
    let p;
    try { p = await S.wiki.cache[e.s]; } catch (err) { delete S.wiki.cache[e.s]; view().innerHTML = `<div class="note-box">Não foi possível abrir esta página.</div>`; return; }
    if (S.route.name !== "wiki") return;
    document.title = `${p.t} · Wiki · Tibia Questski`;
    const kind = WIKI_KINDS[p.k] || WIKI_KINDS.outro;
    const quests = p.howto && p.howto.quests ? [] : (p.quests || []).map((s) => S.bySlug[s]).filter(Boolean);
    const pos = p.pos || (S.npcs[p.t] && S.npcs[p.t].x != null ? S.npcs[p.t] : null);
    view().innerHTML = `
      <article class="wiki-page">
        <header class="box wiki-head"><div class="box-body">
          <span class="slot wiki-sprite">${p.i ? `<img src="${p.i}" alt="">` : icon(kind[1])}</span>
          <div style="min-width:0">
            <div class="meta"><a class="chip" href="#/wiki">${icon("book")}Wiki</a><span class="chip chip-cat">${icon(kind[1])}${kind[0].replace(/s$/, "")}</span><a class="chip chip-grim" id="grimLink" hidden title="Preço no Market, onde cai, hunts e mais, no Grimório">${icon("ext")}Ver no Grimório</a></div>
            <h1>${esc(p.t)}</h1>
            <div class="hero-actions">
              <button class="btn btn-ghost btn-sm" id="wikiBack">‹ Voltar</button>
              ${pos ? `<button class="btn btn-sm" data-coord="${pos.x},${pos.y},${pos.z}" data-label="${esc(p.t)}">${icon("pin")}Ver no mapa</button>` : ""}
            </div>
          </div></div></header>
        ${(() => {
          const r = S.regions.find((x) => x.name === p.t);
          if (!r) return "";
          const qs = S.quests.filter((q) => q.region === r.name).sort((a, b) => (a.rec || a.lvl || 1) - (b.rec || b.lvl || 1));
          return `<section class="box"><h2 class="box-caption">${icon("scroll")}Quests de ${esc(r.name)}<span class="cap-extra">${r.main} da região · ${r.total} no total</span></h2><div class="box-body">
            <ul class="list-clean region-quests">${qs.map((q) => `<li>${lvlShield(q)}<a href="#/quest/${q.slug}" style="align-self:center">${esc(q.name)}</a></li>`).join("")}</ul>
            <p style="margin:10px 0 0"><a class="btn btn-sm" href="#/quests/regiao/${encodeURIComponent(r.name)}">${icon("list")}Ver todas as ${r.total} quests de ${esc(r.name)}</a></p></div></section>`;
        })()}
        ${placeFor(p.t) ? `<section class="box travel-panel"><h2 class="box-caption">${icon("map")}Como chegar e como sair<span class="cap-extra">${esc(placeFor(p.t).near ? "perto de " + placeFor(p.t).near : "")}</span></h2><div class="box-body">${travelBody(placeFor(p.t), { maxCoords: 6 })}</div></section>` : ""}
        ${howtoHTML(p)}
        ${quests.length || pos ? `<div class="wiki-side-grid">
          ${pos ? `<section class="box"><h2 class="box-caption">${icon("pin")}Onde está</h2><div class="coords" style="padding:12px"><div class="coord-card">${minimapHTML(pos.x, pos.y, pos.z, null, p.t)}
            <div class="coord-info"><span class="xyz">${pos.x}, ${pos.y}, ${pos.z} · ${floorLabel(pos.z)}</span>${coordActions(pos.x, pos.y, pos.z, p.t)}</div></div></div></section>` : ""}
          ${quests.length ? `<section class="box"><h2 class="box-caption">${icon("scroll")}Aparece nos guias (${quests.length})</h2><div class="box-body"><ul class="list-clean">
            ${quests.map((q) => `<li>${lvlShield(q)}<a href="#/quest/${q.slug}" style="align-self:center">${esc(q.name)}</a></li>`).join("")}</ul></div></section>` : ""}
        </div>` : ""}
        <section class="box"><h2 class="box-caption">${icon("book")}Ficha completa (TibiaWiki)</h2><div class="box-body wiki-content">${p.html}</div></section>
        <p class="muted" style="font-size:13.5px">Conteúdo copiado da TibiaWiki (tibia.fandom.com), licença CC BY-SA 3.0. Imagens © CipSoft GmbH.</p>
      </article>`;
    translateWiki($(".wiki-content"));
    hydrateMinimaps(view());
    QP.grimHref(p.k, p.t).then((h) => { const a = $("#grimLink"), sw = $("#swGrimorio"); if (!h || !a || S.route.name !== "wiki") return; a.href = h; a.hidden = false; if (sw) sw.href = h; });
    $("#wikiBack").onclick = () => (history.length > 1 ? history.back() : (location.hash = "#/wiki"));
    $$(".wiki-content img").forEach((img) => (img.onerror = () => img.remove()));
  }

  // ---------- acessos (what each quest unlocks)
  const UNLOCK_KINDS = {
    zona: ["Zonas", "map"], transporte: ["Transportes", "swap"], npc: ["NPCs", "users"], loja: ["Lojas e trocas", "bag"],
    funcionalidade: ["Funcionalidades", "spark"], missao: ["Abre outras quests", "scroll"],
  };
  function unlockLi(u, q) {
    const k = UNLOCK_KINDS[u.kind] || UNLOCK_KINDS.zona;
    const href = u.place ? wikiHref(u.place) : null;
    return `<li>${icon(k[1])}<div>
      ${q ? `<span class="unlock-quest">${lvlShield(q)}<a href="#/quest/${q.slug}"><b>${esc(q.name)}</b></a></span>` : ""}
      <b class="unlock-what">${href ? `<a href="${href}">${rich(u.what)}</a>` : rich(u.what)}</b> <span class="chip">${k[0].replace(/s$/, "").replace(/ e trocas$/, "")}</span>
      ${u.when ? `<div class="unlock-when">${rich(u.when)}</div>` : ""}${u.note ? `<div class="unlock-note">${rich(u.note)}</div>` : ""}</div></li>`;
  }
  /** Every unlock of every quest, flattened: [{u, q}] */
  const allUnlocks = () => S.quests.flatMap((q) => (q.unlocks || []).map((u) => ({ u, q })));
  /** Quests that unlock a given place (by place title or by name inside "what"). */
  function accessBy(title) {
    const t = fold(title);
    return allUnlocks().filter(({ u }) => (u.place && fold(u.place) === t) || fold(plainText(u.what)).includes(t));
  }

  let accessView = "area", accessKind = "";
  function renderAccessPage(query) {
    const q0 = query ? decodeURIComponent(query) : "";
    const all = allUnlocks();
    const nQuests = new Set(all.map((e) => e.q.slug)).size;
    view().innerHTML = `
      <div class="toolbar"><h1>${icon("key")} Acessos</h1></div>
      <p class="muted" style="margin-top:-6px">Que quests desbloqueiam cada zona, transporte, NPC ou funcionalidade — ${all.length} acessos em ${nQuests} quests.</p>
      <div class="box"><div class="box-body">
        <input class="input wiki-search-input" id="accQ" type="search" placeholder="Procura uma zona ou quest: ex. warzone, yalahar, djinn, isle of the kings…" value="${esc(q0)}" autocomplete="off">
        <div class="filter-row" style="margin-top:10px">
          <div class="seg">${[["area", "Por zona / acesso"], ["quest", "Por quest"]].map(([v, l]) => `<button data-accview="${v}" class="${accessView === v ? "on" : ""}">${l}</button>`).join("")}</div>
          <div class="cat-pills"><button class="cat-pill ${!accessKind ? "on" : ""}" data-acckind="">Tudo</button>${Object.entries(UNLOCK_KINDS).map(([k, [l, ic]]) => `<button class="cat-pill ${accessKind === k ? "on" : ""}" data-acckind="${k}">${icon(ic)}${l}</button>`).join("")}</div>
        </div></div></div>
      <div id="accResults"></div>`;
    const draw = () => {
      const words = fold($("#accQ").value).split(/\s+/).filter(Boolean);
      const hit = ({ u, q }) => (!accessKind || u.kind === accessKind) &&
        words.every((w) => fold([plainText(u.what), u.place, plainText(u.when || ""), q.name, (q.aka || []).join(" ")].join(" ")).includes(w));
      const list = all.filter(hit);
      const byLvl = (a, b) => (a.q.rec || a.q.lvl || 1) - (b.q.rec || b.q.lvl || 1);
      let html;
      if (accessView === "area") {
        const groups = new Map();
        list.forEach((e) => {
          const key = fold(e.u.place || plainText(e.u.what));
          if (!groups.has(key)) groups.set(key, { title: e.u.place || plainText(e.u.what), place: e.u.place, kind: e.u.kind, items: [] });
          groups.get(key).items.push(e);
        });
        const qf = words.join(" ");
        const rank = (g) => (!qf ? 0 : fold(g.title).startsWith(qf) ? 0 : fold(g.title).includes(qf) ? 1 : 2);
        const gs = [...groups.values()].sort((a, b) => rank(a) - rank(b) || a.title.localeCompare(b.title));
        html = gs.map((g) => {
          const href = g.place ? wikiHref(g.place) : null;
          const k = UNLOCK_KINDS[g.kind] || UNLOCK_KINDS.zona;
          return `<section class="acc-card"><h3>${icon(k[1])}${href ? `<a href="${href}">${esc(g.title)}</a>` : esc(g.title)}<span class="muted">${g.items.length} quest${g.items.length > 1 ? "s" : ""}</span></h3>
            <ul class="list-clean">${g.items.sort(byLvl).map(({ u, q }) => `<li>${lvlShield(q)}<div><a href="#/quest/${q.slug}"><b>${esc(q.name)}</b></a>${fold(plainText(u.what)) !== fold(g.title) ? ` — ${rich(u.what)}` : ""}
              ${u.when ? `<div class="unlock-when">${rich(u.when)}</div>` : ""}${u.note ? `<div class="unlock-note">${rich(u.note)}</div>` : ""}</div></li>`).join("")}</ul></section>`;
        }).join("");
      } else {
        const byQ = new Map();
        list.forEach((e) => { if (!byQ.has(e.q.slug)) byQ.set(e.q.slug, { q: e.q, us: [] }); byQ.get(e.q.slug).us.push(e.u); });
        html = [...byQ.values()].sort((a, b) => byLvl(a, b)).map(({ q, us }) => `<section class="acc-card"><h3>${lvlShield(q)}<a href="#/quest/${q.slug}">${esc(q.name)}</a></h3>
          <ul class="list-clean unlock-list">${us.map((u) => unlockLi(u)).join("")}</ul></section>`).join("");
      }
      $("#accResults").innerHTML = `<p class="muted">${list.length} resultado${list.length === 1 ? "" : "s"}</p><div class="acc-grid">${html}</div>` +
        (list.length ? "" : `<div class="note-box">Nada encontrado. Experimenta outro nome (em inglês, como no jogo).</div>`);
    };
    draw();
    const input = $("#accQ");
    input.addEventListener("input", draw);
    input.addEventListener("change", () => history.replaceState(null, "", `#/acessos/${encodeURIComponent(input.value)}`));
    if (!matchMedia("(hover: none)").matches) input.focus();
    $$("[data-accview]").forEach((b) => (b.onclick = () => { accessView = b.dataset.accview; $$("[data-accview]").forEach((x) => x.classList.toggle("on", x === b)); draw(); }));
    $$("[data-acckind]").forEach((b) => (b.onclick = () => { accessKind = b.dataset.acckind; $$("[data-acckind]").forEach((x) => x.classList.toggle("on", x === b)); draw(); }));
  }

  // ---------- map page
  let pageMap = null;
  function renderMapPage(arg) {
    view().innerHTML = `<div class="map-page">
      <div class="toolbar"><h1>Mapa do Tibia</h1>
        <form id="gotoForm" class="map-toolbar" style="margin:0">
          <input class="input" id="gotoInput" placeholder="x, y, z  (ex. 32369, 32241, 7)" style="width:240px">
          <button class="btn btn-sm" type="submit">${icon("pin")}Ir</button>
          <label class="check"><input type="checkbox" id="showQ" checked> inícios das quests</label>
        </form></div>
      <div class="map-host" id="pageMapHost" tabindex="0"></div>
      <p class="muted" style="font-size:14px;margin-top:8px">Clica no mapa para ver as coordenadas · ▲▼ ou PageUp/PageDown mudam de piso · os marcadores mostram o nível de cada quest (respeitam os filtros da barra lateral).</p></div>`;
    pageMap = TibiaMap($("#pageMapHost"), { quests: true });
    if (arg) {
      const [x, y, z] = arg.split(",").map((n) => parseInt(n, 10));
      if (x && y && z >= 0) pageMap.focusOn(x, y, z, "", 2);
    } else pageMap.map.setView(L.latLng(-(32241 - MAP.y0), 32369 - MAP.x0), -1);
    $("#gotoForm").onsubmit = (e) => {
      e.preventDefault();
      const n = ($("#gotoInput").value.match(/\d+/g) || []).map(Number);
      if (n.length >= 2) pageMap.focusOn(n[0], n[1], n[2] ?? 7, "", 2.5);
      else toast("Escreve as coordenadas como x, y, z");
    };
    $("#showQ").onchange = (e) => pageMap.setShowQuests(e.target.checked);
  }

  // ---------- progress page
  function renderProgress() {
    const groups = grouped(S.quests);
    const done = S.quests.filter((q) => isDone(q.slug));
    const inProg = S.quests.filter((q) => !isDone(q.slug) && stepsDone(q.slug) > 0);
    view().innerHTML = `
      <div class="toolbar"><h1>O meu progresso</h1>
        <button class="btn btn-ghost btn-sm" id="expP">${icon("download")}Exportar</button>
        <label class="btn btn-ghost btn-sm" style="cursor:pointer">${icon("upload")}Importar<input type="file" id="impP" accept="application/json" hidden></label>
        <button class="btn btn-ghost btn-sm" id="clrP">${icon("trash")}Apagar tudo</button></div>
      <section class="box"><h2 class="box-caption">${icon("layers")}Por nível<span class="cap-extra">${done.length}/${S.quests.length} concluídas</span></h2>
        <div class="box-body progress-rows">${groups.map((g, i) => g.length ? `<div class="progress-row"><span>${BANDS[i][2]}</span><span class="bar-lg"><i style="width:${Math.round(g.filter((q) => isDone(q.slug)).length / g.length * 100)}%;background:${bandColor(i)}"></i></span><span>${g.filter((q) => isDone(q.slug)).length}/${g.length}</span></div>` : "").join("")}</div></section>
      ${inProg.length ? `<section class="box"><h2 class="box-caption">${icon("clock")}Em curso (${inProg.length})</h2><div class="box-body"><div class="qgrid">${inProg.map(questCard).join("")}</div></div></section>` : ""}
      <section class="box"><h2 class="box-caption">${icon("checkCircle")}Concluídas (${done.length})</h2><div class="box-body">${done.length ? `<div class="qgrid">${done.map(questCard).join("")}</div>` : `<p class="muted">Ainda não marcaste nenhuma quest como concluída.</p>`}</div></section>
      <p class="muted" style="font-size:14px">O progresso fica guardado apenas neste navegador. Usa Exportar/Importar para o levar para outro computador.</p>`;
    $("#expP").onclick = () => {
      const blob = new Blob([JSON.stringify(S.progress, null, 1)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob); a.download = "tibia-questski-progresso.json"; a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    };
    $("#impP").onchange = (e) => {
      const file = e.target.files[0];
      if (!file) return;
      file.text().then((t) => { S.progress = Object.assign(S.progress, JSON.parse(t)); save("tq-progress", S.progress); toast("Progresso importado"); renderProgress(); renderList(); })
        .catch(() => toast("Ficheiro inválido"));
    };
    $("#clrP").onclick = () => { if (confirm("Apagar todo o progresso guardado?")) { S.progress = {}; save("tq-progress", S.progress); renderProgress(); renderList(); } };
  }

  // ---------------------------------------------------------------- router
  function parseRoute() {
    const h = location.hash.replace(/^#\/?/, "");
    const parts = h.split("/").filter((x) => x !== "").map(decodeURIComponent);
    return { name: parts[0] || "home", args: parts.slice(1) };
  }
  function render() {
    const prev = S.route;
    S.route = parseRoute();
    document.body.classList.remove("drawer-open");
    const sw = $("#swGrimorio"); if (sw) sw.href = "../";
    $$("#mainnav a").forEach((a) => a.classList.toggle("active", a.dataset.nav === (S.route.name === "quest" ? "quests" : S.route.name)));
    if (S.route.name !== "quest") { delete view().dataset.slug; document.title = "Tibia Questski"; }
    if (questMap && !(S.route.name === "quest" && S.route.args[1] === "mapa")) { questMap.map.remove(); questMap = null; }
    if (pageMap && S.route.name !== "mapa") { pageMap.map.remove(); pageMap = null; }
    switch (S.route.name) {
      case "quest": {
        const [slug, tab, anchor] = S.route.args;
        const sameView = prev.name === "quest" && prev.args[0] === slug && (prev.args[1] || "guia") === (tab || "guia");
        if (sameView && anchor) {
          const el = document.getElementById(anchor.startsWith("sec-") ? anchor : "step-" + anchor);
          if (el) { el.scrollIntoView({ behavior: "smooth", block: "start" }); return; }
        }
        renderQuest(slug, tab, anchor);
        return;
      }
      case "quests":
        // #/quests/regiao/Darashia filters by city; #/quests/regiao clears the region
        if (S.route.args[0] === "regiao") {
          const city = S.regions.find((r) => r.name.toLowerCase() === (S.route.args[1] || "").toLowerCase());
          setRegion(city ? city.name : "");
        }
        renderQuestsPage(); break;
      case "wiki":
        if (S.route.args[0]) { renderTabs(); renderList(); window.scrollTo(0, 0); renderWikiPage(S.route.args.join("/")); return; }
        renderWikiHome(); break;
      case "mapa": if (pageMap) { pageMap.map.remove(); pageMap = null; } renderMapPage(S.route.args[0]); break;
      case "progresso": renderProgress(); break;
      case "acessos": renderAccessPage(S.route.args.join("/")); break;
      default: renderHome();
    }
    renderTabs();
    renderList();
    window.scrollTo(0, 0);
  }

  // ---------------------------------------------------------------- global events
  function bindGlobal() {
    const themeBtn = $("#themeToggle");
    const paintTheme = () => { const dark = document.documentElement.dataset.theme === "dark"; themeBtn.innerHTML = icon(dark ? "sun" : "moon"); themeBtn.title = dark ? "Mudar para tema claro" : "Mudar para tema escuro"; };
    paintTheme();
    themeBtn.onclick = () => {
      const t = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
      document.documentElement.dataset.theme = t;
      try { localStorage.setItem("tq-theme", t); } catch (e) { /* ignore */ }
      paintTheme();
    };
    $("#menuBtn").innerHTML = icon("menu");
    $("#menuBtn").onclick = () => document.body.classList.toggle("drawer-open");
    $("#scrim").onclick = () => document.body.classList.remove("drawer-open");
    $(".search-ico").innerHTML = ICONS.search;
    $$("[data-close]").forEach((b) => (b.innerHTML = icon("close")));

    const search = $("#search");
    search.addEventListener("input", () => {
      S.filters.q = search.value;
      renderList();
      if (S.route.name === "quests") renderQuestsPage();
    });
    search.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        const list = filtered();
        if (list.length === 1) location.hash = `#/quest/${list[0].slug}`;
        else if (list.length === 0 || S.route.name === "wiki") {
          const hit = wikiEntry(search.value);
          wikiQuery = search.value; wikiLimit = 120;
          S.filters.q = ""; search.value = ""; renderList();
          location.hash = hit ? `#/wiki/${encodeURIComponent(hit.t)}` : "#/wiki";
          if (!hit && S.route.name === "wiki" && !S.route.args.length) renderWikiHome();
        } else location.hash = "#/quests";
        search.blur();
      } else if (e.key === "Escape") { search.value = ""; S.filters.q = ""; renderList(); search.blur(); }
    });

    document.addEventListener("click", (e) => {
      const t = e.target;
      const closeTabBtn = t.closest("[data-close-tab]");
      if (closeTabBtn) { e.preventDefault(); e.stopPropagation(); closeTab(closeTabBtn.dataset.closeTab); return; }
      if (t.closest("#tabsClear")) { const keep = S.route.name === "quest" ? [S.route.args[0]] : []; S.tabs = keep; save("tq-tabs", S.tabs); renderTabs(); return; }
      const npc = t.closest("[data-npc]");
      if (npc && !e.ctrlKey && !e.metaKey && S.npcs[npc.dataset.npc] && S.npcs[npc.dataset.npc].x != null) { e.preventDefault(); openNpc(npc.dataset.npc); return; }
      const say = t.closest("[data-say]");
      if (say) { copy(say.dataset.say, `Copiado: «${say.dataset.say}» — cola no chat do NPC`); return; }
      const cp = t.closest("[data-copy]");
      if (cp) { e.preventDefault(); copy(cp.dataset.copy); return; }
      const co = t.closest("[data-coord]");
      if (co) { e.preventDefault(); const [x, y, z] = co.dataset.coord.split(",").map(Number); openMap(x, y, z, co.dataset.label || ""); return; }
      const mm = t.closest(".minimap[data-mm]");
      if (mm && !mm.closest("[data-goregion]")) { const d = JSON.parse(mm.dataset.mm); openMap(d.x, d.y, d.z, mm.title !== "Abrir no mapa" ? mm.title : ""); return; }
      const shot = t.closest(".shot");
      if (shot) { openLightbox(shot); return; }
      const lb = $("#lightbox");
      if (!lb.hidden) {
        if (t.closest(".lb-prev")) return lbStep(-1);
        if (t.closest(".lb-next")) return lbStep(1);
        if (t.closest("[data-close]") || t === lb) { lb.hidden = true; return; }
      }
      const modal = $("#mapModal");
      if (!modal.hidden && (t.closest("[data-close]") || t === modal)) closeModal();
    });
    document.addEventListener("auxclick", (e) => {
      const tab = e.target.closest("[data-tab]");
      if (tab && e.button === 1) { e.preventDefault(); closeTab(tab.dataset.tab); }
    });
    document.addEventListener("change", (e) => {
      const c = e.target.closest("[data-check]");
      if (c) toggleStep(c.dataset.check, c.checked);
    });
    document.addEventListener("keydown", (e) => {
      const typing = /input|textarea|select/i.test(document.activeElement?.tagName || "");
      if (e.key === "Escape") {
        if (!$("#lightbox").hidden) $("#lightbox").hidden = true;
        else if (!$("#mapModal").hidden) closeModal();
        else document.body.classList.remove("drawer-open");
      } else if (!$("#lightbox").hidden && (e.key === "ArrowLeft" || e.key === "ArrowRight")) lbStep(e.key === "ArrowLeft" ? -1 : 1);
      else if (e.key === "/" && !typing) { e.preventDefault(); search.focus(); search.select(); }
      else if (e.key === "Enter" && e.target.matches(".minimap")) e.target.click();
    });
    window.addEventListener("hashchange", render);
    // o Grimório aberto noutro separador mudou de personagem ou marcou quests: atualiza o nível e as concluídas
    const grimSig = () => { const ch = QP.char(); return ch ? ch.name + "|" + ch.level + "|" + S.quests.filter((q) => QP.grimDone(q.slug)).length : ""; };
    let lastSig = grimSig();
    window.addEventListener("storage", (e) => {
      if (e.key !== "grimorio-tibia-v4" || grimSig() === lastSig) return;
      lastSig = grimSig();
      const ch = QP.char(); if (ch && ch.level && S.filters.lvlChar) S.filters.level = ch.level;
      const y = window.scrollY; renderFilters(); render(); window.scrollTo(0, y);
    });
  }

  // ---------------------------------------------------------------- boot
  async function boot() {
    view().innerHTML = `<div class="loading">A carregar as quests…</div>`;
    try {
      const [idx, images, npcs, wiki, places] = await Promise.all([getJSON("data/index.json"), getJSON("data/images.json").catch(() => ({})),
        getJSON("data/npcs.json").catch(() => ({})), getJSON("data/wiki-index.json").catch(() => ({ pages: [], alias: {} })),
        getJSON("data/places.json").catch(() => ({ places: {}, alias: {} }))]);
      Object.values(places.places || {}).forEach((p) => (S.places[p.title.toLowerCase()] = p));
      S.placeAlias = places.alias || {};
      S.quests = idx.quests;
      S.generated = idx.generated;
      S.regions = idx.regions || [];
      if (S.filters.region && !S.regions.some((r) => r.name === S.filters.region)) S.filters.region = "";
      S.images = images;
      S.npcs = npcs;
      S.quests.forEach((q) => {
        S.bySlug[q.slug] = q;
        S.questByName[q.name.toLowerCase()] = q.slug;
        (q.aka || []).forEach((a) => (S.questByName[a.toLowerCase()] ??= q.slug));
      });
      S.wiki.pages = wiki.pages;
      S.wiki.alias = wiki.alias || {};
      wiki.pages.forEach((p) => (S.wiki.byLower[p.t.toLowerCase()] = p));
      S.tabs = S.tabs.filter((s) => S.bySlug[s]);
      await QP.load();
      const ch = QP.char();
      if (ch && ch.level && (S.filters.level == null || S.filters.lvlChar)) { S.filters.level = ch.level; S.filters.lvlChar = true; }
    } catch (e) {
      view().innerHTML = `<div class="note-box"><b>Não foi possível carregar os dados.</b><br>Abre o site através do servidor local (<code>python serve.py</code>) e não diretamente pelo ficheiro.<br><span class="muted">${esc(e.message)}</span></div>`;
      return;
    }
    renderFilters();
    bindFilters();
    bindGlobal();
    render();
  }
  boot();
})();
