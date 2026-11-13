#!/usr/bin/env bash
# Deja NavaHack apuntando al GEAS de la hackathon.
#
#   ./scripts/geas_setup.sh 192.168.1.50
#   ./scripts/geas_setup.sh http://192.168.1.50:8790 --token "$GEAS_TOKEN"
#
# El token se busca, por este orden, en --token, GEAS_TOKEN, .env y
# ~/.config/geas/client.env. Nunca se imprime ni se escribe en harness/geas.json.
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "Uso: $0 <IP|host:puerto|url> [opciones de scripts/geas_setup.py]" >&2
  echo "Ejemplo: $0 192.168.1.50" >&2
  exit 2
fi

DESTINO="$1"
shift

cd "$(dirname "$0")/.."
exec uv run python scripts/geas_setup.py --url "$DESTINO" "$@"
