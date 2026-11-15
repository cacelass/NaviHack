// TinyVigo búsqueda (WEB-03): puntos de Navidad, eventos, estaciones y paradas, y calles desde el
// cuadro del panel. Sin tildes ni mayúsculas, perdona una errata por palabra, agrupa por tipo,
// teclado (↑ ↓ Enter Esc), recientes y, al elegir, vuela al sitio y abre su ficha.
(function () {
  const norm = (s) => (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9ñ ]/g, " ").replace(/\s+/g, " ").trim();
  const lu = (name, size = 16) => { const s = document.createElement("span"); s.innerHTML = window.LU ? LU.svg(name, { size }) : ""; return s.firstChild || s; };
  const el = (tag, cls, ...kids) => { const n = document.createElement(tag); if (cls) n.className = cls; n.append(...kids.filter((k) => k != null && k !== false)); return n; };

  // distancia de edición <= 1 (una letra de más, de menos o cambiada)
  function near1(a, b) {
    if (a === b) return true;
    if (Math.abs(a.length - b.length) > 1) return false;
    let i = 0, j = 0, edits = 0;
    while (i < a.length && j < b.length) {
      if (a[i] === b[j]) { i++; j++; continue; }
      if (++edits > 1) return false;
      if (a.length > b.length) i++; else if (b.length > a.length) j++; else { i++; j++; }
    }
    return edits + (a.length - i) + (b.length - j) <= 1;
  }
  // 0 = no casa; más alto = mejor. Cada palabra de la consulta debe casar con alguna del texto.
  function score(query, text) {
    const q = norm(query), t = norm(text);
    if (!q || !t) return 0;
    if (t === q) return 100;
    if (t.startsWith(q)) return 90;
    if (t.includes(q)) return 80;
    const words = t.split(" ");
    let total = 0;
    for (const w of q.split(" ")) {
      if (words.some((x) => x.startsWith(w))) total += 3;
      else if (w.length >= 4 && words.some((x) => near1(w, x.slice(0, Math.max(w.length, Math.min(x.length, w.length + 1)))) || near1(w, x))) total += 2;
      else return 0;
    }
    return 40 + total;
  }

  const GROUPS = [
    { kind: "point", icon: "tree-pine", label: "search.g_points" },
    { kind: "event", icon: "calendar-days", label: "search.g_events" },
    { kind: "station", icon: "train-front", label: "search.g_stations" },
    { kind: "street", icon: "map-pin", label: "search.g_streets" },
  ];

  function buildIndex(P, streets, transit, agenda) {
    const items = [];
    for (const p of P.points) items.push({ kind: "point", label: P.txt(p.name), alt: [p.name.es, p.name.gl, p.address].join(" "), sub: p.address || "", p, lat: p.lat, lon: p.lon });
    for (const e of agenda || []) items.push({ kind: "event", label: e.titulo, alt: e.direccion || "", sub: e.direccion || "", lat: e.where && e.where.lat, lon: e.where && e.where.lon, e });
    const st = { "Vigo Urzaiz": [42.234189, -8.713728], "Vigo-Guixar": [42.2392656, -8.7146089] };
    for (const s of (transit && transit.trains && transit.trains.stations) || []) items.push({ kind: "station", label: s.name, alt: "tren estacion renfe train " + s.name, sub: "Renfe", lat: (st[s.name] || [])[0], lon: (st[s.name] || [])[1] });
    for (const [, name, lat, lon] of (transit && transit.stops) || []) items.push({ kind: "station", label: name, alt: "bus parada vitrasa " + name, sub: "Vitrasa", lat, lon, bus: true });
    for (const [name, lat, lon] of streets || []) items.push({ kind: "street", label: name, alt: "", sub: "", lat, lon });
    items.forEach((it) => (it.key = norm(it.label + " " + it.alt)));
    return items;
  }

  function search(index, query, limit = 5) {
    const out = {};
    for (const it of index) {
      const s = Math.max(score(query, it.label), score(query, it.key) - 5);
      if (!s) continue;
      (out[it.kind] ||= []).push({ it, s: s - (it.bus ? 3 : 0) });
    }
    for (const k in out) out[k] = out[k].sort((a, b) => b.s - a.s || a.it.label.length - b.it.label.length).slice(0, limit).map((x) => x.it);
    return out;
  }

  function init() {
    const P = window.tinyvigoPoints, t = P.t;
    let index = null, results = {}, flat = [], active = -1, input = null, filter = "all";
    // HUD v5: filter chips on top of the dropdown; with no text it lists every place they allow
    const FILTERS = [["all", "points.filter_all", "layers"], ["open", "common.open_now", "circle-check"], ["light", "points.filter_lights", "lightbulb"], ["market", "points.filter_markets", "store"], ["attraction", "points.filter_attractions", "ferris-wheel"]];
    const passes = (p) => filter === "all" || (filter === "open" ? !!(P.status(p) || {}).open : p.type === filter);
    function chips() {
      const row = el("div", "tv-res-filters");
      row.setAttribute("role", "group");
      for (const [f, key, icon] of FILTERS) {
        const b = el("button", "tv-res-filter" + (f === filter ? " is-on" : ""), lu(icon, 16), t(key));
        b.type = "button"; b.setAttribute("aria-pressed", String(f === filter));
        b.onmousedown = (e) => { e.preventDefault(); filter = f; run(input.value); };
        row.append(b);
      }
      return row;
    }
    function pointRow(it) {
      const p = it.p, st = P.status(p), i = flat.length;
      flat.push(it);
      const thumb = p.photo ? Object.assign(el("img", "tv-res-thumb"), { src: p.photo, alt: "", loading: "lazy", decoding: "async", width: 44, height: 44 }) : el("span", "tv-res-thumb", lu("map-pin", 20));
      const b = el("button", "tv-res tv-res-point" + (i === active ? " is-active" : ""), thumb, el("span", "tv-name", it.label),
        st ? el("span", "tv-badge" + (st.open ? " is-open" : ""), st.open ? st.word : st.label) : null);
      b.setAttribute("role", "option");
      b.onmousedown = (e) => { e.preventDefault(); go(it); };
      return b;
    }
    const box = el("div", "tv-results"); box.setAttribute("role", "listbox");
    const RKEY = "tinyvigo.recent";
    const recent = () => { try { return JSON.parse(localStorage.getItem(RKEY) || "[]"); } catch (e) { return []; } };
    const remember = (q) => { try { localStorage.setItem(RKEY, JSON.stringify([q, ...recent().filter((x) => x !== q)].slice(0, 5))); } catch (e) {} };

    Promise.all([
      fetch("data/streets.json").then((r) => r.json()).catch(() => []),
      fetch("data/transit.json").then((r) => r.json()).catch(() => null),
      window.tinyvigoEvents ? window.tinyvigoEvents.load().catch(() => []) : [],
    ]).then(([streets, transit, agenda]) => { index = buildIndex(P, streets, transit, agenda); if (input && input.value) run(input.value); });

    function go(it) {
      remember(input.value.trim() || it.label);
      close();
      if (it.kind === "point") {
        if (!it.p.on_map && window.tinyvigoCity) window.tinyvigoCity.setCity(true);
        P.select(it.p);
        if (!it.p.on_map && window.tinyvigoCity) setTimeout(() => window.tinyvigoCity.map.flyTo([it.lat, it.lon], 17), 120);
        return;
      }
      if (it.lat == null || !window.tinyvigoCity) return;
      const { map, setCity } = window.tinyvigoCity;
      setCity(true);
      setTimeout(() => {
        map.flyTo([it.lat, it.lon], it.kind === "street" ? 17 : 18);
        L.popup({ maxWidth: 260 }).setLatLng([it.lat, it.lon]).setContent("<strong>" + it.label.replace(/</g, "&lt;") + "</strong>" + (it.sub ? "<br>" + it.sub.replace(/</g, "&lt;") : "")).openOn(map);
      }, 120);
    }

    function render(q) {
      box.replaceChildren(chips());
      flat = [];
      if (!q) {
        const rows = P.points.filter(passes).map((p) => pointRow({ kind: "point", label: P.txt(p.name), p, lat: p.lat, lon: p.lon }));
        box.append(...(rows.length ? rows : [el("p", "tv-note tv-res-empty", t("search.none", { q: "" }))]));
        return;
      }
      if (!index) { box.append(el("p", "tv-note tv-res-empty", t("state.loading") + "…")); return; }
      for (const g of GROUPS) {
        let list = results[g.kind];
        if (g.kind === "point" && list) list = list.filter((it) => passes(it.p));
        else if (filter !== "all") list = null; // a place filter leaves only places
        if (!list || !list.length) continue;
        box.append(el("p", "tv-res-head", lu(g.icon), t(g.label)));
        for (const it of list) {
          if (it.kind === "point") { box.append(pointRow(it)); continue; }
          const i = flat.length; flat.push(it);
          const b = el("button", "tv-res" + (i === active ? " is-active" : ""), el("span", "tv-name", it.label), it.sub ? el("span", "tv-badge", it.sub) : null);
          b.setAttribute("role", "option");
          b.onmousedown = (e) => { e.preventDefault(); go(it); };
          box.append(b);
        }
      }
      if (!flat.length) box.append(el("p", "tv-note tv-res-empty", t("search.none", { q })));
    }

    function run(q) { results = index ? search(index, q) : {}; active = -1; render(q.trim()); }
    function open(inp) { input = inp; inp.after(box); box.classList.add("is-open"); run(inp.value); }
    function close() { box.classList.remove("is-open"); active = -1; }

    // el panel se repinta (idioma, filtros): se engancha por delegación
    document.addEventListener("focusin", (e) => { if (e.target.classList && e.target.classList.contains("tv-search")) open(e.target); });
    document.addEventListener("input", (e) => { if (e.target === input) run(input.value); });
    document.addEventListener("focusout", (e) => { if (e.target === input) setTimeout(close, 150); });
    document.addEventListener("keydown", (e) => {
      if (e.target !== input || !box.classList.contains("is-open")) return;
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        if (!flat.length) return;
        active = (active + (e.key === "ArrowDown" ? 1 : -1) + flat.length) % flat.length;
        render(input.value.trim());
      } else if (e.key === "Enter" && flat.length) { e.preventDefault(); go(flat[Math.max(active, 0)]); input.blur(); }
      else if (e.key === "Escape") { close(); input.blur(); }
    });
    window.tinyvigoSearch = { search: (q) => search(index || [], q), ready: () => !!index, norm };
  }

  if (window.tinyvigoPoints) init();
  else document.addEventListener("tv:ready", init, { once: true });
})();
