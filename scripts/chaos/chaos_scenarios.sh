#!/usr/bin/env bash
set -euo pipefail

SCENARIO="${1:-}"
NAMESPACE="${NAMESPACE:-learning-platform}"
DURATION_SECONDS="${DURATION_SECONDS:-60}"

usage() {
  echo "Usage: $0 <delete-api-pod|delete-worker-pod|scale-workers-zero|block-api-egress|unblock-api-egress>"
  exit 1
}

delete_random_pod() {
  local selector="$1"
  local pod
  pod="$(kubectl -n "${NAMESPACE}" get pods -l "${selector}" -o jsonpath='{.items[0].metadata.name}')"
  [[ -n "${pod}" ]] || { echo "No pod found for ${selector}" >&2; exit 1; }
  kubectl -n "${NAMESPACE}" delete pod "${pod}"
}

case "${SCENARIO}" in
  delete-api-pod)
    delete_random_pod "app=api"
    ;;
  delete-worker-pod)
    delete_random_pod "app=celery-worker"
    ;;
  scale-workers-zero)
    kubectl -n "${NAMESPACE}" scale deploy/celery-worker --replicas=0
    sleep "${DURATION_SECONDS}"
    kubectl -n "${NAMESPACE}" scale deploy/celery-worker --replicas=2
    ;;
  block-api-egress)
    kubectl -n "${NAMESPACE}" apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: chaos-deny-api-egress
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
    - Egress
  egress: []
EOF
    ;;
  unblock-api-egress)
    kubectl -n "${NAMESPACE}" delete networkpolicy chaos-deny-api-egress --ignore-not-found
    ;;
  *)
    usage
    ;;
esac
