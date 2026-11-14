// TinyVigo mini-mapa (MAP-01): el lienzo entero en pequeño, con el rectángulo de lo que se está
// viendo. Se puede arrastrar o tocar para mover la vista. Superficie sólida, sin sombras.
(function () {
  function init() {
    const viewer = window.tinyvigo && window.tinyvigo.viewer;
    const m = window.tinyvigo && window.tinyvigo.manifest;
    if (!viewer || !m) return;
    const canvas = m.canvas || { width: m.width, height: m.height };
    const off = m.offset || { x: 0, y: 0 };
    const base = "tiles/" + m.version + "/";

    const box = document.createElement("div");
    box.className = "tv-minimap";
    box.setAttribute("role", "img");
    box.setAttribute("aria-label", (window.tinyvigoPoints ? window.tinyvigoPoints.t("minimap.label") : "Mini-mapa: vista general"));
    const img = document.createElement("img");
    img.alt = "";
    img.src = base + m.min_level + "/0_0." + m.format;
    img.draggable = false;
    const frame = document.createElement("span");
    frame.className = "tv-minimap-view";
    box.append(img, frame);
    document.body.append(box);

    const frac = (ix, iy) => [((off.x + ix) / canvas.width), ((off.y + iy) / canvas.height)];
    const place = () => {
      const r = viewer.viewport.viewportToImageRectangle(viewer.viewport.getBounds());
      const [x0, y0] = frac(r.x, r.y);
      const [x1, y1] = frac(r.x + r.width, r.y + r.height);
      const left = Math.max(0, Math.min(1, Math.min(x0, x1)));
      const top = Math.max(0, Math.min(1, Math.min(y0, y1)));
      const right = Math.max(0, Math.min(1, Math.max(x0, x1)));
      const bottom = Math.max(0, Math.min(1, Math.max(y0, y1)));
      frame.style.left = left * 100 + "%";
      frame.style.top = top * 100 + "%";
      frame.style.width = Math.max(2, (right - left) * 100) + "%";
      frame.style.height = Math.max(2, (bottom - top) * 100) + "%";
    };
    ["open", "animation", "animation-finish", "resize", "zoom"].forEach((ev) => viewer.addHandler(ev, place));
    place();

    // tocar o arrastrar el mini-mapa mueve la vista al mismo sitio
    let dragging = false;
    const go = (ev) => {
      const r = box.getBoundingClientRect();
      const px = Math.max(0, Math.min(1, (ev.clientX - r.left) / r.width));
      const py = Math.max(0, Math.min(1, (ev.clientY - r.top) / r.height));
      const ix = (px * canvas.width - off.x) / m.width;
      const iy = (py * canvas.height - off.y) / m.height;
      viewer.viewport.panTo(new OpenSeadragon.Point(ix, iy));
      viewer.viewport.applyConstraints();
    };
    box.addEventListener("pointerdown", (ev) => { dragging = true; box.setPointerCapture(ev.pointerId); go(ev); });
    box.addEventListener("pointermove", (ev) => { if (dragging) go(ev); });
    box.addEventListener("pointerup", (ev) => { dragging = false; box.releasePointerCapture(ev.pointerId); });
    box.addEventListener("pointercancel", () => { dragging = false; });

    document.addEventListener("tv:lang", () => box.setAttribute("aria-label", window.tinyvigoPoints ? window.tinyvigoPoints.t("minimap.label") : "Mini-mapa"));
    window.tinyvigoMinimap = { refresh: place };
  }

  // el visor se crea cuando terminan los fetch del manifiesto: se espera sin bloquear
  if (window.tinyvigo && window.tinyvigo.manifest) init();
  else {
    const timer = setInterval(() => {
      if (window.tinyvigo && window.tinyvigo.manifest) { clearInterval(timer); init(); }
    }, 150);
    setTimeout(() => clearInterval(timer), 30_000);
  }
})();
