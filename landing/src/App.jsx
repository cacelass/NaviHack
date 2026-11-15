import { Analytics } from '@vercel/analytics/react'
import Header from './components/Header.jsx'
import Hero from './components/Hero.jsx'
import Reveal from './components/Reveal.jsx'
import FeatureCard from './components/FeatureCard.jsx'
import Walk from './components/Walk.jsx'
import TeamCard from './components/TeamCard.jsx'
import LightsNow from './components/LightsNow.jsx'
import Footer from './components/Footer.jsx'
import Icon from './components/Icon.jsx'
import { map, team, site } from './data.js'

export default function App() {
  return (
    <>
      <Header />

      <main>
        <Hero />

        <section className="section" id={map.id}>
          <div className="wrap">
            <div className="section-head">
              <Reveal as="h2" className="section-title">{map.title}</Reveal>
              <Reveal as="p" className="section-intro" delay={80}>{map.intro}</Reveal>
            </div>
            <div className="bento">
              {map.items.map((item, i) => (
                <FeatureCard item={item} delay={90 * (i % 2)} key={item.key} />
              ))}
            </div>
          </div>
        </section>

        <Walk />

        <section className="section team" id={team.id}>
          <div className="wrap">
            <div className="team-grid-wrap">
              <div className="team-copy">
                <Reveal as="h2" className="section-title">{team.title}</Reveal>
                <Reveal as="p" className="team-text" delay={80}>{team.text}</Reveal>
                <Reveal as="p" className="team-more" delay={140}>
                  {team.more}{' '}
                  <a href={site.repo} target="_blank" rel="noopener noreferrer">
                    <Icon name="github" size={16} />
                    {site.repo.replace('https://github.com/', '')}
                  </a>
                </Reveal>
              </div>
              <ul className="team-grid">
                {team.items.map((member, i) => (
                  <li key={member.name}>
                    <TeamCard member={member} delay={90 * i} />
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        <LightsNow />
      </main>

      <Footer />
      <Analytics />
    </>
  )
}
