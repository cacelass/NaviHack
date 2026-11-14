#!/usr/bin/env bash
# Deploy the NaviHack landing to Vercel.
# The landing lives in landing/; the demo it links to (demo/) is web/, copied in at deploy time.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="${VERCEL_PROJECT:-navihack}"
DIST="$(mktemp -d)"
trap 'rm -rf "$DIST"' EXIT

cp -r "$ROOT/landing/." "$DIST/"
rm -f "$DIST/deploy.sh" "$DIST/README.md"
cp -r "$ROOT/web" "$DIST/demo"

cd "$DIST"
npx -y vercel@latest link --yes --project "$PROJECT" >/dev/null
npx -y vercel@latest deploy --prod --yes "$@"
