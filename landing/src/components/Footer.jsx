import { footer } from '../data.js'

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="wrap footer-inner">
        <nav className="footer-links" aria-label="Enlaces">
          {footer.links.map((link) => (
            <a key={link.label} href={link.href} target="_blank" rel="noopener noreferrer">
              {link.label}
            </a>
          ))}
        </nav>
        <p className="footer-disclaimer">{footer.disclaimer}</p>
      </div>
    </footer>
  )
}
