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
  const NEAR_MIN = 5; // a más de 5 min a pie del primer punto, preguntamos cómo quieres llegar (GO-01)
  const ROUTER = "https://routing.openstreetmap.de/routed-foot/route/v1/foot/";
  // PLANNER-01: puntos de salida fijos (estaciones de Renfe del GTFS de X-02)
  const STARTS = {
    here: { label: "tour.from_here" },
    centre: { label: "tour.from_centre", pos: [42.238072, -8.725813] },
    urzaiz: { label: "planner.from_urzaiz", pos: [42.234189, -8.713728] },
    guixar: { label: "planner.from_guixar", pos: [42.2392656, -8.7146089] },
    street: { label: "planner.from_street" },
  };
  const norm = (x) => String(x || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
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
  // (lat, lon) de la calle -> píxel del lienzo. GEO-02: el dibujo se pintó sobre un render de suelo
  // PLANO (pipeline/render/templates/render.html: proj(x, y, 0)), así que lo que va a ras de calle
  // (rutas, tráfico, paradas, farolas…) se proyecta con z = 0; con la cota del terreno se desviaba
  // hasta 40 px en las zonas altas y bajas y cruzaba manzanas. Los puntos de Navidad conservan su
  // posición precalculada (points.json), comprobada sobre cada monumento dibujado.
  function project(lat, lon) {
    const x = (lon - ORIGIN[1]) * MLAT * Math.cos(rad(ORIGIN[0])), y = (lat - ORIGIN[0]) * MLAT;
    const u = Math.cos(HEAD) * x - Math.sin(HEAD) * y, d = Math.sin(HEAD) * x + Math.cos(HEAD) * y;
    return [CANVAS / 2 + SCALE * u, CANVAS / 2 - SCALE * Math.sin(TILT) * d];
  }
  // vuelta: píxel del lienzo -> (lat, lon) del suelo
  function unproject(cx, cy) {
    const u = (cx - CANVAS / 2) / SCALE, d = -(cy - CANVAS / 2) / SCALE / Math.sin(TILT);
    const x = Math.cos(HEAD) * u + Math.sin(HEAD) * d, y = -Math.sin(HEAD) * u + Math.cos(HEAD) * d;
    return [ORIGIN[0] + y / MLAT, ORIGIN[1] + x / (MLAT * Math.cos(rad(ORIGIN[0])))];
  }
  // MAP-01: la proyección también se usa desde el mini-mapa y la ortofoto; queda a mano
  // para poder probarla con node sin arrancar el visor.
  window.tinyvigoGeo = { project, unproject, z };

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
  // ROUTE-02: same drop as the place markers (points.js), with the stop number where the type icon goes
  const PIN = '<svg class="tv-pin-shape" viewBox="3.8 1.8 16.4 20.4" aria-hidden="true"><path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/></svg>';
  let layer = null, pins = [];
  function draw(viewer, line, start, stops, onPick) {
    clear(viewer);
    layer = document.createElementNS(SVG, "svg");
    layer.setAttribute("viewBox", "0 0 " + CANVAS + " " + CANVAS);
    layer.setAttribute("class", "tv-route");
    const xy = line.map(([lo, la]) => project(la, lo)), fmt = (ps) => ps.map((p) => p[0].toFixed(1) + "," + p[1].toFixed(1)).join(" ");
    // GEO-02: where a building hides the street, the walk shows as a faint dashed line instead of
    // running over its roof; the visible stretches are drawn solid on top
    const O = window.tinyvigoOcclusion, runs = O ? O.visibleRuns(xy) : [xy];
    if (O && !(runs.length === 1 && runs[0] === xy)) for (const cls of ["tv-route-hidden-casing", "tv-route-hidden"]) {
      const ghost = document.createElementNS(SVG, "polyline");
      ghost.setAttribute("points", fmt(xy)); ghost.setAttribute("class", cls);
      layer.append(ghost);
    }
    for (const cls of ["tv-route-casing", "tv-route-line"]) for (const run of runs) {
      const pl = document.createElementNS(SVG, "polyline");
      pl.setAttribute("points", fmt(run)); pl.setAttribute("class", cls);
      layer.append(pl);
    }
    const s = project(start[0], start[1]);
    const me = document.createElementNS(SVG, "circle");
    me.setAttribute("cx", s[0]); me.setAttribute("cy", s[1]); me.setAttribute("r", 14); me.setAttribute("class", "tv-route-start");
    layer.append(me);
    viewer.addOverlay({ element: layer, location: new OpenSeadragon.Rect(0, 0, 1, 1) });
    // the stops are HTML pins anchored at the place itself (not floating above it), so they keep their
    // size at any zoom like the other markers; the place marker underneath is hidden by points.js
    pins = stops.map((st, i) => {
      // the pin stands where the place marker stands (points.json), on the drawn monument
      const [x, y] = st.p.x != null ? [st.p.x * CANVAS, st.p.y * CANVAS] : project(st.p.lat, st.p.lon);
      const b = document.createElement("button");
      b.type = "button"; b.className = "tv-stop-pin";
      b.innerHTML = PIN + '<span class="tv-stop-num">' + (i + 1) + "</span>";
      b.setAttribute("aria-label", (i + 1) + ". " + (onPick ? onPick.name(st.p) : ""));
      b.title = b.getAttribute("aria-label");
      viewer.addOverlay({ element: b, location: new OpenSeadragon.Point(x / CANVAS, y / CANVAS), placement: OpenSeadragon.Placement.BOTTOM });
      if (onPick) {
        b.addEventListener("pointerdown", (e) => e.stopPropagation());
        new OpenSeadragon.MouseTracker({ element: b, clickHandler: (e) => { e.preventDefaultAction = true; onPick.pick(i); } });
      }
      return b;
    });
    // encuadra la ruta
    const xs = line.map(([lo, la]) => project(la, lo));
    const minX = Math.min(...xs.map((p) => p[0])), maxX = Math.max(...xs.map((p) => p[0]));
    const minY = Math.min(...xs.map((p) => p[1])), maxY = Math.max(...xs.map((p) => p[1]));
    const pad = matchMedia("(max-width: 700px)").matches ? 90 : 420; // en escritorio los paneles tapan los bordes
    // MOB-01: en móvil la hoja tapa ~60 % de abajo; ampliamos el encuadre hacia abajo para que la ruta quede arriba, a la vista
    const h = maxY - minY + 2 * pad, below = matchMedia("(max-width: 700px)").matches ? h * 1.5 : 0;
    viewer.viewport.fitBounds(new OpenSeadragon.Rect((minX - pad) / CANVAS, (minY - pad) / CANVAS, (maxX - minX + 2 * pad) / CANVAS, (h + below) / CANVAS));
    viewer.viewport.applyConstraints(); // WEB-01: nunca deja ver fondo fuera del bloque
    setTimeout(declutter, 700);
  }
  // two stops a few pixels apart (same square, same street) share one pin: «3·4»
  function declutter() {
    const viewer = window.tinyvigo && window.tinyvigo.viewer;
    if (!viewer || !pins.length) return;
    const pos = pins.map((b) => { const r = b.getBoundingClientRect(); return [r.left + r.width / 2, r.bottom]; });
    const lead = pins.map((_, i) => i);
    for (let i = 0; i < pins.length; i++) {
      if (lead[i] !== i) continue;
      for (let j = i + 1; j < pins.length; j++) if (lead[j] === j && Math.hypot(pos[i][0] - pos[j][0], pos[i][1] - pos[j][1]) < 26) lead[j] = i;
    }
    pins.forEach((b, i) => {
      const group = lead.map((l, k) => (l === i ? k + 1 : 0)).filter(Boolean);
      b.style.visibility = lead[i] !== i ? "hidden" : ""; // OpenSeadragon sets display inline on overlays
      b.querySelector(".tv-stop-num").textContent = group.length ? group.join("·") : String(i + 1);
      b.classList.toggle("is-multi", group.length > 1);
      b.dataset.group = group.join(",");
    });
  }
  // the stop you are heading to stands out; the ones already seen step back
  function markPins(at) {
    pins.forEach((b, i) => {
      const group = (b.dataset.group || String(i + 1)).split(",").map((n) => +n - 1);
      b.classList.toggle("is-current", group.includes(at));
      b.classList.toggle("is-done", at >= 0 && group.every((k) => k < at));
    });
    document.dispatchEvent(new CustomEvent("tv:walk-at", { detail: at })); // TOUR-05: the satellite view colours its stops too
  }
  function clear(viewer) {
    if (layer) { viewer.removeOverlay(layer); layer = null; }
    pins.forEach((b) => viewer.removeOverlay(b)); pins = [];
  }

  // ── interfaz ─────────────────────────────────────────────────────────────
  function init() {
    const P = window.tinyvigoPoints, viewer = window.tinyvigo.viewer;
    const t = P.t, txt = P.txt;
    const btn = document.createElement("button");
    btn.className = "tv-tour-open";
    const box = document.createElement("section");
    box.className = "tv-tour";
    box.id = "tv-tour";
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-hidden", "true");
    btn.setAttribute("aria-controls", box.id);
    btn.setAttribute("aria-haspopup", "dialog");
    document.body.append(btn, box);
    let opener = null, preferredMode = "fastest";
    const closeBox = (restoreFocus = true) => {
      const wasOpen = box.classList.contains("is-open");
      box.classList.remove("is-open");
      render();
      if (wasOpen && restoreFocus && opener && document.body.contains(opener)) setTimeout(() => opener.focus(), 0);
    };
    const openBox = () => {
      const active = document.activeElement;
      opener = active && active !== document.body && active !== document.documentElement ? active : (document.getElementById("dock-ruta") || btn);
      box.classList.add("is-open");
      render();
      setTimeout(() => {
        const target = document.getElementById("tv-tour-title") || box.querySelector(".tv-close");
        if (target) target.focus({ preventScroll: true });
      }, 30);
    };
    let when = "now";
    const startTime = () => {
      if (when === "now") return new Date();
      const [h, m] = String(when).split(":"), d = new Date();
      d.setHours(+h, +(m || 0), 0, 0);
      if (d < new Date()) d.setDate(d.getDate() + 1);
      return d;
    };
    const whenText = (w) => (w === "now" ? t("tour.now") : String(w).includes(":") ? w : String(w).padStart(2, "0") + ":00");

    // PLANNER-02: a wheel picker (drag up or down and it snaps, like the iPhone one), in the app's
    // style. One value per row, the middle one is the choice. Mouse wheel, arrows and Home/End work;
    // screen readers get a spinbutton. Picking does not re-render the form (it would reset the wheel).
    function wheel(values, current, label, onPick) {
      const ITEM = 40;
      let idx = Math.max(0, values.findIndex(([v]) => String(v) === String(current)));
      const box = el("div", "tv-picker");
      // the scrolling list itself takes the focus and the keys (axe: a scrollable region must be focusable)
      const list = el("div", "tv-picker-list", ...values.map(([, text], i) => {
        const o = el("div", "tv-picker-item", text);
        o.onclick = () => go(i, true);
        return o;
      }));
      list.tabIndex = 0;
      list.setAttribute("role", "spinbutton");
      list.setAttribute("aria-label", label);
      list.setAttribute("aria-valuemin", "0"); list.setAttribute("aria-valuemax", String(values.length - 1));
      box.append(list);
      const mark = () => {
        [...list.children].forEach((c, i) => c.classList.toggle("is-on", i === idx));
        list.setAttribute("aria-valuenow", String(idx)); list.setAttribute("aria-valuetext", values[idx][1]);
      };
      const go = (i, smooth) => {
        idx = Math.max(0, Math.min(values.length - 1, i));
        list.scrollTo({ top: idx * ITEM, behavior: smooth ? "smooth" : "auto" });
        mark(); onPick(values[idx][0]);
      };
      let settle = 0;
      list.addEventListener("scroll", () => {
        clearTimeout(settle);
        settle = setTimeout(() => { const i = Math.round(list.scrollTop / ITEM); if (i !== idx) { idx = Math.max(0, Math.min(values.length - 1, i)); mark(); onPick(values[idx][0]); } }, 90);
      }, { passive: true });
      // click and drag with the mouse too (a finger already scrolls it); on release it snaps
      let drag = null;
      list.addEventListener("pointerdown", (e) => {
        if (e.pointerType !== "mouse" || e.button !== 0) return;
        drag = { y: e.clientY, top: list.scrollTop, moved: false };
        list.setPointerCapture(e.pointerId);
        list.style.scrollSnapType = "none"; // snapping fights a manual drag
      });
      list.addEventListener("pointermove", (e) => {
        if (!drag) return;
        const dy = e.clientY - drag.y;
        if (Math.abs(dy) > 3) drag.moved = true;
        list.scrollTop = drag.top - dy;
      });
      const release = (e) => {
        if (!drag) return;
        const moved = drag.moved; drag = null;
        list.releasePointerCapture(e.pointerId);
        list.style.scrollSnapType = "";
        if (moved) { e.preventDefault(); list.dataset.dragged = "1"; go(Math.round(list.scrollTop / ITEM), true); }
      };
      list.addEventListener("pointerup", release);
      list.addEventListener("pointercancel", release);
      // a drag must not count as a click on the item under the pointer
      list.addEventListener("click", (e) => { if (list.dataset.dragged) { e.stopPropagation(); delete list.dataset.dragged; } }, true);
      list.onkeydown = (e) => {
        const k = { ArrowDown: 1, ArrowUp: -1, PageDown: 4, PageUp: -4 }[e.key];
        if (k) { e.preventDefault(); go(idx + k, true); }
        else if (e.key === "Home") { e.preventDefault(); go(0, true); }
        else if (e.key === "End") { e.preventDefault(); go(values.length - 1, true); }
      };
      mark();
      requestAnimationFrame(() => { list.scrollTop = idx * ITEM; });
      return box;
    }
    const durText = (m) => (m < 60 ? t("tour.minutes", { min: m }) : Math.floor(m / 60) + " h" + (m % 60 ? " " + (m % 60) + " min" : ""));
    const DURATIONS = Array.from({ length: 16 }, (_, i) => (i + 1) * 15); // 15 min … 4 h
    function startTimes() {
      // now, then every quarter of an hour until 03:00 (the latest the lights stay on)
      const out = [["now", t("tour.now")]], d = new Date();
      d.setSeconds(0, 0); d.setMinutes(Math.ceil((d.getMinutes() + 1) / 15) * 15);
      const end = new Date(); end.setHours(3, 0, 0, 0); if (end <= new Date()) end.setDate(end.getDate() + 1);
      while (d <= end && out.length < 96) {
        const v = String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0");
        out.push([v, v]); d.setMinutes(d.getMinutes() + 15);
      }
      if (when !== "now" && !out.some(([v]) => v === whenText(when))) out.splice(1, 0, [whenText(when), whenText(when)]); // a shared link's time
      return out;
    }
    let budget = 60, fromHere = true, result = null, startPos = ORIGIN, busy = "", trip = null, offset = 0, editing = false, startKind = "here", startPick = null, streets = null;

    const el = (tag, cls, ...kids) => { const n = document.createElement(tag); if (cls) n.className = cls; n.append(...kids.filter((k) => k != null && k !== false)); return n; };
    const hhmm = (min) => { const d = new Date(startTime().getTime() + (min + offset) * 60000); return String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0"); };
    const gmaps = (mode, dest, way = []) => "https://www.google.com/maps/dir/?api=1&travelmode=" + mode + "&origin=" + startPos.join(",") + "&destination=" + dest.join(",") + (way.length ? "&waypoints=" + way.map((w) => w.join(",")).join("|") : "");

    function render() {
      const open = box.classList.contains("is-open");
      btn.replaceChildren(lu("route"), t("tour.open"));
      btn.setAttribute("aria-expanded", String(open));
      box.setAttribute("aria-hidden", String(!open));
      box.setAttribute("aria-label", t("tour.custom"));
      const dock = document.getElementById("dock-ruta");
      if (dock) dock.setAttribute("aria-expanded", String(open));
      box.replaceChildren();
      if (!open) return;
      const close = el("button", "tv-close", lu("x")); close.setAttribute("aria-label", t("common.close")); close.onclick = () => closeBox();
      const durWheel = wheel(DURATIONS.map((m) => [m, durText(m)]), DURATIONS.includes(budget) ? budget : 60, t("tour.duration"), (v) => { budget = v; });
      // PLANNER-01: la salida acepta mi ubicación, Porta do Sol, las dos estaciones o una calle
      const sel = el("select", "tv-start", ...Object.entries(STARTS).map(([k, v]) => Object.assign(el("option", null, t(v.label)), { value: k, selected: k === startKind })));
      sel.setAttribute("aria-label", t("planner.start"));
      sel.onchange = () => { startKind = sel.value; fromHere = startKind === "here"; startPick = STARTS[startKind].pos ? { pos: STARTS[startKind].pos, label: t(STARTS[startKind].label) } : null; render(); if (startKind === "street") loadStreets(); };
      let street = null;
      if (startKind === "street") {
        // SEARCH-02: any street or address, not only the centre's: the centre's streets first, then
        // OpenStreetMap (geocode.js), in a list under the box that updates in place while typing
        const input = el("input", "tv-street");
        Object.assign(input, { type: "search", placeholder: t("planner.street_placeholder"), value: startPick ? startPick.label : "", autocomplete: "off" });
        input.setAttribute("aria-label", t("planner.street_placeholder"));
        input.setAttribute("role", "combobox"); input.setAttribute("aria-autocomplete", "list"); input.setAttribute("aria-controls", "tv-street-list");
        const list = el("ul", "tv-street-list"); list.id = "tv-street-list"; list.setAttribute("role", "listbox");
        const pick = (it) => {
          startPick = { pos: [it.lat, it.lon], label: it.label + (it.sub ? ", " + it.sub : "") };
          input.value = startPick.label; list.replaceChildren(); input.setAttribute("aria-expanded", "false");
          go.disabled = false;
        };
        const item = (it) => {
          const b = el("button", "tv-street-opt", lu("map-pin", 16), el("span", null, el("strong", null, it.label), it.sub ? el("small", null, it.sub) : null));
          b.type = "button"; b.setAttribute("role", "option");
          b.onmousedown = (e) => e.preventDefault();
          b.onclick = () => pick(it);
          return el("li", null, b);
        };
        let remote = [], remoteState = "";
        const paint = () => {
          const q = norm(input.value);
          const local = q.length < 2 ? [] : (streets || []).filter((x) => norm(x[0]).includes(q)).slice(0, 5).map((x) => ({ label: x[0], sub: "Vigo", lat: x[1], lon: x[2] }));
          const seen = new Set(local.map((x) => norm(x.label)));
          const all = local.concat(remote.filter((x) => !seen.has(norm(x.label)) || x.house));
          list.replaceChildren(...all.slice(0, 8).map(item));
          if (!all.length && q.length >= 3) list.append(el("li", "tv-note", remoteState === "error" ? t("search.addr_error") : remoteState === "busy" ? t("search.looking", { q: input.value.trim() }) : t("search.none", { q: input.value.trim() })));
          input.setAttribute("aria-expanded", String(list.children.length > 0));
        };
        const look = window.tinyvigoGeocode ? window.tinyvigoGeocode.debounced((r, q) => {
          if (q.trim() !== input.value.trim()) return;
          remote = r || []; remoteState = r === null ? "error" : ""; paint();
        }) : null;
        input.oninput = () => {
          startPick = null; go.disabled = true; remote = [];
          remoteState = look && input.value.trim().length >= 3 ? "busy" : "";
          paint();
          if (remoteState === "busy") look(input.value.trim());
        };
        input.onkeydown = (e) => { if (e.key === "Enter") { const first = list.querySelector(".tv-street-opt"); if (first) { e.preventDefault(); first.click(); } } };
        street = el("div", "tv-street-wrap", input, list);
      }
      const from = el("div", "tv-from", el("label", "tv-note", t("planner.start")), sel, street);
      const whenWheel = wheel(startTimes(), when === "now" ? "now" : whenText(when), t("tour.when"), (v) => { when = v; });
      const go = el("button", "tv-btn tv-go tv-plan-start", lu("footprints"), el("span", "tv-plan-start-label", t("walk.start")));
      go.onclick = () => { editing = false; run(); };
      go.disabled = startKind === "street" && !startPick;
      const modeChoices = el("div", "tv-planmodes", ...["fastest", "after_dark", "easy_walk"].map((mode) => planMode(mode)));
      modeChoices.setAttribute("role", "radiogroup");
      modeChoices.setAttribute("aria-label", t("tour.custom"));
      // MOB-01: con un tour o un «cómo llegar» ya calculado, el formulario se pliega en una línea
      // de resumen para que la ruta se vea en el mapa; «Cambiar» lo vuelve a abrir.
      const folded = (result || trip) && !editing && !busy;
      box.classList.toggle("has-result", !!folded);
      if (folded) {
        const edit = el("button", "tv-btn tv-btn-quiet tv-edit", t("go.change"));
        edit.onclick = () => { editing = true; render(); };
        const whenLabel = whenText(when);
        // HUD v5: title + what was asked on one line, with «Cambiar» next to it
        box.append(close, Object.assign(el("h2", null, t("tour.custom")), { id: "tv-tour-title", tabIndex: -1 }), el("div", "tv-tour-head",
          el("p", "tv-kicker", t("tour.minutes", { min: budget }) + " · " + whenLabel + " · " + (startPick ? startPick.label : t(STARTS[startKind].label))), edit));
      } else {
        box.append(close, Object.assign(el("h2", null, t("tour.custom")), { id: "tv-tour-title", tabIndex: -1 }),
          el("div", "tv-pickers",
            el("div", "tv-picker-field", el("p", "tv-note tv-field-label", t("tour.duration")), durWheel),
            el("div", "tv-picker-field", el("p", "tv-note tv-field-label", t("tour.when")), whenWheel)),
          el("p", "tv-note tv-when-hint", t("tour.when_hint")), from,
          el("p", "tv-note tv-field-label", t("tour.kind")), modeChoices,
          el("div", "tv-sticky-foot", go));
      }
      if (busy) box.append(el("p", "tv-note", busy));
      if (folded) { const acc = accuracyNote(); if (acc) box.append(acc); }
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
    // TRAFFIC-01: the Concello's live traffic (data/live/trafico.json) next to the options, and the
    // slow sections a car route goes through. OSRM's car time knows nothing about traffic: it says so.
    let traffic = null, trafficAsked = false;
    const SLOW = (estado) => !["Muy fluido", "Fluido", "Normal"].includes(estado);
    function askTraffic() {
      if (trafficAsked || !window.tinyvigoData || !tinyvigoData.trafico) return;
      trafficAsked = true;
      tinyvigoData.trafico().then((d) => { traffic = d; render(); }).catch(() => {});
      setTimeout(() => { trafficAsked = false; }, 60000); // a minute later it may be asked again
    }
    const streetsOf = (fs) => [...new Set(fs.map((f) => f.properties.nombre_tramo.split(/ desde | entre /i)[0].trim()))].slice(0, 3).join(", ");
    function trafficNow() {
      if (!traffic) return null;
      const bad = traffic.data.features.filter((f) => SLOW(f.properties.estado));
      const when = String(traffic.source_timestamp || "").slice(11, 16);
      const text = bad.length ? t("go.traffic_slow", { streets: streetsOf(bad) }) : t("go.traffic_fluid");
      return el("p", "tv-note tv-traffic-now" + (bad.length ? " is-slow" : ""), lu(bad.length ? "triangle-alert" : "circle-check", 16), el("span", null, t("go.traffic_now", { time: when }) + " " + text));
    }
    function trafficOnRoute(o) {
      if (!traffic || o.mode !== "car") return null;
      const line = o.legs.filter((l) => l.mode === "car").flatMap((l) => l.line || []);
      if (!line.length) return null;
      const near = (c) => line.some(([lo, la], i) => i % 3 === 0 && distM([la, lo], [c[1], c[0]]) < 30);
      const hit = traffic.data.features.filter((f) => SLOW(f.properties.estado) && f.geometry.coordinates.some(near));
      return el("div", "tv-traffic-route",
        hit.length ? el("p", "tv-note is-slow", lu("triangle-alert", 16), el("span", null, t("go.traffic_route", { streets: streetsOf(hit) }))) : null,
        el("p", "tv-note", t("go.traffic_note")));
    }

    function renderGo() {
      askTraffic();
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
        return el("div", "tv-go", ...head, el("div", "tv-goopts", ...opts), trafficNow());
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
        trafficOnRoute(o),
        alt, start, el("div", "tv-actions", all, back));
    }
    function choose(o) {
      trip.chosen = o;
      emit("tv:route", { legs: routeLegs(o), start: startPos, stops: [], showCity: true });
      render();
    }

    const PLAN_ICON = { fastest: "footprints", after_dark: "star", easy_walk: "route" };
    function planMode(value) {
      const option = typeof value === "string" ? null : value;
      const mode = option ? option.mode : value;
      const selected = mode === preferredMode;
      const meta = option ? t("tour.minutes", { min: option.total }) : t("routes." + mode + "_body");
      const b = el("button", "tv-planmode" + (selected ? " is-on" : ""),
        el("span", "tv-set-ico", lu(PLAN_ICON[mode], 20)),
        el("span", "tv-planmode-body", el("span", "tv-planmode-name", t("planner." + mode)), el("span", "tv-planmode-meta", meta)),
        el("span", "tv-radio", null));
      b.type = "button";
      b.dataset.mode = mode;
      b.setAttribute("role", "radio");
      b.setAttribute("aria-checked", String(selected));
      b.onclick = () => {
        preferredMode = mode;
        const available = result && result.options && result.options.some((o) => o.mode === mode && o.ok !== false);
        if (available && result.mode !== mode) { busy = t("tour.routing"); render(); applyMode(mode); return; }
        render();
        const again = box.querySelector('[data-mode="' + mode + '"]'); if (again) again.focus();
      };
      return b;
    }
    function explain(o) {
      const base = t("planner.why_walk", { min: o.walkMin, m: o.walkMeters });
      if (o.mode === "after_dark") return base + " · " + (o.explain.unlitLegs == null ? t("planner.why_dark_day") : t("planner.why_dark", { n: String(o.explain.unlitLegs).replace(".", ",") }));
      if (o.mode === "easy_walk") return base + " · " + (o.explain.maxGradePct == null ? t("planner.why_easy_nodata") : t("planner.why_easy", { pct: o.explain.maxGradePct }));
      return base + " · " + t("planner.why_fastest");
    }
    function renderResult() {
      const { stops, later, closed, line, km } = result;
      if (!stops.length) return el("p", "tv-note", t("tour.nothing"));
      const ol = el("ol", "tv-story", ...stops.map((s, i) => {
        const b = el("button", null,
          s.p.photo ? Object.assign(el("img"), { src: s.p.photo, alt: "", loading: "lazy" }) : el("span", "tv-story-ph"),
          el("span", "tv-num", String(i + 1)),
          el("span", "tv-story-text", el("span", "tv-story-name", txt(s.p.name)),
            el("span", "tv-badge", t("tour.stop_at", { time: hhmm(s.arrive), stay: s.stay }))));
        b.onclick = () => startWalk(i);
        return el("li", null, b);
      }));
      const walk = el("button", "tv-btn tv-go", lu("footprints"), t("walk.start")); walk.onclick = () => startWalk(0);
      const gm = el("a", "tv-icon-btn", lu("arrow-up-right"));
      gm.setAttribute("aria-label", t("tour.open_gmaps")); gm.title = t("tour.open_gmaps");
      const dest = stops[stops.length - 1].p;
      gm.href = gmaps("walking", [dest.lat, dest.lon], stops.slice(0, -1).map((s) => [s.p.lat, s.p.lon]).slice(0, 9));
      gm.target = "_blank"; gm.rel = "noopener";
      const clr = el("button", "tv-icon-btn", lu("x")); clr.setAttribute("aria-label", t("tour.clear")); clr.title = t("tour.clear");
      clr.onclick = () => endRoute(false);
      const share = window.tinyvigoShare ? window.tinyvigoShare.button(t("tour.summary", { min: budget, n: stops.length, km })) : null;
      if (share) share.classList.add("tv-icon-btn");
      const opts = result.options || [];
      const cur = opts.find((o) => o.mode === result.mode);
      const tabs = opts.length > 1 ? el("div", "tv-planmodes tv-planmodes-seg", ...opts.map((o) => planMode(o))) : null;
      if (tabs) { tabs.setAttribute("role", "radiogroup"); tabs.setAttribute("aria-label", t("tour.custom")); }
      const why = cur ? el("p", "tv-note tv-why", explain(cur) + (result.source === "approx" ? " · " + t("go.approx") : "")) : null;
      return el("div", "tv-result",
        el("p", "tv-summary", t("tour.summary", { min: budget, n: stops.length, km })), tabs, why,
        el("p", "tv-note tv-field-label", t("walk.story")), ol,
        later.length ? el("details", "tv-later", el("summary", null, t("tour.later") + " · " + later.length),
          el("ul", null, ...later.slice(0, 12).map((l) => { const b = el("button", null, el("span", "tv-name", txt(l.p.name)), el("span", "tv-badge", t("tour.later_item", { km: l.km.toFixed(1), min: l.min }))); b.onclick = () => P.select(l.p); return el("li", null, b); }))) : null,
        closed.length ? el("details", "tv-later", el("summary", null, t("tour.closed_now") + " · " + closed.length),
          el("ul", null, ...closed.map((c) => el("li", null, el("button", null, el("span", "tv-name", txt(c.p.name)), el("span", "tv-badge", c.st.label)))))) : null,
        el("div", "tv-sticky-foot", walk, el("div", "tv-foot-icons", gm, share, clr)));
    }

    // ── paseo paso a paso: «primero la Bola, luego la Noria…» ──────────────
    const step = document.createElement("section");
    step.className = "tv-step";
    document.body.append(step);
    let at = -1, live = null, offer = false, legEl = null, followBtn = null;
    viewer.addHandler("animation-finish", declutter);
    // ROUTE-02: finishing (or clearing) a walk removes everything it drew: line, numbered pins,
    // the walked trace and «Seguirme», and the place markers come back
    function endRoute(done) {
      at = -1; result = null; trip = null; offset = 0; live = null; offer = false;
      clear(viewer);
      emit("tv:clear-route");
      document.querySelectorAll(".tv-marker.is-selected").forEach((m) => m.classList.remove("is-selected"));
      showStep(); render();
      if (done) toast(t("walk.ended"));
    }
    function toast(text) {
      let n = document.querySelector(".tv-ltoast");
      if (!n) { n = el("div", "tv-ltoast"); n.setAttribute("role", "status"); document.body.append(n); }
      n.textContent = text; n.classList.add("is-on");
      clearTimeout(toast.timer); toast.timer = setTimeout(() => n.classList.remove("is-on"), 2600);
    }
    // ROUTE-03: «Seguirme» (track.js) drives the card: the distance to the stop updates live and the
    // card moves on by itself once you have walked past a stop
    function paintLive() {
      if (!legEl || !followBtn || at < 0 || !result) return;
      const st = result.stops, from = at === 0 ? t("walk.you") : txt(st[at - 1].p.name);
      const togo = live ? Math.max(0, live.stops[at] - live.along) : null;
      legEl.lastChild.textContent = !live ? t("walk.leg", { min: legMin(at), from })
        : togo <= 20 ? t("walk.here")
        : t("walk.live", { m: Math.round(togo / 10) * 10, min: Math.max(1, Math.round(togo / WALK_MS / 60)) });
      legEl.classList.toggle("is-live", !!live);
      // no fix on the route: say so here and offer the simulation (track.js keeps its own bar off)
      const far = step.querySelector(".tv-step-far");
      if (offer && !far) followBtn.before(el("p", "tv-note tv-step-far", t("track.far_body")));
      if (!offer && far) far.remove();
      followBtn.replaceChildren(lu(live ? "x" : offer ? "route" : "crosshair", 18), el("span", null, live ? t("track.stop") : offer ? t("track.simulate") : t("track.follow")));
      followBtn.setAttribute("aria-pressed", String(!!live));
    }
    document.addEventListener("tv:track", (e) => {
      live = e.detail && e.detail.following && e.detail.stops.length ? e.detail : null;
      offer = !!(e.detail && e.detail.offer);
      if (at < 0 || !result) return;
      if (live) {
        const i = live.stops.findIndex((a) => live.along < a + 40);
        const want = i < 0 ? live.stops.length - 1 : i;
        if (want > at) { at = want; showStep(); return; }
      }
      paintLive();
    });
    function legMin(i) {
      const st = result.stops;
      return Math.max(1, Math.round(i === 0 ? st[0].arrive : st[i].arrive - st[i - 1].arrive - st[i - 1].stay));
    }
    function startWalk(i) {
      at = i;
      closeBox(false);
      showStep();
    }
    // STORY-01: cuerpo + «¿Sabías que…?» + filas con icono (compartido con la ficha de points.js)
    function stepStoryParts(p) {
      const c = P.storyContent(p);
      const parts = [];
      if (c.story) parts.push(el("p", "tv-story-body", c.story));
      if (c.fact) parts.push(el("aside", "tv-fact", el("span", "tv-fact-label", lu("lightbulb", 14), t("fact.know")), el("p", "tv-fact-text", c.fact)));
      if (c.facts.length) parts.push(el("ul", "tv-facts", ...c.facts.map((f) => el("li", null, lu(P.factIcon(f.kind), 16), el("span", null, f.text)))));
      return parts;
    }
    // HUD v5: the stop you are heading to, told in some detail (photo, what it is, its story),
    // «Siguiente» as the main action and the whole route one tap away, folded.
    function showStep() {
      step.replaceChildren();
      step.classList.toggle("is-open", at >= 0 && !!result);
      document.body.classList.toggle("is-walking", at >= 0 && !!result);
      markPins(result ? at : -1);
      legEl = followBtn = null;
      if (at < 0 || !result) return;
      const st = result.stops, s = st[at], p = s.p, last = at === st.length - 1;
      const from = at === 0 ? t("walk.you") : txt(st[at - 1].p.name);
      const close = el("button", "tv-close", lu("x")); close.setAttribute("aria-label", t("common.close")); close.onclick = () => { at = -1; showStep(); };
      const prev = el("button", "tv-step-nav tv-step-prev", lu("chevron-left"), el("span", null, t("walk.prev")));
      prev.setAttribute("aria-label", t("walk.prev"));
      prev.disabled = at === 0; prev.onclick = () => { at--; showStep(); };
      const next = el("button", "tv-step-nav tv-step-next" + (last ? " is-end" : ""), el("span", null, last ? t("walk.finish") : t("walk.next")), last ? lu("check") : lu("chevron-right"));
      next.setAttribute("aria-label", last ? t("walk.finish") : t("walk.next"));
      next.onclick = () => { if (last) endRoute(true); else { at++; showStep(); } };
      followBtn = el("button", "tv-step-follow");
      followBtn.type = "button";
      followBtn.onclick = () => { const T = window.tinyvigoTrack; if (!T) return; if (live) T.halt(); else if (offer) T.startSim(); else T.start(); };
      const nextStop = last ? null : el("p", "tv-step-next-stop", t("walk.next_stop", { name: txt(st[at + 1].p.name) }));
      const progress = el("div", "tv-step-dots", ...st.map((_, i) => el("span", i === at ? "is-on" : i < at ? "is-done" : "")));
      const route = el("details", "tv-step-route", el("summary", null, lu("list", 16), t("walk.full_route", { n: st.length })),
        el("ol", null, ...st.map((x, i) => {
          const b = el("button", i === at ? "is-on" : i < at ? "is-done" : "", el("span", "tv-num", String(i + 1)), el("span", "tv-name", txt(x.p.name)), el("span", "tv-badge", hhmm(x.arrive)));
          b.type = "button"; b.onclick = () => { at = i; showStep(); };
          return el("li", null, b);
        })));
      step.append(...[
        close,
        el("p", "tv-kicker", t("walk.step", { n: at + 1, total: st.length }) + " · " + hhmm(s.arrive)),
        progress,
        Object.assign(el("h2", null, txt(p.name)), { id: "tv-step-title", tabIndex: -1 }),
        legEl = el("p", "tv-step-leg", lu("footprints", 16), el("span", null, t("walk.leg", { min: legMin(at), from }))),
        p.photo ? Object.assign(el("img", "tv-step-photo"), { src: p.photo, alt: txt(p.name), loading: "lazy", decoding: "async" }) : null,
        ...stepStoryParts(p),
        last ? el("p", "tv-note", t("walk.end")) : null,
        route,
        el("div", "tv-sticky-foot tv-step-foot", nextStop, window.tinyvigoTrack ? followBtn : null, el("div", "tv-step-nav-row", prev, next)),
      ].filter(Boolean));
      paintLive();
      step.scrollTop = 0;
      // the map follows on the drawn map only; it never switches style on its own
      if (p.on_map && !document.body.classList.contains("is-city")) {
        // centre the stop in the part of the map the card leaves free (right card on a wide
        // screen, bottom sheet on a phone): 1 viewport unit = container width × zoom pixels
        const vp = viewer.viewport, zoom = Math.max(vp.getZoom(), vp.getHomeZoom() * 2.2);
        const phone = matchMedia("(max-width: 700px)").matches, unit = viewer.container.clientWidth * zoom;
        const dx = phone ? 0 : (step.offsetWidth + 12) / 2 / unit, dy = phone ? step.offsetHeight / 2 / unit : 0;
        vp.zoomTo(zoom);
        vp.panTo(new OpenSeadragon.Point(p.x + dx, p.y + dy));
        vp.applyConstraints(); // never past the drawing's edge
      }
      document.dispatchEvent(new CustomEvent("tv:select", { detail: p }));
      document.querySelectorAll(".tv-marker").forEach((m) => m.classList.toggle("is-selected", m.getAttribute("aria-label") === txt(p.name)));
    }
    document.addEventListener("tv:lang", showStep);
    document.addEventListener("tv:stories", showStep);

    // LOC-01: the best fix the device can give (GPS on a phone; on a computer it comes from the wifi
    // and can be a street off). The margin is kept: past 40 m the form says so and offers to pick the street.
    let fixAccuracy = null;
    function locate() {
      return new Promise((res) => {
        if (!fromHere || !navigator.geolocation) return res(null);
        navigator.geolocation.getCurrentPosition((p) => { fixAccuracy = Math.round(p.coords.accuracy || 0); res([p.coords.latitude, p.coords.longitude]); },
          () => res(null), { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 });
      });
    }
    function accuracyNote() {
      if (startKind !== "here" || !fixAccuracy || fixAccuracy <= 40) return null;
      const pick = el("button", "tv-btn tv-btn-quiet", lu("map-pin", 16), t("tour.pick_street"));
      pick.type = "button";
      pick.onclick = () => { startKind = "street"; fromHere = false; startPick = null; editing = true; result = null; trip = null; emit("tv:clear-route"); render(); loadStreets(); };
      return el("div", "tv-accuracy", el("p", "tv-note", lu("crosshair", 16), el("span", null, t("tour.approx_location", { m: fixAccuracy }))), pick);
    }

    async function run() {
      result = null; trip = null; offset = 0; busy = fromHere ? t("tour.locating") : ""; emit("tv:clear-route"); render();
      const here = startKind === "here" ? await locate() : startPick ? startPick.pos : null;
      if (startKind === "here" && !here) busy = t("tour.no_location");
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
      await finish(startPos, planned, startTime());
    }

    // PLANNER-01: optimiza el orden con 3 criterios (js/planner.js) y dibuja la opción elegida
    async function finish(from, planned, at) {
      let options = null, source = null;
      if (window.tinyvigoPlanner && planned.stops.length > 1) {
        const lights = P.points.filter((p) => p.type === "light" && (P.status(p, at) || {}).open).map((p) => [p.lat, p.lon]);
        const h = at.getHours();
        const res = await tinyvigoPlanner.plan({
          start: from,
          stops: planned.stops.map((s) => ({ id: s.p.id, lat: s.p.lat, lon: s.p.lon, stay: s.stay })),
          signals: { dark: h >= 18 || h < 8, lights, elev: elev ? (la, lo) => z(la, lo) : null },
        });
        options = res.options.filter((o) => o.ok); source = res.source;
      }
      const preferred = options && (options.find((o) => o.mode === preferredMode) || options[0]);
      result = { ...planned, options, source, from, mode: preferred ? preferred.mode : null };
      await applyMode(result.mode);
    }
    async function applyMode(mode) {
      const o = result.options && result.options.find((x) => x.mode === mode);
      if (o) {
        const byId = new Map(result.stops.map((s) => [s.p.id, s]));
        result.stops = o.legs.map((l) => ({ ...byId.get(l.id), arrive: l.arrive, stay: l.stay }));
        result.mode = mode;
        preferredMode = mode;
      }
      const from = result.from, stops = result.stops;
      let line, meters;
      try { const r = await route(from, stops); line = r.geometry.coordinates; meters = r.distance; }
      catch (e) {
        line = [from, ...stops.map((s) => [s.p.lat, s.p.lon])].map(([la, lo]) => [lo, la]);
        meters = line.reduce((a, c, i) => (i ? a + distM([line[i - 1][1], line[i - 1][0]], [c[1], c[0]]) : 0), 0) * DETOUR;
      }
      result.line = line;
      result.km = (meters / 1000).toFixed(1).replace(".", P.lang() === "en" ? "." : ",");
      busy = "";
      if (stops.length) draw(viewer, line, from, stops, { name: (p) => txt(p.name), pick: (i) => startWalk(i) });
      // TOUR-05: only the Christmas walk is drawn (the way here is gone once you are here), framed on
      // its own. It is walked on the drawn map; the satellite only when a stop falls outside the drawing
      // (Samil, the circus).
      const m = window.tinyvigo.manifest, off = stops.some((s) => { const [x, y] = project(s.p.lat, s.p.lon); return !(x > 0 && y > 0 && x < m.width && y < m.height); });
      emit("tv:route", { line, start: from, stops, mode: "walking", showCity: off });
      if (!off && document.body.classList.contains("is-city") && window.tinyvigoCity) tinyvigoCity.setCity(false);
      render();
    }
    async function loadStreets() {
      if (streets) return;
      try { streets = await (await fetch("data/streets.json")).json(); } catch (e) { streets = []; }
      render();
    }

    async function startTour() {
      const o = trip.chosen, first = trip.first, from = [first.lat, first.lon];
      offset = o.total;
      const arrive = new Date(startTime().getTime() + offset * 60000);
      const planned = plan(P.points, from, budget, P.status, arrive);
      trip = null; busy = t("tour.routing"); render();
      await finish(from, planned, arrive);
    }

    // SHARE-02: a shared link carries THIS walk (stops in order, start, time) and opens it as it was,
    // without planning again: same stops, same order, same line
    function shareState() {
      if (!result || !result.stops || !result.stops.length) return null;
      return { ids: result.stops.map((s) => s.p.id), from: result.from, when, budget };
    }
    async function openShared(s) {
      const pts = (s.ids || []).map((id) => P.points.find((p) => p.id === id)).filter(Boolean);
      if (!pts.length) return false;
      if (s.when) when = s.when;
      if (s.budget) budget = s.budget;
      const from = s.from || ORIGIN;
      let here = from, used = 0;
      const stops = pts.map((p) => {
        const w = walkMin(here, [p.lat, p.lon]), stay = STAY[p.type] || 5, st = { p, arrive: used + w, stay };
        used += w + stay; here = [p.lat, p.lon];
        return st;
      });
      trip = null; offset = 0; editing = false; startPos = from;
      result = { stops, later: [], closed: [], used, options: null, source: null, from, mode: null };
      busy = t("tour.routing"); openBox(); render();
      await applyMode(null);
      return true;
    }

    btn.onclick = () => { if (box.classList.contains("is-open")) closeBox(); else openBox(); };
    document.addEventListener("tv:lang", render);
    render();
    window.tinyvigoTour = { plan, project, unproject, run, shareState, openShared, setWhen: (v) => { when = v; }, state: () => budget + "-" + when, startWalk: (i) => startWalk(i), setStart: (p) => { fromHere = true; navigator.geolocation.getCurrentPosition = (ok) => ok({ coords: { latitude: p[0], longitude: p[1] } }); }, open: openBox, setBudget: (b) => { budget = b; }, setFromHere: (v) => { fromHere = v; startKind = v ? "here" : "centre"; startPick = v ? null : { pos: STARTS.centre.pos, label: "Porta do Sol" }; }, setStart2: (k) => { startKind = k; fromHere = k === "here"; startPick = STARTS[k].pos ? { pos: STARTS[k].pos, label: k } : null; }, result: () => result };
  }

  if (window.tinyvigoPoints) init();
  else document.addEventListener("tv:ready", init, { once: true });
})();
