# UI exploraciones — TinyVigo

Cuatro direcciones visuales probadas antes de decidir. Cada una es HTML + CSS
autocontenidos (fuentes y assets en esta carpeta). El detalle y las fuentes de
decisión están en `INFORME-UI.md`.

## A. Juego pixel (`mock-a.html`)

Todo en píxel: fuentes de bits, biseles, paneles opacos. Coherente con el mapa.

- **Aprendido:** es la más "de juego", pero el píxel en paneles y datos no es el
  píxel del mapa: es un disfraz. Choca con lo que Jose rechaza (ornamento, algo que
  parece generado).

## B. Consola retro (`dir-b.html`)

Pixelify Sans + Silkscreen + VT323, biseles de 2 px, esquinas cortadas, barra de
título, hora en LCD, paneles opacos.

- **Aprendido:** muy reconocible y de contraste independiente del fondo, pero las
  fuentes de bits solo valen para etiquetas y tapa más mapa. El píxel como lenguaje
  de la interfaz pesa.

## C. Cuaderno técnico (`mock-c.html`)

Fondo de cuaderno, reglas, anotaciones al margen, aire de croquis.

- **Aprendido:** es un truco visual. La metáfora del cuaderno no aporta legibilidad
  y se rompe al verlo en el móvil.

## D. Elástico limpio (`dir-d.html`)

Inter, tonos en vez de bordes ni sombras, vidrio sobre el mapa, esquinas de 8 y
12 px. El píxel vive solo en la marca, los iconos y los marcadores.

- **Elegida.** Motivo: es lo más cercano a lo que Jose ya valida en sus proyectos
  (Inter, jerarquía por tonos, sin sombras, sin esquinas redondeadas, sin píldoras
  pastel); deja el mapa como protagonista y el píxel como recurso, no como lenguaje.
  La versión final pulida de D está en `web/ui/` (la interfaz v2).

## Por qué D y no las otras

El mapa isométrico ya es píxel. Si la interfaz también lo es, no se distingue qué
es imagen y qué es control. D reserva el píxel para las imágenes (mapa, sprites,
iconos y matasellos) y deja el texto en Inter, con jerarquía clara, contraste AA
en claro y oscuro y objetivos táctiles de 44 px. Las otras tres confunden el
recurso con el lenguaje.
