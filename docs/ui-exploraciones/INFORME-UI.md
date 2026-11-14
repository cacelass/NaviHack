# TinyVigo: dirección de interfaz (informe breve, primera entrega)

Estado: hechas la **D (Elástico limpio)** y la **B (Consola retro)**, con hoja de estilo, iconos, componentes y maqueta de pantalla completa (móvil 390×844 y escritorio 1440×900, día y noche). Faltan A (Papel de mapa), C (Cartel de luces), la lista de nombres y la comparación lado a lado. Abre `index.html`.

Leyenda: **[hecho]** verificado en fichero o captura, **[obs.]** observación mía, **[opinión]**.

## 1. El gusto de Jose, con evidencia

- **[hecho]** Su librería, `~/Proyectos/elastic-ui/packages/elastic-ui/DECISIONS.md`: «interfaces limpias donde las cosas se transforman en vez de aparecer». Un botón se convierte en su diálogo (`DialogMorph`), un campo crece desde un icono, una carta se abre en su detalle. Se anima una sola cosa a la vez, con una curva (`cubic-bezier(.22,1,.36,1)`), ~500 ms al abrir y ~300 ms al cerrar, sin rebote.
- **[hecho]** Profundidad por tonos, no por sombras ni bordes (`tokens.css`: `bg-muted`, `surface-sunk`, `surface-raised`); campos como «bandejas» sin línea en reposo; solo una sombra casi invisible en lo que flota (`shadow-overlay`).
- **[hecho]** Tipografía: Inter, cinco tamaños (28/20/16/14/12), tres pesos (400/500/600), cifras tabulares, sin mayúsculas decorativas. Mono: JetBrains Mono. Radios 6/8/12/16/24 px.
- **[hecho]** Color: grises cálidos (Kolmi `frontend/design.md`: `#f8f7f4`, `#efeee9`, `#e6e4dd`), sin acento; el color solo significa algo (éxito, aviso, peligro). «Sin negro como resaltado.» Iconos: Lucide.
- **[hecho]** Mínimo: «icono antes que texto», estado mostrado y no explicado, sin avisos que repitan lo que ya se ve (Kolmi, Strivon `DESIGN.md`). Objetivos de 44 px (Strivon).
- **[hecho]** Rechazos en `USER.md` (sección Diseño/Frontend, líneas 450-452): `rounded-2xl`, fondos pastel en iconos, `box-shadow`, píldoras con fondo pastel, `animate-fade-in` en todo, layouts centrados por defecto. «Esto es AI slop.» También: «nada de movimiento perpetuo después de la entrada».
- **[hecho]** Prosa de UI (handbook `SKILL.md` y `references/humanizer.md`): sin guiones largos, sin «no X sino Y», sin tríadas. Los nombres de proyecto, en inglés (USER.md línea 436).
- **¿Aplica a UI web lo de «insignias, esquinas redondeadas, sombras, tarjetas, collages»?** Esa lista exacta sale de `skills/videos/references/aprendizajes.md` (vídeo). **Sombras, esquinas redondeadas excesivas y pastilla pastel: sí aplican a web**, están en USER.md como regla de frontend. **Collages: solo vídeo.** **Tarjetas:** en web no hay una prohibición escrita, pero elastic-ui dice «menos cajas»; lo he tratado como preferencia fuerte.
- **[obs.]** El handbook no tiene aún rama de «landing/página»: la guía de maquetar páginas no está escrita, así que he seguido DECISIONS.md y USER.md.

## 2. La UI del compañero (`~/Downloads/vigo-map`)

Capturas servidas con `python3 -m http.server` en el puerto 8231: `ref/companero-dia.png`, `ref/companero-noche.png`, `ref/companero-movil.png`.

| Pieza | Qué hay | Reutilizar como idea | No reutilizar |
|---|---|---|---|
| Panel HUD | 270 px a la izquierda, fondo `#1a2236`, borde de 2 px, acento `#ffcf4a`, fuente monoespaciada del sistema | buscador de locales, ir al árbol | 15 botones de texto en filas; tapa el mapa |
| Hora | deslizador de minutos + «Ahora» + «Sombras» | hora con «Ahora» | 3 controles para lo mismo |
| Capas | Calles, Locales, Vida, Cámaras, Parkings, Líneas bus como botones amarillos | la idea de capas | todo activado por defecto compite con el mapa |
| Panel de Navidad | lista con foto, horario, filtros por tipo, fuente | lista con foto y tipo, la fuente citada | ocupa 340 px a la derecha |
| Marcadores | insignia cuadrada de 18 px con glifo 7×7 y color por tipo, con rótulo | glifos pixel por categoría | la insignia con cola negra y brillo superior |
| Minimapa | 220 px abajo a la derecha | útil en escritorio | en móvil se oculta |
| Cámaras, parkings, tráfico | panel de cámara con imagen en directo, plazas libres | datos reales | fuera del alcance de v1 |
| Cargando | barra amarilla con texto | — | |

- **[hecho, captura]** En móvil (390 px) el HUD y el panel de Navidad cubren más de la mitad de la pantalla y se solapan con las coordenadas (`ref/companero-movil.png`). Para el spec («móvil primero, UI mínima») no sirve tal cual.
- **[hecho]** Es un visor propio en canvas con edificios extruidos, no las teselas pintadas: el mapa de este equipo es distinto del de las maquetas.
- **[no verificado]** El modo noche del compañero a las 21:00: el botón cambia pero la captura se hizo a las 13:36, con sol; no he visto su noche real.

## 3. Paleta del mapa (medida con PIL)

Sobre `vigo-bloque-3x3/dia-con-costuras.png` y `vigo-vertex-test.png`, por clases de matiz (el conjunto está en las hojas, sección 01):

| Color | Hex | Dónde |
|---|---|---|
| Mar de la ría | `#29435d` | 31 % de la imagen |
| Granito claro / en sombra | `#a5947e` / `#776756` | fachadas |
| Teja oscura / clara | `#622e1c` / `#7e4329` | tejados |
| Pizarra y asfalto | `#5c5a55` | |
| Calle y arena | `#ad8761` | |
| Verde de parque | `#4b612c` | |
| Mirador blanco | `#dedbd0` | solo 0,1 % |
| Noche: azul, sombra, granito | `#151b2a`, `#25140d`, `#64462e` | escena de referencia |
| Noche: luz cálida, ventana | `#f4cd80`, `#e1b66c` | |

- **[obs.]** El mosaico de día tiene costuras visibles entre teselas (bloques rectangulares con tono distinto en los bordes de 1024 px) y el mar es un azul plano. Los recortes de las maquetas están elegidos para que se note poco, pero se ven.
- **[obs.]** La noche de las maquetas es un multiplicado CSS `#58679f` sobre el día: oscurece y azulea, no ilumina ventanas ni farolas. Se lee como «oscurecido», no como la escena de referencia.

## 4. Direcciones (hechas hasta ahora)

**D. Elástico limpio** (`dir-d.html`). Inter, tonos, vidrio, esquinas de 8 y 12 px, pixel solo en nombre, iconos y marcadores; el icono de buscar se convierte en el campo y el marcador en la ficha (el morph está implementado con WAAPI en `assets/ui.js`, probado solo en captura estática, no he visto el movimiento).
- A favor: es lo más cercano a lo que Jose ha validado; el mapa queda libre; contraste calculado en todos los pares.
- En contra: la menos «de juego»; el vidrio con desenfoque cuesta en móviles flojos; la jerarquía depende solo del tono.

**B. Consola retro** (`dir-b.html`). Pixelify Sans + Silkscreen + VT323, biseles de 2 px, esquinas cortadas, barra de título, hora en pantalla LCD, paneles opacos.
- A favor: coherencia total con el mapa; paneles opacos, contraste independiente del fondo; muy reconocible.
- En contra: va contra lo que Jose rechaza (ornamento, nada se transforma); Silkscreen solo vale para etiquetas; tapa más mapa.

Contraste (WCAG, calculado al generar cada hoja, tabla en la sección 01): D y B cumplen 4,5:1 en texto sobre panel de día y de noche. En D tuve que subir la opacidad del vidrio de día de 80 % a 90 % y oscurecer cuatro colores porque con el primer diseño el texto atenuado, el dorado y el verde/rojo no llegaban (3,5, 3,0 y 4,0:1 en el peor caso). Texto directo sobre el mapa de noche: 13,4:1 en la mediana, 6,6:1 en zonas claras, con este tinte y sin luces.

## 5. Recomendación provisional

**[opinión]** Partir de **D** para estructura, tipografía y comportamiento, y tomar de **B** solo lo que es del mapa: la fuente de píxel para la hora (VT323 en lugar de las cifras de Inter), el estilo de marcadores cuadrados con pico y el parpadeo de selección. Motivo: lo que Jose rechaza por escrito (sombras, ornamento, algo que parezca generado) lo evita D, y los marcadores y los iconos ya aportan la estética de juego sin que la interfaz parezca un disfraz. Decidir tras ver A y C.

## 6. Componentes y assets, por orden

1. `iconos.js` (30 iconos de 16×16, hecho) y marcadores de 3 estados (hecho).
2. Chip de capa, botones, campo de búsqueda (en `elastic-ui` ya existen `Button`, `Toggle`, `SearchMorph`: partir de ellos).
3. Ficha de punto: `PopoverMorph`/`Sheet` de elastic-ui con foto, estado abierto/cerrado, horario y dos botones.
4. Control de hora con «Ahora» y la etiqueta «horario, no en vivo».
5. Lista de eventos con «añadir a la ruta» y lista de paradas con tiempos (`Timetable`, `AnimatedList`).
6. Tira de historia, toasts, estado de carga, marco de postal.

## 7. No verificado

- Todos los morphs y el movimiento: solo he visto capturas estáticas.
- Rendimiento del vidrio con desenfoque sobre el mapa en un móvil real.
- Que Pixelify Sans, Silkscreen y VT323 se vean bien en un móvil físico al sol (solo la captura de 390 px).
- La posición de los marcadores es de ejemplo, no coincide con las coordenadas reales (Porta do Sol es el centro del mosaico, pero no he calibrado el recorte).
- Los textos de las fichas salen de `navidad.json` (Concello); la historia es un extracto, no una ficha con fuente revisada.
- A, C, nombres y comparación: pendientes en esta entrega.
