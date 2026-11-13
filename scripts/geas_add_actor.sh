#!/usr/bin/env bash
# Da de alta un actor (persona o agente) en el GEAS del host del servidor.
#
#   ./scripts/geas_add_actor.sh --name "Ana" --kind user --role manager
#   ./scripts/geas_add_actor.sh --name "Raspy" --kind agent --provider local \
#       --model qwen3-coder --url http://192.168.1.50:8790
#
# Detalles y el procedimiento manual, en harness/GEAS_ACTORES.md.
set -euo pipefail

cd "$(dirname "$0")/.."
exec uv run python scripts/geas_add_actor.py "$@"
