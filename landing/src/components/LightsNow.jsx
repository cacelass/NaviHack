import { useEffect, useState } from 'react'
import Icon from './Icon.jsx'
import { site } from '../data.js'

// The closing line says what is true right now, from the Concello's lights schedule
// (data/programme_2026.json, template «lights»): from 14 Nov 2026, on at 18:00, off at 01:00
// Sunday–Wednesday and at 03:00 Thursday–Saturday; eight nights stay on till dawn. The Concello
// publishes no end date: after Reyes (6 Jan) the line stops promising anything.
const START = new Date(2026, 10, 14, 18)
const END = new Date(2027, 0, 7, 9)
const ALL_NIGHT = ['2026-12-23', '2026-12-24', '2026-12-25', '2026-12-30', '2026-12-31', '2027-01-01', '2027-01-05', '2027-01-06']
const ymd = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

function state(now) {
  if (now < START) return { on: false, text: 'Las luces se encienden el 14 de noviembre a las 18:00' }
  if (now > END) return { on: false, text: 'Las luces de esta Navidad ya se apagaron' }
  const h = now.getHours() + now.getMinutes() / 60
  const yesterday = new Date(now); yesterday.setDate(now.getDate() - 1)
  if ((h >= 18 && ALL_NIGHT.includes(ymd(now))) || (h < 9 && ALL_NIGHT.includes(ymd(yesterday)))) return { on: true, text: 'Encendidas ahora, toda la noche' }
  const late = [4, 5, 6].includes(now.getDay()) // jue, vie, sáb
  const prevLate = [5, 6, 0].includes(now.getDay()) // la madrugada de vie, sáb y dom
  const offAfterMidnight = prevLate ? 3 : 1
  if (h >= 18) return { on: true, text: `Encendidas ahora, hasta las ${late ? '03:00' : '01:00'}` }
  if (h < offAfterMidnight) return { on: true, text: `Encendidas ahora, hasta las 0${offAfterMidnight}:00` }
  const mins = Math.round((18 - h) * 60)
  const hh = Math.floor(mins / 60), mm = mins % 60
  return { on: false, text: `Se encienden hoy a las 18:00, dentro de ${hh ? `${hh} h ` : ''}${mm} min` }
}

export default function LightsNow() {
  const [now, setNow] = useState(() => new Date())
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 60000)
    return () => clearInterval(t)
  }, [])
  const s = state(now)

  return (
    <section className="lights-now" aria-labelledby="lights-now-title">
      <div className="wrap lights-now-inner">
        <p className={`lights-state${s.on ? ' is-on' : ''}`}>
          <span className="lights-dot" aria-hidden="true" />
          {s.text}
        </p>
        <h2 id="lights-now-title">Esta Navidad, sal a verla.</h2>
        <a className="btn btn-gold btn-lg" href={site.demo}>
          Abrir el mapa
          <Icon name="arrow" size={18} />
        </a>
      </div>
    </section>
  )
}
