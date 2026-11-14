# implementer · MAP-01

- **Fecha:** 2026-11-14
- **Veredicto:** ok

MAP-01 implementado en web/ (visor isométrico). Añadido web/js/minimap.js (lienzo completo + rectángulo de vista, arrastrable), web/js/layers.js (panel de 7 capas: navidad, eventos, buses, trenes, parking, cámaras, rutas; navidad+eventos on por defecto; marcadores sobre el isométrico con tour.project), web/js/satellite.js (ortofoto PNOA del IGN de la misma zona, interruptor en el panel, cierre con X/Escape). app.js precarga niveles min y min+1 en paralelo y mide firstViewMs/lastPanFps. Los datos del primer vistazo van incrustados en index.html via scripts/bake_first_view.py (llamado desde build_web_data.py). layers.js usa WEB-05 (web/data/live) para agenda y parkings: cero APIs del Concello desde el navegador. Verificado con Playwright/Firefox: firstView 89 ms, 54-60 fps en animación, 7 capas con defaults correctos, 7 marcadores de parking, 24 teselas PNOA, sin errores de consola. Node: scripts/test_web_geo.mjs valida project/unproject (centro + 5 puntos).
