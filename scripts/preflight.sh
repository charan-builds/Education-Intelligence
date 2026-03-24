#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="${ROOT_DIR}/learning-platform-frontend"
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://127.0.0.1:3000}"

pass() {
  printf "[preflight] PASS: %s\n" "$1"
}

warn() {
  printf "[preflight] WARN: %s\n" "$1"
}

fail() {
  printf "[preflight] FAIL: %s\n" "$1" >&2
}

check_cmd() {
  local cmd="$1"
  if command -v "$cmd" >/dev/null 2>&1; then
    pass "command available -> ${cmd}"
  else
    warn "command missing -> ${cmd}"
  fi
}

printf "[preflight] root=%s\n" "$ROOT_DIR"

check_cmd python
check_cmd npm
check_cmd curl
check_cmd jq
check_cmd docker

if [[ -f "${ROOT_DIR}/.env" ]]; then
  pass ".env present"
else
  warn ".env missing (copy from .env.example before running the stack)"
fi

if [[ -f "${FRONTEND_DIR}/.env.local" ]]; then
  pass "frontend .env.local present"
else
  warn "frontend .env.local missing"
fi

if [[ -x "${ROOT_DIR}/venv/bin/pytest" ]]; then
  pass "backend virtualenv pytest available"
else
  warn "backend virtualenv not found or pytest missing"
fi

if [[ -d "${FRONTEND_DIR}/node_modules" ]]; then
  pass "frontend node_modules present"
else
  warn "frontend node_modules missing (run npm install)"
fi

if curl -fsS "${BASE_URL}/health" >/dev/null 2>&1; then
  pass "backend health reachable at ${BASE_URL}/health"
else
  warn "backend not reachable at ${BASE_URL}/health"
fi

if curl -fsS "${FRONTEND_URL}" >/dev/null 2>&1; then
  pass "frontend reachable at ${FRONTEND_URL}"
else
  warn "frontend not reachable at ${FRONTEND_URL}"
fi

if (cd "${FRONTEND_DIR}" && npx playwright --version >/dev/null 2>&1); then
  pass "playwright installed"
else
  warn "playwright not installed in frontend"
fi

PLAYWRIGHT_CACHE_DIR="${HOME}/.cache/ms-playwright"
if [[ -d "${PLAYWRIGHT_CACHE_DIR}" ]] && find "${PLAYWRIGHT_CACHE_DIR}" -maxdepth 1 -type d -name 'chromium-*' | grep -q .; then
  pass "playwright chromium cache present"
else
  warn "playwright chromium not installed"
fi

printf "[preflight] complete\n"
