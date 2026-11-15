import shotPaseo from '../assets/app-paseo-390.webp'
import shotNoche from '../assets/app-noche-limpia-1200.webp'
import Reveal from './Reveal.jsx'
import Icon from './Icon.jsx'
import Phone from './Phone.jsx'
import { walk, site } from '../data.js'

// «Pasea por la Navidad»: how a walk works, told with the app's own stop pins (the numbered gold
// drop), the real walk card on a phone, and what is worth knowing before going out.
function Pin({ n }) {
  return (
    <span className="pin" aria-hidden="true">
      <svg viewBox="3.8 1.8 16.4 20.4">
        <path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0" />
      </svg>
      <span>{n}</span>
    </span>
  )
}

export default function Walk() {
  return (
    <section className="section walk" id={walk.id}>
      <div className="wrap">
        <div className="walk-grid">
          <div className="walk-copy">
            <Reveal as="h2" className="section-title">{walk.title}</Reveal>
            <Reveal as="p" className="section-intro" delay={80}>{walk.intro}</Reveal>
            <ol className="steps">
              {walk.steps.map((s, i) => (
                <Reveal as="li" className="step" delay={160 + 90 * i} key={s.title}>
                  <Pin n={i + 1} />
                  <div>
                    <h3>{s.title}</h3>
                    <p>{s.text}</p>
                  </div>
                </Reveal>
              ))}
            </ol>
            <Reveal className="walk-cta" delay={460}>
              <a className="btn btn-gold btn-lg" href={site.demo}>
                {walk.cta}
                <Icon name="arrow" size={18} />
              </a>
            </Reveal>
          </div>

          <Reveal className="walk-visual" delay={120}>
            <img className="walk-night" src={shotNoche} alt="El centro de Vigo de noche en el mapa, con las farolas y el Árbol de Porta do Sol encendidos" width="1200" height="900" loading="lazy" decoding="async" />
            <Phone className="phone-float">
              <img src={shotPaseo} alt="La tarjeta del paseo en el móvil: parada 2 de 9, Papá Noel en la Farola, a 2 minutos andando" width="780" height="1688" loading="lazy" decoding="async" />
            </Phone>
          </Reveal>
        </div>

        <Reveal as="h3" className="tips-title">{walk.tipsTitle}</Reveal>
        <ul className="tips">
          {walk.tips.map((t, i) => (
            <Reveal as="li" className="tip" delay={70 * i} key={t.title}>
              <Icon name={t.icon} size={22} className="tip-icon" />
              <h4>{t.title}</h4>
              <p>{t.text}</p>
            </Reveal>
          ))}
        </ul>
      </div>
    </section>
  )
}
