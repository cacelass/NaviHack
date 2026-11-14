export default function Hero() {
  return (
    <section className="hero" id="top">
      <div className="wrap">
        <h1 className="hero-title">
          Mapa navideño de
          <br />
          Vigo en <span className="gold">pixel art.</span>
        </h1>

        <p className="hero-tagline">
          El centro de Vigo dibujado tesela a tesela, con la Navidad del Concello encima:{' '}
          <strong>43 puntos con su horario real</strong>, los eventos del día, transporte y rutas a
          pie, y <strong>postales pixel art</strong> a partir de tu propia foto.
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
