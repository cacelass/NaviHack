// TinyVigo compartir (SHARE-01): el estado va en el enlace y se reabre al cargar.
//   #p=<id>             un punto con su ficha
//   #ruta=<ids>&s=<lat,lon>&h=<hora>&d=<min>  ESE paseo: paradas en orden, salida y hora (SHARE-02)
//   #tour=<min>-<hora>  enlaces viejos: un tour nuevo desde Porta do Sol
// Botón «Compartir»: hoja nativa del móvil (navigator.share) o copia el enlace.
(function () {
  const lu = (name, size = 16) => { const s = document.createElement("span"); s.innerHTML = window.LU ? LU.svg(name, { size }) : ""; return s.firstChild || s; };
  const parse = () => Object.fromEntries(location.hash.replace(/^#/, "").split("&").filter(Boolean).map((kv) => kv.split("=").map(decodeURIComponent)));
  const setHash = (obj) => {
    const lang = window.tinyvigoPoints ? window.tinyvigoPoints.lang() : "";
    const h = Object.entries(obj).map(([k, v]) => k + "=" + encodeURIComponent(v)).join("&");
    history.replaceState(null, "", location.pathname + (lang ? "?lang=" + lang : "") + (h ? "#" + h : ""));
  };

  function toast(text) {
    const n = document.createElement("div");
    n.className = "tv-toast"; n.setAttribute("role", "status"); n.textContent = text;
    document.body.append(n);
    setTimeout(() => n.remove(), 2200);
  }

  async function share(title) {
    const url = location.href, t = window.tinyvigoPoints.t;
    if (navigator.share) { try { await navigator.share({ title: "NaviVigo · " + title, url }); return; } catch (e) { /* cancelado: se copia */ } }
    try { await navigator.clipboard.writeText(url); toast(t("share.copied")); } catch (e) { prompt(t("share.copy"), url); }
  }
  function button(title) {
    const b = document.createElement("button");
    b.className = "tv-btn tv-btn-quiet tv-btn-icon";
    const label = window.tinyvigoPoints.t("share.button");
    b.setAttribute("aria-label", label); b.title = label;
    b.append(lu("share-2", 20));
    b.onclick = () => share(title);
    return b;
  }

  function init() {
    const P = window.tinyvigoPoints;
    // ids «concello-2552» viajan como «2552»; el resto, enteros
    const short = (id) => (/^concello-\d+$/.test(id) ? id.slice(9) : id), long = (id) => (/^\d+$/.test(id) ? "concello-" + id : id);
    const walkHash = () => {
      const s = window.tinyvigoTour && window.tinyvigoTour.shareState();
      return s ? { ruta: s.ids.map(short).join("."), s: s.from.map((n) => n.toFixed(5)).join(","), h: s.when, d: s.budget } : null;
    };
    // while a walk is on, the link keeps the walk (opening a stop's card must not replace it)
    document.addEventListener("tv:select", (e) => { const w = walkHash(); setHash(w || { p: e.detail.id }); });
    document.addEventListener("tv:route", (e) => { if (e.detail.mode === "walking") { const w = walkHash(); if (w) setHash(w); } });
    document.addEventListener("tv:clear-route", () => setHash({}));
    // abrir lo que trae el enlace
    const st = parse();
    if (st.p) { const p = P.points.find((x) => x.id === st.p); if (p) setTimeout(() => P.select(p), 400); }
    if (st.ruta && window.tinyvigoTour) {
      const from = (st.s || "").split(",").map(Number), ok = from.length === 2 && from.every(Number.isFinite);
      const ids = st.ruta.split(".").filter(Boolean).slice(0, 40).map(long);
      // only what makes sense gets in: a time like 18 or 18:30 (or now) and 15 min to 4 h
      const when = /^(now|([01]?\d|2[0-3])(:[0-5]\d)?)$/.test(st.h || "") ? st.h : "now", d = Math.round(+st.d || 0);
      setTimeout(() => window.tinyvigoTour.openShared({ ids, from: ok ? from : null, when, budget: d >= 15 && d <= 240 ? d : 0 }), 500);
    } else if (st.tour && window.tinyvigoTour) {
      const [min, when] = st.tour.split("-");
      setTimeout(() => { const T = window.tinyvigoTour; T.setFromHere(false); T.setBudget(+min || 60); T.setWhen(when || "now"); T.open(); T.run(); }, 500);
    }
    window.tinyvigoShare = { button, share, setHash };
  }
  if (window.tinyvigoPoints && window.tinyvigoTour) init();
  else document.addEventListener("tv:ready", () => setTimeout(init, 0), { once: true });
})();
