// Prueba la proyección del mapa (web/js/tour.js) sin navegador: nodo con stubs mínimos.
// Uso: node scripts/test_web_geo.mjs
import fs from "node:fs";
import vm from "node:vm";
import assert from "node:assert";

const code = fs.readFileSync(new URL("../web/js/tour.js", import.meta.url), "utf8");
const sandbox = {
  window: { addEventListener() {}, tinyvigoPoints: null },
  document: { addEventListener() {}, dispatchEvent() {}, createElement: () => ({ set innerHTML(v) {}, append() {}, get firstChild() { return null; } }) },
  fetch: () => new Promise(() => {}), // nunca resuelve: la elevación no carga
  CustomEvent: class {},
  console,
  Math,
};
vm.createContext(sandbox);
vm.runInContext(code, sandbox);
const { project, unproject } = sandbox.window.tinyvigoGeo;

// el origen del lienzo es el Árbol de Porta do Sol
const [cx, cy] = project(42.238072, -8.725813);
assert.ok(Math.abs(cx - 1536) < 0.5, `centro x: ${cx}`);
assert.ok(Math.abs(cy - 1536) < 0.5, `centro y: ${cy}`);

// ida y vuelta en puntos repartidos por el centro de Vigo (sin elevación cargada)
const pts = [
  [42.238072, -8.725813],
  [42.236839, -8.708156],
  [42.234745, -8.711343],
  [42.2315, -8.7239],
  [42.2402, -8.7171],
];
for (const [lat, lon] of pts) {
  const [x, y] = project(lat, lon);
  const [la, lo] = unproject(x, y);
  assert.ok(Math.abs(la - lat) < 1e-9, `lat ${lat} -> ${la}`);
  assert.ok(Math.abs(lo - lon) < 1e-9, `lon ${lon} -> ${lo}`);
}

// una ida y vuelta arbitraria en coordenadas del lienzo
const [ax, ay] = [1200, 2100];
const [alat, alon] = unproject(ax, ay);
const [bx, by] = project(alat, alon);
assert.ok(Math.abs(bx - ax) < 0.01 && Math.abs(by - ay) < 0.01, `lienzo ${ax},${ay} -> ${bx},${by}`);

console.log("OK proyección: centro y 5 puntos ida/vuelta sin error");
