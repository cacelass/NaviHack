// Fetch IGN orthophoto chunks and Concello buildings for the 3x3 block area
import fs from 'fs';
const cLat = 42.23807, cLon = -8.72581;
const mLat = 111320, mLon = 111320 * Math.cos(cLat * Math.PI / 180);
const HX = 1100, HY = 1360, RES = 0.4;
const S = cLat - HY / mLat, N = cLat + HY / mLat, W = cLon - HX / mLon, E = cLon + HX / mLon;
fs.mkdirSync('work/ortho', { recursive: true });
fs.writeFileSync('work/ortho.bbox', `${S} ${W} ${N} ${E}\n`);
const NX = 4, NY = 5;
const W_PX = Math.round(2 * HX / RES), H_PX = Math.round(2 * HY / RES);
console.log('full px', W_PX, H_PX);
for (let ix = 0; ix < NX; ix++) for (let iy = 0; iy < NY; iy++) {
  const f = `work/ortho/o_${ix}_${iy}.jpg`; if (fs.existsSync(f)) continue;
  const w = W + (E - W) * ix / NX, e = W + (E - W) * (ix + 1) / NX, s = S + (N - S) * iy / NY, n = S + (N - S) * (iy + 1) / NY;
  const pw = Math.round(W_PX / NX), ph = Math.round(H_PX / NY);
  const url = `https://www.ign.es/wms-inspire/pnoa-ma?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=OI.OrthoimageCoverage&STYLES=&CRS=EPSG:4326&BBOX=${s},${w},${n},${e}&WIDTH=${pw}&HEIGHT=${ph}&FORMAT=image/jpeg`;
  let ok = false;
  for (let i = 0; i < 5 && !ok; i++) {
    try { const r = await fetch(url, { headers: { 'User-Agent': 'VigoPixelMap/1.0' } }); const b = Buffer.from(await r.arrayBuffer());
      if (b[0] === 0xff && b[1] === 0xd8) { fs.writeFileSync(f, b); console.log(ix, iy, b.length); ok = true; } else console.log('bad', r.status, b.length, b.toString().slice(0, 200)); }
    catch (e) { console.log('err', e.message); }
    if (!ok) await new Promise(r => setTimeout(r, 2000));
  }
  if (!ok) throw new Error('fail ' + ix + iy);
}
