# Trucos de tinygyn.com y tinyrj.com (vídeo de Thomas Marcelo)

## Ficha y fiabilidad

- **Vídeo:** “How I built a Rio de Janeiro Map in Isometric Pixel Art style”, Thomas Marcelo, 7 nov 2026, 10:27.
  <https://youtu.be/OeYzRevuSCQ>
- **Fuente principal:** subtítulos automáticos en inglés descargados con `yt-dlp`, más fotogramas del propio vídeo para leer el prompt y los diagramas (el texto del prompt no está en los subtítulos).
- **Fuente secundaria:** descripción del vídeo (modelo, datos y créditos). Las webs `tinyrj.com` y `tinygyn.com` son solo el visor: no publican un write-up técnico.
- **No hay hilo/blog del autor** con más detalle. Todo lo que sigue sale del vídeo; lo que no enseña el código va marcado como **[inferencia]**.
- Los subtítulos automáticos deforman nombres: “Andy Coral” es **Andy Coenen** (isometric.nyc), “Boris Tarquov” es **Boris Starkov / ktoya** (tiny.london), “Goyania” es **Goiânia**. Corregido con la descripción.

---

## 1. Pipeline completo, con marcas de tiempo

| Hora | Paso | Qué hace exactamente |
|---|---|---|
| 0:30–2:05 | Idea | Ve isometric.nyc (Andy Coenen) y tiny.london (Boris Starkov). Decide hacer su ciudad, Goiânia, y luego Río. |
| 2:05–2:19 | Cámara | Carga el modelo 3D fotorrealista de Google en el navegador. Cambia la cámara con perspectiva por una **ortográfica inclinada 45° y girada un poco**. Así todos los edificios se ven desde el mismo ángulo, estén donde estén. |
| 2:19–2:41 | Escala | **1 píxel ≈ 30 cm de suelo**. Un tile de 1024 px cubre unos **307 m**. |
| 2:41–2:57 | Teselado | La ciudad se corta en cuadrados de **1024×1024 px**. Río son **más de 21.000 tiles**; el lienzo completo, **250.000 px de ancho**. |
| 2:57–3:12 | Render por tile | Cada tile se renderiza desde el modelo 3D con esa cámara. El render tiene la forma y la posición correctas, pero es feo: árboles derretidos, tejados emborronados, sin estilo. “Convertir esto en un dibujo es todo el juego.” |
| 3:12–3:26 | Primer intento | Un modelo de imagen grande dibuja unos cientos de tiles de ejemplo; con ellos se entrena un modelo abierto pequeño; el pequeño dibuja el resto en la GPU local. Barato y rápido una vez entrenado. |
| 3:26–3:33 | Fracaso | El resultado es **soft, bland, safe**: exactamente el problema que veía en los otros mapas. |
| 3:33–3:54 | Giro | Cada tile lo dibuja un **modelo frontier**, el mejor al que tiene acceso, **sin entrenar**. Entrada: el render + una descripción del estilo. El modelo entiende qué es un tejado, una antena, un depósito de agua. |
| 3:54–4:11 | Prompt | Ahí va “casi todo el trabajo”: mantener todo en su sitio, no inventar árboles, una palmera sigue siendo palmera. |
| 4:11–4:24 | Referencias | Cada tile recibe además una **style reference** y **tiles ya dibujados**, para que toda la ciudad salga “de la misma mano”. |
| 4:24–4:31 | Datos viejos | Donde el 3D de Google está desfasado (un barrio nuevo que aún sale como pasto), dibuja desde la **foto de satélite plana de 2026**. El modelo lee las alturas de la propia foto: la información 3D ya está proyectada en la imagen. |
| 4:31–4:50 | Costuras | Dibujar tile a tile rompe los bordes: una carretera se desplaza, un árbol se corta, un lado es más verde. |
| 4:50–5:11 | Arreglo de costura | Coge la **mitad derecha de un tile y la mitad izquierda del siguiente**, pinta en **rojo transparente los cuartos exteriores** y pide al modelo que redibuje **solo la mitad central**. La tira vuelve encima de la costura con un **fundido** en los bordes. |
| 5:11–5:18 | Horizontales y esquinas | Lo mismo para cada costura horizontal y para cada esquina donde se juntan cuatro tiles. |
| 5:18–5:26 | Conteo | Un barrio de **9×9 tiles = 81 tiles + 144 costuras + 64 esquinas = 289 dibujos**. |
| 5:26–6:08 | Límite aceptado | Al alejarse sobre una zona uniforme (bosque) aún se notan los cuadrados: no en las costuras, sino porque el **tile 1 y el tile 5 no se ven entre sí** y no acuerdan el mismo verde. Un modelo local con latent compartido lo resolvería; con frontier se pierde eso a cambio de detalle. |
| 6:08–6:17 | Orden de trabajo | Empieza en la Praça Cívica y crece hacia fuera. **~1 minuto por dibujo**, hasta **40 en paralelo**. Elige a mano qué tiles van siguiente en un editor propio. |
| 6:17–6:51 | Notas por tile | Para monumentos: fija fotos de Street View al tile y escribe una nota de forma (“la pirámide roja abre al oeste; el lado con ángulo recto mira al oeste”). **Cada dibujo de ese tile recibe las fotos y la nota.** |
| 6:51–7:13 | Zonas desfasadas | Parte del 3D de Goiânia es de **2013** (el aeropuerto no tiene la terminal nueva). Delinea la zona, la redibuja desde la **foto de satélite de 2026** y la funde con borde suave. |
| 7:13–7:33 | Guía de color | Para zonas uniformes (campos, parques): delinea el área, el modelo la dibuja **entera de una vez en una sola imagen**, y luego cada tile se redibuja usando **su trozo de esa imagen como guía de color**. |
| 7:33–7:50 | Filtros finales | Los dibujos salen planos. Abre uno en Photoshop y **apila tres filtros** hasta que “pop”. Cada tile pasa por ese mismo archivo al dibujarse; si retoca los filtros, **todo el mapa vuelve a pasar**. |
| 7:50–8:18 | Agua | En Río cada tile dibujaba un mar distinto. El mar deja de dibujarse: **una textura de mar dibujada una vez**, repetida por el mapa y **coloreada por la profundidad real del fondo**. Guanabara tiene su propia paleta, más calmada y verde. Surf, olas y barcos se conservan del dibujo encima. |
| 8:18–9:00 | Sombra del avión | El avión y su sombra tienen que comportarse como si el dibujo fuese 3D: subir por una fachada, cruzar el tejado, caer a la calle. No usa un depth map del modelo de imagen (da “plausible grace” sin metros ni acuerdo entre tiles). Usa **la altura por píxel del mismo modelo 3D y la misma cámara**; la sombra es **la vista del sol de esas alturas**. |
| 9:00–9:18 | Foco y volumen | Con las mismas alturas, un **foco tilt-shift** sigue al ratón: lo que está a la misma distancia de cámara que el punto bajo el cursor queda nítido y el resto se desenfoca. Donde el terreno cae, se genera una **ladera/falda** en el lado lejano para que las montañas se lean. |
| 9:18–9:41 | El sitio | El sitio son solo imágenes. Cada tile se escala a versiones menores, una por nivel de zoom; el móvil descarga solo lo que cabe en pantalla al tamaño que necesita. Todo lo que se mueve (viento, agua, pájaros, teleférico, aviones) es **código dibujado encima** y lee la misma altura. |
| 9:41–10:27 | Cifras | Goiânia: **7.580 tiles, 31.000 dibujos, 8 gigapíxeles** impresos como una sola imagen. Río seguía dibujándose al publicar el vídeo. |

---

## 2. Teselado y costuras: el método exacto

### Teselado

- **Tile:** 1024×1024 px de render.
- **Escala:** 1 px ≈ 0.30 m → **~307 m por tile**.
- **Cámara:** ortográfica, **45° de inclinación** y giro leve. El giro exacto no lo dice; en la familia de mapas se usa **15°** (nuestro spec ya lo fija).
- **Corte:** la ciudad se renderiza como un lienzo gigante y se corta en una rejilla regular. No hay tiles de tamaño variable ni pirámide en el render; la pirámide llega después, para el visor.
- **Render por tile:** cada tile se vuelve a renderizar desde el 3D con la misma cámara. Eso garantiza que el tile sea una ventana exacta del mismo mundo, no una composición.

### Costura vertical (la que muestra el vídeo)

1. **JOIN.** Toma la **mitad derecha** del tile A (512 px) y la **mitad izquierda** del tile B (512 px). Las pega: tira de **1024×1024 px**.
2. **SHADE.** Pinta en **rojo transparente** los **cuartos exteriores**: 256 px a la izquierda y 256 px a la derecha. Queda:
   `[rojo 25 %][centro limpio 50 %][rojo 25 %]`.
   El rojo no es una máscara de transparencia real: es **contexto que el modelo no debe tocar** (“context, not to touch”).
3. **REDRAW.** Una llamada al modelo con la tira y la instrucción de redibujar **solo la parte no roja**, para que empalme ambos lados. El modelo ve a cada lado del centro el dibujo real de cada tile, así que continúa carreteras, arena, olas y árboles.
4. **BLEND.** La mitad central redibujada vuelve **encima de la costura** con un **fundido** en sus bordes. El fundido evita un corte recto entre lo viejo y lo nuevo.

### Costura horizontal

Exactamente lo mismo, transpuesto: **mitad inferior** de A + **mitad superior** de B; rojo en los **cuartos superior e inferior**; se redibuja la **franja central del 50 %**; se funde.

### Esquina de cuatro tiles

El vídeo dice “lo mismo para cada esquina donde se juntan cuatro tiles”, pero **no muestra el diagrama de recorte**. [inferencia] La aplicación coherente del mismo principio es:

- Componer una ventana centrada en la esquina con **512 px de cada uno de los cuatro tiles** → 1024×1024.
- Dejar limpias las **cuatro cruces centrales** (el centro de la ventana) y pintar en rojo los **cuartos exteriores** de la ventana.
- Redibujar solo la cruz central y fundirla.

La cifra del vídeo confirma que cuenta **solo costuras y esquinas interiores**: 9×9 → 144 = 2·9·8; 64 = 8². No cuenta el borde exterior del bloque.

### Cuántos dibujos por bloque

Fórmula exacta que se deduce del conteo del vídeo:

```text
n×n tiles → n² tiles + 2·n·(n−1) costuras + (n−1)² esquinas = (2n−1)² dibujos
```

| Bloque | Tiles | Costuras | Esquinas | Total |
|---|---:|---:|---:|---:|
| 3×3 | 9 | 12 | 4 | **25** |
| 5×5 | 25 | 40 | 16 | **81** |
| 9×9 | 81 | 144 | 64 | **289** |

Esto es importante para nuestro presupuesto: **un 3×3 no son 9 llamadas, son 25**. Un 9×9 no son 81, son 289; el vídeo lo dice literalmente.

### Fundido

El vídeo no da el ancho del degradado. [inferencia] Un **ramp alpha de 32–64 px** (3–6 % del tile) es suficiente para que no se vea la unión a zoom 1:1 y no se coma detalle. Se compone solo el centro; los cuartos rojos nunca se pegan.

### Límite real del método

Las costuras quedan bien, pero **no desaparecen los cuadrados en zonas uniformes**. La causa no es el borde: es que dos tiles a varias casillas de distancia **nunca se ven** y eligen verdes distintos. Con un modelo frontier (una imagen por llamada) no hay latent compartido; con un modelo local se podrían dibujar vecinos en el mismo latent, pero se pierde el detalle que da el frontier. El autor acepta ese compromiso y lo mitiga con la guía de color global (sección 4).

---

## 3. El truco de la sombra del avión que sube por los edificios

### Lo que NO usa

Un **depth map pedido al modelo de imagen**. Da una profundidad “plausible”, pero:

- no tiene metros,
- no tiene escala,
- no concuerda entre tiles,
- y por tanto la sombra no puede caer en el sitio correcto ni continuar de un tile al siguiente.

### Lo que sí usa

El **height map del propio render 3D**, con la **misma cámara ortográfica**:

- A cada píxel del tile le corresponde una **altura en metros**.
- El height map se genera en el mismo render que la imagen, así que está perfectamente registrado con el dibujo: píxel a píxel, tile a tile.
- La sombra no se “pinta”: se calcula como **la vista del sol de esas alturas**. Es decir, se renderiza el campo de alturas desde la dirección del sol y se compara qué parte del terreno ve el sol y qué parte queda tapada.

### Por qué la sombra “sube” por la fachada

Porque la sombra se calcula sobre la **superficie 3D** (el heightfield), no sobre la imagen 2D:

1. Se lanza un rayo desde el avión en la dirección del sol.
2. El rayo avanza por el campo de alturas.
3. La sombra se deposita en el **primer punto donde el rayo toca la superficie**.
4. Si ese punto es una **fachada**, la sombra aparece en la pared, a la altura del impacto; si es un **tejado**, en el tejado; si pasa de largo, en la **calle**.

Por eso el avión puede cruzar un edificio y su sombra **trepa por el muro, se tumba en el tejado y cae al suelo** sin que nadie dibuje nada a mano. [inferencia] La implementación estándar y compatible con lo que enseña el vídeo es un **shadow map ortográfico desde el sol** sobre el heightfield; otra variante equivalente es **ray marching** sobre el height map en CPU/GPU. El vídeo no muestra el código.

### Datos que necesita

- Height map en **metros** por píxel (mismo encuadre y misma cámara que el tile).
- Dirección del sol (acimut y elevación) para la hora que se quiera.
- Posición del avión y su altura de vuelo.
- Opcional: mapa de **building-id** para saber qué superficie es edificio, calle o agua y aplicar la sombra solo donde toca.

### Todo lo que se mueve lee la misma altura

No solo el avión: árboles con viento, agua, pájaros, el teleférico del Pan de Azúcar y los aviones. Todos consultan el mismo height map, así que quedan **anclados al mundo** y no “flotan” sobre el dibujo. Es la misma razón por la que el foco tilt-shift funciona: la distancia a cámara se calcula con la altura, no con el color.

---

## 4. Coherencia de estilo y color entre teselas

El vídeo usa **cinco mecanismos acumulativos**, no uno solo:

| Mecanismo | Qué aporta | Dónde se ve |
|---|---|---|
| **Style reference fija** | Una tile ya dibujada que se pasa en **todas** las llamadas. Fija paleta, grosor de píxel, tratamiento de tejados, árboles y sombras. | 4:11 |
| **Tiles vecinos ya dibujados** | Además de la referencia, se pasan vecinos reales para que el modelo continúe lo que hay al lado. | 4:11 |
| **“Picture 1”: dibujo global de baja definición** | Un dibujo **de toda la zona** (o del área) del que se recorta el encuadre de cada tile. Se usa **solo para posición y color**, nunca para tamaño. Es lo que hace que “cada frame del área coincida”. | Prompt, Fig. 6 (~3:58) |
| **Guía de color para zonas uniformes** | El área entera se dibuja **una vez en una sola imagen**; luego cada tile se redibuja usando su trozo como guía de color. Resuelve campos, parques y bosques. | 7:13–7:33 |
| **Filtros finales fijos** | Un stack de **tres filtros** (Photoshop) que pasa **cada tile** al dibujarse, y **todo el mapa** cuando se retoca. Corrige el look plano y unifica el color. | 7:33–7:50 |

### La clave del prompt de color

El prompt no describe el contenido (“fachadas de granito, tejados rojos”): eso haría que el modelo pintase granite y tejados donde no los hay. **El contenido sale del render**; el prompt solo dice **cómo dibujar**. La referencia global (“Picture 1”) y la style reference dicen **cómo se ve**; el render dice **qué hay y dónde**.

### Lo que no se puede arreglar

La deriva de tono entre tiles lejanos. El autor lo dice sin adornos: “tile one and tile five, a few squares apart, never see each other, and they don’t always agree on the same green”. Con frontier se mitiga con la guía global y los filtros, pero **no se elimina**. Para nosotros es un riesgo conocido, no un bug a perseguir infinito.

---

## 5. Prompts, referencias, parámetros, llamadas y coste

### Prompt real (transcrito del fotograma, Fig. 6, ~3:58)

El texto visible, en inglés, es este. Los corchetes son aclaraciones mías, no parte del prompt.

```text
Picture 1 is a rough, low-detail drawing of one square frame of an isometric
pixel-art city map, cut out of one drawing of the whole area so that every frame
of the area matches. Use Picture 1 for two things only: where things are, and
their colours.

Never take the size of anything from Picture 1: it was drawn at a much smaller
scale, so its trees, cars, people and other small things are far bigger than
they really are.

Picture 2 is the real place, Copacabana, Rio de Janeiro. Every shape, position
and size comes from Picture 2: every field edge, track, crop line, tree, car,
building and road stays exactly where Picture 2 has it, exactly as big as
Picture 2 shows it, with all its small details.

TREES: draw a tree only where you are certain Picture 2 shows one, at exactly
its size in Picture 2. Neighbouring trees never swell into one mass: a row of
small trees stays a row of small trees with ground between them. Where Picture 2
clearly shows another kind of tree, draw that kind: a palm stays a palm (a thin
trunk under a star of fronds), a silva tree stays silva [sic].

Add nothing that is not in Picture 2 and remove nothing that is. No text,
labels, borders or frames. Fill the whole square edge to edge.
```

**Lectura del prompt:**

- **Picture 1** no es el render: es un **dibujo global de baja definición** de toda la zona, recortado al encuadre del tile. Se usa **solo para posición y color**.
- **Picture 2** es el **render 3D** (o la foto de satélite cuando el 3D está desfasado). De ahí salen **forma, posición y tamaño**.
- La frase “Never take the size of anything from Picture 1” existe porque el modelo, si no se le dice, **copia los tamaños del dibujo global** y pinta árboles y coches gigantes.
- “Add nothing / remove nothing” y “no text, labels, borders or frames” son las dos reglas que evitan invenciones y contaminación tipográfica.
- El nombre del lugar (“Copacabana, Rio de Janeiro”) cambia por tile/ciudad; el resto es plantilla.

### Entradas por llamada

1. **Render** del tile (1024×1024), como Picture 2.
2. **Recorte del dibujo global** de baja definición, como Picture 1.
3. **Style reference**: una tile ya dibujada.
4. **Vecinos ya dibujados** cuando existen.
5. **Nota del tile** (fotos + texto) en monumentos.
6. **Guía de color** del área en zonas uniformes.

### Parámetros que el vídeo NO da

- Modelo exacto: solo “OpenAI’s image model, through Codex” (descripción). **No dice versión, temperatura, seed, pasos ni resolución de salida.** [inferencia] La salida es 1024×1024, porque el tile de entrada lo es y el flujo recorta/pega a ese tamaño.
- No dice si usa máscara de inpainting real o solo el rojo como instrucción visual. El vídeo dice “shade the outer parts in transparent red and ask the model to redraw only the middle, the part that isn’t red”. Es **instrucción visual**, no necesariamente una máscara de API.
- No dice el ancho del fundido ni el número de muestras.

### Llamadas y ritmo

- **1 llamada por dibujo** (tile, costura o esquina). No hay lote de varios tiles en una llamada con frontier.
- **~1 minuto por dibujo**.
- **Hasta 40 en paralelo**.
- Goiânia: **7.580 tiles → 31.000 dibujos** (tiles + costuras + esquinas; 31.000/7.580 ≈ 4,09, coherente con la fórmula).
- Río: **21.000+ tiles** y seguía dibujándose; el total de dibujos no se dice. Con la fórmula, del orden de **75.000–84.000** dibujos si se hiciera el mapa completo con costuras y esquinas. [cálculo propio, no dato del vídeo]

### Coste

**El vídeo no da ninguna cifra de coste.** No dice precio por imagen ni factura total. Solo dice “cheap and fast once it’s trained” del modelo local, y que el frontier es el compromiso por el detalle.

Para presupuestar nuestro caso, la cuenta es:

```text
dibujos = (2n−1)² por bloque
coste   = dibujos × precio_imagen_del_modelo
tiempo  ≈ dibujos × 1 min / 40 (paralelismo), si el proveedor lo aguanta
```

Ejemplo con nuestro 3×3: **25 dibujos**. Con un 5×5: **81**. Con un 9×9: **289**. A 1 min y 40 concurrentes, 289 dibujos son **~7 minutos de reloj** en teoría; en la práctica el cuello es el rate limit del proveedor, no el tiempo de cómputo.

---

## 6. Errores que cometieron y qué cambiaron

| Error | Síntoma | Cambio | Hora |
|---|---|---|---|
| Entrenar un modelo pequeño con ejemplos del grande | Resultado **soft, bland, safe**; bordes blandos y textura uniforme | Pasar a **frontier model, una tile por llamada, sin entrenar** | 3:12–3:33 |
| Paletas de los mapas de referencia | Colores **lavados, grises** | Stack de **tres filtros** y re-procesar todo el mapa | 1:38–1:46; 7:33–7:50 |
| Dibujo blando al acercarse | Edificios sin borde, todo se funde en la misma textura | Frontier + style reference + píxel duro; el detalle es el objetivo | 1:46–2:01 |
| Costuras entre tiles | Carretera desplazada, árbol cortado, verde distinto | Tira de mitades + rojo en cuartos exteriores + redibujar centro + fundido | 4:31–5:11 |
| Zonas uniformes | Se ven los cuadrados aunque las costuras estén bien | **Guía de color**: dibujar el área entera una vez y redibujar cada tile con su trozo | 5:26–6:08; 7:13 |
| Mar dibujado por tiles | Cada tile un mar distinto | **Mar por código**: una textura repetida + profundidad real; dos paletas (mar y bahía) | 7:50–8:18 |
| Look plano | Dibujos correctos pero sin vida | Tres filtros apilados; cada tile pasa por el mismo archivo | 7:33–7:50 |
| 3D desfasado | Edificios demolidos, terminal inexistente, barrio nuevo como pasto | **Delinear y redibujar desde satélite 2026**; fundir con borde suave | 4:24; 6:51–7:13 |
| Prompt sin regla de escala | El modelo copiaba tamaños del dibujo global y hacía árboles/coches gigantes | Frase explícita: “Never take the size of anything from Picture 1” | Prompt |
| Modelo inventando vegetación | Árboles donde no hay, palmeras convertidas en árboles genéricos | “Draw a tree only where you are certain”, “a palm stays a palm” | Prompt |
| Depth map del modelo de imagen | Profundidad plausible pero sin metros ni continuidad entre tiles | Height map del **mismo 3D y misma cámara** | 8:18–9:00 |

---

## 7. Cómo aplicarlo a TinyVigo

### 7.1 Bloque 3×3 (el primer hito)

**No son 9 llamadas: son 25.** El orden que evita rehacer trabajo:

1. **Render de los 9 tiles** con la cámara ortográfica fija (45° + 15°) y height map por tile. Guardar también building-id.
2. **Pase global de baja definición** de los 9 tiles (o de la zona si ya existe) → “Picture 1”. Sin este paso, cada tile elige su verde y se notan los cuadrados.
3. **9 tiles** con el prompt adaptado: render = Picture 2, recorte global = Picture 1, style reference fija, vecinos ya dibujados.
4. **12 costuras** (6 verticales + 6 horizontales): tira 1024×1024, rojo 256 px en cada extremo, redibujar 512 px centrales, fundir 32–64 px.
5. **4 esquinas**: misma lógica en cruz; el vídeo no muestra el recorte exacto, validar a ojo con una esquina.
6. **Filtros finales** en código (LUT + curva + saturación) sobre los 25 resultados, no en Photoshop a mano.
7. **Chequeos**: comparar cada dibujo con su render (¿se ha movido una silueta?), estadísticas de color por tile (deriva de paleta), salto en cada costura. El vídeo no los menciona; nuestro spec ya los tiene y aquí son baratos.

**Presupuesto:** 25 dibujos. A 1 min y 40 concurrentes, minutos; el coste real es 25 × precio/imagen.

**Prompt adaptado:** cambiar “Copacabana, Rio de Janeiro” por la zona de Vigo y añadir la regla de estilo: “unlit, neutral daylight, no cast shadows, no warm tint, slight ambient occlusion only; roofs, left walls and right walls with fixed gentle tones”. La luz va después, en código.

### 7.2 Ampliación a Vialia

Vialia no es solo “más tiles”: es una zona con **datos desfasados** (la noria de 2026 está donde el 3D base muestra un aparcamiento) y con un edificio nuevo. Aplicar los tres trucos de mantenimiento del vídeo:

1. **Bloque 5×5 con 1 tile de solape** sobre el mapa ya dibujado. Se dibujan 25 tiles, pero solo se conserva el **3×3 nuevo**; el anillo exterior es contexto y se usa para las costuras del borde. Así el bloque nuevo no choca con el viejo.
2. **Costuras del borde del bloque** con el mismo método (mitades + rojo + centro + fundido). No pegues el 3×3 nuevo contra el viejo sin costura: se verá el corte.
3. **Nota de tile para Vialia**: fotos de la estación, la noria y el aparcamiento; texto con qué hay, altura y qué mira a cada lado. Cada dibujo de esos tiles recibe la nota.
4. **Zona desfasada**: delinear el aparcamiento/estación y redibujar desde la ortofoto/PNOA más reciente, fundiendo con borde suave. Igual que el aeropuerto de Goiânia.
5. **La noria NO se pinta en el tile base.** Es una instalación temporal: va como **asset separado** encima, con su propio trozo de suelo, animación por código y horario. Si se pinta, hay que redibujar tiles cada temporada y se pierde la posibilidad de animarla o quitarla.
6. **Coherencia**: reutilizar la misma style reference y el mismo pase global; no crear una referencia nueva solo para Vialia o se verá el cambio de mano.

**Coste del 5×5:** 81 dibujos (25 tiles + 40 costuras + 16 esquinas), de los que se publican 9. Es el precio de no tener una costura visible en el borde.

### 7.3 Mar por código

Copiar el patrón exacto del vídeo, adaptado a la ría:

1. **Una textura de agua** de 1024×1024 dibujada **una vez** por el modelo (o pintada a mano), **tileable** (offset + wrap para comprobar que no hay costura).
2. **Repetirla** por todo el mapa con un UV continuo, no una textura por tile.
3. **Colorear por profundidad real**: LUT de 0 / 5 / 10 / 20 / 40 m. Fuente: GMRT/GEBCO (el vídeo las usa) o batimetría propia; la máscara de costa sale de OpenStreetMap.
4. **Dos paletas**: ría interior más verde, calmada y con menos contraste; mar exterior más azul y con más contraste. En el vídeo: mar 0–10–20–40 m; Guanabara 2–5–15–30 m.
5. **Surf, olas y barcos** no se generan con el agua: se conservan como sprites del dibujo o se animan por código encima.
6. **Animación**: desplazar UV y modular el brillo; nada de redibujar el mar por tile.

Esto elimina de golpe la principal fuente de deriva de color en Vigo (la ría es una gran área uniforme) y ahorra decenas de llamadas.

### 7.4 Luz y sombras por código sobre teselas pintadas neutras

El vídeo y nuestro spec coinciden: **el tile se pinta sin luz**. La luz se calcula después.

1. **Prompt de tile neutro**: “unlit, flat neutral daylight, no cast shadows, no warm tint, no glow, only slight ambient occlusion in the narrowest streets”. Cada cara (tejado, pared izquierda, pared derecha) con un tono fijo suave para que el volumen se lea incluso sin luz.
2. **Height map** en metros por píxel, mismo encuadre que el tile. Se guarda junto al tile, no se pide al modelo.
3. **Sombra del sol**: renderizar el heightfield desde la dirección del sol (shadow map ortográfico) o hacer ray marching. La sombra cae en el **primer punto de intersección**: suelo, tejado o **fachada**. Eso da el efecto de “subir por el edificio” sin pintarlo.
4. **Avión, dirigible o grúa**: el sprite se dibuja encima; su sombra se calcula con el mismo height map y la misma dirección de sol. Si se mueve, se recalcula por frame (o se precomputa una sombra por posición).
5. **Tilt-shift**: usar la altura para calcular la distancia a cámara; lo que está a la misma distancia que el punto bajo el cursor queda nítido, el resto se desenfoca. Es el mismo dato, otro uso.
6. **Falda de terreno**: donde el heightfield cae bruscamente (Castro, laderas), extruir una falda en el lado lejano; si no, el mapa parece una maqueta plana.
7. **Hora y noche**: la misma sombra se atenúa al ponerse el sol; la noche es un multiply azul + ventanas encendidas por código, no un segundo set de tiles.

**Regla de oro:** si la sombra está pintada en el tile, no se puede mover con la hora, no se puede reutilizar para el avión y no se puede apagar de noche. Todo lo que sea luz, sombra o agua va en código.

---

## 8. Lo que el vídeo no dice (para no inventar)

- **Modelo exacto y versión:** solo “OpenAI’s image model, through Codex”. No hay nombre, precio ni parámetros.
- **Coste total:** no hay cifra. Ni por imagen ni por mapa.
- **Ancho del fundido de costuras:** no lo dice; 32–64 px es una elección nuestra.
- **Recorte exacto de la esquina de 4 tiles:** no lo muestra; la lógica en cruz es inferencia.
- **Filtros concretos:** dice “tres filtros” en Photoshop, pero no cuáles. Nuestro equivalente debe ser una LUT/curva versionada en código.
- **Resolución de salida y seed:** no se dicen.
- **Google Photorealistic 3D Tiles:** es el input del vídeo, pero **no está disponible para proyectos facturados en el EEE**. Nuestro render parte de PNOA + 3D del Concello + OSM. Los trucos son del método, no del proveedor; se aplican igual.
- **“2016” vs “2026”:** los subtítulos dicen 2016 en un punto y 2026 en otro; el fotograma y la descripción dicen **2026**. Usar 2026.

---

## 9. Checklist para el bloque 3×3

- [ ] Render 1024×1024 de los 9 tiles, cámara ortográfica fija, height map y building-id por tile.
- [ ] Pase global de baja definición de la zona → Picture 1.
- [ ] Style reference elegida y congelada (una sola para todo Vigo).
- [ ] Prompt con las tres reglas: posición/tamaño del render, nada inventado, sin texto ni bordes.
- [ ] 9 tiles + 12 costuras + 4 esquinas = **25 dibujos**.
- [ ] Costuras: mitades, rojo 25 % + 25 %, centro 50 %, fundido 32–64 px.
- [ ] Filtros finales en código sobre los 25, no a mano.
- [ ] Chequeo de siluetas, color por tile y salto en cada costura.
- [ ] Mar: una textura tileable + LUT de profundidad, cero llamadas.
- [ ] Luz: ninguna sombra pintada; height map listo para sol, avión y tilt-shift.
- [ ] Vialia: 5×5 con solape, nota de tile, zona desfasada, noria como asset aparte.
