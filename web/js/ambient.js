// TinyVigo ambiente: el mapa dibujado cambia con la hora y el tiempo, sin lastrar el visor.
// - Noche gradual: 0 antes de la puesta de sol real (Open-Meteo), sube durante una hora y
//   baja antes del amanecer. Tinte oscuro y luces de Navidad con esa intensidad.
// - Ligero: un halo por punto (21 elementos en total), los destellos van dentro del halo;
//   sin mix-blend-mode ni filtros; solo se anima la opacidad (compositor).
// - Tiempo en canvas a ~20 fps con ≤ 140 partículas (gotas según el código, copos o
//   relámpagos), en pausa si la pestaña no se ve. Niebla fuera: velaba el mapa.
// Hora y clima: automáticos o forzados desde Ajustes y el botón rápido.
(function () {
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const state = { time: "auto", weather: "auto" };
  let live = null; // {kind, sunrise:[Date], sunset:[Date]}
  try { Object.assign(state, JSON.parse(localStorage.getItem("tinyvigo.ambient") || "{}")); } catch (e) {}

  // WMO weather_code → clima (Open-Meteo). Sin niebla: se trata como nublado.
  const kindOf = (c) =>
    c == null || c <= 1 ? "clear"
    : c === 2 || c === 3 || c === 45 || c === 48 ? "cloudy"
    : c >= 51 && c <= 57 ? "drizzle"
    : c >= 61 && c <= 67 ? (c === 65 ? "heavy" : "rain")
    : c >= 71 && c <= 77 ? "snow"
    : c >= 80 && c <= 82 ? (c === 82 ? "heavy" : "showers")
    : c >= 85 && c <= 86 ? "snow"
    : c >= 95 ? "storm"
    : "clear";
  const CLIMATES = {
    clear:   { rain: 0 },
    cloudy:  { rain: 0, clouds: true },
    drizzle: { rain: 0.22 },
    rain:    { rain: 0.55 },
    heavy:   { rain: 1 },
    showers: { rain: 0.5, showers: true },
    storm:   { rain: 0.9, storm: true },
    snow:    { snow: true },
  };
  function fetchLive() {
    tinyvigoData.weather().then((d) => { // WEB-05: fichero propio
      live = { kind: kindOf(d.current.weather_code), sunrise: d.daily.sunrise.map((s) => new Date(s)), sunset: d.daily.sunset.map((s) => new Date(s)) };
      apply();
    }).catch(() => {});
  }
  // 0 = día, 1 = noche cerrada; rampa de 60 min tras la puesta y antes del amanecer
  function nightLevel(now = new Date()) {
    if (state.time === "night") return 1;
    if (state.time === "day") return 0;
    const ramp = 60 * 60000;
    if (live) {
      const rise = live.sunrise[0], set = live.sunset[0], riseNext = live.sunrise[1] || rise;
      if (now < rise) return Math.min(1, Math.max(0, (rise - now) / ramp));
      if (now < set) return 0;
      return Math.min(Math.min(1, (now - set) / ramp), Math.max(0, Math.min(1, (riseNext - now) / ramp)));
    }
    const h = now.getHours() + now.getMinutes() / 60; // sin datos: noviembre en Vigo, ~18:00–08:30
    return h >= 19 || h < 7.5 ? 1 : h >= 18 ? h - 18 : h < 8.5 ? 8.5 - h : 0;
  }
  const isNight = () => nightLevel() > 0.5;
  const weather = () => {
    const w = state.weather !== "auto" ? state.weather : live ? live.kind : "clear";
    return CLIMATES[w] ? w : "clear"; // un "fog" antiguo en localStorage cae a despejado
  };

  // ── capas ────────────────────────────────────────────────────────────────
  let tint = null, glows = [], viewer = null, built = false;
  const fx = document.createElement("canvas");
  fx.className = "tv-rain";
  const clouds = document.createElement("div");
  clouds.className = "tv-clouds";
  for (let i = 0; i < 2; i++) clouds.append(Object.assign(document.createElement("span"), { style: "--i:" + i }));
  document.body.append(clouds, fx);

  function build() {
    if (built || !viewer || !window.tinyvigoPoints) return;
    built = true;
    // tinte fijo sobre la pantalla (no una capa pegada al mapa que se recoloca en cada fotograma)
    tint = document.createElement("div");
    tint.className = "tv-night";
    const cv = viewer.drawer && viewer.drawer.canvas; // encima del dibujo, debajo de luces y marcadores
    if (cv && cv.parentNode) cv.parentNode.insertBefore(tint, cv.nextSibling); else document.getElementById("map").after(tint);
    const pts = window.tinyvigoPoints.points.filter((p) => p.on_map && ["light", "attraction", "market", "santa_kings"].includes(p.type));
    pts.forEach((p, i) => {
      const halo = document.createElement("span");
      halo.className = "tv-glow tv-glow-" + p.type;
      halo.style.setProperty("--d", ((i * 0.37) % 3).toFixed(2) + "s");
      // el halo escala con el mapa (~40 m de radio): de lejos es pequeño, de cerca se ve
      const r = 0.0075;
      viewer.addOverlay({ element: halo, location: new OpenSeadragon.Rect(p.x - r, p.y - r * 0.8, 2 * r, 1.6 * r) });
      glows.push(halo);
    });
  }

  // tiempo: gotas (densidad por código), copos o relámpagos en un solo canvas.
  // ≤ 140 partículas, ~20 fps, pausa con la pestaña oculta.
  let drops = [], flakes = [], bolt = null, nextBolt = 2000, raf = 0, last = 0;
  const seedRain = (k) => {
    const n = Math.round((innerWidth * innerHeight) / 12000 * k.rain);
    drops = Array.from({ length: Math.min(140, Math.max(24, n)) }, () => ({ x: Math.random() * innerWidth, y: Math.random() * innerHeight }));
  };
  const seedSnow = () => {
    const n = Math.round((innerWidth * innerHeight) / 9000);
    flakes = Array.from({ length: Math.min(140, Math.max(24, n)) }, () => ({ x: Math.random() * innerWidth, y: Math.random() * innerHeight, r: 0.6 + Math.random() * 2.2, v: 1.6 + Math.random() * 2.2, ph: Math.random() * Math.PI * 2, a: 0.4 + Math.random() * 0.5 }));
  };
  function weatherLoop(ts) {
    raf = requestAnimationFrame(weatherLoop);
    if (document.hidden || ts - last < 50) return;
    last = ts;
    const c = fx, ctx = c.getContext("2d"), W = innerWidth, H = innerHeight;
    if (c.width !== W || c.height !== H) { c.width = W; c.height = H; drops = []; flakes = []; }
    const k = CLIMATES[weather()] || CLIMATES.clear;
    if (k.snow) { if (!flakes.length) seedSnow(); }
    else if (k.rain > 0) { if (!drops.length) seedRain(k); }
    ctx.clearRect(0, 0, W, H);
    const sec = ts / 1000;
    if (k.snow) {
      ctx.fillStyle = "rgba(240, 246, 255, .8)";
      for (const f of flakes) {
        f.y += f.v; f.x += Math.sin(sec * 0.8 + f.ph) * 0.25;
        if (f.y > H + 4) { f.y = -4; f.x = Math.random() * W; }
        if (f.x < -4) f.x = W + 4; else if (f.x > W + 4) f.x = -4;
        ctx.globalAlpha = f.a * (0.7 + 0.3 * Math.sin(sec * 2 + f.ph));
        ctx.beginPath(); ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2); ctx.fill();
      }
      ctx.globalAlpha = 1;
    } else if (k.rain > 0) {
      const gust = k.showers ? 0.7 + 0.5 * Math.abs(Math.sin(sec / 0.9)) : 1;
      const inten = k.rain * gust;
      const v = 21 + inten * 45, len = 8 + inten * 12, alpha = 0.3 + inten * 0.3;
      ctx.strokeStyle = "rgba(210, 222, 240," + alpha.toFixed(2) + ")"; ctx.lineWidth = 1.2; ctx.beginPath();
      for (const d of drops) {
        ctx.moveTo(d.x, d.y); ctx.lineTo(d.x - len * 0.25, d.y + len);
        d.y += v; d.x -= v * 0.25;
        if (d.y > H + len) { d.y = -len; d.x = Math.random() * (W + 100); }
      }
      ctx.stroke();
    }
    if (k.storm) {
      if (bolt) {
        bolt.t += 50;
        const a = Math.max(0, 1 - bolt.t / 320);
        ctx.strokeStyle = "rgba(255, 255, 255," + (0.9 * a).toFixed(2) + ")";
        ctx.lineWidth = 2.5; ctx.lineJoin = ctx.lineCap = "round";
        ctx.beginPath(); ctx.moveTo(bolt.pts[0].x, bolt.pts[0].y);
        for (let i = 1; i < bolt.pts.length; i++) ctx.lineTo(bolt.pts[i].x, bolt.pts[i].y);
        ctx.stroke();
        if (bolt.t > 320) { bolt = null; nextBolt = 1800 + Math.random() * 4200; }
      } else if ((nextBolt -= 50) <= 0) {
        const x = W * (0.2 + Math.random() * 0.6), y1 = H * (0.5 + Math.random() * 0.35);
        const pts = [{ x, y: 0 }]; let yy = 0, xx = x;
        while (yy < y1) { yy += 24 + Math.random() * 40; xx += (Math.random() - 0.5) * 90; pts.push({ x: xx, y: yy }); }
        bolt = { pts, t: 0 };
      }
    }
  }

  function apply() {
    const lvl = nightLevel(), w = weather(), k = CLIMATES[w] || CLIMATES.clear, city = document.body.classList.contains("is-city");
    document.body.classList.toggle("tv-is-night", lvl > 0.5);
    document.documentElement.style.setProperty("--night", lvl.toFixed(2));
    if (lvl > 0 && !city) build();
    if (tint) tint.style.display = lvl > 0 ? "" : "none";
    glows.forEach((g) => (g.style.display = lvl > 0.15 && !city ? "" : "none"));
    const weatherOn = (k.snow || k.rain > 0) && !city;
    fx.style.display = weatherOn ? "block" : "none";
    cancelAnimationFrame(raf);
    if (weatherOn && !reduced) raf = requestAnimationFrame(weatherLoop);
    clouds.classList.toggle("is-on", (k.clouds || k.rain > 0 || k.snow) && !city && !reduced);
    document.body.classList.toggle("tv-reduced", reduced);
  }

  // botón rápido junto a Ajustes: Ahora (hora real) -> Noche -> Día
  const quick = document.createElement("button");
  quick.className = "tv-time-quick";
  const ORDER = ["auto", "night", "day"], ICON = { auto: "clock", night: "moon", day: "sun" };
  function paintQuick() {
    const t = window.tinyvigoPoints ? window.tinyvigoPoints.t : (k) => k;
    const label = { auto: t("tour.now"), night: t("settings.dark"), day: t("settings.light") }[state.time];
    quick.innerHTML = (window.LU ? LU.svg(ICON[state.time], { size: 20 }) : "") + "<span>" + label + "</span>";
    quick.setAttribute("aria-label", t("settings.time") + ": " + label);
    quick.classList.toggle("is-forced", state.time !== "auto");
  }
  function set(next) {
    Object.assign(state, next);
    try { localStorage.setItem("tinyvigo.ambient", JSON.stringify(state)); } catch (e) {}
    apply();
    paintQuick();
  }
  quick.onclick = () => set({ time: ORDER[(ORDER.indexOf(state.time) + 1) % ORDER.length] });
  document.body.append(quick);
  document.addEventListener("tv:lang", paintQuick);

  function init() {
    paintQuick();
    viewer = window.tinyvigo && window.tinyvigo.viewer;
    if (!viewer) { setTimeout(init, 200); return; }
    fetchLive(); setInterval(fetchLive, 600000); setInterval(apply, 60000);
    new MutationObserver(apply).observe(document.body, { attributes: true, attributeFilter: ["class"] });
    apply();
  }
  window.tinyvigoAmbient = { set, state: () => ({ ...state }), isNight, nightLevel, weather };
  if (window.tinyvigoPoints) init(); else document.addEventListener("tv:ready", init, { once: true });
})();
