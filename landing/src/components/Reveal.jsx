import useReveal from './useReveal.js'

// Fades content up the first time it enters the view, like the portfolio's Reveal.
export default function Reveal({ as: Tag = 'div', delay = 0, className = '', children }) {
  const { ref, className: revealClass, style } = useReveal(delay)
  const cls = [revealClass, className].filter(Boolean).join(' ')

  return (
    <Tag ref={ref} className={cls} style={style}>
      {children}
    </Tag>
  )
}
