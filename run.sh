#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

UVICORN_BIN="${UVICORN_BIN:-./venv/bin/uvicorn}"
APP="${APP:-main:app}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
RELOAD="${RELOAD:-1}"

if [[ ! -x "$UVICORN_BIN" ]]; then
  echo "uvicorn not found at: $UVICORN_BIN" >&2
  exit 1
fi

if [[ "$RELOAD" == "1" ]]; then
  exec "$UVICORN_BIN" "$APP" --host "$HOST" --port "$PORT" --reload
fi

exec "$UVICORN_BIN" "$APP" --host "$HOST" --port "$PORT"
