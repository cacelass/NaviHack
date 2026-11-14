# Zona nueva hacia Vialia: estado y qué queda

Escrito por el agente de georreferencia y render. Actualizado a v10.

## Publicado en `main`

| Versión | Qué trae |
|---|---|
| v7-puerto-vialia | Puerto repintado (3 ventanas a caballo entre filas) y primera zona de Vialia |
| v8-este-ampliado | Una columna más al este (5120×3072), muelle norte completo, ventanas repintadas con referencia de estilo, mar por código |
| v9-noria | v8 + la noria dibujada en el aparcamiento de Vialia (mismo método que el árbol) |
| **v10-costura-izq** | v9 + ventana nueva sobre la costura más fea del 3x3 (`H y=2048`, columna 0) |

`canvas` = 3072 en todos, así que los puntos y el tour no se mueven. `on_map` sale del manifest publicado.

## Lo que cuesta llamadas de imagen y está guardado

Todo en `~/proyectos/NaviHack/work/` (el `work/` de cada worktree está fuera de git y se pierde al borrarlo):
`puerto/`, `zona/`, `estilo/`, `estilo2/` (ventanas pintadas; `*_fallida.png` son las que salieron mal),
`noria/`, `seams/` y `seamwin/` (costuras). Receta y prompts en `pipeline/render/zona/`.

## Lecciones que cuestan caro olvidar

1. **La referencia de estilo copia contenido.** Con el recorte de 512 px del centro, el modelo puso casas sobre el
   muelle de maderas, una estación sobre una autovía, bloques en rojo carmín y un tinte naranja. Cada ventana se
   repintó con una línea explícita de «no inventes X» (`reroll-prompt-*.txt`). **Revisar cada ventana a ojo contra el
   render antes de integrarla**: las métricas de color no lo detectan.
2. **La tesela del puerto no se pinta sola.** Es casi toda mar y el modelo hace zoom e inventa. Se pinta en ventanas de
   1024 px a caballo entre dos filas.
3. **Umbral de la máscara.** El del árbol (15) sirve para un objeto macizo. Para estructuras finas (radios) el modelo
   retoca todo el recorte y la máscara cubre el 58 %; con 30 queda la silueta (9,7 %). Ver `noria.py`.
4. **El mar va por código y de una vez** (`pipeline/render/sea.py`), no por tesela.
5. **Redibujar una costura ya pintada no funciona con este modelo.** Probado en `H y=2048 col0` (1,99×):
   - Con el método del vídeo tal cual (`pipeline/seam_redraw.py`, solo la tira teñida de rojo): la métrica de salto
     dice «arreglado» (0,91×) pero el modelo **inventa otro barrio** (de calles diagonales a cuadrícula con parque).
     Correlación de bordes con el render 0,36 → 0,04.
   - Pasándole además el render de la misma caja como ancla: ya no inventa (0,357) pero **copia las dos mitades,
     raya incluida** (1,85×). No arregla nada.
   - **Lo que sí funciona: pintar una ventana nueva desde el render** centrada en la costura, con la referencia de
     estilo y «no inventes» (`zona/seam-window-prompt.txt`), e integrarla con `port_fix --hard-left`. 1,99× → 1,01×,
     el trazado se conserva y la ventana no se nota como bloque.
6. **La métrica de salto de color sola engaña**: una tira inventada y uniforme siempre «casa». Mirar siempre también la
   fidelidad al render (`pipeline/render/fidelity.py`) y la imagen. Referencias: original 0,36; inventado 0,04;
   ventana buena 0,23.

## Herramientas nuevas

- `pipeline/render/seam_metric.py imagen.png`: salto de color de cada costura frente a lo normal dentro de una tesela.
- `pipeline/render/fidelity.py render.png x0 y0 x1 y1 imagen.png ...`: correlación de bordes con el render.
- `pipeline/render/port_fix.py`: integra una ventana pintada (`--extend --hard-left --hard-right --cut-top`).
- `pipeline/render/sea.py`, `edge_fix.py`, `noria.py`, `fetch_ortho.py --north-cap`.

## Queda

- **Costuras restantes del 3x3** (media 1,26×): `V x=1024 fila2` 1,60×, `V x=2048 fila1` 1,58×, `H y=2048 col2` 1,37×,
  `V x=2048 fila2` 1,36×, `V x=1024 fila1` 1,34×, `H y=2048 col1` 1,30×. Mismo método (ventana centrada en la
  costura), una llamada cada una; cuidado con repintar encima de ventanas ya buenas.
- **Noche de la noria** encendida por código, como el árbol: vive en `web/ui` (no es de este agente).
- **Marcador de la noria**: oculto por `PAINTED` en `web/js/points.js`; si algún día se quiere, quitarla de ahí.
- GEAS estuvo caído; GEO-01 y ZONE-02 siguen sin cerrar en el ticket.
