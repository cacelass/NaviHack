import useReveal from './useReveal.js'
import Icon from './Icon.jsx'

export default function TeamCard({ member, delay = 0 }) {
  const { ref, className, style } = useReveal(delay)

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
          {member.portfolio && (
            <a className="link-ghost" href={member.portfolio} target="_blank" rel="noopener noreferrer">
              Portfolio
              <Icon name="external" size={14} />
            </a>
          )}
          <a
            className="link-ghost"
            href={`https://github.com/${member.github}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            GitHub
            <Icon name="external" size={14} />
          </a>
        </div>
      </div>
    </article>
  )
}
