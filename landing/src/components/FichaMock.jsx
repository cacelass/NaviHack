import Icon from './Icon.jsx'
import shotNoria from '../assets/ficha-noria.webp'

// The app's place screen ("ficha"), rebuilt as real markup instead of a screenshot: photo, type
// and area, title, live state, official hours, distance, the two actions and what happens nearby
// today. Same content as web/ui/ficha.html, with the noria's real photo from web/data/photos.
export default function FichaMock() {
  return (
    <div className="ficha-mock">
      <div className="fm-photo">
        <img src={shotNoria} alt="La noria gigante iluminada, en Vialia" loading="lazy" decoding="async" width="480" height="270" />
      </div>

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
        <p className="fm-p">La noria cambia de sitio en 2026 y pasa a Vialia, junto al centro comercial.</p>
      </div>

    </div>
  )
}
