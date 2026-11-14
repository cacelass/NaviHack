# El puerto del mapa (v6) está roto: qué pasa, por qué y cómo se arregla

Hallazgo del agente de georreferencia, **con las imágenes delante**. Sustituye a la nota
anterior, que recomendaba rellenar el mar con `cv2.inpaint`: se probó y queda una mancha
borrosa; no sirve. No hay parche de código que arregle esto.

## Cómo se ve

En `web/tiles/v6-pulido-arbol`, la banda del puerto (lienzo 3072, x 1024–2048, y 512–1536):

- Un **rectángulo con bordes rectos** (arriba y a la derecha) donde cambia el dibujo.
- El **edificio grande con patio y las tres torres salen duplicados**, uno encima del otro.
- **No está el muelle largo en diagonal ni la dársena con barcos** que sí tiene el render.
- Una **orilla de arena como pegatina** alrededor de todos los muelles, e islotes sueltos en el mar.

Comparación: `work/render-expansion/` → `puerto-render-vs-v6.png` y `puerto-v4-v5-v6.png`.

## Por qué

1. La tesela r0c1 (el puerto, con muelle y dársena) **nunca se pintó**: lo guardado en
   `work/tiles-p3/draw_r0c1.png` es el render tal cual, en foto. Se trató como «tesela de
   mar» aunque tiene tierra. En v5 se ve: muelle fotográfico pegado a un dibujo.
   `draw_block.py` tiene la opción `--flat-sea` («sin muelles, sin tierra»), pensada para mar puro.
2. Entre foto y dibujo quedó una costura horizontal enorme (la peor del informe, 144 de salto).
3. `seam_redraw.py --kind h --row 1 --col 1` (ledger 15:29, `seam-h-r1c1`, caja 1024,512–2048,1536)
   intentó arreglarla con el método del vídeo, pero **una de las dos mitades de la tira era foto
   sin pintar**; el modelo inventó una ciudad que no existe. Eso es v10 = lo que sirve la web.

El método del vídeo no falla aquí: falla la entrada. «Garbage in» a la tira de costura.

## Qué hay que hacer (en este orden, solo el pintor puede)

1. **Pintar r0c1 de verdad**, con el prompt normal (sin `--flat-sea`). El mar se sustituye
   después **por código** con la máscara de agua, conservando muelle y barcos del dibujo,
   como en el vídeo («surf, olas y barcos se conservan del dibujo encima»).
2. **Descartar el parche** de `seam-h-r1c1` y rehacer las costuras que tocan r0c1 con el
   método del vídeo: V r0 (c0|c1 y c1|c2), H c1 (r0|r1) y las dos esquinas de la fila 0.
3. Quitar el halo de arena (`shore` en `assemble_block.py`).

Las entradas de pintura de r0c1 y de la zona nueva están preparadas en
`work/render-expansion/pack/` (render, muestra de estilo de v6, tiras de vecinas).

## Qué no se debe hacer

- No usar `inpaint` ni «mar plano» sobre v10: probado, deja manchas y muñones.
- No pegar la columna nueva contra v6 sin costura (el vídeo, §7.2).
