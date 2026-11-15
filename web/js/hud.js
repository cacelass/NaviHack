// HUD v5 (_prototipos/hud/v5-dock-agenda.html): top bar with the search box on the left and the
// quick actions on the right, and a bottom-right corner with the zoom pair over the minimap.
// The controls are the ones the other modules already build: they are moved here, not copied,
// so their handlers and state stay where they are.
(function () {
  const lu = (name, size = 20) => (window.LU ? LU.svg(name, { size }) : "");

  // SEARCH-02: a row of chips that scrolls sideways says so: a fade on the edge with more to see and
  // an arrow button that moves it on (both go away at the end). Used by search and «Ver sitios».
  window.tvScrollHint = (row) => {
    const wrap = document.createElement("div");
    wrap.className = "tv-scroll-hint";
    const more = document.createElement("button");
    more.type = "button";
    more.className = "tv-scroll-more";
    more.innerHTML = lu("chevron-right", 18);
    const label = () => (window.tinyvigoPoints ? window.tinyvigoPoints.t("search.more_filters") : "");
    more.title = label() || "›";
    // a pointer shortcut only: keyboard and screen-reader users reach every chip with Tab already
    more.tabIndex = -1; more.setAttribute("aria-hidden", "true");
    more.onmousedown = (e) => e.preventDefault(); // keep the search box focused
    more.onclick = () => row.scrollBy({ left: Math.max(120, row.clientWidth * 0.7), behavior: "smooth" });
    const sync = () => {
      const max = row.scrollWidth - row.clientWidth;
      wrap.classList.toggle("can-left", row.scrollLeft > 4);
      wrap.classList.toggle("can-right", row.scrollLeft < max - 4);
    };
    row.addEventListener("scroll", sync, { passive: true });
    new ResizeObserver(sync).observe(row);
    wrap.append(row, more);
    requestAnimationFrame(sync);
    return wrap;
  };
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
