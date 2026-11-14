#!/usr/bin/env bash
# Deploy the NaviHack landing (a Vite React app) to Vercel.
# The demo it links to (demo/) is web/, copied in next to the built landing.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="${VERCEL_PROJECT:-navihack}"
DIST="$(mktemp -d)"
trap 'rm -rf "$DIST"' EXIT

(cd "$ROOT/landing" && npm ci && npm run build)
cp -r "$ROOT/landing/dist/." "$DIST/"
cp -r "$ROOT/web" "$DIST/demo"

cd "$DIST"
npx -y vercel@latest link --yes --project "$PROJECT" >/dev/null
npx -y vercel@latest deploy --prod --yes "$@"
