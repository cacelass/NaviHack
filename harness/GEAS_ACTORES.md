# Añadir actores a GEAS

Un **actor** es quien reclama y ejecuta tickets: una **persona** (`user`) o un
**agente** (`agent`, un dispositivo/LLM). Cada actor tiene un **rol** que
define qué puede hacer. Sin rol, su conjunto de permisos está vacío y toda
llamada responde `FORBIDDEN`.

La API de GEAS **lista** actores (`list_actors`) pero **no los crea**: para
dar de alta un actor hay que escribir en la base de datos del servidor, y el
servidor SQLite es de un solo escritor. Este documento es el procedimiento,
para que un LLM lo ejecute sin romper nada.

## Quién escribe qué

| Pieza | Dónde vive | Quién la escribe |
|-------|-----------|------------------|
| El actor (user/agent) + su rol | base de datos de GEAS | `geas user/agent create`, en el host del servidor |
| El token | `~/.local/share/geas/tokens.env` | tú, o `scripts/geas_add_actor.sh` |
| El mapeo token → actor | memoria del proxy, al arrancar | el proxy, leyendo `tokens.env` |
| La URL y el token del arnés | `.env` del repo (`GEAS_URL`, `GEAS_TOKEN`) | `scripts/geas_setup.sh`, o tú |

## Roles disponibles

| Rol | Para qué | Permisos clave |
|-----|----------|----------------|
| `agent` | dispositivos/LLM que ejecutan tickets | `ticket:start/complete/block`, `resource:lock`, `user:read` |
| `developer` | personas que programan, sin administrar | `ticket:create/update`, `git:push` |
| `manager` | quien crea y asigna tickets | `ticket:assign`, `user:manage`, `audit:read` |
| `admin` | todo | todos los permisos |
| `service_account` | solo lectura | `ticket:read`, `audit:read` |

> **El error más habitual:** `developer` **no** tiene `ticket:start`. Para
> reclamar tickets hace falta rol `agent` (o `admin`). Un LLM con rol
> `developer` verá los tickets pero no podrá empezarlos.

## Procedimiento manual (host del servidor)

### 1. Localiza la organización y el rol

El `org_id` completo está en `harness/geas.json` (tras `geas_setup.sh`) o en
la respuesta de `list_actors` / `get_organization`. `geas org list` solo
imprime los 8 primeros caracteres: **no sirve** para esto.

```bash
# roles de la organización (imprime id[:8] + nombre)
geas role list <org_id>

# si tienes a mano geas_admin.py (vive en el repo de edgebet), da el UUID:
python3 geas_admin.py ~/.local/share/geas/geas.db lookup role agent <org_id>

# alternativa sin abrir la BD: copia el role_id de un actor que ya existe
curl -s -X POST http://<IP>:8790/api/tools/list_actors \
  -H "Authorization: Bearer $GEAS_TOKEN" -H "Content-Type: application/json" -d '{}'
```

### 2. Para el servidor

`geas user/agent create` se niega a escribir si el servidor está vivo (dos
escritores sobre el mismo SQLite se pisan, GEAS-005/006):

```bash
systemctl --user stop geas-server
```

### 3. Crea el actor

```bash
# agente (dispositivo/LLM)
geas agent create <org_id> <nombre> <provider> <model> "" <role_id>

# persona
geas user create <org_id> <nombre> [email] "" <role_id>
```

El `""` es el `department_id` (vacío si no usas departamentos). El último
argumento es el `role_id` **completo**.

### 4. Levanta el servidor

```bash
systemctl --user start geas-server
```

### 5. Averigua el UUID completo del actor

`geas agent list <org_id>` solo imprime 8 caracteres. Para el token hace falta
el UUID entero:

```bash
# con un token que ya funcione:
curl -s -X POST http://<IP>:8790/api/tools/list_actors \
  -H "Authorization: Bearer $GEAS_TOKEN" -H "Content-Type: application/json" -d '{}'
```

### 6. Emite el token y regístralo

El proxy lee `tokens.env` con un formato de **dos líneas**: el token y, justo
debajo, un comentario `# <nombre> = <UUID>`. El valor del comentario **debe ser
el UUID**, no el nombre: el proxy lo manda tal cual como `X-Geas-Actor`.

```bash
umask 077
printf 'GEAS_TOKEN_ANA=%s\n# Ana = %s\n' \
  "$(head -c 32 /dev/urandom | base64 | tr -d '/+=' | head -c 32)" \
  "<uuid-del-actor>" >> ~/.local/share/geas/tokens.env
```

### 7. Reinicia el proxy

El proxy carga `tokens.env` al arrancar; un token nuevo no existe hasta que lo
reinicia:

```bash
systemctl --user restart geas-proxy
```

### 8. Verifica

```bash
curl -s -X POST http://<IP>:8790/api/tools/list_actors \
  -H "Authorization: Bearer <token-nuevo>" -H "Content-Type: application/json" -d '{}'

# y que puede trabajar:
curl -s -X POST http://<IP>:8790/api/tools/get_available_tasks \
  -H "Authorization: Bearer <token-nuevo>" -H "Content-Type: application/json" -d '{}'
```

## Atajo: el script

`scripts/geas_add_actor.sh` hace los pasos 1–8 en el host del servidor
(resuelve org/rol leyendo la BD, para el servidor, crea el actor, lo levanta,
escribe el token y reinicia el proxy). Es idempotente en el sentido de que se
niega a duplicar: si el actor o el token ya existen, para.

```bash
# persona
./scripts/geas_add_actor.sh --name "Ana" --kind user --role manager \
  --url http://192.168.1.50:8790

# agente
./scripts/geas_add_actor.sh --name "Raspy" --kind agent --provider local \
  --model qwen3-coder --role agent --url http://192.168.1.50:8790

# ver el plan sin tocar nada
./scripts/geas_add_actor.sh --name "Ana" --kind user --dry-run
```

Al terminar imprime `GEAS_URL` y `GEAS_TOKEN` **una sola vez**: pásaselos al
actor y no los commitees.

## Vía rápida para personas (sin parar el servidor)

El servidor expone `POST /api/create-user` (lo usa el panel web). A través del
proxy, con cualquier token válido, crea una persona **en vivo**:

```bash
curl -s -X POST http://<IP>:8790/api/create-user \
  -H "Authorization: Bearer $GEAS_TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Ana","role_id":"<uuid-del-rol>"}'
```

Solo crea `user` (no `agent`), y sin `role_id` el actor nace **sin permisos**.
Para agentes, o para asignar rol con garantías, usa el procedimiento o el
script.

## Errores típicos

| Síntoma | Causa |
|---------|-------|
| `FORBIDDEN ... 'permission': 'ticket:start'` | el actor tiene rol `developer` (sin `ticket:start`); dale `agent` |
| `me hago atrás. Hay un servidor de GEAS con ... abierta` | intentaste `geas user/agent create` con el servidor vivo: páralo primero |
| `401 TOKEN_REQUERIDO` | el proxy no reconoce el token: falta reiniciarlo o el token no está en `tokens.env` |
| `FORBIDDEN` con un token que sí está en `tokens.env` | el comentario del token no es el UUID del actor, o el actor no tiene rol |
| El token no aparece en `list_actors` | al token le falta la línea `# Nombre = UUID` justo debajo |

## Reglas de oro

1. **Un token por actor.** No se comparte, no se reutiliza.
2. **El token nunca va a git.** Vive en `tokens.env` (0600) y en el `.env`
   local del repo, que está ignorado.
3. **El comentario del token es el UUID**, no el nombre.
4. **Reinicia el proxy** después de tocar `tokens.env`.
5. **Parar el servidor** antes de crear actores a mano; el script ya lo hace.
