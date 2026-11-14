// NaviVigo landing content. Images are imported so Vite fingerprints and bundles
// them (works at a domain root or a subpath).

import shotCentro from './assets/web-centro-1400.webp'
import shotFicha from './assets/web-ficha-390.webp'
import shotMovil from './assets/web-movil-390.webp'
import shotHoy from './assets/web-hoy-1400.webp'
import shotTour from './assets/web-tour-1400.webp'

export const site = {
  name: 'NaviVigo',
  url: 'https://navivigo.vercel.app',
  repo: 'https://github.com/cacelass/navivigo',
  readme: 'https://github.com/cacelass/navivigo/blob/main/README.md',
  demo: 'demo/',
}

export const nav = [
  { href: '#about', id: 'about', label: 'La Navidad' },
  { href: '#features', id: 'features', label: 'Qué ver' },
  { href: '#origin', id: 'origin', label: 'Origen' },
  { href: '#team', id: 'team', label: 'Equipo' },
]

export const stats = [
  { value: '35', label: 'puntos de Navidad con su horario' },
  { value: '3', label: 'paseos a pie por cada plan' },
  { value: '12', label: 'parkings con plazas en vivo' },
  { value: '3', label: 'idiomas: gallego, castellano e inglés' },
]

export const about = {
  id: 'about',
  title: 'La Navidad de Vigo',
  intro: 'Un solo mapa para saber qué hay, qué está abierto y cómo llegar, sin abrir cinco webs.',
  items: [
    {
      icon: 'map',
      title: 'Un mapa ilustrado del centro',
      desc: 'Vigo y Vialia en isométrico, con la Navidad encima: las luces del Concello, los mercados, la Noria y los 35 puntos que no te puedes perder.',
    },
    {
      icon: 'bulb',
      title: 'Luces que están encendidas',
      desc: 'Cada punto con su horario oficial y los eventos del día, para saber qué está abierto ahora y adónde acercarte cuando cae la tarde.',
    },
    {
      icon: 'phone',
      title: 'Para pasear de noche',
      desc: 'En el móvil, con una mano, mientras paseas: se entiende de un vistazo, aunque haga frío y vayas con prisa.',
    },
    {
      icon: 'database',
      title: 'Hecho con datos abiertos',
      desc: 'El Concello, el IGN, OpenStreetMap, Renfe y Open-Meteo ponen los datos. Nosotros los juntamos en un único mapa.',
    },
  ],
}

export const features = {
  id: 'features',
  title: 'Luces, sitios y planes',
  items: [
    {
      title: 'El centro, en pixel art',
      tag: 'isométrico',
      img: shotCentro,
      wide: true,
      alt: 'El mapa isométrico del centro de Vigo, con el árbol de la Puerta del Sol',
      desc: 'Un mapa del centro y de Vialia ilustrado a partir de la ortofoto del IGN. La luz cambia con la hora: de día, o de noche con las luces encendidas.',
    },
    {
      title: 'Cada sitio, con su ficha',
      tag: '35 puntos',
      img: shotFicha,
      phone: true,
      tall: true,
      alt: 'La ficha del Árbol gigante de Nadal en el móvil, con su foto y su estado',
      desc: 'El Árbol, la Noria, los mercados, el Palacio Navideño… con su foto, su horario oficial y un «Abierto · Cierra 00:30» calculado al momento.',
    },
    {
      title: 'Tu paseo a pie',
      tag: '3 rutas',
      img: shotTour,
      alt: 'El planificador de paseos con una ruta de 60 minutos sobre el mapa',
      desc: 'Dices cuánto tiempo tienes y cuándo vas, y te propone 3 paseos por lo que está abierto, trazados por calles reales.',
    },
    {
      title: 'Navidad hoy',
      tag: 'Open-Meteo',
      img: shotHoy,
      alt: 'La vista «Navidad hoy», con el tiempo de Vigo y la agenda del día',
      desc: 'Encendido de luces, pases del Árbol, lo abierto ahora y el tiempo de Vigo, para saber si te hace falta el paraguas.',
    },
    {
      title: 'Pensado para el móvil',
      tag: 'gl · es · en',
      img: shotMovil,
      phone: true,
      alt: 'El mapa de noche en el móvil, con los puntos de Navidad',
      desc: 'Mapa a pantalla completa, controles grandes y el idioma de tu navegador. Se abre sin instalar nada.',
    },
  ],
}

export const origin = {
  id: 'origin',
  title: 'Nació en 1Hack',
  text: 'Hecho por tres jóvenes de Vigo en un solo día, en 1Hack, en A Coruña, el 14 de noviembre de 2026: un mapa para enseñar la Navidad de su ciudad.',
  facts: [
    { value: '14 de noviembre de 2026' },
    { value: 'A Coruña' },
    { value: '1Hack' },
  ],
}

export const team = {
  id: 'team',
  title: 'Hecho por',
  intro: 'Tres personas y un solo proyecto. Todo vive en un único sitio, navivigo.vercel.app: una web, un mapa y una demo.',
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

export const cta = {
  id: 'cta',
  title: 'Pasea por la Navidad de Vigo',
  intro: 'Abre el mapa y recorre el centro: las luces, los sitios y los planes de esta Navidad. En el navegador, sin instalar nada.',
}

export const footer = {
  blurb: 'El mapa de la Navidad de Vigo: sitios, horarios y paseos a pie.',
  links: [
    { label: 'Probar demo', href: site.demo },
    { label: 'Código en GitHub', href: site.repo, external: true },
    { label: 'README', href: site.readme, external: true },
  ],
  dataTitle: 'Datos y créditos',
  data: [
    { label: 'Concello de Vigo', note: 'datos.vigo.org (ODC-BY) y capa «Puntos de interés de Navidad 2026-27»', href: 'https://datos.vigo.org' },
    { label: 'IGN', note: 'PNOA y MDT05 © Instituto Geográfico Nacional (CC BY 4.0)', href: 'https://www.ign.es' },
    { label: 'OpenStreetMap', note: '© colaboradores de OpenStreetMap (ODbL)', href: 'https://www.openstreetmap.org/copyright' },
    { label: 'Renfe', note: 'GTFS de Renfe Operadora (CC BY 4.0)', href: 'https://data.renfe.com' },
    { label: 'Open-Meteo', note: 'Weather data by Open-Meteo.com (CC BY 4.0)', href: 'https://open-meteo.com' },
  ],
  origin: 'Hecho en un día por tres jóvenes de Vigo en 1Hack (A Coruña, 14/11/2026).',
  disclaimer:
    'Proyecto independiente: no es una web oficial del Concello de Vigo. Las fotos de los puntos son del Concello y los derechos son de sus autores. Los horarios son orientativos: confírmalos con la organización.',
}
