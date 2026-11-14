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

## Tiempo: Open-Meteo (D-10)

- Forecast: `api.open-meteo.com/v1/forecast`, punto Porta do Sol
  (42.2376, -8.7247), `timezone=Europe/Madrid`, `forecast_days=4` → 96 horas
  con `temperature_2m, precipitation_probability, precipitation, weather_code,
  cloud_cover_low/mid/high, visibility, wind_speed_10m, wind_direction_10m,
  wind_gusts_10m`. Licencia **CC BY 4.0** (atribución «Weather data by
  Open-Meteo.com» → `D-17`). Actualiza cada 15 min; snapshot cada 30 min,
  «sin datos» a las 3 h.
- **Marine en la ría: cobertura gruesa.** `marine-api.open-meteo.com` devuelve
  la **misma celda** (42.2917, -8.7917, boca de la ría junto a Cíes) para Porta
  do Sol, el centro de la ría (42.24, -8.76) y Cíes (42.22, -8.80): ola 1,2 m,
  SST 15,6–15,9 °C (2026-11-14). Sirve como indicativo de «estado del mar en
  la boca», **no** como dato por punto dentro de la ría. No se usa en v1 más
  allá de, como mucho, un icono en la capa de tiempo.

## Capa navideña del Concello (R-06)

- **Item:** ArcGIS Online `41caae2067564a92a79d91f5a08c00f6`, «Puntos interés
  Navidad 2026 2027», dueño `concellovigo`, acceso público. Modificado
  **2026-11-13 14:25** → **la edición 2026-27 ya está publicada**, no hace
  falta esperar a la 2025-26 + overrides que suponía el spec.
- **FeatureServer:** `https://services9.arcgis.com/ss3qikvq575kYKRJ/arcgis/rest/services/Puntos_interés_Navidad_2023_2024/FeatureServer/0`
  (el nombre del servicio es de 2023-24: el Concello reutiliza el mismo cada
  temporada). Puntos, `maxRecordCount` 2000.
- **35 puntos** (no 43 como decía el spec para 2025-26): 16 elementos
  lumínicos, 8 atracciones, 4 expositivos, 2 mercados, 2 Papá Noel/Reyes,
  2 galerías de fotos, 1 photocall.
- **Campos:** `id, nombre, nombre_gl, descripcion_corta(_gl), descripcion_larga(_gl)`
  (HTML), `horario_atencion(_gl)` (HTML con horas de encendido/apagado),
  `tipologia(_gl)`, `image_url`, `imagen`, `dir_*` (vía, número, texto
  alternativo, CP, parroquia, barrio, distrito, sección), `telefono1/2, web,
  email, lon, lat`. Mapeo a `points.json` en `scripts/christmas_layer.py`.
- **Otras capas del mismo dueño** (para R-01/histórico): «Nadal Puntos de
  Interés_Pública» (36 puntos, 2019, campos `tipo, elemento, descripcion`),
  «Puntos interés Navidad 2021», «puntos_interese_2020», «Zonas Nadal 2021»,
  «Encendido 2024 Accesos», web scene «Navidad 2026-2027 3D» (`ed9c99f2…`).
- **Licencia:** el item no declara `licenseInfo` ni `accessInformation`. Se
  aplican las condiciones generales de datos.vigo.org (citar fuente y fecha de
  actualización, ver arriba). Pendiente confirmar por el canal del Concello si
  se va a redistribuir texto o fotos (`image_url`) tal cual → `LIC-01`.
- **Fallback:** cada descarga guarda la copia cruda en
  `data/raw/concello_navidad/<UTC>.json` (versionada en git). Si la capa
  desaparece o falla, `python -m scripts.christmas_layer` sigue con la última
  copia; `--offline` lo fuerza. Los cambios que el Concello aún no publique van
  a `data/points_overrides.json` (`{"id", ...campos}` parchea, un id nuevo se
  añade como `status: not_confirmed`, `"remove": true` lo quita).

## Transporte (X-01, X-02)

| Fuente | URL | Licencia | Refresco | Notas |
|---|---|---|---|---|
| Vitrasa GTFS | `https://datos.vigo.org/data/transporte/gtfs_vigo.zip` (CKAN `gtfs-vitrasa`) | ODC-BY | diario (~13:05 UTC) | 1165 paradas, 59 líneas, 132 672 salidas. `calendar.txt` vacío: todo en `calendar_dates.txt`. Lleva dentro un `Google_transit.zip` anidado (se ignora). **Solo horario programado**: no hay tiempo real oficial. |
| Avisos de transporte | `https://datos.vigo.org/data/avisos/avisos_transporte_es.json` | ODC-BY | — | «DESVÍOS NADAL 2026 / 2027» (id 4033): 11/11/2026–10/01/2027, 22 líneas, zona restringida Policarpo Sanz → 3 paradas marcadas `christmas_detour`. |
| Renfe AV/LD/MD GTFS | `https://ssl.renfe.com/gtransit/Fichero_AV_LD/google_transit.zip` | **CC BY 4.0** (Renfe Operadora) | diario (~00:08 UTC) | `Vigo Urzaiz` (08223) y `Vigo-Guixar` (22308) presentes. 185 movimientos en Vigo (84 salidas). Cabeceras rellenas de espacios. Sin Cercanías. |

Créditos para `D-17`: «Concello de Vigo — datos.vigo.org (ODC-BY)», «Vitrasa
(GTFS vía datos.vigo.org)», «Renfe Operadora (CC BY 4.0)», «Weather data by
Open-Meteo.com (CC BY 4.0)».

## Edificios 3D del Concello (X-05)

- **Servicio:** `https://services9.arcgis.com/ss3qikvq575kYKRJ/arcgis/rest/services/Edificios_3D_de_Vigo_en_vectorial/FeatureServer/0`
  (item `1196c4f7cdfa478eb9ac09b1fffc2576`), capa `EDIFICIOS`, **41 289**
  edificios, MultiPatch, EPSG:25829, `maxRecordCount` 2000, formatos JSON,
  geoJSON, PBF. Hay también SceneServer I3S (`7a4b08ad…`, `fe74b88f…`) con el
  volumen real, fuera de v1.
- **Campos útiles:** `refcat` (une con Catastro), `altura`, `z` (cota del
  tejado), `ano_antiguedade`, `ano_reforma`, `uso_principal_superficie`,
  `barrio`, `parroquia`, `distrito`, `seccion` (+ superficies por uso,
  habitantes, riesgo de inundación, radiación).
- **MultiPatch en GeoJSON: no.** `f=geojson` devuelve `Polygon` 2D;
  `f=json&returnZ=true` devuelve `rings` con z = 0. Es decir, el servidor
  aplana a huella. Para el render: extruir la huella `height_m` desde
  `base_z = z − altura`.
- **Reproyección:** `outSR=4326` en servidor; comprobada contra una
  conversión UTM 29N → WGS84 propia (`utm29n_to_wgs84`): 0,03 mm de diferencia
  en el vértice de `2565705NG2726N`.
- **Completitud de `altura`:** ciudad 40 622 / 41 289 = **98,4 %** (667 sin
  altura o ≤ 0); núcleo navideño 2 975 edificios, **99,6 %**. `ano_antiguedade`
  falta en 93; `ano_reforma` > 0 en 10 868.
- **Año de los datos por zona:** el servicio no publica la fecha de captura.
  Usamos como indicador el año más reciente (construcción o reforma) por
  barrio, en `stats.newest_year_by_barrio` del fichero exportado: un barrio
  cuyo edificio más nuevo es de hace años es candidato a «zona desactualizada».
- **Licencia:** no declarada en el item → ver `licencias.md` (pedir
  confirmación para imágenes derivadas antes de publicar tiles).
- **Fichero offline:** `data/render/buildings.geojson` (núcleo
  `-8.7320,42.2310,-8.7080,42.2430`, 1,8 MB, versionado), WGS84, un
  Polygon/MultiPolygon por edificio con `refcat, height_m, base_z, year_built,
  year_reformed, use, barrio`. Otra zona: `python -m scripts.buildings --bbox …`.
- **Fallback:** huellas de Catastro (INSPIRE, WFS de edificios) unidas por
  `refcat`; la altura saldría de plantas × 3 m, peor que la del Concello.

## Renfe en vivo (X-03) — comprobado 2026-11-14 17:33

| Endpoint | Formato | Cobertura Vigo | Frescura | Veredicto |
|---|---|---|---|---|
| `gtfsrt.renfe.com/trip_updates_LD.json` | GTFS-RT en **JSON** (no hace falta protobuf) | sí: 12 viajes del día cruzan con el GTFS de X-02 (p. ej. Vigo–Barcelona +20 min) | cabecera a 15 s | **GO** para retrasos (`scripts/renfe_live.py`, solo si la cabecera tiene < 5 min) |
| `gtfsrt.renfe.com/vehicle_positions_LD.json` | JSON | 3 trenes a < 60 km | cabecera **1 h atrasada**, entidades del día anterior | **NO-GO** para mover trenes en el mapa |
| `gtfsrt.renfe.com/trip_updates.json`, `vehicle_positions.json` | JSON | ninguna (son Cercanías) | — | no aplica |

Hasta nueva comprobación, los trenes del mapa (TRANSIT-02) van con horario programado
y etiqueta «programado»; los retrasos se pueden mostrar como texto en el tablero.
