# Domain Model Guide

This guide details the core entities of the platform's domain model, explaining their business meaning, relationships, lifecycles, validation constraints, and typical operations.

---

## 1. Tenant Entity

### Business Meaning
Represents the organizational boundaries (e.g. schools, universities, or corporate training departments) that define user workspaces and content parameters.

### Relationships
*   Has many **Users** registered under its namespace.
*   Has many **Topics** and **Goals** curated by its administrators.

### Lifecycle States
```text
[ Draft / Provisioning ] ──> [ Active / Running ] ──> [ Suspended / Deactivated ]
```

### Invariants & Constraints
*   Identifiers must be unique across the platform.
*   Deactivation suspends access for all users linked to the tenant.

### Typical Operations
*   `create_tenant`: Provisions a new tenant account and seeds default schemas.
*   `suspend_tenant`: Suspends tenant access and denies logins.

---

## 2. DiagnosticTest Entity

### Business Meaning
Represents a timed assessment session taken by a student to identify their baseline strengths and weaknesses.

### Relationships
*   Belongs to a **User** (the student taking the test).
*   Belongs to a **Goal** (defining the scope of the questions).
*   Has many **UserAnswers** logged during the session.

### Lifecycle States
```text
[ Initialized ] ──> [ Question Active ] ──> [ Answered / Next Step ] ──> [ Finalized ]
```

### Invariants & Constraints
*   Diagnostic sessions are limited to one active question at a time.
*   Answers submitted after the session is finalized are rejected.

### Typical Operations
*   `start_diagnostic`: Initializes a test session and selects initial questions.
*   `submit_answer`: Records an answer and updates the active test state.

---

## 3. Roadmap Entity

### Business Meaning
Represents a personalized, chronologically ordered path of topics designed to guide a student toward their goals.

### Relationships
*   Belongs to a **User** (the student following the path).
*   Belongs to a **Goal** (defining the learning target).
*   Has many **RoadmapSteps** representing individual topics.

### Lifecycle States
```text
[ Generated ] ──> [ Active / Progressing ] ──> [ Completed ]
```

### Invariants & Constraints
*   Steps cannot be started until all of their prerequisites have been completed.

### Typical Operations
*   `generate_roadmap`: Traverses prerequisites to create a learning path.
*   `complete_step`: Marks a step completed and unlocks dependent topics.

---

## 4. OutboxEvent Entity

### Business Meaning
Represents an asynchronous event payload saved to the database during a transaction to be processed by background workers.

### Relationships
*   None.

### Lifecycle States
```text
[ Pending ] ──> [ Processing / Locked ] ──> [ Processed ] OR [ Failed / Retry ] ──> [ Dead-Letter ]
```

### Invariants & Constraints
*   Payloads must be valid JSON objects.
*   Retries are capped at 5 attempts before the event is moved to the dead-letter queue.

### Typical Operations
*   `save_event`: Saves a new event to the outbox table.
*   `mark_processed`: Updates event status to processed after successful dispatch.
