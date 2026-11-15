import { useEffect, useRef, useState } from 'react'
import { nav, site } from '../data.js'

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
      className="icon-btn theme-toggle"
      type="button"
      aria-label={dark ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
      aria-pressed={dark}
      title="Modo claro / oscuro"
      onClick={toggle}
    >
      <svg className="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
      </svg>
      <svg className="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
      </svg>
    </button>
  )
}

export default function Header() {
  const [scrolled, setScrolled] = useState(false)
  const [hidden, setHidden] = useState(false)
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState('')
  const headerRef = useRef(null)
  const burgerRef = useRef(null)
  const openRef = useRef(open)
  openRef.current = open

  // Solid bar that tucks away when scrolling down and returns when scrolling up.
  useEffect(() => {
    let lastY = window.scrollY
    let ticking = false
    const update = () => {
      const y = window.scrollY
      setScrolled(y > 8)
      if (!openRef.current) {
        if (y > lastY + 6 && y > 320) setHidden(true)
        else if (y < lastY - 6 || y < 320) setHidden(false)
      }
      lastY = y
      ticking = false
    }
    const onScroll = () => {
      if (!ticking) {
        ticking = true
        requestAnimationFrame(update)
      }
    }
    update()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  // Highlight the link of the section on screen.
  useEffect(() => {
    const sections = nav.map((l) => document.getElementById(l.id)).filter(Boolean)
    if (!('IntersectionObserver' in window) || !sections.length) return
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) setActive(e.target.id)
        })
      },
      { rootMargin: '-45% 0px -50% 0px', threshold: 0 },
    )
    sections.forEach((s) => io.observe(s))
    const hero = document.getElementById('top')
    const heroIo = hero
      ? new IntersectionObserver(([e]) => e.isIntersecting && setActive(''), { rootMargin: '-45% 0px -50% 0px' })
      : null
    if (hero && heroIo) heroIo.observe(hero)
    return () => {
      io.disconnect()
      if (heroIo) heroIo.disconnect()
    }
  }, [])

  // Mobile menu: Escape and outside click close it; widening the window resets it.
  useEffect(() => {
    if (!open) return
    const onKey = (e) => {
      if (e.key === 'Escape') {
        setOpen(false)
        burgerRef.current?.focus()
      }
    }
    const onPointer = (e) => {
      if (headerRef.current && !headerRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('keydown', onKey)
    document.addEventListener('pointerdown', onPointer)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('pointerdown', onPointer)
    }
  }, [open])

  useEffect(() => {
    const mq = window.matchMedia('(min-width: 800px)')
    const onChange = () => mq.matches && setOpen(false)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])

  const cls = ['site-header', scrolled && 'is-scrolled', hidden && !open && 'is-hidden', open && 'is-open']
    .filter(Boolean)
    .join(' ')

  return (
    <header className={cls} ref={headerRef}>
      <div className="wrap header-inner">
        <a className="brand" href="#top" aria-label={`${site.name}, ir al inicio`} onClick={() => setOpen(false)}>
          <svg className="brand-mark" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M6.4 12.2L12 7L17.6 12.2" stroke="currentColor" strokeWidth="3.6" strokeLinecap="butt" strokeLinejoin="miter" />
            <path d="M2.2 22L12 15L21.8 22" stroke="currentColor" strokeWidth="3.6" strokeLinecap="butt" strokeLinejoin="miter" />
            <circle cx="12" cy="2.15" r="1.65" fill="currentColor" />
          </svg>
          <span className="brand-name">{site.name}</span>
        </a>

        <nav className="nav" aria-label="Navegación principal">
          {nav.map((link) => (
            <a key={link.id} href={link.href} className={active === link.id ? 'is-active' : undefined} aria-current={active === link.id ? 'true' : undefined}>
              {link.label}
            </a>
          ))}
        </nav>

        <a className="btn btn-gold btn-sm header-cta" href={site.demo}>
          Abrir el mapa
        </a>

        <ThemeToggle />

        <button
          ref={burgerRef}
          className="icon-btn burger"
          type="button"
          aria-label={open ? 'Cerrar menú' : 'Abrir menú'}
          aria-expanded={open}
          aria-controls="mobile-menu"
          onClick={() => setOpen((v) => !v)}
        >
          <span className="burger-lines" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
        </button>
      </div>

      <div className="mobile-menu" id="mobile-menu" aria-hidden={!open}>
        <nav className="wrap mobile-menu-inner" aria-label="Menú móvil">
          {nav.map((link, i) => (
            <a
              key={link.id}
              href={link.href}
              className={active === link.id ? 'is-active' : undefined}
              style={{ '--i': i }}
              tabIndex={open ? 0 : -1}
              onClick={() => setOpen(false)}
            >
              {link.label}
            </a>
          ))}
          <a className="btn btn-gold mobile-cta" href={site.demo} style={{ '--i': nav.length }} tabIndex={open ? 0 : -1}>
            Abrir el mapa
          </a>
        </nav>
      </div>
    </header>
  )
}
