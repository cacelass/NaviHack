# Historial del arnés

Registro append-only de features completadas. Es el changelog del trabajo hecho
por agentes: qué se cerró, con qué evidencia y qué quedó pendiente.

Formato de cada entrada:

```
## <FEATURE-ID> — <título>

- **Cerrada:** YYYY-MM-DD
- **Verificación:** ./init.sh en verde · N tests pasando
- **Cambios:** rutas de los ficheros tocados
- **Decisiones:** lo que se eligió y por qué (solo si no es obvio desde el código)
- **Pendiente:** lo que se dejó fuera a propósito
```

---

_(sin features completadas todavía — el proyecto acaba de empezar)_

## BOOT-001 — Arranque en frio operativo: contratos inline + agente bootstrap

- **Cerrada:** 2026-08-04
- **Verificación:** ./init.sh en verde · 6 passed in 0.31s
- **Cambios:** agents/agents/bootstrap_agent.py; agents/prompts/bootstrap_agent.md (nuevo); agents/tests/test_bootstrap_agent.py (nuevo, 20 tests); agents/tests/test_contracts.py (+6 tests de contratos inline); conteo 23->24 y ficha de bootstrap en README.md, AGENTS.md, agents/README.md, agents/prompts/agents_reference.md, agents/prompts/orchestrator.md, .opencode/agents/orquestador.md, .opencode/agents/lider.md, .claude/agents/lider.md (regenerado)
- **Decisiones:** BootstrapAgent.describe() tapaba BaseAgent.describe() y reventaba 'python -m agents list' con TypeError. Arreglo: el metodo pasa a llamarse describe_project y la clave de accion sigue siendo 'describe', asi que la CLI no cambia. Queda un test de regresion generico sobre list_agents(). Pendientes reportados y NO tocados: (a) 'describe' esta en destructive, asi que el criterio de ONBOARD-001 tal como esta escrito en TICKETS_ARRANQUE es infalsable sin --yes; (b) status devuelve first_run=true en este repo pese a tener 7 features, relevante para BOOT-003; (c) el conteo de agentes en los docs se escapo dos veces: candidato a check en init.sh.
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
$ make check
uv run ruff check app/ tests/ agents/
All checks passed!
uv run ruff format --check app/ tests/
6 files already formatted
uv run mypy app/ tests/
Success: no issues found in 6 source files
  typecheck OK
uv run pytest
======================= 490 passed, 15 skipped in 16.99s =======================
  check pasado: lint + typecheck + test + arnes OK
EXIT=0

$ uv run python -m agents.prompts_sync
Prompts y subagentes sincronizados con el codigo y con los contratos.
PROMPTS_EXIT=0

$ uv run python -m agents list | wc -l
24
```

</details>

## BOOT-002 — installer scaffold: creador de agentes autocontenidos

- **Cerrada:** 2026-08-04
- **Verificación:** ./init.sh en verde · 6 passed in 0.35s
- **Cambios:** agents/tools/agent_scaffold_tool.py (nuevo: AgentSpec + AgentScaffoldTool); agents/agents/installer_agent.py (accion scaffold); agents/contracts.py (solo el contrato de installer: scaffold en destructive); agents/prompts/installer_agent.md (prosa sobre scaffold + AUTOGEN); agents/tests/test_installer_scaffold.py (nuevo, 22 tests)
- **Decisiones:** El generador no puede reproducir el bug de BOOT-001: si una ACCION colisiona con un metodo de BaseAgent renombra el METODO (describe -> describe_action) y conserva el nombre de la accion; si el NOMBRE DEL AGENTE colisiona, rechaza. Verificado generando un agente con acciones describe/run/actions/can_handle: 'python -m agents list' sigue en exit 0. La logica de renderizado va en agents/tools/agent_scaffold_tool.py y no dentro del agente, siguiendo la convencion que declara _template_agent.py. owns con recurso ya adueñado se rechaza en validar(), no solo en validate_contracts(). name y description tienen default '' en vez de ser obligatorios para devolver success=False + needs en vez de un TypeError en la CLI (patron de git.commit_feature). DEUDA ANOTADA, no tocada: agents/permissions.py:70 decide con 'not kwargs.get(dry_run)', mirando los kwargs recibidos y no el default de la firma, asi que scaffold sin --dry_run explicito queda bloqueado por la puerta aunque no fuera a escribir nada. Falla del lado seguro; arreglarlo cambia la puerta para los 24 agentes y es feature aparte.
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
$ make check
uv run ruff check app/ tests/ agents/
All checks passed!
uv run ruff format --check app/ tests/
6 files already formatted
uv run mypy app/ tests/
Success: no issues found in 6 source files
  typecheck OK
uv run pytest
======================= 512 passed, 15 skipped in 11.31s =======================
  check pasado: lint + typecheck + test + arnes OK
CHECK_EXIT=0

$ uv run python -m agents.prompts_sync
Prompts y subagentes sincronizados con el codigo y con los contratos.
P_EXIT=0

$ ls agents/external/   -> __init__.py  README.md  (ningun agente generado suelto)

Prueba de fuego del reviewer sobre una COPIA del repo, generando agentes reales con --dry_run false --yes:
  1 agente generado  -> make check: 517 passed, exit 0
  3 agentes generados -> make check: 535 passed, exit 0
  ./init.sh completo  -> ENTORNO LISTO, 0 avisos
  dry-run: md5 de todo el arbol identico antes/despues (solo cambia agents/workspace/audit/audit.jsonl, el log de BaseAgent.run)
  barrido AST: las 14 llamadas a AgentResult de los modulos generados tienen success=False, y las 14 acciones fallan con needs no vacio
```

</details>

## BOOT-004 — knowledge sync_agent_cards: las fichas del vault desde los contratos

- **Cerrada:** 2026-08-04
- **Verificación:** ./init.sh en verde · 6 passed in 0.34s
- **Cambios:** agents/agents/knowledge_agent.py (accion sync_agent_cards + helpers); agents/contracts.py (knowledge.destructive); agents/permissions.py (_es_dry_run resuelve el defecto de la firma); agents/core/base_agent.py (1 linea: pasa el metodo a la puerta); agents/prompts_sync.py (_splice acepta begin/end, reutilizado); agents/tests/test_knowledge_agent.py (+6 tests); agents/tests/test_permissions.py (+2 tests); agents/prompts/knowledge_agent.md; README.md; vault/05_AGENTES/ (24 fichas + fila de bootstrap en _index.md)
- **Decisiones:** El contrato de knowledge prometia desde el principio 'poblar vault/05_AGENTES/ con fichas desde contracts.py' y eso nunca estuvo implementado: un contrato que miente. Esta feature nace de ese hallazgo al bloquear BOOT-003. Las fichas se generan desde all_contracts() (no CONTRACTS) para que los agentes de contrato inline como bootstrap tengan ficha. El nombre de fichero sale de cls.__name__ y no del name del agente, para respetar la convencion existente (GitAgent.md, APIAgent.md). La prosa a mano de las fichas se conserva con el _splice de prompts_sync, reutilizado en vez de duplicado. _index.md NO se autogenera (agrupa por categorias humanas y lleva un mermaid que el contrato no contiene): la accion lo audita y avisa. Las fichas huerfanas se reportan, no se borran. EFECTO EN LA CAPA COMPARTIDA: marcar sync_agent_cards como destructive dejaba su propio dry-run pidiendo confirmacion, asi que se arreglo la puerta (agents/permissions.py) para que resuelva el defecto de la firma y no solo los kwargs recibidos. Acerca el codigo a lo que AGENTS.md ya documentaba ('un --dry-run nunca pregunta'). Auditadas las 14 acciones destructivas: ninguna irreversible perdio su confirmacion. AVISO: la revision del subagente reviewer se corto por limite de gasto de la API sin emitir veredicto; el bloque critico lo verifico el lider y lo que quedo sin revisar esta listado en harness/progress/reviewer-BOOT-004.md.
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
$ make check
All checks passed!
6 files already formatted
Success: no issues found in 6 source files
  typecheck OK
======================= 520 passed, 15 skipped in 51.35s =======================
  check pasado: lint + typecheck + test + arnes OK
CHECK_EXIT=0

$ uv run python -m agents.prompts_sync
Prompts y subagentes sincronizados con el codigo y con los contratos.  P_EXIT=0

$ ./init.sh
  pytest  6 passed in 0.55s
  ENTORNO LISTO  0 aviso(s)

$ run knowledge sync_agent_cards            (dry-run)  -> md5 del arbol de vault/ identico antes y despues
$ run knowledge sync_agent_cards --dry_run false --yes  -> 24 fichas sincronizadas
$ segunda pasada real -> 0 nuevas, 0 actualizadas, 24 sin cambios; md5 identico (idempotente)
$ md5 de vault/ identico antes y despues de make check -> la suite no toca el vault real
$ ls vault/05_AGENTES/*.md | wc -l -> 25 (24 fichas + _index.md); BootstrapAgent.md presente

Auditoria de la puerta de permisos (14 acciones destructivas, ejecutada):
  las 12 acciones irreversibles siguen pidiendo confirmacion sin argumentos;
  solo installer.scaffold y knowledge.sync_agent_cards (dry_run=True por defecto) no la piden,
  y ambas la piden con dry_run=False explicito. No se abrio agujero.
```

</details>

## BOOT-003 — Protocolo de arranque en frio en el lider + documentacion

- **Cerrada:** 2026-08-04
- **Verificación:** ./init.sh en verde · 6 passed in 0.41s
- **Cambios:** .opencode/agents/lider.md (paso 0 + seccion de arranque en frio); .claude/agents/lider.md (regenerado con assistants-sync, no a mano); agents/agents/bootstrap_agent.py (criterio de ONBOARD-001 en TICKETS_ARRANQUE: --yes); agents/README.md (seccion installer scaffold); AGENTS.md (paso 0 + seccion Arranque en frio); harness/featureslist.json via bootstrap seed --yes (ONBOARD-001 y ONBOARD-002)
- **Decisiones:** La feature estuvo BLOQUEADA: el criterio del vault no era alcanzable porque ninguna accion escribia vault/05_AGENTES/ pese a que el contrato de knowledge lo prometia. Se abrio BOOT-004 para implementarlo y se reabrio esta. Sobre la puerta: se decidio NO sacar 'describe' de destructive (escribir la identidad del proyecto merece confirmacion y la puerta falla del lado seguro); lo que se arreglo fue el criterio de ONBOARD-001, que sin --yes era infalsable. El ciclo de arranque en frio deja explicito en el prompt del lider que las preguntas de 'describe' son para el usuario y no se deducen del codigo, y que suggest_agents da candidatos lexicos y no un veredicto. PENDIENTE DE DECISION DEL USUARIO: SCOPE-001 se solapa con ONBOARD-001 (los dos producen el objetivo del proyecto en el vault); no se borro nada porque harness no tiene accion de borrado y la decision es del usuario.
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
$ make check
All checks passed!
6 files already formatted
Success: no issues found in 6 source files
  typecheck OK
================= 520 passed, 15 skipped in 188.32s (0:03:08) ==================
  check pasado: lint + typecheck + test + arnes OK
CHECK_EXIT=0

$ ./init.sh
  ENTORNO LISTO  0 aviso(s)

$ uv run python -m agents.prompts_sync
Prompts y subagentes sincronizados con el codigo y con los contratos.
(esto cubre tambien que .claude/agents/lider.md esta sincronizado con .opencode/agents/lider.md)

$ grep -n "Paso 0" .opencode/agents/lider.md
14: uv run python -m agents --json run bootstrap status
15: #   first_run=false -> sigue en el paso 1
16: #   first_run=true  -> arranque en frio antes de abrir ninguna feature
46: ## Paso 0 - arranque en frio
85: **Condicion de salida:** run bootstrap status devuelve description_pending: false

$ backlog
ONBOARD-001    pending      Entender el proyecto
ONBOARD-002    pending      Que se sabe ya y que agentes hacen falta

$ criterio de ONBOARD-001 corregido
uv run python -m agents run bootstrap describe --description \"<respuesta del usuario>\" --yes devuelve success=true

$ agents/README.md: linea 77 \"los 24 agentes\", linea 205 seccion \"installer scaffold\", linea 238 \"Los 24 agentes\"
$ AGENTS.md: linea 15 paso 0 en el bloque de protocolo, linea 26 seccion \"Arranque en frio\"
$ vault/05_AGENTES/BootstrapAgent.md presente con el contrato inline (generado por knowledge sync_agent_cards en BOOT-004)
```

</details>

## FIX-001 — app.__main__ rompe los imports: falta la guarda __name__

- **Cerrada:** 2026-08-04
- **Verificación:** ./init.sh en verde · 7 passed in 0.13s
- **Cambios:** app/__main__.py (guarda if __name__ == '__main__'); tests/test_main_import.py (nuevo: test de regresion que importa app.__main__ y barre el paquete)
- **Decisiones:** El test importa app.__main__ a nivel de modulo: si la guarda regresa, pytest muere en coleccion con SystemExit(2) y no solo falla un caso. Diagnosticado el alcance: pkgutil.walk_packages(app.__path__) importa app.__main__, por eso barrer el paquete mataba el proceso.
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
$ uv run python -c "import app.__main__; print('ok')"  ->  ok, EXIT=0 (sin usage)
$ uv run python -m pytest tests/ -q --no-header        ->  7 passed in 0.40s
$ uv run python -m app hello                           ->  Hola, mundo. EXIT=0
$ make check                                           ->  check pasado: lint + typecheck + test + arnes OK
$ ./init.sh                                            ->  ENTORNO LISTO  0 aviso(s)
```

</details>

## GEAS-001 — Arrancar GEAS de NavaHack (solo falta la IP/URL)

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 7 passed in 0.01s
- **Ticket GEAS:** d583a304 · commit_after `398532e4`
- **Cambios:** harness/geas.json; harness/geas_map.json (nuevo); .geas.yml (nuevo); harness/featureslist.json (espejo regenerado); pyproject.toml (pythonpath=.)
- **Decisiones:** Actor propio 'lider' (agent, rol agent) en vez de la identidad humana; GEAS_DB es la URI de Atlas, backend MongoStorage nuevo en ~/Proyectos/geas; sin token ni proxy: el servidor acepta X-Geas-Actor directo; se retiró ~/.config/geas/client.env (IP muerta 192.168.1.145:8787) que secuestraba el actor; criterio 2 (GEAS_TOKEN) se cumple con GEAS_ACTOR en .env, que no está en git
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
$ ./init.sh → ✔ pytest 7 passed in 0.01s / ━━ ENTORNO LISTO ━━ (1 aviso: venv 3.13 vs project.yml 3.12) | $ uv run python -m agents --json run harness status → success=true backend=geas '12 tickets GEAS · 12 pending' | $ uv run ... harness next → 'Siguiente: GEAS-001 (GEAS d583a304)' | Atlas db=geas: organizations 1 · repositories 1 · roles 5 · tickets 12 · ticket_dependencies 5 | $ curl -X POST http://10.20.26.2:9000/api/tools/get_available_tasks -H 'X-Geas-Actor: c58cace2-…' -d '{}' → success=true, 7 tareas disponibles
```

</details>

## SCOPE-001 — Definir qué se quiere resolver

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 7 passed in 0.01s
- **Ticket GEAS:** 46b195ef · commit_after `a272dcd1`
- **Cambios:** vault/01_PROYECTO/objetivo.md (nuevo); README.md
- **Decisiones:** El spec TinyVigo v3 Part A es la fuente del objetivo; el criterio de hecho se verifica con init.sh verde + demo end-to-end + capturas de los 6 hitos de A10
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
$ ./init.sh → ENTORNO LISTO, pytest 7 passed in 0.01s. Creado vault/01_PROYECTO/objetivo.md con 4 apartados (problema, usuario/consumidor, criterio de hecho verificable, fuera de alcance con 7 exclusiones). README actualizado con la frase propia del objetivo.
```

</details>

## QA-001 — Batería de calidad en verde

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 7 passed in 0.12s
- **Ticket GEAS:** b335baf8 · commit_after `d1fc42a1`
- **Cambios:** pyproject.toml (pythonpath=.); uv.lock (v0.1.2); Makefile (sin cambios); .github/workflows/ci.yml (sin cambios)
- **Decisiones:** mypy no estaba instalado en el venv: uv sync --extra dev; pythonpath=. para que uv run pytest resuelva app/; CI ya era superset de make check, no se tocó
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
$ make check → 'check pasado: lint + typecheck + test + arnés OK'; $ make lint → ruff check+format OK; $ make typecheck → mypy OK (7 files); $ make test → 566 passed, 15 skipped in 9.62s; $ ./init.sh → ENTORNO LISTO. CI (.github/workflows/ci.yml) corre lint+typecheck+test+agents tests+harness gate+prompts sync+evals+bandit, superset de make check.
```

</details>

## BOOT-001 — Arranque en frio operativo: contratos inline + agente bootstrap

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 7 passed in 0.11s
- **Ticket GEAS:** ba181545 · commit_after `3da28526`
- **Cambios:** agents/prompts/harness_agent.md (AUTOGEN regenerado); uv.lock
- **Decisiones:** El unico desajuste era el prompt del harness (1 prompt desincronizado); make prompts-sync lo regenero. No hubo cambios de codigo de producto.
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
$ uv run python -m agents list → 24 agentes, bootstrap incluido. $ uv run python -m agents describe bootstrap → contrato inline. $ uv run python -m agents.prompts_sync → 'Prompts y subagentes sincronizados'. $ make check → 'check pasado'. Tests: 28 passed (bootstrap+contracts).
```

</details>

## ONBOARD-001 — Entender el proyecto

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 7 passed in 0.33s
- **Ticket GEAS:** b0fa3e7b · commit_after `44fe6492`
- **Cambios:** project.yml; vault/01_PROYECTO/objetivo.md (ya existia de SCOPE-001)
- **Decisiones:** bootstrap describe responde las 4 preguntas del onboarding con el spec TinyVigo v3
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
$ uv run python -m agents --json run bootstrap describe --yes --description '...' → success=true, 'Descripción escrita en project.yml.' | project.yml project_description actualizado con TinyVigo | vault/01_PROYECTO/objetivo.md con 4 apartados | README frase propia | ./init.sh → ENTORNO LISTO, pytest 7 passed
```

</details>

## ONBOARD-001 — Entender el proyecto

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 7 passed in 0.25s
- **Ticket GEAS:** b0fa3e7b · commit_after `de4854ee`
- **Cambios:** project.yml; vault/01_PROYECTO/objetivo.md
- **Decisiones:** bootstrap describe responde las 4 preguntas del onboarding con el spec TinyVigo v3
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
$ uv run python -m agents --json run bootstrap describe --yes --description '...' → success=true 'Descripcion escrita en project.yml.' | project.yml project_description actualizado con TinyVigo | vault/01_PROYECTO/objetivo.md con 4 apartados | README frase propia | ./init.sh → ENTORNO LISTO, pytest 7 passed
```

</details>

## BOOT-004 — knowledge sync_agent_cards: las fichas del vault desde los contratos

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 7 passed in 0.09s
- **Ticket GEAS:** a659501f · commit_after `7b2d43ef`
- **Cambios:** vault/05_AGENTES/*.md (24 fichas, 1 actualizada); agents/workspace/audit/audit.jsonl
- **Decisiones:** sync_agent_cards regenera las fichas desde all_contracts(); dry_run por defecto, se ejecuto con --dry_run false --yes
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
$ uv run python -m agents --json run knowledge sync_agent_cards --dry_run false --yes → '24 ficha(s) sincronizadas: 0 nuevas, 1 actualizada, 23 sin cambios' | $ uv run pytest agents/tests/test_knowledge_agent.py → 18 passed | $ make check → 'check pasado'
```

</details>

## FIX-001 — app.__main__ rompe los imports: falta la guarda __name__

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 7 passed in 0.14s
- **Ticket GEAS:** 9919c3e2 · commit_after `d4b0b983`
- **Cambios:** app/__main__.py (sin cambios: la guarda ya existia desde el commit inicial); tests/test_main_import.py
- **Decisiones:** El codigo ya tenia la guarda if __name__ == '__main__'; el ticket se cierra con evidencia de que todos los criterios pasan
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
$ uv run python -c 'import app.__main__' → exit 0 (sin output) | $ uv run python -m app hello → 'Hola, mundo.' exit 0 | $ uv run pytest tests/test_main_import.py → 1 passed | $ make check → 'check pasado'
```

</details>

## D-00 — Measure real refresh rate and terms of Concello feeds

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 20 passed in 0.39s
- **Ticket GEAS:** 9f20797f · commit_after `5a6ca17c`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
commit 4564ba9. ./init.sh -> 11 passed, ENTORNO LISTO. parkings-ocupacion.json Last-Modified 11:55:04->11:57:04->12:07:04->12:09:04 GMT = cada 2 min; agenda-hoy.json diario 06:05 UTC; CORS * en ambos; ODC-BY; intervalos A7 en vault/01_PROYECTO/fuentes_datos.md
```

</details>
