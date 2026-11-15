// NaviVigo «Vista ciudad» en 3D (MAP3D-01): fuera del dibujo, el mundo real con satélite, edificios
// de OpenStreetMap levantados en 3D y los nombres de las calles, con las rutas de «cómo llegar»
// dibujadas encima. MapLibre GL (BSD-3, vendor/maplibre) se carga la primera vez que se abre.
// Fuentes: PNOA (IGN, CC BY 4.0) en España y World Imagery (Esri) en el resto; edificios y nombres,
// OpenStreetMap vía OpenFreeMap (ODbL). Sin WebGL, se queda la vista 2D de siempre (city.js).
// Expone la misma API que city.js: map, setCity, focus, popup, setWalked, clearWalked, addTransit.
(function () {
  const webgl = (() => { try { const c = document.createElement("canvas"); return !!(c.getContext("webgl2") || c.getContext("webgl")); } catch (e) { return false; } })();
  if (!webgl) return; // city.js toma el relevo

  const PNOA = "https://www.ign.es/wmts/pnoa-ma?request=GetTile&service=WMTS&version=1.0.0&layer=OI.OrthoimageCoverage&style=default&tilematrixset=GoogleMapsCompatible&tilematrix={z}&tilerow={y}&tilecol={x}&format=image/jpeg";
  const ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";
  const VIGO = [-8.7215, 42.2375];
  const STYLE = {
    car: { color: "#4ea3ff", width: 6 },
    bus: { color: "#34c38f", width: 6 },
    walk: { color: "#f4cd80", width: 4, dash: [0.5, 2] },
    tour: { color: "#f4cd80", width: 5 },
  };
  const esc = (s) => String(s || "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const PIN = '<svg class="tv-pin-shape" viewBox="3.8 1.8 16.4 20.4" aria-hidden="true"><path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/></svg>';

  let map = null, loading = null, P = null, t = (k) => k, txt = (o) => o;
  const queue = []; // what was asked before the map existed
  const markers = { route: [], park: [], stations: [] };
  let lastBounds = null, walkedMe = null, transitArgs = null;
  const wrap = document.createElement("div");
  wrap.id = "city";
  wrap.className = "tv-city3d";
  const btn = document.createElement("button");
  btn.className = "tv-view";

  const phone = () => matchMedia("(max-width: 700px)").matches;
  const pad = () => (phone() ? { top: 90, left: 24, right: 24, bottom: Math.round(innerHeight * 0.62) } : { top: 80, left: 60, right: 60, bottom: 80 });

  function marker(html, lngLat, opts = {}) {
    const el = document.createElement("div");
    el.innerHTML = html;
    const node = el.firstElementChild || el;
    if (opts.title) node.title = opts.title;
    if (opts.onClick) { node.style.cursor = "pointer"; node.addEventListener("click", (e) => { e.stopPropagation(); opts.onClick(); }); }
    return new maplibregl.Marker({ element: node, anchor: opts.anchor || "center" }).setLngLat(lngLat).addTo(map);
  }
  function popup(lat, lon, html) {
    if (!map) { queue.push(() => popup(lat, lon, html)); return; }
    new maplibregl.Popup({ maxWidth: "260px", offset: 18 }).setLngLat([lon, lat]).setHTML(html).addTo(map);
  }

  async function load() {
    if (map) return map;
    if (loading) return loading;
    loading = (async () => {
      const need = window.tinyvigo && window.tinyvigo.need;
      if (!window.maplibregl) {
        const css = document.createElement("link"); css.rel = "stylesheet"; css.href = "vendor/maplibre/maplibre-gl.css"; document.head.append(css);
        await need(() => window.maplibregl, "vendor/maplibre/maplibre-gl.js");
      }
      map = new maplibregl.Map({
        container: wrap,
        center: VIGO, zoom: 15.2, pitch: 58, bearing: -15, maxPitch: 70,
        attributionControl: { compact: true },
        style: {
          version: 8,
          glyphs: "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
          sources: {
            world: { type: "raster", tiles: [ESRI], tileSize: 256, maxzoom: 19, attribution: "Imágenes: Esri, Maxar, Earthstar Geographics" },
            pnoa: { type: "raster", tiles: [PNOA], tileSize: 256, maxzoom: 20, bounds: [-9.4, 35.9, 4.4, 43.9], attribution: "PNOA © Instituto Geográfico Nacional" },
            osm: { type: "vector", url: "https://tiles.openfreemap.org/planet", attribution: "© OpenStreetMap · OpenFreeMap" },
          },
          layers: [
            { id: "sat-world", type: "raster", source: "world" },
            { id: "sat-es", type: "raster", source: "pnoa", minzoom: 6 },
            { id: "buildings", type: "fill-extrusion", source: "osm", "source-layer": "building", minzoom: 14,
              paint: { "fill-extrusion-color": "#f3ecdc", "fill-extrusion-height": ["coalesce", ["get", "render_height"], 9], "fill-extrusion-base": ["coalesce", ["get", "render_min_height"], 0], "fill-extrusion-opacity": 0.42 } },
            { id: "street-names", type: "symbol", source: "osm", "source-layer": "transportation_name", minzoom: 14.5,
              layout: { "symbol-placement": "line", "text-field": ["coalesce", ["get", "name"], ""], "text-font": ["Noto Sans Regular"], "text-size": 12, "text-max-angle": 30 },
              paint: { "text-color": "#ffffff", "text-halo-color": "rgba(16,18,26,.85)", "text-halo-width": 1.6 } },
            { id: "places", type: "symbol", source: "osm", "source-layer": "place", maxzoom: 15,
              layout: { "text-field": ["coalesce", ["get", "name"], ""], "text-font": ["Noto Sans Bold"], "text-size": ["interpolate", ["linear"], ["zoom"], 6, 11, 13, 15] },
              paint: { "text-color": "#ffffff", "text-halo-color": "rgba(16,18,26,.85)", "text-halo-width": 1.8 } },
          ],
        },
      });
      map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "bottom-right");
      await new Promise((res) => map.once("load", res));
      // credits folded behind the (i) button: they took the whole bottom strip
      const attrib = wrap.querySelector(".maplibregl-ctrl-attrib"); if (attrib) attrib.classList.remove("maplibregl-compact-show");
      // las rutas y lo andado: fuentes vacías listas para recibir datos
      map.addSource("route", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      map.addLayer({ id: "route-casing", type: "line", source: "route", layout: { "line-join": "round", "line-cap": "round" }, paint: { "line-color": "#151b2a", "line-opacity": 0.8, "line-width": ["+", ["get", "w"], 4] } });
      for (const [mode, s] of Object.entries(STYLE)) {
        map.addLayer({ id: "route-" + mode, type: "line", source: "route", filter: ["==", ["get", "mode"], mode], layout: { "line-join": "round", "line-cap": "round" },
          paint: Object.assign({ "line-color": s.color, "line-width": s.width }, s.dash ? { "line-dasharray": s.dash } : {}) });
      }
      map.addSource("walked", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      map.addLayer({ id: "walked", type: "line", source: "walked", layout: { "line-join": "round", "line-cap": "round" }, paint: { "line-color": "#8a8f9c", "line-width": 6, "line-opacity": 0.95 } });
      addPoints(); loadParkings(); setInterval(loadParkings, 120000);
      if (transitArgs) addTransit(transitArgs);
      queue.splice(0).forEach((f) => f());
      return map;
    })();
    return loading;
  }

  // puntos de Navidad: la misma gota dorada con el icono del tipo que en el dibujo
  function addPoints() {
    for (const p of P.points) {
      const st = P.status(p);
      marker('<button type="button" class="tv-marker tv-marker-3d' + (st && st.open ? " is-open" : "") + '">' + PIN + (window.LU ? LU.svg(P.typeIcon(p.type), { size: 14 }) : "") + "</button>",
        [p.lon, p.lat], { anchor: "bottom", title: txt(p.name), onClick: () => P.select(p, false) }).getElement().setAttribute("aria-label", txt(p.name));
    }
  }

  async function loadParkings() {
    let rows;
    try { rows = (await tinyvigoData.parkings()).filter((r) => r.lat); } catch (e) { return; } // WEB-05; sin feed, sin capa
    markers.park.forEach((m) => m.remove()); markers.park = [];
    for (const r of rows) {
      const age = (Date.now() - new Date(r.fechahora.replace(" ", "T"))) / 60000, stale = !(age <= 10);
      const free = Math.max(0, r.plazaslibres), cls = stale ? "stale" : free === 0 ? "full" : free < 30 ? "low" : "ok";
      const label = stale ? t("common.no_data") : free ? free : t("go.full");
      const gm = "https://www.google.com/maps/dir/?api=1&travelmode=driving&destination=" + r.lat + "," + r.lon;
      const html = "<strong>" + esc(r.nombre) + "</strong><br>" + (stale ? t("common.no_data") : free ? t(free === 1 ? "go.free_1" : "go.free_n", { n: free }) : t("go.full")) + " / " + r.totalplazas +
        "<br><small>" + t("common.updated", { when: r.fechahora.slice(11, 16) }) + '</small><br><a target="_blank" rel="noopener" href="' + gm + '">' + t("go.route_to") + "</a>";
      markers.park.push(marker('<div class="tv-park tv-park-' + cls + '"><b>P</b>' + label + "</div>", [r.lon, r.lat], { title: r.nombre, onClick: () => popup(r.lat, r.lon, html) }));
    }
  }

  function fit() {
    if (!lastBounds) return;
    map.fitBounds(lastBounds, { padding: pad(), pitch: 55, bearing: -15, duration: 900, maxZoom: 17.5 });
  }

  // rutas del paseo o de casa al centro (tv:route), con sus tramos coche / bus / a pie
  function drawRoute(d) {
    if (!map) { queue.push(() => drawRoute(d)); return; }
    markers.route.forEach((m) => m.remove()); markers.route = [];
    const legs = d.legs || (d.line ? [{ line: d.line, mode: d.mode === "driving" ? "car" : "tour" }] : []);
    const features = [], all = [];
    for (const leg of legs) {
      if (!leg.line || !leg.line.length) continue;
      const mode = STYLE[leg.mode] ? leg.mode : "tour";
      features.push({ type: "Feature", properties: { mode, w: STYLE[mode].width }, geometry: { type: "LineString", coordinates: leg.line } });
      all.push(...leg.line);
      const badge = (pos, cls, label) => markers.route.push(marker('<div class="tv-legpin ' + cls + '">' + label + "</div>", [pos[1], pos[0]]));
      if (leg.parking) badge(leg.parking, "is-park", "P");
      if (leg.board) badge(leg.board, "is-bus", window.LU ? LU.svg("bus", { size: 14 }) : "B");
      if (leg.alight) badge(leg.alight, "is-bus", window.LU ? LU.svg("bus", { size: 14 }) : "B");
    }
    map.getSource("route").setData({ type: "FeatureCollection", features });
    if (!all.length) { lastBounds = null; return; }
    if (d.start) markers.route.push(marker('<div class="tv-route-me"></div>', [d.start[1], d.start[0]]));
    (d.stops || []).forEach((s, i) => markers.route.push(marker('<div class="tv-stopnum">' + (i + 1) + "</div>", [s.p.lon, s.p.lat],
      { anchor: "bottom", title: (i + 1) + ". " + txt(s.p.name), onClick: () => (window.tinyvigoTour ? tinyvigoTour.startWalk(i) : P.select(s.p, false)) })));
    const b = new maplibregl.LngLatBounds();
    all.forEach((c) => b.extend(c));
    lastBounds = b;
    if (d.showCity) setCity(true);
    else if (document.body.classList.contains("is-city")) fit();
  }
  function clearRoute() {
    lastBounds = null;
    if (!map) return;
    markers.route.forEach((m) => m.remove()); markers.route = [];
    map.getSource("route").setData({ type: "FeatureCollection", features: [] });
  }

  function setCity(on) {
    document.body.classList.toggle("is-city", on);
    btn.innerHTML = (window.LU ? LU.svg(on ? "layers" : "map-pin", { size: 20 }) : "") + "<span>" + (on ? "Vigo 3D" : t("app.city_view")) + "</span>";
    if (on) load().then(() => { map.resize(); if (lastBounds) fit(); });
  }
  let focusPin = null;
  function focus(lat, lon, html, zoom = 17) {
    setCity(true);
    load().then(() => {
      if (focusPin) { focusPin.remove(); focusPin = null; }
      if (html) focusPin = marker('<div class="tv-focus-pin">' + (window.LU ? LU.svg("map-pin", { size: 34 }) : "") + "</div>", [lon, lat], { anchor: "bottom" });
      map.flyTo({ center: [lon, lat], zoom: Math.min(zoom + 0.3, 18.5), pitch: 58, bearing: -15, duration: 1400, essential: true });
      if (html) popup(lat, lon, html);
    });
  }
  function setWalked(latlngs, here) {
    if (!map) return; // only drawn on an open 3D view
    map.getSource("walked").setData({ type: "Feature", geometry: { type: "LineString", coordinates: latlngs.map(([la, lo]) => [lo, la]) } });
    if (!walkedMe) walkedMe = marker('<div class="tv-route-me is-live"></div>', [here[1], here[0]]);
    else walkedMe.setLngLat([here[1], here[0]]);
  }
  function clearWalked() {
    if (!map) return;
    map.getSource("walked").setData({ type: "FeatureCollection", features: [] });
    if (walkedMe) { walkedMe.remove(); walkedMe = null; }
  }

  // paradas de bus (solo a nivel de calle) y estaciones de tren, con sus próximas salidas
  function addTransit(args) {
    transitArgs = args;
    if (!map) return;
    const { stops, stations, stopHtml, stationHtml } = args;
    if (!map.getSource("bus-stops")) {
      map.addSource("bus-stops", { type: "geojson", data: { type: "FeatureCollection", features: stops.map(([id, name, lat, lon, detour]) => ({ type: "Feature", properties: { id, name, detour: !!detour }, geometry: { type: "Point", coordinates: [lon, lat] } })) } });
      map.addLayer({ id: "bus-stops", type: "circle", source: "bus-stops", minzoom: 16.5, paint: { "circle-radius": 5, "circle-color": ["case", ["get", "detour"], "#f4cd80", "#ffffff"], "circle-stroke-color": "#3d6a96", "circle-stroke-width": 1.5 } });
      map.on("click", "bus-stops", (e) => { const f = e.features[0], [lon, lat] = f.geometry.coordinates; popup(lat, lon, stopHtml(f.properties.id, f.properties.name)); });
      map.on("mouseenter", "bus-stops", () => (map.getCanvas().style.cursor = "pointer"));
      map.on("mouseleave", "bus-stops", () => (map.getCanvas().style.cursor = ""));
    }
    markers.stations.forEach((m) => m.remove());
    markers.stations = stations.map((st) => marker('<div class="tv-train">' + (window.LU ? LU.svg("train-front", { size: 16 }) : "T") + "</div>", [st.lon, st.lat], { title: st.name, onClick: () => popup(st.lat, st.lon, stationHtml(st.name)) }));
  }

  function init() {
    P = window.tinyvigoPoints; t = P.t; txt = P.txt;
    document.body.append(wrap, btn);
    btn.onclick = () => setCity(!document.body.classList.contains("is-city"));
    document.addEventListener("tv:lang", () => setCity(document.body.classList.contains("is-city")));
    document.addEventListener("tv:route", (e) => drawRoute(e.detail));
    document.addEventListener("tv:clear-route", clearRoute);
    document.addEventListener("tv:select", (e) => { if (map && document.body.classList.contains("is-city")) map.flyTo({ center: [e.detail.lon, e.detail.lat], zoom: Math.max(map.getZoom(), 16.5), duration: 1000 }); });
    setCity(false);
    window.tinyvigoCity = { get map() { return map; }, setCity, focus, popup, setWalked, clearWalked, addTransit, load, kind: "3d" };
  }
  if (window.tinyvigoPoints) init();
  else document.addEventListener("tv:ready", init, { once: true });
})();
