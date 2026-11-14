// TinyVigo viewer: tiles come from tiles/<version>/ (version in tiles/current.json).
(async function () {
  const current = await (await fetch("tiles/current.json")).json();
  const base = "tiles/" + current.version + "/";
  const m = await (await fetch(base + "manifest.json")).json();

  const viewer = OpenSeadragon({
    id: "map",
    showNavigationControl: false,
    showRotationControl: false,
    gestureSettingsMouse: { clickToZoom: false },
    animationTime: 0.6,
    maxZoomPixelRatio: 6,
    homeFillsViewer: true,
    visibilityRatio: 1,
    constrainDuringPan: true,
    immediateRender: true,
    imageSmoothingEnabled: false,
    tileSources: {
      width: m.width,
      height: m.height,
      tileSize: m.tile_size,
      minLevel: m.min_level,
      maxLevel: m.max_level,
      getTileUrl: (level, x, y) => base + level + "/" + x + "_" + y + "." + m.format,
    },
  });
  // The home view covers the whole screen; it is also the farthest you can zoom out.
  const fit = (goHome) => {
    const vp = viewer.viewport;
    vp.minZoomLevel = vp.getHomeZoom();
    if (goHome) vp.goHome(true);
    vp.applyConstraints(true);
  };
  viewer.addHandler("open", () => fit(true));
  viewer.addHandler("resize", () => fit(false));
  viewer.addHandler("tile-load-failed", (e) => console.warn("tile failed", e.tile && e.tile.url, e.message));
  const zoomBy = (f) => { viewer.viewport.zoomBy(f); viewer.viewport.applyConstraints(); };
  document.getElementById("zoom-in").onclick = () => zoomBy(1.6);
  document.getElementById("zoom-out").onclick = () => zoomBy(1 / 1.6);
  window.tinyvigo = { viewer, manifest: m };
})();
