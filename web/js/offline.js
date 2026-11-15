// NaviVigo sin conexión (OFFLINE-01): registra sw.js, dice cuándo no hay red y, desde Ajustes,
// guarda el mapa entero (todas las teselas, las fotos y los datos, ~10 MB) para caminar sin
// cobertura. El estado queda a la vista (NN/g): «Guardado», «Guardando… 42 %», «Sin conexión».
(function () {
  if (!("serviceWorker" in navigator) || !/^https?:$/.test(location.protocol)) return;
  const t = (k, v) => (window.tinyvigoPoints ? window.tinyvigoPoints.t(k, v) : k);
  const KEY = "tinyvigo.offline"; // versión de teselas que quedó guardada entera
  let saving = null; // { done, total } mientras se descarga
  const listeners = new Set();
  const changed = () => listeners.forEach((f) => f());

  navigator.serviceWorker.register("sw.js").catch(() => {});

  // ── qué hay que guardar: todo lo que el mapa usa sin pedir nada fuera ──
  function everything() {
    const m = window.tinyvigo && window.tinyvigo.manifest, P = window.tinyvigoPoints;
    if (!m || !P) return null;
    const urls = new Set();
    const base = "tiles/" + m.version + "/";
    for (const [level, d] of Object.entries(m.levels || {}))
      for (let x = 0; x < d.cols; x++) for (let y = 0; y < d.rows; y++) urls.add(base + level + "/" + x + "_" + y + "." + m.format);
    urls.add(base + "manifest.json");
    for (const p of P.points) if (p.photo) urls.add(p.photo);
    ["data/transit.json", "data/streets.json", "data/street-lamps.json", "data/venues.json", "data/layers/cameras.geojson",
     "data/live/parkings.json", "data/live/weather.json", "data/live/agenda.json", "data/live/centros.json"].forEach((u) => urls.add(u));
    // only the app's own files (under its folder): not Vercel's analytics or anything else on the host
    const root = new URL(".", location.href).pathname;
    const local = (u) => { try { const a = new URL(u, location.href); const rel = a.origin === location.origin && a.pathname.startsWith(root) ? a.pathname.slice(root.length) : null; return rel && !rel.startsWith("_vercel/") ? rel : null; } catch (e) { return null; } };
    document.querySelectorAll("script[src], link[rel=stylesheet]").forEach((n) => { const u = local(n.src || n.href); if (u) urls.add(u); });
    return { urls: [...urls], version: m.version };
  }
  const savedVersion = () => { try { return localStorage.getItem(KEY); } catch (e) { return null; } };
  const isSaved = () => { const m = window.tinyvigo && window.tinyvigo.manifest; return !!m && savedVersion() === m.version; };

  async function save() {
    const job = everything(), reg = await navigator.serviceWorker.ready;
    if (!job || saving || !reg.active) return;
    saving = { done: 0, total: job.urls.length, failed: 0 }; changed();
    const ch = new MessageChannel();
    ch.port1.onmessage = (e) => {
      saving = e.data;
      if (e.data.finished) {
        if (!e.data.failed) { try { localStorage.setItem(KEY, job.version); } catch (x) {} }
        saving = null;
      }
      changed();
    };
    reg.active.postMessage({ type: "save-all", urls: job.urls }, [ch.port2]);
  }

  // ── fila para Ajustes (settings.js la pide si existe) ──
  function control(lu, el) {
    const row = el("div", "tv-offline");
    const paint = () => {
      const pct = saving ? Math.round((100 * saving.done) / Math.max(1, saving.total)) : 0;
      const state = saving ? t("offline.saving", { pct }) : isSaved() ? t("offline.saved") : t("offline.hint");
      const btn = el("button", "tv-btn tv-btn-quiet", lu(isSaved() && !saving ? "circle-check" : "download", 16), isSaved() && !saving ? t("offline.update") : t("offline.save"));
      btn.disabled = !!saving || !navigator.onLine;
      btn.onclick = save;
      const bar = saving ? el("span", "tv-offline-bar", Object.assign(el("span"), { style: "width:" + pct + "%" })) : null;
      const note = el("p", "tv-offline-state", state);
      note.setAttribute("role", "status");
      row.replaceChildren(...[note, bar, btn].filter(Boolean));
    };
    listeners.add(() => { if (row.isConnected) paint(); });
    paint();
    return row;
  }

  // ── aviso al quedarse sin red: qué pasa y qué sigue funcionando ──
  function toast(text) {
    let n = document.querySelector(".tv-ltoast");
    if (!n) { n = document.createElement("div"); n.className = "tv-ltoast"; n.setAttribute("role", "status"); document.body.append(n); }
    n.textContent = text; n.classList.add("is-on");
    clearTimeout(toast.timer); toast.timer = setTimeout(() => n.classList.remove("is-on"), 4200);
  }
  const net = () => {
    document.body.classList.toggle("is-offline", !navigator.onLine);
    if (!navigator.onLine) toast(isSaved() ? t("offline.now_saved") : t("offline.now"));
    changed();
  };
  addEventListener("offline", net);
  addEventListener("online", () => { net(); toast(t("offline.back")); });

  window.tinyvigoOffline = { save, control, isSaved, state: () => ({ saving, saved: isSaved() }) };
})();
