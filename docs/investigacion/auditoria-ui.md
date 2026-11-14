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
