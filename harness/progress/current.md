# Tarea actual

**Feature:** BOOT-001
**Estado:** in_progress
**Iniciada:** 2026-11-14
**Responsable:** implementer

## Objetivo

Completar el codigo ya escrito y nunca ejecutado: el soporte de contratos inline en agents/contracts.py y el agente bootstrap. Incluye arreglar la colision de nombre entre la accion 'describe' del agente y BaseAgent.describe(), que hoy rompe 'python -m agents list'.

Criterios de aceptación:
  1. python -m agents list lista los 24 agentes sin excepcion, bootstrap incluido
  2. python -m agents describe bootstrap devuelve el contrato inline
  3. existe agents/prompts/bootstrap_agent.md con prosa a mano y bloque AUTOGEN
  4. uv run python -m agents.prompts_sync sale en verde
  5. hay tests de contratos inline (inline_contracts, all_contracts, contract_for, validate_contracts) y de las cuatro acciones de bootstrap
  6. make check pasa

[importada desde harness/featureslist.json: BOOT-001]

## Criterios de aceptación

- [ ] python -m agents list lista los 24 agentes sin excepcion, bootstrap incluido
- [ ] python -m agents describe bootstrap devuelve el contrato inline
- [ ] existe agents/prompts/bootstrap_agent.md con prosa a mano y bloque AUTOGEN
- [ ] uv run python -m agents.prompts_sync sale en verde
- [ ] hay tests de contratos inline (inline_contracts, all_contracts, contract_for, validate_contracts) y de las cuatro acciones de bootstrap
- [ ] make check pasa

## Bitácora

_(pendiente)_

## Bloqueos

_(ninguno)_
