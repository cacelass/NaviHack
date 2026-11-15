// Máscara de «suelo tapado» del mapa dibujado (GEO-02): web/data/layers/occlusion.png
//
// En la vista isométrica una calle que pasa por detrás de un edificio no se ve: la tapa el edificio.
// Una línea dibujada a ras de suelo (tráfico, ruta) sale entonces pintada encima de tejados y fachadas.
// Aquí se rasterizan los edificios del Concello con su altura y la misma cámara del render del que sale
// el dibujo (pipeline/render/templates/render.html: suelo plano, prisma de 0 a max(3, h || 6) m), y se
// guarda qué píxeles del lienzo cubren. La web corta las líneas donde el suelo queda tapado.
//
// PNG en blanco y negro de 1 bit a media resolución (1 px = 2 px del lienzo). Sin dependencias.
//
//     node scripts/build_occlusion.mjs
import { readFileSync, writeFileSync } from "node:fs";
import { deflateSync } from "node:zlib";
import { fileURLToPath } from "node:url";

const ROOT = fileURLToPath(new URL("..", import.meta.url));
const SOURCES = ["pipeline/render/original/edificios_concello.json", "pipeline/render/original/edificios_este.json"];
const OUT = ROOT + "web/data/layers/occlusion.png";
const MANIFEST = JSON.parse(readFileSync(ROOT + "web/tiles/" + JSON.parse(readFileSync(ROOT + "web/tiles/current.json", "utf8")).version + "/manifest.json", "utf8"));
const W = MANIFEST.width / 2, H = MANIFEST.height / 2; // media resolución

// la cámara de web/js/tour.js (project) y de pipeline/render/render-params.json
const ORIGIN = [42.238072, -8.725813], MLAT = 111320, rad = (d) => (d * Math.PI) / 180;
const HEAD = rad(-15), TILT = Math.PI / 4, SCALE = 2, C = 1536;
function project(lat, lon, z) {
  const x = (lon - ORIGIN[1]) * MLAT * Math.cos(rad(ORIGIN[0])), y = (lat - ORIGIN[0]) * MLAT;
  const u = Math.cos(HEAD) * x - Math.sin(HEAD) * y, d = Math.sin(HEAD) * x + Math.cos(HEAD) * y;
  return [(C + SCALE * u) / 2, (C + SCALE * (-Math.sin(TILT) * d - Math.cos(TILT) * z)) / 2];
}

const mask = new Uint8Array(W * H);
// relleno de un polígono por barrido (par-impar), muestreando el centro de cada píxel
function fill(poly) {
  let y0 = Infinity, y1 = -Infinity;
  for (const [, y] of poly) { y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
  y0 = Math.max(0, Math.ceil(y0 - 0.5)); y1 = Math.min(H - 1, Math.floor(y1 - 0.5));
  const xs = [];
  for (let row = y0; row <= y1; row++) {
    const yc = row + 0.5;
    xs.length = 0;
    for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      const [xa, ya] = poly[i], [xb, yb] = poly[j];
      if ((ya > yc) !== (yb > yc)) xs.push(xa + ((yc - ya) / (yb - ya)) * (xb - xa));
    }
    xs.sort((a, b) => a - b);
    for (let k = 0; k + 1 < xs.length; k += 2) {
      const a = Math.max(0, Math.ceil(xs[k] - 0.5)), b = Math.min(W - 1, Math.floor(xs[k + 1] - 0.5));
      mask.fill(1, row * W + a, row * W + b + 1);
    }
  }
}

let n = 0;
for (const src of SOURCES) {
  for (const b of JSON.parse(readFileSync(ROOT + src, "utf8"))) {
    const ring = b.rings && b.rings[0];
    if (!ring || ring.length < 3) continue;
    const h = Math.max(3, b.h || 6);
    const base = ring.map(([lon, lat]) => project(lat, lon, 0)), top = ring.map(([lon, lat]) => project(lat, lon, h));
    if (top.every(([x, y]) => x < 0 || y < 0 || x >= W || y >= H) && base.every(([x, y]) => x < 0 || y < 0 || x >= W || y >= H)) continue;
    fill(base); fill(top);
    for (let i = 0; i + 1 < ring.length; i++) fill([base[i], base[i + 1], top[i + 1], top[i]]);
    n++;
  }
}

// PNG gris de 1 bit
const stride = Math.ceil(W / 8), raw = Buffer.alloc((stride + 1) * H);
for (let y = 0; y < H; y++) {
  const o = y * (stride + 1);
  for (let x = 0; x < W; x++) if (mask[y * W + x]) raw[o + 1 + (x >> 3)] |= 0x80 >> (x & 7);
}
const crcTable = Array.from({ length: 256 }, (_, k) => { let c = k; for (let i = 0; i < 8; i++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; return c >>> 0; });
const crc = (buf) => { let c = 0xffffffff; for (const v of buf) c = crcTable[(c ^ v) & 0xff] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; };
const chunk = (type, data) => {
  const len = Buffer.alloc(4); len.writeUInt32BE(data.length);
  const body = Buffer.concat([Buffer.from(type, "ascii"), data]), sum = Buffer.alloc(4); sum.writeUInt32BE(crc(body));
  return Buffer.concat([len, body, sum]);
};
const ihdr = Buffer.alloc(13);
ihdr.writeUInt32BE(W, 0); ihdr.writeUInt32BE(H, 4); ihdr[8] = 1; ihdr[9] = 0; // 1 bit, gris
const png = Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), chunk("IHDR", ihdr), chunk("IDAT", deflateSync(raw, { level: 9 })), chunk("IEND", Buffer.alloc(0))]);
writeFileSync(OUT, png);
const covered = mask.reduce((a, v) => a + v, 0);
console.log(`${n} edificios · ${W}x${H} · ${((100 * covered) / mask.length).toFixed(1)} % tapado · ${(png.length / 1024).toFixed(0)} KB`);
