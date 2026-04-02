#!/usr/bin/env bash
set -euo pipefail

TARGET_DATABASE_URL="${TARGET_DATABASE_URL:-${DATABASE_URL:-}}"
BACKUP_FILE="${BACKUP_FILE:-}"
BACKUP_BUCKET="${BACKUP_BUCKET:-}"
BACKUP_PREFIX="${BACKUP_PREFIX:-db-backups}"
CHECKSUM_FILE="${CHECKSUM_FILE:-}"
RESTORE_MODE="${RESTORE_MODE:-replace}"
PUSHGATEWAY_URL="${PUSHGATEWAY_URL:-}"
JOB_NAME="${JOB_NAME:-db_restore}"
INSTANCE_NAME="${INSTANCE_NAME:-$(hostname)}"

if [[ -z "${TARGET_DATABASE_URL}" ]]; then
  echo "TARGET_DATABASE_URL or DATABASE_URL is required" >&2
  exit 1
fi

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

download_latest_backup() {
  local latest
  latest="$(aws s3 ls "s3://${BACKUP_BUCKET}/${BACKUP_PREFIX}/" | awk '{print $4}' | grep -E '\.(dump|sql\.gz)$' | sort | tail -n 1)"
  [[ -n "${latest}" ]] || { echo "No backup found in S3" >&2; exit 1; }
  BACKUP_FILE="/tmp/${latest}"
  aws s3 cp "s3://${BACKUP_BUCKET}/${BACKUP_PREFIX}/${latest}" "${BACKUP_FILE}"
  CHECKSUM_FILE="${BACKUP_FILE}.sha256"
  aws s3 cp "s3://${BACKUP_BUCKET}/${BACKUP_PREFIX}/${latest}.sha256" "${CHECKSUM_FILE}"
}

if [[ -z "${BACKUP_FILE}" ]]; then
  if [[ -z "${BACKUP_BUCKET}" ]]; then
    echo "Either BACKUP_FILE or BACKUP_BUCKET must be provided" >&2
    exit 1
  fi
  download_latest_backup
fi

if [[ -z "${CHECKSUM_FILE}" && -f "${BACKUP_FILE}.sha256" ]]; then
  CHECKSUM_FILE="${BACKUP_FILE}.sha256"
fi

if [[ -n "${CHECKSUM_FILE}" ]]; then
  sha256sum -c "${CHECKSUM_FILE}"
fi

if [[ "${RESTORE_MODE}" == "replace" ]]; then
  if [[ "${BACKUP_FILE}" == *.sql.gz ]]; then
    gunzip -c "${BACKUP_FILE}" | psql "${TARGET_DATABASE_URL}"
  else
    pg_restore --clean --if-exists --no-owner --no-privileges --dbname="${TARGET_DATABASE_URL}" "${BACKUP_FILE}"
  fi
else
  if [[ "${BACKUP_FILE}" == *.sql.gz ]]; then
    gunzip -c "${BACKUP_FILE}" | psql "${TARGET_DATABASE_URL}"
  else
    pg_restore --no-owner --no-privileges --dbname="${TARGET_DATABASE_URL}" "${BACKUP_FILE}"
  fi
fi

push_metric learning_platform_restore_last_success_timestamp_seconds "$(date -u +%s)"
echo "restore complete from ${BACKUP_FILE}"
