# Tarea actual

**Feature:** QA-001
**Estado:** in_progress
**Iniciada:** 2026-11-14
**Responsable:** implementer

## Objetivo

Dejar make check (lint + typecheck + test + arnés) pasando de punta a punta, y el CI ejecutando lo mismo que se ejecuta en local. Es la condición que ./init.sh verifica antes de dejar trabajar a cualquier agente.

Criterios de aceptación:
  1. make lint pasa sin errores
  2. make typecheck pasa sin errores
  3. make test pasa y la salida real queda como evidencia
  4. El workflow de CI ejecuta los mismos comandos que make check
  5. ./init.sh termina con ENTORNO LISTO

[importada desde harness/featureslist.json: QA-001]

## Criterios de aceptación

- [ ] make lint pasa sin errores
- [ ] make typecheck pasa sin errores
- [ ] make test pasa y la salida real queda como evidencia
- [ ] El workflow de CI ejecuta los mismos comandos que make check
- [ ] ./init.sh termina con ENTORNO LISTO

## Bitácora

_(pendiente)_

## Bloqueos

_(ninguno)_
