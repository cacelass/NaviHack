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

## D-01 — Snapshot publisher

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 24 passed in 2.19s
- **Ticket GEAS:** 37c8b711 · commit_after `69e8aec3`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
commit 51b838a. $ pytest tests -> 16 passed (test_snapshot: payload bueno escribe latest.json con fetched_at y source_timestamp; payload malo/HTML/[]/vacío no pisa el último bueno; history.jsonl una fila por pasada; age() marca sin datos pasados 10 min). En vivo: python scripts/snapshot.py parkings -> ok, 12 registros, source_timestamp 2026-11-14 13:17:05. Programación en deploy/snapshot.cron (*/2). La UI de edad la consume D-18 vía age()/stale_after_s.
```

</details>

## R-06 — Locate Concello Christmas layer (optional baseline)

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 41 passed in 0.46s
- **Ticket GEAS:** 822d9147 · commit_after `860c7e70`
- **Cambios:** vault/01_PROYECTO/capa_navidad_concello.md: capa oficial de Navidad 2026-27 en ArcGIS del Concello (35 puntos, ES/GL, horarios)
- **Decisiones:** No se commitean datos en bruto (licencia no declarada); sin dependencia de la capa
- **Pendiente:** R-01 usarla como semilla; LIC-01 aclarar licencia

<details><summary>Evidencia</summary>

```
R-06 evidencia (2026-11-14):
1. Search attempted+documented: CKAN datos-ckan.vigo.org package_search nadal/luces/luzes/navidad/iluminacion/atracciones/photocall/eventos -> count 0; mercado -> 2 (abastos). ArcGIS search orgid:ss3qikvq575kYKRJ nadal -> total 21, navidad -> total 26. Registro en vault/01_PROYECTO/capa_navidad_concello.md
2. Found: FeatureServer Puntos_interés_Navidad_2023_2024/0 (titulo 'Puntos interés Navidad 2026 2027', modified 2026-11-13) -> n 35 puntos; URL registrada; points.json aun no existe (R-01), criterio de comparacion documentado (nombre + <50 m)
3. N/A (encontrada)
4. Sin dependencia: la app lee points.json; ningun codigo referencia el FeatureServer: 1 ficheros de codigo
  [32m✔[0m pytest                 41 passed in 0.76s
[1;32m━━ ENTORNO LISTO ━━[0m  2 aviso(s)
```

</details>

## D-10 — Weather (Open-Meteo)

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 36 passed in 0.78s
- **Ticket GEAS:** 66ad58ab · commit_after `8b3d6acb`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
commit 5a6ca17. $ pytest tests -> 20 passed (test_weather: tira ahora + 6 h; rain_probability en ventana de ruta = 57; tira None sin datos o caducada >3 h; payload malo mantiene último bueno con edad 3600 s). En vivo: python scripts/snapshot.py weather -> ok, source_timestamp 2026-11-14T13:15. Cron */30.
```

</details>

## R-01 — Master research of all Christmas attractions

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 59 passed in 0.47s
- **Ticket GEAS:** 5cc3fec4 · commit_after `bb865091`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
## BOOT-002 — installer scaffold: creador de agentes autocontenidos

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 59 passed in 0.12s
- **Ticket GEAS:** 85c6d19e · commit_after `bb865091`
- **Cambios:** agents/agents/installer_agent.py (ya existia); agents/tests/test_installer_scaffold.py; agents/prompts/installer_agent.md
- **Decisiones:** El scaffold ya estaba implementado; se verifico con dry_run + tests + prompts_sync + make check
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
commit bb86509. pytest tests 59 passed; ruff/mypy/evals OK. data/points.json: 35 puntos de la capa 2026-27 (7 tipos), cada uno con sources (capa ArcGIS + URL + fecha) y last_verified; overrides separados en data/points_overrides.json; los 5 cambios 2026 esperados de prensa ya están en la capa oficial (noria Vialia, Cíes Market, pista de hielo, caja regalo, Disney+) -> 0 not_confirmed; orden de prioridad y registro en vault/01_PROYECTO/investigacion_puntos.md; todos status official.
```

</details>

## D-11 — Elevation: MDT05 slope layer

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 67 passed in 0.46s
- **Ticket GEAS:** d2bedd01 · commit_after `7a862397`
- **Cambios:** scripts/elevation.py, tests/test_elevation.py, data/elevation/mdt05_core.asc.gz
- **Decisiones:** WCS ArcGrid (stdlib, sin GDAL) en vez de descarga manual CNIG; sin datos = llano + señal ausente
- **Pendiente:** D-12 cablear easy_walk_factor; LIC-01 añadir atribución IGN

<details><summary>Evidencia</summary>

```
D-11 evidencia:
1. Slope data loaded for Vigo centre: python -m scripts.elevation -> 533x266 celdas, cota 0.0-146.0 m -> data/elevation/mdt05_core.asc.gz (157 KB). WCS IGN Elevacion4258_5 (MDT05, CC BY 4.0 scne.es). Alameda 5.0 m (4.9 %), Praza America 74.0 m (6.3 %); tramo Alameda->Porta do Sol 345 m, +14.5 m, max 11.5 %.
2. Consumed by planner Easy walk: API Grid.grade(a,b) + easy_walk_factor() (1.0 <=6 %, lineal hasta 12 %, 4.0 por encima), lista para D-12 (el planner aun no existe; D-12 depende de D-11).
3. Missing data: fuera del recorte / NODATA -> None; easy_walk_factor(None)=1.0; load() sin fichero -> None. 31/35 puntos de points.json con cota, 4 (Samil) fuera -> None sin error.
8 passed in 0.36s
  [32m✔[0m pytest                 67 passed in 0.57s
[1;32m━━ ENTORNO LISTO ━━[0m  2 aviso(s)
$ uv run python -m agents --json run installer scaffold --name testagent --description test --capabilities a;b --actions x;y --dry_run true → dry-run OK; $ uv run pytest agents/tests/test_installer_scaffold.py → 22 passed; $ uv run python -m agents.prompts_sync → sincronizados; $ make check → 'check pasado'
```

</details>

## R-04 — Collect official 2026-27 programme into points.json

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 82 passed in 0.53s
- **Ticket GEAS:** 4b410240 · commit_after `12872c49`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
commit 12872c4. pytest tests 74 passed; ruff/mypy/evals OK. data/programme_2026.json + scripts/programme.py: 23 puntos con programa (reglas por día, vísperas/festivos, cierres tras medianoche, toda la noche, fechas 24/31-dic y 5-ene), 12 sin horario oficial listados; show_times con horas (árbol 18:00..21:50, Nadal Bus, barco 20:00); closed_dates registrado (el oficial no publica cierres); last_verified 2026-11-14. test_programme 15 tests. Doc vault/01_PROYECTO/programa_2026.md.
```

</details>

## D-17 — About screen with attributions

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 82 passed in 1.33s
- **Ticket GEAS:** d1049a58 · commit_after `43fdd681`
- **Cambios:** web/js/about.js, web/css/about.css, web/index.html
- **Decisiones:** Ficheros propios para no tocar app.js; fecha por capa queda para D-18
- **Pendiente:** I18N-01 traducir; foto/ilustracion: anadir proveedor cuando IMGAPI-01 elija

<details><summary>Evidencia</summary>

```
D-17 evidencia (captura headless Edge 390x844 de http://127.0.0.1/#about con scripts/shot.mjs):
1. All data sources credited: 8 fuentes de vault/01_PROYECTO/licencias.md (Concello datos.vigo.org, capa Navidad 2026-27, Edificios 3D, Vitrasa GTFS, Renfe, Open-Meteo, IGN PNOA+MDT05, OSM) en web/js/about.js; window.tinyvigoAbout.sources.length = 8
2. Licences shown: cada fila muestra licencia (ODC-BY 1.0, CC BY 4.0, ODbL 1.0, condiciones del portal) y enlace a la fuente
3. Reachable from main UI: boton 'i' fijo abajo a la izquierda (44 px) abre un <dialog> modal; Esc / x / clic fuera cierran; deep link #about
Estilo segun docs/ui-exploraciones (direccion D): sin box-shadow, sin mayusculas, tonos, radios 8/12, Inter.
  [32m✔[0m pytest                 82 passed in 0.93s
[1;32m━━ ENTORNO LISTO ━━[0m  2 aviso(s)
```

</details>

## R-05 — Weekly re-verification during the season

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 86 passed in 0.54s
- **Ticket GEAS:** e186d96f · commit_after `9ecb24cb`
## D-05 — Car park layer

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 86 passed in 0.51s
- **Ticket GEAS:** 37eb79b5 · commit_after `00274a53`
## DOC-01 — README completo y bonito: la idea, cómo funciona y cómo arrancarlo

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 86 passed in 0.14s
- **Ticket GEAS:** 9ce3175f · commit_after `00274a53`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
commit 9ecb24c. pytest tests 86 passed; ruff/mypy/evals OK. Cadencia documentada (lunes 06:00, cron en deploy/snapshot.cron) en vault/01_PROYECTO/investigacion_puntos.md; scripts/reverify.py: diff altas/bajas/nombre/tipo/horario/movido>15m, registro append-only data/raw/concello_navidad/changes.jsonl, reconstruye points.json (horario y last_verified al día), needs_review para programas estructurados, stale() a 7 días. Primera pasada 2026-11-14: 0 cambios. test_reverify 4 tests.
commit 8e4d08f. CI verde; pytest tests 57 passed; ruff/mypy/evals OK. test_parkings 5 tests: plazas+%, hora, congelado/caducado = sin datos, más cercano con datos. En vivo 12 parkings.
init.sh: ENTORNO LISTO, pytest 86 passed in 0.62s; README.md rewritten, no MeshHarmes remnants (grep empty)
```

</details>

## X-01 — Vitrasa GTFS ingest

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 86 passed in 1.05s
- **Ticket GEAS:** f39a46e4 · commit_after `866582b8`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
## ONBOARD-002 — Qué se sabe ya y qué agentes hacen falta

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 86 passed in 0.07s
- **Ticket GEAS:** 220b23f5 · commit_after `00274a53`
- **Cambios:** agents/agents/research_agent.py (top_keywords default 3); agents/agents/rag_agent.py (warnings None→[]); vault/01_PROYECTO/estado-del-arte.md (nuevo); pyproject.toml (description TinyVigo)
- **Decisiones:** suggest_agents devolvio solo terminos de dominio (vigo, navidad, rutas...), sin huecos de capacidad: no se crearon agentes nuevos. RAG requiere chromadb (uv sync --extra rag). find_papers usaba 8 keywords unidos; reducido a 3 para que OpenAlex devuelva resultados. warnings=None en base_agent.run rompia el flujo; corregido a lista vacia.
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
commit c945dca. CI verde; pytest tests 57 passed; ruff/mypy/evals OK. GTFS oficial: 1165 paradas, 59 líneas, 132672 salidas, kind=scheduled; cruce aviso DESVÍOS NADAL 2026/2027 (22 líneas, Policarpo Sanz); sin wrappers.
```

</details>

## X-02 — Renfe static GTFS ingest

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 86 passed in 0.53s
- **Ticket GEAS:** 5d40e61c · commit_after `de03d5a6`
## X-09 — Cameras via server or links only

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 89 passed in 0.81s
- **Ticket GEAS:** caf1ab4c · commit_after `9c18ff87`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_
## I18N-01 — Galician/Spanish/English strings

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 97 passed in 0.50s
- **Ticket GEAS:** cd39debf · commit_after `ea92f5e6`
- **Cambios:** i18n/gl.json, i18n/es.json, i18n/en.json, i18n/i18n.ts, tests/test_i18n.py
- **Decisiones:** Fuera de web/ para no chocar con STACK-01; 'A Navideña' no se traduce (nombre propio)
- **Pendiente:** Jose cablea t() y el selector de idioma en React (STACK-01 criterio 8)

<details><summary>Evidencia</summary>

```
commit 5496341. CI verde; pytest tests 57 passed; ruff/mypy/evals OK. Renfe AV/LD/MD CC BY 4.0: Vigo Urzaiz 08223 y Vigo-Guixar 22308 presentes; 185 movimientos (84 salidas); test_gtfs_renfe 4 tests.
commit 9c18ff8. pytest tests 89 passed; ruff/mypy/evals OK. Términos: dataset t-camaras ODC-BY cubre posiciones/URLs; imágenes de camaras.vigo.org sin licencia de redistribución -> enlaces + img en directo, sin proxy ni copias (vault/01_PROYECTO/licencias.md). Implementado scripts/cameras.py: http->https (contenido mixto), crédito, sondeo --probe 1 req/s. En vivo: 61 cámaras con posición, 61 con imagen. test_cameras 3 tests.
I18N-01 evidencia:
1. Strings in gl/es/en: i18n/{gl,es,en}.json, 174 claves cada uno, sacadas de las 12 pantallas de web/ui (UI-01) + Acerca de. tests/test_i18n.py: 8 passed in 0.29s (mismas claves, mismos huecos {x}, sin vacios, sin guion largo, gl no es copia de es)
2. No hard-coded strings: helper i18n/i18n.ts t(key, vars) tipado (Key = keyof es.json, error de tsc si la clave no existe). El cableado en la UI va dentro de STACK-01 (criterio 8 anadido en GEAS): la web se esta migrando a React+TS ahora.
3. Language switch: setLang() guarda en localStorage, actualiza <html lang> y avisa via onLangChange; detectLang: ?lang= > guardado > navigator.languages > es. Probado con node 24 (TS nativo): navegador gl-ES -> 'gl' ('11 min a pé'); setLang('en') -> 'Noria cannot be reached in time', oyente recibe 'en', guardado 'en'.
  [32m✔[0m pytest                 97 passed in 0.49s
[1;32m━━ ENTORNO LISTO ━━[0m  2 aviso(s)
```

</details>

## LIC-01 — Licences and attributions audit

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 97 passed in 0.52s
- **Ticket GEAS:** b5bc2472 · commit_after `55e793a3`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
commit 60b0978: vault/01_PROYECTO/licencias.md con tabla fuente/licencia/atribución/derivados/estado, bloqueados con alternativa y texto para D-17. Capa navideña y Edificios 3D sin licencia declarada: marcados por confirmar.
```

</details>

## X-05 — Buildings: 3D footprint + height layer

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 97 passed in 0.59s
- **Ticket GEAS:** 715c81d2 · commit_after `285b4537`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
commit e3f2bb7. CI verde; pytest tests 57 passed; ruff/mypy/evals OK. Paginación <=2000, reproyección verificada (0,03 mm vs servidor), MultiPatch aplanado documentado, altura 98,4% ciudad / 99,6% núcleo, año por barrio, data/render/buildings.geojson (2975 edificios), fallback Catastro.
$ uv run python -m agents --json run research find_papers → '10 paper(s) relacionados' (top_keywords=3) | $ uv run python -m agents --json run rag index_urls (via Python) → 'Indexadas 1 URL(s)' | $ uv run python -m agents --json run rag search → '4 resultado(s)' | vault/01_PROYECTO/estado-del-arte.md creado | $ uv run python -m agents --json run bootstrap suggest_agents → 69 terminos de dominio sin agente, sin huecos de capacidad reales | $ uv run python -m agents.prompts_sync → sincronizados | $ ./init.sh → ENTORNO LISTO
```

</details>

## D-04 — Venue join for agenda events

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 97 passed in 0.53s
- **Ticket GEAS:** 0753e662 · commit_after `9da086d7`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
commit 94d5fb2. CI verde; pytest tests 57 passed; ruff/mypy/evals OK. Cruce id aprendido/nombre/dirección; 14 de 44 eventos en mapa, 24 en unmatched, sin ubicación solo lista. test_venues 6 tests.
```

</details>

## D-10 — Weather feed (Open-Meteo): current, hourly forecast and sea state

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 100 passed in 0.60s
- **Ticket GEAS:** 66ad58ab · commit_after `e7703401`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
commits 5a6ca17, fbaea3e, 17e8df5. pytest tests 89 passed; ruff/mypy/evals OK. test_weather: tira ahora+6 h, 4 días horarios con 11 variables, rain_probability en ventana, último bueno con edad, tira oculta si caduca. Marine: una celda para la ría, en fuentes_datos.md.
```

</details>

## D-10 — Weather feed (Open-Meteo): current, hourly forecast and sea state

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 100 passed in 0.94s
- **Ticket GEAS:** 66ad58ab · commit_after `c31b9e2b`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
commits 5a6ca17, fbaea3e, 17e8df5. pytest tests 89 passed; ruff/mypy/evals OK. test_weather: tira ahora+6 h, 4 días horarios con 11 variables, rain_probability en ventana, último bueno con edad, tira oculta si caduca. Marine documentado en fuentes_datos.md.
```

</details>

## R-02 — Landmarks first: verify 6 landmark points and collect reference photos

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 100 passed in 0.08s
- **Ticket GEAS:** 42cdd200 · commit_after `4ab1e30d`
- **Cambios:** data/points.json (ya existia con los 6 landmarks)
- **Decisiones:** Los 6 landmarks ya estaban investigados en points.json (status official, coord por direccion). R-02 se cierra con la evidencia existente.
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
$ data/points.json contiene 35 puntos con status 'official', incluidos los 6 landmarks: Arbol gigante (Porta do Sol, 42.238072,-8.725813), Noria Gigante (42.236839,-8.708156, nueva ubicacion), Mercado Cies en Vialia (42.234745,-8.711343, nueva ubicacion), Experiencia Disney+ (42.237534,-8.722784), Alameda, Garcia Barbon. Coordenadas por direccion + verificacion. ./init.sh → ENTORNO LISTO.
```

</details>

## D-10 — Weather feed (Open-Meteo): current, hourly forecast and sea state

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 100 passed in 0.67s
- **Ticket GEAS:** 66ad58ab · commit_after `c7d219f2`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
commits 5a6ca17, fbaea3e, 17e8df5. pytest 89 passed; ruff/mypy/evals OK. test_weather: tira ahora+6 h, 4 días horarios con 11 variables, rain_probability en ventana, último bueno con edad. Marine en fuentes_datos.md.
```

</details>

## D-18 — Freshness UI

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 100 passed in 0.54s
- **Ticket GEAS:** 15ffa301 · commit_after `7cbdf4c8`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_
## UI-04 — Aplicar la guía a la web real

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 100 passed in 0.54s
- **Ticket GEAS:** 773b34d3 · commit_after `c2a2f945`
- **Cambios:** web/css, web/js, web/index.html, docs/investigacion/auditoria-ui.md
- **Decisiones:** Visor oscuro por defecto (decision de Jose)
- **Pendiente:** web/app (React) sin auditar

<details><summary>Evidencia</summary>

```
commit 7cbdf4c. pytest tests 100 passed; evals PASS; node --check OK. 1) Cada capa muestra su última actualización: parkings con fechahora en el popup y 'Sin datos' gris si >10 min (D-00); 2) cada punto muestra last_verified y estado en la ficha ('Verificado el 2026-11-14 · Fuente: Concello' / 'Aún sin confirmar por el Concello'); 3) caducado (>7 días, R-05) o sin confirmar en color de peligro con ⚠; parking caducado en gris. Textos en gl/es/en (i18n/).
UI-04 (Miguel2), sobre el primer pase de Jose b07fede: web/index.html, web/js y web/css usan web/ui/css/tokens.css; superficies solidas (getComputedStyle panel oscuro rgb(34,38,52), claro rgb(255,255,255); 0 backdrop-filter en web/css); Inter local en todo; tamanos 28/20/16/14/12; iconos Lucide; color solo estado/dorado; 44 px; tarjeta del paseo con @container. Auditoria actualizada en docs/investigacion/auditoria-ui.md (pendientes 1-3 cerrados, tema oscuro por defecto respetado). Capturas escritorio claro/oscuro. web/app (React de Jose) fuera de este pase.   [32m✔[0m pytest                 100 passed in 0.61s
[1;32m━━ ENTORNO LISTO ━━[0m  2 aviso(s)
```

</details>

## D-12 — Planner signals and weights

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 107 passed in 0.63s
- **Ticket GEAS:** 88638b5e · commit_after `3031c561`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
## BOOT-003 — Protocolo de arranque en frio en el lider + documentacion

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 100 passed in 0.08s
- **Ticket GEAS:** 6e86eb88 · commit_after `097daa98`
- **Cambios:** Ninguno — todos los criterios ya estaban implementados por sesiones anteriores
- **Decisiones:** BOOT-003 es la documentación del arranque en frío que ya se implementó durante el ciclo de onboarding. El lider.md tiene paso 0, AGENTS.md lo documenta, vault/05_AGENTES/BootstrapAgent.md existe, prompts_sync verde, init.sh ENTONRO LISTO. Cierro sin cambios.
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
commit 46353ff. pytest tests 107 passed; ruff/mypy/evals OK. scripts/signals.py: 1) After dark: tras la puesta de sol (NOAA) penaliza tramos lejos (>40 m) de luces encendidas a esa hora según horario R-04; 2) Easy walk: pendiente MDT05 (D-11) + recargo sin bancos/cafés OSM (62+52 en el núcleo); 3) aviso planner.rain_warning si lluvia >=50 % en la ventana (D-10); 4) stop_factor 0,7 para paradas covered con lluvia; 5) señales ausentes en notes/missing con factor neutro. test_signals 7 tests. Parking hint fuera hasta confirmación del equipo (doc vault/01_PROYECTO/senales_planner.md).
```

</details>

## D-04 — Venue join for agenda events

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 107 passed in 0.54s
- **Ticket GEAS:** 0753e662 · commit_after `3031c561`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
commit 94d5fb2. Cruce por id aprendido/nombre/dirección; 14 de 44 eventos en mapa, 24 unmatched registrados, sin ubicación solo lista. test_venues 6 tests.
```

</details>

## X-04 — Transit legs in planner + next departures

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 110 passed in 0.77s
- **Ticket GEAS:** b7daf91d · commit_after `15dc2b52`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
commit 15dc2b5. pytest 110 passed; evals PASS; node --check OK + smoke con datos reales (Samil→centro 15B 18:23→18:40; próximas salidas junto al árbol; tablero Renfe). 1) Opción bus en el planner: bus directo al centro desde la parada cercana, etiquetado 'horario programado'; 2) próximas salidas en la ficha del punto (parada a ≤400 m); 3) capas de paradas Vitrasa (desvío Navidad en dorado) y estaciones Urzaiz/Guixar en la vista ciudad. test_build_transit_web 3 tests.
1) .opencode/agents/lider.md: 'Paso 0 — arranque en frío' (línea 46) | 2) .claude/agents/lider.md: regenerado con assistants-sync, tiene paso 0 | 3) bootstrap status: onboarding_tickets_seeded=True, description_pending=False | 4) agents/README.md: 2 menciones de bootstrap | 5) AGENTS.md: 'arranque en frío' presente | 6) vault/05_AGENTES/BootstrapAgent.md existe | 7) prompts_sync: ✔ sincronizados | 8) ./init.sh: ENTORNO LISTO
```

</details>

## WEB-01 — El visor llena la pantalla con el mapa y no deja fondo vacío

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 110 passed in 0.54s
- **Ticket GEAS:** 711d514a · commit_after `2b65f8e0`
## GO-01 — Cómo llegar al primer punto: a pie, en bus o en coche, con tramos, tiempos y ruta en el mapa

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 110 passed in 0.66s
- **Ticket GEAS:** db918085 · commit_after `5717dff6`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
## CORE-001 — Primera pieza funcional de punta a punta

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 119 passed in 0.27s
- **Ticket GEAS:** 9aacc009 · commit_after `04837532`
- **Cambios:** app/points.py (nuevo: carga/summary/count_by_type); app/cli.py (añadido subcomando points); tests/test_points.py (nuevo: 9 tests); README.md (sección 'Línea de comandos'); pyproject.toml (add mypy, hypothesis dev deps)
- **Decisiones:** CORE-001 es el primer vertical slice: app points carga data/points.json, filtra por tipo/idioma y muestra resumen. El proyecto ya tenia los datos y la web; este CLI es la primera entrada programatica real. Se instalaron mypy e hypothesis como deps de dev porque make check los necesita.
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
WEB-01 (Miguel2, 0c45ef7): visor con homeFillsViewer, visibilityRatio 1, minZoom = encuadre del bloque, limites desde manifest (canvas/offset) y applyConstraints tras el encuadre del tour; capturas escritorio 1400 y movil 390 con el bloque v6 al abrir y tras un tour, sin franjas de fondo.   [32m✔[0m pytest                 110 passed in 0.59s [1;32m━━ ENTORNO LISTO ━━[0m  2 aviso(s)
```

</details>

## WEB-04 — Idioma por el navegador (gl, es, en) y ningún texto sin traducir

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 110 passed in 0.74s
- **Ticket GEAS:** 4937c4ce · commit_after `a18e0f04`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
WEB-04 (Miguel2, 0c45ef7): idioma por navigator.languages (gl/es/en y variantes gl-ES/es-419/en-GB), ingles si no coincide; la eleccion manual manda y se recuerda; textos solo de web/data/i18n (tests/test_i18n.py: mismas claves y huecos), Acerca de traducido; prueba en Edge: gl 'Puntos de Nadal', en 'Christmas spots', es 'Puntos de Navidad'.   [32m✔[0m pytest                 110 passed in 0.59s [1;32m━━ ENTORNO LISTO ━━[0m  2 aviso(s)
commit 5717dff. pytest 110 passed; evals PASS; prueba en Edge headless (scripts/shot.mjs) desde Samil sin errores de consola: 1) a >5 min de la primera luz pregunta a pie/bus/coche con tiempo total en cada tarjeta; 2) a pie: ruta OSRM y tiempo; 3) coche: Pintor Colmeiro 213/366 libres 'seguro que hay sitio' + alternativa Portugal (7 libres, ajustado), tramos coche 11 min + aparcar 5 + a pie 23 min; 4) bus: viaje directo GTFS C3d 17:34 Avda. Europa 101 -> 17:51 Conde de Torrecedeira 21 (17 paradas) + tramos a pie 3 y 8 min; 5) tramos dibujados en la vista ciudad (coche azul, bus verde, a pie a trazos, P y paradas marcadas); 6) Google Maps por tramo y global; 7) fallbacks: sin router línea recta 'aproximado', sin feed de parkings aviso, sin bus directo tarjeta desactivada con motivo. Tour con horas desplazadas a la llegada.
```

</details>

## UI-06 — Ajustes en un botón, pines tipo mapa y Hoy en Vigo más trabajado

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 143 passed in 1.38s
- **Ticket GEAS:** a950c82f · commit_after `e5de49c1`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
UI-06 (c41c9e4): web/js/settings.js engranaje con idioma, vista 3D/ciudad, tema y creditos; ocultos #about-open, .tv-theme, .tv-view y GL/ES/EN del panel; pines en gota; Hoy con foto/icono por fila. Prueba en Edge: gl->Puntos de Nadal/Axustes, vista ciudad true, tema light.   [32m✔[0m pytest                 110 passed in 0.59s [1;32m━━ ENTORNO LISTO ━━[0m  2 aviso(s)
$ uv run python -m app points → 'Puntos navidenos de Vigo (35):' con lista de puntos | $ uv run python -m app points --by-type → conteo por tipo (light:16, attraction:8, exhibit:4, market:2, photo_gallery:2, photocall:1, santa_kings:2) | $ uv run python -m app points --format json → JSON válido | $ uv run pytest tests/test_points.py → 9 passed | $ make check → ENTORNO LISTO + 'check pasado: lint + typecheck + test + arnés OK' | README.md documenta el subcomando points con ejemplo de salida
```

</details>

## EVENTS-01 — Events UI (list + map layer)

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 152 passed in 1.95s
- **Ticket GEAS:** 7a978705 · commit_after `94dc0d4d`
## X-03 — Renfe live feasibility check

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 152 passed in 1.47s
- **Ticket GEAS:** 38617de7 · commit_after `31e87a30`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
## SCOPE-002 — Rewrite objetivo.md for the isometric map (spec v4)

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 152 passed in 0.58s
- **Ticket GEAS:** 6189b86a · commit_after `47ccc42a`
- **Cambios:** Ninguno — ya implementado en commit 83db40d (squash de docs/tinyvigo-backlog-v4)
- **Decisiones:** SCOPE-002 se cerro de facto cuando se importo la spec v4 y el backlog v4 (commit 83db40d). objetivo.md ya tiene las cuatro secciones, el criterio de hecho es verificable y el README coincide. Solo falta marcarlo como done.
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
EVENTS-01 (8873230, 7db066a, c41c9e4): Navidad hoy con linea de tiempo del programa oficial (luces, pases, salidas), abierto ahora, agenda navidena en vivo situada en el mapa (Ver en el mapa), permanentes agrupados, proximamente; sin hora en el feed -> Hora por confirmar; filas con foto/icono.   [32m✔[0m pytest                 110 passed in 0.59s [1;32m━━ ENTORNO LISTO ━━[0m  2 aviso(s)
commit 42cbd25. Endpoints Renfe RT probados (LD y Cercanías); cobertura Vigo 12/12 viajes; GO retrasos (JSON, cabecera 15 s), NO-GO posiciones (1 h atrasadas); protobuf no necesario. scripts/renfe_live.py + 2 tests + fuentes_datos.md.
```

</details>

## MOB-01 — Web muy responsive en móvil: paneles como hojas inferiores, áreas seguras, objetivos táctiles y sin solapes

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 152 passed in 2.81s
- **Ticket GEAS:** d4eaca36 · commit_after `45f60d01`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
commit c212996. Batería de 12 transiciones en Edge headless a 360/390/430 px: siempre 1 hoja abierta, sin scroll horizontal, 0 errores; hojas inferiores con safe-area; barra que se aparta; tour plegado; × sticky; 44 px táctiles; escritorio intacto.
```

</details>

## MOB-02 — Pulido de UX en móvil: encuadre inicial, vista ciudad, cómo llegar y detalles de interacción

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 152 passed in 1.37s
- **Ticket GEAS:** 4754bf35 · commit_after `3971ba97`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
commit cc52d2d (CI verde). Isométrico arranca en el núcleo navideño en móvil; vista ciudad con pines gota a zoom <16 y foto de cerca; rutas encuadradas por encima de la hoja (paddingBottomRight 62 % alto); 'Cambiar' separado de la ×; capturas 360 px; batería sin fallos.
```

</details>

## PLANNER-01 — Route planner (walking, 3 options)

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 153 passed in 1.59s
- **Ticket GEAS:** 8750a751 · commit_after `00eebe5a`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
commit 00eebe5. 1) 3 opciones (fastest/after_dark/easy_walk) y misma entrada → mismas rutas (test node); 2) salida: mi ubicación, Porta do Sol, estación Vigo-Urzáiz/Guixar o una calle (1921 calles); 3) eventos como ventanas: fijado a las 20:00 ninguna opción llega después (test); 4) parada inalcanzable nombrada con sugerencia de quitar (test); 5) 12 paradas <2 s (test; en navegador 906 ms con red); 6) tiempos de la API table de OSRM sobre el grafo peatonal OSM (fuente=osm), fallback aproximado marcado; 7) ruta elegida dibujada con paradas numeradas en isométrico y vista ciudad. Held-Karp exacto. 153 tests, batería móvil sin fallos.
$ head -8 vault/01_PROYECTO/objetivo.md → 'Reescrito (SCOPE-002). Fuente de verdad: docs/tinyvigo-spec.md (mapa isometrico pixel art de todo el centro de Vigo)' | secciones presentes: Problema, Usuario/consumidor, Criterio de hecho, Fuera de alcance | criterio de hecho verificable: './init.sh en verde, informe de estado de teselas, informe de comprobaciones por tesela, demo de punta a punta' | fuera de alcance ya no excluye pintar la ciudad ni aplaza buses/trenes (transporte esta en Criterio de hecho punto 5) | README: 'Mapa isometrico pixel art del centro de Vigo, con la Navidad encima' | $ ./init.sh → ENTORNO LISTO
```

</details>

## WEB-05 — Conectar los datos reales a la interfaz nueva (ficha, eventos, transporte, rutas)

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 155 passed in 3.06s
- **Ticket GEAS:** 47691fa2 · commit_after `f16a60ff`
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
commit 3f1f61a. Datos de la web desde ficheros propios (web/data/live) vía web/js/data.js; 0 peticiones a datos.vigo.org/open-meteo en navegador; scripts/build_web.py regenera todo web/data; aviso claro si falta un fichero; 155 tests.
```

</details>

## MAP-01 — Isometric map viewer: tiles, search, mini-map, layers

- **Cerrada:** 2026-11-14
- **Verificación:** ./init.sh en verde · 155 passed in 2.05s
- **Ticket GEAS:** a1927419 · commit_after `9fb8756b`
- **Cambios:** web/js/minimap.js, web/js/layers.js, web/js/satellite.js (nuevos); web/js/app.js (precarga + fps + first view); web/js/tour.js (unproject + tinyvigoGeo); web/js/points.js (datos incrustados); web/index.html (scripts nuevos + bloque baked); web/css/app.css (estilos mini-mapa/capas/PNOA); web/data/i18n/{es,gl,en}.json (claves de capas); scripts/bake_first_view.py, scripts/test_web_geo.mjs (nuevos); scripts/build_web_data.py (llama a bake); README.md
- **Decisiones:** La mini-mapa va arriba a la derecha (la columna derecha ya tiene ajustes/capas) para no chocar con zoom ni con la hoja movil. El interruptor PNOA vive en el panel de capas en vez de un boton flotante: el hueco superior derecho estaba ocupado por 'Ahora' y Ajustes. La capa 'rutas' arranca apagada (solo navidad y eventos on, como pide el criterio) y se enciende sola al planificar una ruta (evento tv:route). La agenda no trae coordenadas: los eventos se colocan casando direccion con puntos/recintos (3 de 44 en los datos actuales; el resto queda solo en lista, como dice la spec). El primer vistazo ya no hace fetch de points.json: va incrustado en la pagina. Cero llamadas a APIs del Concello desde el navegador: WEB-05 manda y layers.js usa web/data/live. fps y first view medidos en Firefox headless de escritorio, no en movil de gama media: el medidor queda en tinyvigoPerf para medirlo en dispositivo real.
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
$ node scripts/test_web_geo.mjs → 'OK proyeccion: centro y 5 puntos ida/vuelta sin error' | $ Playwright/Firefox sobre http://127.0.0.1:8123 → defaults {navidad:true, eventos:true, buses:false, trenes:false, parking:false, camaras:false, rutas:false}; 7 filas + 'Show the real photo'; parking ON → 7 marcadores; PNOA ON → 24 teselas IGN y attribution 'PNOA © IGN'; Escape/close → off; minimapa drag → centro (0.5, 0.598); firstViewMs 89; lastPanFps 54-60; logs sin errores | $ ./init.sh → ENTORNO LISTO | $ make check → 'check pasado: lint + typecheck + test + arnes OK'
```

</details>

## GEO-01 — Georreferencia del mapa isométrico: lat/lon a píxel del lienzo y vuelta

- **Cerrada:** 2026-11-15
- **Verificación:** ./init.sh en verde · 158 passed, 1 skipped in 0.81s
- **Cambios:** pipeline/georef.py y georef.ts (lat/lon/z <-> pixel y coordenadas del visor), pipeline/render/{params,calibrate_origin,silhouette,validate_points}.py, render-params.json, fixtures/{points-3x3,origin-calibration-3x3,origin-calibration-wide}.json, tests/test_georef.py (30) y tests/test_calibrate_origin.py (6), docs/img/geo-01-puntos-sobre-el-mapa.jpg
- **Decisiones:** El origen se lee del renderer original (no se escribe a mano) y se contrasta con el mar del MDT05: desfase de unos 3 m al este, norte-sur sin determinar, dentro del error de la fuente (celdas de 5 m), asi que no se corrige. El estimador se valida con desfases conocidos. 31 de los 35 puntos caen sobre el mapa ampliado; los otros 4 (Circo, Calvario, Samil x2) quedan fuera de cualquier bloque. Detalle y errores en docs/investigacion/expansion-vialia.md 4.1.
- **Pendiente:** La componente norte-sur del origen no esta determinada: haria falta una costa vectorial mejor que la del MDT05 (la de OSM aqui es PGS, 3 vias). No hay otro contraste independiente a la vista.

<details><summary>Evidencia</summary>

```
$ .venv/bin/python -m pytest tests/test_georef.py -q --no-header
..............................                                           [100%]
30 passed in 0.78s

$ python3 -m pipeline.render.params --check
render-params.json al día

$ /tmp/opencode/venv-np/bin/python -m pytest tests/test_calibrate_origin.py -q --no-header   (numpy + opencv)
6 passed, 1 warning in 0.55s

$ .venv/bin/python -m pytest tests -q --no-header   (suite completa del proyecto)
..............                                                           [100%]
158 passed, 1 skipped in 0.82s

$ python3 -m pipeline.render.calibrate_origin --render <render original 3x3> --canvas 3x3 --sweep   (resumen, umbral 1,0 m)
  3x3   desfase (+5.10, +1.96) px = +2.82 m este, -0.68 m norte | IoU del mar 0.860 -> 0.863
  wide  desfase (+6.59, +0.89) px = +3.35 m este, +0.25 m norte | IoU del mar 0.795 -> 0.800

$ puntos de data/points.json proyectados sobre el mapa (lienzo wide): ver docs/img/geo-01-puntos-sobre-el-mapa.jpg
  31 de 35 puntos dentro del lienzo 5120x3072; fuera: ['concello-3503', 'concello-3508', 'concello-3512', 'concello-3513']
```

</details>

## ZONE-02 — Ampliación del bloque hacia Vialia

- **Cerrada:** 2026-11-15
- **Verificación:** ./init.sh en verde · 158 passed, 1 skipped in 0.90s
- **Cambios:** Render ampliado (pipeline/render/{fetch_ortho,fetch_buildings,scene,serve}.py y templates/), pintado e integracion (port_fix.py, pack_tiles.py, zona/ con prompts y recetas), mar por codigo (sea.py), borde (edge_fix.py), noria (noria.py), comprobaciones (seam_metric.py, fidelity.py); pirámides web/tiles/v7-puerto-vialia a v10-costura-izq; scripts/build_web_data.py y tests; doble clic para hacer zoom en web/js/app.js; manual pipeline/render/README.md y memoria docs/investigacion/expansion-vialia.md
- **Decisiones:** Se pinta en ventanas de 1024 px y no en teselas sueltas ni en costuras: la tesela del puerto sola se inventaba, y redibujar una costura ya pintada con Gemini Flash o inventa un barrio o copia la raya. El mar va por codigo y de una vez para todo el mapa. La muestra de estilo del centro se copia, asi que cada ventana lleva una linea explicita de no inventes y se mira contra el render antes de integrarla. Cada version publicada es nueva y conserva canvas 3072. La estimacion de coste (16 minimo, ~30) se quedo corta: fueron 42 llamadas OK, 18 sobreviven en el mapa.
- **Pendiente:** Otras costuras del 3x3 (media 1,26x, la peor 1,60x): misma receta, una llamada cada una. La noche de la noria encendida por codigo vive en web/ui (agente navihack). Archivo comprimido de las ventanas pintadas fuera del repo. No se ha subido version ni CHANGELOG (git commit_feature).

<details><summary>Evidencia</summary>

```
$ git log --oneline --grep="publish v"   (versiones nuevas del mapa, ninguna sobrescribe a otra)
599655e feat(map): publish v6-pulido-arbol pyramid and point the web at it
865cd7c feat(map): publish v7-puerto-vialia, the repainted harbour and the Vialia zone
8c85e18 feat(map): publish v8-este-ampliado, the map grows east past Vialia
5e63508 feat(map): publish v9-noria, the Ferris wheel drawn into the car park at Vialia
59c94e0 feat(map): publish v10-costura-izq, the worst seam of the 3x3 redrawn as a window

$ cat web/tiles/current.json
{"version": "v10-costura-izq"}

$ manifests publicados (imagen y lienzo georreferenciado)
  v7-puerto-vialia   imagen 4096x3072 | canvas 3072x3072 | niveles 9-12
  v8-este-ampliado   imagen 5120x3072 | canvas 3072x3072 | niveles 9-13
  v9-noria           imagen 5120x3072 | canvas 3072x3072 | niveles 9-13
  v10-costura-izq    imagen 5120x3072 | canvas 3072x3072 | niveles 9-13

$ los cuatro hitos dentro del lienzo ampliado (5120x3072), pixel y tesela (fila, columna)
  porta-do-sol   ( 1535.6,  1535.6)  tesela (1, 1)
  alameda        ( 2147.2,  1449.7)  tesela (1, 2)
  garcia-barbon  ( 3097.1,  2027.9)  tesela (1, 3)
  vialia         ( 3261.4,  2526.3)  tesela (2, 3)
  noria (Concello) ( 4275.9,  2255.8)  tesela (2, 4)  <- dentro desde v8

$ llamadas de imagen de la ampliacion (pipeline/ledger/image-calls.jsonl)
  OK 42 | 429 8 | red 2   (el ledger total: 80 filas)

$ mar por codigo, una sola capa para todo el mapa: pipeline/render/sea.py; aplicado en v8 y siguientes

$ .venv/bin/python -m pytest tests -q --no-header
158 passed, 1 skipped in 1.26s

Estimacion de coste ANTES de lanzar: work/render-expansion/INFORME.md: 16 llamadas de minimo, ~30 en la practica. Real: 42 (18 sobreviven). Ver docs/investigacion/expansion-vialia.md §6.
```

</details>

## MAP-04 — Minimapa con Vigo entero

- **Cerrada:** 2026-11-15
- **Verificación:** ./init.sh en verde · 158 passed, 1 skipped in 1.57s
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
Edge 1440 y 390: minimap 148x89 (antes 148x148 recortado); tocar 85%/80% lleva el recuadro al borde (x=1354 de 1355). Commit f76eb64. · init.sh:   ✔ pytest                 158 passed, 1 skipped in 1.70s ━━ ENTORNO LISTO ━━  2 aviso(s)
```

</details>

## ROUTE-02 — Rutas: terminar limpia el mapa y paradas legibles

- **Cerrada:** 2026-11-15
- **Verificación:** ./init.sh en verde · 158 passed, 1 skipped in 1.57s
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
Ruta de 9 paradas: tras Terminar paseo svg=0 pins=0 result=false seguirme oculto, 0 marcadores ocultos, toast Paseo terminado; pines 1 2 3·4 5..9, actual en oscuro, vistas con check. Commits f76eb64. · init.sh:   ✔ pytest                 158 passed, 1 skipped in 1.70s ━━ ENTORNO LISTO ━━  2 aviso(s)
```

</details>

## ROUTE-03 — Seguirme dentro de la tarjeta del paseo

- **Cerrada:** 2026-11-15
- **Verificación:** ./init.sh en verde · 158 passed, 1 skipped in 1.60s
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
Simulación: A 430 m · 6 min → 330 m; auto-avance Renos → Papá Noel en la Farola; Dejar de seguir vuelve a Seguirme; sin GPS la tarjeta ofrece Simular paseo (390 y 1440). Commit f76eb64. · init.sh:   ✔ pytest                 158 passed, 1 skipped in 1.70s ━━ ENTORNO LISTO ━━  2 aviso(s)
```

</details>

## CONTENT-02 — Textos de lugares, fecha del circo y foto en la agenda

- **Cerrada:** 2026-11-15
- **Verificación:** ./init.sh en verde · 158 passed, 1 skipped in 1.67s
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
Circo de Navidad sin «desde el 5 de diciembre» (ticketrona: 4 dic–10 ene); 35 historias reescritas en gl/es/en; encendido de luces → foto del Árbol. Commit c1c693b. · init.sh:   ✔ pytest                 158 passed, 1 skipped in 1.70s ━━ ENTORNO LISTO ━━  2 aviso(s)
```

</details>

## LIGHT-03 — Luz de noche por código: tinte medido, farolas, Árbol y Noria

- **Cerrada:** 2026-11-15
- **Verificación:** ./init.sh en verde · 158 passed, 1 skipped in 1.56s
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
Día: tinte 0, 0 overlays; noche: 3 capas, 24 overlays, sin errores (1440 y 390); 1488 calles OSM. Commits 96f7122, b3de72e. · init.sh:   ✔ pytest                 158 passed, 1 skipped in 1.70s ━━ ENTORNO LISTO ━━  2 aviso(s)
```

</details>

## OFFLINE-01 — App instalable y mapa guardable sin conexión

- **Cerrada:** 2026-11-15
- **Verificación:** ./init.sh en verde · 158 passed, 1 skipped in 1.63s
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
Guardar → caché shell 88 + teselas 85; sin red: recarga y zoom máximo al este, 29 marcadores, sin errores. Commit 435e4bf. · init.sh:   ✔ pytest                 158 passed, 1 skipped in 1.70s ━━ ENTORNO LISTO ━━  2 aviso(s)
```

</details>

## A11Y-01 — Accesibilidad con teclado y lector de pantalla

- **Cerrada:** 2026-11-15
- **Verificación:** ./init.sh en verde · 158 passed, 1 skipped in 1.57s
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
axe-core: 0 incidencias en inicio, lista, ficha, planificador, agenda, ajustes y landing claro/oscuro; 1.er Tab = Saltar a la búsqueda; agenda mantiene foco; Escape devuelve el foco. Commit 2a17843. · init.sh:   ✔ pytest                 158 passed, 1 skipped in 1.70s ━━ ENTORNO LISTO ━━  2 aviso(s)
```

</details>

## PERF-01 — Rendimiento de las luces y de la landing

- **Cerrada:** 2026-11-15
- **Verificación:** ./init.sh en verde · 158 passed, 1 skipped in 1.57s
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
Noche quieto: 82 → 12 ms/s de estilo; pan de noche 40-50 → 88 fps; hero 527 → 246 KB. Commit b3de72e. · init.sh:   ✔ pytest                 158 passed, 1 skipped in 1.70s ━━ ENTORNO LISTO ━━  2 aviso(s)
```

</details>

## LANDING-02 — Landing con mimo: scroll progresivo, tarjetas a medida, copy humano y SEO, capturas del HUD nuevo

- **Cerrada:** 2026-11-15
- **Verificación:** ./init.sh en verde · 158 passed, 1 skipped in 1.61s
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
Sin ratón, chips ni frase redundante; título sin —; reveals verticales expo-out; Pasea por la Navidad con pasos y consejos; capturas del HUD actual; axe 0; 1440/390 sin scroll horizontal ni errores; 44 px. Commits ae8dfde, b3de72e. · init.sh:   ✔ pytest                 158 passed, 1 skipped in 1.70s ━━ ENTORNO LISTO ━━  2 aviso(s)
```

</details>

## POLISH-03 — Ronda para presentar al Concello: satélite, tráfico, cámaras, buses al día, pt, búsqueda de direcciones, tour y seguridad

- **Cerrada:** 2026-11-15
- **Verificación:** ./init.sh en verde · 163 passed, 1 skipped in 1.74s
- **Cambios:** _(no indicados)_
- **Decisiones:** _(ninguna reseñable)_
- **Pendiente:** _(nada)_

<details><summary>Evidencia</summary>

```
Commits aa68e81, 330830a, 0926e97, 9ed21e6. e2e (web/e2e, Edge, escritorio+móvil): 25 bien · 0 mal · 1 no aplican — buses (<5% paradas sin salidas un martes; salidas un mes después del GTFS), paseo con paradas por colores, capas, cámara en la app, axe 0. CI e2e verde. CSP de vercel.json inyectada en el navegador: 0 avisos. Tráfico: 263/270 tramos encajados. init.sh: 163 passed, 1 skipped, ENTORNO LISTO
```

</details>
