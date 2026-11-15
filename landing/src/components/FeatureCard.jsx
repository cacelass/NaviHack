import useReveal from './useReveal.js'

// One flat card per thing the map does: the real screen on a sunk panel, then title and text.
// Its place in the bento grid comes from `item.key` (index.css, .map-card.is-<key>).
export default function FeatureCard({ item, delay = 0 }) {
  const { ref, className, style } = useReveal(delay)
  const cls = ['map-card', `is-${item.key}`, item.phone && 'is-phone', className].filter(Boolean).join(' ')

  return (
    <article ref={ref} className={cls} style={style}>
      <div className="map-media">
        {item.phone ? (
          <div className="phone phone-sm">
            <img src={item.img} alt={item.alt} loading="lazy" decoding="async" width={item.w} height={item.h} />
          </div>
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
