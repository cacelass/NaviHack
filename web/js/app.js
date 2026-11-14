// TinyVigo viewer: tiles come from tiles/<version>/ (version in tiles/current.json).
(async function () {
  // Si vendor/openseadragon no llegó a ejecutarse (primera carga con caché vacía), se reintenta.
  const need = (ok, src) => ok() ? null : new Promise((res, rej) => { const s = document.createElement("script"); s.src = src + "?r=" + Date.now(); s.onload = res; s.onerror = rej; document.head.append(s); });
  await need(() => window.OpenSeadragon, "vendor/openseadragon.min.js");
  const t0 = performance.now();
  const current = await (await fetch("tiles/current.json")).json();
  const base = "tiles/" + current.version + "/";
  const m = await (await fetch(base + "manifest.json")).json();
  // MAP-01: los niveles más gruesos se precargan en paralelo (son pocas teselas) y el
  // visor arranca con ellos ya en caché; los del primer vistazo los pide OSD a la vez.
  const preload = (level) => {
    const lv = m.levels && m.levels[level];
    if (!lv) return;
    for (let y = 0; y < lv.rows; y++) for (let x = 0; x < lv.cols; x++) {
      const im = new Image();
      im.src = base + level + "/" + x + "_" + y + "." + m.format;
    }
  };
  preload(m.min_level);
  preload(m.min_level + 1);

  // el mapa es pixel art: dibujarlo a la densidad de la pantalla (2x, 3x) multiplica el trabajo de
  // cada fotograma sin ganar nitidez (se escala con image-rendering: pixelated). Se dibuja a 1x.
  OpenSeadragon.pixelDensityRatio = 1;
  const viewer = OpenSeadragon({
    id: "map",
    showNavigationControl: false,
    showRotationControl: false,
    gestureSettingsMouse: { clickToZoom: false },
    animationTime: 0.6,
    maxZoomPixelRatio: 6,
    homeFillsViewer: true,
    visibilityRatio: 1,
    constrainDuringPan: true,
    immediateRender: true,
    imageSmoothingEnabled: false,
    tileSources: (() => {
      const source = {
        width: m.width,
        height: m.height,
        tileSize: m.tile_size,
        minLevel: m.min_level,
        maxLevel: m.max_level,
        getTileUrl: (level, x, y) => base + level + "/" + x + "_" + y + "." + m.format,
      };
      // An image that covers only part of the georeferenced canvas is placed at its real position.
      if (!m.canvas) return source;
      return { tileSource: new OpenSeadragon.TileSource(source), x: m.offset.x / m.canvas.width, y: m.offset.y / m.canvas.width, width: m.width / m.canvas.width };
    })(),
  });
  // The home view covers the whole screen; it is also the farthest you can zoom out.
  const fit = (goHome) => {
    const vp = viewer.viewport;
    vp.minZoomLevel = vp.getHomeZoom();
    if (goHome) {
      vp.goHome(true);
      // MOB-02: en un móvil vertical «home» encaja todo el alto del lienzo (mucho mar); arrancamos
      // ya en el núcleo navideño (Porta do Sol = centro del lienzo). Alejar sigue llegando al todo.
      if (matchMedia("(max-width: 700px)").matches) {
        vp.zoomTo(vp.getHomeZoom() * 1.7, null, true);
        vp.panTo(new OpenSeadragon.Point(0.5, 0.53), true);
      }
    }
    vp.applyConstraints(true);
  };
  viewer.addHandler("open", () => {
    fit(true);
    // MAP-01: tiempo del primer vistazo (criterio 6), medido desde el inicio del script.
    performance.mark("tv-first-view");
    window.tinyvigoPerf = { firstViewMs: Math.round(performance.now() - t0) };
    console.info("TinyVigo primer vistazo:", window.tinyvigoPerf.firstViewMs + " ms");
  });
  viewer.addHandler("resize", () => fit(false));
  viewer.addHandler("tile-load-failed", (e) => console.warn("tile failed", e.tile && e.tile.url, e.message));
  const zoomBy = (f) => { viewer.viewport.zoomBy(f); viewer.viewport.applyConstraints(); };
  // MAP-01: fps mientras se mueve el mapa (criterio 5). Se mide en el dispositivo real:
  // consola -> tinyvigoPerf.lastPanFps; no se envía a ningún sitio.
  let frames = 0, fpsStart = 0, raf = 0;
  const countFrame = () => { frames++; raf = requestAnimationFrame(countFrame); };
  viewer.addHandler("animation-start", () => {
    frames = 0; fpsStart = performance.now(); cancelAnimationFrame(raf); raf = requestAnimationFrame(countFrame);
  });
  viewer.addHandler("animation-finish", () => {
    cancelAnimationFrame(raf);
    const ms = performance.now() - fpsStart;
    if (ms > 120 && frames) {
      const fps = Math.round((frames * 1000) / ms);
      (window.tinyvigoPerf ||= {}).lastPanFps = fps;
      console.info("TinyVigo pan:", fps + " fps");
    }
  });
  document.getElementById("zoom-in").onclick = () => zoomBy(1.6);
  document.getElementById("zoom-out").onclick = () => zoomBy(1 / 1.6);
  window.tinyvigo = { viewer, manifest: m, need };
})();
