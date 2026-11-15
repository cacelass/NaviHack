// TinyVigo: qué suelo del mapa dibujado queda tapado por un edificio (GEO-02).
// data/layers/occlusion.png lo genera scripts/build_occlusion.mjs con los edificios del Concello y la
// cámara del render: 1 bit por píxel, a media resolución del lienzo. Lo que va a ras de calle (tráfico,
// ruta, farolas) no se pinta encima de un edificio que tapa la calle.
(function () {
  let bits = null, W = 0, H = 0;
  const ready = fetch("data/layers/occlusion.png")
    .then((r) => (r.ok ? r.blob() : Promise.reject(new Error("sin máscara"))))
    .then((b) => createImageBitmap(b))
    .then((bm) => {
      W = bm.width; H = bm.height;
      const c = Object.assign(document.createElement("canvas"), { width: W, height: H }), g = c.getContext("2d");
      g.drawImage(bm, 0, 0);
      const d = g.getImageData(0, 0, W, H).data;
      bits = new Uint8Array(W * H);
      for (let i = 0; i < bits.length; i++) bits[i] = d[i * 4] > 127 ? 1 : 0;
    })
    .catch(() => {}); // sin máscara todo se ve, como antes

  // (x, y) en píxeles del lienzo
  const hidden = (x, y) => {
    if (!bits) return false;
    const i = Math.floor(x / 2), j = Math.floor(y / 2);
    return i >= 0 && j >= 0 && i < W && j < H && bits[j * W + i] === 1;
  };

  // una polilínea en píxeles del lienzo -> los tramos que se ven, cada uno como lista de puntos.
  // Se muestrea cada 3 px; huecos y trozos de menos de 8 px no cuentan (bordes de la máscara).
  function visibleRuns(pts) {
    if (!bits || pts.length < 2) return [pts];
    const samples = [];
    for (let k = 1; k < pts.length; k++) {
      const [x0, y0] = pts[k - 1], [x1, y1] = pts[k], n = Math.max(1, Math.ceil(Math.hypot(x1 - x0, y1 - y0) / 3));
      for (let s = k === 1 ? 0 : 1; s <= n; s++) { const x = x0 + ((x1 - x0) * s) / n, y = y0 + ((y1 - y0) * s) / n; samples.push([x, y, hidden(x, y)]); }
    }
    // huecos cortos (menos de 3 muestras) se cierran: son esquinas de la máscara, no edificios
    for (let i = 0; i < samples.length; ) {
      if (!samples[i][2]) { i++; continue; }
      let j = i; while (j < samples.length && samples[j][2]) j++;
      if (j - i < 3 && i > 0 && j < samples.length) for (let k = i; k < j; k++) samples[k][2] = false;
      i = j;
    }
    const runs = []; let cur = [];
    for (const [x, y, h] of samples) {
      if (!h) cur.push([x, y]);
      else if (cur.length) { runs.push(cur); cur = []; }
    }
    if (cur.length) runs.push(cur);
    return runs.filter((r) => r.length >= 3);
  }

  window.tinyvigoOcclusion = { ready, hidden, visibleRuns };
})();
