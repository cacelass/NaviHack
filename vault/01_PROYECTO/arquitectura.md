# Arquitectura — TinyVigo

> Rellenado por `DESIGN-001`. Fuente: spec TinyVigo v3 (Part A7, Part B).

## Piezas del sistema

1. **Frontend estático** (mapa, escenas, UI): servido desde CDN o el VPS existente. Mapa satélite PNOA, puntos como sprites pixel-art, capa de luces animada, posición del usuario.
2. **Servidor pequeño** (Python): planificación de rutas y generación de postales. Guarda las credenciales de los modelos; nada llega al navegador.
3. **Snapshot publisher**: job programado (cron/systemd timer) en el mismo servidor que descarga los feeds de la ciudad, los valida y publica snapshots JSON estáticos que la app lee.
4. **Escenas offline**: generadas una vez por punto, guardadas como imágenes en el repo junto al prompt y la foto fuente.
5. **Dataset `points.json`**: fuente de verdad de los puntos navideños, construido por investigación (R-01..R-05).

## Flujo

```
Usuario (móvil) → Frontend estático (CDN)
   ├── lee snapshots JSON (nuestro dominio) ← Snapshot publisher ← feeds ciudad
   ├── mapa satélite (PNOA) + sprites
   └── para rutas/postal → Servidor Python → modelos de imagen (credenciales server-side)
```

El navegador nunca llama a un feed de la ciudad ni a un modelo. Todo pasa por nuestro dominio o por el servidor.

## Alternativas consideradas y descartadas

- **El navegador llama al feed de la ciudad directamente**: rechazado. Los endpoints del Concello pueden no permitir CORS, las fuentes HTTP no se pueden llamar desde HTTPS, y cada visitante golpearía el servidor del Concello.
- **Proxy que descarga en cada petición del usuario**: rechazado. Añade latencia, multiplica peticiones al Concello en noches de mucho tráfico y no genera historial.
- **Conexión en vivo (websocket/streaming)**: rechazado. Los feeds son ficheros polled; no hay nada que streamear y la complejidad no compensa.
- **Repintar toda la ciudad como pixel art**: rechazado. Un render aéreo repintado da una ilustración plana con contornos finos y paleta lavada, y necesita un apaño en cada costura de tile. Las escenas cercanas funcionan mucho mejor.

## Riesgos conocidos

- El Concello publica el programa 2026-27 a trozos y algunos cambios solo aparecen en prensa: ubicaciones y horarios pueden cambiar tras el lanzamiento (mitigación: R-05, fecha de verificación visible, etiqueta de estado).
- Fuentes contradictorias sobre dónde está una atracción (mitigación: reglas de conflicto en F2 y comprobación in situ).
- Los metadatos del Concello dicen "diario" para feeds que parecen de 3–5 minutos; la frescura real se desconoce hasta D-00.
- El join de sedes para la agenda puede dejar muchos eventos fuera del mapa si es débil.
- Rate limiting de los sitios del Concello (observado en mapas.vigo.org): el publisher descarga con cortesía, una petición a la vez, con back-off.
- El layer de Navidad del Concello puede no localizarse nunca: es solo una línea base, no bloquea v1.
- Los wrappers no oficiales de Vitrasa pueden romperse o bloquearse: solo Part B, nunca dependencia.
- La estimación de afluencia puede ser errónea y las cifras de visitantes son sensibles: solo Part B, etiquetada como estimación.
- Los tiers gratuitos (TomTom, claves AEMET) pueden agotarse en una noche de mucho tráfico: solo Part B, cacheado.

## Decisiones diferidas (Part B y posteriores)

- Transporte público (autobuses Vitrasa, trenes Renfe): v2. Incluye patas de tránsito en el planner, próximas salidas y capas de paradas/estaciones.
- Huella de edificios y alturas (capa 3D del Concello): v1.1.
- Estimación de afluencia ("busy-now"): v2, siempre etiquetada como estimación.
- Backups de tiempo (AEMET, MeteoGalicia) y mareas: v1.1.
- Tiles de tráfico TomTom: v2, opcional.
- Movilidad histórica MITMA: v2.
- Tráfico y cámaras: v1.1.
- Alertas (DGT DATEX II, avisos del Concello): v1.1.
- Autenticación y pago del modelo de imagen para postales: decisión pendiente antes de publicar postales.
- Ángulo de vista (mapa satélite vs isométrico): pregunta abierta A11.
- Público objetivo primario (turistas vs vigueses): pregunta abierta A11.
- Nombre y dominio (`tinyvigo` es nombre de trabajo): pregunta abierta A11.
- Fecha de fin de temporada (cierre de luces): pregunta abierta A11.
- Fotos de las atracciones (propias vs con permiso): pregunta abierta A11.

## Stack

- Lenguaje: Python 3.12+ (el .venv de referencia es 3.13)
- Entorno y dependencias: uv (uv.lock)
- Calidad: ruff, mypy, pytest, bandit, pip-audit
- Conocimiento: vault Obsidian + graphify + RAG local opcional (chromadb)
- Frontend: estático, mapa satélite PNOA, escenas pixel-art generadas offline
- Servidor: Python (rutas + postales), credenciales server-side
- Datos: snapshots JSON publicados por job programado

## Estructura del repositorio

```
tinyvigo/              — Código del proyecto (TinyVigo)
tests/                 — Tests del proyecto
agents/                — Sistema multi-agente del arnés (stdlib pura)
harness/               — El arnés: backlog, progreso, memoria
vault/                 — Conocimiento estable (Obsidian)
docs/                  — Sphinx
```
EOF
echo written