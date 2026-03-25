# Reliability Runbook

## Infra Design

- PostgreSQL runs as a managed primary with at least one hot standby replica in a separate zone.
- Backups are taken daily with `pg_dump` custom-format archives and uploaded to S3-compatible object storage.
- Weekly restore drills run into an isolated verification database.
- API and worker deployments stay stateless so DB failover is a connection-string cutover plus rollout restart.
- Redis, Kafka, and object storage should each use managed HA offerings or clustered deployments.

## Backup Strategy

- Script: [backup_db.sh](/home/charan_derangula/projects/intelligentSystems/scripts/ops/backup_db.sh)
- Output artifacts:
  - dump file
  - `.sha256` checksum
  - manifest JSON
- Pushes optional Prometheus heartbeat metrics through Pushgateway:
  - `learning_platform_backup_last_success_timestamp_seconds`
  - `learning_platform_backup_last_size_bytes`

Recommended cadence:
- full logical backup daily
- WAL/PITR via managed database service
- retention 14-30 days for daily dumps
- monthly restore verification retained separately

## Restore Procedure

- Script: [restore_db.sh](/home/charan_derangula/projects/intelligentSystems/scripts/ops/restore_db.sh)
- Supports restore from local file or latest S3 object.
- Verifies checksum before restore.
- Supports `RESTORE_MODE=replace` for full replacement.

Recommended drill:
1. Restore latest backup to isolated database.
2. Run migrations compatibility check.
3. Run smoke tests against restored environment.
4. Record RTO and RPO.

## Failover Strategy

- Script: [failover_cutover.sh](/home/charan_derangula/projects/intelligentSystems/scripts/ops/failover_cutover.sh)
- Promote managed standby or replica through provider control plane.
- Update `DATABASE_URL` secret to the promoted writer.
- Restart API, worker, and beat deployments.
- Validate health endpoints and queue recovery.

Production sequence:
1. Confirm primary failure and replica readiness.
2. Freeze non-essential admin writes if possible.
3. Promote standby.
4. Run cutover script.
5. Validate app health, outbox drain, and background workers.
6. Rebuild replica topology after incident.

## Chaos Scenarios

- Script: [chaos_scenarios.sh](/home/charan_derangula/projects/intelligentSystems/scripts/chaos/chaos_scenarios.sh)

Recommended scenarios:
- delete one API pod and confirm no user-visible outage
- delete one worker pod and confirm outbox backlog recovers
- scale workers to zero for 60s and confirm retry/backlog alerts trigger
- block API egress and confirm dependency/circuit-breaker behavior
- simulate DB failover cutover in staging

Success criteria:
- p95 API latency returns to baseline after pod loss
- no event loss
- restore verification completes within target RTO
- alerts fire within 5 minutes for backup or failover regressions

## Monitoring Setup

Prometheus must scrape:
- API `/metrics`
- nginx exporter
- optional Pushgateway for backup/restore heartbeats

Key alerts:
- stale or missing backup heartbeat
- stale restore drill heartbeat
- backup artifact unexpectedly small
- existing API, outbox, DB slow-query, and websocket alerts
