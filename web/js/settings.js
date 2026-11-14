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
    pop.setAttribute("role", "dialog");
    document.body.append(btn, pop);

    const seg = (items, current, onPick) => el("div", "tv-langs tv-seg", ...items.map(([v, label, icon]) => {
      const b = el("button", v === current ? "is-on" : "", icon ? lu(icon, 16) : null, label);
      b.onclick = () => { onPick(v); render(); };
      return b;
    }));
    const isCity = () => document.body.classList.contains("is-city");
    const theme = () => document.documentElement.getAttribute("data-theme") || "dark";

    function render() {
      btn.setAttribute("aria-label", t("settings.title"));
      pop.replaceChildren();
      if (!pop.classList.contains("is-open")) return;
      const close = el("button", "tv-close", lu("x")); close.setAttribute("aria-label", t("common.close"));
      close.onclick = () => { pop.classList.remove("is-open"); render(); };
      const info = el("button", "tv-btn tv-btn-quiet", lu("info", 16), t("nav.about"));
      info.onclick = () => { pop.classList.remove("is-open"); render(); const d = document.getElementById("about"); if (d) d.showModal(); };
      pop.append(close, el("h2", null, t("settings.title")),
        el("p", "tv-note", t("settings.language")),
        seg([["gl", "Galego"], ["es", "Español"], ["en", "English"]], P.lang(), (l) => {
          const b = document.querySelectorAll(".tv-panel .tv-langs button")[["gl", "es", "en"].indexOf(l)];
          if (b) b.click();
        }),
        el("p", "tv-note", t("settings.view")),
        seg([["iso", "Vigo 3D", "layers"], ["city", t("app.city_view"), "map-pin"]], isCity() ? "city" : "iso", (v) => window.tinyvigoCity && window.tinyvigoCity.setCity(v === "city")),
        el("p", "tv-note", t("settings.theme")),
        seg([["dark", t("settings.dark"), "moon"], ["light", t("settings.light"), "sun"]], theme(), (v) => {
          document.documentElement.setAttribute("data-theme", v);
          try { localStorage.setItem("tinyvigo-theme", v); } catch (e) {}
        }),
        info);
    }
    btn.onclick = () => { pop.classList.toggle("is-open"); render(); };
    document.addEventListener("tv:lang", render);
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && pop.classList.contains("is-open")) { pop.classList.remove("is-open"); render(); } });
    render();
    window.tinyvigoSettings = { open: () => { pop.classList.add("is-open"); render(); } };
  }
  if (window.tinyvigoPoints) init();
  else document.addEventListener("tv:ready", () => setTimeout(init, 0), { once: true });
})();
