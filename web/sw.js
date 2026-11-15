// NaviVigo sin conexión (OFFLINE-01): la app se instala y el mapa se puede guardar entero para
// caminar sin cobertura. Estrategias por tipo de fichero, todo del mismo origen:
// - teselas (tiles/<versión>/…): primero la caché; la versión va en la ruta, nunca cambian.
// - fotos, vendor y assets de la interfaz: primero la caché.
// - datos en vivo (data/live/…): primero la red; sin red, el último que se guardó.
// - el resto (HTML, JS, CSS, datos): primero la red, para que un despliegue nuevo se vea al momento,
//   y la caché si no hay red.
// Lo de fuera (cámaras del Concello, rutas OSRM, OpenStreetMap) pasa sin tocar.
const SHELL = "navivigo-shell-v1";
const TILES = "navivigo-tiles-v1";
const KEEP = [SHELL, TILES];
const CORE = [
  "./", "index.html", "favicon.svg", "manifest.webmanifest",
  "ui/css/tokens.css", "vendor/leaflet/leaflet.css", "css/app.css", "css/about.css", "css/points.css", "css/hud.css",
  "ui/assets/theme.js", "ui/assets/lucide.js", "vendor/openseadragon.min.js", "vendor/leaflet/leaflet.js",
  "tiles/current.json", "data/points.json", "data/stories.json", "data/elevation.json",
  "data/i18n/gl.json", "data/i18n/es.json", "data/i18n/en.json",
];

self.addEventListener("install", (e) => {
  // uno a uno: si falta un fichero (renombrado en otro despliegue) el resto se guarda igual
  e.waitUntil(caches.open(SHELL).then((c) => Promise.all(CORE.map((u) => c.add(u).catch(() => {})))).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => !KEEP.includes(k)).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});

async function cacheFirst(req, name) {
  const hit = await caches.match(req);
  if (hit) return hit;
  const res = await fetch(req);
  if (res.ok) (await caches.open(name)).put(req, res.clone());
  return res;
}
async function networkFirst(req, name) {
  try {
    const res = await fetch(req);
    if (res.ok) (await caches.open(name)).put(req, res.clone());
    return res;
  } catch (err) {
    const hit = await caches.match(req, { ignoreSearch: true });
    if (hit) return hit;
    if (req.mode === "navigate") { const home = await caches.match("index.html"); if (home) return home; }
    throw err;
  }
}

self.addEventListener("fetch", (e) => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== location.origin) return;
  const path = url.pathname;
  if (path.includes("/tiles/") && !path.endsWith("current.json")) e.respondWith(cacheFirst(req, TILES));
  else if (/\/(data\/photos|vendor|ui\/assets)\//.test(path)) e.respondWith(cacheFirst(req, SHELL));
  else e.respondWith(networkFirst(req, SHELL));
});

// «Guardar el mapa»: la página manda la lista de ficheros; se descargan de 6 en 6 y se avisa del avance
self.addEventListener("message", (e) => {
  if (!e.data || e.data.type !== "save-all") return;
  const urls = e.data.urls, port = e.ports[0];
  e.waitUntil((async () => {
    const tiles = await caches.open(TILES), shell = await caches.open(SHELL);
    let done = 0, failed = 0;
    const queue = [...urls];
    const worker = async () => {
      for (let u = queue.shift(); u; u = queue.shift()) {
        try {
          const cache = u.includes("/tiles/") || u.startsWith("tiles/") ? tiles : shell;
          if (!(await cache.match(u))) { const res = await fetch(u); if (!res.ok) throw new Error(res.status); await cache.put(u, res); }
        } catch (err) { failed++; }
        done++;
        port.postMessage({ done, total: urls.length, failed });
      }
    };
    await Promise.all(Array.from({ length: 6 }, worker));
    port.postMessage({ done, total: urls.length, failed, finished: true });
  })());
});
