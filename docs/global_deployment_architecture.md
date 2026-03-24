# Global Deployment Architecture

## Target Cloud Shape

This platform is prepared for production deployment on either AWS or GCP with the same logical topology:

- global CDN for the frontend
- managed Kubernetes for application workloads
- managed PostgreSQL with HA and backups
- managed Redis for cache, broker, and lightweight queueing
- cloud load balancer with TLS termination
- secrets manager and IAM-backed workload identity
- CI/CD pipeline for image build and rollout

## Reference Topologies

### AWS

- `CloudFront` for global frontend delivery
- `S3` or frontend container origin for static delivery
- `Route 53` for DNS
- `AWS WAF` in front of CloudFront / ALB
- `EKS` for orchestration
- `ALB Ingress Controller` for HTTP routing
- `RDS PostgreSQL Multi-AZ` for transactional data
- `ElastiCache Redis` for cache / Celery broker
- `Secrets Manager` + `IAM Roles for Service Accounts`
- `ECR` for image registry

### GCP

- `Cloud CDN` for global frontend delivery
- `Cloud Storage` or frontend container origin
- `Cloud DNS`
- `Cloud Armor`
- `GKE` for orchestration
- `GKE Ingress` / `Gateway API`
- `Cloud SQL for PostgreSQL` with HA
- `Memorystore Redis`
- `Secret Manager` + `Workload Identity`
- `Artifact Registry`

## Runtime Components

Kubernetes workloads:

- `frontend`
- `api`
- `ai-service`
- `celery-worker`
- `celery-beat`
- `ingress-nginx` or cloud-native ingress

Managed services:

- PostgreSQL primary + replica
- Redis primary + replica / managed failover
- object storage for backups and assets
- observability stack or managed cloud monitoring

## Traffic Flow

1. user hits global DNS
2. CDN serves frontend assets near the user
3. API calls route through global or regional load balancer
4. ingress routes `/api`, `/mentor`, `/topics`, `/roadmap`, websocket traffic, and health checks to backend services
5. backend reads/writes PostgreSQL and Redis
6. async jobs run on Celery worker and beat

## Scale Strategy

- frontend scales horizontally behind CDN and ingress
- API uses HPA on CPU and memory
- Celery worker scales on queue depth and CPU
- AI service scales independently from the API
- PostgreSQL uses managed replication and automated failover
- Redis uses managed replication and backups

## Security Baseline

- TLS everywhere
- external secrets from cloud secret manager
- workload identity instead of static cloud credentials
- private subnets for stateful services
- least-privilege IAM roles
- WAF and rate limiting at edge + ingress
- encrypted volumes and encrypted database snapshots

## CI/CD Flow

1. run backend/frontend verification
2. build and tag container images
3. push images to cloud registry
4. update Kubernetes deployment images
5. run rollout verification
6. optionally gate production behind manual approval

## Database Production Policy

- managed PostgreSQL only
- Multi-AZ / HA enabled
- daily snapshots
- point-in-time recovery enabled
- at least one read replica for analytics and failover readiness
- restore drill at regular cadence

## Frontend Global Delivery

- deploy frontend behind CDN
- cache immutable Next.js static assets aggressively
- route API traffic separately to ingress
- use regional failover DNS for multi-region expansion

## Multi-Region Path

Phase 1:

- single region
- global CDN
- HA database in one region

Phase 2:

- standby region for stateless workloads
- cross-region database replica
- failover runbook

Phase 3:

- active/active stateless services
- region-aware routing
- split read traffic and disaster recovery automation
