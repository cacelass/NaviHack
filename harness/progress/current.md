# Tarea actual

**Feature:** ONBOARD-002
**Estado:** in_progress
**Iniciada:** 2026-11-14
**Responsable:** implementer

## Objetivo

Con el objetivo escrito, dos preguntas antes de construir nada: qué ha publicado ya alguien sobre este problema (papers y fuentes que aporten al repo, indexadas para poder consultarlas después) y qué trabajo de este proyecto no cubre ningún agente actual. Lo segundo se resuelve creando los agentes que falten con `installer scaffold`, no improvisando scripts sueltos.

Criterios de aceptación:
  1. uv run python -m agents run research find_papers devuelve success=true con al menos 3 referencias relevantes
  2. Las URLs útiles quedan indexadas (run rag index_urls --urls ...) y run rag search las encuentra
  3. vault/01_PROYECTO/estado-del-arte.md resume cada fuente en 2-3 líneas: qué se toma y qué se descarta
  4. uv run python -m agents run bootstrap suggest_agents devuelve la lista de huecos de capacidad
  5. Cada hueco aceptado tiene su agente creado con installer scaffold, con contrato, prompt y test
  6. uv run python -m agents.prompts_sync sale en verde (todo agente registrado tiene prompt y contrato)
  7. ./init.sh termina con ENTORNO LISTO

[importada desde harness/featureslist.json: ONBOARD-002]

## Criterios de aceptación

- [ ] uv run python -m agents run research find_papers devuelve success=true con al menos 3 referencias relevantes
- [ ] Las URLs útiles quedan indexadas (run rag index_urls --urls ...) y run rag search las encuentra
- [ ] vault/01_PROYECTO/estado-del-arte.md resume cada fuente en 2-3 líneas: qué se toma y qué se descarta
- [ ] uv run python -m agents run bootstrap suggest_agents devuelve la lista de huecos de capacidad
- [ ] Cada hueco aceptado tiene su agente creado con installer scaffold, con contrato, prompt y test
- [ ] uv run python -m agents.prompts_sync sale en verde (todo agente registrado tiene prompt y contrato)
- [ ] ./init.sh termina con ENTORNO LISTO

## Bitácora

_(pendiente)_

## Bloqueos

_(ninguno)_
