# Señales del planner (D-12)

`scripts/signals.py` → `Signals.load()` y, por tramo, `leg_factor(a, b, hora, modo)`.

| Opción | Señal | Fuente | Efecto | Sin datos |
|---|---|---|---|---|
| After dark | Luces de Navidad **encendidas a esa hora** a ≤ 40 m del tramo | `points.json` + horario R-04 | coste × (1 + 0,6 × fracción a oscuras), solo tras la puesta de sol (NOAA, ±10 min) | factor 1,0 + `missing:lights` |
| Easy walk | Pendiente máxima del tramo | MDT05 (D-11) | `elevation.easy_walk_factor`: 1,0 hasta 6 %, sube hasta ×2 a 12 %, ×4 por encima | factor 1,0 + `missing:elevation` |
| Easy walk | Bancos y cafés a ≤ 60 m en tramos > 150 m | OSM (Overpass, `data/osm/rest_core.json`, 62 bancos + 52 cafés en el núcleo, ODbL) | × 1,15 si no hay ninguno | `missing:rest_spots` |
| Todas | Lluvia en la ventana de la ruta | Open-Meteo (D-10) | aviso `planner.rain_warning` si la probabilidad máxima ≥ 50 % | sin aviso + `missing:weather` |
| Todas, con lluvia | Paradas `covered: true` | overrides / recintos bajo techo | coste de la parada × 0,7 | — |

- **Determinismo:** misma entrada (incluida la hora y el snapshot del tiempo) → mismos factores.
- **Aparcamiento:** el aviso de ocupación > 90 % queda fuera hasta que el equipo lo confirme (no está en el spec v4, duda 6 de la propuesta v4).
- **Atribución nueva para D-17:** «© OpenStreetMap contributors (ODbL)» por los bancos y cafés.
