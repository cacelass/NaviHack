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

  // HUD controls hide only where an open surface will cover them (HUD v5): on a wide screen a
  // centred sheet takes the dock and nothing else; on a phone, whatever it reaches. The check
  // uses where the surface ENDS UP, not where its slide-in is now, so the covered controls go
  // away at the same moment the surface starts to appear, with no timers.
  const HUD = ".tv-dock, .tv-event-chip, .tv-corner, .tv-topsearch, .tv-topbar-actions > *";
  const hit = (a, b) => a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
  // translate of a transform string; transition keyframes can keep percentages (translate(-50%, 0)),
  // which DOMMatrix cannot parse, so those resolve against the surface's own size
  function shift(str, n) {
    if (!str || str === "none") return [0, 0];
    try { const m = new DOMMatrixReadOnly(str); return [m.m41, m.m42]; } catch (e) { /* has % */ }
    const len = (v, size) => (v.trim().endsWith("%") ? (parseFloat(v) / 100) * size : parseFloat(v) || 0);
    let m, x = 0, y = 0;
    if ((m = str.match(/translate\(\s*([^,)]+)(?:,\s*([^)]+))?\)/))) { x = len(m[1], n.offsetWidth); y = m[2] ? len(m[2], n.offsetHeight) : 0; }
    if ((m = str.match(/translateX\(([^)]+)\)/))) x = len(m[1], n.offsetWidth);
    if ((m = str.match(/translateY\(([^)]+)\)/))) y = len(m[1], n.offsetHeight);
    return [x, y];
  }
  function finalRect(n) {
    // layout box (transforms excluded; fixed elements measure from the viewport) moved by the
    // transform it is heading to: the end of a running transition, or the current one when still.
    // Keyframe slide-ins (tv-in-left / tv-in-up) end at none.
    const anims = n.getAnimations();
    let x = 0, y = 0;
    if (!anims.some((a) => a.animationName)) {
      const run = anims.find((a) => a.transitionProperty === "transform");
      [x, y] = shift(run ? run.effect.getKeyframes().at(-1).transform : getComputedStyle(n).transform, n);
    }
    const left = n.offsetLeft + x, top = n.offsetTop + y;
    return { left, top, right: left + n.offsetWidth, bottom: top + n.offsetHeight };
  }
  function cover(open) {
    let rects = [];
    try { rects = open.filter((n) => n.isConnected && n.offsetWidth).map(finalRect); } catch (e) { /* never leave a stale cover */ }
    document.querySelectorAll(HUD).forEach((n) => {
      const on = rects.some((r) => hit(n.getBoundingClientRect(), r));
      n.classList.toggle("tv-covered", on);
      n.inert = on;
      if (on) n.setAttribute("aria-hidden", "true"); else n.removeAttribute("aria-hidden");
    });
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
