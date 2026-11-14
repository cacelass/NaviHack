# Tarea actual

**Feature:** GEAS-001
**Estado:** in_progress
**Iniciada:** 2026-11-14
**Responsable:** implementer

## Objetivo

Dejar el arnés de NavaHack respaldado por GEAS con MongoDB. Ya está todo preparado: harness/geas.json, scripts/geas_setup.py, scripts/geas_setup.sh y el modo GEAS de agents/agents/harness_agent.py. Lo único que falta es sustituir <IP> por la IP/URL real del servidor, poner GEAS_TOKEN en .env y ejecutar el setup. A partir de ahí el backlog vive en tickets: nadie edita featureslist.json a mano y harness start hace commit WIP + pull --rebase + push antes de reclamar.

Criterios de aceptación:
  1. harness/geas.json tiene la IP/URL real (sin <IP>), org_id y repository_id de NavaHack
  2. El token está en .env como GEAS_TOKEN y no aparece en harness/geas.json ni en git
  3. ./scripts/geas_setup.sh <IP> importa el backlog a GEAS y escribe harness/geas_map.json
  4. run harness status devuelve backend=geas y el conteo real de tickets
  5. run harness next devuelve un ticket de GEAS, no del espejo local
  6. run harness start <ID> hace commit WIP, pull --rebase y push antes de start_ticket
  7. ./init.sh termina con ENTORNO LISTO

[importada desde harness/featureslist.json: GEAS-001]

## Criterios de aceptación

- [ ] harness/geas.json tiene la IP/URL real (sin <IP>), org_id y repository_id de NavaHack
- [ ] El token está en .env como GEAS_TOKEN y no aparece en harness/geas.json ni en git
- [ ] ./scripts/geas_setup.sh <IP> importa el backlog a GEAS y escribe harness/geas_map.json
- [ ] run harness status devuelve backend=geas y el conteo real de tickets
- [ ] run harness next devuelve un ticket de GEAS, no del espejo local
- [ ] run harness start <ID> hace commit WIP, pull --rebase y push antes de start_ticket
- [ ] ./init.sh termina con ENTORNO LISTO

## Bitácora

_(pendiente)_

## Bloqueos

_(ninguno)_
