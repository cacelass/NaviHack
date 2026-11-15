# Mapa, ronda 2: cómo se arregló (v11 a v18)

Guía para repetirlo. Las reglas cortas están en `vault/01_PROYECTO/mapa_render.md`; las cifras, en la sección «Ronda 2» de
`expansion-vialia.md`. Aquí va el método paso a paso, qué falló y por qué.

## Versiones publicadas

| Versión | Qué arregla | Llamadas |
|---|---|---|
| `v11-costuras` | Las 6 peores costuras del 3×3 (1,30-1,60× → ≤ 1,14×) | 6 |
| `v12-sin-fantasmas` | Dos edificios translúcidos donde se solapaban dos ventanas | 0 |
| `v13-muelle` | La máscara de mar se comía grúas y borde del muelle este (solo esa zona) | 0 |
| `v14-gruas` | Borde del muelle este y grúa norte redibujados | 1 |
| `v15-gruas2` | Grúa oeste y borde del muelle redibujados | 1 |
| `v16-costa` | Costa de 7 tramos redibujada (espigón, barcos, bordes nítidos) | 16 |
| `v17-sombras` | Tres sombras que la máscara de agua tomaba por agua | 3 |
| `v18-cuenca` | Cuenca de agua inventada y texto falso en un tejado | 1 |
| `v19-eliptica` | Error mío: quité la cúpula de la Plaza Elíptica y la dejé plana. Sustituida por v20 | 1 |
| `v20-eliptica2` | Plaza Elíptica con la cúpula baja y ovalada que tiene de verdad, base de piedra, monumento de tubos de acero, pérgola (con fotos reales de referencia) | 1 |
| `v21-capturas` | Costura H y=2048 que cortaba un bosquecillo (el render es una explanada de grava) y mancha clara con borde junto a la estación (ya estaba en el mapa original) | 2 |
| `v22-plaza-estacion` | La plaza de la estación era asfalto oscuro y el aparcamiento salía vacío; en el render es hormigón claro y aparcamiento lleno de coches | 1 |
| `v23-costura-h` | Costura H y=2048 desde x=2560 (cruzaba los tejados): ventana nueva centrada en (2800, 2048), 1,14× → 1,04× | 1 |

Gasto total de la ronda: 36 llamadas de imagen de 40. Cada versión sale del fichero anterior; los intermedios están en
`work/mapa-sonnet/` (`s4` a `s16`) y no se versionan.

## Principio: componer, no rehacer

No se repinta una ventana entera. Se pide al modelo un recorte pequeño y se pega **solo lo que cambia**, con máscara suave.
Lo que queda fuera de la máscara no cambia ni un píxel. Todo lo de abajo son variantes de esa idea.

## 1. Costuras del 3×3

1. Medir: `python3 pipeline/render/seam_metric.py MAPA.png` (ratio de salto de color; meta ≤ 1,15×).
2. Pintar una ventana de 1024 px **centrada en la costura**, desde el render, con una muestra de estilo de 512 px de otra
   zona y `zona/seam-window-prompt.txt` (para el parque se cambió la frase de contenido; ver `integrate_seams_r2.sh`).
   Para el cruce de dos costuras, una ventana centrada en el cruce.
3. Mezclar: `pipeline/render/seam_window_blend.py` (núcleo 48 px, fundido a 200 px, color ajustado a la media y desviación
   del mapa en la banda). `--axis v|h|x` (`x` = cruce), `--clip X0 Y0 X1 Y1` limita la ventana a un tramo.
4. La cadena completa y en orden está en `pipeline/render/zona/integrate_seams_r2.sh`.

Lo que falló:
- Ajustar solo el color (rampa suave) baja la media pero no las peores: el salto era de contenido.
- Dos ventanas solapadas en un fundido dejan un fantasma (edificio translúcido). Se evita con `--clip` y, si ya está hecho,
  con una ventana a máscara casi opaca (núcleo 400, fundido 480) o restaurando el mapa anterior con borde suave.

## 2. Qué falla con el agua y por qué

El mar va por código (`sea.py`) a partir de una máscara de agua del render (color + conectividad, `port_fix.get_water`).
Esa máscara se equivoca de dos maneras, ambas por **sombras oscuras**:

- **Come muelles y grúas**: la sombra de una grúa o del borde del muelle se lee como agua; el mar por código pisa lo dibujado.
- **Inventa agua tierra adentro**: una sombra de muro, de calle o de edificio queda como charca. Se ven como componentes
  conectados de la máscara que no son el mar. Se listan así:

```python
n, l, st, cen = cv2.connectedComponentsWithStats(wm.astype(np.uint8), connectivity=8)  # wm = get_water(render)
# el componente 1 es el mar; los pequeños (bbox y área en st) son sospechosos: comparar con el render
```

En la ronda salieron 6 componentes: el mar, el canal junto a la glorieta (real, se dejó) y tres sombras (muro junto a las
vías, calle, patio de manzana), más una cuenca que el dibujo del modelo inventó sobre un montón de rocas.

Probado y descartado:
- **SAM 2** (CPU, 25 tramos de 512 px, con puntos de la máscara de color): bordes limpios en la grúa, pero halos de arena
  en casi todo lo demás. No mejora lo que ya había.
- **Ensanchar la franja protegida de `apply_sea`** (de 7 a 30 px): protege objetos pero deja dos tonos de agua.
- **Abrir la máscara** (quitar franjas finas de agua): arregla un muelle y mancha otros (manchas claras redondas).

Lo que sí funciona: **redibujar el recorte** con el modelo.

## 3. Receta de redibujo de un recorte

1. Elegir el recorte (350 px para un objeto o borde; 512 px para un tramo de costa) y mirar antes el mapa y el render lado a
   lado.
2. Subir ambos a 1024 px y llamar al modelo con el mapa primero y el render segundo (`pipeline/imggen.mjs`, `AR=1:1`,
   `MODEL=gemini-3.1-flash-image`). Prompts en `pipeline/render/zona/coast_r3/prompt.txt` (costa) y
   `zona/shadows_r3/` (sombras y cuenca). El prompt dice qué arreglar y que no se añada ni quite nada más.
3. **Mirar antes de pegar** (hoja con mapa | respuesta | render: `coast_r3/sheet.py`).
4. Pegar: `python3 pipeline/render/paste_patch.py mapa.png respuesta.png salida.png --box X0 Y0 X1 Y1 [--thr 45]
   [--limit ...] [--color-match]`. Para la costa, `coast_r3/compose.py` limita el pegado a agua más 45 px de tierra y sube el
   umbral a 85 en mar abierto (para no pegar cambios de tono del agua).
5. Medir las costuras, tests, pirámide, navegador (apartado «Publicar» del README de `pipeline/render`).

Criterios para aceptar o rechazar una respuesta (se rechazaron 9 de 16 recortes de costa):
- **Rechazar** si inventa barcos, plataformas o espigones en mar abierto que el render no tiene, si cambia el color de los
  edificios hacia el del render, o si deja una franja clara en el borde del recorte.
- **Aceptar** si añade lo que el render sí tiene (espigón largo, barcos atracados, grúas completas) y los bordes quedan nítidos.
- Los recortes con mucho mar abierto son los que más inventan: mejor recortes pequeños centrados en el borde.

## 4. Auditoría y comprobaciones

- **Un arreglo no acaba al quitar el defecto**: hay que volver a comparar con el render lo que queda. En v21 quité una mancha y dejé la plaza oscura cuando es hormigón claro.

- **Localizar una captura de Jose**: están en `~/Pictures/Screenshots/` (la más reciente por fecha). `cv2.matchTemplate` sobre el mapa en gris reducido a la mitad, escalas 0,3-1,6 en pasos de 0,05, recortando de la captura la interfaz (barra, botones). Con captura de noche el tinte baja la correlación (0,47 y aun así acertó); cuando sale < 0,35 se amplía el rango de escalas, no se rinde. La escala del navegador puede ser mayor que 1.

- **Identificar lo que el mapa dibuja antes de darlo por bueno**: coordenadas con `pipeline.georef.to_latlon(px, py)` y búsqueda web del lugar. La «cúpula» de v10 a v18 era la Plaza Elíptica (42,2318 N, −8,7207 E): existe una cúpula de cristal, pero baja y ovalada, sobre un basamento de pizarra; el modelo la había exagerado a una esfera alta. Buscar **fotos reales** (Wikimedia Commons: `commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch=<lugar>&gsrnamespace=6&prop=imageinfo&iiprop=url&iiurlwidth=900&format=json`) y pasarlas como tercera imagen a `imggen.mjs`. Error mío en v19: leí «plaza plana» en la web, quité la cúpula sin mirar una foto y la dejé mal. Primero la foto, después la decisión.

- Hojas de 24 pares mapa | render a 600 px **no ven** defectos finos (los dos fantasmas, las grúas, las charcas); las capturas
  de Jose con zoom sí. Ante una captura: localizarla con `cv2.matchTemplate` multiescala sobre el mapa (la escala sale sola),
  recortar la misma zona del render y comparar.
- La correlación de bordes (`fidelity.py`) engaña en el centro urbano: el render lleva fachadas lisas y las celdas «peores» se
  veían fieles. Úsala solo para encontrar candidatos y mira la imagen.
- Las rayitas blancas verticales que se ven sobre el mar en el navegador no están en el mapa (también aparecen sobre
  tejados): es un efecto de la web.

## 4b. Luz de noche del Árbol y de la Noria (v20 en adelante, sin versión nueva de mapa)

Antes: líneas vectoriales dibujadas encima con cifras medidas a mano (`web/js/lights.js`), que no seguían la forma pintada y
eran de una versión antigua del árbol. Ahora cada asset lleva una capa de luz pintada (`web/ui/assets/luces/*.png`, 400 px del
lienzo, negro = sin luz) que se **suma** al mapa con `screen` en OpenSeadragon y solo cambia de opacidad.

1. Recorte de 400 px del mapa por `NIGHT_TINT` (0,292 / 0,396 / 0,696) = noche apagada, a 1024 px.
2. Una llamada al modelo con ese recorte, el render y una foto real: «enciende el asset sin tocar nada más»
   (`zona/lights_r3/prompt_arbol.txt`, `prompt_noria.txt`). La luz sigue la celosía y los radios pintados.
3. `zona/lights_r3/make_emission.py`: se queda solo con la diferencia positiva respecto a la noche apagada, rodilla suave
   (sin núcleos blancos), resplandor y bordes difuminados 60 px (si no, se ve el recorte). Variante fría del árbol girando el tono.
4. Animación en `lights.js`: pulso lento, paso de rosa a azul hielo cada 14 s en el árbol (el real cambia de color) y brillo con
   saltos irregulares en los pases de música; con «reducir movimiento», fijo.

Referencias de la técnica: luz en el mundo y no filtro encima, fuente / resplandor / iluminación del entorno como tres cosas,
núcleo pequeño y halo aditivo, parpadeo a saltos y contención (Unity 2D Lighting, PixelLight 2D, Pixel-Editor, AI Game Dev).
Datos reales: árbol de 45 m con 100.000 leds que cambian de color; noria con cabinas rojas bordeadas de luces azules.
Pendiente: el bosque de 10 árboles de 8-10 m junto al árbol; el CSS `.tv-tree` / `.tv-wheel` de `points.css` ya no se usa.

## 5. Trampas de entorno

- `work/` se comparte entre worktrees pero `pipeline/ledger/image-calls.jsonl` es del checkout desde el que se llama a
  `imggen.mjs`: llamar siempre desde el worktree que va a commitear, o fusionar los dos ledgers (`sort -u`) antes del commit.
- `/tmp` es tmpfs (7,7 GB) y `/home` va justo: PyTorch con CUDA no cabe; la versión CPU sí (1,1 GB).
- `pkill -f <patrón>` mata la propia shell si el patrón sale en su línea de comandos. Matar servidores por PID.
- zsh no separa en palabras una variable sin comillas: pasar los argumentos de dos en dos (`${t%,*}`, `${t#*,}`).
- La máscara de agua tarda 6 min la primera vez y queda en `/tmp/opencode/port_fix_cache/` (clave: md5 del render).

## 6. Qué queda

- 9 recortes de costa en mar abierto sin redibujar (sobre todo el muelle este, x 4096-4608): hacerlo con recortes más
  pequeños y un prompt que prohíba explícitamente barcos y estructuras nuevas.
- El montón de rocas de la cuenca quedó con estilo algo más fotográfico que el resto.
- La grúa pequeña del extremo oeste del muelle este se redibujó con una pluma algo grande; se puede rehacer.
