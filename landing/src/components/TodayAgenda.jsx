import Icon from './Icon.jsx'
import fotoArbol from '../assets/hoy-arbol.webp'
import fotoEstrella from '../assets/hoy-estrella.webp'
import fotoBus from '../assets/hoy-bus.webp'
import fotoBarco from '../assets/hoy-barco.webp'

// «Lo que pasa hoy»: the app's agenda rebuilt as markup. Today's date, the weather hour by hour
// with the umbrella warning, and the day's events with their real photos and times. Same content
// as the app's agenda (web/js/events.js); the panel rises from the bottom of the card, cut off.
const HOURS = [
  { h: '20h', rain: 48, wet: true },
  { h: '21h', rain: 45, wet: true },
  { h: '22h', rain: 25 },
  { h: '23h', rain: 25 },
  { h: '00h', rain: 25 },
  { h: '01h', rain: 15 },
]

const EVENTS = [
  { photo: fotoEstrella, title: 'Se encienden las luces', meta: '11 puntos de luz en el centro', times: ['18:00'], done: true },
  { photo: fotoArbol, title: 'Animación musical · 10 min', meta: 'Árbol gigante de Nadal', times: ['19:00', '20:00', '21:00', '21:50'], next: '21:00' },
  { photo: fotoBus, title: 'Nadal Bus', meta: 'Sale de Urzáiz–Príncipe · 40 min', times: ['18:30', '19:30', '20:30'], next: '20:30' },
  { photo: fotoBarco, title: 'El barco de la Navidad', meta: 'Paseo por la ría · 1 h 30 min', times: ['20:00'] },
]

const raw = new Intl.DateTimeFormat('es-ES', { weekday: 'long', day: 'numeric', month: 'long' }).format(new Date())
const today = raw.charAt(0).toUpperCase() + raw.slice(1)

export default function TodayAgenda() {
  return (
    <div className="today" role="img" aria-label="La agenda de hoy: el tiempo en Vigo hora a hora y los horarios del Árbol, del Nadal Bus y del barco">
      <div className="today-head" aria-hidden="true">
        <span className="today-title">Agenda</span>
        <span className="today-date">{today}</span>
      </div>

      <div className="today-weather" aria-hidden="true">
        <div className="today-now">
          <Icon name="cloud-rain" size={26} />
          <span className="today-temp">15°</span>
          <span className="today-sky">Lluvia</span>
        </div>
        <p className="today-warn"><Icon name="umbrella" size={15} /> Lluvia probable hacia las 20:00 (48 %). Lleva paraguas.</p>
        <ul className="today-hours">
          {HOURS.map((x) => (
            <li key={x.h} className={x.wet ? 'is-wet' : ''}>
              <span>{x.h}</span>
              <Icon name={x.wet ? 'cloud-rain' : 'cloud'} size={16} />
              <b>{x.rain} %</b>
            </li>
          ))}
        </ul>
      </div>

      <ul className="today-events" aria-hidden="true">
        {EVENTS.map((e) => (
          <li key={e.title} className={e.done ? 'is-done' : ''}>
            <img src={e.photo} alt="" width="72" height="72" loading="lazy" decoding="async" />
            <div className="today-ev-text">
              <p className="today-ev-title">{e.title}</p>
              <p className="today-ev-meta">{e.meta}</p>
            </div>
            <div className="today-times">
              {e.times.map((t) => (
                <span key={t} className={t === e.next ? 'is-next' : ''}>{t}</span>
              ))}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
