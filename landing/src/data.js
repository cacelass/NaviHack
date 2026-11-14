// NaviHack / TinyVigo landing content. Images are imported so Vite fingerprints
// and bundles them (works at a domain root or a subpath).

import shotMap from './assets/web-desktop-1400.webp'
import shotFicha from './assets/web-ficha-movil-390.webp'
import shotMovil from './assets/web-movil-390.webp'
import shotHoy from './assets/web-hoy-1400.webp'
import shotTour from './assets/web-tour-1400.webp'
import shotArbol from './assets/arbol-final-noche.webp'

export const nav = [
  { href: '#about', label: 'El proyecto' },
  { href: '#features', label: 'Funciones' },
  { href: '#team', label: 'Equipo' },
  { href: 'demo/', label: 'Probar demo', cta: true },
]

export const about = {
  id: 'about',
  title: 'El mapa de la Navidad en Vigo',
  items: [
    {
      title: 'Qué es',
      desc: 'El centro de Vigo en un mapa isométrico pixel art, con la capa navideña del Concello encima: 43 puntos con horario real, eventos del día y rutas a pie.',
    },
    {
      title: 'Para quién',
      desc: 'Para quien pasea el centro con el móvil, de día o de noche — vecinos y turistas — y para quien planea una visita corta de 1 a 3 horas.',
    },
    {
      title: 'Cómo se usa',
      desc: 'Con una mano, a la intemperie, de noche. Mobile-first: el primer vistazo se entiende en menos de 3 segundos en un móvil de gama media con 4G.',
    },
    {
      title: 'Estado',
      desc: 'Proyecto de hackathon (NaviHack), abierto bajo licencia MIT. Los datos traen sus propias licencias: Concello, IGN, OSM, Renfe y Open-Meteo.',
    },
  ],
}

export const features = {
  id: 'features',
  title: 'Qué hay dentro',
  items: [
    {
      title: 'Mapa isométrico',
      tag: '4×4 / 5×5 teselas',
      img: shotMap,
      alt: 'El mapa isométrico de Vigo en la vista de escritorio',
      desc: 'El centro de Vigo dibujado una sola vez, tesela a tesela. La luz, las sombras, la noche y el clima se pintan por código sobre el mapa.',
    },
    {
      title: 'Puntos navideños',
      tag: '43 puntos del Concello',
      img: shotFicha,
      alt: 'La ficha de un punto navideño con su horario',
      desc: 'El árbol, el mercadillo, la pista de hielo: los 43 puntos del Concello con su horario real, etiquetados «según horario», nunca «en directo».',
    },
    {
      title: 'Transporte',
      tag: 'Vitrasa · Renfe',
      img: shotMovil,
      alt: 'El mapa en el móvil, con el transporte visible',
      desc: 'Autobuses y trenes visibles sobre el mapa, con su horario. Para llegar al centro sin dar vueltas.',
    },
    {
      title: 'Clima y hora',
      tag: 'Open-Meteo',
      img: shotHoy,
      alt: 'La vista de hoy, con el clima y la hora',
      desc: 'El tiempo real de Vigo y un control de hora para ver el mapa de día o de noche, como lo vives.',
    },
    {
      title: 'Planificador',
      tag: '3 opciones · rutas a pie',
      img: shotTour,
      alt: 'El planificador de rutas con un recorrido a pie',
      desc: 'Dile por dónde quieres pasar y te devuelve 3 rutas a pie en menos de 2 segundos, hasta 12 paradas.',
    },
    {
      title: 'Postal pixel art',
      tag: 'con tu foto',
      img: shotArbol,
      alt: 'El árbol de Navidad en pixel art, de noche',
      desc: 'Convierte una foto tuya en una postal pixel art con los puntos navideños. El recuerdo, listo para compartir.',
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
  title: 'Probar la demo',
  intro: 'Mapa interactivo con los puntos navideños de Vigo. Funciona en el navegador, sin instalar nada.',
}

export const footer = {
  links: [
    { label: 'GitHub repo', href: 'https://github.com/cacelass/NaviHack' },
    { label: 'README', href: 'https://github.com/cacelass/NaviHack/blob/main/README.md' },
  ],
  disclaimer:
    'Proyecto de hackathon (NaviHack). Datos del Concello de Vigo, IGN, OSM, Renfe y Open-Meteo con sus respectivas licencias.',
}
