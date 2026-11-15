# NaviVigo — nota de entrega para el Concello

Estado a 15 de noviembre de 2026 (versión 0.1.16). Demo: <https://navivigo.vercel.app/demo/>.

## Qué hace

- **Mapa ilustrado** del centro y Vialia con los 35 puntos de Navidad del Concello, abiertos o
  cerrados según el programa oficial, y su historia, foto y horario.
- **Vista satélite** de todo Vigo con las mismas capas: puntos, eventos de la agenda, parkings con
  plazas libres, cámaras de tráfico, paradas de Vitrasa, estaciones de Renfe y tráfico.
- **Tráfico en directo** del Concello, coloreado por estado y dibujado sobre la calzada.
- **Cámaras de tráfico** con su imagen en directo dentro de la app (se refresca cada 20 s).
- **Buses y trenes:** próximas salidas de cada parada y estación, siempre marcadas «horario
  programado» (Vitrasa y Renfe no publican tiempo real).
- **Paseo a pie:** cuánto tiempo tienes y a qué hora sales; elige lo abierto, lo enruta por calles
  reales y lo cuenta parada a parada. «Cómo llegar» compara a pie, bus y coche con el tráfico del
  momento. Al llegar queda solo la ruta de Navidad, y las paradas cambian de color según avanzas.
- **Búsqueda** de puntos, eventos y cualquier calle y número.
- **Cuatro idiomas:** gallego, castellano, inglés y portugués.
- Día y noche con la puesta de sol real, tiempo de Open-Meteo, uso sin conexión y accesibilidad
  revisada (axe, teclado, objetivos táctiles de 44 px).

## Se mantiene sola

| Dato | Cómo llega | Frescura |
|---|---|---|
| Parkings, tráfico, agenda, centros, tiempo | Función de Vercel (`deploy/vercel/api/live.mjs`) contra datos.vigo.org y Open-Meteo | 1–15 min |
| Cámaras | Imagen directa de camaras.vigo.org | 20 s |
| Horarios de bus y tren | GitHub Actions los rehace cada día y los publica en la release `datos-transporte`, sin commits; la función los sirve | diaria |

Si una fuente cae, se sirve la última copia buena y la app lo indica. Pasada la semana que publica
Vitrasa, se usa el mismo día de la semana, así que nunca se queda sin buses.

## Arreglos de esta ronda

- Buses: solo 16 de 557 paradas tenían salidas y el horario guardado tenía huecos; ahora todas, y
  al día sin redesplegar.
- Capas: no aparecían hasta abrir el panel; «Ver la foto real» lo tapaba todo. Ahora cargan al
  abrir y el satélite las respeta.
- Tráfico: los tramos del Concello traen 2–3 vértices por calle y cruzaban manzanas; se encajan
  una vez sobre OpenStreetMap (`scripts/build_traffic_geom.py`).
- Mapa ilustrado: lo que va a ras de calle (tráfico, rutas, paradas, parkings, cámaras, farolas) se
  desviaba hasta 40 px porque se proyectaba con la cota del terreno y el dibujo se pintó sobre suelo
  plano. Además, en la vista isométrica las calles que pasan detrás de un edificio quedan tapadas: una
  máscara hecha con los edificios del Concello y la cámara del render (`scripts/build_occlusion.mjs`)
  evita pintar tráfico y farolas encima de los tejados, y el paseo sigue en puntos donde la calle no
  se ve.
- Cámaras: abrían una descarga «.php»; ahora la imagen sale en la app.
- Parking de Vialia ausente, fondo vacío al mover el mapa, ubicación imprecisa (ahora avisa y deja
  elegir la calle), selectores de tiempo y hora con rueda, flechas de los chips y Ajustes en móvil.

## Seguridad

- Sin claves en el repositorio ni en la web publicada; la única función de servidor solo acepta una
  lista cerrada de fuentes con URL fija (sin parámetros que lleguen a otra parte).
- Cabeceras en Vercel: CSP en la demo, `nosniff`, `Referrer-Policy`, `X-Frame-Options` y
  `Permissions-Policy` (solo geolocalización propia). HTTPS con HSTS, que pone Vercel.
- El texto que viene de fuera (GTFS, Renfe, agenda, buscador) se escapa antes de pintarse.
- La ubicación del vecino no se guarda ni se envía a servidores propios; solo va a los servicios
  de rutas y búsqueda (OSRM, Photon) cuando pide un camino.

## Pruebas

- `./init.sh`: 163 tests de Python en verde.
- `web/e2e`: 13 recorridos de vecino en escritorio y móvil (buscar, paseo, capas, cámaras, buses,
  noche/día, Ajustes, accesibilidad), también en la CI de cada push.

## Publicar

Vercel no se despliega desde GitHub: lo hace quien tenga acceso con `./landing/deploy.sh`.
