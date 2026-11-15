import Icon from './Icon.jsx'

// A phone with the real app inside. The screen starts under the status bar (clock, signal, wifi,
// battery) with the Dynamic Island in the middle of it, as on a real phone, so nothing of the app
// hides behind the island and the top is not cut flush.
export default function Phone({ className = '', children }) {
  return (
    <div className={['phone', className].filter(Boolean).join(' ')}>
      <div className="phone-screen">
        <div className="phone-status" aria-hidden="true">
          <span className="phone-time">18:30</span>
          <span className="phone-island" />
          <span className="phone-icons">
            <Icon name="signal" size={14} />
            <Icon name="wifi" size={14} />
            <Icon name="battery" size={18} />
          </span>
        </div>
        {children}
      </div>
    </div>
  )
}
