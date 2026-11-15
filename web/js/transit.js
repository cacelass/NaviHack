// TinyVigo: bus y tren en horario PROGRAMADO (X-04). Datos: data/transit.json (scripts/build_transit_web.py).
// Nunca decimos «llega en»: Vitrasa no publica tiempo real oficial y Renfe AV/LD/MD tampoco para Vigo.
(function () {
  let data = null, loading = null;
  const load = () => loading || (loading = fetch("data/transit.json").then((r) => r.json()).then((d) => (data = d)).catch(() => null));
  const R = 6371000, rad = (x) => (x * Math.PI) / 180;
  const dist = (a, b, c, d) => { const p = rad(c - a), q = rad(d - b); const h = Math.sin(p / 2) ** 2 + Math.cos(rad(a)) * Math.cos(rad(c)) * Math.sin(q / 2) ** 2; return 2 * R * Math.asin(Math.sqrt(h)); };
  const ymd = (d) => d.getFullYear() + String(d.getMonth() + 1).padStart(2, "0") + String(d.getDate()).padStart(2, "0");
  const hm = (min) => String(Math.floor(min / 60) % 24).padStart(2, "0") + ":" + String(min % 60).padStart(2, "0");
  const nowMin = (d) => d.getHours() * 60 + d.getMinutes();
  const P = () => window.tinyvigoPoints;
  const t = (k, v) => (P() ? P().t(k, v) : k);

  // BUS-02: the GTFS Vitrasa publishes covers about a week. Outside it, the same weekday of the
  // published week stands in (the timetable repeats weekly) instead of «no buses» for everyone.
  function active(day) {
    const on = (key) => new Set(data.services.map((dates, i) => (dates.includes(key) ? i : -1)).filter((i) => i >= 0));
    const svc = on(ymd(day));
    if (svc.size) return svc;
    const known = [...new Set(data.services.flat())].sort();
    const same = known.filter((k) => new Date(+k.slice(0, 4), +k.slice(4, 6) - 1, +k.slice(6, 8)).getDay() === day.getDay());
    if (!same.length) return svc;
    // before the published week: its first such day; after it: its last one
    return on(ymd(day) < known[0] ? same[0] : same[same.length - 1]);
  }
  // BUS-02: departures of ANY stop, from the trips (data.departures only has the stops next to a point)
  function departuresOf(stopId) {
    if (data.departures[stopId]) return data.departures[stopId];
    if (!data._deps) {
      const idx = new Map(), detour = new Map(data.stops.map(([id, , , , d]) => [id, d]));
      data.trips.forEach(([line, headsign, s, stops, mins]) => stops.forEach((st, i) => {
        if (i === stops.length - 1) return; // the last stop: nobody boards there
        (idx.get(st) || idx.set(st, []).get(st)).push([mins[i], line, headsign, s]);
      }));
      for (const v of idx.values()) v.sort((a, b) => a[0] - b[0]);
      data._deps = { idx, detour, at: new Map(data.all_stops.map(([id], i) => [id, i])) };
    }
    const D = data._deps, d = D.detour.get(stopId) ? 1 : 0;
    return (D.idx.get(D.at.get(stopId)) || []).map(([m, l, h, s]) => [m, l, h, s, d]);
  }
  const stopById = () => (data._stops ||= Object.fromEntries(data.stops.map(([id, name, lat, lon, detour]) => [id, { id, name, lat, lon, detour }])));

  // próximas salidas programadas de una parada: [{time, line, headsign, detour}]
  function nextDepartures(stopId, when = new Date(), n = 3) {
    if (!data) return [];
    const svc = active(when), m = nowMin(when);
    return departuresOf(stopId).filter(([min, , , s]) => svc.has(s) && min >= m).slice(0, n)
      .map(([min, line, headsign, , detour]) => ({ time: hm(min), line, headsign, detour: !!detour }));
  }

  // BUS-02: «no quedan hoy» only when some bus did stop here today; otherwise say none runs today
  function emptyText(stopId, when = new Date()) {
    const day = new Date(when); day.setHours(0, 0, 0, 0);
    return t(nextDepartures(stopId, day, 1).length ? "transit.no_more_today" : "transit.none_today");
  }

  // bus directo al centro desde las paradas a ≤ 600 m de (lat, lon): el que antes te deja allí
  function toCentre(lat, lon, when = new Date()) {
    if (!data) return null;
    const svc = active(when), m = nowMin(when), stops = stopById();
    let best = null;
    for (const [id, deps] of Object.entries(data.to_centre)) {
      const s = stops[id]; if (!s) continue;
      const d = dist(lat, lon, s.lat, s.lon); if (d > 600) continue;
      const walk = Math.ceil(d / 75); // 4,5 km/h
      const dep = deps.find(([min, , sv]) => svc.has(sv) && min >= m + walk);
      if (!dep) continue;
      const arrive = dep[0] + dep[3];
      if (!best || arrive < best.arriveMin) best = { stop: s.name, walk, line: dep[1], time: hm(dep[0]), ride: dep[3], arrive: hm(arrive), arriveMin: arrive };
    }
    return best;
  }

  // trenes de Renfe en Vigo: próximas salidas/llegadas programadas
  function trains(when = new Date(), kind = "departure", n = 4) {
    const tr = data && data.trains; if (!tr) return [];
    const d = ymd(when), wd = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"][when.getDay()], m = hm(nowMin(when));
    const runs = (sid) => {
      if ((tr.removed[sid] || []).includes(d)) return false;
      if ((tr.added[sid] || []).includes(d)) return true;
      const c = tr.calendar[sid]; return !!c && c.start <= d && d <= c.end && c.days.includes(wd);
    };
    return tr.movements.filter((x) => x.type === kind && x.time >= m && runs(x.service_id)).slice(0, n);
  }

  // ── UI ─────────────────────────────────────────────────────────────────────
  const el = (tag, cls, ...kids) => { const x = document.createElement(tag); if (cls) x.className = cls; x.append(...kids.filter((k) => k != null)); return x; };

  function departuresBlock(p) {
    const near = data && data.near[p.id];
    if (!near) return null;
    const s = stopById()[near.stop_id], deps = nextDepartures(near.stop_id);
    const ic = document.createElement("span"); ic.className = "tv-transit-ic"; ic.innerHTML = window.LU ? LU.svg("bus", { size: 18 }) : "";
    const walk = Math.max(1, Math.round((near.distance_m * 1.3) / 75));
    const box = el("div", "tv-transit",
      el("div", "tv-transit-head", ic, el("div", "tv-transit-stop", el("strong", null, s ? s.name : near.stop_id), el("span", null, near.distance_m + " m · " + t("common.walk_min", { min: walk })))),
      deps.length
        ? el("ul", "tv-deps", ...deps.map((x) => el("li", null, el("b", "tv-dep-time", x.time), el("span", "tv-line", x.line), el("span", "tv-dep-to", x.headsign), x.detour ? el("span", "tv-badge", "⚠") : null)))
        : el("p", "tv-note", emptyText(near.stop_id)),
      el("div", "tv-transit-foot",
        s ? Object.assign(el("a", "tv-leg-maps tv-stop-maps", t("transit.go_to_stop")), {
          // sin origen: Google Maps usa la ubicación del móvil
          href: "https://www.google.com/maps/dir/?api=1&travelmode=walking&destination=" + s.lat.toFixed(6) + "," + s.lon.toFixed(6),
          target: "_blank", rel: "noopener", title: t("transit.go_to_stop") + " · " + s.name,
        }) : null,
        el("p", "tv-note tv-transit-note", t("transit.scheduled"))));
    return box;
  }

  document.addEventListener("tv:select", (e) => {
    const p = e.detail;
    load().then(() => setTimeout(() => {
      const sheet = document.querySelector(".tv-sheet"); if (!sheet || !data) return;
      const target = sheet.querySelector(".tv-pane-go") || sheet; // HUD v5: departures live in «Llegar»
      sheet.querySelectorAll(".tv-transit").forEach((n) => n.remove());
      const b = departuresBlock(p); if (b) target.append(b);
    }, 0));
  });

  // capa de paradas y estaciones en la vista ciudad
  function addLayers() {
    const C = window.tinyvigoCity; if (!C || !data) return;
    const stopHtml = (id, name) => { const deps = nextDepartures(id); return "<strong>" + name + "</strong><br>" + (deps.length ? deps.map((x) => x.time + " · " + x.line + " → " + x.headsign).join("<br>") : emptyText(id)) + "<br><small>" + t("transit.scheduled") + "</small>"; };
    const stationHtml = (name) => { const rows = trains().filter((x) => x.station === name); return "<strong>" + name + "</strong><br>" + (rows.length ? rows.map((x) => x.time + " · " + x.train + " → " + x.to).join("<br>") : t("transit.no_more_today")) + "<br><small>" + t("transit.scheduled") + "</small>"; };
    if (C.kind === "3d") { // MAP3D-01
      const POS = { "Vigo Urzaiz": [42.234189, -8.713728], "Vigo-Guixar": [42.2392656, -8.7146089] };
      C.addTransit({ stops: data.stops, stations: ((data.trains && data.trains.stations) || []).map((st) => ({ name: st.name, lat: (POS[st.name] || POS["Vigo-Guixar"])[0], lon: (POS[st.name] || POS["Vigo-Guixar"])[1] })), stopHtml, stationHtml });
      return;
    }
    if (!window.L) return;
    const layer = L.layerGroup().addTo(C.map);
    // paradas de bus: discretas y solo a nivel de calle (zoom >= 17), no las ~1000 de Vigo a la vez
    const stopLayer = L.layerGroup();
    const STOP_ZOOM = 17;
    const syncStops = () => (C.map.getZoom() >= STOP_ZOOM ? stopLayer.addTo(C.map) : stopLayer.remove());
    C.map.on("zoomend", syncStops); syncStops();
    for (const [id, name, lat, lon, detour] of data.stops) {
      L.circleMarker([lat, lon], { radius: 3, weight: 1, color: "#3d6a96", fillColor: detour ? "#f4cd80" : "#ffffff", fillOpacity: 1, opacity: 0.9 })
        .on("click", function () {
          const deps = nextDepartures(id);
          this.bindPopup("<strong>" + name + "</strong><br>" + (deps.length ? deps.map((x) => x.time + " · " + x.line + " → " + x.headsign).join("<br>") : emptyText(id)) + "<br><small>" + t("transit.scheduled") + "</small>").openPopup();
        }).addTo(stopLayer);
    }
    for (const st of (data.trains && data.trains.stations) || []) {
      const pos = st.name === "Vigo Urzaiz" ? [42.234189, -8.713728] : [42.2392656, -8.7146089];
      L.marker(pos, { icon: L.divIcon({ className: "", html: '<div class="tv-train">' + (window.LU ? LU.svg("train-front", { size: 16 }) : "🚆") + "</div>", iconSize: [28, 28], iconAnchor: [14, 14] }), title: st.name })
        .on("click", function () {
          const rows = trains().filter((x) => x.station === st.name);
          this.bindPopup("<strong>" + st.name + "</strong><br>" + (rows.length ? rows.map((x) => x.time + " · " + x.train + " → " + x.to).join("<br>") : t("transit.no_more_today")) + "<br><small>" + t("transit.scheduled") + "</small>").openPopup();
        }).addTo(layer);
    }
  }
  load().then(() => { let n = 0; const wait = () => (window.tinyvigoCity ? addLayers() : ++n < 100 && setTimeout(wait, 300)); wait(); });

  // para el planner (tour.js): opción de bus programado hasta el centro
  function renderToCentre(start, when) {
    const r = toCentre(start[0], start[1], when);
    if (!r) return null;
    return el("p", "tv-note tv-transit-leg", t("transit.direct_bus", r) + " · " + t("transit.scheduled"));
  }

  window.tinyvigoTransit = { load, nextDepartures, toCentre, trains, renderToCentre, emptyText, active: (when) => (data ? active(when) : new Set()) };
})();
