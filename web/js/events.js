// TinyVigo «Hoy en Vigo»: agenda del Concello en vivo (agenda-hoy.json, CORS abierto), con los
// eventos del día primero y los permanentes agrupados. Se sitúan en el mapa por la instalación
// (mapa aprendido de D-04: data/venues.json -> centros culturales) o por la dirección escrita.
(function () {
      const norm = (s) => (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9 ]/g, " ").replace(/\s+/g, " ").trim();
  const lu = (name, size = 20) => { const s = document.createElement("span"); s.innerHTML = window.LU ? LU.svg(name, { size }) : ""; return s.firstChild || s; };
  const el = (tag, cls, ...kids) => { const n = document.createElement(tag); if (cls) n.className = cls; n.append(...kids.filter((k) => k != null && k !== false)); return n; };

  async function load(points) {
    const [agenda, centros, ids] = await Promise.all([
      tinyvigoData.agenda(), // WEB-05: fichero propio (web/data/live), no la API del Concello
      tinyvigoData.centros().catch(() => []),
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
    // the Christmas point an event is about, for its photo on the agenda row: named in the title, or
    // the Árbol for the lights switch-on. The address alone is not enough: several points share a street.
    const tree = points.find((p) => p.id === "concello-2552");
    const pointOf = (e) => {
      const ti = norm(e.titulo);
      return points.find((p) => norm(p.name.es).length > 5 && ti.includes(norm(p.name.es)))
        || (/encend|acend|luces|luz/.test(ti) ? tree : null) || null;
    };
    const today = new Date().toISOString().slice(0, 10);
    return agenda.map((e) => ({ ...e, where: locate(e), point: pointOf(e), today: !e.permanente && e.fecha_inicio <= today && today <= (e.fecha_fin || e.fecha_inicio) }));
  }

  function init() {
    const P = window.tinyvigoPoints, t = P.t, txt = P.txt;
    const btn = el("button", "tv-today-open");
    const box = el("section", "tv-tour tv-events");
    const chip = document.getElementById("dock-hoy");
    const chipLabel = document.getElementById("tv-event-label");
    const chipPrefix = document.getElementById("tv-event-prefix");
    const compactChip = matchMedia("(max-width: 700px)");
    box.id = "tv-events"; box.setAttribute("role", "dialog"); box.setAttribute("aria-labelledby", "tv-events-title"); box.setAttribute("aria-hidden", "true");
    btn.setAttribute("aria-controls", "tv-events"); btn.setAttribute("aria-haspopup", "dialog");
    if (chip) chip.setAttribute("aria-controls", "tv-events");
    document.body.append(btn, box);
    let events = null, error = false, loading = false, dayOffset = 0, opener = null;
    const closeBox = (restoreFocus = true) => {
      const wasOpen = box.classList.contains("is-open");
      box.classList.remove("is-open");
      render();
      if (wasOpen && restoreFocus && opener && document.body.contains(opener)) setTimeout(() => opener.focus(), 0);
    };
    const openBox = () => {
      const active = document.activeElement;
      opener = active && active !== document.body && active !== document.documentElement ? active : (chip || btn);
      box.classList.add("is-open");
      render();
      setTimeout(() => { const h = document.getElementById("tv-events-title"); if (h) h.focus({ preventScroll: true }); }, 30);
    };

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
        e.point && e.point.photo ? Object.assign(el("img", "tv-thumb"), { src: e.point.photo, alt: "", width: 84, height: 56, loading: "lazy", decoding: "async" }) : el("span", "tv-thumb", lu(/belen|bel[eé]n|nacimiento/i.test(e.titulo) ? "star" : /disney|desfile|parade|cabalgata/i.test(e.titulo) ? "ticket" : "calendar-days")),
        el("div", "tv-ev-main",
          el("p", "tv-ev-title", e.titulo),
          place ? el("p", "tv-ev-place", lu("map-pin", 14), place) : null,
          el("p", "tv-badge", e.permanente ? t("events.permanent") : t("common.time_tbc"))),
        go);
    }

    const XMAS = /nadal|navidad|navide|luces|luzes|bel[eé]n|papa noel|pap[aá] noel|reyes|reis|cabalgata|disney|mercado de navidad|c[ií]es market|[aá]rbol|noria|pista de hielo|patinaxe|nadal bus|cartero real|turr[oó]n|villancico|panxoliña/i;
    const DAYS = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"];
    const iso = (d) => d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
    const hm = (d) => String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0");
    const timeIn = (label) => ((label || "").match(/(\d{1,2}:\d{2})/) || [])[1];
    const locale = () => P.lang() === "en" ? "en-GB" : P.lang() === "gl" ? "gl-ES" : "es-ES";
    const selectedDate = () => { const d = new Date(); if (dayOffset) d.setHours(12, 0, 0, 0); d.setDate(d.getDate() + dayOffset); return d; };

    function renderChip() {
      if (!chip || !chipLabel) return;
      const now = new Date();
      const lights = P.points.filter((p) => p.type === "light" && p.programme);
      const tree = P.points.find((p) => p.id === "concello-2552") || lights[0];
      const st = tree ? P.status(tree, now) : null;
      let full = "", short = "";
      if (st && st.open) {
        full = t("common.lit_now");
        short = t("common.lit_now");
      } else if (st) {
        const time = timeIn(st.label);
        if (time) {
          const [h, m] = time.split(":").map(Number);
          const target = new Date(now); target.setHours(h, m, 0, 0);
          if (target <= now) target.setDate(target.getDate() + 1);
          const minutes = Math.max(1, Math.ceil((target - now) / 60000));
          let when;
          if (minutes < 60) when = t("transport.in_min", { min: minutes });
          else {
            const hours = Math.floor(minutes / 60), rest = minutes % 60;
            when = rest ? t("events.in_hours_minutes", { h: hours, min: rest }) : t("events.in_hours", { h: hours });
          }
          full = t("events.chip_countdown", { when });
          short = time;
        }
      }
      if (chipPrefix) chipPrefix.textContent = full ? t("events.open") + " ·" : t("events.open");
      chipLabel.textContent = compactChip.matches ? short : full;
      const accessible = full ? t("events.open") + " · " + full : t("events.open");
      chip.setAttribute("aria-label", accessible);
      chip.title = accessible;
    }
    function classes(day, holidays) {
      const c = new Set([DAYS[day.getDay()]]), next = new Date(day); next.setDate(day.getDate() + 1);
      if ((holidays || []).includes(iso(day))) c.add("holiday");
      if ((holidays || []).includes(iso(next))) c.add("eve");
      return c;
    }
    // Build the selected day from the same schedules and live agenda used by today.
    function christmasToday(agenda, day = new Date()) {
      const actualNow = new Date(), today = iso(day), isToday = today === iso(actualNow);
      const scheduleAt = new Date(day);
      if (!isToday) scheduleAt.setHours(12, 0, 0, 0);
      const timeline = [], openNow = [], soon = [];
      const lights = P.points.filter((p) => p.type === "light" && p.programme);
      if (lights.length) {
        const tree = P.points.find((p) => p.id === "concello-2552") || lights[0];
        const st = P.status(tree, scheduleAt);
        const on = st && st.open ? null : timeIn(st && st.label);
        const off = st && st.open ? timeIn(st.label) : null;
        if (on || off) timeline.push({ time: on || hm(scheduleAt), title: on ? t("xmas.lights_on") : t("xmas.lights_lit"), sub: t("xmas.lights_sub", { n: lights.length }) + (off ? " · " + t("common.closes_at", { time: off }) : ""), p: tree });
      }
      for (const p of P.points) {
        const e = p.programme;
        if (!e) continue;
        const st = P.status(p, scheduleAt);
        for (const sh of e.shows || []) {
          if (st === null || (!st.open && !timeIn(st.label))) continue;
          for (const tm of sh.times) timeline.push({ time: tm, title: sh.label.charAt(0).toUpperCase() + sh.label.slice(1) + " · " + sh.minutes + " min", sub: txt(p.name), p });
        }
        for (const dep of e.departures || []) {
          if (dep.from <= today && today <= dep.to && dep.days.some((d) => classes(day, e.holidays).has(d))) dep.times.forEach((tm) => timeline.push({ time: tm, title: txt(p.name), sub: t("xmas.departure"), p }));
          else if (dep.from > today && !soon.some((x) => x.p === p)) soon.push({ p, date: dep.from });
        }
        if (isToday && st && st.open && ["attraction", "market", "santa_kings"].includes(p.type)) openNow.push({ p, label: st.label });
      }
      const nowHM = hm(actualNow);
      timeline.sort((a, b) => a.time.localeCompare(b.time));
      timeline.forEach((x) => (x.past = isToday && x.time < nowHM && !/^0[0-5]/.test(x.time)));
      const agendaX = (agenda || []).filter((e) => !e.permanente && e.fecha_inicio <= today && today <= (e.fecha_fin || e.fecha_inicio) && XMAS.test(e.titulo + " " + (e.direccion || "")));
      return { timeline, openNow, soon: soon.sort((a, b) => a.date.localeCompare(b.date)), agendaX };
    }
    const pick = (p) => { P.select(p); if (window.matchMedia("(max-width: 700px)").matches) { box.classList.remove("is-open"); render(); } };
    const dateFmt = (d) => new Date(d + "T12:00").toLocaleDateString(locale(), { day: "numeric", month: "long" });
    const thumb = (p) => (p.photo ? Object.assign(el("img", "tv-thumb"), { src: p.photo, alt: "", width: 84, height: 56, loading: "lazy", decoding: "async" }) : null);

    function dayNavigator() {
      const d = selectedDate();
      const weekday = d.toLocaleDateString(locale(), { weekday: "long" });
      const big = dayOffset === 0 ? t("common.today") : dayOffset === 1 ? t("events.tomorrow") : weekday.charAt(0).toUpperCase() + weekday.slice(1);
      const small = d.toLocaleDateString(locale(), { day: "numeric", month: "long" });
      const prev = el("button", "tv-day-prev", lu("chevron-right"));
      prev.id = "tv-day-prev"; prev.type = "button"; prev.disabled = dayOffset === 0; prev.setAttribute("aria-label", t("events.previous_day"));
      const next = el("button", "tv-day-next", lu("chevron-right"));
      next.id = "tv-day-next"; next.type = "button"; next.disabled = dayOffset >= 6; next.setAttribute("aria-label", t("events.next_day"));
      const move = (delta, id) => {
        dayOffset = Math.max(0, Math.min(6, dayOffset + delta));
        render();
        const target = document.getElementById(id); if (target) target.focus();
      };
      prev.onclick = () => move(-1, prev.id); next.onclick = () => move(1, next.id);
      const title = el("div", "tv-day-label", Object.assign(el("strong"), { id: "tv-day-title", textContent: big }), Object.assign(el("span"), { id: "tv-day-date", textContent: small }));
      return el("div", "tv-daynav", prev, title, next);
    }

    // tiempo (D-10): Open-Meteo en vivo para el centro, cada 10 min; si falla no se enseña nada
    let wx = null, wxAt = 0, wxLoading = false;
    function loadWx() {
      if (wxLoading || (wx && Date.now() - wxAt < 600000)) return;
      wxLoading = true;
      tinyvigoData.weather()
        .then((d) => { wx = d; wxAt = Date.now(); }).catch(() => {}).finally(() => { wxLoading = false; render(); });
    }
    const wxKind = (c) => (c === 0 ? "clear" : c <= 3 ? "cloudy" : c <= 48 ? "fog" : c <= 67 || (c >= 80 && c <= 82) ? "rain" : c <= 77 || c <= 86 ? "snow" : "storm");
    const WX_ICON = { clear: "sun", cloudy: "cloud", fog: "cloud-fog", rain: "cloud-rain", snow: "cloud", storm: "cloud-rain" };
    function wxBlock() {
      if (!wx || !wx.current) return null;
      const c = wx.current, k = wxKind(c.weather_code), night = c.is_day === 0 && k === "clear";
      const hours = (wx.hourly && wx.hourly.time) || [], probs = (wx.hourly && wx.hourly.precipitation_probability) || [];
      const nowH = new Date().getHours();
      let rainAt = null;
      hours.forEach((h, i) => { const hh = +h.slice(11, 13); if (rainAt === null && probs[i] >= 50 && (hh >= nowH || hh < 6)) rainAt = { time: h.slice(11, 16), pct: probs[i] }; });
      const strip = el("ol", "tv-wx-hours", ...hours.slice(0, 6).map((h, i) => el("li", null, el("span", null, h.slice(11, 13) + "h"), lu(WX_ICON[wxKind(wx.hourly.weather_code[i])], 16), el("span", "tv-badge" + (probs[i] >= 50 ? " is-rain" : ""), probs[i] + " %"))));
      return el("div", "tv-wx",
        el("div", "tv-wx-now", lu(night ? "moon" : WX_ICON[k], 28), el("strong", null, Math.round(c.temperature_2m) + "°"), el("span", null, t("wx." + k))),
        el("p", "tv-wx-hint" + (rainAt ? " is-rain" : ""), rainAt ? t("wx.rain_at", rainAt) : t("wx.dry")),
        strip,
        el("p", "tv-note", t("wx.source")));
    }

    function render() {
      const open = box.classList.contains("is-open");
      btn.replaceChildren(lu("calendar-days"), t("events.open"));
      btn.setAttribute("aria-expanded", String(open));
      box.setAttribute("aria-hidden", String(!open));
      if (chip) chip.setAttribute("aria-expanded", String(open));
      box.replaceChildren();
      if (!open) return;
      const close = el("button", "tv-close", lu("x")); close.setAttribute("aria-label", t("common.close"));
      close.onclick = () => closeBox();
      box.append(close, Object.assign(el("h2", null, t("events.agenda")), { id: "tv-events-title", tabIndex: -1 }), dayNavigator());
      if (!events && !error && !loading) {
        loading = true;
        load(P.points).then((e) => { events = e; }).catch(() => { error = true; }).finally(() => { loading = false; render(); });
      }
      if (dayOffset === 0) {
        loadWx();
        const w = wxBlock(); if (w) box.append(w);
      }
      const x = christmasToday(events, selectedDate());
      if (x.timeline.length) {
        box.append(el("ol", "tv-timeline", ...x.timeline.map((it) => {
          const image = it.p && it.p.photo
            ? Object.assign(el("img", "tv-thumb tv-tl-img"), { src: it.p.photo, alt: "", width: 72, height: 48, loading: "lazy", decoding: "async" })
            : el("span", "tv-thumb", lu("calendar-days"));
          const main = el("span", "tv-tl-main", el("span", "tv-ev-title", it.title), el("span", "tv-ev-place", it.sub));
          const right = el("span", "tv-ev-right", el("span", "tv-time", it.time));
          const b = el("button", it.past ? "is-past" : "", image, main, right);
          b.onclick = () => pick(it.p);
          return el("li", null, b);
        })));
      } else if (!x.agendaX.length) box.append(el("p", "tv-note", t("state.no_events_body")));
      if (dayOffset === 0 && x.openNow.length) {
        box.append(el("h3", null, t("xmas.open_now")), el("ul", "tv-evlist tv-open-list", ...x.openNow.map((o) => {
          const b = el("button", null, thumb(o.p), el("span", "tv-name", txt(o.p.name)), el("span", "tv-badge is-open", o.label));
          b.onclick = () => pick(o.p); return el("li", null, b);
        })));
      }
      if (x.agendaX.length) box.append(el("h3", null, t("xmas.agenda")), el("ul", "tv-evlist", ...x.agendaX.map(row)));
      else if (loading) box.append(el("p", "tv-note", t("state.loading") + "…"));
      if (dayOffset === 0 && x.soon.length) {
        box.append(el("h3", null, t("xmas.soon")), el("ul", "tv-evlist tv-open-list", ...x.soon.map((o) => {
          const b = el("button", null, thumb(o.p), el("span", "tv-name", txt(o.p.name)), el("span", "tv-badge", t("xmas.from_date", { date: dateFmt(o.date) })));
          b.onclick = () => pick(o.p); return el("li", null, b);
        })));
      }
      const src = el("a", null, t("common.see_source")); src.href = "https://datos.vigo.org/"; src.target = "_blank"; src.rel = "noopener";
      box.append(el("p", "tv-note", t("xmas.source") + " · ", src));
    }

    btn.onclick = () => { if (box.classList.contains("is-open")) closeBox(); else openBox(); };
    document.addEventListener("tv:lang", () => { renderChip(); render(); });
    if (compactChip.addEventListener) compactChip.addEventListener("change", renderChip);
    renderChip();
    setInterval(renderChip, 30000);
    render();
    window.tinyvigoEvents = { open: openBox, load: () => load(P.points) };
  }

  if (window.tinyvigoPoints) init();
  else document.addEventListener("tv:ready", init, { once: true });
})();
