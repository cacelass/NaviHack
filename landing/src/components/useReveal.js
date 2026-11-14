import { useEffect, useRef, useState } from 'react'

// Reveal-on-scroll state shared by Reveal and the card components.
export default function useReveal(delay = 0) {
  const ref = useRef(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setVisible(true)
      return
    }
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setVisible(true)
            io.unobserve(entry.target)
          }
        })
      },
      { rootMargin: '-60px', threshold: 0 },
    )
    io.observe(el)
    return () => io.disconnect()
  }, [])

  return {
    ref,
    className: `reveal${visible ? ' is-visible' : ''}`,
    style: delay ? { '--reveal-delay': `${delay}ms` } : undefined,
  }
}
