import Icon from './Icon.jsx'

// The app's place screen ("ficha"), rebuilt as real markup instead of a screenshot: type and
// area, title, live state, official hours, distance, the two actions, the story with its source
// and what happens nearby today. Same content as web/ui/ficha.html, from web/data/stories.json.
export default function FichaMock() {
  return (
    <div className="ficha-mock">
      <div className="fm-top">
        <div>
          <p className="fm-type">Atracciones · Vialia</p>
          <h4 className="fm-title">Noria gigante</h4>
        </div>
        <span className="fm-close" aria-hidden="true"><Icon name="x" size={12} /></span>
      </div>

      <p className="fm-state is-on"><Icon name="circle-check" size={14} /> Abierto ahora, hasta las <b>22:30</b></p>
      <p className="fm-hours">Laborables de 17:00 a 22:30<small>Cambia del 21 de diciembre al 12 de enero</small></p>
      <p className="fm-meta"><Icon name="footprints" size={12} /> 11 min andando desde Porta do Sol</p>

      <div className="fm-actions">
        <span className="fm-btn is-sec"><Icon name="pin" size={12} /> Cómo llegar</span>
        <span className="fm-btn is-pri"><Icon name="route" size={12} /> A la ruta</span>
      </div>

      <div className="fm-story">
        <p className="fm-h">Historia</p>
        <p className="fm-p">La noria cambia de sitio en 2026 y pasa a Vialia. La información viene de la prensa local y el Concello aún no la ha confirmado.</p>
        <p className="fm-src">Prensa local, sin confirmar por el Concello</p>
      </div>

      <div className="fm-near">
        <p className="fm-h">Cerca de aquí hoy</p>
        <div className="fm-ev"><span className="fm-ev-time">19:30</span><div><p className="fm-ev-title">Desfile de los Reyes Magos</p><p className="fm-ev-meta">Rúa do Príncipe · 3 min</p></div></div>
        <div className="fm-ev"><span className="fm-ev-time">20:00</span><div><p className="fm-ev-title">Pase de música y luz</p><p className="fm-ev-meta">En este punto</p></div></div>
      </div>
    </div>
  )
}
