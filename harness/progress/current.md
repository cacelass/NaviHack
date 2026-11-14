# Tarea actual

**Feature:** FIX-001
**Estado:** in_progress
**Iniciada:** 2026-11-14
**Responsable:** implementer

## Objetivo

app/__main__.py ejecuta sys.exit(main()) sin guarda if __name__ == '__main__'. Importar el paquete app (o barrerlo con pkgutil.walk_packages) ejecuta la CLI y mata el proceso con SystemExit(2). agents/__main__.py tiene la guarda; app/__main__.py no.

Criterios de aceptación:
  1. uv run python -c "import app.__main__" termina con exit 0 sin imprimir el usage de la CLI
  2. un test en tests/ importa app.__main__ y barre los modulos de app con pkgutil.walk_packages sin que el proceso muera
  3. uv run python -m app hello sigue imprimiendo Hola, mundo. y devuelve 0
  4. make check pasa y ./init.sh termina con ENTORNO LISTO

[importada desde harness/featureslist.json: FIX-001]

## Criterios de aceptación

- [ ] uv run python -c "import app.__main__" termina con exit 0 sin imprimir el usage de la CLI
- [ ] un test en tests/ importa app.__main__ y barre los modulos de app con pkgutil.walk_packages sin que el proceso muera
- [ ] uv run python -m app hello sigue imprimiendo Hola, mundo. y devuelve 0
- [ ] make check pasa y ./init.sh termina con ENTORNO LISTO

## Bitácora

_(pendiente)_

## Bloqueos

_(ninguno)_
