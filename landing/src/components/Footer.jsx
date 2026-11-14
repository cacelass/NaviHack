import { footer, site } from '../data.js'
import Icon from './Icon.jsx'

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="wrap">
        <div className="footer-top">
          <div className="footer-brand">
            <p className="footer-name">{site.name}</p>
            <p className="footer-blurb">{footer.blurb}</p>
            <p className="footer-origin">{footer.origin}</p>
          </div>

          <nav className="footer-col" aria-label="Enlaces">
            <h2 className="footer-heading">Proyecto</h2>
            <ul>
              {footer.links.map((link) => (
                <li key={link.label}>
                  <a href={link.href} {...(link.external ? { target: '_blank', rel: 'noopener noreferrer' } : {})}>
                    {link.label}
                    {link.external && <Icon name="external" size={14} />}
                  </a>
                </li>
              ))}
            </ul>
          </nav>

          <div className="footer-col footer-data">
            <h2 className="footer-heading">{footer.dataTitle}</h2>
            <ul>
              {footer.data.map((d) => (
                <li key={d.label}>
                  <a href={d.href} target="_blank" rel="noopener noreferrer">
                    {d.label}
                  </a>
                  <span>{d.note}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <p className="footer-disclaimer">{footer.disclaimer}</p>
      </div>
    </footer>
  )
}
