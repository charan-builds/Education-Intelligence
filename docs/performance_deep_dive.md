# Performance Deep Dive

This document details the performance analysis of the platform, identifying query latencies, CPU hotspots, memory profiles, network overhead, and client-side rendering bottlenecks.

---

## 1. SQL Query Latency Analysis (Slow Queries)

### RLS Overhead on Table Scans
*   **The Problem**: Every tenant-scoped query runs setting validation filters (`SET LOCAL app.current_tenant_id`). On tables containing millions of rows (like `learning_events` and `user_answers`), these filters can result in full table scans if appropriate indexes are missing.
*   **Mitigation**: Verify that composite indexes cover target query filters, as detailed in the [Index Recommendations SQL](file:///home/charan_derangula/projects/intelligentSystems/docs/postgres_index_recommendations.sql):
    ```sql
    CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_learning_events_tenant_user_event_ts
    ON learning_events (tenant_id, user_id, event_timestamp DESC);
    ```

### Lock Contention during Outbox Sweeps
*   **The Problem**: Celery outbox dispatcher sweeps query the `outbox_events` table periodically. Standard query sweeps lock table rows, blocking concurrent API writes.
*   **Mitigation**: Implement `SKIP LOCKED` filters in outbox query scripts to skip locked rows:
    ```sql
    SELECT * FROM outbox_events WHERE status = 'PENDING' FOR UPDATE SKIP LOCKED LIMIT 100;
    ```

---

## 2. Expensive API Endpoints

1.  **`/diagnostic/submit`**: Validates diagnostic questions, checks timers, and updates student ability scores ($\theta$). This multi-step workflow increases latency under high concurrency.
2.  **`/roadmap/generate`**: Traverses topic networks and sorts dependencies topologically. In-memory sorting can lead to API request timeouts.
3.  **`/mentor/chat`**: AI chat routes depend on external LLM response rates. Network latencies can lock container thread pools.

---

## 3. CPU & Memory Hotspots

### CPU Hotspots
*   **Bcrypt Password Hashing**: Hashing credentials uses significant CPU resources to prevent brute-force logins.
*   **Topological Sorting**: Sorting prerequisites in application memory blocks Python's event loop.
*   **Theta Ability Calculations**: Matrix calculations in the adaptive engine block CPU cycles during test runs.

### Memory Hotspots
*   **Realtime Websocket Connections**: Persistent client connections consume server file descriptors and memory resources.
*   **Model Parameter Storage**: Loading serialization models into the AI service's memory space increases memory consumption.

---

## 4. Network Overhead & Rendering Bottlenecks

### Network Overhead
*   **Chat History Payloads**: Sending full chat histories to AI services increases request sizes.
*   **Analytical Log Exports**: Downloading raw event data in single requests blocks connections.

### Client-Side Rendering Bottlenecks
*   **Progress Dashboard Hydration**: Rendering complex charts with many data points causes client-side lag.
*   **Recursive Accordion Lists**: Rendering large topics graphs as nested accordion lists causes layout shifts.

---

## 5. Optimization Opportunities

1.  **Implement Server-Side Caching**: Cache static topic graphs and precalculated dashboard metrics in Redis to avoid database queries on every request.
2.  **Use Pre-signed URLs for Uploads**: Route file uploads directly to storage buckets, offloading network traffic from API containers.
3.  **Optimize Graph Calculations**: Offload prerequisite sorting to PostgreSQL using recursive CTEs.
4.  **Debounce Telemetry Writes**: Batch client telemetry logs in-memory before writing them to the database.
