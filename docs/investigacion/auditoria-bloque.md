# Auditoría del bloque 3x3 (MAP-03)

Hecha sobre `work/tiles-p3/draw_r*c*.png` (las 9 teselas pintadas de BASE-01) ensambladas con
`pipeline/assemble_block.py`. Todas las medidas son de código (métricas o estadísticas de píxel), no
solo a ojo; las imágenes de referencia están en `work/assets/` o se regeneran con los comandos dados.

## 0. Cómo se generó esta auditoría

```bash
python3 pipeline/assemble_block.py --tiles work/tiles-p3 \
  --render ~/Downloads/vigo-bloque-3x3/render/render.png \
  --out work/tiles-p3/ensamblado-v9.png --flat-sea --finish
```

`v9` es la versión con todos los arreglos de código de esta auditoría aplicados (ver §5). `v6` es la
versión anterior (la que vio Jose en `cmp-v6.png`), sin ninguno de estos arreglos.

## 1. Mar y orilla

| Defecto | v6 (antes) | v9 (después) | Cómo se verificó |
|---|---|---|---|
| Balsa de agua oscura y plana en el dique del puerto (x≈0-300, y≈1390-1810 en el lienzo 3072; x≈0-100,y≈470-600 a escala 1024) | Sin tocar: `water_mask()` solo guardaba la componente que toca el borde norte, y un muelle estrecho (un almacén) desconecta el dique del color del mar abierto en el umbral de color crudo | Incluida: +69 504 px de agua (3 350 476 → 3 419 980), igual de clara que el resto de la ría | `assemble_block.water_mask()`; medido con `cv2.connectedComponentsWithStats` antes/después, ver commit de la máscara |
| Halo pálido alrededor de muelles/punta del puerto | Parcial: el borde de `water_mask` se quedaba corto en el dique anterior y en los bordes recortados por barcos/muelles estrechos | Reducido: la máscara por geometría+uniformidad (ver abajo) ya no deja bordes "a medias"; sigue habiendo un borde de 2 px de `cv2.dilate` en la orilla de arena (`shore`), deliberado, no un error | Inspección visual de `work/assets/raft-v8.png` / `raft-v9.png` |
| Mar con rayas diagonales muy regulares ("se ve generado") | `sin((y+x)*0.035)*2.2 + sin(y*0.05+x*0.02)*1.6` — dos senos, periodicidad visible a simple vista | `water_texture()`: 4 octavas de ruido de valor (campo aleatorio de baja resolución, difuminado y escalado) con amplitud decreciente + destellos puntuales dispersos (density 0.15%). Sin periodicidad: cada parche de mar es distinto | Comparar `cmp-v6.png` vs `cmp-v9.png`, zoom al mar norte |

**Cómo se decidió que la balsa era agua y no una sombra** (la regla pedía nunca usar solo un umbral de
color): se midió la desviación típica de color y el sesgo azul (B−R) de cada componente conectada de
"agua candidata" que NO toca el borde norte, en todo el bloque:

| Componente | área (px) | std color medio | B−R medio | ¿Es agua? |
|---|---:|---:|---:|---|
| Mar abierto (toca el norte) | 3 350 476 | 6.2 | 34.0 | sí, referencia |
| Dique del puerto (la balsa) | 68 010 | 7.1 | 26.9 | **sí** — tan uniforme como el mar |
| Sombra bajo arbolado del Castro (×6 manchas, 2 000-48 000 px) | 2 000-47 752 | 12.6-19.8 | 17.3-28.8 | **no** — mucho más moteada (follaje) |

El agua real tiene std < 10; las sombras de árboles, aun siendo oscuras y algo azuladas, tienen std ≥
12.6 porque la luz que se filtra entre las hojas rompe la uniformidad. Ese umbral (std < 10 y B−R > 15,
área > 1000 px) es lo que añade `water_mask()` a la regla de "toca el borde norte", en vez de relajar la
conectividad a cualquier blob grande (eso sí habría pintado media ladera del Castro como mar).

## 2. Costuras

Métrica: salto de color medio (ΣRGB |Δ|) a ±3 px de cada costura, cada 4 px a lo largo de toda su
longitud, **después** de aplicar todos los arreglos de código (de-vigñeteado, color-matching,
`blend_seams`, `blend_corners`). Línea base: salto medio en 10 cortes verticales aleatorios dentro de
una tesela (no en una costura) = **43** (rango 35-51) — es el ruido de contraste normal de una ciudad
densa, no cero.

| Costura | salto medio | p90 | vs línea base |
|---|---:|---:|---|
| V columna 1, fila 0 | 49.6 | 84.0 | 1.2× — dentro de lo normal |
| V columna 1, fila 1 | 88.6 | 182.3 | 2.1× |
| V columna 1, fila 2 | 90.1 | 188.3 | 2.1× |
| V columna 2, fila 0 | 57.7 | 80.0 | 1.3× |
| V columna 2, fila 1 | 86.2 | 164.2 | 2.0× |
| V columna 2, fila 2 | 85.4 | 169.7 | 2.0× |
| H fila 1, columna 0 | 107.4 | 145.3 | 2.5× |
| **H fila 1, columna 1** | **144.8** | **319.3** | **3.4×** — la peor |
| H fila 1, columna 2 | 140.2 | 178.2 | 3.3× |
| H fila 2, columna 0 | 116.5 | 227.3 | 2.7× |
| H fila 2, columna 1 | 88.3 | 191.0 | 2.0× |
| H fila 2, columna 2 | 90.7 | 191.5 | 2.1× |

**Lectura:** las costuras verticales de la columna 0 (borde oeste del centro) ya están en el rango
normal tras el arreglo de código — sin más que hacer ahí. El resto (10 de 12) siguen en 2-3.4× la línea
base. Mirado a zoom (`work/assets/cross-v9.png`, costura H fila 2 / columna 1, que cruza con la columna
0-1 en la esquina (1536,2048)): el salto no es solo de luz — es la **esquina de 4 teselas**, donde las
cuatro tienen una interpretación de tejado/calle ligeramente distinta en la misma huella. Un ajuste de
color (`blend_corners`, nuevo en esta auditoría, difumina un parche de 192 px alrededor de cada una de
las 4 esquinas interiores) **no cambió el salto medible** en ese punto: la discrepancia es de contenido,
no de color, exactamente lo que el vídeo de tinygyn (`tinygyn-video-trucos.md`, §2) dice sobre las
esquinas — "la aplicación coherente del mismo principio" (mitades + rojo + redibujar centro) es la única
vía, no un filtro.

**Banda clara encima del puerto (x≈340-640, y≈345 a escala 1024 → x≈1020-1920, y≈1035 en el lienzo):**
confirmado en bruto en `draw_r1c1.png`: sus 150 px superiores tienen L medio 177→160 bajando
gradualmente (vignette del propio modelo, sobrevive a `--no-blend`, así que no es una costura) frente a
L≈120-130 en el interior de la tesela. `devignette()` (nueva) quita una tendencia lenta (blur gaussiano
σ=180, un sexto de la tesela) del canal L de cada tesela por separado: reduce el salto en esa zona en
13.9 de media (`work/assets/paleband-v8.png` vs `v7`). El residuo que queda al mirarlo es, comparado con
el render (`paleband-render.png`), el propio edificio del Náutico/Centro de Congresos, que es
realmente de un beige claro — no es ya un defecto, es contenido correcto.

## 3. Coherencia entre teselas

| Medida | Resultado |
|---|---|
| Escala de los edificios | No medida con una métrica automática en esta pasada (pendiente: comparar la altura en píxeles de 3-4 edificios iguales en teselas vecinas contra el render). A ojo en `cmp-v9.png` no hay un cambio de escala evidente entre teselas. |
| Paleta (LAB, teselas de tierra) | Ya corregida por `match_colour()` desde BASE-01 (media y std de cada tesela movidas hacia la tesela central); no se ha vuelto a medir la deriva residual en esta auditoría — **pendiente**. |
| Desplazamiento de contenido vs render | `alignment()` en `assemble_block.py`: desplazamiento de fase 0.3 px, respuesta de fase 0.21, IoU de la máscara de agua 0.96 — el dibujo está bien alineado con el render en conjunto. No descarta desplazamientos locales pequeños dentro de una tesela. |
| Orientación de sombras pintadas | No medida (requeriría detectar la dirección del degradado de sombra por tesela; el spec ya prevé que la luz vaya por código — ver `LIGHT-01`/`LIGHT-02` — así que esto deja de ser relevante en cuanto esa feature sustituya las sombras pintadas). |
| Contenido inventado | No se ha repetido el barrido manual de REPORT.md (BLOCK-01) sobre las 9 teselas finales; ese informe ya documentó un barco de más y un tejado rojo puro en una costura de una pasada anterior — pendiente confirmar si sobreviven en `draw_r*c*.png` actuales. |

## 4. Bordes del bloque y zonas vacías

Sin huecos ni zonas en blanco dentro del 3x3; los 4 bordes exteriores del bloque (no son costuras
interiores) no se han comparado contra lo que habrá alrededor hasta que exista la expansión de Vialia
(ZONE-02) — en ese momento se les aplicará el mismo tratamiento de costura.

## 5. Qué se arregló por código en esta pasada (sin gastar llamadas)

Todo en `pipeline/assemble_block.py`:

1. `water_mask()`: dique del puerto incluido por uniformidad+matiz, sombras del Castro excluidas por lo
   mismo (§1).
2. `water_texture()`: ruido de valor en 4 octavas + destellos, sustituye las dos senoides regulares.
3. `devignette()`: aplana el desvanecimiento del canal L de `draw_r1c1.png` por tesela, antes del
   ajuste de color.
4. `blend_corners()`: difuminado radial de 192 px en las 4 esquinas interiores — reduce el salto de
   color suave, pero no el de contenido (§2).

## 6. Lo que necesita repintar (no se arregla con código)

Las costuras horizontales fila 1 (columnas 0-2) y la esquina (1536, 2048) siguen en 2-3.4× la línea
base **tras** aplicar los 4 arreglos de arriba, y a zoom se ve que el salto es de contenido (tejado,
calle), no de luz. Siguiendo el método del vídeo (tira de mitades, cuartos exteriores en rojo
transparente, redibujar solo el 50% central, fundir el resultado) — ver `pipeline/seam_redraw.py` y
§7 de `tinygyn-video-trucos.md` — se van a repintar, por orden de salto medido, empezando por la
esquina y las costuras horizontales de la fila 1. Cada repintado cuenta como una llamada en
`pipeline/ledger/image-calls.jsonl`.
