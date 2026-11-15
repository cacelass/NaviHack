// TinyVigo Ajustes (UI-06): idioma, tema, vista (mapa dibujado / ciudad) e información en un
// único botón; los controles sueltos (GL/ES/EN del panel, tema, «Vista ciudad», «i») se ocultan.
(function () {
  const lu = (name, size = 20) => { const s = document.createElement("span"); s.innerHTML = window.LU ? LU.svg(name, { size }) : ""; return s.firstChild || s; };
  const el = (tag, cls, ...kids) => { const n = document.createElement(tag); if (cls) n.className = cls; n.append(...kids.filter((k) => k != null && k !== false)); return n; };

  function init() {
    const P = window.tinyvigoPoints, t = P.t;
    document.body.classList.add("tv-has-settings");
    const btn = el("button", "tv-settings-open", lu("settings"));
    const pop = el("div", "tv-settings");
    pop.id = "tv-settings"; pop.setAttribute("role", "dialog"); pop.setAttribute("aria-labelledby", "tv-settings-title"); pop.setAttribute("aria-hidden", "true");
    btn.setAttribute("aria-controls", "tv-settings"); btn.setAttribute("aria-haspopup", "dialog");
    document.body.append(btn, pop);

    // grupo de opciones: aria-pressed para lectores de pantalla; el foco se queda en la opción elegida
    const seg = (items, current, onPick, label) => {
      const g = el("div", "tv-langs tv-seg", ...items.map(([v, text, icon]) => {
        const b = el("button", v === current ? "is-on" : "", icon ? lu(icon, 16) : null, text);
        b.setAttribute("aria-pressed", v === current ? "true" : "false");
        b.dataset.v = v;
        b.onclick = () => { onPick(v); render(); const again = pop.querySelector("[data-v='" + v + "']"); if (again) again.focus(); };
        return b;
      }));
      g.classList.add("tv-seg-" + items.length);
      g.setAttribute("role", "group"); if (label) g.setAttribute("aria-label", label);
      return g;
    };
    const isCity = () => document.body.classList.contains("is-city");
    const LANG_OPTIONS = [["gl", "Galego"], ["es", "Español"], ["en", "English"], ["pt", "Português"]];
    const theme = () => document.documentElement.getAttribute("data-theme") || "dark";
    // UI-08: one group per setting: its title (icon + name) and the control under it, full width.
    // The old icon | label | control row broke on a phone (the control fell over the next row).
    const group = (icon, label, control) => {
      const id = "tv-set-" + label.toLowerCase().replace(/[^a-z0-9]+/g, "-");
      const g = el("section", "tv-set-group", el("h3", "tv-set-title", lu(icon, 16), Object.assign(el("span"), { id, textContent: label })), control);
      if (control && control.setAttribute && !control.getAttribute("aria-label")) control.setAttribute("aria-labelledby", id);
      return g;
    };

    function closePop(restoreFocus = true) {
      pop.classList.remove("is-open");
      render();
      if (restoreFocus) btn.focus();
    }

    function render() {
      const open = pop.classList.contains("is-open");
      btn.setAttribute("aria-label", t("settings.title"));
      btn.setAttribute("aria-expanded", String(open));
      pop.setAttribute("aria-hidden", String(!open));
      pop.replaceChildren();
      if (!open) return;
      const close = el("button", "tv-close", lu("x")); close.setAttribute("aria-label", t("common.close"));
      close.onclick = () => closePop();
      const info = el("button", "tv-btn tv-btn-quiet", lu("info", 16), t("nav.about"));
      info.onclick = () => { closePop(false); const d = document.getElementById("about"); if (d) d.showModal(); };
      // UI-09: the groups sit in a wrapper so desktop can lay them out in two columns
      // without disturbing the close button or the title (display:contents below 701px).
      const grid = el("div", "tv-set-grid",
        group("languages", t("settings.language"), seg(LANG_OPTIONS, P.lang(), (l) => {
          const b = document.querySelectorAll(".tv-panel .tv-langs button")[LANG_OPTIONS.map((x) => x[0]).indexOf(l)];
          if (b) b.click();
        }, t("settings.language"))),
        group("layers", t("settings.view"), seg([["iso", "Vigo 3D", "layers"], ["city", t("app.city_view"), "map-pin"]], isCity() ? "city" : "iso", (v) => window.tinyvigoCity && window.tinyvigoCity.setCity(v === "city"), t("settings.view"))),
        group("clock", t("settings.time"), seg([["auto", t("tour.now"), "clock"], ["day", t("settings.light"), "sun"], ["night", t("settings.dark"), "moon"]], window.tinyvigoAmbient ? window.tinyvigoAmbient.state().time : "auto", (v) => window.tinyvigoAmbient && window.tinyvigoAmbient.set({ time: v }), t("settings.time"))),
        group("cloud", t("settings.weather"), seg([["auto", t("settings.weather_real"), "layers"], ["clear", t("settings.weather_clear"), "sun"], ["cloudy", t("wx.cloudy"), "cloud"], ["rain", t("settings.weather_rain"), "cloud-rain"]], window.tinyvigoAmbient ? window.tinyvigoAmbient.state().weather : "auto", (v) => window.tinyvigoAmbient && window.tinyvigoAmbient.set({ weather: v }), t("settings.weather"))),
        group("palette", t("settings.theme"), seg([["dark", t("settings.dark"), "moon"], ["light", t("settings.light"), "sun"]], theme(), (v) => {
          document.documentElement.setAttribute("data-theme", v);
          try { localStorage.setItem("tinyvigo-theme", v); } catch (e) {}
        }, t("settings.theme"))),
        window.tinyvigoOffline ? group("wifi-off", t("offline.title"), window.tinyvigoOffline.control(lu, el)) : null);
      pop.append(close, Object.assign(el("h2", null, t("settings.title")), { id: "tv-settings-title" }), grid, info);
    }
    btn.onclick = () => {
      pop.classList.toggle("is-open"); render();
      if (pop.classList.contains("is-open")) { const first = pop.querySelector(".tv-seg .is-on") || pop.querySelector("button"); if (first) first.focus(); }
    };
    document.addEventListener("tv:lang", render);
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && pop.classList.contains("is-open")) { e.stopImmediatePropagation(); closePop(); } });
    render();
    window.tinyvigoSettings = { open: () => { pop.classList.add("is-open"); render(); const first = pop.querySelector(".tv-seg .is-on"); if (first) first.focus(); } };
  }
  if (window.tinyvigoPoints) init();
  else document.addEventListener("tv:ready", () => setTimeout(init, 0), { once: true });
})();
