#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
EMAIL="${SMOKE_EMAIL:-smoke_$(date +%s)@example.com}"
PASSWORD="${SMOKE_PASSWORD:-Secret123!}"
ROLE="${SMOKE_ROLE:-student}"
TENANT_ID="${SMOKE_TENANT_ID:-1}"
GOAL_ID="${SMOKE_GOAL_ID:-1}"

log() {
  printf "\n[smoke] %s\n" "$1"
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

need_cmd curl
need_cmd jq

log "Checking API health at ${BASE_URL}"
if ! curl -fsS "${BASE_URL}/" >/dev/null; then
  echo "API is not reachable at ${BASE_URL}. Start backend first." >&2
  exit 1
fi

log "1) Register"
REGISTER_PAYLOAD=$(jq -n \
  --arg email "$EMAIL" \
  --arg password "$PASSWORD" \
  --argjson tenant_id "$TENANT_ID" \
  --arg role "$ROLE" \
  '{email: $email, password: $password, tenant_id: $tenant_id, role: $role}')

REGISTER_RESP=$(curl -fsS -X POST "${BASE_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d "$REGISTER_PAYLOAD")

USER_ID=$(echo "$REGISTER_RESP" | jq -r '.id')
if [[ -z "$USER_ID" || "$USER_ID" == "null" ]]; then
  echo "Register failed: $REGISTER_RESP" >&2
  exit 1
fi
echo "Registered user_id=${USER_ID}, email=${EMAIL}"

log "2) Login"
LOGIN_PAYLOAD=$(jq -n --arg email "$EMAIL" --arg password "$PASSWORD" '{email: $email, password: $password}')
LOGIN_RESP=$(curl -fsS -X POST "${BASE_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d "$LOGIN_PAYLOAD")
TOKEN=$(echo "$LOGIN_RESP" | jq -r '.access_token')
if [[ -z "$TOKEN" || "$TOKEN" == "null" ]]; then
  echo "Login failed: $LOGIN_RESP" >&2
  exit 1
fi
echo "Login successful (token received)"

AUTH_HEADER=( -H "Authorization: Bearer ${TOKEN}" )

log "3) Start diagnostic"
START_PAYLOAD=$(jq -n --argjson goal_id "$GOAL_ID" '{goal_id: $goal_id}')
START_RESP=$(curl -fsS -X POST "${BASE_URL}/diagnostic/start" \
  "${AUTH_HEADER[@]}" \
  -H "Content-Type: application/json" \
  -d "$START_PAYLOAD")
TEST_ID=$(echo "$START_RESP" | jq -r '.id')
if [[ -z "$TEST_ID" || "$TEST_ID" == "null" ]]; then
  echo "Start diagnostic failed: $START_RESP" >&2
  exit 1
fi
echo "Started test_id=${TEST_ID}"

log "4) Submit answers"
SUBMIT_PAYLOAD=$(jq -n \
  --argjson test_id "$TEST_ID" \
  '{
    test_id: $test_id,
    answers: [
      {question_id: 1, user_answer: "A", score: 45.0, time_taken: 5.5},
      {question_id: 2, user_answer: "B", score: 62.0, time_taken: 7.2}
    ]
  }')
SUBMIT_RESP=$(curl -fsS -X POST "${BASE_URL}/diagnostic/submit" \
  "${AUTH_HEADER[@]}" \
  -H "Content-Type: application/json" \
  -d "$SUBMIT_PAYLOAD")
SUBMITTED_ID=$(echo "$SUBMIT_RESP" | jq -r '.id')
if [[ "$SUBMITTED_ID" != "$TEST_ID" ]]; then
  echo "Submit answers failed: $SUBMIT_RESP" >&2
  exit 1
fi
echo "Submitted answers for test_id=${TEST_ID}"

log "5) Generate roadmap"
GENERATE_PAYLOAD=$(jq -n --argjson goal_id "$GOAL_ID" --argjson test_id "$TEST_ID" '{goal_id: $goal_id, test_id: $test_id}')
GENERATE_RESP=$(curl -fsS -X POST "${BASE_URL}/roadmap/generate" \
  "${AUTH_HEADER[@]}" \
  -H "Content-Type: application/json" \
  -d "$GENERATE_PAYLOAD")
ROADMAP_ID=$(echo "$GENERATE_RESP" | jq -r '.id')
if [[ -z "$ROADMAP_ID" || "$ROADMAP_ID" == "null" ]]; then
  echo "Generate roadmap failed: $GENERATE_RESP" >&2
  exit 1
fi
echo "Generated roadmap_id=${ROADMAP_ID}"

log "6) View roadmap"
VIEW_RESP=$(curl -fsS "${BASE_URL}/roadmap/${USER_ID}" "${AUTH_HEADER[@]}")
ITEMS_COUNT=$(echo "$VIEW_RESP" | jq -r '.items | length')
if [[ "$ITEMS_COUNT" == "0" ]]; then
  echo "View roadmap failed/no items: $VIEW_RESP" >&2
  exit 1
fi

echo "Roadmap entries=${ITEMS_COUNT}"

log "Flow completed successfully"
printf "[smoke] register -> login -> start diagnostic -> submit answers -> generate roadmap -> view roadmap: PASS\n"
