# Tarea actual

**Feature:** WEB-01
**Estado:** in_progress
**Iniciada:** 2026-11-14
**Responsable:** implementer

## Objetivo

En la web real (web/index.html y web/js/app.js, servida con `python3 -m http.server` desde web/) el bloque 3x3 se ve como un rectángulo pequeño pegado a la izquierda, cortado por la derecha y flotando sobre un fondo azul oscuro vacío. El visor (OpenSeadragon) no se ajusta al bloque: el encuadre inicial y los límites de paneo y zoom no coinciden con el tamaño real del bloque que describe manifest.json, tampoco en las variantes que traen `canvas` y `offset`.

Qué se espera: al abrir, el bloque ocupa la pantalla entera sin franjas de fondo; no se puede arrastrar ni alejar hasta dejar hueco vacío; el zoom mínimo es el encuadre del bloque; al llegar al borde se ve mar continuo y no el azul de fondo; y cuando ZONE-02 publique el bloque ampliado hacia Vialia, el encuadre y los límites se recalculan desde el manifiesto, sin anchos ni altos escritos a mano.

Va en web/css/app.css y web/js/app.js. Pensado para Miguel.

Criterios de aceptación:
  1. En escritorio (1400x900) y en móvil (390x844) el bloque ocupa todo el viewport, sin franjas de fondo vacío a los lados, arriba ni abajo
  2. No se puede arrastrar el mapa hasta dejar hueco vacío en ningún borde; en el zoom mínimo el bloque sigue llenando la pantalla
  3. El zoom mínimo es el encuadre del bloque y no se puede alejar más; el máximo mantiene el pixelado nítido, sin suavizado
  4. Con un manifest.json de otro tamaño (bloque 4x4 sintético o el de ZONE-02) encuadre y límites se recalculan solos, sin tocar JS: no hay ancho ni alto del bloque escrito a mano
  5. Al salir del bloque se ve mar continuo, nunca el azul de fondo de la página
  6. Redimensionar la ventana y girar el móvil reajusta el encuadre sin dejar huecos
  7. Capturas antes y después en web/ui/capturas/

Solapa con MAP-01 (visor de teselas, búsqueda, minimapa y capas), que sigue libre: coordinar con quien lo coja para no hacerlo dos veces.

BUENA UX QUE YA EXISTE Y HAY QUE CONSERVAR (se amplía, no se rehace): la Vista ciudad (todo Vigo en un mapa real con fotos de cada punto y parkings), el tour a pie contado parada a parada dentro de la web ("primero la Bola...") y "¿Cuándo vas?" (ahora, 18:00, 20:00, 22:00), que planifica el paseo según la hora. Son lo mejor de la web actual: cualquier cambio de este ticket tiene que dejarlos igual de claros o mejor. Sigue web/ui/DESIGN.md (UI-03).

## Criterios de aceptación

- [ ] En escritorio (1400x900) y en móvil (390x844) el bloque ocupa todo el viewport, sin franjas de fondo vacío a los lados, arriba ni abajo
- [ ] No se puede arrastrar el mapa hasta dejar hueco vacío en ningún borde; en el zoom mínimo el bloque sigue llenando la pantalla
- [ ] El zoom mínimo es el encuadre del bloque y no se puede alejar más; el máximo mantiene el pixelado nítido, sin suavizado
- [ ] Con un manifest.json de otro tamaño (bloque 4x4 sintético o el de ZONE-02) encuadre y límites se recalculan solos, sin tocar JS: no hay ancho ni alto del bloque escrito a mano
- [ ] Al salir del bloque se ve mar continuo, nunca el azul de fondo de la página
- [ ] Redimensionar la ventana y girar el móvil reajusta el encuadre sin dejar huecos
- [ ] Capturas antes y después en web/ui/capturas/

## Bitácora

_(pendiente)_

## Bloqueos

_(ninguno)_
