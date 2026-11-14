# Auditoría de interfaz — web real

Alcance: `web/index.html`, `web/js/` (app, points, tour, about) y `web/css/` (app,
points, about), contra `web/ui/DESIGN.md` (UI-03). Fecha: 14 nov 2026.

## Corregidas (estilo puro)

| Desviación del checklist | Antes | Ahora |
|---|---|---|
| Controles sobre el mapa translúcidos (punto 5) | zoom y «acerca» con `rgba(11,16,32,.6)`; panel, hoja y tour con `backdrop-filter: blur` + `rgba(21,27,42,.92)` | fondo sólido `#151b2a`, sin `backdrop-filter` |
| Fuentes fuera de Inter (punto 2) | zoom, «acerca» y su cierre en `system-ui` | `Inter, system-ui, sans-serif` |
| Objetivo táctil < 44 px (punto 8) | botones de zoom 40×40 | 44×44 |

Verificado con `getComputedStyle` sobre la página servida: zoom `44px`/`rgb(21,27,42)`/`Inter`/`backdropFilter: none`; «acerca» `rgb(21,27,42)`/`Inter`; panel y hoja `rgb(21,27,42)`/`backdropFilter: none`.

## Pendientes (estructural, van a ticket)

1. **Color por tipo de punto (punto 4).** La lista y los marcadores usan cinco
   colores (dorado, `#e7836a`, `#8fcf7a`, `#d9534f`, `#9cc4ff`). La guía deja el
   color para estado o para el acento dorado. Es una decisión de producto (cómo
   distinguir tipos sin color), no de estilo puro: va a ticket.
2. **Iconos de interfaz (punto 6).** La lista usa cuadrados de color (`.tv-dot`) en
   vez de iconos Lucide de línea. Requiere elegir un icono por tipo: ticket.
3. **Tarjeta adaptativa (punto 7).** La ficha pone la foto arriba a todo el ancho
   también en escritorio. Debe recolocarse según el ancho (imagen a la izquierda con
   sitio): ticket.
4. **Tema.** La web está en tono oscuro de noche (el mapa es de noche). Los paneles
   oscuros sobre el mapa son correctos por contexto; el «fondo blanco y gris» aplica
   a las páginas de contenido (inicio, ajustes), no al visor nocturno. Sin cambio.

## Nota

Las correcciones son de estilo puro y no tocan la lógica (puntos, tour, horario).
El resto se deja como ticket para no cambiar el producto sin revisión.

## Segundo pase (Miguel2, UI-04)

Los tres pendientes estructurales se cierran sin cambiar el producto, y el primer pase
se mantiene (sin blur, sólido, Inter, 44 px) ahora sobre los tokens de `web/ui/css/tokens.css`:

| Pendiente | Ahora |
|---|---|
| 1. Color por tipo | Fuera los cinco colores. Marcadores en el dorado de las luces; el estado abierto aclara el marcador y va en verde (`--ok`) en lista, ficha y pines. |
| 2. Iconos de interfaz | Lucide de línea (`web/ui/assets/lucide.js`): tipo en chips (`star`, `ferris-wheel`, `store`, `gift`, `camera`), cerrar `x`, zoom `plus`/`minus`, info, tema, `footprints`, `camera`, `route`. En la lista, la miniatura es la **foto real** del punto. |
| 3. Tarjeta adaptativa | El paso del paseo es una tarjeta con la imagen a la izquierda con sitio y arriba en estrecho (`@container`, un solo componente). |
| 4. Tema | Se respeta: el visor arranca en **oscuro**. Conmutador claro/oscuro de `theme.js` (recuerda la elección); `#light` para capturas. |

Además: tamaños solo 28/20/16/14/12 y pesos 400/500/600 (fuera los 13 px y 22 px),
superficies `--raised` con filo de 1 px y cero sombras, controles de Leaflet en
«Vista ciudad» con la misma superficie sólida y 44 px.

