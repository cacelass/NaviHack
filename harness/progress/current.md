# Tarea actual

**Feature:** WEB-05
**Estado:** in_progress
**Iniciada:** 2026-11-14
**Responsable:** implementer

## Objetivo

Las pantallas de web/ui/ (ficha, eventos, transporte, rutas, lista de puntos) se apoyan todavía en datos de ejemplo o en copias sueltas, y la web del mapa se carga los suyos por su lado en web/js/points.js. Los datos reales ya existen: los 35 puntos de data/points.json, la agenda de D-03, los parkings de D-05 y los horarios de Vitrasa y Renfe de X-01 y X-02.

Qué se espera: una sola fuente por dato y que las pantallas nuevas se alimenten de esos ficheros publicados, sin arrays inventados dentro del HTML. Cuando un dato no existe (sin horario, sin precio) la pantalla lo dice, del tipo «Hora por confirmar», en vez de rellenarlo con un ejemplo.

Va entre web/ui/, web/data/ y los scripts que generan los datos de la web (empezando por scripts/build_web_data.py). Pensado para quien quiera enlazar datos con diseño.

Criterios de aceptación:
  1. Ficha, lista de puntos, eventos, transporte y rutas leen de los ficheros publicados (points.json, agenda, parkings, GTFS) y no de arrays de ejemplo dentro del HTML o el JS
  2. Los 35 puntos aparecen en la lista y en la ficha con nombre, tipo, horario y estado reales; ninguno inventado
  3. Los eventos salen de la agenda de D-03 con fecha, hora y lugar, y los que no tienen hora dicen «Hora por confirmar»
  4. Transporte muestra próximas salidas y líneas de Vitrasa y Renfe desde X-01 y X-02, con la fecha de los datos a la vista
  5. Parkings muestra los de D-05 con plazas o estado si el dato existe; si no, se oculta el campo en lugar de inventarlo
  6. Los puntos y eventos que se pueden añadir a una ruta salen del mismo dataset, sin listas paralelas
  7. Un script regenera todo web/data/ y la web funciona solo con esos ficheros, sin pedir nada a APIs de terceros desde el navegador
  8. Si un fichero falta o viene vacío, la pantalla muestra un error claro y no una tabla vacía sin explicación

BUENA UX QUE YA EXISTE Y HAY QUE CONSERVAR (se amplía, no se rehace): la Vista ciudad (todo Vigo en un mapa real con fotos de cada punto y parkings), el tour a pie contado parada a parada dentro de la web ("primero la Bola...") y "¿Cuándo vas?" (ahora, 18:00, 20:00, 22:00), que planifica el paseo según la hora. Son lo mejor de la web actual: cualquier cambio de este ticket tiene que dejarlos igual de claros o mejor. Sigue web/ui/DESIGN.md (UI-03).

## Criterios de aceptación

- [ ] Ficha, lista de puntos, eventos, transporte y rutas leen de los ficheros publicados (points.json, agenda, parkings, GTFS) y no de arrays de ejemplo dentro del HTML o el JS
- [ ] Los 35 puntos aparecen en la lista y en la ficha con nombre, tipo, horario y estado reales; ninguno inventado
- [ ] Los eventos salen de la agenda de D-03 con fecha, hora y lugar, y los que no tienen hora dicen «Hora por confirmar»
- [ ] Transporte muestra próximas salidas y líneas de Vitrasa y Renfe desde X-01 y X-02, con la fecha de los datos a la vista
- [ ] Parkings muestra los de D-05 con plazas o estado si el dato existe; si no, se oculta el campo en lugar de inventarlo
- [ ] Los puntos y eventos que se pueden añadir a una ruta salen del mismo dataset, sin listas paralelas
- [ ] Un script regenera todo web/data/ y la web funciona solo con esos ficheros, sin pedir nada a APIs de terceros desde el navegador
- [ ] Si un fichero falta o viene vacío, la pantalla muestra un error claro y no una tabla vacía sin explicación

## Bitácora

_(pendiente)_

## Bloqueos

_(ninguno)_
