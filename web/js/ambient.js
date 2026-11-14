// TinyVigo ambiente: el mapa dibujado cambia con la hora y el tiempo.
// Noche: tinte azul y las luces de Navidad encendidas, brillando y parpadeando.
// Lluvia: gotas animadas. Nubes: sombras que pasan. Automático (hora local + Open-Meteo) o
// forzado desde Ajustes. Con prefers-reduced-motion todo queda quieto.
(function () {
  const WX = "https://api.open-meteo.com/v1/forecast?latitude=42.2376&longitude=-8.7247&current=weather_code,is_day&timezone=Europe%2FMadrid";
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const state = { time: "auto", weather: "auto" };
  let live = null; // {night, kind}
  try { Object.assign(state, JSON.parse(localStorage.getItem("tinyvigo.ambient") || "{}")); } catch (e) {}

  const kindOf = (c) => (c === 0 || c === 1 ? "clear" : c <= 3 || c === 45 || c === 48 ? "cloudy" : "rain");
  function fetchLive() {
    fetch(WX).then((r) => r.json()).then((d) => { live = { night: d.current.is_day === 0, kind: kindOf(d.current.weather_code) }; apply(); }).catch(() => {});
  }
  const isNight = () => (state.time === "night" ? true : state.time === "day" ? false : live ? live.night : (new Date().getHours() >= 18 || new Date().getHours() < 8));
  const weather = () => (state.weather !== "auto" ? state.weather : live ? live.kind : "clear");

  // ── capas ────────────────────────────────────────────────────────────────
  let tint = null, glows = [], viewer = null;
  const rainCanvas = document.createElement("canvas");
  rainCanvas.className = "tv-rain";
  const clouds = document.createElement("div");
  clouds.className = "tv-clouds";
  for (let i = 0; i < 4; i++) clouds.append(Object.assign(document.createElement("span"), { style: "--i:" + i }));
  document.body.append(clouds, rainCanvas);

  function buildNight() {
    if (tint || !viewer) return;
    tint = document.createElement("div");
    tint.className = "tv-night";
    viewer.addOverlay({ element: tint, location: new OpenSeadragon.Rect(-0.5, -0.5, 2, 2) });
    // luces: un halo por punto de luz y chispas alrededor, con ritmos distintos
    const pts = window.tinyvigoPoints.points.filter((p) => p.on_map && ["light", "attraction", "market", "santa_kings"].includes(p.type));
    let seed = 7; const rnd = () => ((seed = (seed * 9301 + 49297) % 233280) / 233280);
    // el Árbol de Porta do Sol (46 m) está pintado en el centro del render (origen de GEO-01);
    // el punto del Concello queda a ~58 m. Cono de luz que escala con el zoom, sobre el dibujo.
    if (pts.some((p) => p.id === "concello-2552")) {
      // medido sobre el bloque v6: base del árbol pintado en (0.525, 0.523), punta en 0.458, ancho 0.029
      const cx = 0.525, base = 0.523, H = 0.0654, W = 0.0286;
      const cone = document.createElement("span");
      cone.className = "tv-glow-tree";
      viewer.addOverlay({ element: cone, location: new OpenSeadragon.Rect(cx - W / 2, base - H, W, H) });
      glows.push(cone);
      for (let k = 0; k < 22; k++) {
        const sp = document.createElement("span");
        sp.className = "tv-spark";
        sp.style.setProperty("--d", (rnd() * 2).toFixed(2) + "s");
        sp.style.setProperty("--t", (0.9 + rnd() * 1.4).toFixed(2) + "s");
        const h = rnd(), w = (1 - h) * W * 0.5;
        viewer.addOverlay({ element: sp, location: new OpenSeadragon.Point(cx + (rnd() - 0.5) * 2 * w, base - h * H), placement: OpenSeadragon.Placement.CENTER });
        glows.push(sp);
      }
    }
    for (const p of pts) {
      const halo = document.createElement("span");
      halo.className = "tv-glow tv-glow-" + p.type;
      halo.style.setProperty("--d", (rnd() * 3).toFixed(2) + "s");
      viewer.addOverlay({ element: halo, location: new OpenSeadragon.Point(p.x, p.y), placement: OpenSeadragon.Placement.CENTER });
      glows.push(halo);
      for (let k = 0; k < 7; k++) {
        const s = document.createElement("span");
        s.className = "tv-spark";
        s.style.setProperty("--d", (rnd() * 2.4).toFixed(2) + "s");
        s.style.setProperty("--t", (1.2 + rnd() * 1.8).toFixed(2) + "s");
        s.style.setProperty("--h", Math.round(rnd() * 360) + "deg");
        const ang = rnd() * Math.PI * 2, r = 0.004 + rnd() * 0.012;
        viewer.addOverlay({ element: s, location: new OpenSeadragon.Point(p.x + Math.cos(ang) * r, p.y + Math.sin(ang) * r * 0.6), placement: OpenSeadragon.Placement.CENTER });
        glows.push(s);
      }
    }
  }

  // lluvia en canvas: trazos inclinados que caen
  let drops = [], raf = 0;
  function rainLoop() {
    const c = rainCanvas, ctx = c.getContext("2d");
    if (c.width !== innerWidth || c.height !== innerHeight) { c.width = innerWidth; c.height = innerHeight; }
    if (!drops.length) drops = Array.from({ length: Math.round((innerWidth * innerHeight) / 5500) }, () => ({ x: Math.random() * innerWidth, y: Math.random() * innerHeight, v: 9 + Math.random() * 9, l: 10 + Math.random() * 14 }));
    ctx.clearRect(0, 0, c.width, c.height);
    ctx.strokeStyle = isNight() ? "rgba(190, 210, 255, .45)" : "rgba(220, 230, 245, .55)";
    ctx.lineWidth = 1.2; ctx.lineCap = "round"; ctx.beginPath();
    for (const d of drops) {
      ctx.moveTo(d.x, d.y); ctx.lineTo(d.x - d.l * 0.25, d.y + d.l);
      if (!reduced) { d.y += d.v; d.x -= d.v * 0.25; if (d.y > c.height) { d.y = -20; d.x = Math.random() * (c.width + 100); } }
    }
    ctx.stroke();
    if (!reduced) raf = requestAnimationFrame(rainLoop);
  }

  function apply() {
    const night = isNight(), w = weather(), city = document.body.classList.contains("is-city");
    document.body.classList.toggle("tv-is-night", night);
    if (night) buildNight();
    if (tint) tint.style.opacity = night ? "1" : "0";
    glows.forEach((g) => (g.style.display = night ? "" : "none"));
    const raining = w === "rain" && !city;
    rainCanvas.style.display = raining ? "block" : "none";
    cancelAnimationFrame(raf);
    if (raining) { drops = []; rainLoop(); }
    clouds.classList.toggle("is-on", (w === "cloudy" || w === "rain") && !city);
    clouds.classList.toggle("is-rain", w === "rain");
    document.body.classList.toggle("tv-reduced", reduced);
  }

  function set(next) {
    Object.assign(state, next);
    try { localStorage.setItem("tinyvigo.ambient", JSON.stringify(state)); } catch (e) {}
    apply();
  }

  function init() {
    viewer = window.tinyvigo && window.tinyvigo.viewer;
    if (!viewer) { setTimeout(init, 200); return; }
    fetchLive(); setInterval(fetchLive, 600000); setInterval(apply, 60000);
    new MutationObserver(apply).observe(document.body, { attributes: true, attributeFilter: ["class"] });
    apply();
  }
  window.tinyvigoAmbient = { set, state: () => ({ ...state }), isNight, weather };
  if (window.tinyvigoPoints) init(); else document.addEventListener("tv:ready", init, { once: true });
})();
