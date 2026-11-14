import useReveal from './useReveal.js'
import Icon from './Icon.jsx'

export default function TeamCard({ member, delay = 0 }) {
  const { ref, className, style } = useReveal(delay)
  const links = [
    { kind: 'github', icon: 'github', label: 'GitHub', href: `https://github.com/${member.github}` },
    member.linkedin && { kind: 'linkedin', icon: 'linkedin', label: 'LinkedIn', href: member.linkedin },
    member.portfolio && { kind: 'portfolio', icon: 'globe', label: 'Portfolio', href: member.portfolio },
  ].filter(Boolean)

  return (
    <article ref={ref} className={`team-card ${className}`} style={style}>
      <img
        className="team-avatar"
        src={`https://github.com/${member.github}.png`}
        alt={`Foto de perfil de ${member.name}`}
        width="52"
        height="52"
        loading="lazy"
      />
      <div className="team-info">
        <h3>{member.name}</h3>
        <p className="team-handle">{member.handle}</p>
        <div className="team-links">
          {links.map((l) => (
            <a
              className={`team-link is-${l.kind}`}
              href={l.href}
              target="_blank"
              rel="noopener noreferrer"
              key={l.kind}
              aria-label={`${l.label} de ${member.name}`}
              data-tip={l.label}
            >
              <Icon name={l.icon} size={20} />
            </a>
          ))}
        </div>
      </div>
    </article>
  )
}
