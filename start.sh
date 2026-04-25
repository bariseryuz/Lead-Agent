#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"

if [[ ! -d "$FRONTEND_DIR" ]]; then
  echo "frontend/ directory not found at: $FRONTEND_DIR" >&2
  exit 1
fi

cd "$FRONTEND_DIR"

# Railway (and some builders) set npm "production" config globally, which makes npm warn.
# We need devDependencies for the Vite/TS build, so force production=false for this install.
export NPM_CONFIG_PRODUCTION=false

if [[ -f package-lock.json ]]; then
  npm ci --include=dev
else
  npm install --include=dev
fi

if [[ ! -d dist ]]; then
  npm run build
fi

PORT="${PORT:-3000}"
npm run preview -- --host 0.0.0.0 --port "$PORT"

