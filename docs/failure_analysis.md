# Failure Analysis Catalog (50 Operational Scenarios)

This catalog outlines the top 50 operational failure scenarios for the platform. It provides the diagnostic metrics, log parameters, and recovery steps required by on-call operators.

---

## Group 1: Authentication & Identity Failures

### FS-01: JWT Signing Key Rotation Outage
*   **Cause**: The secret key environment variable (`JWT_SECRET_KEY`) is updated on the API pods but not updated on the Celery workers.
*   **Symptoms**: Users can log in, but background tasks that verify token signatures (e.g. processing invites) fail with signature validation errors.
*   **Detection**: Celery logs output `AuthenticationError: Invalid token signature` exceptions.
*   **Recovery**: Verify and sync the config variables across the API and Celery worker deployments, and restart the worker pods.
*   **Prevention**: Store common configurations in a shared Kubernetes ConfigMap/Secret.
*   **Monitoring**: Alert on `celery_task_failures_total` metrics spikes.

### FS-02: Redis Blacklist Cache Memory Eviction
*   **Cause**: Redis memory limits are reached under high load, causing it to evict blacklisted tokens.
*   **Symptoms**: Logged-out users can access API routes using old, unexpired tokens.
*   **Detection**: Users access routes without logs indicating new login events.
*   **Recovery**: Clear the cache and increase the Redis memory limits.
*   **Prevention**: Configure the Redis instance with a `noeviction` policy for session and token namespaces.
*   **Monitoring**: Alert if Redis memory usage (`redis_memory_used_bytes`) exceeds 90% of limits.

### FS-03: MFA TOTP Code Validation Timeout
*   **Cause**: Network latency or clock drift between user devices and API containers exceeds the verification window.
*   **Symptoms**: Users fail to log in, receiving `MFA validation failed` errors.
*   **Detection**: API logs output `HTTP 401 Unauthorized: MFA code expired`.
*   **Recovery**: Sync the system clocks on the API containers using NTP protocols.
*   **Prevention**: Enable time synchronization services (like NTP) on all cluster nodes.
*   **Monitoring**: Track the frequency of failed login attempts on `mfa_login_failures_total` metrics.

### FS-04: OTP SMS Gateway Request Limits Reached
*   **Cause**: SMS gateway limits are exhausted due to high traffic or spam registrations.
*   **Symptoms**: Users do not receive phone verification codes during signup.
*   **Detection**: Logs output `GatewayError: SMS quota exceeded` from the external provider client.
*   **Recovery**: Upgrade the SMS gateway tier or configure a backup provider.
*   **Prevention**: Implement IP rate limits on OTP request routes to block spam.
*   **Monitoring**: Alert if third-party gateway API responses return error statuses.

### FS-05: Invite Token Expiration Drift
*   **Cause**: Token expiration times are calculated using the host node's local system clock, which drifts from database timestamps.
*   **Symptoms**: Valid invitation links are rejected as expired.
*   **Detection**: Logs output `HTTP 400 Bad Request: Invite token expired`.
*   **Recovery**: Manually extend the invite expiration timestamps in the database.
*   **Prevention**: Use database-generated UTC timestamps for all validation checks.
*   **Monitoring**: Track the ratio of failed invite accepts.

---

## Group 2: Multi-Tenancy & Isolation Failures

### FS-06: Database Connection Context Leakage
*   **Cause**: Database connections are returned to the pool without clearing the session context variable `app.current_tenant_id`.
*   **Symptoms**: Users see data from other tenants, causing cross-tenant data leaks.
*   **Detection**: Database query logs show mismatched tenant IDs on connections.
*   **Recovery**: Recycle all database connections in the pool and restart the API pods.
*   **Prevention**: Configure database pool adapters to reset session variables on connection release.
*   **Monitoring**: Alert if connections execute queries without setting `app.current_tenant_id`.

### FS-07: PostgreSQL RLS Policy Syntax Lockups
*   **Cause**: Running DDL changes to update RLS policies locks parent tables, blocking concurrent queries.
*   **Symptoms**: API routes timeout, and connection pools saturate.
*   **Detection**: Database logs show `LockTimeoutException` on RLS migrations.
*   **Recovery**: Terminate the migration transaction and run DDL changes during low-traffic maintenance windows.
*   **Prevention**: Run migrations with short lock timeout limits.
*   **Monitoring**: Alert on elevated active database connection metrics.

### FS-08: RLS Gaps on ML Snapshot Tables
*   **Cause**: RLS policies are missing on the `ml_feature_snapshots` table.
*   **Symptoms**: Models query features across tenants, leading to cross-tenant data leaks.
*   **Detection**: Security audits find queries execution on ML tables without RLS validation.
*   **Recovery**: Deploy the missing RLS policies using SQL migrations.
*   **Prevention**: Include RLS verification assertions in unit tests.
*   **Monitoring**: Run weekly schema audits to identify tables missing RLS policies.

### FS-09: Context Override Abuse by Super Admin Accounts
*   **Cause**: Compromised super-admin accounts bypass tenant boundaries using `X-Tenant-ID` headers.
*   **Symptoms**: Data modification logs show administrative changes initiated by external IPs.
*   **Detection**: Audit logs show `SuperAdmin context override` actions.
*   **Recovery**: Disable the compromised account and revoke the active tokens.
*   **Prevention**: Limit super-admin access to internal VPNs and require MFA for all overrides.
*   **Monitoring**: Alert on any request containing `X-Tenant-ID` headers.

### FS-10: Tenant Deactivation Data Access
*   **Cause**: Cache nodes do not clear tenant metadata keys when a tenant is deactivated.
*   **Symptoms**: Users from deactivated tenants can access cached API endpoints.
*   **Detection**: API logs show queries from users linked to inactive tenants.
*   **Recovery**: Evict the deactivated tenant's metadata keys from the Redis cache.
*   **Prevention**: Implement cache invalidation hooks in the tenant deactivation workflows.
*   **Monitoring**: Track request rates from deactivated tenant IDs.

---

## Group 3: Adaptive Testing Engine Failures

### FS-11: Theta Calculation Recursion Timeout
*   **Cause**: The adaptive testing engine encounters recursion timeouts while traversing deep topic maps under high concurrency.
*   **Symptoms**: Diagnostic submission routes timeout, leading to connection failures.
*   **Detection**: API logs output `RecursionError` exceptions.
*   **Recovery**: Restart the API pods and clear the active diagnostic session cache.
*   **Prevention**: Set recursion limits and optimize graph search loops.
*   **Monitoring**: Alert if `/diagnostic/submit` latency P99 exceeds 2 seconds.

### FS-12: Session State Lock Contention
*   **Cause**: Rapid submission requests on the same diagnostic session trigger transaction locks.
*   **Symptoms**: Users receive `HTTP 409 Conflict: State update in progress` errors.
*   **Detection**: Database logs output `deadlock detected` errors.
*   **Recovery**: Release database locks and retry the transaction.
*   **Prevention**: Implement optimistic locking configurations using version keys.
*   **Monitoring**: Track the frequency of SQL transaction rollbacks.

### FS-13: Question Pool Exhaustion
*   **Cause**: The adaptive testing engine cannot find questions matching the student's ability level.
*   **Symptoms**: Diagnostic routes fail, returning `No questions available` errors.
*   **Detection**: Logs output `IndexError: list index out of range` from the question selector module.
*   **Recovery**: Add backup questions to the target topic pools.
*   **Prevention**: Implement fallback rules to select questions from parent topics.
*   **Monitoring**: Alert if diagnostic routes return HTTP 500 error responses.

### FS-14: Question Timeout Enforcement Outage
*   **Cause**: Delayed worker schedules cause time checks to fail, marking valid answers as timed out.
*   **Symptoms**: Valid answers are rejected with timeout errors.
*   **Detection**: Logs show `DiagnosticAnswerResponse: answer rejected (timed out)`.
*   **Recovery**: Reschedule background task queues and clear worker backlogs.
*   **Prevention**: Set lenient timing thresholds to tolerate small network latencies.
*   **Monitoring**: Alert if answer timeout rates exceed 5%.

### FS-15: Diagnostic Score Desynchronization
*   **Cause**: Database transaction rollbacks restore diagnostic states but do not revert cache updates in Redis.
*   **Symptoms**: Student dashboards display incorrect score metrics.
*   **Detection**: Dashboards display scores that differ from database records.
*   **Recovery**: Evict the student's cache keys to force a database reload.
*   **Prevention**: Evict cache keys *after* database transactions commit successfully.
*   **Monitoring**: Run data verification scripts to identify discrepancies.

---

## Group 4: Learning Roadmaps & Content Traversal Gaps

### FS-16: Circular Prerequisite Dependency Loop
*   **Cause**: Administrators create prerequisite cycles (e.g. Topic A requires B, which requires A).
*   **Symptoms**: Roadmap generation requests loop infinitely, causing container timeouts.
*   **Detection**: API logs show timeout exceptions in the topological sort modules.
*   **Recovery**: Locate and delete the circular loop relationship in the database.
*   **Prevention**: Implement loop detection checks in the prerequisite creation route.
*   **Monitoring**: Track execution times in the topological sort modules.

### FS-17: Roadmap Step Complete Transaction Deadlock
*   **Cause**: Multiple concurrent completions update shared topic stats, causing database deadlocks.
*   **Symptoms**: Users receive HTTP 500 errors on step completions.
*   **Detection**: Database logs show `deadlock detected` errors.
*   **Recovery**: Retry the failed transaction after a random backoff delay.
*   **Prevention**: Update aggregations asynchronously using Celery background tasks.
*   **Monitoring**: Alert if transaction rollback rates exceed 2%.

### FS-18: Cache Desynchronization on Topic Updates
*   **Cause**: Modifying topic prerequisites does not clear the cached roadmap graphs.
*   **Symptoms**: Students see outdated roadmap layouts.
*   **Detection**: Roadmaps display relationships that differ from database configurations.
*   **Recovery**: Clear the active roadmap cache keys in Redis.
*   **Prevention**: Implement cache invalidation hooks in the topic update routes.
*   **Monitoring**: Verify cached roadmap layouts against database configurations.

### FS-19: Topic Knowledge Score Leakage
*   **Cause**: RLS is disabled on the topic score table during aggregation updates.
*   **Symptoms**: Students see metrics from other tenants on their dashboard views.
*   **Detection**: Dashboards display student names from other tenants.
*   **Recovery**: Enable database-level RLS policies on the topic score table.
*   **Prevention**: Include RLS verification assertions in test suites.
*   **Monitoring**: Run weekly schema audits to verify RLS policies.

### FS-20: Missing Steps on Goal Changes
*   **Cause**: Modifying goal topics does not update existing student roadmaps.
*   **Symptoms**: Students cannot access newly added topics in their active goals.
*   **Detection**: Students report missing roadmap steps for updated goals.
*   **Recovery**: Run a batch database script to append steps to active roadmaps.
*   **Prevention**: Trigger roadmap update actions when goal topics are modified.
*   **Monitoring**: Track the sync status of roadmaps against parent goals.

---

## Group 5: AI Orchestration & Prompt Failures

### FS-21: External LLM Provider API Outage
*   **Cause**: OpenAI or Google API service is down.
*   **Symptoms**: Mentor chat requests timeout, and users receive error messages.
*   **Detection**: Logs output `LLMClientError: Provider API unavailable`.
*   **Recovery**: Failover to a backup LLM provider or activate the fallback advisor.
*   **Prevention**: Implement circuit breakers and fallback configurations.
*   **Monitoring**: Alert if LLM client API calls return error statuses.

### FS-22: AI JSON Parse Failure
*   **Cause**: The LLM outputs unstructured text instead of the requested JSON schema.
*   **Symptoms**: Chats fail, returning parsing errors to the user.
*   **Detection**: Logs show `JSONDecodeError` exceptions.
*   **Recovery**: Request the AI to regenerate the response using strict schema parameters.
*   **Prevention**: Use strict schema generation formats (such as OpenAI Structured Outputs).
*   **Monitoring**: Track the frequency of failed JSON parses.

### FS-23: Prompt Injection Vulnerability Trigger
*   **Cause**: User prompts contain injection phrases (e.g. `ignore previous instructions`).
*   **Symptoms**: The AI reveals system prompts or executes unauthorized instructions.
*   **Detection**: Guardrail logs show `injection_hints` warnings.
*   **Recovery**: Block the prompt and return a standardized error message.
*   **Prevention**: Implement sanitizers to filter inputs before calling the model.
*   **Monitoring**: Alert on any prompt injection detections.

### FS-24: Token Context Window Exhaustion
*   **Cause**: Large chat histories exceed the model's token limits.
*   **Symptoms**: Chat routes return HTTP 400 errors.
*   **Detection**: Logs output `LLMClientError: Maximum context length exceeded`.
*   **Recovery**: Truncate the chat history to the last 5 conversations.
*   **Prevention**: Implement context truncation rules in the API client.
*   **Monitoring**: Track the average token usage per chat request.

### FS-25: Multi-Agent Synthesis Timeout
*   **Cause**: Waiting for multiple specialist agent runs exceeds API timeouts.
*   **Symptoms**: Chat requests fail due to gateway timeout errors.
*   **Detection**: Nginx logs show HTTP 504 gateway timeouts.
*   **Recovery**: Run specialist agent tasks in parallel to reduce latency.
*   **Prevention**: Set short timeout limits for each agent run.
*   **Monitoring**: Track individual agent execution latencies.

---

## Group 6: Transactional Outbox & Celery Failures

### FS-26: Outbox Event Processing Stall
*   **Cause**: A worker process crashes while processing a batch, leaving tasks in a locked state.
*   **Symptoms**: Events remain pending, and downstream systems do not sync.
*   **Detection**: Logs show outbox events in a `PROCESSING` state for longer than 5 minutes.
*   **Recovery**: Reset the status of stuck events to `PENDING` to trigger a reprocess run.
*   **Prevention**: Implement automated sweeps to identify and recover stuck events.
*   **Monitoring**: Alert if pending events exceed 100 items.

### FS-27: Redis Memory Exhaustion
*   **Cause**: Large Celery task backlogs fill up Redis memory resources.
*   **Symptoms**: Redis crashes, stalling all task queues and cache operations.
*   **Detection**: Redis logs show `OOM command not allowed when used memory > 'maxmemory'`.
*   **Recovery**: Clear the cache and increase the Redis memory limits.
*   **Prevention**: Configure task limits and evict completed jobs automatically.
*   **Monitoring**: Alert if Redis memory usage exceeds 90% of limits.

### FS-28: Duplicate Event Delivery (At-Least-Once Delivery)
*   **Cause**: Network failures delay confirmations, causing workers to retry processed events.
*   **Symptoms**: Downstream systems process events twice (e.g. sending duplicate emails).
*   **Detection**: Logs show duplicate executions for the same event ID.
*   **Recovery**: Deduplicate the affected datasets in the database.
*   **Prevention**: Implement idempotency keys and check execution logs before reprocessing.
*   **Monitoring**: Track duplicate event executions.

### FS-29: Dead-Letter Queue Overload
*   **Cause**: Chronic failures (e.g. database disconnects) move many events to the DLQ.
*   **Symptoms**: Outbox dashboards display high error rates.
*   **Detection**: Logs output `OutboxEvent: moved to DLQ`.
*   **Recovery**: Fix the underlying issue and trigger an outbox replay run.
*   **Prevention**: Implement circuit breakers to stop processing if database connections drop.
*   **Monitoring**: Alert if dead-letter queue count exceeds 10 items.

### FS-30: Celery Beat Duplicate Scheduler Runs
*   **Cause**: Multiple instances of Celery Beat run concurrently, scheduling duplicate tasks.
*   **Symptoms**: Background jobs run twice simultaneously.
*   **Detection**: Logs show duplicate schedules for the same tasks.
*   **Recovery**: Terminate the duplicate Celery Beat containers.
*   **Prevention**: Enforce singleton deployments for Celery Beat.
*   **Monitoring**: Track the execution frequency of scheduled tasks.

---

## Group 7: Realtime WebSockets & Caches

### FS-31: Redis Pub/Sub Connection Drop
*   **Cause**: Network interruptions disconnect API containers from Redis.
*   **Symptoms**: WebSocket messages are not delivered, and users do not see real-time updates.
*   **Detection**: Logs show `ConnectionError: Redis connection lost` in the realtime bus module.
*   **Recovery**: Reconnect the realtime bus instances to Redis.
*   **Prevention**: Implement auto-reconnect logic with exponential backoff delays.
*   **Monitoring**: Alert if Pub/Sub connection states drop.

### FS-32: WebSocket Client Connection Leak
*   **Cause**: API instances fail to release connections when browser tabs close.
*   **Symptoms**: Server memory usage rises, eventually triggering OOM crashes.
*   **Detection**: Server file descriptor counts increase.
*   **Recovery**: Restart the affected API containers to release connections.
*   **Prevention**: Implement heartbeat checks to detect and terminate dead connections.
*   **Monitoring**: Track active connection counts.

### FS-33: Cache Stampede on Topic Graphs
*   **Cause**: Many concurrent requests query topic graphs when the cache expires.
*   **Symptoms**: Database load spikes, causing request timeouts.
*   **Detection**: Database query logs show duplicate executions of the same graph queries.
*   **Recovery**: Pre-warm the cache and resolve queries using single lock pools.
*   **Prevention**: Implement probabilistic early expiration caching strategies.
*   **Monitoring**: Alert on database CPU usage spikes.

### FS-34: Cache Key Collision
*   **Cause**: Namespace configurations overlap, writing topic scores to user profile keys.
*   **Symptoms**: API routes return schema parsing errors on profile lookups.
*   **Detection**: Logs show `ValidationError: Invalid profile data`.
*   **Recovery**: Clear the affected cache keys in Redis.
*   **Prevention**: Enforce unique namespace prefixes for all cache keys.
*   **Monitoring**: Track validation failure rates on cached lookups.

### FS-35: Redis Sentinel Failover Timeout
*   **Cause**: Sentinels fail to promote new Redis master nodes within timeout limits.
*   **Symptoms**: Write requests to Redis fail, stalling queues.
*   **Detection**: Logs show `ReadOnlyError: Write queries rejected by replica`.
*   **Recovery**: Manually promote a replica node to master.
*   **Prevention**: Set failover timeout limits under 10 seconds.
*   **Monitoring**: Alert on Redis master node failures.

---

## Group 8: Ecosystem Integrations & Storage

### FS-36: S3 Upload Request Expiration
*   **Cause**: Network delays delay uploads, causing pre-signed URLs to expire.
*   **Symptoms**: Users receive HTTP 403 errors during file uploads.
*   **Detection**: Browser logs show `S3UploadError: Request expired`.
*   **Recovery**: Request a new pre-signed URL and retry the upload.
*   **Prevention**: Extend pre-signed URL lifespans to 15 minutes.
*   **Monitoring**: Track the ratio of failed upload requests.

### FS-37: Marketplace Listing Review Fraud
*   **Cause**: Lack of purchase validation checks allows users to spam review entries.
*   **Symptoms**: Listing scores display fraudulent ratings.
*   **Detection**: Database logs show multiple reviews submitted by the same user ID.
*   **Recovery**: Delete the fraudulent reviews from the database.
*   **Prevention**: Enforce purchase verification before allowing reviews.
*   **Monitoring**: Track review submission frequencies.

### FS-38: API Key Credentials Compromise
*   **Cause**: Third-party developers commit partner API keys to public repositories.
*   **Symptoms**: Unauthorized API access events are logged from external IP addresses.
*   **Detection**: Logs show access queries with signatures matching blacklisted IP addresses.
*   **Recovery**: Revoke the compromised API key and notify the developer.
*   **Prevention**: Implement automated IP whitelists for API credentials.
*   **Monitoring**: Alert if API keys execute queries from unexpected locations.

### FS-39: Billing Status Mismatch
*   **Cause**: Network dropouts prevent billing platforms from syncing with subscription records.
*   **Symptoms**: Active customers lose access to features due to status sync failures.
*   **Detection**: Logs show `BillingError: Status mismatch for subscription ID`.
*   **Recovery**: Run a manual sync task to update subscription statuses.
*   **Prevention**: Enforce eventual consistency checks via outbox sweeps.
*   **Monitoring**: Alert on any subscription status mismatches.

### FS-40: Plugin Registry Validation Failures
*   **Cause**: Custom plugins export invalid JSON schemas.
*   **Symptoms**: API routes crash when trying to render plugin configurations.
*   **Detection**: Logs show `ValidationError` in the plugin registry module.
*   **Recovery**: Disable the affected plugin in the registry.
*   **Prevention**: Enforce strict schema validations before loading configurations.
*   **Monitoring**: Track validation error rates on registry lookups.

---

## Group 9: Observability & Monitoring Failures

### FS-41: Exporter Port Connection Timeout
*   **Cause**: Node firewall changes block Prometheus from accessing container metrics.
*   **Symptoms**: Prometheus dashboards display empty graphs.
*   **Detection**: Prometheus status logs show target endpoints as `DOWN`.
*   **Recovery**: Update network policies to allow Prometheus metrics scraping.
*   **Prevention**: Verify container network rules in CI pipelines.
*   **Monitoring**: Alert if scrape targets return timeout errors.

### FS-42: Alertmanager Routing Failures
*   **Cause**: Alertmanager fails to route notifications due to missing webhook credentials.
*   **Symptoms**: Alerts fire in Prometheus but are not dispatched to operators.
*   **Detection**: Prometheus logs show `AlertmanagerNotificationFailed` warnings.
*   **Recovery**: Verify and sync Alertmanager webhook credentials.
*   **Prevention**: Enforce credential checks in deployment pipelines.
*   **Monitoring**: Alert if Alertmanager status endpoints return failures.

### FS-43: Log Volume Disk Space Exhausted
*   **Cause**: Verbose logging fills up the host node's disk volumes.
*   **Symptoms**: Application pods crash, and node scheduling fails.
*   **Detection**: Logs show `No space left on device` errors.
*   **Recovery**: Purge historical log files and enable log rotation.
*   **Prevention**: Set disk limit policies and enforce log rotation rules.
*   **Monitoring**: Alert if disk usage exceeds 85% of limits.

### FS-44: Metrics Scrape Rate Limiting
*   **Cause**: Scrape frequencies exceed API metrics endpoint rate limits.
*   **Symptoms**: Exporters return HTTP 429 rate limit errors to Prometheus.
*   **Detection**: Prometheus logs show metrics query timeouts.
*   **Recovery**: Adjust Prometheus scrape intervals to reduce query rates.
*   **Prevention**: Whitelist Prometheus IP addresses in rate limit configurations.
*   **Monitoring**: Track metrics endpoint error rates.

### FS-45: Alert Rules Evaluation Timeout
*   **Cause**: Large metrics datasets cause Prometheus alert evaluations to timeout.
*   **Symptoms**: Alerts do not fire during outages.
*   **Detection**: Prometheus logs show `alert evaluation skipped due to timeout` warnings.
*   **Recovery**: Optimize alert queries to reduce data footprints.
*   **Prevention**: Set evaluation interval limits to at least 15 seconds.
*   **Monitoring**: Track metrics query latencies.

---

## Group 10: Infrastructure & Deployment Failures

### FS-46: Kubernetes Pod OOMKilled Exception
*   **Cause**: Application processes exceed container memory limits.
*   **Symptoms**: Pods terminate abruptly, returning HTTP 502 errors to clients.
*   **Detection**: Kubernetes logs show status `OOMKilled`.
*   **Recovery**: Restart the pods and increase memory allocation values.
*   **Prevention**: Set memory limits and profile process allocations.
*   **Monitoring**: Alert on `kube_pod_container_status_terminated_reason` changes.

### FS-47: HPA Scaling Lag
*   **Cause**: Traffic spikes outpace Kubernetes HPA scale-up rates.
*   **Symptoms**: API responses timeout due to container resource starvation.
*   **Detection**: HPA metrics show scale-up actions delayed by node provisioning times.
*   **Recovery**: Manually scale up deployment pod counts.
*   **Prevention**: Set lenient HPA scale thresholds and pre-provision backup nodes.
*   **Monitoring**: Alert on high CPU usage metrics during scale-up delays.

### FS-48: ConfigMap Validation Failures
*   **Cause**: YAML syntax errors prevent ConfigMaps from loading.
*   **Symptoms**: Pod launches fail, returning configuration load errors.
*   **Detection**: Kubernetes logs show `CreateContainerConfigError`.
*   **Recovery**: Fix the YAML syntax errors in the ConfigMap and redeploy.
*   **Prevention**: Validate Kubernetes configurations in CI/CD pipelines.
*   **Monitoring**: Track deployment launch failures.

### FS-49: SSL/TLS Handshake Timeout
*   **Cause**: Expired SSL certificates or configuration errors cause handshakes to fail.
*   **Symptoms**: Browsers reject HTTPS connection requests.
*   **Detection**: Logs show `SSL: CERTIFICATE_VERIFY_FAILED` errors.
*   **Recovery**: Renew and deploy updated SSL certificates.
*   **Prevention**: Enable automated certificate renewals using tools like Let's Encrypt.
*   **Monitoring**: Alert on certificate expiration dates.

### FS-50: Database Schema Migration Drift
*   **Cause**: Migrations are run out of order, leading to schema drifts across nodes.
*   **Symptoms**: Database queries fail due to missing columns or tables.
*   **Detection**: Logs show `ProgrammingError: column does not exist`.
*   **Recovery**: Run Alembic repair scripts to reconcile database schemas.
*   **Prevention**: Enforce sequential migration checks in CI/CD pipelines.
*   **Monitoring**: Verify database schemas against active models.
