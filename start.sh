#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"
BACKEND_DIR="${ROOT_DIR}/backend"

if [[ ! -d "$FRONTEND_DIR" ]]; then
  echo "frontend/ directory not found at: $FRONTEND_DIR" >&2
  exit 1
fi

if [[ ! -d "$BACKEND_DIR" ]]; then
  echo "backend/ directory not found at: $BACKEND_DIR" >&2
  exit 1
fi

python -m pip install --upgrade pip
python -m pip install -r "${BACKEND_DIR}/requirements.txt"

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

# ---- Start backend (serves API + frontend dist) ----
cd "$ROOT_DIR"

# Ensure `import app...` works when running uvicorn from repo root
export PYTHONPATH="${BACKEND_DIR}"

PORT="${PORT:-8000}"
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"

