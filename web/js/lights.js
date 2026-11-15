// NaviVigo: la luz de la noche, por código (LIGHT-03). El mapa está pintado de día; la noche se
// compone encima sin tocar las teselas:
// - Tinte: el mapa se MULTIPLICA por el azul medido en pipeline/arbol_noche.py (NIGHT_TINT, del par
//   día/noche del bloque), en vez de un velo gris encima: los tejados siguen teniendo su color.
// - Farolas: un brillo cálido cada ~32 m por las calles de OSM (data/street-lamps.json), pintado una
//   sola vez en un canvas. Se encienden con la puesta de sol.
// - Luces de Navidad: un halo por punto, solo mientras su horario oficial dice que están encendidas.
// - El Árbol de Porta do Sol y la Noria de Vialia: su luz, dibujada sobre la forma pintada.
// Coste: tinte y farolas son dos capas más del canvas de OpenSeadragon («multiply» y «screen»; con
// opacidad 0, de día, no se dibujan) y el resto son unos pocos overlays que solo animan opacity/transform.
(function () {
  const CANVAS = 3072; // 1 unidad del visor = 3072 px del lienzo (como el SVG de la ruta, tour.js)
  const TINT = "rgb(74, 101, 177)"; // NIGHT_TINT (0.292, 0.396, 0.696) × 255
  const LAMP_EVERY = 64; // px del lienzo entre farolas (2 px/m → 32 m, lo habitual en una calle)
  const LAMP_SCALE = 0.5; // la capa de farolas se pinta a media resolución: es luz difusa
  // forma pintada del Árbol y de la Noria en las teselas actuales (px del lienzo, medido en v11)
  const TREE = { apex: [1620, 1408], base: [1613, 1596], rx: 36, ry: 10 };
  const WHEEL = { c: [4314, 2182], r: 53 };
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let viewer = null, P = null, tint = null, lamps = null, lampsLoading = false;
  let halos = [], tree = null, wheel = null, level = 0;

  const vp = (x, y) => new OpenSeadragon.Point(x / CANVAS, y / CANVAS);
  const rect = (x, y, w, h) => new OpenSeadragon.Rect(x / CANVAS, y / CANVAS, w / CANVAS, h / CANVAS);
  const SVG = "http://www.w3.org/2000/svg";
  const svgEl = (tag, attrs) => { const n = document.createElementNS(SVG, tag); for (const k in attrs) n.setAttribute(k, attrs[k]); return n; };

  // una capa más del visor, alineada con la imagen del mapa
  function addLayer(url, op, done) {
    const b = viewer.world.getItemAt(0).getBounds();
    viewer.addTiledImage({ tileSource: { type: "image", url }, x: b.x, y: b.y, width: b.width, opacity: 0, compositeOperation: op, success: (e) => done(e.item) });
  }

  function buildTint() {
    // same proportions as the map: a square tint made the world 1.67 tall and let the view slide
    // past the bottom of the drawing into the empty background
    const m = window.tinyvigo.manifest, cw = Math.round(m.width / 256), ch = Math.round(m.height / 256);
    const c = Object.assign(document.createElement("canvas"), { width: cw, height: ch });
    const g = c.getContext("2d"); g.fillStyle = TINT; g.fillRect(0, 0, cw, ch);
    addLayer(c.toDataURL(), "multiply", (item) => { tint = item; paint(); });
  }

  // farolas: brillo cálido con un punto claro en el centro, sumados («lighter») en un solo canvas
  async function buildLamps() {
    if (lamps || lampsLoading) return;
    lampsLoading = true;
    const project = window.tinyvigoGeo && window.tinyvigoGeo.project;
    let doc;
    try { doc = await (await fetch("data/street-lamps.json")).json(); } catch (e) { return; }
    const m = window.tinyvigo.manifest, s = LAMP_SCALE;
    const cv = Object.assign(document.createElement("canvas"), { width: Math.round(m.width * s), height: Math.round(m.height * s) });
    const g = cv.getContext("2d");
    const R = 7; // radio del charco de luz a esta escala (≈ 7 m)
    const spr = Object.assign(document.createElement("canvas"), { width: 2 * R, height: 2 * R });
    const sg = spr.getContext("2d"), grad = sg.createRadialGradient(R, R, 0, R, R, R);
    grad.addColorStop(0, "rgba(255, 228, 170, .85)");
    grad.addColorStop(0.15, "rgba(255, 196, 120, .42)");
    grad.addColorStop(0.5, "rgba(255, 170, 90, .1)");
    grad.addColorStop(1, "rgba(255, 160, 80, 0)");
    sg.fillStyle = grad; sg.fillRect(0, 0, 2 * R, 2 * R);
    g.globalCompositeOperation = "lighter";
    for (const line of doc.lines) {
      let prev = project(line[0][0], line[0][1]), carry = LAMP_EVERY / 2;
      for (let i = 1; i < line.length; i++) {
        const cur = project(line[i][0], line[i][1]);
        const dx = cur[0] - prev[0], dy = cur[1] - prev[1], len = Math.hypot(dx, dy);
        let d = carry;
        while (d <= len) {
          const x = (prev[0] + (dx * d) / len) * s, y = (prev[1] + (dy * d) / len) * s;
          if (x > -R && y > -R && x < cv.width + R && y < cv.height + R) g.drawImage(spr, x - R, y - R);
          d += LAMP_EVERY;
        }
        carry = d - len; prev = cur;
      }
    }
    cv.toBlob((blob) => addLayer(URL.createObjectURL(blob), "screen", (item) => { lamps = item; paint(); }));
  }

  // halos de Navidad: el de antes (ambient.js), ahora en «screen» y solo si el punto está encendido
  function buildHalos() {
    const PAINTED = new Set(["concello-2552", "concello-3494"]); // el Árbol y la Noria llevan su propia luz
    P.points.filter((p) => p.on_map && !PAINTED.has(p.id) && ["light", "attraction", "market", "santa_kings"].includes(p.type)).forEach((p, i) => {
      const h = document.createElement("span");
      h.className = "tv-glow tv-glow-" + p.type;
      h.style.setProperty("--d", ((i * 0.37) % 3).toFixed(2) + "s");
      const r = 0.0075; // ~40 m de radio: escala con el mapa
      viewer.addOverlay({ element: h, location: new OpenSeadragon.Rect(p.x - r, p.y - r * 0.8, 2 * r, 1.6 * r) });
      halos.push({ el: h, p });
    });
  }

  // Each animated part is its own <svg> inside an HTML box and only whole elements animate
  // (opacity, transform): the compositor moves them. Animating nodes inside one SVG made the browser
  // recalculate style every frame (~80 ms/s at night with the map still, LIGHT-03 measure).
  function layer(cls, viewBox, ...kids) {
    const s = svgEl("svg", { viewBox, class: cls, preserveAspectRatio: "none" });
    s.append(...kids);
    return s;
  }
  function box(cls, x, y, w, h, ...layers) {
    const d = document.createElement("div");
    d.className = "tv-light " + cls;
    d.append(...layers);
    viewer.addOverlay({ element: d, location: rect(x, y, w, h) });
    return d;
  }

  // el Árbol real: celosía cónica con tiras LED blancas y cian de arriba abajo, aros y la estrella roja
  function buildTree() {
    const [ax, ay] = TREE.apex, [bx, by] = TREE.base, pad = 30;
    const x0 = bx - TREE.rx - pad, y0 = ay - pad - 14, w = 2 * (TREE.rx + pad), h = by + TREE.ry + pad - y0;
    const vb = [x0, y0, w, h].join(" ");
    const back = svgEl("g", { class: "tv-tree-back" }), front = svgEl("g", { class: "tv-tree-front" });
    const N = 22;
    for (let k = 0; k < N; k++) {
      const a = (k / N) * Math.PI * 2, ex = bx + Math.cos(a) * TREE.rx, ey = by + Math.sin(a) * TREE.ry;
      const isFront = Math.sin(a) > 0; // la mitad de abajo de la elipse queda delante
      (isFront ? front : back).append(svgEl("line", { x1: ax, y1: ay + 6, x2: ex, y2: ey }));
    }
    for (let j = 1; j <= 6; j++) { // aros: a lo largo del cono, más anchos abajo
      const t = j / 6.4, cx = ax + (bx - ax) * t, cy = ay + 6 + (by - ay - 6) * t;
      front.append(svgEl("ellipse", { cx, cy, rx: TREE.rx * t, ry: TREE.ry * t }));
    }
    // destellos sueltos sobre la celosía, en dos tandas que se alternan
    const sparks = [svgEl("g", {}), svgEl("g", {})];
    for (let k = 0; k < 26; k++) {
      const t = 0.12 + ((k * 37) % 100) / 115, a = k * 2.4;
      sparks[k % 2].append(svgEl("circle", { cx: ax + (bx - ax) * t + Math.cos(a) * TREE.rx * t * 0.9, cy: ay + 6 + (by - ay - 6) * t + Math.sin(a) * TREE.ry * t, r: 0.9 }));
    }
    const star = svgEl("g", { class: "tv-tree-star" });
    const sg = svgEl("radialGradient", { id: "tv-star-glow" });
    sg.append(svgEl("stop", { offset: "0", "stop-color": "rgba(255,90,60,.55)" }), svgEl("stop", { offset: "1", "stop-color": "rgba(255,60,40,0)" }));
    const pg = svgEl("radialGradient", { id: "tv-pool-glow" });
    pg.append(svgEl("stop", { offset: "0", "stop-color": "rgba(140,225,255,.3)" }), svgEl("stop", { offset: "1", "stop-color": "rgba(120,220,255,0)" }));
    const defs = svgEl("defs", {}); defs.append(sg, pg);
    star.append(svgEl("circle", { cx: ax, cy: ay - 2, r: 18, class: "tv-tree-star-halo" }));
    for (let k = 0; k < 12; k++) { const a = (k / 12) * Math.PI * 2, l = k % 2 ? 9 : 14; star.append(svgEl("line", { x1: ax, y1: ay - 2, x2: ax + Math.cos(a) * l, y2: ay - 2 + Math.sin(a) * l })); }
    const pool = svgEl("ellipse", { cx: bx, cy: by + 2, rx: TREE.rx + 22, ry: TREE.ry + 12, class: "tv-tree-pool" }); // luz sobre la plaza
    const bloom = front.cloneNode(true); bloom.setAttribute("class", "tv-tree-bloom"); // brillo: la misma celosía, ancha y tenue
    const el = box("tv-tree", x0, y0, w, h,
      layer("tv-tree-still", vb, defs, pool, back),
      layer("tv-tree-glow", vb, bloom, front, star), // respira
      layer("tv-tree-spark tv-tree-spark-a", vb, sparks[0]),
      layer("tv-tree-spark tv-tree-spark-b", vb, sparks[1]));
    tree = { el, p: P.points.find((p) => p.id === "concello-2552") };
  }

  // la Noria: aro de bombillas de colores que gira despacio, radios encendidos y su resplandor
  function buildWheel() {
    const { c: [cx, cy], r } = WHEEL, pad = 26, size = 2 * (r + pad), vb = [cx - r - pad, cy - r - pad, size, size].join(" ");
    const wg = svgEl("radialGradient", { id: "tv-wheel-glow" });
    wg.append(svgEl("stop", { offset: ".55", "stop-color": "rgba(255,120,200,.22)" }), svgEl("stop", { offset: "1", "stop-color": "rgba(255,120,200,0)" }));
    const defs = svgEl("defs", {}); defs.append(wg);
    const spin = [];
    for (let k = 0; k < 16; k++) { const a = (k / 16) * Math.PI * 2; spin.push(svgEl("line", { x1: cx, y1: cy, x2: cx + Math.cos(a) * r, y2: cy + Math.sin(a) * r, class: "tv-wheel-spoke" })); }
    ["#ff5b9a", "#ffd166", "#5be1ff"].forEach((col, i) => spin.push(svgEl("circle", { cx, cy, r, class: "tv-wheel-rim", stroke: col, "stroke-dashoffset": (i * 7).toFixed(1) })));
    const el = box("tv-wheel", cx - r - pad, cy - r - pad, size, size,
      layer("tv-wheel-still", vb, defs, svgEl("circle", { cx, cy, r: r + 22, class: "tv-wheel-halo" })),
      layer("tv-wheel-spin", vb, ...spin), // gira entero: el centro de la caja es el eje
      layer("tv-wheel-still", vb, svgEl("circle", { cx, cy, r: 2.5, class: "tv-wheel-hub" })));
    wheel = { el, p: P.points.find((p) => p.id === "concello-3494") };
  }

  // ¿encendido? El horario oficial manda; con «Noche» forzada se mira a las 20:00 de hoy, para que
  // la vista de noche enseñe la Navidad encendida aunque se mire a mediodía.
  function lit(p) {
    if (!p) return false;
    const forced = window.tinyvigoAmbient && window.tinyvigoAmbient.state().time === "night";
    const at = new Date(); if (forced) at.setHours(20, 0, 0, 0);
    const st = P.status(p, at);
    return st ? st.open : true; // sin horario publicado: se da por encendido de noche
  }
  // los pases de música del Árbol (18:00, 19:00, 20:00, 21:00 y 21:50, 10 min): más brillo
  function treeShow() {
    const d = new Date(), m = d.getHours() * 60 + d.getMinutes();
    return [1080, 1140, 1200, 1260, 1310].some((s) => m >= s && m < s + 10);
  }

  function paint() {
    const city = document.body.classList.contains("is-city"), on = city ? 0 : level;
    if (tint) tint.setOpacity(on);
    // las farolas se encienden un poco después de la puesta (nivel 0,15) y del todo al rato
    const street = Math.max(0, Math.min(1, (on - 0.15) / 0.35));
    if (lamps) lamps.setOpacity(street * 0.8);
    if (street > 0 && !lamps) buildLamps();
    const show = on > 0.3;
    for (const h of halos) h.el.style.display = show && lit(h.p) ? "" : "none";
    if (tree) { tree.el.style.display = show && lit(tree.p) ? "" : "none"; tree.el.classList.toggle("is-show", treeShow()); }
    if (wheel) wheel.el.style.display = show && lit(wheel.p) ? "" : "none";
    document.body.classList.toggle("tv-lights-reduced", reduced);
  }

  function init() {
    viewer = window.tinyvigo && window.tinyvigo.viewer; P = window.tinyvigoPoints;
    if (!viewer || !P || !window.tinyvigoAmbient || !viewer.world.getItemCount()) { setTimeout(init, 200); return; }
    buildTint(); buildHalos(); buildTree(); buildWheel();
    // the Árbol and the Noria only animate while they are on screen
    if ("IntersectionObserver" in window) {
      const io = new IntersectionObserver((es) => es.forEach((e) => e.target.classList.toggle("is-offscreen", !e.isIntersecting)));
      io.observe(tree.el); io.observe(wheel.el);
    }
    level = window.tinyvigoAmbient.nightLevel();
    document.addEventListener("tv:night", (e) => { level = e.detail.level; paint(); });
    new MutationObserver(paint).observe(document.body, { attributes: true, attributeFilter: ["class"] });
    setInterval(paint, 60000); // horarios: encendido a las 18:00, apagado, pases de música
    paint();
  }
  window.tinyvigoLights = { paint, state: () => ({ level, tint: !!tint, lamps: !!lamps, halos: halos.length }) };
  if (window.tinyvigoPoints) init(); else document.addEventListener("tv:ready", init, { once: true });
})();
