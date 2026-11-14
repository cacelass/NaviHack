# Objetivo — TinyVigo

> Reescrito (SCOPE-002). Fuente de verdad del producto: `docs/tinyvigo-spec.md`
> (mapa isométrico pixel art de todo el centro de Vigo). Sustituye a la spec v3
> (mapa por satélite con escenas sueltas por punto).

## Problema

En Navidad el centro de Vigo se llena de atracciones, luces y eventos, pero la
información está dispersa: el programa oficial sale a trozos, las ubicaciones
cambian de un año a otro (este año la noria se ha movido a Vialia, el Mercado
Cíes también, y hay pista de hielo y regalos gigantes) y no existe un lugar donde
ver, de un vistazo y en el móvil, qué hay cerca, si está encendido ahora, qué
ocurre hoy y cómo llegar andando o en transporte público. Los mapas existentes
(el del Concello, la prensa, los blogs) son estáticos: no cruzan horarios con tu
posición, no ordenan una ruta por horas y no cuentan por qué está ahí cada cosa.

TinyVigo lo resuelve con un mapa isométrico pixel art de todo el centro de la
ciudad, dibujado una sola vez y servido como teselas, en la familia de tiny.london,
isometric.nyc, tinygyn y tinyrj. Encima van la Navidad de Vigo (instalaciones,
mercados, atracciones y espectáculos con su horario real y una historia corta),
los eventos del día, rutas a pie que respetan horarios, autobuses y trenes, y una
postal pixel art con una foto del propio usuario. Nadie combina hoy Navidad,
rutas con ventanas horarias, eventos del día y postal con foto en un mapa
isométrico de una sola ciudad.

## Usuario / consumidor

Personas que pasean por el centro de Vigo con el móvil, de día y sobre todo por
la tarde-noche: vecinos y turistas. También quien planifica una visita corta y
quiere saber qué le cabe en 1–3 horas. Es mobile-first, de uso con una mano y a la
intemperie, de noche. Quién va primero (turistas o vecinos) está por decidir: cambia
las historias y el idioma por defecto (gallego, castellano e inglés desde el
principio).

## Criterio de hecho

v1 está "hecho" cuando se cumple todo lo siguiente. Cada punto se comprueba con un
comando o con una observación concreta:

1. **Mapa de la zona dibujado.** La zona de v1 es el núcleo de la Navidad (Porta
   do Sol, Alameda, García Barbón): unas 4x4 o 5x5 teselas, límites fijados en
   `ZONE-01`. La herramienta de estado de teselas informa de que todas están
   dibujadas y aceptadas tras revisión, con 0 teselas pendientes o marcadas para
   rehacer; lo no dibujado se ve con el render de la ortofoto, nunca como un
   hueco. El resto del centro es la extensión natural con la misma tubería, pero
   rutas, eventos, activos de Navidad y postal tienen prioridad sobre el tamaño
   del mapa. El dibujo del día es "sin luz": sol, sombras, noche y clima van por
   código, y el agua también.
2. **Navidad.** Los 43 puntos de la capa del Concello más los cambios de 2026
   aparecen como activos separados (nunca pintados en el mapa base), con horario,
   estado "encendido/abierto ahora" y tarjeta de historia con fuente; los puntos
   sin confirmar por el Concello lo dicen. Los puntos fuera de la zona dibujada se
   muestran sobre la ortofoto.
3. **Rendimiento.** En un móvil de gama media con 4G, el primer vistazo muestra
   algo reconocible en menos de 3 s y el mapa se mueve con fluidez con las capas
   por defecto (umbral propuesto: ≥30 fps, dispositivo de referencia por fijar);
   con lluvia forzada a las 21:00 mantiene esa fluidez.
4. **Rutas y eventos.** El planificador devuelve 3 opciones en menos de 2 s para
   hasta 12 paradas; el mismo dato de entrada da siempre las mismas 3 rutas; con
   un evento fijado a las 20:00 ninguna opción llega después. Se puede añadir un
   evento del día a la ruta.
5. **Transporte.** Autobuses (GTFS de Vitrasa) y trenes (GTFS de Renfe, con
   Vigo-Urzáiz y Vigo-Guixar) se ven en el mapa y dentro de las rutas, y todo
   vehículo en movimiento se etiqueta "según horario", nunca "en directo" mientras
   no haya un feed en vivo comprobado.
6. **Tiempo y hora.** La capa de clima coincide al cargar con las condiciones
   actuales de Open-Meteo para Vigo y el control de hora permite ver luces y
   clima de otra hora.
7. **Postal.** Una foto propia se convierte en una postal pixel art de un punto
   elegido, con marco, título y texto puestos por código, tope diario por
   dispositivo y tope mensual de gasto.
8. **Estado compartible.** La vista, las capas, el punto, la ruta y la hora
   viven en la URL; un enlace enviado por mensaje abre el mismo estado.

Verificable con: `./init.sh` en verde, el informe de estado de teselas, el
informe de comprobaciones automáticas por tesela, y una demo de punta a punta en
un dispositivo real con capturas de cada punto anterior.

## Fuera de alcance (v1)

- Toda el área metropolitana de Vigo, y por ahora el resto del centro fuera del
  núcleo de la Navidad: v1 dibuja la zona de `ZONE-01`.
- Posiciones GPS reales de los autobuses de Vitrasa (no se publican): solo horarios.
- Trenes "en directo" mientras no se confirme que el feed GTFS-RT de Renfe cubre Vigo.
- Datos de afluencia o colas, y cualquier estimación de "busy-now" (no existe fuente
  abierta).
- Venta de entradas, reservas, cuentas de usuario y seguimiento más allá de
  conteos de página que respeten la privacidad.
- Juegos, misiones, coleccionables, multijugador y modos pesados (vuelo, conducción).
- Cualquier cosa fuera de Vigo y de la temporada navideña.
- Dibujar con un modelo de imagen en tiempo real: el mapa se dibuja offline; lo
  único con IA en directo es la postal.
- Entrenar un modelo de estilo propio (LoRA): solo es plan B si, tras las mejoras
  de estilo, recorte de referencia y color por código, más del 30 % de las
  teselas siguen fallando en la revisión.
- Pintar las esquinas de teselas con IA (dejan manchas): se igualan por código.
- Ilustraciones de cerca de cada monumento en estilo nocturno: bonus posterior,
  no requerido para el primer lanzamiento.
