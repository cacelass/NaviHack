# Objetivo — TinyVigo

> Rellenado por `SCOPE-001`. Fuente de verdad del producto: spec TinyVigo v3 (Part A).

## Problema

En Navidad el centro de Vigo se llena de atracciones, luces y eventos, pero la
información está dispersa: el programa oficial sale a trozos, las ubicaciones
cambian de un año a otro (este año la noria se ha movido, los puestos del
Mercado Cíes se han movido y han llegado novedades Disney) y no existe un
lugar donde ver, de un vistazo y en el móvil, qué hay cerca, si está abierto
ahora y cómo llegar andando. El resultado es que quien pasea por el centro
improvisa, se pierde puntos y no sabe si un plan le cabe en el tiempo que
tiene.

## Usuario / consumidor

Personas que pasean por el centro de Vigo con el móvil, de día y sobre todo de
noche: vecinos y turistas. También quien planifica una visita corta y quiere
saber qué le cabe en 1–3 horas. El producto es mobile-first, para uso con una
mano y a la intemperie, de noche.

## Criterio de hecho

v1 está "hecho" cuando, en un móvil de gama media y con 4G, se puede abrir el
mapa, ver los puntos navideños investigados con su horario y estado "abierto
ahora", consultar un evento del día, generar una ruta a pie de 3 opciones en
menos de 2 s para hasta 12 paradas, y crear una postal pixel-art a partir de
una foto propia. Verificable con: `./init.sh` en verde + demo end-to-end en
dispositivo real + capturas de los 6 hitos de la sección A10 del spec.

## Fuera de alcance (v1)

- Autobuses y trenes (horarios, llegadas, transbordos, paradas cercanas): Part B, v2.
- Huella de edificios y alturas (capa 3D del Concello): Part B, v1.1.
- Estimación de afluencia ("busy-now"): Part B, v2, y siempre etiquetada como estimación.
- Conteo real de gente, datos de afluencia medidos: no existe fuente abierta.
- Venta de entradas, reservas, cuentas de usuario, tracking más allá de conteos anónimos.
- Zona fuera de Vigo y fuera de la temporada navideña.
- Pintar toda la ciudad o todos los edificios como pixel art (solo escenas por punto).
- Generación de escenas en tiempo real al tocar un punto (se generan offline).
- Datos en tiempo real de Vitrasa (no existe feed oficial abierto).
EOF
echo written