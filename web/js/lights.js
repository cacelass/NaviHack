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
  // Luz del Árbol y de la Noria: capas pintadas (assets/luces/*.png, 400 px del lienzo cada una; negro = sin luz) que se
  // SUMAN al mapa («screen») sobre la forma que ya tiene. Salen de una versión nocturna encendida de cada recorte
  // (pipeline/render/zona/lights_r3/): la luz sigue la celosía y los radios pintados, no unas cifras medidas a mano.
  const GLOWS = [
    { id: "concello-2552", box: [1415, 1300, 400], srcs: ["arbol-a.png", "arbol-b.png"], tree: true }, // rosa y azul hielo: el real cambia de color
    { id: "concello-3494", box: [4113, 1980, 400], srcs: ["noria-a.png"] },
  ];
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let viewer = null, P = null, tint = null, lamps = null, lampsLoading = false;
  let halos = [], glows = [], level = 0;

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
    const O = window.tinyvigoOcclusion; if (O) await O.ready; // GEO-02: no lamp glowing on a roof
    const m = window.tinyvigo.manifest, s = LAMP_SCALE;
    const cv = Object.assign(document.createElement("canvas"), { width: Math.round(m.width * s), height: Math.round(m.height * s) });
    const g = cv.getContext("2d");
    const R = 9; // radio de cada toque de luz a esta escala (≈ 9 m)
    const spr = Object.assign(document.createElement("canvas"), { width: 2 * R, height: 2 * R });
    const sg = spr.getContext("2d"), grad = sg.createRadialGradient(R, R, 0, R, R, R);
    // sin núcleo claro: un punto brillante suelto parece polvo; la luz es un charco ancho que cae suave
    grad.addColorStop(0, "rgba(255, 190, 110, .24)");
    grad.addColorStop(0.45, "rgba(255, 170, 90, .10)");
    grad.addColorStop(1, "rgba(255, 150, 70, 0)");
    sg.fillStyle = grad; sg.fillRect(0, 0, 2 * R, 2 * R);
    g.globalCompositeOperation = "lighter";
    // la luz recorre la calle: toques cada pocos px que se solapan en charcos bajo cada farola y se apagan entre ellas
    const STEP = 9;
    for (const line of doc.lines) {
      let prev = project(line[0][0], line[0][1]), run = 0;
      for (let i = 1; i < line.length; i++) {
        const cur = project(line[i][0], line[i][1]);
        const dx = cur[0] - prev[0], dy = cur[1] - prev[1], len = Math.hypot(dx, dy);
        for (let d = STEP - (run % STEP); d <= len; d += STEP) {
          const x = (prev[0] + (dx * d) / len) * s, y = (prev[1] + (dy * d) / len) * s;
          const k = Math.cos(((run + d) / LAMP_EVERY) * Math.PI), pool = 0.14 + 0.86 * k * k * k * k;
          if (x > -R && y > -R && x < cv.width + R && y < cv.height + R && !(O && O.hidden(x / s, y / s))) {
            g.globalAlpha = pool; g.drawImage(spr, x - R, y - R);
          }
        }
        run += len; prev = cur;
      }
    }
    g.globalAlpha = 1;
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

  // Árbol y Noria: una o dos capas «screen» alineadas con su recorte del mapa; solo cambia su opacidad
  function buildGlows() {
    const b = viewer.world.getItemAt(0).getBounds();
    glows = GLOWS.map((g) => {
      const o = { ...g, p: P.points.find((p) => p.id === g.id), items: [] };
      g.srcs.forEach((src, i) => viewer.addTiledImage({
        tileSource: { type: "image", url: "ui/assets/luces/" + src },
        x: b.x + g.box[0] / CANVAS, y: b.y + g.box[1] / CANVAS, width: g.box[2] / CANVAS,
        opacity: 0, compositeOperation: "screen", success: (e) => { o.items[i] = e.item; },
      }));
      return o;
    });
  }
  // sin animación (reduced motion) o con ella: pulso lento y, en el Árbol, paso de rosa a azul hielo cada ~14 s;
  // en los pases de música (treeShow) el brillo sube y parpadea a saltos, no con una onda suave
  function animate() {
    const t = performance.now() / 1000, on = Math.max(0, Math.min(1, (level - 0.3) / 0.4));
    for (const g of glows) {
      const lightOn = on > 0 && lit(g.p);
      const it = g.items;
      if (!it.length) continue;
      if (!lightOn) { it.forEach((i) => i && i.setOpacity(0)); continue; }
      let gain = reduced ? 0.9 : 0.86 + 0.1 * Math.sin(t * (g.tree ? 1.3 : 0.9));
      if (g.tree && treeShow()) gain = Math.min(1, gain + 0.1 + (Math.floor(t * 10) % 3 === 0 ? 0.1 : 0));
      let mix = 0;
      if (g.tree && !reduced) mix = 0.5 - 0.5 * Math.cos((t / 14) * Math.PI * 2); // 0 → 1 → 0
      if (it[0]) it[0].setOpacity(on * gain * (g.tree ? 1 - mix : 1));
      if (it[1]) it[1].setOpacity(on * gain * mix);
    }
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
    animate();
    document.body.classList.toggle("tv-lights-reduced", reduced);
  }

  function init() {
    viewer = window.tinyvigo && window.tinyvigo.viewer; P = window.tinyvigoPoints;
    if (!viewer || !P || !window.tinyvigoAmbient || !viewer.world.getItemCount()) { setTimeout(init, 200); return; }
    buildTint(); buildHalos(); buildGlows();
    if (!reduced) setInterval(() => { if (document.visibilityState === "visible" && level > 0.3) animate(); }, 66); // ~15 imágenes/s solo de noche
    level = window.tinyvigoAmbient.nightLevel();
    document.addEventListener("tv:night", (e) => { level = e.detail.level; paint(); });
    new MutationObserver(paint).observe(document.body, { attributes: true, attributeFilter: ["class"] });
    setInterval(paint, 60000); // horarios: encendido a las 18:00, apagado, pases de música
    paint();
  }
  window.tinyvigoLights = { paint, state: () => ({ level, tint: !!tint, lamps: !!lamps, halos: halos.length }) };
  if (window.tinyvigoPoints) init(); else document.addEventListener("tv:ready", init, { once: true });
})();
