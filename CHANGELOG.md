# Changelog

Todos los cambios relevantes del proyecto se documentan aquí.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

El dueño de este fichero es el agente `documentation`: `git commit_feature`
añade aquí una entrada por cada feature cerrada del arnés.

---

## [Unreleased] — 2026-11-14

### Añadido

- Primer vertical slice: CLI points carga data/points.json (CORE-001)

## [Unreleased] — 2026-11-14

### Añadido

- Cerrar BOOT-003 (arranque en frio verificado) (BOOT-003)

## [Unreleased] — 2026-11-14

### Añadido

- Verificar ubicacion de los 6 landmarks de Navidad (R-02)

## [Unreleased] — 2026-11-14

### Añadido

- Estado del arte y huecos de capacidad (TinyVigo) (ONBOARD-002)

## [Unreleased] — 2026-11-14

### Añadido

- Installer scaffold: creador de agentes autocontenidos (BOOT-002)

## [Unreleased] — 2026-11-14

### Añadido

- Definir la arquitectura del proyecto (TinyVigo) (DESIGN-001)

## [Unreleased] — 2026-11-14

### Añadido

- Arreglar import de app.__main__ (FIX-001)

## [Unreleased] — 2026-11-14

### Añadido

- Sincronizar fichas de agentes en el vault (BOOT-004)

## [Unreleased] — 2026-11-14

### Añadido

- Entender el proyecto (TinyVigo) (ONBOARD-001)

## [Unreleased] — 2026-11-14

### Añadido

- Arranque en frio operativo (BOOT-001)

## [Unreleased] — 2026-11-14

### Añadido

- Batería de calidad en verde (QA-001)

## [Unreleased] — 2026-11-14

### Añadido

- Definir el objetivo del proyecto (TinyVigo) (SCOPE-001)

## [Unreleased] — 2026-11-14

### Añadido

- Conectar el arnés a GEAS sobre MongoDB Atlas (GEAS-001)

## [Unreleased] — 2026-08-04

### Añadido

- protege app.__main__ para que importar el paquete no ejecute la CLI (FIX-001)

## [0.1.0] — 2026-08-04

### Añadido

- Arnés de trabajo: `AGENTS.md`, `init.sh`, `harness/` (backlog + progreso) y
  los cuatro subagentes (`lider`, `explorer`, `implementer`, `reviewer`).
- Sistema de 23 agentes Python en `agents/`, con contratos de rol y puerta de
  permisos (`agents/permissions.py`) para las acciones irreversibles.
- `agents/policy_guard.py` como política para las herramientas del asistente,
  sin cablear a ningún hook: se activa a mano (ver `AGENTS.md`).
- Vault de conocimiento en `vault/`, RAG local opcional y grafo con graphify.
- Paquete de ejemplo `app/` con su CLI y tests, `make check` en verde y CI.
