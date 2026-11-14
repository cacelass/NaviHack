# DESIGN.md — TinyVigo UI v2 (dirección D ejecutada)

Decisiones de esta carpeta, para que el siguiente cambio parta de aquí y no de cero.

## Qué es

La UI de TinyVigo. El pixel es un **recurso** (el mapa isométrico, los iconos, los
marcadores y la marca), no el lenguaje de la interfaz. La UI es Inter + vidrio +
jerarquía por tonos. Nada de fuentes de píxel en paneles, navegación o datos, ni
biseles pixel, ni esquinas muy redondeadas, ni píldoras pastel, ni sombras, ni
degradados llamativos.

## Sistema (copiado de Strivon: el sistema, no su identidad)

- **5 superficies** por tono, sin sombras: `bg`, `surface`, `sunk`, `raised` y una
  línea fina (`line`). Neutros cálidos, no grises fríos.
- **3 niveles de texto**: `fg`, `fg-secondary`, `fg-muted`.
- **3 estados**: `danger`, `warning`, `ok`. El color solo significa un estado
  (abierto/cerrado, lluvia, de noche), nunca decora.
- **Un acento con rampa de 7 pasos** (`accent-1..7`): la luz cálida de la Navidad.
  Se usa para magnitudes y para "cuánto falta/queda" (progreso de sellos, barra de
  hora, encendido). Los 7 pasos viven en `css/tokens.css`.

## Tipografía, radios, movimiento

- Inter, cinco tamaños fijos (28/20/16/14/12) y tres pesos (400/500/600), sin
  tamaños intermedios. Pixelify Sans solo en la marca y en los números sobre el mapa.
  Cifras tabulares.
- Radios 6 / 8 / 12 (16 para el certificado). Profundidad por tonos, **cero sombras**.
- Movimiento mínimo: una curva `cubic-bezier(.22,1,.36,1)`, 200–500 ms, siempre
  respetando `prefers-reduced-motion`.

## Representación (de Strivon)

- **Hero de una frase**, "cómo funciona" en 3 pasos, "qué puedes hacer hoy" en
  tarjetas de icono + título + una línea.
- **Cifras en tríada**: número grande, etiqueta pequeña, fuente debajo. Lo dudoso
  lleva "estimación" o "aproximado" y su fuente visible. Nunca se usa una cifra de
  Caballero como dato: si aparece, es estimación con fuente.

## Tono del copy

Frases cortas en presente, cero adjetivos, se nombra la tecnología real
(Open-Meteo, GTFS de Vitrasa y Renfe, el mapa por teselas). Nada de
"revolucionario" ni "impulsado por IA".

## Puntos de Navidad y mapa

- La noria y el árbol no son marcadores: son **assets animados integrados en el
  mapa**. Los marcadores que quedan (bus, tren, parking, cámara) tienen silueta,
  color y dibujo propios en píxel, nada genérico.
- Noria y Cíes Market están en **Vialia** (al este, fuera del bloque 3×3 centrado
  en Porta do Sol). El Belén está en Casa das Artes.

## Ficheros

- `css/tokens.css` — tokens y temas claro/oscuro (única fuente de valores).
- `css/base.css` — reset, tipografía, botón, foco, estados de carga.
- `css/layout.css` — shell de app (mapa, HUD, buscador, hojas, zoom).
- Un CSS por componente: `panel-lugar`, `tarjeta-evento`, `barra-tiempo`,
  `chip-filtro`, `lista-ruta`, `aviso`, `tooltip`, `marcadores`, `cifras`,
  `navidena`.
- `components.html` — catálogo en claro y oscuro.
- `navidena.html` — "A Navideña" jugable (43 sellos, certificado numerado).

## Iconos

`assets/iconos.js` es el set propio de 16×16 en píxel (ya validado). Se buscaron
pixelarticons (MIT), game-icons.net (CC BY 3.0) y NES.css (MIT): no tienen los
temáticos de Vigo con buenos nombres, así que se mantienen en `assets/vendor/`
con su licencia en `CREDITOS.md`. No se cargan CDN en tiempo de ejecución.

## Reglas no negociables de Jose

Sin sombras. Sin esquinas muy redondeadas. Sin píldoras pastel. Sin degradados
llamativos. El pixel solo como recurso. Contraste AA en claro y en oscuro. Objetivos
táctiles de 44 px o más. El estado (ruta, hora, capas, sellos) vive en la URL.
