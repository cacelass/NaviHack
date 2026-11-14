// TinyVigo: tour a pie según tu tiempo y, si estás lejos, cómo llegar al primer punto (a pie, bus o coche: GO-01, js/getthere.js).
// Elige paradas abiertas y cercanas que caben en el tiempo, ordena por vecino más próximo,
// enruta por calles reales (OSRM a pie de openstreetmap.de) y dibuja la línea sobre el mapa isométrico.
(function () {
  const ORIGIN = [42.238072, -8.725813]; // Árbol de Porta do Sol = centro del lienzo (GEO-01)
  const CANVAS = 3072, SCALE = 2, TILT = Math.PI / 4, HEAD = (-15 * Math.PI) / 180, MLAT = 111320;
  const WALK_MS = 4.5 / 3.6; // 4,5 km/h
  const DETOUR = 1.3; // calle frente a línea recta
  const STAY = { light: 5, exhibit: 3, photo_gallery: 5, photocall: 3, santa_kings: 10, market: 20, attraction: 15 };
  const VALUE = { attraction: 3, market: 3, light: 2.5, santa_kings: 2, photocall: 1.5, exhibit: 1, photo_gallery: 1 };
  const BUDGETS = [30, 60, 90, 120];
  const NEAR_MIN = 5; // a más de 5 min a pie del primer punto, preguntamos cómo quieres llegar (GO-01)
  const ROUTER = "https://routing.openstreetmap.de/routed-foot/route/v1/foot/";
  const lu = (name, size = 20) => { const s = document.createElement("span"); s.innerHTML = window.LU ? LU.svg(name, { size }) : ""; return s.firstChild || s; };
  const emit = (name, detail) => document.dispatchEvent(new CustomEvent(name, { detail }));

  let elev = null;
  fetch("data/elevation.json").then((r) => r.json()).then((g) => (elev = g)).catch(() => {});

  const rad = (d) => (d * Math.PI) / 180;
  const distM = (a, b) => {
    const dy = (b[0] - a[0]) * MLAT, dx = (b[1] - a[1]) * MLAT * Math.cos(rad((a[0] + b[0]) / 2));
    return Math.hypot(dx, dy);
  };
  const walkMin = (a, b) => (distM(a, b) * DETOUR) / WALK_MS / 60;
  function z(lat, lon) {
    if (!elev) return 0;
    const i = Math.round((elev.north - lat) / elev.dy), j = Math.round((lon - elev.west) / elev.dx);
    const row = elev.rows[i];
    return row && row[j] != null ? row[j] - (elev.origin_z || 0) : 0;
  }
  // (lat, lon) -> coordenadas del visor (0..1 sobre el ancho del lienzo); igual que scripts/build_web_data.py
  function project(lat, lon) {
    const x = (lon - ORIGIN[1]) * MLAT * Math.cos(rad(ORIGIN[0])), y = (lat - ORIGIN[0]) * MLAT;
    const u = Math.cos(HEAD) * x - Math.sin(HEAD) * y, d = Math.sin(HEAD) * x + Math.cos(HEAD) * y;
    const v = -Math.sin(TILT) * d - Math.cos(TILT) * z(lat, lon);
    return [CANVAS / 2 + SCALE * u, CANVAS / 2 + SCALE * v];
  }

  // ── planificador ─────────────────────────────────────────────────────────
  function plan(points, start, budget, status, now = new Date()) {
    const pool = [], later = [], closed = [];
    for (const p of points) {
      const pos = [p.lat, p.lon], reach = walkMin(start, pos);
      const st = status(p, now);
      if (reach > budget * 0.6) later.push({ p, km: distM(start, pos) / 1000, min: Math.round(reach) });
      else if (st && !st.open) closed.push({ p, st });
      else pool.push(p);
    }
    const stops = [];
    let here = start, used = 0;
    // puntos casi en el mismo sitio cuentan como una parada
    while (pool.length) {
      let best = null, bestScore = -1;
      for (const p of pool) {
        const w = walkMin(here, [p.lat, p.lon]), stay = STAY[p.type] || 5;
        if (used + w + stay > budget) continue;
        const score = (VALUE[p.type] || 1) / (w + stay);
        if (score > bestScore) { best = p; bestScore = score; }
      }
      if (!best) break;
      const w = walkMin(here, [best.lat, best.lon]), stay = STAY[best.type] || 5;
      stops.push({ p: best, arrive: used + w, stay });
      used += w + stay;
      here = [best.lat, best.lon];
      pool.splice(pool.indexOf(best), 1);
    }
    later.sort((a, b) => a.km - b.km);
    return { stops, later, closed, used };
  }

  async function route(start, stops) {
    const coords = [start, ...stops.map((s) => [s.p.lat, s.p.lon])].map(([la, lo]) => lo.toFixed(6) + "," + la.toFixed(6)).join(";");
    const r = await fetch(ROUTER + coords + "?overview=full&geometries=geojson");
    const j = await r.json();
    if (j.code !== "Ok") throw new Error(j.code);
    return j.routes[0];
  }

  // ── dibujo sobre el mapa ─────────────────────────────────────────────────
  const SVG = "http://www.w3.org/2000/svg";
  let layer = null;
  function draw(viewer, line, start, stops, onPick) {
    clear(viewer);
    layer = document.createElementNS(SVG, "svg");
    layer.setAttribute("viewBox", "0 0 " + CANVAS + " " + CANVAS);
    layer.setAttribute("class", "tv-route");
    const pts = line.map(([lo, la]) => project(la, lo).map((n) => n.toFixed(1)).join(",")).join(" ");
    for (const cls of ["tv-route-casing", "tv-route-line"]) {
      const pl = document.createElementNS(SVG, "polyline");
      pl.setAttribute("points", pts); pl.setAttribute("class", cls);
      layer.append(pl);
    }
    const s = project(start[0], start[1]);
    const me = document.createElementNS(SVG, "circle");
    me.setAttribute("cx", s[0]); me.setAttribute("cy", s[1]); me.setAttribute("r", 14); me.setAttribute("class", "tv-route-start");
    layer.append(me);
    stops.forEach((st, i) => {
      const [x, y] = project(st.p.lat, st.p.lon);
      const g = document.createElementNS(SVG, "g");
      g.setAttribute("class", "tv-route-stop");
      const c = document.createElementNS(SVG, "circle"); c.setAttribute("cx", x); c.setAttribute("cy", y - 40); c.setAttribute("r", 20);
      const tx = document.createElementNS(SVG, "text"); tx.setAttribute("x", x); tx.setAttribute("y", y - 33); tx.textContent = i + 1;
      const hit = document.createElementNS(SVG, "circle"); hit.setAttribute("cx", x); hit.setAttribute("cy", y - 40); hit.setAttribute("r", 34); hit.setAttribute("class", "tv-route-hit");
      const title = document.createElementNS(SVG, "title"); title.textContent = (i + 1) + ". " + (onPick ? onPick.name(st.p) : "");
      g.append(c, tx, hit, title); layer.append(g);
      if (onPick) {
        g.addEventListener("pointerdown", (e) => e.stopPropagation());
        new OpenSeadragon.MouseTracker({ element: g, clickHandler: (e) => { e.preventDefaultAction = true; onPick.pick(i); } });
      }
    });
    viewer.addOverlay({ element: layer, location: new OpenSeadragon.Rect(0, 0, 1, 1) });
    // encuadra la ruta
    const xs = line.map(([lo, la]) => project(la, lo));
    const minX = Math.min(...xs.map((p) => p[0])), maxX = Math.max(...xs.map((p) => p[0]));
    const minY = Math.min(...xs.map((p) => p[1])), maxY = Math.max(...xs.map((p) => p[1]));
    const pad = matchMedia("(max-width: 700px)").matches ? 90 : 420; // en escritorio los paneles tapan los bordes
    // MOB-01: en móvil la hoja tapa ~60 % de abajo; ampliamos el encuadre hacia abajo para que la ruta quede arriba, a la vista
    const h = maxY - minY + 2 * pad, below = matchMedia("(max-width: 700px)").matches ? h * 1.5 : 0;
    viewer.viewport.fitBounds(new OpenSeadragon.Rect((minX - pad) / CANVAS, (minY - pad) / CANVAS, (maxX - minX + 2 * pad) / CANVAS, (h + below) / CANVAS));
    viewer.viewport.applyConstraints(); // WEB-01: nunca deja ver fondo fuera del bloque
  }
  function clear(viewer) { if (layer) { viewer.removeOverlay(layer); layer = null; } }

  // ── interfaz ─────────────────────────────────────────────────────────────
  function init() {
    const P = window.tinyvigoPoints, viewer = window.tinyvigo.viewer;
    const t = P.t, txt = P.txt;
    const btn = document.createElement("button");
    btn.className = "tv-tour-open";
    const box = document.createElement("section");
    box.className = "tv-tour";
    document.body.append(btn, box);
    let when = "now";
    const startTime = () => { if (when === "now") return new Date(); const d = new Date(); d.setHours(+when, 0, 0, 0); if (d < new Date()) d.setDate(d.getDate() + 1); return d; };
    let budget = 60, fromHere = true, result = null, startPos = ORIGIN, busy = "", trip = null, offset = 0, editing = false;

    const el = (tag, cls, ...kids) => { const n = document.createElement(tag); if (cls) n.className = cls; n.append(...kids.filter((k) => k != null && k !== false)); return n; };
    const hhmm = (min) => { const d = new Date(startTime().getTime() + (min + offset) * 60000); return String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0"); };
    const gmaps = (mode, dest, way = []) => "https://www.google.com/maps/dir/?api=1&travelmode=" + mode + "&origin=" + startPos.join(",") + "&destination=" + dest.join(",") + (way.length ? "&waypoints=" + way.map((w) => w.join(",")).join("|") : "");

    function render() {
      btn.replaceChildren(lu("route"), t("tour.open"));
      box.replaceChildren();
      if (!box.classList.contains("is-open")) return;
      const close = el("button", "tv-close", lu("x")); close.setAttribute("aria-label", t("common.close")); close.onclick = () => { box.classList.remove("is-open"); render(); };
      const chips = el("div", "tv-chips", ...BUDGETS.map((b) => { const c = el("button", b === budget ? "is-on" : "", t("tour.minutes", { min: b })); c.onclick = () => { budget = b; render(); }; return c; }));
      const from = el("div", "tv-langs tv-from", ...[[true, "tour.from_here"], [false, "tour.from_centre"]].map(([v, k]) => { const c = el("button", v === fromHere ? "is-on" : "", t(k)); c.onclick = () => { fromHere = v; render(); }; return c; }));
      const whenChips = el("div", "tv-chips", ...[["now", t("tour.now")], ["18", "18:00"], ["20", "20:00"], ["22", "22:00"]].map(([v, label]) => { const c = el("button", v === when ? "is-on" : "", label); c.onclick = () => { when = v; render(); }; return c; }));
      const go = el("button", "tv-btn tv-go", t("tour.go")); go.onclick = () => { editing = false; run(); };
      // MOB-01: con un tour o un «cómo llegar» ya calculado, el formulario se pliega en una línea
      // de resumen para que la ruta se vea en el mapa; «Cambiar» lo vuelve a abrir.
      const folded = (result || trip) && !editing && !busy;
      box.classList.toggle("has-result", !!folded);
      if (folded) {
        const edit = el("button", "tv-btn tv-btn-quiet tv-edit", t("go.change"));
        edit.onclick = () => { editing = true; render(); };
        const whenLabel = when === "now" ? t("tour.now") : when + ":00";
        box.append(close, el("div", "tv-tour-head",
          el("p", "tv-kicker", t("tour.minutes", { min: budget }) + " · " + whenLabel + " · " + t(fromHere ? "tour.from_here" : "tour.from_centre")), edit));
      } else {
        box.append(close, el("h2", null, t("tour.title")), chips, el("p", "tv-note", t("tour.when")), whenChips, from, go);
      }
      if (busy) box.append(el("p", "tv-note", busy));
      if (trip) box.append(renderGo());
      if (result) box.append(renderResult());
    }

    // ── GO-01: cómo llegar al primer punto ───────────────────────────────
    const MODE_ICON = { walk: "footprints", bus: "bus", car: "car" };
    const minTxt = (m) => t("tour.minutes", { min: Math.round(m) });
    const clock = (d) => String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0");
    const routeLegs = (o) => o.legs.map((l) => ({ line: l.line, mode: l.mode, parking: l.parking ? l.to : null, board: l.mode === "bus" ? l.from : null, alight: l.mode === "bus" ? l.to : null }));
    function optionSub(o) {
      if (o.unavailable) return t(o.unavailable);
      if (o.mode === "bus") { const b = o.legs[1]; return t("go.opt_bus_sub", { line: b.busLine, time: b.dep, stop: b.fromName }); }
      if (o.mode === "car" && o.legs[0].parking) { const k = o.legs[0].parking; return t("go.opt_car_sub", { name: k.name, free: k.free }); }
      return t("go.arrive_at", { time: clock(o.arrive) });
    }
    function legRow(l, o) {
      let title, detail;
      if (l.mode === "walk") { title = t("go.leg_walk", { to: l.toName }); detail = t("go.meters", { m: Math.round(l.meters / 10) * 10 }); }
      else if (l.mode === "bus") { title = t("go.leg_bus", { line: l.busLine, headsign: l.headsign }); detail = t("go.leg_bus_detail", { dep: l.dep, from: l.fromName, arr: l.arr, to: l.toName, n: l.nStops }); }
      else {
        title = t("go.leg_car", { to: l.toName });
        const k = l.parking;
        detail = k ? t("go.park_detail", { free: k.free, total: k.total, time: k.updated }) + " · " + t("go.forecast_" + k.forecast) + " · " + t("go.park_time", { min: o.parkMin }) : t(o.warning || "go.no_parking_data");
      }
      const toStop = l.mode === "walk" && o.mode === "bus" && o.legs[0] === l;
      const maps = Object.assign(el("a", "tv-leg-maps", lu("arrow-up-right", 14), t(toStop ? "go.open_to_stop" : "go.open_leg")), { href: l.gmaps, target: "_blank", rel: "noopener" });
      return el("li", "tv-leg tv-leg-" + l.mode,
        el("span", "tv-leg-icon", lu(MODE_ICON[l.mode], 18)),
        el("div", "tv-leg-body", el("strong", null, title), el("span", null, detail + (l.approx ? " · " + t("go.approx") : "")), maps),
        el("span", "tv-leg-time", minTxt(l.min)));
    }
    function renderGo() {
      const name = txt(trip.first.name);
      const head = [el("h3", null, t("go.how_title", { name })), el("p", "tv-note", t("go.how_body", { min: trip.away }))];
      if (trip.loading) return el("div", "tv-go", ...head, el("p", "tv-note tv-loading", t("go.calculating")));
      if (!trip.chosen) {
        const opts = ["walk", "bus", "car"].map((m) => {
          const o = trip.opts[m];
          const b = el("button", "tv-goopt" + (o.unavailable ? " is-off" : ""),
            el("span", "tv-leg-icon", lu(MODE_ICON[m], 20)),
            el("span", "tv-goopt-body", el("strong", null, t("go." + m)), el("span", null, optionSub(o))),
            el("span", "tv-leg-time", o.unavailable ? "—" : minTxt(o.total)));
          b.disabled = !!o.unavailable;
          b.onclick = () => choose(o);
          return b;
        });
        return el("div", "tv-go", ...head, el("div", "tv-goopts", ...opts));
      }
      const o = trip.chosen;
      let alt = null;
      if (o.alternative) {
        const k = o.alternative.legs[0].parking;
        alt = el("button", "tv-btn tv-btn-quiet tv-go-alt", lu("rotate-cw", 16), t("go.use_parking", { name: k.name, free: k.free, min: o.alternative.total }));
        alt.onclick = () => { const a = o.alternative; a.alternative = { ...o, alternative: null }; choose(a); };
      }
      const start = el("button", "tv-btn tv-go", t("go.start_tour"));
      start.onclick = () => startTour();
      const all = Object.assign(el("a", "tv-btn", lu("route", 16), t("tour.open_gmaps")), { href: o.gmaps, target: "_blank", rel: "noopener" });
      const back = el("button", "tv-btn tv-btn-quiet", t("go.change"));
      back.onclick = () => { trip.chosen = null; emit("tv:clear-route"); render(); };
      return el("div", "tv-go", ...head,
        el("p", "tv-summary", t("go.total", { min: o.total, time: clock(o.arrive) })),
        el("ol", "tv-legs", ...o.legs.map((l) => legRow(l, o))),
        o.mode === "bus" ? el("p", "tv-note", t("transit.scheduled")) : null,
        alt, start, el("div", "tv-actions", all, back));
    }
    function choose(o) {
      trip.chosen = o;
      emit("tv:route", { legs: routeLegs(o), start: startPos, stops: [], showCity: true });
      render();
    }

    function renderResult() {
      const { stops, later, closed, line, km } = result;
      if (!stops.length) return el("p", "tv-note", t("tour.nothing"));
      const ol = el("ol", "tv-story", ...stops.map((s, i) => {
        const b = el("button", null,
          s.p.photo ? Object.assign(el("img"), { src: s.p.photo, alt: "", loading: "lazy" }) : el("span", "tv-story-ph"),
          el("span", "tv-num", String(i + 1)),
          el("span", "tv-story-name", txt(s.p.name)),
          el("span", "tv-badge", t("tour.stop_at", { time: hhmm(s.arrive), stay: s.stay })));
        b.onclick = () => startWalk(i);
        return el("li", null, b);
      }));
      const walk = el("button", "tv-btn tv-go", t("walk.start")); walk.onclick = () => startWalk(0);
      const gm = el("a", "tv-btn tv-btn-quiet", t("tour.open_gmaps"));
      const dest = stops[stops.length - 1].p;
      gm.href = gmaps("walking", [dest.lat, dest.lon], stops.slice(0, -1).map((s) => [s.p.lat, s.p.lon]).slice(0, 9));
      gm.target = "_blank"; gm.rel = "noopener";
      const clr = el("button", "tv-btn tv-btn-quiet", t("tour.clear")); clr.onclick = () => { result = null; clear(viewer); emit("tv:clear-route"); render(); };
      return el("div", "tv-result",
        el("p", "tv-summary", t("tour.summary", { min: budget, n: stops.length, km })),
        el("p", "tv-note", t("walk.story")), ol, walk, el("div", "tv-actions", gm, window.tinyvigoShare ? window.tinyvigoShare.button(t("tour.summary", { min: budget, n: stops.length, km })) : null, clr),
        later.length ? el("details", "tv-later", el("summary", null, t("tour.later") + " · " + later.length),
          el("ul", null, ...later.slice(0, 12).map((l) => { const b = el("button", null, el("span", "tv-name", txt(l.p.name)), el("span", "tv-badge", t("tour.later_item", { km: l.km.toFixed(1), min: l.min }))); b.onclick = () => P.select(l.p); return el("li", null, b); }))) : null,
        closed.length ? el("details", "tv-later", el("summary", null, t("tour.closed_now") + " · " + closed.length),
          el("ul", null, ...closed.map((c) => el("li", null, el("button", null, el("span", "tv-name", txt(c.p.name)), el("span", "tv-badge", c.st.label)))))) : null);
    }

    // ── paseo paso a paso: «primero la Bola, luego la Noria…» ──────────────
    const step = document.createElement("section");
    step.className = "tv-step";
    document.body.append(step);
    let at = -1;
    function legMin(i) {
      const st = result.stops;
      return Math.max(1, Math.round(i === 0 ? st[0].arrive : st[i].arrive - st[i - 1].arrive - st[i - 1].stay));
    }
    function startWalk(i) {
      at = i;
      box.classList.remove("is-open"); render();
      showStep();
    }
    function showStep() {
      step.replaceChildren();
      step.classList.toggle("is-open", at >= 0 && !!result);
      if (at < 0 || !result) return;
      const st = result.stops, s = st[at], p = s.p;
      const from = at === 0 ? t("walk.you") : txt(st[at - 1].p.name);
      const prev = el("button", "tv-btn tv-btn-quiet", t("walk.prev")); prev.disabled = at === 0; prev.onclick = () => { at--; showStep(); };
      const last = at === st.length - 1;
      const next = el("button", "tv-btn", last ? t("common.close") : t("walk.next")); next.onclick = () => { if (last) { at = -1; } else { at++; } showStep(); };
      const close = el("button", "tv-close", lu("x")); close.setAttribute("aria-label", t("common.close")); close.onclick = () => { at = -1; showStep(); };
      const dots = el("div", "tv-step-dots", ...st.map((_, i) => el("span", i === at ? "is-on" : i < at ? "is-done" : "")));
      step.append(...[close, el("div", "tv-step-body",
        p.photo ? Object.assign(el("img", "tv-step-photo"), { src: p.photo, alt: txt(p.name) }) : null,
        el("div", null,
        el("p", "tv-kicker", t("walk.step", { n: at + 1, total: st.length }) + " · " + hhmm(s.arrive)),
        el("h2", null, txt(p.name)),
        el("p", "tv-step-leg", lu("footprints", 16), t("walk.leg", { min: legMin(at), from })),
        p.short ? el("p", "tv-short", txt(p.short)) : null)),
        dots,
        last ? el("p", "tv-note", t("walk.end")) : null,
        el("div", "tv-actions", prev, next)].filter(Boolean));
      // el mapa acompaña: isométrico si el punto está dibujado, ciudad si no
      if (p.on_map && !document.body.classList.contains("is-city")) {
        viewer.viewport.panTo(new OpenSeadragon.Point(p.x, p.y));
        viewer.viewport.zoomTo(Math.max(viewer.viewport.getZoom(), viewer.viewport.getHomeZoom() * 2.2));
      }
      document.dispatchEvent(new CustomEvent("tv:select", { detail: p }));
      document.querySelectorAll(".tv-marker").forEach((m) => m.classList.toggle("is-selected", m.getAttribute("aria-label") === txt(p.name)));
    }
    document.addEventListener("tv:lang", showStep);

    function locate() {
      return new Promise((res) => {
        if (!fromHere || !navigator.geolocation) return res(null);
        navigator.geolocation.getCurrentPosition((p) => res([p.coords.latitude, p.coords.longitude]), () => res(null), { timeout: 6000, maximumAge: 60000 });
      });
    }

    async function run() {
      result = null; trip = null; offset = 0; busy = fromHere ? t("tour.locating") : ""; emit("tv:clear-route"); render();
      const here = await locate();
      if (fromHere && !here) busy = t("tour.no_location");
      startPos = here || ORIGIN;
      offset = 0;
      // GO-01: el tour empieza en el punto abierto más cercano; si está a más de 5 min, ¿cómo llegas?
      if (here && window.tinyvigoGo) {
        const now = startTime();
        // el tour arranca en las luces (el núcleo navideño): la luz encendida más cercana, o la más cercana
        const lights = P.points.filter((p) => p.type === "light");
        const lit = lights.filter((p) => { const st = P.status(p, now); return st && st.open; });
        const pool = lit.length ? lit : lights.length ? lights : P.points;
        const anchor = pool.reduce((a, p) => (walkMin(startPos, [p.lat, p.lon]) < walkMin(startPos, [a.lat, a.lon]) ? p : a));
        const away = walkMin(startPos, [anchor.lat, anchor.lon]);
        if (away > NEAR_MIN) {
          trip = { first: anchor, away: Math.round(away), loading: true, opts: null, chosen: null };
          busy = ""; render();
          try { trip.opts = await tinyvigoGo.options(startPos, [anchor.lat, anchor.lon], txt(anchor.name), now); }
          catch (e) { const off = (mode) => ({ mode, unavailable: "go.unavailable" }); trip.opts = { walk: off("walk"), bus: off("bus"), car: off("car") }; }
          trip.loading = false; render();
          return;
        }
      }
      const planned = plan(P.points, startPos, budget, P.status, startTime());
      if (!planned.stops.length) { result = { ...planned, line: [], km: "0" }; busy = ""; render(); return; }
      busy = t("tour.routing"); render();
      let line, meters;
      try {
        const r = await route(startPos, planned.stops);
        line = r.geometry.coordinates; meters = r.distance;
      } catch (e) {
        line = [startPos, ...planned.stops.map((s) => [s.p.lat, s.p.lon])].map(([la, lo]) => [lo, la]);
        meters = line.reduce((a, c, i) => (i ? a + distM([line[i - 1][1], line[i - 1][0]], [c[1], c[0]]) : 0), 0) * DETOUR;
      }
      result = { ...planned, line, km: (meters / 1000).toFixed(1).replace(".", P.lang() === "en" ? "." : ",") };
      busy = "";
      draw(viewer, line, startPos, planned.stops, { name: (p) => txt(p.name), pick: (i) => startWalk(i) });
      emit("tv:route", { line, start: startPos, stops: planned.stops, mode: "walking", showCity: planned.stops.some((s) => !s.p.on_map) || distM(startPos, ORIGIN) > 900 });
      render();
    }

    async function startTour() {
      const o = trip.chosen, first = trip.first, from = [first.lat, first.lon];
      offset = o.total;
      const arrive = new Date(startTime().getTime() + offset * 60000);
      const planned = plan(P.points, from, budget, P.status, arrive);
      busy = t("tour.routing"); render();
      let line = [], meters = 0;
      if (planned.stops.length) {
        try { const r = await route(from, planned.stops); line = r.geometry.coordinates; meters = r.distance; }
        catch (e) {
          line = [from, ...planned.stops.map((s) => [s.p.lat, s.p.lon])].map(([la, lo]) => [lo, la]);
          meters = line.reduce((a, c, i) => (i ? a + distM([line[i - 1][1], line[i - 1][0]], [c[1], c[0]]) : 0), 0) * DETOUR;
        }
      }
      result = { ...planned, line, km: (meters / 1000).toFixed(1).replace(".", P.lang() === "en" ? "." : ",") };
      const legs = routeLegs(o);
      trip = null; busy = "";
      if (planned.stops.length) draw(viewer, line, from, planned.stops, { name: (p) => txt(p.name), pick: (i) => startWalk(i) });
      emit("tv:route", { legs: legs.concat(line.length ? [{ line, mode: "tour" }] : []), start: startPos, stops: planned.stops, showCity: true });
      render();
    }

    btn.onclick = () => { const open = !box.classList.contains("is-open"); document.querySelectorAll(".tv-tour.is-open").forEach((b) => b.classList.remove("is-open")); box.classList.toggle("is-open", open); render(); };
    document.addEventListener("tv:lang", render);
    render();
    window.tinyvigoTour = { plan, project, run, setWhen: (v) => { when = v; }, state: () => budget + "-" + when, startWalk: (i) => startWalk(i), setStart: (p) => { fromHere = true; navigator.geolocation.getCurrentPosition = (ok) => ok({ coords: { latitude: p[0], longitude: p[1] } }); }, open: () => { box.classList.add("is-open"); render(); }, setBudget: (b) => { budget = b; }, setFromHere: (v) => { fromHere = v; } };
  }

  if (window.tinyvigoPoints) init();
  else document.addEventListener("tv:ready", init, { once: true });
})();
