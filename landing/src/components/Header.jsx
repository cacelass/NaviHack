import { useEffect, useState } from 'react'
import { nav } from '../data.js'

function ThemeToggle() {
  const [dark, setDark] = useState(() => document.documentElement.dataset.theme === 'dark')

  const toggle = () => {
    const next = !dark
    setDark(next)
    document.documentElement.dataset.theme = next ? 'dark' : 'light'
    try {
      localStorage.setItem('site-theme', next ? 'dark' : 'light')
    } catch {
      /* storage unavailable */
    }
  }

  return (
    <button
      className="theme-toggle"
      type="button"
      aria-label={dark ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
      aria-pressed={dark}
      title="Modo claro / oscuro"
      onClick={toggle}
    >
      <svg className="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
      </svg>
      <svg className="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
      </svg>
    </button>
  )
}

export default function Header() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <header className={`site-header${scrolled ? ' is-scrolled' : ''}`}>
      <div className="wrap header-inner">
        <a className="brand" href="#top" aria-label="NaviHack TinyVigo">
          <svg className="brand-mark" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M6.2 9.2L12 3.4L17.8 9.2" stroke="currentColor" strokeWidth="2.4" strokeLinecap="butt" strokeLinejoin="miter" />
            <path d="M1.6 19.6L12 10.8L22.4 19.6" stroke="currentColor" strokeWidth="2.4" strokeLinecap="butt" strokeLinejoin="miter" />
            <circle cx="12" cy="1.7" r="1.5" fill="#d9a441" />
          </svg>
          <span className="brand-name">NaviHack</span>
          <span className="brand-sub">/ tinyvigo</span>
        </a>

        <nav className="nav" aria-label="Navegación principal">
          {nav.map((link) => (
            <a key={link.label} href={link.href} className={link.cta ? 'nav-cta' : undefined}>
              {link.label}
            </a>
          ))}
        </nav>

        <ThemeToggle />
      </div>
    </header>
  )
}
