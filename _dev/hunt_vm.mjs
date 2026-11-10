// O motor das hunts do index.html (G, huntRows, huntEst pelo GrimFicha, estAdj, avgMon, compatFor…) num node:vm, sem browser.
// Usado por _dev/huntest_gold.mjs e _dev/calib_node.mjs. huntVm(F) → contexto; F = o shared/fichas.js (ou uma cópia mudada).
// C() devolve {level: ctx.LV} (muda o ctx.LV para mudar o nível da "personagem").
import fs from "node:fs";
import vm from "node:vm";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
export const Fichas = require("../shared/fichas.js");

export function huntVm(F = Fichas) {
  const html = fs.readFileSync(new URL("../index.html", import.meta.url), "utf8");
  const take = (a, b, from = 0) => { const s = html.indexOf(a, from); if (s < 0) throw new Error("sem " + a); const e = html.indexOf(b, s); if (e < 0) throw new Error("sem " + b); return html.slice(s, e); };
  const G = JSON.parse(html.match(/<script[^>]*id="G"[^>]*>([\s\S]*?)<\/script>/)[1]);
  const ctx = { G, GrimFicha: F, ST: { ui: {} }, LV: 100, hasKey: (o, k) => !!o && Object.prototype.hasOwnProperty.call(o, k), cap1: s => s };
  ctx.C = () => ({ level: ctx.LV });
  vm.createContext(ctx);
  const app = html.indexOf("<script>\n(function(){");
  vm.runInContext([take("const VOCS = ", "\n", app), take("const ELN = ", "\n", app),
    take("/* ---------- hunts ---------- */", '// "segura": risco 1', app)].join("\n"), ctx);
  return ctx;
}
