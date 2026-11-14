import Header from './components/Header.jsx'
import Hero from './components/Hero.jsx'
import Reveal from './components/Reveal.jsx'
import FeatureCard from './components/FeatureCard.jsx'
import TeamCard from './components/TeamCard.jsx'
import Footer from './components/Footer.jsx'
import Icon from './components/Icon.jsx'
import { about, features, origin, team, cta, stats, site } from './data.js'

export default function App() {
  return (
    <>
      <Header />

      <main>
        <Hero />

        <section className="stats" aria-label="NaviVigo en cifras">
          <div className="wrap">
            <ul className="stats-grid">
              {stats.map((s, i) => (
                <Reveal as="li" className="stat" delay={50 * i} key={s.label}>
                  <span className="stat-value">{s.value}</span>
                  <span className="stat-label">{s.label}</span>
                </Reveal>
              ))}
            </ul>
          </div>
        </section>

        <section className="section" id={about.id}>
          <div className="wrap">
            <Reveal as="h2" className="section-title">
              {about.title}
            </Reveal>
            <Reveal as="p" className="section-intro">
              {about.intro}
            </Reveal>
            <div className="about-grid">
              {about.items.map((item, i) => (
                <Reveal as="article" className="about-card" delay={60 * i} key={item.title}>
                  <span className="about-icon">
                    <Icon name={item.icon} size={22} />
                  </span>
                  <h3>{item.title}</h3>
                  <p>{item.desc}</p>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        <section className="section section-tint" id={features.id}>
          <div className="wrap">
            <Reveal as="h2" className="section-title">
              {features.title}
            </Reveal>
            <div className="feature-grid">
              {features.items.map((feature, i) => (
                <FeatureCard feature={feature} delay={60 * (i % 3)} key={feature.title} />
              ))}
            </div>
          </div>
        </section>

        <section className="section" id={origin.id}>
          <div className="wrap">
            <Reveal>
              <div className="origin-band">
                <p className="origin-meta">{origin.facts.map((f) => f.value).join(' · ')}</p>
                <h2 className="origin-title">{origin.title}</h2>
                <p className="origin-text">{origin.text}</p>
                <a className="origin-link" href={site.repo} target="_blank" rel="noopener noreferrer">
                  <Icon name="github" size={18} />
                  {site.repo.replace('https://github.com/', '')}
                  <Icon name="arrow" size={16} />
                </a>
              </div>
            </Reveal>
          </div>
        </section>

        <section className="section section-tint" id={team.id}>
          <div className="wrap">
            <Reveal as="h2" className="section-title">
              {team.title}
            </Reveal>
            <Reveal as="p" className="section-intro">
              {team.intro}
            </Reveal>
            <div className="team-grid">
              {team.items.map((member, i) => (
                <TeamCard member={member} delay={60 * i} key={member.name} />
              ))}
            </div>
          </div>
        </section>

        <section className="section" id={cta.id}>
          <div className="wrap">
            <Reveal>
              <div className="cta-band">
                <h2>{cta.title}</h2>
                <p>{cta.intro}</p>
                <a className="btn btn-tile btn-lg" href={site.demo}>
                  Probar demo
                  <Icon name="arrow" size={18} />
                </a>
              </div>
            </Reveal>
          </div>
        </section>
      </main>

      <Footer />
    </>
  )
}
