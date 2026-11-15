// Garlands of Christmas lights across the card, drawn as SVG: three long swags, one under the
// other, bulbs spaced evenly along each wire and hanging under gravity. Flat: no shadow, no
// gradient. Each bulb is an off glass plus a gold lit layer (with a flat halo) that fades in and
// out, so the strings twinkle without washing the colour out.
const W = 600
const H = 440

// three long garlands across the card, one under the other, never crossing: [y of both ends, depth
// of the swag, bulbs]. Different bulb counts keep the bulbs of neighbouring rows from lining up.
const X0 = -24
const X1 = W + 24
const SWAGS = [
  [26, 58, 9],
  [158, 58, 10],
  [290, 58, 9],
]

// the swag is a quadratic from (X0, y) to (X1, y) whose lowest point is `depth` below y
const quad = (y, depth, t) => {
  const cx = (X0 + X1) / 2
  const cy = y + depth * 2
  const u = 1 - t
  return {
    x: u * u * X0 + 2 * u * t * cx + t * t * X1,
    y: u * u * y + 2 * u * t * cy + t * t * y,
    slope: Math.atan2(2 * u * (cy - y) + 2 * t * (y - cy), 2 * u * (cx - X0) + 2 * t * (X1 - cx)),
  }
}

// n points spaced evenly by arc length (not by t), so the bulbs are not bunched where it is steep
function spaced(y, depth, n) {
  const pts = Array.from({ length: 241 }, (_, i) => quad(y, depth, i / 240))
  const len = [0]
  for (let i = 1; i < pts.length; i++) len.push(len[i - 1] + Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y))
  const total = len[len.length - 1]
  return Array.from({ length: n }, (_, k) => {
    const target = (total * (k + 0.5)) / n
    return pts[len.findIndex((l) => l >= target)]
  })
}

export const GLASS = 'M-6.5 6 C-12 15 -9 26 0 30 C9 26 12 15 6.5 6 Z'

// one bulb hanging from a wire: off glass, lit layer with halo, shine, cap. `rot` in degrees.
function Bulb({ x, y, rot = 0, i = 0 }) {
  return (
    <g transform={`translate(${x.toFixed(1)} ${y.toFixed(1)}) rotate(${rot.toFixed(1)})`}>
      <path className="xmas-glass" d={GLASS} />
      <g className="xmas-lit" style={{ '--i': i }}>
        <circle className="xmas-halo" cx="0" cy="17" r="20" />
        <path className="xmas-bulb" d={GLASS} />
      </g>
      <path className="xmas-shine" d="M-4 10 Q-5.5 15 -4 21" />
      <rect className="xmas-cap" x="-4.5" y="-2" width="9" height="9" rx="2" />
      <path className="xmas-ridge" d="M-4.5 1.5h9M-4.5 4.5h9" />
    </g>
  )
}

export default function ChristmasLights() {
  let bulb = 0
  return (
    <svg className="xmas" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMin slice" role="img" aria-label="Guirnaldas de luces de Navidad encendidas">
      {SWAGS.map(([y, depth, n], si) => (
        <g key={si}>
          <path className="xmas-wire" d={`M${X0} ${y} Q${(X0 + X1) / 2} ${y + depth * 2} ${X1} ${y}`} />
          {spaced(y, depth, n).map((p, i) => (
            <Bulb key={i} x={p.x} y={p.y} rot={((p.slope * 180) / Math.PI) * 0.25} i={bulb++} />
          ))}
        </g>
      ))}
    </svg>
  )
}
