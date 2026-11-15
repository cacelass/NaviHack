// HUD v5 (_prototipos/hud/v5-dock-agenda.html): top bar with the search box on the left and the
// quick actions on the right, and a bottom-right corner with the zoom pair over the minimap.
// The controls are the ones the other modules already build: they are moved here, not copied,
// so their handlers and state stay where they are.
(function () {
  const lu = (name, size = 20) => (window.LU ? LU.svg(name, { size }) : "");
  // right-hand actions, in this order: time, view, layers, theme, settings
  const ACTIONS = [".tv-time-quick", ".tv-view", ".tv-layers-btn", ".tv-theme", ".tv-settings-open"];

  const bar = document.createElement("div");
  bar.className = "tv-topbar";
  const field = document.createElement("label");
  field.className = "tv-topsearch";
  field.innerHTML = lu("search", 20);
  const input = document.createElement("input");
  input.type = "search";
  input.className = "tv-search";
  input.autocomplete = "off";
  input.spellcheck = false;
  field.append(input);
  const actions = document.createElement("div");
  actions.className = "tv-topbar-actions";
  bar.append(field, actions);

  const corner = document.createElement("div");
  corner.className = "tv-corner";
  document.body.append(bar, corner);

  function labels() {
    const P = window.tinyvigoPoints;
    if (!P) return;
    input.placeholder = P.t("points.search");
    input.setAttribute("aria-label", P.t("points.search"));
  }

  // Adopt the controls as their modules create them (some arrive after tv:ready).
  function adopt() {
    for (const sel of ACTIONS) {
      const n = document.querySelector(sel);
      if (n && n.parentNode !== actions) actions.append(n);
    }
    // keep the declared order even if a control arrived late
    ACTIONS.map((s) => actions.querySelector(":scope > " + s)).filter(Boolean).forEach((n) => actions.append(n));
    const zoom = document.getElementById("zoom"), mini = document.querySelector(".tv-minimap");
    if (zoom && zoom.parentNode !== corner) corner.prepend(zoom);
    if (mini && mini.parentNode !== corner) corner.append(mini);
  }

  new MutationObserver(adopt).observe(document.body, { childList: true });
  adopt();
  labels();
  document.addEventListener("tv:lang", labels);
  document.addEventListener("tv:ready", () => { labels(); adopt(); }, { once: true });
  window.tinyvigoHud = { input, adopt };
})();
