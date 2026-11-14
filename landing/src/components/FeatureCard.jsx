import useReveal from './useReveal.js'

export default function FeatureCard({ feature, delay = 0 }) {
  const { ref, className, style } = useReveal(delay)

  return (
    <article ref={ref} className={`feature-card ${className}`} style={style}>
      <div className="feature-media">
        <img src={feature.img} alt={feature.alt} loading="lazy" width="1400" height="1050" />
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
