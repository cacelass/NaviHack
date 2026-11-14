# Tarea actual

**Feature:** WEB-04
**Estado:** in_progress
**Iniciada:** 2026-11-14
**Responsable:** implementer

## Objetivo

El idioma de la web se elige por el idioma del navegador, no fijo. Hoy el panel lateral dice «Christmas spots» en inglés aunque el visitante esté en español, y quedan textos sueltos sin traducir.

Qué se espera: detectar navigator.languages y elegir el primer idioma que sea gl, es o en, aceptando variantes como gl-ES, es-ES, es-419 o en-GB; si ninguno coincide, inglés. El conmutador GL/ES/EN sigue visible y la elección manual manda por encima de la detección y se recuerda. Todos los textos de la interfaz salen en el idioma activo, sin ninguno sin traducir, empezando por «Christmas spots». Las cadenas viven en un solo sitio: se reutilizan las de I18N-01 en web/data/i18n/{gl,es,en}.json, sin textos nuevos escritos a mano en el HTML o el JS. Frases cortas y llanas en los tres idiomas, del tipo «Encendido ya» o «11 min andando».

Va en web/index.html, web/js/ y web/data/i18n/. Pensado para Miguel.

Criterios de aceptación:
  1. Con el navegador en gallego la web arranca en gallego; con el navegador en español, en español; con el navegador en inglés, en inglés
  2. Con el navegador en francés, o sin ninguno de los tres, la web arranca en inglés
  3. Las variantes gl-ES, es-419, en-GB y es-ES se resuelven a su idioma base
  4. Elegir GL, ES o EN a mano cambia el idioma en el momento y se recuerda en la siguiente visita, por encima de lo que diga el navegador
  5. Ningún texto visible queda sin traducir en los tres idiomas, revisadas las 12 pantallas y el panel lateral: «Christmas spots» ya no aparece en español ni en gallego
  6. Todo el texto sale de web/data/i18n/{gl,es,en}.json: una búsqueda en HTML y JS no encuentra cadenas de interfaz escritas a mano
  7. Las frases son cortas y llanas en los tres idiomas, sin jerga ni frases largas
  8. Capturas de la misma pantalla en gallego, español e inglés en web/ui/capturas/

BUENA UX QUE YA EXISTE Y HAY QUE CONSERVAR (se amplía, no se rehace): la Vista ciudad (todo Vigo en un mapa real con fotos de cada punto y parkings), el tour a pie contado parada a parada dentro de la web ("primero la Bola...") y "¿Cuándo vas?" (ahora, 18:00, 20:00, 22:00), que planifica el paseo según la hora. Son lo mejor de la web actual: cualquier cambio de este ticket tiene que dejarlos igual de claros o mejor. Sigue web/ui/DESIGN.md (UI-03).

## Criterios de aceptación

- [ ] Con el navegador en gallego la web arranca en gallego; con el navegador en español, en español; con el navegador en inglés, en inglés
- [ ] Con el navegador en francés, o sin ninguno de los tres, la web arranca en inglés
- [ ] Las variantes gl-ES, es-419, en-GB y es-ES se resuelven a su idioma base
- [ ] Elegir GL, ES o EN a mano cambia el idioma en el momento y se recuerda en la siguiente visita, por encima de lo que diga el navegador
- [ ] Ningún texto visible queda sin traducir en los tres idiomas, revisadas las 12 pantallas y el panel lateral: «Christmas spots» ya no aparece en español ni en gallego
- [ ] Todo el texto sale de web/data/i18n/{gl,es,en}.json: una búsqueda en HTML y JS no encuentra cadenas de interfaz escritas a mano
- [ ] Las frases son cortas y llanas en los tres idiomas, sin jerga ni frases largas
- [ ] Capturas de la misma pantalla en gallego, español e inglés en web/ui/capturas/

## Bitácora

_(pendiente)_

## Bloqueos

_(ninguno)_
