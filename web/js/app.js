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
    minZoomImageRatio: 0.9,
    maxZoomPixelRatio: 6,
    visibilityRatio: 0.6,
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
  viewer.addHandler("open", () => viewer.viewport.goHome(true));
  viewer.addHandler("tile-load-failed", (e) => console.warn("tile failed", e.tile && e.tile.url, e.message));
  window.tinyvigo = { viewer, manifest: m };
})();
