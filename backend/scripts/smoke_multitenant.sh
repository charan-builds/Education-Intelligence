#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

log() {
  printf "\n[multi-tenant-smoke] %s\n" "$1"
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  local label="$3"

  if ! echo "$haystack" | jq -e --arg needle "$needle" 'any(.[]?; .name == $needle)' >/dev/null 2>&1; then
    echo "Expected ${label} to include '${needle}', but it did not." >&2
    echo "$haystack" >&2
    exit 1
  fi
}

login() {
  local email="$1"
  local password="$2"

  local payload
  payload=$(jq -n --arg email "$email" --arg password "$password" '{email: $email, password: $password}')

  curl -fsS -X POST "${BASE_URL}/auth/login" \
    -H "Content-Type: application/json" \
    -d "$payload" | jq -r '.access_token'
}

verify_tenant() {
  local tenant_label="$1"
  local email="$2"
  local password="$3"
  local expected_goal="$4"
  local expected_topic_a="$5"
  local expected_topic_b="$6"

  log "Logging in as ${tenant_label} admin (${email})"
  local token
  token=$(login "$email" "$password")
  if [[ -z "$token" || "$token" == "null" ]]; then
    echo "Failed to obtain token for ${email}" >&2
    exit 1
  fi

  local auth_header
  auth_header=( -H "Authorization: Bearer ${token}" )

  log "Checking ${tenant_label} goals"
  local goals
  goals=$(curl -fsS "${BASE_URL}/goals" "${auth_header[@]}")
  assert_contains "$goals" "$expected_goal" "${tenant_label} goals"

  log "Checking ${tenant_label} topics"
  local topics
  topics=$(curl -fsS "${BASE_URL}/topics" "${auth_header[@]}")
  assert_contains "$topics" "$expected_topic_a" "${tenant_label} topics"
  assert_contains "$topics" "$expected_topic_b" "${tenant_label} topics"

  log "Checking ${tenant_label} admin dashboard"
  local dashboard
  dashboard=$(curl -fsS "${BASE_URL}/dashboard/admin" "${auth_header[@]}")
  local total_users
  total_users=$(echo "$dashboard" | jq -r '.total_users')
  if [[ -z "$total_users" || "$total_users" == "null" ]]; then
    echo "Admin dashboard did not return total_users for ${tenant_label}" >&2
    echo "$dashboard" >&2
    exit 1
  fi

  echo "[multi-tenant-smoke] ${tenant_label}: PASS (goal=${expected_goal}, topics=${expected_topic_a}/${expected_topic_b}, total_users=${total_users})"
}

need_cmd curl
need_cmd jq

log "Checking API health at ${BASE_URL}"
curl -fsS "${BASE_URL}/health" >/dev/null

verify_tenant \
  "Demo University" \
  "admin@demo.learnova.ai" \
  "admin123" \
  "AI/ML Engineer" \
  "Linear Algebra" \
  "Machine Learning"

verify_tenant \
  "Northwind Academy" \
  "admin@northwind.learnova.ai" \
  "admin123" \
  "STEM Foundations" \
  "Reading Comprehension" \
  "Basic Algebra"

verify_tenant \
  "Acme Learning Co" \
  "admin@acme.learnova.ai" \
  "admin123" \
  "Product Analyst" \
  "Product Analytics" \
  "Experiment Design"

log "All seeded tenants verified successfully"
