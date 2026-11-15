// NaviVigo landing content. Images are imported so Vite fingerprints and bundles them.
// Every figure here comes from the app's data (web/data/points.json, stories.json, live/parkings.json).

import shotMapa from './assets/app-mapa-1440.webp'
import shotNoche from './assets/app-noche-1600.webp'
import shotHoy from './assets/app-hoy-1440.webp'

export const site = {
  name: 'NaviVigo',
  url: 'https://navivigo.vercel.app',
  repo: 'https://github.com/cacelass/navivigo',
  readme: 'https://github.com/cacelass/navivigo/blob/main/README.md',
  demo: 'demo/',
}

export const nav = [
  { href: '#mapa', id: 'mapa', label: 'El mapa' },
  { href: '#pasear', id: 'pasear', label: 'Pasear' },
  { href: '#equipo', id: 'equipo', label: 'Quiénes' },
]

export const hero = {
  kicker: 'Navidad 2026–27 en Vigo',
  title: ['La Navidad de Vigo,', 'en un mapa'],
  text: 'Las luces del Concello, los mercados y la noria, sobre un dibujo del centro. Mira qué está encendido ahora y sal a dar un paseo que cabe en el tiempo que tienes.',
}

export const map = {
  id: 'mapa',
  title: 'Todo lo de la Navidad, en su sitio',
  intro: 'Un mapa del centro de Vigo para saber qué hay, si está abierto y cómo llegar, sin saltar de web en web.',
  items: [
    {
      key: 'mapa',
      title: 'El centro, dibujado',
      text: 'Vigo y Vialia en isométrico, calle a calle, a partir de la ortofoto del IGN. Cada punto de Navidad está donde está de verdad.',
      img: shotMapa,
      w: 1440, h: 900,
      alt: 'El mapa ilustrado del centro de Vigo con los puntos de Navidad marcados',
    },
    {
      key: 'ficha',
      title: 'Cada sitio, con su ficha',
      text: 'Horario oficial, si está encendido ahora, la historia del sitio y los minutos andando hasta él.',
      phone: true,
    },
    {
      key: 'noche',
      title: 'De noche, con sus luces',
      text: 'Al ponerse el sol se encienden las farolas y cada luz de Navidad a su hora. El Árbol de Porta do Sol brilla más en sus pases de música.',
      img: shotNoche,
      w: 1600, h: 900,
      alt: 'El mapa de noche: farolas encendidas y el Árbol de Porta do Sol iluminado',
    },
    {
      key: 'hoy',
      title: 'Lo que pasa hoy',
      text: 'El encendido, los pases del Árbol, las salidas del Nadal Bus y el tiempo de Vigo hora a hora, para saber si hace falta paraguas.',
      img: shotHoy,
      w: 1440, h: 900,
      alt: 'La agenda del día con el tiempo de Vigo y los horarios del Árbol y del Nadal Bus',
    },
  ],
}

export const walk = {
  id: 'pasear',
  title: 'Pasea por la Navidad',
  intro: 'Dices cuánto tiempo tienes y desde dónde sales. El mapa elige lo que está abierto a esa hora y te lleva parada a parada por calles reales.',
  steps: [
    { title: 'Elige el tiempo', text: 'El que tengas, de 15 minutos a 4 horas, y la hora a la que sales, con una rueda como la del móvil. Desde donde estás o desde cualquier calle.' },
    { title: 'Sigue las paradas', text: 'Cada una con su foto y lo que vas a ver. Con «Seguirme» sabes a cuántos metros estás, y la tarjeta pasa sola a la siguiente.' },
    { title: 'Llévatelo', text: 'Comparte el paseo con un enlace o ábrelo en Google Maps.' },
  ],
  tipsTitle: 'Antes de salir',
  tips: [
    { icon: 'clock', title: 'Las luces, a las 18:00', text: 'Se apagan a la 01:00, o a las 03:00 de jueves a sábado, en festivos y en sus vísperas.' },
    { icon: 'music', title: 'El Árbol suena cinco veces', text: '10 minutos de música a las 18:00, 19:00, 20:00, 21:00 y 21:50.' },
    { icon: 'moon', title: 'Ocho noches sin apagar', text: 'El 23, 24, 25, 30 y 31 de diciembre y el 1, 5 y 6 de enero el Árbol sigue encendido hasta el amanecer.' },
    { icon: 'parking', title: 'Sabe dónde aparcar', text: 'Las plazas libres de los 12 parkings públicos del centro, cada dos minutos.' },
  ],
  cta: 'Planear un paseo',
}

export const team = {
  id: 'equipo',
  title: 'Hecho por',
  text: 'Tres jóvenes de Vigo, en un solo día, en 1Hack, en A Coruña, el 14 de noviembre de 2026: un mapa para enseñar la Navidad de su ciudad.',
  more: 'Lo seguimos mejorando. El código está abierto.',
  items: [
    {
      name: 'Alejandro Cancelas',
      handle: '@cacelass',
      github: 'cacelass',
      portfolio: 'https://cacelass.github.io/',
      linkedin: 'https://www.linkedin.com/in/cacelas/',
    },
    {
      name: 'Miguel Fernández',
      handle: '@miguelfdezparis',
      github: 'miguelfdezparis',
      portfolio: 'https://miguelparis.com',
      linkedin: 'https://www.linkedin.com/in/miguel-fernandez-de-la-cigona-paris/',
    },
    {
      name: 'Jose Estévez',
      handle: '@JoseEstevez520',
      github: 'JoseEstevez520',
      portfolio: 'https://joseestevez.vercel.app/',
      linkedin: 'https://www.linkedin.com/in/jose-est%C3%A9vez-b9b761388',
    },
  ],
}

export const footer = {
  blurb: 'El mapa de la Navidad de Vigo: dónde están las luces, a qué hora se encienden y un paseo a pie a tu medida.',
  links: [
    { label: 'Abrir el mapa', href: site.demo },
    { label: 'Código en GitHub', href: site.repo, external: true },
    { label: 'README', href: site.readme, external: true },
  ],
  dataTitle: 'Datos y créditos',
  data: [
    { label: 'Concello de Vigo', note: 'datos.vigo.org (ODC-BY) y capa «Puntos de interés de Navidad 2026-27»', href: 'https://datos.vigo.org' },
    { label: 'IGN', note: 'PNOA y MDT05 © Instituto Geográfico Nacional (CC BY 4.0)', href: 'https://www.ign.es' },
    { label: 'OpenStreetMap', note: 'Calles y farolas: © colaboradores de OpenStreetMap (ODbL)', href: 'https://www.openstreetmap.org/copyright' },
    { label: 'Renfe', note: 'GTFS de Renfe Operadora (CC BY 4.0)', href: 'https://data.renfe.com' },
    { label: 'Open-Meteo', note: 'Weather data by Open-Meteo.com (CC BY 4.0)', href: 'https://open-meteo.com' },
  ],
  origin: 'Hecho en un día en 1Hack (A Coruña, 14 de noviembre de 2026).',
  disclaimer:
    'Proyecto independiente: no es una web oficial del Concello de Vigo. Las fotos de los puntos son del Concello y los derechos son de sus autores. Los horarios son orientativos: confírmalos con la organización.',
}
