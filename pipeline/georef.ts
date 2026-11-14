// Georreferencia del mapa isométrico de Vigo: (lat, lon, z) <-> píxel del lienzo.
// Espejo de pipeline/georef.py, sin dependencias. Las constantes salen de
// render/render-params.json, que se genera desde el renderer (no se escriben aquí).
import params from "./render/render-params.json" with { type: "json" };

const rad = (deg: number): number => (deg * Math.PI) / 180;
const { camera, geo, canvases } = params;
const head = rad(camera.head_deg);
const K = Math.sin(rad(camera.tilt_deg));
const KZ = Math.cos(rad(camera.tilt_deg));
const FX = Math.sin(head);
const FY = Math.cos(head);
const RX = Math.cos(head);
const RY = -Math.sin(head);

export type CanvasName = keyof typeof canvases;
export interface Point {
  x: number;
  y: number;
}

/** (lat, lon, z en metros) -> píxel del lienzo. */
export function toPixel(lat: number, lon: number, z = 0, canvas: CanvasName = "3x3"): Point {
  const c = canvases[canvas];
  const x = (lon - geo.lon0) * geo.m_per_deg_lon;
  const y = (lat - geo.lat0) * geo.m_per_deg_lat;
  return {
    x: c.origin_x + camera.sc * (RX * x + RY * y),
    y: c.origin_y + camera.sc * (-K * (FX * x + FY * y) - KZ * z),
  };
}

/** Píxel del lienzo -> (lat, lon) del suelo (o de un tejado a altura z). */
export function toLatLon(
  px: number,
  py: number,
  z = 0,
  canvas: CanvasName = "3x3",
): { lat: number; lon: number } {
  const c = canvases[canvas];
  const u = (px - c.origin_x) / camera.sc;
  const v = (-(py - c.origin_y) / camera.sc - KZ * z) / K;
  const x = RX * u + FX * v;
  const y = RY * u + FY * v;
  return { lat: geo.lat0 + y / geo.m_per_deg_lat, lon: geo.lon0 + x / geo.m_per_deg_lon };
}

/** Coordenadas de viewport de OpenSeadragon: las dos se normalizan por el ANCHO de la imagen. */
export function toOsd(lat: number, lon: number, z = 0, canvas: CanvasName = "3x3"): Point {
  const { x, y } = toPixel(lat, lon, z, canvas);
  return { x: x / canvases[canvas].width, y: y / canvases[canvas].width };
}
