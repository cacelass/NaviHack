# Fuentes de datos del Concello — medidas reales

> Rellenado por `D-00`. Fija los intervalos de snapshot de la sección **A7** del
> spec TinyVigo v3 con valores medidos, no supuestos. Lo consumen `D-01`
> (snapshot publisher), `D-03` (agenda loader), `D-05` (parkings), `D-18`
> (freshness UI) y `X-09`.
>
> Re-medir: `python scripts/measure_feeds.py --minutes 30 --every 20`
> (stdlib, sin instalar nada; GET condicional con `If-None-Match`, así que
> casi todos los sondeos son `304` y no cargan al servidor).

## Medición del 2026-11-14

Ventana: 11:55–12:10 UTC (≈15 min; sondeos con `curl -I` y `scripts/measure_feeds.py`), sondeo cada 20 s, desde la red del evento.

| | `parkings-ocupacion.json` | `agenda-hoy.json` |
|---|---|---|
| URL | `https://datos.vigo.org/data/trafico/parkings-ocupacion.json` | `https://datos.vigo.org/data/axenda/agenda-hoy.json` |
| Dataset CKAN | `t-parking-real` | `agenda-cultura` |
| Refresco declarado | «Actualización cada 3 minutos» (CKAN) | ninguno |
| Refresco medido | **cada 2 min**, en minuto par +4 s (`Last-Modified` 11:55:04 → 11:57:04 → 12:07:04 → 12:09:04 GMT). Más rápido que lo declarado | 1 vez al día, ~06:05 UTC (`Last-Modified: Sat, 14 Nov 2026 06:05:45 GMT`); sin cambios en la ventana |
| Timestamp de origen | `fechahora` por registro (hora local, sin zona) | ninguno: hay que usar `Last-Modified` |
| Tamaño | ~2,1 KB, 8 parkings | ~11,9 KB, 44 entradas |
| Disponibilidad | 100 % (0 errores) | 100 % (0 errores) |
| CORS | `Access-Control-Allow-Origin: *` | `Access-Control-Allow-Origin: *` |
| Caché HTTP | `ETag` + `Last-Modified` (nginx, estático) | `ETag` + `Last-Modified` (nginx, estático) |

Observaciones:

- **El fichero de parkings se reescribe con desfase.** `Last-Modified` llega
  ~4 s después del minuto de `fechahora` (p. ej. `fechahora 12:55:00` →
  `Last-Modified 11:55:04 GMT`). `fechahora` es **hora local de Madrid sin
  zona**: hay que interpretarla como `Europe/Madrid`, no como UTC.
- **La agenda no es “de hoy” en sentido estricto:** mezcla eventos con fecha y
  entradas `permanente: true` sin fechas (p. ej. «Contemplar unha posta de sol
  en Vigo»). `D-03` tiene que separar ambas y no sacar horas de aquí (las horas
  salen de `points.json`, criterio de `D-03`).
- **CORS abierto:** el navegador podría leer los feeds directo, pero el spec
  pide snapshots propios (`D-01`) para tener último-bueno, histórico y edad.

## Condiciones de uso

- Licencia de ambos datasets: **Open Data Commons Attribution (ODC-BY)**
  (`https://opendatacommons.org/licenses/by/summary/`).
- Condiciones del portal (`https://datos.vigo.org/condiciones-de-uso-de-los-datos/`,
  art. 8 Lei 37/2007): no alterar el contenido ni desnaturalizar su sentido,
  **citar la fuente** y **mencionar la fecha de última actualización**.
  → `D-17` (About) cita «Concello de Vigo — datos.vigo.org (ODC-BY)»;
  `D-18` (freshness) muestra la fecha de actualización de cada capa.

## A7 — Intervalos de snapshot (medidos)

| Feed | Intervalo de snapshot | “Sin datos” a partir de | Por qué |
|---|---|---|---|
| `parkings-ocupacion.json` | **cada 2 min**, en minuto par +30 s (p. ej. `*/2 * * * *` con `sleep 30`) | 10 min | El origen cambia cada 2 min; muestrear más rápido solo da `304`. 10 min = 5 publicaciones perdidas: tolera cortes breves sin enseñar ocupación vieja como actual. |
| `agenda-hoy.json` | 1 al día, **07:30 Europe/Madrid** (+ reintento 09:00) | 36 h | Se publica ~06:05 UTC = 07:05 en Madrid (horario de invierno); antes de esa hora el fichero aún es el de ayer. 36 h tolera un día sin publicar sin marcar “sin datos”. |

`D-01` usa `If-None-Match` con el `ETag` guardado: un `304` no es un fallo ni
genera snapshot nuevo, solo actualiza `checked_at`.
