#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-learning-platform}"
SECRET_NAME="${SECRET_NAME:-learning-platform-secrets}"
DATABASE_KEY="${DATABASE_KEY:-DATABASE_URL}"
NEW_DATABASE_URL="${NEW_DATABASE_URL:-}"
DRY_RUN="${DRY_RUN:-false}"

if [[ -z "${NEW_DATABASE_URL}" ]]; then
  echo "NEW_DATABASE_URL is required" >&2
  exit 1
fi

echo "Preparing database failover cutover in namespace ${NAMESPACE}"

if [[ "${DRY_RUN}" == "true" ]]; then
  echo "kubectl -n ${NAMESPACE} create secret generic ${SECRET_NAME} --from-literal=${DATABASE_KEY}=<redacted> --dry-run=client -o yaml | kubectl apply -f -"
  echo "kubectl -n ${NAMESPACE} rollout restart deploy/api deploy/celery-worker deploy/celery-beat"
  exit 0
fi

kubectl -n "${NAMESPACE}" create secret generic "${SECRET_NAME}" \
  --from-literal="${DATABASE_KEY}=${NEW_DATABASE_URL}" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl -n "${NAMESPACE}" rollout restart deploy/api || true
kubectl -n "${NAMESPACE}" rollout restart deploy/celery-worker || true
kubectl -n "${NAMESPACE}" rollout restart deploy/celery-beat || true
kubectl -n "${NAMESPACE}" rollout status deploy/api --timeout=180s || true

echo "failover cutover applied"
