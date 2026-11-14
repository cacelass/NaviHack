// NaviHack / TinyVigo landing content. Images are imported so Vite fingerprints
// and bundles them (works at a domain root or a subpath).

import shotMap from './assets/web-desktop-1400.webp'
import shotFicha from './assets/web-ficha-movil-390.webp'
import shotMovil from './assets/web-movil-390.webp'
import shotHoy from './assets/web-hoy-1400.webp'
import shotTour from './assets/web-tour-1400.webp'
import shotArbol from './assets/arbol-final-noche.webp'

export const nav = [
  { href: '#about', label: 'La Navidad' },
  { href: '#features', label: 'Qué ver' },
  { href: '#team', label: 'Equipo' },
  { href: 'demo/', label: 'Probar demo', cta: true },
]

export const about = {
  id: 'about',
  title: 'La Navidad de Vigo',
  items: [
    {
      title: 'El centro, en pixel art',
      desc: 'Vigo dibujado tesela a tesela, con su Navidad encima: las luces del Concello, el mercadillo, la pista de hielo y los 43 puntos que no te puedes perder.',
    },
    {
      title: 'Luces que están encendidas',
      desc: 'Cada punto con su horario real y los eventos del día, para saber qué hay encendido hoy y adónde acercarte cuando cae la tarde.',
    },
    {
      title: 'Para pasear de noche',
      desc: 'En el móvil, con una mano, mientras paseas: se entiende de un vistazo, aunque haga frío y vayas con prisa.',
    },
    {
      title: 'Hecho en NaviHack',
      desc: 'Un proyecto de hackathon, abierto (MIT). Los datos son del Concello, IGN, OSM, Renfe y Open-Meteo.',
    },
  ],
}

export const features = {
  id: 'features',
  title: 'Luces, sitios y planes',
  items: [
    {
      title: 'El centro en pixel art',
      tag: 'tesela a tesela',
      img: shotMap,
      alt: 'El mapa isométrico de Vigo en la vista de escritorio',
      desc: 'Un mapa isométrico del centro dibujado una sola vez. La luz y las sombras cambian con la hora: de día, o de noche con las luces.',
    },
    {
      title: 'Las luces y los sitios',
      tag: '43 puntos',
      img: shotFicha,
      alt: 'La ficha de un punto navideño con su horario',
      desc: 'El árbol, el mercadillo, la pista de hielo y los demás puntos del Concello, con su horario para saber cuándo visitarlos.',
    },
    {
      title: 'Cómo llegar',
      tag: 'Vitrasa · Renfe',
      img: shotMovil,
      alt: 'El mapa en el móvil, con el transporte visible',
      desc: 'Autobuses y trenes sobre el mapa, con su horario. Para acercarte al centro sin dar vueltas.',
    },
    {
      title: 'De día o de noche',
      tag: 'Open-Meteo',
      img: shotHoy,
      alt: 'La vista de hoy, con el clima y la hora',
      desc: 'El tiempo de Vigo y un control de hora para ver el mapa como lo vas a vivir: con luz o con las luces encendidas.',
    },
    {
      title: 'Tu paseo, a tu medida',
      tag: '3 rutas a pie',
      img: shotTour,
      alt: 'El planificador de rutas con un recorrido a pie',
      desc: 'Elige por dónde quieres pasar y te propone 3 paseos a pie, con tus paradas.',
    },
    {
      title: 'Llévate una postal',
      tag: 'con tu foto',
      img: shotArbol,
      alt: 'El árbol de Navidad en pixel art, de noche',
      desc: 'Convierte una foto tuya en una postal pixel art con los puntos navideños. Un recuerdo de tu paseo.',
    },
  ],
}

export const team = {
  id: 'team',
  title: 'Quiénes lo hicimos',
  intro: 'Un hackathon, tres demos. Cada una vive en su GitHub Pages — pruébalas.',
  items: [
    {
      name: 'Alejandro Cancelas',
      handle: '@cacelass',
      github: 'cacelass',
      portfolio: 'https://cacelass.github.io/',
    },
    {
      name: 'Miguel Fernández',
      handle: '@miguelfdezparis',
      github: 'miguelfdezparis',
      portfolio: null,
    },
    {
      name: 'Jose Estévez',
      handle: '@JoseEstevez520',
      github: 'JoseEstevez520',
      portfolio: 'https://joseestevez.vercel.app/',
    },
  ],
}

export const cta = {
  id: 'cta',
  title: 'Pasea por la Navidad de Vigo',
  intro: 'Abre el mapa y recorre el centro: las luces, los sitios y los planes de esta Navidad. En el navegador, sin instalar nada.',
}

export const footer = {
  links: [
    { label: 'GitHub repo', href: 'https://github.com/cacelass/NaviHack' },
    { label: 'README', href: 'https://github.com/cacelass/NaviHack/blob/main/README.md' },
  ],
  disclaimer:
    'Proyecto de hackathon (NaviHack). Datos del Concello de Vigo, IGN, OSM, Renfe y Open-Meteo con sus respectivas licencias.',
}
