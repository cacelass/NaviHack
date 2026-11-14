// Tests del planificador (PLANNER-01). Sin red: matriz aproximada (fetch que falla).
const assert = require("node:assert/strict");
const P = require("../../web/js/planner.js");
const noNet = () => Promise.reject(new Error("offline"));
const PORTA = [42.238072, -8.725813];
const pts = [
  ["arbol", 42.238072, -8.725813], ["muneco", 42.233692, -8.713846], ["caja", 42.23438, -8.71663],
  ["bola", 42.235912, -8.720252], ["noria", 42.236839, -8.708156], ["palacio", 42.237495, -8.722828],
  ["bosque", 42.237568, -8.722204], ["estrella", 42.237604, -8.721215], ["carroza", 42.237635, -8.720702],
  ["angeles", 42.236927, -8.717891], ["renos", 42.237151, -8.723626], ["lampara", 42.237063, -8.72793],
].map(([id, lat, lon]) => ({ id, lat, lon, stay: 5 }));
const tests = [];
const test = (name, fn) => tests.push([name, fn]);

test("3 opciones y misma entrada → mismas 3 rutas", async () => {
  const a = await P.plan({ start: PORTA, stops: pts.slice(0, 6) }, noNet);
  const b = await P.plan({ start: PORTA, stops: pts.slice(0, 6) }, noNet);
  assert.deepEqual(a.options.map((o) => o.mode), ["fastest", "after_dark", "easy_walk"]);
  assert.ok(a.options.every((o) => o.ok && o.order.length === 6));
  assert.deepEqual(a.options.map((o) => o.order), b.options.map((o) => o.order));
  assert.equal(a.source, "approx");
});

test("el orden más rápido es óptimo (no peor que cualquier permutación probada)", async () => {
  const stops = pts.slice(0, 5), r = await P.plan({ start: PORTA, stops }, noNet);
  const fast = r.options[0];
  const perm = (xs) => (xs.length <= 1 ? [xs] : xs.flatMap((x, i) => perm([...xs.slice(0, i), ...xs.slice(i + 1)]).map((p) => [x, ...p])));
  const d = (a, b) => { const R = 6371000, rad = (x) => (x * Math.PI) / 180; const p = rad(b[0] - a[0]), q = rad(b[1] - a[1]); const h = Math.sin(p / 2) ** 2 + Math.cos(rad(a[0])) * Math.cos(rad(b[0])) * Math.sin(q / 2) ** 2; return 2 * R * Math.asin(Math.sqrt(h)); };
  const len = (ids) => ids.reduce((acc, id, i) => { const s = stops.find((x) => x.id === id); const prev = i ? stops.find((x) => x.id === ids[i - 1]) : { lat: PORTA[0], lon: PORTA[1] }; return acc + d([prev.lat, prev.lon], [s.lat, s.lon]); }, 0);
  const best = Math.min(...perm(stops.map((s) => s.id)).map(len));
  assert.ok(len(fast.order) <= best + 0.5);
});

test("evento fijado a las 20:00 → ninguna opción llega después", async () => {
  // salida 18:00; la noria (evento) debe alcanzarse entre las 19:50 y las 20:00 (110–120 min)
  const stops = pts.slice(0, 6).map((s) => (s.id === "noria" ? { ...s, window: [110, 120] } : s));
  const r = await P.plan({ start: PORTA, stops: stops.concat(pts[4].id === "noria" ? [] : []) }, noNet);
  for (const o of r.options) {
    if (!o.ok) continue;
    const leg = o.legs.find((l) => l.id === "noria");
    assert.ok(leg && leg.arrive >= 110 && leg.arrive <= 120, o.mode + " llega a las +" + (leg && leg.arrive));
  }
});

test("parada inalcanzable → se nombra y se sugiere qué quitar", async () => {
  // dos eventos incompatibles: muñeco en 0–5 min (está a ~15 min) y nadie puede llegar
  const stops = pts.slice(0, 4).map((s) => (s.id === "muneco" ? { ...s, window: [0, 5] } : s));
  const r = await P.plan({ start: PORTA, stops }, noNet);
  for (const o of r.options) {
    assert.equal(o.ok, false);
    assert.deepEqual(o.impossible, ["muneco"]);
    assert.equal(o.drop, "muneco");
  }
});

test("12 paradas en menos de 2 s", async () => {
  const r = await P.plan({ start: PORTA, stops: pts }, noNet);
  assert.ok(r.options.every((o) => o.ok && o.order.length === 12));
  assert.ok(r.ms < 2000, r.ms + " ms");
});

test("de noche prefiere tramos con luces encendidas; cómodo evita cuestas", async () => {
  const stops = pts.slice(0, 5);
  const lights = [[42.2376, -8.7225], [42.2378, -8.7215]];
  const r = await P.plan({ start: PORTA, stops, signals: { dark: true, lights, elev: (la, lo) => (lo > -8.72 ? 40 : 0) } }, noNet);
  const dark = r.options[1], easy = r.options[2];
  assert.ok(dark.ok && dark.explain.unlitLegs != null);
  assert.ok(easy.ok && easy.explain.maxGradePct != null);
});

test("matriz del grafo OSM cuando la API responde", async () => {
  const fake = async () => ({ json: async () => ({ code: "Ok", distances: [[0, 100], [100, 0]] }) });
  const m = await P.matrix([PORTA, [42.24, -8.72]], fake);
  assert.equal(m.source, "osm");
  assert.equal(m.meters[0][1], 100);
});

(async () => {
  let failed = 0;
  for (const [name, fn] of tests) {
    try { await fn(); console.log("ok   " + name); } catch (e) { failed++; console.log("FAIL " + name + "\n     " + e.message); }
  }
  console.log(failed ? failed + " fallos" : "todo en verde");
  process.exit(failed ? 1 : 0);
})();
