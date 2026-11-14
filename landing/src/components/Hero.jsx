import heroBg from '../assets/hero-vigo.webp'
import shotFicha from '../assets/web-ficha-390.webp'
import Icon from './Icon.jsx'
import { site } from '../data.js'

export default function Hero() {
  return (
    <section className="hero" id="top">
      <img className="hero-bg" src={heroBg} alt="" aria-hidden="true" width="1920" height="1080" fetchPriority="high" decoding="async" />
      <div className="hero-veil" aria-hidden="true" />

      <div className="wrap hero-grid">
        <div className="hero-copy">

          <h1 className="hero-title">Conoce la Navidad de Vigo</h1>

          <p className="hero-tagline">
            Las luces, los sitios y los planes de esta Navidad, sobre un mapa ilustrado del centro. <strong>Pasea</strong>,
            descubre los puntos del Concello y mira <strong>qué está abierto ahora</strong>.
          </p>

          <div className="hero-actions">
            <a className="btn btn-gold btn-lg" href={site.demo}>
              Probar demo
              <Icon name="arrow" size={18} />
            </a>
            <a className="btn btn-outline btn-lg" href={site.repo} target="_blank" rel="noopener noreferrer">
              <Icon name="github" size={18} />
              Ver código
            </a>
          </div>

          <ul className="hero-points" aria-label="Lo esencial">
            <li>Gratis</li>
            <li>En el navegador</li>
            <li>Datos abiertos</li>
          </ul>
        </div>

        <div className="hero-phone" aria-hidden="true">
          <div className="phone">
            <img src={shotFicha} alt="" width="780" height="1130" decoding="async" />
          </div>
        </div>
      </div>

      <a className="hero-scroll" href="#about" aria-label="Bajar a la siguiente sección">
        <span />
      </a>
    </section>
  )
}
