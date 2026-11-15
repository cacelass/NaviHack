import { useEffect, useRef, useState } from 'react'

// Reveal-on-scroll state shared by Reveal and the card components. Each element rises into place
// the first time it is a little way into the viewport; `delay` staggers siblings (in ms). The motion
// itself lives in CSS (.reveal), so prefers-reduced-motion just shows everything.
export default function useReveal(delay = 0) {
  const ref = useRef(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches || !('IntersectionObserver' in window)) {
      setVisible(true)
      return
    }
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true)
          io.disconnect()
        }
      },
      { rootMargin: '0px 0px -12% 0px', threshold: 0 },
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
