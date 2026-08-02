# Architecture Decision Record (ADR) Catalog

This catalog documents the core architectural decisions that govern the **Learning Intelligence Platform**. It outlines the alternatives considered, trade-offs accepted, and long-term scaling implications.

---

## ADR 01: Modular Monolith Application Topology with Decoupled AI Boundary

### Context & Rationale
The platform houses diverse domains (analytics, community, diagnostic quiz engines, roadmap generators). Splitting these into separate microservices early introduces latency, network overhead, and complex database transactions. We chose a **modular monolith application style** for the primary FastAPI backend [main.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/main.py) to keep deployment simple and cognitive load low. 
However, LLM prompt engineering, prompt caching, and guardrail processing ([ai_service/service.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/service.py)) are slow and resource-heavy. We decoupled the AI code into a separate FastAPI microservice boundary to prevent slow LLM requests from exhausting database connection pools on the core backend.

### Alternative Designs Considered
1.  **Distributed Microservices Grid**: Splitting every domain (Auth, Content, Diagnostics) into independent network services.
2.  **Monolithic AI execution**: Running LLM requests directly inside the primary backend process.

### Why Alternatives Were Rejected
1.  **Microservices**: Rejected due to high operational complexity, distributed transaction overhead, and the latency costs of RPC calls across container networks.
2.  **Monolithic AI**: Rejected because LLM calls are slow. Running them in the same process would lead to thread pool starvation, slowing down transactional database queries.

### Trade-offs
*   **Con**: We manage two Python deployables and coordinate an internal REST integration contract.
*   **Pro**: Core web route latencies remain fast, and we can scale the AI service independently.

### Long-term Impact
*   *Scalability*: Compute nodes can scale out on EKS/GKE pods independently based on CPU load.
*   *Maintenance*: Developers can update AI prompt templates without risking bugs in the core authentication or payment modules.
*   *If Built Today*: **Yes**, I would make the same decision. Decoupling slow, external-API-dependent services is critical.

---

## ADR 02: PostgreSQL Row-Level Security (RLS) for SaaS Multi-Tenant Isolation

### Context & Rationale
The platform operates as a multi-tenant SaaS application. We chose a **Shared-Database, Shared-Schema** model to keep infrastructure costs low. To prevent cross-tenant data leaks, we enabled database-level RLS policies ([postgres_tenant_rls.sql](file:///home/charan_derangula/projects/intelligentSystems/backend/sql/postgres_tenant_rls.sql)), automatically filtering queries using session settings set on connection pools.

### Alternative Designs Considered
1.  **Database-per-tenant**: Provisioning separate databases for each client.
2.  **Schema-per-tenant**: Using separate Postgres schemas for each client.
3.  **Application-level filters**: Appending `tenant_id` filters to queries manually.

### Why Alternatives Were Rejected
1.  **Database-per-tenant**: Too expensive; managing connection pools across hundreds of databases is operationally complex.
2.  **Schema-per-tenant**: Hard to migrate; running schema migrations across hundreds of tenant schemas is slow and error-prone.
3.  **Application-level filters**: High risk of data leaks if developers forget to append filters.

### Trade-offs
*   **Con**: Postgres RLS adds a small execution overhead to table scans, and debugging query flows requires setting session contexts manually.
*   **Pro**: Strong database-level isolation guarantees that prevent accidental data leaks.

### Long-term Impact
*   *Scalability*: RLS is highly scalable, but query planners must compile execution plans carefully. All tables must have indexes covering the `tenant_id` column.
*   *Maintenance*: DBAs must audit migrations to ensure all new tables have RLS policies enabled.
*   *If Built Today*: **Yes**, I would make the same decision. RLS provides the best balance of cost efficiency and database-level security.

---

## ADR 03: Transactional Event Outbox Pattern for Eventual Consistency & Cache Sync

### Context & Rationale
When database mutations complete, background systems (caches, search indexes, analytics) must sync. Publishing messages to brokers during HTTP requests risks data inconsistency if network failures occur. We implemented the **Transactional Outbox Pattern** ([outbox_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/outbox_service.py)). Business changes and outbox event payloads are saved to the database in a single transaction, and processed asynchronously by background sweep workers.

### Alternative Designs Considered
1.  **Synchronous In-Route Publishing**: Publishing events to Redis/Kafka brokers directly inside API routers.
2.  **CDC (Change Data Capture)**: Using Debezium to stream updates from Postgres write-ahead logs (WAL).

### Why Alternatives Were Rejected
1.  **In-Route Publishing**: Dual-write problems; if the database transaction commits but the network call to the broker fails, the systems drift out of sync.
2.  **CDC**: Rejected due to high infrastructure costs and complexity for early-stage deployments.

### Trade-offs
*   **Con**: Adds write overhead to transactions and introduces eventual consistency delays.
*   **Pro**: Guarantees at-least-once event delivery and prevents transactional failures from blocking message dispatches.

### Long-term Impact
*   *Scalability*: The outbox table can grow quickly, requiring database vacuuming and purging jobs.
*   *Maintenance*: Simple to maintain; event schemas are validated using Pydantic models.
*   *If Built Today*: **Yes**, I would make the same decision. Eventual consistency is critical for high-availability SaaS platforms.

---

## ADR 04: Redis as a Shared Cache & Celery Task Broker

### Context & Rationale
To keep deployment costs low, we combined caching and Celery task brokering into a single high-performance Redis cluster.

### Alternative Designs Considered
1.  **Memcached + RabbitMQ**: Memcached for caching and RabbitMQ for Celery tasks.
2.  **PostgreSQL as Celery Broker**: Using database tables as Celery queues.

### Why Alternatives Were Rejected
1.  **Memcached + RabbitMQ**: Operational overhead of managing two separate stateful services.
2.  **PostgreSQL Broker**: DB queue polling introduces high database load and lock contention.

### Trade-offs
*   **Con**: Redis stores data in-memory. If a node crashes without persistent volumes enabled, pending Celery tasks can be lost.
*   **Pro**: High performance, sub-millisecond latencies, and low operational overhead.

### Long-term Impact
*   *Scalability*: Under heavy loads, the Redis cluster can experience memory pressure, requiring separate cache and broker nodes.
*   *Maintenance*: Standard maintenance procedures apply.
*   *If Built Today*: **Yes**, but I would configure persistent disk storage for Celery broker nodes to prevent task losses on container restarts.

---

## ADR 05: Next.js 15 App Router React Client Hydration & Middleware Authentication

### Context & Rationale
We chose **Next.js 15** with the App Router to build a role-based frontend client. The platform uses Next.js route middleware ([middleware.ts](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/middleware.ts)) to inspect cookies and redirect unauthenticated requests before views render.

### Alternative Designs Considered
1.  **Single Page Application (SPA)**: Pure Client-side React app.
2.  **Multi-Page Application (MPA)**: Traditional server-rendered HTML.

### Why Alternatives Were Rejected
1.  **SPA**: Poor initial load speeds and search engine optimization (SEO) performance.
2.  **MPA**: Slow, page-refreshing interface that degrades student quiz experiences.

### Trade-offs
*   **Con**: Complexity of coordinating Server-Side Rendering (SSR) layouts with interactive Client-Side Components.
*   **Pro**: Fast initial page loads, optimized SEO metrics, and a responsive user interface.

### Long-term Impact
*   *Scalability*: Frontend nodes scale horizontally behind global CDNs.
*   *Maintenance*: Layout wrappers separate student, teacher, and administrator dashboard modules.
*   *If Built Today*: **Yes**, I would make the same decision. Next.js provides the best balance of SEO performance and interactive user interfaces.

---

## ADR 06: Decoupled AI Microservice with Supervisor-Specialist Agent Routing

### Context & Rationale
Generalist LLM prompts struggle to balance tutor, motivator, and analyst roles simultaneously. We implemented a **Supervisor-Specialist Multi-Agent System** that routes student queries to specialized agents dynamically based on intent keywords.

### Alternative Designs Considered
1.  **Single Prompt Agent**: Enforcing tutor and analyst rules inside a single system prompt.
2.  **LangChain Agentic Graph**: Complex agent framework networks.

### Why Alternatives Were Rejected
1.  **Single Prompt**: Opaque responses and high hallucination rates when switching between motivation and analytics contexts.
2.  **LangChain**: Overengineered; adds system complexity and response latency.

### Trade-offs
*   **Con**: Multiple model evaluations can increase response latency.
*   **Pro**: Higher response accuracy, reduced hallucinations, and modular agent prompts.

### Long-term Impact
*   *Scalability*: Independent agent routing allows teams to test and update prompts without affecting core workflows.
*   *Maintenance*: Prompts are declared as clean Python configurations in [prompts.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/prompts.py).
*   *If Built Today*: **Yes**, I would make the same decision. Specialized agents provide higher pedagogical quality.

---

## ADR 07: Online/Offline Hybrid Feature Snapshot Store (`ml_feature_snapshots`)

### Context & Rationale
Training models requires consistent, pre-engineered student and topic features. We chose to store feature snapshots directly inside PostgreSQL tables ([ml_platform_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/ml_platform_service.py)) rather than spinning up dedicated feature stores.

### Alternative Designs Considered
1.  **Enterprise Feature Store (Feast)**: Decoupled feature store system.
2.  **Dynamic Feature Aggregations**: Computing features on-demand during inference runs.

### Why Alternatives Were Rejected
1.  **Feast**: Too complex for initial scale; adds significant infrastructure overhead.
2.  **Dynamic Feature Aggregations**: Querying large database tables dynamically on inference routes causes API timeouts under high traffic.

### Trade-offs
*   **Con**: Snapshot tables can grow quickly, requiring regular database indexing and maintenance.
*   **Pro**: Fast SQL query access times and schema consistency with existing databases.

### Long-term Impact
*   *Scalability*: Postgres tables can scale to millions of rows, but will eventually require partitioning.
*   *Maintenance*: Simple database migrations cover schema changes.
*   *If Built Today*: **Yes**, I would make the same decision. Storing snapshots in PostgreSQL is the most cost-efficient choice for early-stage deployments.
