<img src="web/favicon.svg" width="32" height="32" alt=""> TinyVigo

![TinyVigo](docs/img/web-desktop-1400.png)

> Mapa isométrico pixel art del centro de Vigo, con la Navidad encima: puntos con
> su horario real, eventos del día, rutas a pie, autobuses y trenes, y postales
> pixel art a partir de una foto propia. Mobile-first, una sola ciudad, un solo
> mapa dibujado una vez.

**Para quién:** personas que pasean por el centro de Vigo con el móvil, de día y
sobre todo por la tarde-noche (vecinos y turistas), y quien planifica una visita
corta y quiere saber qué le cabe en 1–3 horas. Uso con una mano, a la
intemperie, de noche.

## Arrancar en local

```bash
make setup      # uv sync --extra dev + hooks de pre-commit
make website    # sirve web/ en http://127.0.0.1:8000 y abre el navegador
```

Alternativa sin `make` (Windows o entorno sin make):

```bash
uv run python -m scripts.serve_web --port 8000
# o, sin uv:
python -m scripts.serve_web --port 8000 --no-open
```

La web es estática pero hace `fetch()` de los tiles, por eso hace falta un
servidor: abrir `web/index.html` con doble clic (file://) no funciona.

Comprobaciones de salud del proyecto:

```bash
./init.sh            # puerta de entrada: ¿se puede trabajar?
make test            # pytest (proyecto + agentes)
make check           # lint + typecheck + test + arnés
```

<<<<<<< HEAD
## Qué hace la web

![Tour a pie con el paseo parada a parada](docs/img/web-tour-1400.jpg)

- **Mapa dibujado del centro** (isométrico, OpenSeadragon) con los 35 puntos de Navidad del
  Concello: pin con icono por tipo, verde si está abierto ahora, agrupados si se solapan.
- **Ficha de cada punto:** foto entera (en grande al tocarla), «Abierto · Cierra 00:30» o
  «Cerrado · Abre 18:00» calculado con el programa oficial 2026-27, horario, dirección con
  mini-mapa, parking más cercano con plazas libres en vivo y próximos buses programados.
- **Tour a pie:** «¿Cuánto tiempo tienes?» (30–120 min) y «¿Cuándo vas?» (ahora, 18:00, 20:00,
  22:00); elige lo que cabe y está abierto, lo enruta por calles reales y lo dibuja sobre el
  mapa; «Empezar el paseo» lo cuenta parada a parada. Lo lejano queda «para otro día».
- **Navidad hoy:** línea de tiempo con horas reales (encendido de luces, pases del Árbol,
  salidas), lo abierto ahora y lo navideño de la agenda del Concello, situado en el mapa.
- **Vista ciudad:** todo Vigo en OpenStreetMap con la foto de cada punto, los 12 parkings en
  vivo, estaciones y paradas (estas solo a nivel de calle) y la ruta desde casa.
- **Búsqueda** de puntos, eventos, estaciones y 1921 calles, sin tildes y con erratas.
- **Ajustes** en un solo botón: idioma (gl/es/en, por el navegador), vista, tema y créditos.
- **Compartir:** el enlace guarda el punto (`#p=...`) o el tour (`#tour=60-20`).

<p><img src="docs/img/web-ficha-movil-390.jpg" width="260" alt="Ficha en el móvil"> <img src="docs/img/web-hoy-1400.jpg" width="520" alt="Navidad hoy"></p>

El servidor de `make website` es `scripts/serve_web.mjs` (Node, sin dependencias): el
`http.server` de Python en Windows deja respuestas a medias con varias conexiones y la
primera carga podía quedar en blanco. `scripts/serve_web.py` lo usa si hay Node.
=======
## Línea de comandos

El paquete `app` expone un CLI con `python -m app`. El subcomando principal es
`points`, que lee los puntos navideños de ``data/points.json`` y muestra un
resumen:

```bash
uv run python -m app points                          # texto en español
uv run python -m app points --lang gl                # en galego
uv run python -m app points --by-type                # conteo por tipo
uv run python -m app points --format json            # salida JSON
```

Ejemplo de salida:

```
Puntos navidenos de Vigo (35):
  concello-2552: Arbol gigante de Nadal (light)
  concello-2553: Muneco de Nieve (light)
  ...
```
>>>>>>> 0e3b18c (feat(CORE-001): Primer vertical slice: CLI points carga data/points.json)

## Arquitectura

```
  fuentes de datos (Concello, IGN, OSM, GTFS, Open-Meteo, ...)
            │
            ▼
  scripts/*  (snapshots versionados en data/raw/ + data/*.json)
            │
            ▼
  pipeline de render (isométrico, offline, una sola vez)
            │
            ▼
  web/tiles/*  +  web/js/*  (sitio estático)
            │
            ▼
  scripts/serve_web.py  →  navegador (mobile-first)
```

Dos tuberías conviven:

- **Datos → snapshots → web.** Cada fuente se descarga a `data/raw/` con su
  `fetched_at` y se normaliza a JSON en `data/`. La web consume esos JSON;
  nada se pide en vivo al usuario salvo el clima actual.
- **Render → tiles.** El mapa base se dibuja una sola vez (modelo de imagen) y
  se publica como pirámide de teselas en `web/tiles/`. Sol, sombras, noche y
  clima se aplican por código sobre esas teselas, no se redibujan.

Diagrama del pipeline de render (Mermaid):

```mermaid
flowchart LR
  A[Ortofoto PNOA] --> B[Tiles base isométrico]
  C[Edificios 3D Concello] --> B
  B --> D[Pirámide de teselas web/tiles]
  E[Capa navideña Concello] --> F[Activos separados]
  G[GTFS Vitrasa/Renfe] --> F
  H[Open-Meteo] --> I[Clima y hora]
  F --> J[Web mobile-first]
  I --> J
  D --> J
```

## Fuentes de datos

Tabla resumida; la auditoría completa (licencias, atribución y estado) está en
[`vault/01_PROYECTO/licencias.md`](vault/01_PROYECTO/licencias.md).

| Fuente | Licencia | Atribución |
|---|---|---|
| Concello — parkings, agenda, avisos, GTFS Vitrasa | ODC-BY 1.0 | Concello de Vigo — datos.vigo.org (ODC-BY) |
| Concello — capa navideña (ArcGIS) | No declarada (público) | Concello de Vigo — Puntos de interés de Navidad 2026-27 |
| Concello — Edificios 3D | No declarada | Concello de Vigo — Edificios 3D |
| Renfe GTFS AV/LD/MD | CC BY 4.0 | Renfe Operadora (CC BY 4.0) |
| Open-Meteo (forecast + marine) | CC BY 4.0 (API no comercial) | Weather data by Open-Meteo.com |
| IGN — PNOA ortofoto y LiDAR | CC BY 4.0 | PNOA cedido por © Instituto Geográfico Nacional |
| IGN/CNIG — MDT05 | CC BY 4.0 | MDT05 © Instituto Geográfico Nacional |
| OpenStreetMap | ODbL 1.0 | © OpenStreetMap contributors |
| Catastro (fallback de huellas) | Reutilización libre con atribución | Dirección General del Catastro |

Reglas duras: todo vehículo en movimiento se etiqueta «según horario», nunca
«en directo», mientras no haya un feed en vivo comprobado. Las fotos de la capa
navideña se enlazan con crédito; las propias (R-03) tienen prioridad.

## Cómo se trabaja aquí

Este repositorio usa un **arnés de desarrollo** que rige cómo trabaja un agente
de IA sobre él: puerta de entrada, backlog con criterios de aceptación, memoria
fuera de la ventana de contexto y puerta de permisos para las acciones que no
se deshacen. La fuente de verdad del backlog es **GEAS** (MongoDB); el fichero
local `harness/featureslist.json` es un espejo de solo lectura.

Reglas que se aplican a todo el mundo (humanos y agentes):

1. **Un actor por dispositivo.** Cada persona/máquina tiene su propio actor en
   GEAS (rol `agent`). No se comparte token entre cuentas.
2. **Claim antes de tocar.** Antes de modificar código se reclama el ticket con
   `harness start <ID>`: hace commit WIP, fetch, pull --rebase, push y
   `start_ticket` de forma atómica. Sin remoto configurado no hay claim.
3. **Una feature a la vez.** `harness next` dice qué toca; no se empieza otra
   sin cerrar la anterior.
4. **Evidencia, no afirmaciones.** Ninguna feature se marca `done` sin que
   `./init.sh` pase en verde y con la salida real del comando que prueba cada
   criterio.
5. **No se commitean marcadores de conflicto** (`<<<<<<<` / `>>>>>>>`): un
   `featureslist.json` con marcadores es JSON inválido y tumba la CI de todo el
   equipo.

Comandos habituales del arnés:

```bash
./init.sh                              # puerta de entrada
uv run python -m agents run harness next    # ¿qué toca?
uv run python -m agents run harness start --id DOC-01
uv run python -m agents run harness finish --id DOC-01 --evidence "..."
uv run python -m agents run git commit_feature --id DOC-01 --title "..." --dry-run true
```

El protocolo completo está en [`AGENTS.md`](AGENTS.md).

## Estado y roadmap

El estado vivo del trabajo está en [`harness/progress/current.md`](harness/progress/current.md)
y el histórico en [`harness/progress/history.md`](harness/progress/history.md). El
backlog con criterios de aceptación está en GEAS y se espeja en
[`harness/featureslist.json`](harness/featureslist.json).

Criterio de «hecho» del v1 (resumen; texto completo en
[`vault/01_PROYECTO/objetivo.md`](vault/01_PROYECTO/objetivo.md)):

- Mapa de la zona (4x4 o 5x5 teselas) dibujado y aceptado, 0 pendientes.
- 43 puntos de la capa navideña del Concello como activos separados con horario.
- Primer vistazo reconocible en < 3 s en móvil gama media con 4G.
- Planificador devuelve 3 opciones en < 2 s para hasta 12 paradas.
- Autobuses (Vitrasa) y trenes (Renfe) visibles y etiquetados «según horario».
- Clima de Open-Meteo y control de hora.
- Postal pixel art a partir de una foto propia.

Fuera de alcance del v1: área metropolitana, GPS real de buses, afluencia,
venta de entradas, cuentas, juegos, LoRA propia.

## Marca

<img src="web/favicon.svg" width="48" height="48" alt="El árbol de TinyVigo, que girado 180° es la V de Vigo">

El árbol que se gira: dos capas y una luz en la punta. Del derecho es el árbol
de Porta do Sol; girado 180°, la falda es la V de Vigo. Guía completa (concepto,
variantes, paleta, tipografía y aplicaciones) en
[`web/ui/marca.html`](web/ui/marca.html).

## Licencia

Código bajo la licencia del repositorio (ver [`LICENSE`](LICENSE)). Los datos
tienen sus propias licencias (ver tabla de fuentes y `licencias.md`).
