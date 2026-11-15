import heroBg from '../assets/hero-vigo.webp'
import shotMovil from '../assets/app-movil-390.webp'
import Icon from './Icon.jsx'
import { hero, site } from '../data.js'

// The illustrated map fills the hero; copy on the left, the real app on a phone on the right.
// On load the title rises line by line, then the text, the buttons and the phone (CSS only).
export default function Hero() {
  return (
    <section className="hero" id="top">
      <img className="hero-bg" src={heroBg} alt="" aria-hidden="true" width="1600" height="900" fetchPriority="high" decoding="async" />
      <div className="hero-veil" aria-hidden="true" />

      <div className="wrap hero-grid">
        <div className="hero-copy">
          <p className="hero-kicker load" style={{ '--load': 0 }}>{hero.kicker}</p>
          <h1 className="hero-title">
            {hero.title.map((line, i) => (
              <span className="line" key={line}>
                <span className="line-in" style={{ '--load': i + 1 }}>{line}</span>
              </span>
            ))}
          </h1>
          <p className="hero-text load" style={{ '--load': 3 }}>{hero.text}</p>
          <div className="hero-actions load" style={{ '--load': 4 }}>
            <a className="btn btn-gold btn-lg" href={site.demo}>
              Abrir el mapa
              <Icon name="arrow" size={18} />
            </a>
            <a className="btn btn-quiet btn-lg" href={site.repo} target="_blank" rel="noopener noreferrer">
              <Icon name="github" size={18} />
              Código en GitHub
            </a>
          </div>
        </div>

        <div className="hero-phone load" style={{ '--load': 5 }} aria-hidden="true">
          <div className="phone">
            <img src={shotMovil} alt="" width="780" height="1688" decoding="async" />
          </div>
        </div>
      </div>
    </section>
  )
}
