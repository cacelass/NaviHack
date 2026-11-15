#!/usr/bin/env bash
# Deploy the NaviVigo landing (a Vite React app) to Vercel.
# The demo it links to (demo/) is web/, copied in next to the built landing.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="${VERCEL_PROJECT:-navivigo}"
DIST="$(mktemp -d)"
trap 'rm -rf "$DIST"' EXIT

(cd "$ROOT/landing" && npm ci && npm run build)
cp -r "$ROOT/landing/dist/." "$DIST/"
cp -r "$ROOT/web" "$DIST/demo"
# las pruebas del navegador (y sus node_modules) no se publican
rm -rf "$DIST/demo/e2e"
# Datos en vivo: los sirve deploy/vercel/api/live.mjs; los ficheros del repo quedan de respaldo.
# Se renombran porque en Vercel un fichero estático gana a la reescritura de vercel.json.
mv "$DIST/demo/data/live" "$DIST/demo/data/live-snapshot"
cp -r "$ROOT/deploy/vercel/." "$DIST/"

cd "$DIST"
npx -y vercel@latest link --yes --project "$PROJECT" >/dev/null
npx -y vercel@latest deploy --prod --yes "$@"
