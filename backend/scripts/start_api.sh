#!/usr/bin/env bash
set -euo pipefail

alembic upgrade head

if [[ "${RUN_SEED_ON_STARTUP:-false}" == "true" ]]; then
  python seed.py
fi

PORT="${PORT:-8000}"
API_WORKERS="${API_WORKERS:-4}"
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-120}"
GUNICORN_GRACEFUL_TIMEOUT="${GUNICORN_GRACEFUL_TIMEOUT:-30}"
GUNICORN_KEEPALIVE="${GUNICORN_KEEPALIVE:-15}"

exec gunicorn \
  -k uvicorn.workers.UvicornWorker \
  -w "${API_WORKERS}" \
  -b "0.0.0.0:${PORT}" \
  --timeout "${GUNICORN_TIMEOUT}" \
  --graceful-timeout "${GUNICORN_GRACEFUL_TIMEOUT}" \
  --keep-alive "${GUNICORN_KEEPALIVE}" \
  app.main:app
