# Tarea actual

**Feature:** PLANNER-01
**Estado:** in_progress
**Iniciada:** 2026-11-14
**Responsable:** implementer

## Objetivo

F5. Input: start (user location, address, or 'I arrive at Vigo-Urzaiz station'), time window, chosen stops, mode. Output: 3 options (fastest, after dark, easy walk) with total time, walking distance, ordered stops and a plain explanation. Events are time windows. Pedestrian graph from OSM. Exact search up to about 12 stops. A stop that cannot be reached in time is named with a drop suggestion. The chosen route is drawn on the map as a line with numbered stops.

Criterios de aceptación:
  1. 3 options returned for the same input; same input gives the same 3 routes
  2. Start accepts location, address and a station
  3. Event pinned at 20:00 -> no option arrives after 20:00
  4. Unreachable stop reported with a drop suggestion, never silently skipped
  5. Answers in under 2 s for 12 stops
  6. Walking times from the OSM pedestrian graph
  7. Chosen route drawn on the map with numbered stops

## Criterios de aceptación

- [ ] 3 options returned for the same input; same input gives the same 3 routes
- [ ] Start accepts location, address and a station
- [ ] Event pinned at 20:00 -> no option arrives after 20:00
- [ ] Unreachable stop reported with a drop suggestion, never silently skipped
- [ ] Answers in under 2 s for 12 stops
- [ ] Walking times from the OSM pedestrian graph
- [ ] Chosen route drawn on the map with numbered stops

## Bitácora

_(pendiente)_

## Bloqueos

_(ninguno)_
