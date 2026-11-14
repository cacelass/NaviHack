# Tarea actual

**Feature:** ONBOARD-001
**Estado:** in_progress
**Iniciada:** 2026-11-14
**Responsable:** implementer

## Objetivo

Nadie puede implementar contra un objetivo que no está escrito. Esta feature convierte lo que el usuario tiene en la cabeza en algo que un agente pueda leer: qué problema se resuelve, para quién, cuándo está hecho y qué queda fuera. El agente `bootstrap` hace las preguntas; el usuario las responde; la respuesta acaba en project.yml y en el vault.

Criterios de aceptación:
  1. uv run python -m agents run bootstrap describe --description "<respuesta del usuario>" --yes devuelve success=true
  2. project.yml tiene una descripción propia del proyecto, no la de la plantilla
  3. vault/01_PROYECTO/objetivo.md recoge problema, usuario, criterio de hecho y fuera de alcance
  4. El README describe el objetivo en una frase propia
  5. ./init.sh termina con ENTORNO LISTO

[importada desde harness/featureslist.json: ONBOARD-001]

## Criterios de aceptación

- [ ] uv run python -m agents run bootstrap describe --description "<respuesta del usuario>" --yes devuelve success=true
- [ ] project.yml tiene una descripción propia del proyecto, no la de la plantilla
- [ ] vault/01_PROYECTO/objetivo.md recoge problema, usuario, criterio de hecho y fuera de alcance
- [ ] El README describe el objetivo en una frase propia
- [ ] ./init.sh termina con ENTORNO LISTO

## Bitácora

_(pendiente)_

## Bloqueos

_(ninguno)_
