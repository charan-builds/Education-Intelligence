# Debugging Handbook

This handbook provides instructions for troubleshooting and debugging the core modules of the **Learning Intelligence Platform** backend.

---

## 1. Authentication & JWT Session Engine

### Common Bug: Session Expired during Action
*   **Symptom**: Users receive HTTP 401 Unauthorized errors during active sessions.
*   **Reproduction Steps**:
    1.  Log in to get access and refresh tokens.
    2.  Set the system clock forward by 35 minutes on the client machine.
    3.  Submit a request (e.g. marking a roadmap step complete).
*   **Debugging Workflow**:
    1.  Inspect [auth_routes.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/presentation/auth_routes.py) and confirm that headers contain valid Bearer tokens.
    2.  Attach a breakpoint inside the token validation logic in [security.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/core/security.py) (e.g., `decode_access_token`).
*   **Relevant Logs**:
    *   `app.core.security: JWT access token expired (sub=user-uuid)`
*   **Fix Strategy**: Check that token refresh queries are running in the frontend API client interceptor.

---

## 2. Multi-Tenancy & RLS Context Isolation

### Common Bug: Cross-Tenant Data Leak
*   **Symptom**: User queries return records belonging to other tenants.
*   **Reproduction Steps**:
    1.  Register User A on Tenant 1, and User B on Tenant 2.
    2.  Use User B's active token to send a request to a route (e.g. `GET /goals`).
    3.  Verify if the returned goals array contains records from Tenant 1.
*   **Debugging Workflow**:
    1.  Inspect [tenant_rls.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/tenant_rls.py) and confirm that session context variables are set.
    2.  Attach a breakpoint inside `set_db_tenant_context` to verify parameter assignments.
*   **Relevant Logs**:
    *   `app.infrastructure.tenant_rls: RLS session context initialized (tenant_id=tenant-uuid)`
*   **Fix Strategy**: Verify that the table containing the queried model has PostgreSQL RLS enabled.

---

## 3. Adaptive Diagnostics & Quiz Engine

### Common Bug: Question Pool Exhaustion Index Error
*   **Symptom**: Diagnostic quiz routes fail, returning HTTP 500 errors.
*   **Reproduction Steps**:
    1.  Start a diagnostic test with question count set to 20.
    2.  Answer all questions correctly in sequence.
    3.  Verify if the next question endpoint fails on the 15th question.
*   **Debugging Workflow**:
    1.  Inspect [adaptive_testing_engine.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/domain/engines/adaptive_testing_engine.py).
    2.  Attach a breakpoint inside `select_next_item` to trace query logic.
*   **Relevant Logs**:
    *   `app.domain.engines.adaptive_testing_engine: IndexError: list index out of range`
*   **Fix Strategy**: Implement fallback rules to select questions from parent topics when exact matches are missing.

---

## 4. Content Graph & Roadmap Generator

### Common Bug: Circular Prerequisite Dependency Loop
*   **Symptom**: Roadmap generation requests loop infinitely, causing container timeouts.
*   **Reproduction Steps**:
    1.  Create Topic A, and set Topic B as its prerequisite.
    2.  Modify Topic B, and set Topic A as its prerequisite.
    3.  Submit a roadmap generation request.
*   **Debugging Workflow**:
    1.  Inspect [knowledge_graph.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/domain/engines/knowledge_graph.py).
    2.  Attach a breakpoint inside the topological sort module.
*   **Relevant Logs**:
    *   `app.domain.engines.knowledge_graph: Infinite loop detected during topological sort`
*   **Fix Strategy**: Implement cycle detection checks in the prerequisite creation route.

---

## 5. Supervisor-Specialist AI Agent Routing

### Common Bug: AI JSON Parse Failure
*   **Symptom**: Chats fail, returning parsing errors to the user.
*   **Reproduction Steps**:
    1.  Submit a complex prompt to the mentor chat.
    2.  Force the LLM to output a response containing invalid JSON syntax.
*   **Debugging Workflow**:
    1.  Inspect [service.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/service.py).
    2.  Attach a breakpoint inside the JSON parsing logic.
*   **Relevant Logs**:
    *   `ai_service.service: JSONDecodeError: Expecting property name enclosed in double quotes`
*   **Fix Strategy**: Enforce strict JSON output schemas (like OpenAI Structured Outputs).

---

## 6. Transactional Outbox & Celery Workers

### Common Bug: Duplicate Task Execution
*   **Symptom**: Background jobs run twice simultaneously.
*   **Reproduction Steps**:
    1.  Start multiple Celery Beat containers.
    2.  Verify if scheduled tasks are scheduled twice.
*   **Debugging Workflow**:
    1.  Inspect [celery_app.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/celery_app.py).
    2.  Attach a breakpoint inside the task scheduler.
*   **Relevant Logs**:
    *   `app.infrastructure.jobs.tasks: Task scheduled twice for event ID`
*   **Fix Strategy**: Enforce singleton deployments for Celery Beat.
