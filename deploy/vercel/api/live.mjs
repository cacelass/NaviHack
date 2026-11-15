// Datos en vivo de la demo en Vercel (WEB-05 sin cron): /demo/data/live/<feed>.json se reescribe aquí.
// Mismo formato que scripts/build_web_live.py, así web/js/data.js no cambia: la web sigue leyendo
// ficheros propios (mismo origen) y quien pide a datos.vigo.org / Open-Meteo es el servidor, con caché
// en el CDN de Vercel. Si la fuente falla o no valida, se sirve el último snapshot publicado
// (demo/data/live-snapshot/, lo copia deploy.sh), igual que el «último bueno» de build_web_live.
const UA = "NaviVigo/0.1 (+https://github.com/cacelass/NaviHack)";
const WEATHER_HOURLY = [
  "temperature_2m", "precipitation_probability", "precipitation", "weather_code", "cloud_cover_low",
  "cloud_cover_mid", "cloud_cover_high", "visibility", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m",
];
const PARKING_KEYS = ["nombre", "plazaslibres", "totalplazas", "lat", "lon", "fechahora"];

// url, validación y TTL de CDN copiados de scripts/snapshot.py (FEEDS) y deploy/snapshot.cron
// TRAFFIC-01: same reduction as scripts/snapshot.py slim_trafico (only sections with data, 4 fields, 5 decimals)
const slimTrafico = (d) => ({ type: "FeatureCollection", features: d.features.filter((f) => f.properties && f.properties.estado && f.properties.estado !== "Sin datos").map((f) => ({
  type: "Feature",
  properties: { estado: f.properties.estado, nombre_tramo: f.properties.nombre_tramo, segundos: f.properties.segundos, longitud: f.properties.longitud },
  geometry: { type: f.geometry.type, coordinates: f.geometry.coordinates.map(([x, y]) => [Math.round(x * 1e5) / 1e5, Math.round(y * 1e5) / 1e5]) },
})) });

const FEEDS = {
  trafico: {
    url: "https://datos.vigo.org/data/trafico/treal.geojson",
    valid: (d) => d && Array.isArray(d.features) && d.features.length > 0 && d.features.every((f) => f && f.properties && "estado" in f.properties && f.geometry && f.geometry.coordinates),
    ts: (d) => String(d.features[0].properties.actualizacion || ""),
    slim: slimTrafico,
    stale: 15 * 60, ttl: 60,
  },
  parkings: {
    url: "https://datos.vigo.org/data/trafico/parkings-ocupacion.json",
    valid: (d) => Array.isArray(d) && d.length > 0 && d.every((r) => r && PARKING_KEYS.every((k) => k in r)),
    ts: (d) => d.map((r) => String(r.fechahora)).sort().pop(),
    stale: 10 * 60, ttl: 60,
  },
  agenda: {
    url: "https://datos.vigo.org/data/axenda/agenda-hoy.json",
    valid: (d) => Array.isArray(d) && d.every((r) => r && "titulo" in r),
    ts: () => null,
    stale: 36 * 3600, ttl: 1800,
  },
  centros: {
    url: "https://datos.vigo.org/data/cultura/centros.json",
    valid: (d) => Array.isArray(d) && d.length > 0,
    ts: () => null,
    stale: 7 * 24 * 3600, ttl: 86400,
  },
  weather: {
    url: "https://api.open-meteo.com/v1/forecast?latitude=42.2376&longitude=-8.7247" +
      "&hourly=" + WEATHER_HOURLY.join(",") + "&current=temperature_2m,weather_code," +
      "precipitation,wind_speed_10m,is_day&daily=sunrise,sunset" +
      "&timezone=Europe%2FMadrid&forecast_days=4",
    valid: (d) => d && typeof d.current === "object" && d.hourly && Array.isArray(d.hourly.time) &&
      d.hourly.time.length > 0 && WEATHER_HOURLY.every((v) => Array.isArray(d.hourly[v]) && d.hourly[v].length === d.hourly.time.length),
    ts: (d) => String(d.current.time),
    stale: 3 * 3600, ttl: 900,
  },
};

function json(body, ttl) {
  return new Response(typeof body === "string" ? body : JSON.stringify(body), {
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "public, max-age=0, must-revalidate",
      "cdn-cache-control": `public, s-maxage=${ttl}, stale-while-revalidate=${ttl * 10}`,
    },
  });
}

export async function GET(request) {
  const url = new URL(request.url);
  const name = url.searchParams.get("feed");
  const feed = FEEDS[name];
  if (!feed) return new Response("feed desconocido", { status: 404 });
  try {
    const r = await fetch(feed.url, { headers: { "user-agent": UA }, signal: AbortSignal.timeout(8000) });
    if (!r.ok) throw new Error("http " + r.status);
    const data = await r.json();
    if (!feed.valid(data)) throw new Error("no valida");
    return json({
      feed: name,
      fetched_at: new Date().toISOString(),
      source_url: feed.url,
      source_timestamp: feed.ts(data) || r.headers.get("last-modified"),
      stale_after_s: feed.stale,
      data: feed.slim ? feed.slim(data) : data,
    }, feed.ttl);
  } catch (err) {
    const snap = await fetch(new URL(`/demo/data/live-snapshot/${name}.json`, url.origin));
    if (!snap.ok) return new Response("sin datos", { status: 502 });
    return json(await snap.text(), 60); // reintenta la fuente en un minuto
  }
}
