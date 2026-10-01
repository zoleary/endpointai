#!/usr/bin/env bash
# Start the Endpoint AI Security demo on http://localhost:8000
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "[run.sh] creating .venv"
  python3 -m venv .venv
fi
.venv/bin/pip install -q -r requirements.txt

if [ ! -f .env ]; then
  echo "[run.sh] creating .env from .env.example (edit it to add your API key)"
  cp .env.example .env
fi

echo "[run.sh] starting on http://localhost:${PORT:-8000}"
exec .venv/bin/uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
