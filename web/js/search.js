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
    let index = null, results = {}, flat = [], active = -1, input = null, filter = "all", addresses = [], addrState = "";
    // HUD v5: filter chips on top of the dropdown; with no text it lists every place they allow
    const FILTERS = [["all", "points.filter_all", "layers"], ["open", "common.open_now", "circle-check"], ["light", "points.filter_lights", "lightbulb"], ["market", "points.filter_markets", "store"], ["attraction", "points.filter_attractions", "ferris-wheel"]];
    const passes = (p) => filter === "all" || (filter === "open" ? !!(P.status(p) || {}).open : p.type === filter);
    function chips() {
      const row = el("div", "tv-res-filters");
      row.setAttribute("role", "group");
      row.setAttribute("aria-label", t("search.filters"));
      for (const [f, key, icon] of FILTERS) {
        const b = el("button", "tv-res-filter" + (f === filter ? " is-on" : ""), lu(icon, 16), t(key));
        b.type = "button"; b.setAttribute("aria-pressed", String(f === filter));
        b.onmousedown = (e) => { e.preventDefault(); filter = f; run(input.value, true); };
        row.append(b);
      }
      return window.tvScrollHint ? window.tvScrollHint(row) : row;
    }
    // SEARCH-02: one card per result. Name on top (up to two lines, never cut mid-word), then what it
    // is and its state on a second line; the picture or the kind's icon on the left.
    function card(it, media, name, meta) {
      const i = flat.length;
      flat.push(it);
      const b = el("button", "tv-res" + (i === active ? " is-active" : ""), media, el("span", "tv-res-text", el("span", "tv-name", name), meta ? el("span", "tv-res-meta", ...meta) : null));
      b.type = "button";
      b.setAttribute("role", "option");
      b.onmousedown = (e) => { e.preventDefault(); go(it); };
      return b;
    }
    const iconBox = (name) => el("span", "tv-res-thumb tv-res-ico", lu(name, 20));
    function pointRow(it) {
      const p = it.p, st = P.status(p);
      const thumb = p.photo ? Object.assign(el("img", "tv-res-thumb"), { src: p.photo, alt: "", loading: "lazy", decoding: "async", width: 56, height: 56 }) : iconBox(P.typeIcon(p.type));
      const kind = el("span", "tv-res-kind", lu(P.typeIcon(p.type), 14), t(P.typeKey(p.type) || "points.filter_all"));
      const state = st ? el("span", "tv-res-state" + (st.open ? " is-open" : ""), lu(st.open ? "circle-check" : "clock", 14), st.open ? st.word : st.label) : null;
      return card(it, thumb, it.label, [kind, state]);
    }
    const KIND_ICON = { event: "calendar-days", station: "train-front", street: "map-pin", address: "map-pin" };
    function otherRow(it) {
      const icon = it.kind === "station" && it.bus ? "bus" : KIND_ICON[it.kind];
      return card(it, iconBox(icon), it.label, it.sub ? [el("span", "tv-res-sub", it.sub)] : null);
    }
    const box = el("div", "tv-results"); box.setAttribute("role", "listbox");
    box.setAttribute("aria-label", t("points.search"));
    const RKEY = "tinyvigo.recent";
    const recent = () => { try { return JSON.parse(localStorage.getItem(RKEY) || "[]"); } catch (e) { return []; } };
    const remember = (q) => { try { localStorage.setItem(RKEY, JSON.stringify([q, ...recent().filter((x) => x !== q)].slice(0, 5))); } catch (e) {} };

    Promise.all([
      fetch("data/streets.json").then((r) => r.json()).catch(() => []),
      fetch("data/transit.json").then((r) => r.json()).catch(() => null),
      window.tinyvigoEvents ? window.tinyvigoEvents.load().catch(() => []) : [],
    ]).then(([streets, transit, agenda]) => { index = buildIndex(P, streets, transit, agenda); if (input && input.value) run(input.value); });

    // anything OpenStreetMap knows (other streets with their number, other towns), after a pause
    const lookUp = window.tinyvigoGeocode ? window.tinyvigoGeocode.debounced((r, q) => {
      if (!input || input.value.trim() !== q.trim()) return;
      addrState = r === null ? "error" : "";
      // the centre's own streets are already listed: only what they do not cover
      const known = new Set((results.street || []).map((x) => norm(x.label)));
      addresses = (r || []).filter((a) => a.house || !known.has(norm(a.label)));
      render(input.value.trim());
    }) : null;

    function go(it) {
      remember(input.value.trim() || it.label);
      close();
      const C = window.tinyvigoCity, esc = (s) => String(s || "").replace(/</g, "&lt;");
      if (it.kind === "point") {
        P.select(it.p);
        if (!it.p.on_map && C) C.focus(it.lat, it.lon, null, 17);
        return;
      }
      if (it.lat == null) return;
      if ((it.kind === "address" || it.kind === "street") && window.tinyvigoGeocode) { window.tinyvigoGeocode.show(it); return; }
      if (C) C.focus(it.lat, it.lon, "<strong>" + esc(it.label) + "</strong>" + (it.sub ? "<br>" + esc(it.sub) : ""), 18);
    }

    function render(q) {
      const top = box.scrollTop;
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
        for (const it of list) box.append(it.kind === "point" ? pointRow(it) : otherRow(it));
      }
      if (filter === "all" && q.length >= 3) {
        if (addresses.length) {
          box.append(el("p", "tv-res-head", lu("map-pin"), t("search.g_addresses")));
          for (const it of addresses) box.append(otherRow(it));
          box.append(el("p", "tv-res-credit", window.tinyvigoGeocode.credit));
        } else if (addrState === "error") box.append(el("p", "tv-note tv-res-empty", t("search.addr_error")));
      }
      if (!flat.length && addrState !== "error") box.append(el("p", "tv-note tv-res-empty", t(q.length >= 3 && lookUp ? "search.looking" : "search.none", { q })));
      box.scrollTop = top;
    }

    function run(q, keepAddresses) {
      results = index ? search(index, q) : {}; active = -1;
      if (!keepAddresses) { addresses = []; addrState = ""; if (lookUp && q.trim().length >= 3) lookUp(q.trim()); }
      render(q.trim());
    }
    function open(inp) { input = inp; inp.after(box); box.classList.add("is-open"); document.body.classList.add("is-searching"); run(inp.value); }
    function close() { box.classList.remove("is-open"); document.body.classList.remove("is-searching"); active = -1; }

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
        const a = box.querySelector(".tv-res.is-active"); if (a) a.scrollIntoView({ block: "nearest" });
      } else if (e.key === "Enter" && flat.length) { e.preventDefault(); go(flat[Math.max(active, 0)]); input.blur(); }
      else if (e.key === "Escape") { close(); input.blur(); }
    });
    window.tinyvigoSearch = { search: (q) => search(index || [], q), ready: () => !!index, norm };
  }

  if (window.tinyvigoPoints) init();
  else document.addEventListener("tv:ready", init, { once: true });
})();
