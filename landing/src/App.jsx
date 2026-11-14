import Header from './components/Header.jsx'
import Hero from './components/Hero.jsx'
import Reveal from './components/Reveal.jsx'
import FeatureCard from './components/FeatureCard.jsx'
import TeamCard from './components/TeamCard.jsx'
import Footer from './components/Footer.jsx'
import { about, features, team, cta } from './data.js'

export default function App() {
  return (
    <>
      <Header />

      <main>
        <Hero />

        <section className="section" id={about.id}>
          <div className="wrap">
            <Reveal as="h2" className="section-title">
              {about.title}
            </Reveal>
            <div className="about-grid">
              {about.items.map((item, i) => (
                <Reveal as="article" className="about-card" delay={60 * i} key={item.title}>
                  <h3>{item.title}</h3>
                  <p>{item.desc}</p>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        <section className="section" id={features.id}>
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

        <section className="section" id={team.id}>
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
                <a className="btn btn-tile" href="demo/">
                  Probar demo
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
