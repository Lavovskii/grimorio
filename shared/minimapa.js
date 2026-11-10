/* Tibia Grimoire — minimapa (window.GrimMini; em node, module.exports). Recorte do maps/floor-NN-map.png num <canvas> com
   marcadores numerados (.mm-mark, CSS em shared/sites.css). Usado pelo Questski (passos dos guias) e pelo Grimório (troços do
   «Como lá chegar»). fit é puro (teste: node _dev/fichas_test.mjs); draw desenha.
   fit(pts, sel, W, H): pts = [[x,y,z]]; sel = índice do ponto escolhido → só os pontos do andar dele, e com pontos longe demais
   para a escala mínima (0,6) centra no escolhido; sel null → todos os pontos, centro da caixa (o minimapa do Questski).
   draw(el, o): o = {img (Image ou Promise), view {cx,cy,s} (senão fit das marcas), marks [{x,y,n,cls}], line}. */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.GrimMini = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";
  var X0 = 31744, Y0 = 30976;

  function fit(pts, sel, W, H) {
    if (!pts || !pts.length) return null;
    var hasSel = sel != null && !!pts[sel], z = pts[hasSel ? sel : 0][2], on = [];
    pts.forEach(function (p, i) { if (!hasSel || p[2] === z) on.push(i); });
    var xs = on.map(function (i) { return pts[i][0]; }), ys = on.map(function (i) { return pts[i][1]; });
    var minX = Math.min.apply(null, xs), maxX = Math.max.apply(null, xs), minY = Math.min.apply(null, ys), maxY = Math.max.apply(null, ys);
    var s = Math.max(0.6, Math.min(5, W / (maxX - minX + 12), H / (maxY - minY + 12)));
    var cx = (minX + maxX) / 2 + 0.5, cy = (minY + maxY) / 2 + 0.5;
    if (hasSel && ((maxX - minX + 12) * s > W || (maxY - minY + 12) * s > H)) { cx = pts[sel][0] + 0.5; cy = pts[sel][1] + 0.5; }
    return { z: z, on: on, cx: cx, cy: cy, s: s };
  }

  async function draw(el, o) {
    var img;
    try { img = await o.img; } catch (e) { return; }
    if (!img) return;
    var cw = el.clientWidth || 260, ch = el.clientHeight || 173, marks = o.marks || [], v = o.view;
    if (!v) {
      v = fit(marks.map(function (m) { return [m.x, m.y, m.z]; }), o.sel == null ? 0 : o.sel, cw, ch);
      if (!v) return;
      marks = v.on.map(function (i) { return marks[i]; });
    }
    var cx = v.cx - X0, cy = v.cy - Y0, s = v.s;
    var dpr = window.devicePixelRatio || 1;
    var cv = el.querySelector("canvas");
    cv.width = Math.round(cw * dpr); cv.height = Math.round(ch * dpr);
    cv.style.width = cw + "px"; cv.style.height = ch + "px";
    var ctx = cv.getContext("2d");
    ctx.imageSmoothingEnabled = false;
    var sw = cw / s, sh = ch / s, sx = cx - sw / 2, sy = cy - sh / 2;
    ctx.fillStyle = "#000"; ctx.fillRect(0, 0, cv.width, cv.height);
    ctx.drawImage(img, sx, sy, sw, sh, 0, 0, cv.width, cv.height);
    el.querySelectorAll(".mm-mark").forEach(function (m) { m.remove(); });
    var xy = function (m) { return [(m.x - X0 + 0.5 - sx) * s, (m.y - Y0 + 0.5 - sy) * s]; };
    if (o.line && marks.length > 1) {
      // linha tracejada entre marcadores seguidos (a ordem dos passos, não o caminho a pé)
      ctx.save(); ctx.scale(dpr, dpr); ctx.globalAlpha = 0.6; ctx.lineWidth = 2; ctx.setLineDash([6, 4]);
      ctx.strokeStyle = o.color || "#f3c33b"; ctx.beginPath();
      marks.forEach(function (m, i) { var p = xy(m); if (i) ctx.lineTo(p[0], p[1]); else ctx.moveTo(p[0], p[1]); });
      ctx.stroke(); ctx.restore();
    }
    marks.forEach(function (m) {
      var e = document.createElement("span"), p = xy(m);
      e.className = "mm-mark " + (m.cls || "");
      e.style.left = p[0] + "px"; e.style.top = p[1] + "px";
      if (m.n) e.dataset.n = m.n;
      el.appendChild(e);
    });
  }

  return { X0: X0, Y0: Y0, fit: fit, draw: draw };
});
