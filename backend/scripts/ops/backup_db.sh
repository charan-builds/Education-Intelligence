#!/usr/bin/env bash
set -euo pipefail

TS="$(date -u +%F-%H%M%S)"
BACKUP_FORMAT="${BACKUP_FORMAT:-custom}"
BACKUP_PREFIX="${BACKUP_PREFIX:-db-backups}"
BACKUP_BUCKET="${BACKUP_BUCKET:-}"
BACKUP_DIR="${BACKUP_DIR:-/tmp}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
PUSHGATEWAY_URL="${PUSHGATEWAY_URL:-}"
JOB_NAME="${JOB_NAME:-db_backup}"
INSTANCE_NAME="${INSTANCE_NAME:-$(hostname)}"

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is required" >&2
  exit 1
fi

mkdir -p "${BACKUP_DIR}"
FILE_EXT="dump"
if [[ "${BACKUP_FORMAT}" == "plain" ]]; then
  FILE_EXT="sql.gz"
fi

BACKUP_FILE="${BACKUP_DIR}/learning-platform-${TS}.${FILE_EXT}"
CHECKSUM_FILE="${BACKUP_FILE}.sha256"
MANIFEST_FILE="${BACKUP_FILE}.manifest.json"

cleanup_old_local_backups() {
  find "${BACKUP_DIR}" -maxdepth 1 -type f -name 'learning-platform-*' -mtime "+${RETENTION_DAYS}" -delete || true
}

push_metric() {
  local metric_name="$1"
  local metric_value="$2"
  if [[ -z "${PUSHGATEWAY_URL}" ]]; then
    return 0
  fi
  cat <<EOF | curl --silent --show-error --fail --data-binary @- \
    "${PUSHGATEWAY_URL%/}/metrics/job/${JOB_NAME}/instance/${INSTANCE_NAME}"
# TYPE ${metric_name} gauge
${metric_name} ${metric_value}
EOF
}

if [[ "${BACKUP_FORMAT}" == "plain" ]]; then
  pg_dump "${DATABASE_URL}" | gzip > "${BACKUP_FILE}"
else
  pg_dump --format=custom --file="${BACKUP_FILE}" "${DATABASE_URL}"
fi

sha256sum "${BACKUP_FILE}" > "${CHECKSUM_FILE}"
cat > "${MANIFEST_FILE}" <<EOF
{
  "created_at": "${TS}",
  "format": "${BACKUP_FORMAT}",
  "file": "$(basename "${BACKUP_FILE}")",
  "checksum_file": "$(basename "${CHECKSUM_FILE}")"
}
EOF

if [[ -n "${BACKUP_BUCKET}" ]]; then
  aws s3 cp "${BACKUP_FILE}" "s3://${BACKUP_BUCKET}/${BACKUP_PREFIX}/$(basename "${BACKUP_FILE}")"
  aws s3 cp "${CHECKSUM_FILE}" "s3://${BACKUP_BUCKET}/${BACKUP_PREFIX}/$(basename "${CHECKSUM_FILE}")"
  aws s3 cp "${MANIFEST_FILE}" "s3://${BACKUP_BUCKET}/${BACKUP_PREFIX}/$(basename "${MANIFEST_FILE}")"
fi

cleanup_old_local_backups
push_metric learning_platform_backup_last_success_timestamp_seconds "$(date -u +%s)"
push_metric learning_platform_backup_last_size_bytes "$(wc -c < "${BACKUP_FILE}")"

echo "backup complete: ${BACKUP_FILE}"
