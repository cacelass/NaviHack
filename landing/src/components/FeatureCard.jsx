import useReveal from './useReveal.js'
import Phone from './Phone.jsx'
import FichaMock from './FichaMock.jsx'
import ChristmasLights from './ChristmasLights.jsx'
import TodayAgenda from './TodayAgenda.jsx'

// One flat card per thing the map does: the real screen on a sunk panel, then title and text.
// Its place in the bento grid comes from `item.key` (index.css, .map-card.is-<key>).
export default function FeatureCard({ item, delay = 0 }) {
  const { ref, className, style } = useReveal(delay)
  const cls = ['map-card', `is-${item.key}`, item.phone && 'is-phone', className].filter(Boolean).join(' ')

  return (
    <article ref={ref} className={cls} style={style}>
      {item.key === 'noche' && (
        <div className="xmas-wrap">
          <ChristmasLights />
        </div>
      )}
      {item.key === 'hoy' && (
        <div className="today-wrap">
          <TodayAgenda />
        </div>
      )}
      <div className="map-media">
        {item.key === 'noche' || item.key === 'hoy' ? null : item.key === 'ficha' ? (
          <Phone className="phone-sm"><FichaMock /></Phone>
        ) : item.phone ? (
          <Phone className="phone-sm">
            <img src={item.img} alt={item.alt} loading="lazy" decoding="async" width={item.w} height={item.h} />
          </Phone>
        ) : (
          <img src={item.img} alt={item.alt} loading="lazy" decoding="async" width={item.w} height={item.h} />
        )}
      </div>
      <div className="map-body">
        <h3>{item.title}</h3>
        <p>{item.text}</p>
      </div>
    </article>
  )
}
