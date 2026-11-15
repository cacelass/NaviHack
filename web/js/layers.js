// TinyVigo capas (MAP-01): panel de 7 capas conmutables. Navidad y eventos encendidas por
// defecto; el resto apagadas. Los marcadores de eventos, buses, trenes, parking y cámaras se
// pintan sobre el mapa isométrico con la misma proyección que el resto de la app (tour.project).
(function () {
  const CANVAS = 3072; // 1 viewer unit = 3072 canvas px (the drawing itself is wider, see within)
  // inside the drawing: its real size from the manifest. The old check used 3072 and dropped
  // everything east of it after the map grew (v8): Vialia's car park, its stops, its cameras.
  const within = (xy) => { const m = window.tinyvigo && window.tinyvigo.manifest, w = m ? m.width : CANVAS, h = m ? m.height : CANVAS; return xy[0] > 0 && xy[0] < w && xy[1] > 0 && xy[1] < h; };
  const LAYERS = [
    { id: "navidad", icon: "tree-pine", text: "layer.navidad", on: true },
    { id: "eventos", icon: "calendar-days", text: "layer.eventos", on: true },
    { id: "buses", icon: "bus", text: "layer.buses", on: false },
    { id: "trenes", icon: "train-front", text: "layer.trenes", on: false },
    { id: "parking", icon: "square-parking", text: "layer.parking", on: false },
    { id: "camaras", icon: "camera", text: "layer.camaras", on: false },
    { id: "trafico", icon: "car", text: "layer.trafico", on: false },
    { id: "rutas", icon: "route", text: "layer.rutas", on: false },
  ];
  const KEY = "tinyvigo.layers";
  let state = Object.fromEntries(LAYERS.map((l) => [l.id, l.on]));
  try { const saved = JSON.parse(localStorage.getItem(KEY) || "null"); if (saved) state = { ...state, ...saved }; } catch (e) { /* sin storage */ }

  const lu = (name, size = 18) => { const s = document.createElement("span"); s.innerHTML = window.LU ? LU.svg(name, { size }) : ""; return s.firstChild || s; };
  const el = (tag, cls, ...kids) => { const n = document.createElement(tag); if (cls) n.className = cls; n.append(...kids.filter((k) => k != null && k !== false)); return n; };
  const t = (k) => (window.tinyvigoPoints ? window.tinyvigoPoints.t(k) : k);
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* sin storage */ } };

  // ── marcadores sobre el isométrico ───────────────────────────────────────
  const groups = {}; // id -> [elementos]
  function add(id, node) { (groups[id] ||= []).push(node); }
  // LAYERS-02: the same marker on the satellite view (city3d.js), shown and hidden with its layer.
  // Off-drawing places (out of the pixel map) only exist there.
  function twin(id, b, lat, lon) {
    const C = window.tinyvigoCity; if (!C || !C.addMarker) return;
    const n = b.cloneNode(true); n.onclick = b.onclick; n.classList.add("is-on-city");
    C.addMarker(n, lat, lon); add(id, n);
  }
  function visible(id) { return state[id]; }
  function apply(id) {
    // OpenSeadragon rewrites the inline display of its overlays: visibility is what really hides them
    for (const n of groups[id] || []) { n.style.display = state[id] ? "" : "none"; n.style.visibility = state[id] ? "" : "hidden"; }
    if (id === "navidad") document.querySelectorAll(".tv-marker").forEach((m) => { m.style.display = state.navidad ? "" : "none"; });
    if (id === "rutas") document.querySelectorAll(".tv-route").forEach((r) => { r.style.display = state.rutas ? "" : "none"; });
  }
  function project(lat, lon) {
    if (window.tinyvigoTour && window.tinyvigoTour.project) return window.tinyvigoTour.project(lat, lon);
    return null;
  }
  function overlay(node, x, y) {
    const viewer = window.tinyvigo.viewer;
    if (!viewer) return null;
    viewer.addOverlay({ element: node, location: new OpenSeadragon.Point(x / CANVAS, y / CANVAS), placement: OpenSeadragon.Placement.CENTER });
    // el visor se queda el clic de los overlays: se reenvía a onclick, como los marcadores de tour.js
    node.addEventListener("pointerdown", (e) => e.stopPropagation());
    new OpenSeadragon.MouseTracker({ element: node, clickHandler: (e) => { e.preventDefaultAction = true; if (node.onclick) node.onclick(); } });
    return node;
  }
  function dot(cls, icon, label) {
    const b = el("button", "tv-lmark " + cls);
    b.title = label; b.setAttribute("aria-label", label);
    if (window.LU) b.append(lu(icon, 14));
    return b;
  }

  const norm = (s) => (s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9ñ ]/g, " ").replace(/\s+/g, " ").trim();
  async function loadEventos() {
    if (!window.tinyvigoTour || !window.tinyvigoTour.project) return; // aún sin proyección
    if (groups.eventos) return;
    groups.eventos = [];
    try {
      const [rows, centros] = await Promise.all([
        window.tinyvigoData ? window.tinyvigoData.agenda() : [],
        window.tinyvigoData ? window.tinyvigoData.centros().catch(() => []) : [],
      ]);
      // la agenda no trae coordenadas: se casa la dirección con los puntos y los recintos
      const places = [];
      const P = window.tinyvigoPoints;
      for (const p of (P && P.points) || []) {
        if (p.lat == null || p.lon == null) continue;
        for (const key of [p.address, p.name && p.name.es, p.name && p.name.gl]) {
          const q = norm(key); if (q && q.length > 5) places.push({ q, lat: p.lat, lon: p.lon });
        }
      }
      for (const c of centros || []) {
        if (c.lat == null || c.lon == null) continue;
        const q = norm(c.nombre); if (q && q.length > 5) places.push({ q, lat: c.lat, lon: c.lon });
      }
      const find = (dir) => {
        const q = norm(dir); if (!q) return null;
        return places.find((pl) => pl.q === q)
          || places.find((pl) => q.includes(pl.q) || pl.q.includes(q))
          || null;
      };
      let placed = 0;
      for (const e of (rows || [])) {
        const at = find(e.direccion);
        if (!at) continue;
        const xy = project(at.lat, at.lon); if (!xy) continue;
        const b = dot("is-event", "calendar-days", e.titulo || "Evento");
        b.onclick = () => toast((e.titulo || "Evento") + (e.horario ? " · " + e.horario : "") + (e.direccion ? "\n" + e.direccion : ""));
        twin("eventos", b, at.lat, at.lon);
        if (overlay(b, xy[0], xy[1])) { add("eventos", b); placed++; }
      }
      if (placed === 0) console.info("TinyVigo capas: agenda sin direcciones casadas con el mapa");
    } catch (err) { /* sin feed: capa vacía */ }
    apply("eventos");
  }

  async function loadTransit() {
    if (!window.tinyvigoTour || !window.tinyvigoTour.project) return; // aún sin proyección
    if (groups.buses) return;
    groups.buses = []; groups.trenes = [];
    try {
      const d = await (await fetch("data/transit.json")).json();
      for (const [id, name, lat, lon] of d.stops || []) {
        const xy = project(lat, lon); if (!xy) continue;
        const inside = within(xy);
        if (!inside) continue;
        const b = dot("is-bus", "bus", name);
        b.onclick = () => departuresToast(name, (T) => T.nextDepartures(id).map((x) => x.time + " " + x.line + " → " + x.headsign), (T) => T.emptyText(id)); // BUS-02
        if (overlay(b, xy[0], xy[1])) add("buses", b);
      }
      // las estaciones de Renfe no traen lat/lon en transit.json: coordenadas conocidas (WEB-03)
      const ST = { "Vigo Urzaiz": [42.234189, -8.713728], "Vigo-Guixar": [42.2392656, -8.7146089] };
      for (const s of (d.trains && d.trains.stations) || []) {
        const pos = ST[s.name]; if (!pos) continue;
        const xy = project(pos[0], pos[1]); if (!xy) continue;
        const b = dot("is-train", "train-front", s.name);
        b.onclick = () => departuresToast(s.name, (T) => T.trains().filter((x) => x.station === s.name).map((x) => x.time + " " + x.train + " → " + x.to));
        if (overlay(b, xy[0], xy[1])) add("trenes", b);
      }
    } catch (err) { /* sin dato: capa vacía */ }
    apply("buses"); apply("trenes");
  }

  async function loadParking() {
    if (!window.tinyvigoTour || !window.tinyvigoTour.project) return; // aún sin proyección
    if (groups.parking) return;
    groups.parking = [];
    try {
      const rows = (window.tinyvigoData ? await window.tinyvigoData.parkings() : []).filter((r) => r.lat && r.lon); // WEB-05
      for (const r of rows) {
        const xy = project(r.lat, r.lon); if (!xy) continue;
        const inside = within(xy);
        if (!inside) continue;
        const b = dot("is-park", "square-parking", r.nombre || "Parking");
        b.onclick = () => toast(r.nombre + " · " + (r.plazaslibres ?? "?") + "/" + (r.totalplazas ?? "?") + " libres");
        if (overlay(b, xy[0], xy[1])) add("parking", b);
      }
    } catch (err) { /* sin feed: capa vacía */ }
    apply("parking");
  }

  async function loadCamaras() {
    if (!window.tinyvigoTour || !window.tinyvigoTour.project) return; // aún sin proyección
    if (groups.camaras) return;
    groups.camaras = [];
    try {
      const geo = await (await fetch("data/layers/cameras.geojson")).json();
      const rows = geo.features || geo || [];
      for (const f of rows) {
        const c = f.geometry ? f.geometry.coordinates : [f.lon, f.lat];
        if (!c || c[1] == null) continue;
        const props = f.properties || f;
        const b = dot("is-cam", "camera", props.name || props.nombre || "Cámara");
        if (props.image_url) b.onclick = () => showCam(props); // CAM-01: la imagen en directo, dentro de la app
        twin("camaras", b, c[1], c[0]);
        const xy = project(c[1], c[0]); if (!xy || !within(xy)) continue;
        if (overlay(b, xy[0], xy[1])) add("camaras", b);
      }
    } catch (err) { /* sin capa: vacía */ }
    apply("camaras");
  }

  // CAM-01: the live picture from the Concello in a card (the camera URL has no content type, so
  // opening it downloaded a «.php» file; in an <img> it shows fine). Refreshed every 20 s.
  let camCard = null, camTimer = 0, camOpener = null;
  function showCam(props) {
    const P = window.tinyvigoPoints, tt = (k) => (P ? P.t(k) : k);
    if (!camCard) {
      camCard = el("section", "tv-cam");
      camCard.setAttribute("role", "dialog"); camCard.setAttribute("aria-modal", "false");
      document.body.append(camCard);
      document.addEventListener("keydown", (e) => { if (e.key === "Escape" && camCard.classList.contains("is-open")) closeCam(); });
    }
    camOpener = document.activeElement;
    const src = () => props.image_url + (props.image_url.includes("?") ? "&" : "?") + "t=" + Date.now();
    const img = Object.assign(el("img", "tv-cam-img"), { alt: props.name || tt("layer.camaras"), width: 640, height: 360, decoding: "async" });
    const state = el("p", "tv-cam-state", tt("state.loading") + "…");
    state.setAttribute("role", "status");
    img.onload = () => { state.textContent = tt("camera.live"); camCard.classList.remove("is-broken"); };
    img.onerror = () => { state.textContent = tt("camera.no_image"); camCard.classList.add("is-broken"); };
    img.src = src();
    const close = el("button", "tv-close", lu("x", 20)); close.type = "button"; close.setAttribute("aria-label", tt("common.close")); close.onclick = closeCam;
    const title = el("h2", null, props.name || tt("layer.camaras")); title.id = "tv-cam-title";
    camCard.setAttribute("aria-labelledby", "tv-cam-title");
    camCard.replaceChildren(close, title, el("div", "tv-cam-frame", img), state, el("p", "tv-cam-credit", props.credit || "Imagen: Concello de Vigo"));
    camCard.classList.add("is-open");
    clearInterval(camTimer);
    camTimer = setInterval(() => { if (!document.hidden) img.src = src(); }, 20000);
    setTimeout(() => close.focus(), 30);
  }
  function closeCam() {
    clearInterval(camTimer);
    camCard.classList.remove("is-open");
    if (camOpener && document.body.contains(camOpener)) camOpener.focus();
  }

  // TRAFFIC-01: the Concello's live traffic state (data/live/trafico.json, refreshed every minute),
  // each section coloured by its state on the drawn map and on the 3D city. Colour means state here.
  const TRAFFIC_CLASS = { "Muy fluido": "ok", "Fluido": "ok", "Normal": "normal", "Lento": "slow" }; // the rest: congested
  const trafficClass = (estado) => TRAFFIC_CLASS[estado] || "jam";
  let trafficSvg = null, trafficTimer = 0, trafficShapes = null;
  async function loadTrafico() {
    const viewer = window.tinyvigo && window.tinyvigo.viewer, project = window.tinyvigoGeo && window.tinyvigoGeo.project;
    if (!viewer || !project) return;
    let doc;
    try { doc = await window.tinyvigoData.trafico(); } catch (err) { return; } // sin feed: el aviso de data.js ya lo dice
    // TRAFFIC-02: the feed's sections have a handful of vertices and cut across blocks; their shape
    // snapped to the street (scripts/build_traffic_geom.py) replaces it, the live state stays
    const shape = await (trafficShapes ||= fetch("data/layers/trafico_geom.json").then((r) => r.json()).catch(() => ({})));
    doc = { ...doc, data: { ...doc.data, features: doc.data.features.map((f) => (shape[f.properties.nombre_tramo] ? { ...f, geometry: { type: "LineString", coordinates: shape[f.properties.nombre_tramo] } } : f)) } };
    const SVG = "http://www.w3.org/2000/svg";
    if (!trafficSvg) {
      trafficSvg = document.createElementNS(SVG, "svg");
      trafficSvg.setAttribute("viewBox", "0 0 " + CANVAS + " " + CANVAS);
      trafficSvg.setAttribute("class", "tv-traffic");
      viewer.addOverlay({ element: trafficSvg, location: new OpenSeadragon.Rect(0, 0, 1, 1) });
      add("trafico", trafficSvg);
      trafficTimer = setInterval(() => { if (state.trafico && !document.hidden) loadTrafico(); }, 60000);
    }
    if (window.tinyvigoOcclusion) await window.tinyvigoOcclusion.ready;
    trafficSvg.replaceChildren();
    for (const f of doc.data.features) {
      const pts = f.geometry.coordinates.map(([lo, la]) => project(la, lo));
      if (!pts.some(within)) continue;
      // GEO-02: only where the street shows; behind a building the line would sit on its roof
      const runs = window.tinyvigoOcclusion ? window.tinyvigoOcclusion.visibleRuns(pts) : [pts];
      for (const run of runs) {
        const pl = document.createElementNS(SVG, "polyline");
        pl.setAttribute("points", run.map((p) => p[0].toFixed(1) + "," + p[1].toFixed(1)).join(" "));
        pl.setAttribute("class", "is-" + trafficClass(f.properties.estado));
        const title = document.createElementNS(SVG, "title");
        title.textContent = f.properties.nombre_tramo + " · " + f.properties.estado;
        pl.append(title);
        trafficSvg.append(pl);
      }
    }
    if (window.tinyvigoCity && window.tinyvigoCity.setTraffic) window.tinyvigoCity.setTraffic(state.trafico ? doc.data : null);
    apply("trafico");
  }

  const lazies = { eventos: loadEventos, buses: loadTransit, trenes: loadTransit, parking: loadParking, camaras: loadCamaras, trafico: loadTrafico };

  // aviso breve para los clics de capa
  let toastTimer = null;
  function toast(text, ms = 2600) {
    let n = document.querySelector(".tv-ltoast");
    if (!n) { n = el("div", "tv-ltoast"); document.body.append(n); }
    n.textContent = text; n.classList.add("is-on");
    clearTimeout(toastTimer); toastTimer = setTimeout(() => n.classList.remove("is-on"), ms);
  }
  // BUS-02: a stop or station on the drawn map says its next scheduled departures
  async function departuresToast(name, rows, empty) {
    const T = window.tinyvigoTransit; if (!T) return toast(name);
    await T.load();
    const r = rows(T), t = (k) => (window.tinyvigoPoints ? window.tinyvigoPoints.t(k) : k);
    toast([name, ...(r.length ? r : [empty ? empty(T) : t("transit.no_more_today")]), t("transit.scheduled")].join("\n"), 7000);
  }

  function set(id, on, opts = {}) {
    state[id] = !!on; save(); apply(id);
    const group = document.querySelector('.tv-layers-pop [data-layer="' + id + '"]');
    if (group) {
      group.classList.toggle("is-on", !!on);
      group.setAttribute("aria-pressed", String(!!on));
      group.setAttribute("aria-checked", String(!!on));
    }
    if (on && lazies[id] && !opts.silent) lazies[id]();
    if (id === "trafico" && !on && window.tinyvigoCity && window.tinyvigoCity.setTraffic) window.tinyvigoCity.setTraffic(null);
    document.dispatchEvent(new CustomEvent("tv:layer", { detail: { id, on: !!on } }));
  }

  function init() {
    if (document.querySelector(".tv-layers")) return;
    const wrap = el("div", "tv-layers");
    const btn = el("button", "tv-layers-btn");
    btn.type = "button";
    btn.setAttribute("aria-label", t("layers.title"));
    btn.setAttribute("aria-haspopup", "dialog");
    btn.setAttribute("aria-expanded", "false");
    btn.append(lu("layers", 20));
    const pop = el("div", "tv-layers-pop");
    pop.id = "tv-layers-pop";
    pop.setAttribute("role", "dialog");
    pop.setAttribute("aria-labelledby", "tv-layers-title");
    pop.setAttribute("aria-hidden", "true");
    btn.setAttribute("aria-controls", pop.id);
    function closePop(restoreFocus = false) {
      pop.classList.remove("is-open");
      pop.setAttribute("aria-hidden", "true");
      btn.setAttribute("aria-expanded", "false");
      if (restoreFocus) btn.focus();
    }
    const close = el("button", "tv-layers-close", lu("x", 20));
    close.type = "button";
    close.setAttribute("aria-label", t("common.close"));
    close.onclick = () => closePop(true);
    const title = el("h2", null, t("layers.title")); title.id = "tv-layers-title";
    pop.append(close, title);
    for (const l of LAYERS) {
      const b = el("button", "tv-layer" + (state[l.id] ? " is-on" : ""),
        lu(l.icon, 18), el("span", "tv-layer-label", t(l.text)), el("span", "tv-layer-switch"));
      b.type = "button";
      b.dataset.layer = l.id;
      b.setAttribute("role", "switch");
      b.setAttribute("aria-pressed", String(state[l.id]));
      b.setAttribute("aria-checked", String(state[l.id]));
      b.setAttribute("aria-label", t(l.text));
      b.onclick = () => set(l.id, !state[l.id]);
      pop.append(b);
    }
    // MAP-01: el «arte pixel off» enseña la ortofoto real de la misma zona.
    const sep = el("div", "tv-layers-sep");
    const satOn = () => !!(window.tinyvigoSat && window.tinyvigoSat.isOn());
    const sat = el("button", "tv-layer tv-layer-sat" + (satOn() ? " is-on" : ""), lu("image", 18), el("span", "tv-layer-label", t("sat.button")), el("span", "tv-layer-switch"));
    sat.type = "button";
    sat.setAttribute("role", "switch");
    sat.setAttribute("aria-pressed", String(satOn()));
    sat.setAttribute("aria-checked", String(satOn()));
    sat.setAttribute("aria-label", t("sat.button"));
    sat.onclick = () => {
      if (!window.tinyvigoSat) return;
      window.tinyvigoSat.set(!window.tinyvigoSat.isOn());
    };
    document.addEventListener("tv:sat", (e) => {
      sat.classList.toggle("is-on", e.detail.on);
      sat.setAttribute("aria-pressed", String(e.detail.on));
      sat.setAttribute("aria-checked", String(e.detail.on));
      sat.setAttribute("aria-label", e.detail.on ? t("sat.back") : t("sat.button"));
      sat.querySelector(".tv-layer-label").textContent = e.detail.on ? t("sat.back") : t("sat.button");
      closePop();
    });
    pop.append(sep, sat);
    btn.onclick = () => {
      const open = !pop.classList.contains("is-open");
      if (!open) { closePop(); return; }
      pop.classList.add("is-open");
      pop.setAttribute("aria-hidden", "false");
      btn.setAttribute("aria-expanded", "true");
      Object.keys(lazies).forEach((id) => { if (state[id]) lazies[id](); });
      const first = pop.querySelector(".tv-layer.is-on") || close;
      first.focus();
    };
    wrap.append(btn, pop);
    document.body.append(wrap);
    // Closing outside keeps the trigger state synchronized with the sheet manager.
    document.addEventListener("pointerdown", (ev) => {
      if (!wrap.contains(ev.target) && !btn.contains(ev.target)) closePop(); // the button may live in the top bar (HUD v5)
    });
    document.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape" && pop.classList.contains("is-open")) { ev.stopImmediatePropagation(); closePop(true); }
    });

    for (const l of LAYERS) apply(l.id);
    // LAYERS-02: what is on shows from the start, not only after opening the panel (the loaders
    // wait for the projection, which tour.js sets up right after tv:ready)
    (function loadOn(n = 0) {
      if (!(window.tinyvigoTour && window.tinyvigoTour.project)) { if (n < 100) setTimeout(() => loadOn(n + 1), 200); return; }
      Object.keys(lazies).forEach((id) => { if (state[id]) lazies[id](); });
    })();
    // los marcadores de puntos se crean después de tv:ready
    document.addEventListener("tv:ready", () => { apply("navidad"); apply("rutas"); }, { once: true });
    // una ruta nueva debe verse aunque la capa estuviera apagada: se enciende al planificar
    document.addEventListener("tv:clear-route", () => apply("rutas"));
    // una ruta recién planificada enciende su capa aunque estuviera apagada
    document.addEventListener("tv:route", () => { if (!state.rutas) set("rutas", true); else apply("rutas"); });
    document.addEventListener("tv:lang", () => {
      btn.setAttribute("aria-label", t("layers.title"));
      title.textContent = t("layers.title");
      close.setAttribute("aria-label", t("common.close"));
      pop.querySelectorAll("[data-layer]").forEach((b) => {
        const id = b.dataset.layer, l = LAYERS.find((x) => x.id === id);
        if (l) { b.querySelector(".tv-layer-label").textContent = t(l.text); b.setAttribute("aria-label", t(l.text)); }
      });
      const satLabel = window.tinyvigoSat && window.tinyvigoSat.isOn() ? t("sat.back") : t("sat.button");
      sat.querySelector(".tv-layer-label").textContent = satLabel;
      sat.setAttribute("aria-label", satLabel);
    });
    window.tinyvigoLayers = { isOn: (id) => !!state[id], set, toggle: (id) => set(id, !state[id]), state: () => ({ ...state }), close: () => closePop() };
  }

  if (window.tinyvigoPoints) init();
  else document.addEventListener("tv:ready", init, { once: true });
})();
