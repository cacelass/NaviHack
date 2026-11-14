// TinyVigo «Hoy en Vigo»: agenda del Concello en vivo (agenda-hoy.json, CORS abierto), con los
// eventos del día primero y los permanentes agrupados. Se sitúan en el mapa por la instalación
// (mapa aprendido de D-04: data/venues.json -> centros culturales) o por la dirección escrita.
(function () {
  const AGENDA = "https://datos.vigo.org/data/axenda/agenda-hoy.json";
  const CENTROS = "https://datos.vigo.org/data/cultura/centros.json";
  const norm = (s) => (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9 ]/g, " ").replace(/\s+/g, " ").trim();
  const lu = (name, size = 20) => { const s = document.createElement("span"); s.innerHTML = window.LU ? LU.svg(name, { size }) : ""; return s.firstChild || s; };
  const el = (tag, cls, ...kids) => { const n = document.createElement(tag); if (cls) n.className = cls; n.append(...kids.filter((k) => k != null && k !== false)); return n; };

  async function load(points) {
    const [agenda, centros, ids] = await Promise.all([
      fetch(AGENDA).then((r) => r.json()),
      fetch(CENTROS).then((r) => r.json()).catch(() => []),
      fetch("data/venues.json").then((r) => r.json()).catch(() => ({})),
    ]);
    const byId = new Map((Array.isArray(centros) ? centros : []).map((c) => ["cultura-" + c.id, c]));
    const places = (Array.isArray(centros) ? centros : []).map((c) => ({ key: norm(c.nombre), lat: c.lat, lon: c.lon, name: c.nombre }))
      .concat(points.map((p) => ({ key: norm(p.address || ""), lat: p.lat, lon: p.lon, name: p.address })))
      .concat(points.map((p) => ({ key: norm(p.name.es), lat: p.lat, lon: p.lon, name: p.name.es })))
      .filter((p) => p.key.length > 5 && p.lat);
    const locate = (e) => {
      const c = e.instalacion && byId.get(ids[String(e.instalacion)]);
      if (c) return { lat: c.lat, lon: c.lon, name: c.nombre };
      const d = norm(e.direccion);
      if (d.length < 5) return null;
      const hit = places.find((p) => d.includes(p.key) || p.key.includes(d));
      return hit ? { lat: hit.lat, lon: hit.lon, name: e.direccion } : null;
    };
    const today = new Date().toISOString().slice(0, 10);
    return agenda.map((e) => ({ ...e, where: locate(e), today: !e.permanente && e.fecha_inicio <= today && today <= (e.fecha_fin || e.fecha_inicio) }));
  }

  function init() {
    const P = window.tinyvigoPoints, t = P.t;
    const btn = el("button", "tv-today-open");
    const box = el("section", "tv-tour tv-events");
    document.body.append(btn, box);
    let events = null, error = false, loading = false;

    function show(e) {
      if (!e.where || !window.tinyvigoCity) return;
      const { map, setCity } = window.tinyvigoCity;
      setCity(true);
      setTimeout(() => {
        map.flyTo([e.where.lat, e.where.lon], 17);
        L.popup({ maxWidth: 260 }).setLatLng([e.where.lat, e.where.lon])
          .setContent("<strong>" + e.titulo.replace(/</g, "&lt;") + "</strong><br>" + (e.where.name || "").replace(/</g, "&lt;")).openOn(map);
      }, 120);
      if (window.matchMedia("(max-width: 700px)").matches) { box.classList.remove("is-open"); render(); }
    }

    function row(e) {
      const place = e.direccion || (e.where && e.where.name) || "";
      const go = e.where ? el("button", "tv-btn tv-btn-quiet tv-ev-go", lu("map-pin", 16), t("events.on_map")) : null;
      if (go) go.onclick = () => show(e);
      return el("li", "tv-ev",
        el("div", "tv-ev-main",
          el("p", "tv-ev-title", e.titulo),
          place ? el("p", "tv-ev-place", lu("map-pin", 14), place) : null,
          el("p", "tv-badge", e.permanente ? t("events.permanent") : t("common.time_tbc"))),
        go);
    }

    async function render() {
      btn.replaceChildren(lu("calendar-days"), t("events.open"));
      box.replaceChildren();
      if (!box.classList.contains("is-open")) return;
      const close = el("button", "tv-close", lu("x")); close.setAttribute("aria-label", t("common.close"));
      close.onclick = () => { box.classList.remove("is-open"); render(); };
      box.append(close, el("h2", null, t("events.title")));
      if (!events && !error) {
        box.append(el("p", "tv-note", t("state.loading") + "…"));
        if (!loading) {
          loading = true;
          try { events = await load(P.points); } catch (e) { error = true; }
          loading = false; render();
        }
        return;
      }
      if (error) {
        const retry = el("button", "tv-btn", lu("rotate-ccw", 16), t("common.retry"));
        retry.onclick = () => { error = false; render(); };
        box.append(el("p", null, t("state.error_title")), retry);
        return;
      }
      const dated = events.filter((e) => e.today), perm = events.filter((e) => e.permanente);
      box.append(dated.length
        ? el("ul", "tv-evlist", ...dated.map(row))
        : el("div", null, el("h3", null, t("state.no_events_title")), el("p", "tv-note", t("state.no_events_body"))));
      if (perm.length) box.append(el("details", "tv-later", el("summary", null, t("events.permanent") + " · " + perm.length), el("ul", "tv-evlist", ...perm.map(row))));
      const src = el("a", null, t("common.see_source")); src.href = "https://datos.vigo.org/"; src.target = "_blank"; src.rel = "noopener";
      box.append(el("p", "tv-note", t("events.source_note") + " · ", src));
    }

    btn.onclick = () => {
      const open = !box.classList.contains("is-open");
      document.querySelectorAll(".tv-tour.is-open").forEach((b) => b.classList.remove("is-open"));
      box.classList.toggle("is-open", open); render();
    };
    document.addEventListener("tv:lang", render);
    render();
    window.tinyvigoEvents = { open: () => { box.classList.add("is-open"); render(); }, load: () => load(P.points) };
  }

  if (window.tinyvigoPoints) init();
  else document.addEventListener("tv:ready", init, { once: true });
})();
