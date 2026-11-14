# Tarea actual

**Feature:** GO-01
**Estado:** in_progress
**Iniciada:** 2026-11-14
**Responsable:** implementer

## Objetivo

Pedido por Miguel (2026-11-14). Si el usuario está a más de ~5 min a pie del primer punto del tour, la app pregunta cómo quiere ir: andando, en bus o en coche. A pie: ruta normal. Coche: de su ubicación a un parking cercano al primer punto que esté libre o que previsiblemente lo esté al llegar (D-05), y del parking a pie al primer punto. Bus: parada cercana con bus directo hasta cerca del primer punto (GTFS programado, X-04) y ruta a pie desde la parada de bajada. Cada tramo con su tiempo, todo dibujado en el mapa integrado y botón para abrir exactamente esa ruta en Google Maps. Aspecto profesional, sin bugs.

Criterios de aceptación:
  1. A más de 5 min a pie del primer punto se pregunta cómo ir: a pie, bus o coche
  2. A pie: ruta y tiempo hasta el primer punto
  3. Coche: ruta hasta un parking cercano al primer punto con plazas libres (o previsión al llegar) y tramo a pie parking-primer punto, cada uno con su tiempo
  4. Bus: parada de subida cercana con bus directo, hora programada, parada de bajada y tramo a pie hasta el primer punto, cada uno con su tiempo
  5. Todos los tramos dibujados en el mapa integrado con estilo distinto por modo
  6. Botón que abre en Google Maps exactamente esa ruta
  7. Sin errores en consola y con alternativa si falla la geolocalización, el router o un feed

## Criterios de aceptación

- [ ] A más de 5 min a pie del primer punto se pregunta cómo ir: a pie, bus o coche
- [ ] A pie: ruta y tiempo hasta el primer punto
- [ ] Coche: ruta hasta un parking cercano al primer punto con plazas libres (o previsión al llegar) y tramo a pie parking-primer punto, cada uno con su tiempo
- [ ] Bus: parada de subida cercana con bus directo, hora programada, parada de bajada y tramo a pie hasta el primer punto, cada uno con su tiempo
- [ ] Todos los tramos dibujados en el mapa integrado con estilo distinto por modo
- [ ] Botón que abre en Google Maps exactamente esa ruta
- [ ] Sin errores en consola y con alternativa si falla la geolocalización, el router o un feed

## Bitácora

_(pendiente)_

## Bloqueos

_(ninguno)_
