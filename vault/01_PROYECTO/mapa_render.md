# Mapa isométrico: render, pintado y publicación (GEO-01, ZONE-02)

Las reglas en una página. El porqué, las cifras y lo que falló: `docs/investigacion/expansion-vialia.md`. Los
comandos: `pipeline/render/README.md`.

## Estado

El mapa publicado es `v10-costura-izq`: 5120×3072 px, 2 px/m, cámara ortográfica a 45° con giro de −15°, centrado
en Porta do Sol (`42.23807, −8.72581`). Cubre desde el puerto hasta pasada Vialia. Todas las versiones llevan
`canvas 3072` en su manifest, así que los puntos y el tour no se mueven aunque la imagen crezca hacia el este.

## Reglas que no se discuten

1. **Georreferencia: `pipeline/georef.py` / `georef.ts`.** Las constantes salen del renderer original
   (`pipeline/render/params.py`), no se escriben a mano. Origen contrastado con el mar del MDT05: ≤ 4 m (≤ 8 px),
   sin corregir.
2. **El modelo copia lo que ve.** Referencia de estilo = recorte de 512 px del centro, nunca la tesela entera, más una
   línea explícita de «no inventes X». Mirar cada ventana pintada contra el render antes de integrarla.
3. **Se pinta en ventanas de 1024 px**, solapadas 64 px, no en teselas sueltas (lo que es casi todo mar se inventa) ni
   en costuras.
4. **Redibujar una costura ya pintada no funciona con este modelo** (copia el fallo o inventa un barrio). Se pinta una
   ventana nueva centrada en la costura, desde el render.
5. **El mar va por código y de una vez** para todo el mapa (`pipeline/render/sea.py`), no por tesela. La máscara de
   agua es de color + conectividad y se valida contra la geometría del MDT05 (IoU 0,80-0,86).
6. **Un objeto suelto** (árbol, noria): una llamada sobre un recorte de 350 px y se pega solo lo que cambia, con
   máscara suave; fuera de la máscara el mapa queda idéntico. Para líneas finas, umbral de máscara 30, no 15.
7. **Una métrica sola engaña.** Salto de color en costuras + fidelidad al render + mirar la imagen, siempre las tres.
8. **Cada versión publicada es nueva** (`scripts/build_pyramid.py` se niega a sobrescribir) y se mira en el navegador
   (0 teselas con error) antes de darla por buena.
9. **Lo pintado cuesta llamadas y vive fuera de git** (`work/`). Copia en `~/proyectos/NaviHack/work/` y cada
   llamada queda en `pipeline/ledger/image-calls.jsonl`.

## Dónde mirar

| Para | Mira |
|---|---|
| Repetir o ampliar el mapa | `pipeline/render/README.md` |
| Entender por qué cada regla | `docs/investigacion/expansion-vialia.md` |
| El método del vídeo y dónde no se cumplió | `docs/investigacion/tinygyn-video-trucos.md` §11 |
| Prompts y recetas de integración | `pipeline/render/zona/` |
| Qué queda por hacer | `docs/investigacion/expansion-vialia.md` §9 |
