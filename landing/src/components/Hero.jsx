import baseV5 from '../assets/base-v5.webp'

export default function Hero() {
  return (
    <section className="hero" id="top">
      <img className="hero-bg" src={baseV5} alt="" aria-hidden="true" />
      <div className="hero-veil" aria-hidden="true" />

      <div className="wrap">
        <h1 className="hero-title">Conoce la Navidad de Vigo</h1>

        <p className="hero-tagline">
          Las luces, los sitios y los planes de esta Navidad, sobre un mapa pixel art del centro.{' '}
          <strong>Pasea</strong>, descubre los puntos del Concello y <strong>llévate una postal</strong>{' '}
          hecha con tu foto.
        </p>

        <div className="hero-actions">
          <a className="btn btn-gold" href="demo/">
            Probar demo
          </a>
          <a
            className="btn btn-outline"
            href="https://github.com/cacelass/NaviHack"
            target="_blank"
            rel="noopener noreferrer"
          >
            Ver repo
          </a>
        </div>
      </div>
    </section>
  )
}
