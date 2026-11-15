import { useState } from 'react'
import { footer, site } from '../data.js'
import Icon from './Icon.jsx'

// Minimal footer: the header's own logo, three quiet columns, no rules. The credits show three names;
// «Ver más» opens the rest with their licence notes.
export default function Footer() {
  const [more, setMore] = useState(false)
  return (
    <footer className="site-footer">
      <div className="wrap">
        <div className="footer-top">
          <div className="footer-brand">
            <a className="brand" href="#top" aria-label={`${site.name}, ir al inicio`}>
              <svg className="brand-mark" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M6.4 12.2L12 7L17.6 12.2" stroke="currentColor" strokeWidth="3.6" strokeLinecap="butt" strokeLinejoin="miter" />
                <path d="M2.2 22L12 15L21.8 22" stroke="currentColor" strokeWidth="3.6" strokeLinecap="butt" strokeLinejoin="miter" />
                <circle cx="12" cy="2.15" r="1.65" fill="currentColor" />
              </svg>
              <span className="brand-name">{site.name}</span>
            </a>
            <p className="footer-blurb">{footer.blurb}</p>
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
              {(more ? footer.data : footer.data.slice(0, 3)).map((d) => (
                <li key={d.label}>
                  <a href={d.href} target="_blank" rel="noopener noreferrer">
                    {d.label}
                  </a>
                  {more && <span>{d.note}</span>}
                </li>
              ))}
            </ul>
            <button className="footer-more" type="button" aria-expanded={more} onClick={() => setMore(!more)}>
              {more ? 'Ver menos' : 'Ver más'}
              <Icon name="arrow" size={14} />
            </button>
          </div>
        </div>
      </div>
    </footer>
  )
}
