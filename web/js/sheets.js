// TinyVigo: una sola hoja abierta a la vez (MOB-01).
// Lista, ficha, tour, «Hoy», paseo y ajustes se abren cada uno por su cuenta; aquí, al abrirse
// uno, los demás se cierran con SU PROPIO botón × (así cada componente reinicia su estado y no
// queda nada a medias debajo). Marca <body> con .tv-has-sheet y oculta solo los controles tapados.
(function () {
  const SHEETS = [".tv-sheet", ".tv-tour", ".tv-step", ".tv-settings", ".tv-layers-pop", ".tv-panel"];
  const isPanel = (n) => n.classList.contains("tv-panel");
  const isOpen = (n) => (isPanel(n) ? !n.classList.contains("is-collapsed") : n.classList.contains("is-open"));
  const wasOpen = (n, old) => {
    const had = (c) => (" " + (old || "") + " ").includes(" " + c + " ");
    return isPanel(n) ? !had("is-collapsed") : had("is-open");
  };
  const all = () => [...document.querySelectorAll(SHEETS.join(","))];

  function close(n) {
    if (isPanel(n)) { n.classList.add("is-collapsed"); return; }
    const x = [...n.children].find((c) => c.classList && (c.classList.contains("tv-close") || c.classList.contains("tv-layers-close"))) || n.querySelector(".tv-close, .tv-layers-close");
    if (x) x.click();
    if (n.classList.contains("is-open")) n.classList.remove("is-open"); // por si su × no lo hace
  }

  // HUD controls hide only where an open surface actually covers them (HUD v5): on a wide
  // screen a centred sheet takes the dock and nothing else; on a phone, whatever it reaches.
  const HUD = ".tv-dock, .tv-event-chip, .tv-corner, .tv-topsearch, .tv-brand, .tv-topbar-actions > *";
  const CENTRED = ".tv-tour, .tv-step, .tv-settings, .tv-layers-pop";
  const phone = matchMedia("(max-width: 700px)");
  const hit = (a, b) => a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
  function setCovered(n, on) {
    n.classList.toggle("tv-covered", on);
    n.inert = on;
    if (on) n.setAttribute("aria-hidden", "true"); else n.removeAttribute("aria-hidden");
  }
  let settleTimer = 0;
  function cover(open) {
    clearTimeout(settleTimer);
    const huds = [...document.querySelectorAll(HUD)];
    if (!open.length) { huds.forEach((n) => setCovered(n, false)); return; }
    // Straight away, hide what is sure to end up covered (sheets slide in for ~0.4 s) ...
    const bottom = [".tv-dock", ".tv-event-chip", ".tv-corner"];
    const sure = phone.matches ? bottom : open.some((n) => n.matches(CENTRED)) ? [".tv-dock"] : [];
    huds.forEach((n) => { if (sure.some((s) => n.matches(s))) setCovered(n, true); });
    // ... then measure the surfaces where they settled and hide exactly what they cover.
    settleTimer = setTimeout(() => {
      const rects = open.filter((n) => n.isConnected).map((n) => n.getBoundingClientRect()).filter((r) => r.width && r.height);
      huds.forEach((n) => setCovered(n, rects.some((r) => hit(n.getBoundingClientRect(), r))));
    }, 600);
  }

  let closing = false;
  function update() {
    const open = all().filter(isOpen);
    const sheetOpen = open.some((n) => !isPanel(n));
    document.body.classList.toggle("tv-has-sheet", sheetOpen);
    document.body.classList.toggle("tv-has-list", open.some(isPanel));
    cover(open);
  }
  addEventListener("resize", () => update());

  const mo = new MutationObserver((records) => {
    if (closing) return;
    for (const r of records) {
      const n = r.target;
      if (!(n instanceof Element) || !SHEETS.some((s) => n.matches(s))) continue;
      if (isOpen(n) && !wasOpen(n, r.oldValue)) {
        closing = true;
        try { all().forEach((o) => { if (o !== n && isOpen(o)) close(o); }); } finally { closing = false; }
      }
    }
    update();
  });

  function start() {
    mo.observe(document.body, { subtree: true, attributes: true, attributeFilter: ["class"], attributeOldValue: true });
    update();
  }
  if (document.body) start(); else document.addEventListener("DOMContentLoaded", start, { once: true });
  window.tinyvigoSheets = { open: () => all().filter(isOpen).map((n) => n.className), closeAll: () => all().filter(isOpen).forEach(close) };
})();
