import { useEffect, useRef } from 'react'

// A minimal overlay scrollbar for the page. The native one is hidden (index.css): its track is
// always a solid strip over the page background, which shows as a white band beside the dark
// hero. This thumb floats over the content, fades out when idle and can still be dragged.
export default function ScrollBar() {
  const bar = useRef(null)
  const thumb = useRef(null)

  useEffect(() => {
    const root = document.documentElement
    let hideTimer = 0
    let drag = null

    const metrics = () => {
      const view = window.innerHeight
      const total = root.scrollHeight
      const track = bar.current.clientHeight
      const size = Math.max(44, (view / total) * track)
      const room = track - size
      const max = total - view
      return { view, total, size, room, max }
    }

    const update = () => {
      const m = metrics()
      if (m.max <= 1) {
        bar.current.hidden = true
        return
      }
      bar.current.hidden = false
      thumb.current.style.height = `${m.size}px`
      thumb.current.style.transform = `translateY(${(window.scrollY / m.max) * m.room}px)`
    }

    const wake = () => {
      bar.current.classList.add('is-awake')
      clearTimeout(hideTimer)
      hideTimer = window.setTimeout(() => {
        if (!drag) bar.current.classList.remove('is-awake')
      }, 1100)
    }

    const onScroll = () => {
      update()
      wake()
    }

    const onDown = (e) => {
      const m = metrics()
      if (e.target === thumb.current) {
        drag = { y: e.clientY, top: window.scrollY, m }
      } else {
        // click on the track: centre the thumb there
        const to = ((e.clientY - bar.current.getBoundingClientRect().top - m.size / 2) / m.room) * m.max
        window.scrollTo({ top: Math.min(m.max, Math.max(0, to)), behavior: 'instant' })
        drag = { y: e.clientY, top: window.scrollY, m }
      }
      bar.current.setPointerCapture(e.pointerId)
      bar.current.classList.add('is-drag')
      e.preventDefault()
    }

    const onMove = (e) => {
      if (!drag) return
      const to = drag.top + ((e.clientY - drag.y) / drag.m.room) * drag.m.max
      window.scrollTo({ top: Math.min(drag.m.max, Math.max(0, to)), behavior: 'instant' })
    }

    const onUp = (e) => {
      drag = null
      bar.current.classList.remove('is-drag')
      if (bar.current.hasPointerCapture(e.pointerId)) bar.current.releasePointerCapture(e.pointerId)
      wake()
    }

    const el = bar.current
    update()
    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('resize', update)
    const ro = new ResizeObserver(update)
    ro.observe(document.body)
    el.addEventListener('pointerdown', onDown)
    el.addEventListener('pointermove', onMove)
    el.addEventListener('pointerup', onUp)
    el.addEventListener('pointercancel', onUp)
    el.addEventListener('pointerenter', wake)

    return () => {
      clearTimeout(hideTimer)
      window.removeEventListener('scroll', onScroll)
      window.removeEventListener('resize', update)
      ro.disconnect()
      el.removeEventListener('pointerdown', onDown)
      el.removeEventListener('pointermove', onMove)
      el.removeEventListener('pointerup', onUp)
      el.removeEventListener('pointercancel', onUp)
      el.removeEventListener('pointerenter', wake)
    }
  }, [])

  return (
    <div className="page-scroll" ref={bar} aria-hidden="true" hidden>
      <div className="page-scroll-thumb" ref={thumb} />
    </div>
  )
}
