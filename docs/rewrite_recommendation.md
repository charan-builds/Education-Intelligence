# Rewrite Recommendation Report

This document outlines structural and technology recommendations if we were to rebuild the platform from scratch today, explaining what to keep, redesign, or remove.

---

## 1. Summary of Recommendations

```text
========================================================================
[KEEP]                               │ [REDESIGN]
------------------------------------ │ ----------------------------------
- Layered codebase structure         │ - In-Memory graph sorting logic
- PostgreSQL dynamic RLS isolation   │ - Monolithic database connections
- Decoupled AI Microservice boundary│ - Redis as primary task broker
========================================================================
```

---

## 2. Rationale & Recommendations

### A. Architectural Changes
*   **Keep**: The layered design (Presentation $\rightarrow$ Application $\rightarrow$ Domain $\rightarrow$ Infrastructure) because it isolates core algorithms from database details.
*   **Redesign**: Migrate the modular monolith to three decoupled services (Auth Service, Content Service, Diagnostic Service). This allows teams to scale and deploy services independently.

### B. Database Changes
*   **Keep**: PostgreSQL RLS policies ([postgres_tenant_rls.sql](file:///home/charan_derangula/projects/intelligentSystems/backend/sql/postgres_tenant_rls.sql)) because database-level security provides a reliable safety net against cross-tenant leaks.
*   **Redesign**: Use **Neo4j** as a dedicated graph database for the content layer. Storing topic prerequisites as graph nodes makes traversal queries faster and simpler.

### C. Technological Changes
*   **Keep**: FastAPI and Next.js because they support fast development cycles and strong type validation schemas.
*   **Redesign**: Replace Redis queues with **Apache Kafka** to handle background tasks. Kafka supports partition keys, guaranteeing events are processed sequentially within tenants.

### D. Deployment Changes
*   **Keep**: Stateless pod deployments using Kubernetes.
*   **Redesign**: Replace raw Kubernetes manifests with **Helm Charts** to simplify environment configuration management.
