// NaviVigo: direcciones de cualquier sitio (SEARCH-02). Las calles del centro están en
// data/streets.json; lo demás (otra calle de Vigo con su número, Cangas, Ourense, Porto…) se busca en
// Photon, el geocodificador de OpenStreetMap hecho para buscar mientras se escribe (Nominatim lo
// prohíbe en su política de uso). Con preferencia por Vigo, sin clave, con su crédito (© OSM, ODbL).
// Lo usan el buscador de arriba (search.js) y «Salgo desde una calle» del paseo (tour.js).
(function () {
  const PHOTON = "https://photon.komoot.io/api/";
  const VIGO = [42.2376, -8.7247];
  const cache = new Map();
  let ctrl = null;

  const VIGO_BOX = "-8.86,42.12,-8.58,42.31"; // Vigo y alrededores: lo de aquí va primero

  // «Avenida da Gran Vía 100 · Vigo», «Hospital Álvaro Cunqueiro · Estrada de Clara Campoamor, Vigo»
  function label(pr) {
    const street = pr.street ? pr.street + (pr.housenumber ? " " + pr.housenumber : "") : null;
    const poi = pr.name && !/^[\d\s,]+$/.test(pr.name) && pr.type !== "house" && pr.osm_key !== "highway";
    const main = poi ? pr.name : street || pr.name || "";
    const place = pr.city || pr.town || pr.village || pr.district || pr.county || pr.state || "";
    const sub = [poi && street ? street : null, place && place !== main ? place : null,
      pr.country && !/^(España|Spain)$/.test(pr.country) ? pr.country : null].filter(Boolean).join(", ");
    return { label: main, sub };
  }

  async function query(params, signal) {
    const res = await fetch(PHOTON + "?" + params + "&lang=default", { signal });
    if (!res.ok) throw new Error("photon " + res.status);
    return (await res.json()).features || [];
  }

  async function search(q, { limit = 6 } = {}) {
    q = (q || "").trim();
    if (q.length < 3) return [];
    const key = q.toLowerCase();
    if (cache.has(key)) return cache.get(key);
    if (ctrl) ctrl.abort();
    ctrl = new AbortController();
    const enc = encodeURIComponent(q);
    const [near, far] = await Promise.all([
      query("q=" + enc + "&bbox=" + VIGO_BOX + "&limit=" + limit, ctrl.signal),
      query("q=" + enc + "&lat=" + VIGO[0] + "&lon=" + VIGO[1] + "&zoom=12&location_bias_scale=0.6&limit=" + limit, ctrl.signal).catch(() => []),
    ]);
    const seen = new Set();
    const out = [];
    // Vigo first; the rest of the world only when Vigo has (almost) nothing: «Gran Vía 100» is the
    // one here, not Barcelona's
    // ...unless the query names another place («gran via madrid»): then that place goes first
    const fold = (x) => String(x || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
    const words = fold(q).split(/[\s,]+/).filter((w) => w.length >= 4 && w !== "vigo");
    const named = far.filter((f) => { const pr = f.properties || {}; const where = fold([pr.city, pr.town, pr.village, pr.county, pr.state, pr.country].join(" ")); return words.some((w) => where.includes(w)) && !where.includes("vigo"); });
    const pool = named.length ? named.concat(near) : near.length >= 2 ? near : near.concat(far);
    for (const f of pool) {
      const [lon, lat] = f.geometry.coordinates, pr = f.properties || {};
      const { label: l, sub } = label(pr);
      const id = (l + "|" + sub).toLowerCase();
      if (!l || seen.has(id)) continue;
      seen.add(id);
      out.push({ kind: "address", label: l, sub, lat, lon, house: !!pr.housenumber });
      if (out.length >= limit) break;
    }
    cache.set(key, out);
    return out;
  }

  // espera a que se deje de escribir (250 ms); solo responde la última búsqueda.
  // cb(results, q): results = [] sin nada, null si no se pudo buscar (sin red, servicio caído)
  function debounced(cb, ms = 250) {
    let timer = 0, seq = 0;
    return (q) => {
      clearTimeout(timer);
      const mine = ++seq;
      timer = setTimeout(async () => {
        let r;
        try { r = await search(q); } catch (e) { if (e.name === "AbortError") return; r = null; }
        if (mine === seq) cb(r, q);
      }, ms);
    };
  }

  // ¿Cae dentro del mapa pixel? (con un margen: en el borde no se ve bien)
  function onPixel(lat, lon) {
    const G = window.tinyvigoGeo, m = window.tinyvigo && window.tinyvigo.manifest;
    if (!G || !m) return null;
    const [x, y] = G.project(lat, lon);
    return x > 60 && y > 60 && x < m.width - 60 && y < m.height - 60 ? [x, y] : null;
  }
  const esc = (s) => String(s || "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

  // Lleva a la dirección y la marca: en el dibujo si está dentro (y no estás en la vista ciudad),
  // si no, en el mapa real (vista ciudad), con su nombre en un globo.
  let pin = null;
  function show(it) {
    const viewer = window.tinyvigo && window.tinyvigo.viewer;
    const px = onPixel(it.lat, it.lon);
    if (pin && viewer) { viewer.removeOverlay(pin); pin = null; }
    if (px && viewer && !document.body.classList.contains("is-city")) {
      pin = document.createElement("div");
      pin.className = "tv-addr-pin";
      pin.setAttribute("role", "status");
      pin.innerHTML = '<span class="tv-addr-label"><strong>' + esc(it.label) + "</strong>" + (it.sub ? "<small>" + esc(it.sub) + "</small>" : "") + "</span>" + (window.LU ? LU.svg("map-pin", { size: 28 }) : "");
      viewer.addOverlay({ element: pin, location: new OpenSeadragon.Point(px[0] / 3072, px[1] / 3072), placement: OpenSeadragon.Placement.BOTTOM });
      const vp = viewer.viewport;
      vp.zoomTo(Math.max(vp.getZoom(), vp.getHomeZoom() * (it.house ? 4 : 3)));
      vp.panTo(new OpenSeadragon.Point(px[0] / 3072, px[1] / 3072));
      vp.applyConstraints();
      return "pixel";
    }
    const C = window.tinyvigoCity;
    if (!C) return null;
    C.focus(it.lat, it.lon, "<strong>" + esc(it.label) + "</strong>" + (it.sub ? "<br>" + esc(it.sub) : ""), it.house ? 18 : 17);
    return "city";
  }

  window.tinyvigoGeocode = { search, debounced, show, onPixel, credit: "© OpenStreetMap (Photon)" };
})();
