// HUD v5 (_prototipos/hud/v5-dock-agenda.html): top bar with the search box on the left and the
// quick actions on the right, and a bottom-right corner with the zoom pair over the minimap.
// The controls are the ones the other modules already build: they are moved here, not copied,
// so their handlers and state stay where they are.
(function () {
  const lu = (name, size = 20) => (window.LU ? LU.svg(name, { size }) : "");

  // SEARCH-02: a row of chips that scrolls sideways says so: an edge fade and a quiet chevron on
  // each side that has more (both go away at the ends). Used by search and «Ver sitios».
  window.tvScrollHint = (row) => {
    const wrap = document.createElement("div");
    wrap.className = "tv-scroll-hint";
    // a quiet chevron on each edge with more to see (not a button with a box): a pointer shortcut,
    // keyboard and screen readers reach every chip with Tab already
    const arrow = (dir) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "tv-scroll-more is-" + dir;
      b.innerHTML = lu(dir === "left" ? "chevron-left" : "chevron-right", 18);
      b.tabIndex = -1; b.setAttribute("aria-hidden", "true");
      b.onmousedown = (e) => e.preventDefault(); // keep the search box focused
      b.onclick = () => row.scrollBy({ left: (dir === "left" ? -1 : 1) * Math.max(120, row.clientWidth * 0.7), behavior: "smooth" });
      return b;
    };
    const sync = () => {
      const max = row.scrollWidth - row.clientWidth;
      wrap.classList.toggle("can-left", row.scrollLeft > 4);
      wrap.classList.toggle("can-right", row.scrollLeft < max - 4);
    };
    row.addEventListener("scroll", sync, { passive: true });
    new ResizeObserver(sync).observe(row);
    wrap.append(arrow("left"), row, arrow("right"));
    requestAnimationFrame(sync);
    return wrap;
  };

  // right-hand actions, in this order: time, view, layers, theme, settings
  // UI-08: the theme lives in Ajustes only (a second sun/moon next to «Ahora» confused people)
  const ACTIONS = [".tv-time-quick", ".tv-view", ".tv-layers-btn", ".tv-settings-open"];

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

  // A11Y-01: the map and its ~30 markers come first in the DOM; the first Tab offers a jump to search
  const skip = document.createElement("a");
  skip.className = "tv-skip";
  skip.href = "#";
  skip.onclick = (e) => { e.preventDefault(); input.focus(); };
  document.body.prepend(skip);

  function labels() {
    const P = window.tinyvigoPoints;
    if (!P) return;
    input.placeholder = P.t("points.search");
    input.setAttribute("aria-label", P.t("points.search"));
    skip.textContent = P.t("a11y.skip");
    // the dock was written in Spanish in index.html and never translated; on a phone it shows only
    // its icons, so each button carries its full name for screen readers too
    for (const [id, key] of [["dock-sitios", "dock.sites"], ["dock-ruta", "dock.route"]]) {
      const b = document.getElementById(id); if (!b) continue;
      const full = b.querySelector(".tv-dock-label"), short = b.querySelector(".tv-dock-label-short");
      if (full) full.textContent = P.t(key);
      if (short) short.textContent = P.t(key + "_short");
      b.setAttribute("aria-label", P.t(key));
    }
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
