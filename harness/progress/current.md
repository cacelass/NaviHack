# Tarea actual

**Feature:** BOOT-004
**Estado:** in_progress
**Iniciada:** 2026-11-14
**Responsable:** implementer

## Objetivo

El contrato de knowledge dice que puebla vault/05_AGENTES/ con una ficha por agente desde contracts.py, y eso no esta implementado: ninguna accion escribe ese directorio. Las 23 fichas actuales vienen de la plantilla y ya estan desfasadas (falta bootstrap). Esta feature implementa la accion que el contrato ya prometia.

Criterios de aceptación:
  1. run knowledge sync_agent_cards genera una ficha por agente registrado en vault/05_AGENTES/, incluidos los de contrato inline como bootstrap
  2. la ficha trae rol, can, cannot, needs, owns, collaborates y destructive desde all_contracts(), no texto a mano
  3. dry_run por defecto que enseña que ficheros escribiria sin escribir nada
  4. las fichas de la plantilla que ya no corresponden a ningun agente registrado se reportan, no se borran en silencio
  5. hay tests sobre tmp_path que no tocan el vault real del repo
  6. make check pasa y prompts_sync sigue en verde

[importada desde harness/featureslist.json: BOOT-004]

## Criterios de aceptación

- [ ] run knowledge sync_agent_cards genera una ficha por agente registrado en vault/05_AGENTES/, incluidos los de contrato inline como bootstrap
- [ ] la ficha trae rol, can, cannot, needs, owns, collaborates y destructive desde all_contracts(), no texto a mano
- [ ] dry_run por defecto que enseña que ficheros escribiria sin escribir nada
- [ ] las fichas de la plantilla que ya no corresponden a ningun agente registrado se reportan, no se borran en silencio
- [ ] hay tests sobre tmp_path que no tocan el vault real del repo
- [ ] make check pasa y prompts_sync sigue en verde

## Bitácora

_(pendiente)_

## Bloqueos

_(ninguno)_
