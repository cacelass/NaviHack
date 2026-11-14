import useReveal from './useReveal.js'

export default function FeatureCard({ feature, delay = 0 }) {
  const { ref, className, style } = useReveal(delay)
  const cls = ['feature-card', feature.wide && 'is-wide', feature.phone && 'is-phone', feature.tall && 'is-tall', className].filter(Boolean).join(' ')

  return (
    <article ref={ref} className={cls} style={style}>
      <div className="feature-media">
        <img
          src={feature.img}
          alt={feature.alt}
          loading="lazy"
          decoding="async"
          width={feature.phone ? 780 : 1400}
          height={feature.phone ? 1130 : feature.wide ? 1050 : 900}
        />
      </div>
      <div className="feature-body">
        <div className="feature-head">
          <h3>{feature.title}</h3>
          <span className="feature-tag">{feature.tag}</span>
        </div>
        <p>{feature.desc}</p>
      </div>
    </article>
  )
}
