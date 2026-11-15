// TinyVigo «arte pixel off» (MAP-01): enseña la ortofoto real (PNOA, IGN) de la misma zona que
// se está viendo, para orientarse. El mapa isométrico queda debajo; esto es una capa Leaflet
// a pantalla completa con la misma vista. El interruptor vive en el panel de capas.
(function () {
  const PNOA = "https://www.ign.es/wmts/pnoa-ma?request=GetTile&service=WMTS&version=1.0.0"
    + "&layer=OI.OrthoimageCoverage&style=default&tilematrixset=GoogleMapsCompatible"
    + "&tilematrix={z}&tilerow={y}&tilecol={x}&format=image/jpeg";

  const lu = (name, size = 20) => { const s = document.createElement("span"); s.innerHTML = window.LU ? LU.svg(name, { size }) : ""; return s.firstChild || s; };
  const el = (tag, cls, ...kids) => { const n = document.createElement(tag); if (cls) n.className = cls; n.append(...kids.filter((k) => k != null && k !== false)); return n; };
  const t = (k, fallback) => (window.tinyvigoPoints ? window.tinyvigoPoints.t(k) : fallback);

  let wrap = null, map = null, on = false;

  function bounds() {
    const T = window.tinyvigoTour;
    const viewer = window.tinyvigo && window.tinyvigo.viewer;
    if (!T || !viewer) return null;
    const size = viewer.viewport.getContainerSize();
    return [[0, 0], [size.x, 0], [0, size.y], [size.x, size.y]].map(([x, y]) => {
      const p = viewer.viewport.pointFromPixel(new OpenSeadragon.Point(x, y), true);
      return T.unproject(p.x * 3072, p.y * 3072);
    });
  }

  function show() {
    if (!map) {
      wrap = el("div", "tv-sat");
      const mapDiv = el("div", "tv-sat-map");
      const close = el("button", "tv-sat-close");
      close.type = "button";
      close.setAttribute("aria-label", t("sat.back", "Volver al mapa pixel"));
      close.append(lu("x", 20));
      close.onclick = () => set(false);
      wrap.append(mapDiv, close);
      document.body.append(wrap);
      map = L.map(mapDiv, { zoomControl: false, attributionControl: true, keyboard: false });
      L.control.zoom({ position: "bottomright" }).addTo(map);
      L.tileLayer(PNOA, {
        maxZoom: 19,
        attribution: 'Ortofoto: <a href="https://www.ign.es/" target="_blank" rel="noopener">PNOA © IGN</a> · CC BY 4.0',
      }).addTo(map);
    }
    wrap.style.display = "block";
    const b = bounds();
    if (b) {
      const lats = b.map((p) => p[0]), lons = b.map((p) => p[1]);
      map.fitBounds([[Math.min(...lats), Math.min(...lons)], [Math.max(...lats), Math.max(...lons)]], { animate: false });
    } else {
      map.setView([42.238072, -8.725813], 16);
    }
    setTimeout(() => map.invalidateSize(), 30);
  }

  function set(v) {
    // LAYERS-02: with the satellite city view (city3d.js) the «real photo» is that view, at the same
    // place and with every layer on it; this bare orthophoto stays only as its fallback
    const C = window.tinyvigoCity;
    if (C && C.show) {
      if (v) C.show(bounds()); else C.setCity(false);
      return;
    }
    on = !!v;
    document.body.classList.toggle("is-sat", on);
    if (on) {
      // el panel de capas se cierra para no tapar la ortofoto; el botón sigue arriba
      document.querySelectorAll(".tv-layers-pop.is-open").forEach((p) => p.classList.remove("is-open"));
      show();
    } else if (wrap) wrap.style.display = "none";
    document.dispatchEvent(new CustomEvent("tv:sat", { detail: { on } }));
  }

  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && on) set(false); });
  window.tinyvigoSat = { set, isOn: () => (window.tinyvigoCity && window.tinyvigoCity.show ? document.body.classList.contains("is-city") : on) };
})();
