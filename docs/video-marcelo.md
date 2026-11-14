# Vídeo de Thomas Marcelo (tinygyn / tinyrj) — problemas y método

Transcripción automática (EN) de https://youtu.be/OeYzRevuSCQ, descargada con yt-dlp.
Es la fuente de los problemas comunes del mapa isométrico por teselas y de cómo resolverlos.
Resumen propio, no una cita literal.

## El método (pasos)

1. **Render.** Cámara ortográfica 45° inclinada y girada, tiles de 1024 px, ~0,3 m/pixel.
   Cada tile sale del modelo 3D. El render es "feo" (árboles derretidos, tejados emborronados):
   pasarlo a dibujo es todo el juego.
2. **Dibujo.** Modelo frontier (sin entrenar), tile a tile. Entrada: render + descripción del
   estilo + referencia de estilo + tiles ya dibujados. El prompt es donde va casi todo el trabajo:
   "mantén todo donde está, nunca inventes un árbol que no está, una palmera sigue palmera".
3. **Datos desactualizados.** Si el 3D está desfasado (barrio nuevo que sale como pasto), se dibuja
   desde la foto satélite reciente en vez del 3D.

## Los problemas y sus arreglos

- **Costuras (el problema central).** Dos tiles juntos no coinciden: una carretera se desplaza,
  un árbol se corta, un lado más verde. Arreglo: tira con la mitad derecha de un tile y la izquierda
  del siguiente, bandas externas en rojo transparente, el modelo redibuja solo el medio, se pega con
  fundido. Igual para horizontales y esquinas (9×9 = 81 tiles, 144 costuras, 64 esquinas).
  **Pero no es perfecto:** sobre algo uniforme (bosque) se siguen viendo los cuadrados. No en las
  costuras (esas se funden), sino porque el tile 1 y el tile 5, a varios cuadrados de distancia, no
  se ven entre sí y no acuerdan el mismo verde. Con un modelo local (LoRA) se dibujan vecinos en un
  latent compartido y el tono fluye; con frontier no (uno a uno). Es el compromiso por el detalle.
- **Notas por tile (monumentos).** Fotos de referencia + descripción de la forma (qué abre a qué
  lado). Cada dibujo de ese tile las recibe.
- **Zonas desactualizadas.** Se delinean, se redibujan desde foto satélite reciente y se funden con
  borde suave.
- **Guía de color para áreas uniformes** (campos, parques, bosques). Se dibuja el área entera de una
  vez, y luego cada tile se redibuja usando su trozo de esa imagen como guía de color.
- **Filtros finales.** Unos pocos filtros apilados (Photoshop) que cada tile pasa al dibujarse; al
  retocarlos, todo el mapa pasa otra vez. Arregla el "se ve plano".
- **Agua por código (Río).** El mar no se dibuja: una textura de mar dibujada una vez, repetida por
  el mapa y coloreada por la profundidad real del fondo. La bahía más calmada y verde. Surf, olas y
  barcos se conservan del dibujo encima.
- **Alturas y sombras.** El render da una altura en metros por píxel; la sombra es la vista del sol
  de esas alturas. Con eso: foco tilt-shift que sigue al ratón, sombras que caen por las fachadas.
- **El sitio.** Pirámide de tiles por zoom; el móvil solo carga lo que se ve. Todo lo que se mueve
  es código (viento, agua, pájaros, cable car, aviones), leyendo la misma altura.

## Qué aplica a TinyVigo ahora

- Mar por código (ya, pero con textura + profundidad en vez de color plano).
- Guía de color para el parque del Castro (área uniforme: el verde no acuerda entre tiles).
- Filtros finales para quitar lo plano y unificar el look.
- Costuras entre tiles no adyacentes: compromiso conocido con modelo frontier; se reduce con la guía
  de color y los filtros, no desaparece del todo.
- El mapa de alturas ya lo escribe el render: sirve para sombras y foco (tickets LIGHT-01).
