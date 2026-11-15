# pipeline/render: del render al mapa publicado

Manual de uso. El **porqué** de cada decisión, lo que falló y las cifras están en
[`docs/investigacion/expansion-vialia.md`](../../docs/investigacion/expansion-vialia.md): léelo antes de
repintar nada, porque varias cosas «obvias» no funcionan con este modelo.

Todo se ejecuta desde la raíz del repo. Los PNG grandes y las ventanas pintadas **no están en git**
(`work/` está en `.gitignore`; pintar cuesta llamadas de imagen). Copia de seguridad en
`~/proyectos/NaviHack/work/`.

## Qué hace cada módulo

| Módulo | Para qué |
|---|---|
| `../georef.py`, `../georef.ts` | lat/lon ↔ píxel del lienzo (y coordenadas del visor). Mismo cálculo en Python y TypeScript |
| `params.py` → `render-params.json` | saca la cámara y el origen **del renderer original** (no hay constantes a mano) y define los lienzos `3x3`, `expansion` y `wide` |
| `fetch_ortho.py` | baja la ortofoto PNOA que falta, alineada a la rejilla de 0,4 m de la vieja |
| `fetch_buildings.py` | baja los edificios del Concello que faltan (`pipeline/render/original/edificios_este.json`) |
| `scene.py` + `templates/` | prepara la carpeta que pinta el navegador: render, mapa de alturas y mapa de ids de edificio |
| `serve.py` | servidor mínimo que guarda los PNG que mandan las páginas del navegador |
| `silhouette.py`, `validate_points.py` | predicen la altura de cada píxel con los edificios y la cámara (comprobar la georreferencia) |
| `calibrate_origin.py` | contrasta el origen del lienzo con el mar del MDT05 (desfase en px y metros, por mitades) |
| `pack_tiles.py` | prepara las entradas de pintura de una tesela (render, muestra de estilo, tiras de vecinas) |
| `port_fix.py` | integra una **ventana pintada** en el mapa (color, mar por código, fundido) |
| `sea.py` | mar por código para todo el mapa de una vez |
| `edge_fix.py` | quita la viñeta oscura que el modelo deja a veces en el borde |
| `noria.py` | dibuja un objeto suelto (la noria) con una llamada y una máscara suave |
| `seam_metric.py`, `fidelity.py` | miden salto de color en costuras y fidelidad al render |
| `zona/` | prompts y recetas exactas de integración (ver abajo) |

## 1. Georreferencia

```bash
python3 -m pipeline.render.params            # regenera render-params.json
python3 -m pipeline.render.params --check    # falla si está desfasado (lo ejecuta un test)
.venv/bin/python -m pytest tests/test_georef.py -q
```

Contraste del origen con una fuente independiente (el mar del MDT05 del IGN, que sale a 0,0 m):

```bash
python3 -m pipeline.render.calibrate_origin --render work/render-wide/render.png --canvas wide --sweep \
  --json pipeline/render/fixtures/origin-calibration-wide.json
python3 -m pipeline.render.calibrate_origin --render ~/Downloads/vigo-bloque-3x3/render/render.png --canvas 3x3 --sweep
```

Da el desfase en píxeles y en metros de suelo para toda la zona y por mitades, con barrido del umbral de mar
(0,5 a 2,0 m). **Léelo con cuidado:** el MDT05 tiene celdas de 5 m, así que desfases de ~3 m están en su ruido; una
mitad con la costa recta sale «INDETERMINADO» (problema de la apertura) y no cuenta. El resultado y su
interpretación están en `docs/investigacion/expansion-vialia.md` §4.1.

Los tests que necesitan numpy y OpenCV (`tests/test_calibrate_origin.py`) **se saltan** en el entorno del proyecto
(`.venv`, que no los trae). Para ejecutarlos de verdad:

```bash
python3 -m venv --system-site-packages /tmp/opencode/venv-np && /tmp/opencode/venv-np/bin/pip install -q pytest
/tmp/opencode/venv-np/bin/python -m pytest tests/test_calibrate_origin.py -q
```

```python
from pipeline import georef
p = georef.params()
p.to_pixel(42.234, -8.7135)                    # (lat, lon) -> píxel del lienzo 3x3
p.to_pixel(42.234, -8.7135, canvas="wide")     # mismo punto en el lienzo ancho (mismo origen)
p.to_latlon(3261.4, 2526.3)                    # píxel -> (lat, lon) del suelo
p.to_osd(42.234, -8.7135)                      # coordenadas de viewport de OpenSeadragon
```

## 2. Render de un lienzo ampliado

El render del 3×3 salió de una ortofoto vieja de 5500×6800 px (`ortho.jpg`, 0,4 m/px) que **no está en git**:
hay una copia en `~/Downloads/vigo-bloque-3x3/work/ortho.jpg` y otra en
`~/proyectos/NaviHack/work/render-expansion/ortho/old.jpg`.

```bash
OUT=work/render-wide
# 1. ortofoto: franja nueva al este (alineada a 0,4 m) + el hueco de arriba (--north-cap)
python3 -m pipeline.render.fetch_ortho --out $OUT/ortho --old <ruta>/ortho.jpg                 # expansion (4096)
python3 -m pipeline.render.fetch_ortho --out $OUT/ortho --canvas wide --from-x 1617.6 --north-cap  # wide (5120)
# 2. edificios del Concello que faltan
python3 -m pipeline.render.fetch_buildings
# 3. escena y servidor
python3 -m pipeline.render.scene --out $OUT --canvas wide
python3 -m pipeline.render.serve $OUT --port 8097 &
# 4. pintar en el navegador (uno solo a la vez, el PC va justo de RAM): cada página guarda su PNG
for pg in render height ids; do
  agent-browser open http://127.0.0.1:8097/$pg.html
  agent-browser wait --fn "document.title === 'READY'"
done
```

Salidas: `render.png` (foto con volúmenes), `height.png` (canal rojo = altura en metros × 4) e `ids.png`
(índice de edificio + 1 en RGB; 0 = suelo). Tardan 1-2 minutos cada una.

## 3. Pintar una ventana

Se pinta en **ventanas de 1024 px**, no en teselas sueltas ni en costuras. El plan de las 13 ventanas del mapa
publicado está en `zona/wide-plan.json` (origen, filas que se descartan arriba y qué prompt lleva).

```bash
python3 - <<'EOF'
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
Image.open("work/render-wide/render.png").convert("RGB").crop((4096, 1894, 5120, 2918)).save("work/estilo/render_e1_b2.png")
EOF
# muestra de estilo: 512 px del centro ya dibujado (NO la tesela entera: el modelo copia el contenido)
python3 -c "from PIL import Image; Image.open('work/tiles-p3/draw_r1c1.png').crop((256,256,768,768)).save('work/estilo/swatch512.png')"
MODEL=gemini-3.1-flash-image AR=1:1 LABEL=estilo-e1_b2 node pipeline/imggen.mjs \
  work/estilo/draw_e1_b2.png pipeline/render/zona/wide-prompt-nowater.txt \
  work/estilo/render_e1_b2.png work/estilo/swatch512.png
```

- Con agua en la ventana: `zona/wide-prompt-water.txt`. Sin agua (si lleva mar el modelo se inventa ensenadas): `wide-prompt-nowater.txt`.
- Si el modelo inventa algo, repetir con una línea explícita de «no inventes X»: ver `zona/reroll-prompt-*.txt`.
- **Mirar cada ventana al lado del render antes de integrarla.** Ninguna métrica detecta casas sobre un muelle.
- Cada intento queda apuntado en `pipeline/ledger/image-calls.jsonl` (cuenta las líneas `OK`). Los 429 se reintentan solos.

## 4. Integrar, mar y bordes

```bash
# una ventana
python3 -m pipeline.render.port_fix --extend --base BASE.png --render work/render-wide/render.png \
  --window work/estilo/draw_e1_b2.png --origin 4096 1894 --fade 99990 100000 --hard-right --out SALIDA.png
```

| Opción | Efecto |
|---|---|
| `--origin X Y` | esquina superior izquierda de la ventana en el lienzo |
| `--cut-top N` | filas de la ventana (desde arriba) que **no** se usan: ya las cubre la anterior |
| `--hard-right`, `--hard-left` | sin fundido en ese lado (borde del lienzo, o lo cubrirá la ventana siguiente) |
| `--fade Y0 Y1` | fundido por abajo entre esas filas del lienzo (solo para respetar el árbol; `99990 100000` lo anula) |
| `--extend` | amplía el mapa al tamaño del render rellenando con mar por código |
| `--drop-floaters` | quita trozos de tierra sueltos en mar abierto |

La **receta completa y en orden** de las 13 ventanas es `zona/integrate_wide.sh` (base `work/puerto/v14.png`).
Después:

```bash
python3 -m pipeline.render.edge_fix --base work/estilo/v17.png --render work/render-wide/render.png --rows 0 1000 --out work/estilo/v17c.png
python3 -m pipeline.render.sea      --base work/estilo/v17c.png --render work/render-wide/render.png --out work/estilo/v18c.png
```

La máscara de agua pesa (6 min en 5120 px); `port_fix.get_water` la guarda en `/tmp/opencode/port_fix_cache/`
(25 s la segunda vez). Si cambias el render, la clave (md5 del contenido) cambia sola.

## 5. Un objeto suelto sobre el mapa (noria, árbol)

```bash
python3 -m pipeline.render.noria --canvas work/estilo/v18c.png --center 4310 2245 \
  --photo work/noria/foto-noria.jpg --call --out-dir work/noria --out work/noria/v19.png
# repetir la composición sin gastar otra llamada:
python3 -m pipeline.render.noria --canvas work/estilo/v18c.png --center 4310 2245 \
  --from-file work/noria/respuesta1024.png --out-dir work/noria --out work/noria/v19.png
```

Recorta una caja de 350 px, la sube a 1024, pide el objeto al modelo y pega **solo** lo que cambia (máscara
suave por diferencia real). Lo de fuera de la máscara queda bit a bit igual y el script lo comprueba.
`--mask thin` (por defecto) sirve para radios y líneas finas; `--mask solid` es la del árbol.

## 6. Comprobar antes de publicar

```bash
python3 pipeline/render/seam_metric.py MAPA.png                       # salto de cada costura (1,0 = no se nota)
python3 pipeline/render/fidelity.py RENDER.png 0 1792 1024 2304 MAPA.png   # ¿sigue el dibujo al render?
```

**Las dos a la vez**: el salto de color solo se puede «arreglar» inventando una tira uniforme, y la fidelidad
sola no ve las costuras. Referencias: el dibujo original de una banda correlaciona 0,36 con el render, el
inventado 0,04 y una ventana buena 0,23. Y siempre **mirar la imagen**.

## 7. Publicar

```bash
python3 scripts/build_pyramid.py --image work/seamwin/s3.png --version v10-costura-izq \
  --canvas 3072 3072 --offset 0 0 --set-current          # nunca sobrescribe una versión existente
python3 -m scripts.build_web_data                         # on_map según el tamaño publicado
python3 -m scripts.serve_web --port 8000 --no-open        # y mirarlo en un navegador
```

- `--canvas 3072 3072` es lo que mantiene en su sitio los puntos y el tour aunque la imagen sea más ancha.
- `build_web_data` también reescribe `web/data/i18n/*` y el bloque incrustado de `web/index.html`; si no son
  tuyos, no los incluyas en el commit (`git checkout -- web/data/i18n web/index.html`).
- Comprobación en navegador: 0 teselas con error (`performance.getEntriesByType('resource')`) y mirar la zona tocada.
