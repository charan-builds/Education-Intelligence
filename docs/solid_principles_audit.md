# SOLID Principles Audit Report

This report documents the architectural audit of the platform backend against the five **SOLID** principles of software engineering.

---

## 1. Single Responsibility Principle (SRP)

### Definition
A class should have one, and only one, reason to change.

### Compliance Example
Open [adaptive_testing_engine.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/domain/engines/adaptive_testing_engine.py):
*   **Why**: The `AdaptiveTestingEngine` class focuses entirely on mathematical calculations to evaluate student ability scores ($\theta$) and select the next questions. It does not perform database query actions or parse HTTP schemas, keeping it focused on a single responsibility.

### Violation Example
Open [auth_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/auth_service.py):
*   **Why**: The `AuthService` class handles user registration, credentials verification, password hashing, invite validations, MFA configurations, session logging, and welcome email queues in a single file. Modifying email template styles requires changing the authentication service file.

---

## 2. Open/Closed Principle (OCP)

### Definition
Software entities should be open for extension, but closed for modification.

### Compliance Example
Open [distributed_bus.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/realtime/distributed_bus.py):
*   **Why**: The realtime message bus exposes generic subscriber register functions. Developers can add new message channels without modifying the core bus class file.

### Violation Example
Open [ai_service/service.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/service.py):
*   **Why**: The `_route_agents` routing method uses hardcoded keyword matches. Adding a new agent requires modifying the core routing file, violating the open/closed principle.

---

## 3. Liskov Substitution Principle (LSP)

### Definition
Subtypes must be substitutable for their base types without breaking application logic.

### Compliance Example
Open [user_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/user_repository.py):
*   **Why**: The `UserRepository` class inherits from `BaseRepository[User]`. It extends base methods without changing their parameter types or return signatures, ensuring it remains substitutable.

### Violation Example
Open [tests/conftest.py](file:///home/charan_derangula/projects/intelligentSystems/backend/tests/conftest.py):
*   **Why**: Certain mock repository classes used in tests return dictionaries instead of SQLAlchemy model entities. Calling code that expects model attributes (e.g. `user.id`) fails when given dict keys, violating Liskov substitution rules.

---

## 4. Interface Segregation Principle (ISP)

### Definition
Clients should not be forced to depend on methods they do not use.

### Compliance Example
Open [auth_schema.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/schemas/auth_schema.py):
*   **Why**: Pydantic schemas are split into granular models (e.g., `LoginRequest`, `RegisterRequest`, `OTPRequest`). Routers only consume the specific properties they require, keeping validation interfaces segregated.

### Violation Example
Open [base_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/base_repository.py):
*   **Why**: The base repository class exposes all CRUD write operations (`create`, `update`, `delete`). Read-only repository subclasses (like `AuthLogRepository`) still inherit these write methods, exposing operations they do not require.

---

## 5. Dependency Inversion Principle (DIP)

### Definition
High-level modules should not depend on low-level modules. Both should depend on abstractions.

### Compliance Example
Open [dependencies.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/core/dependencies.py):
*   **Why**: API routes do not import database connections directly; they depend on abstract sessions (`get_db_session`) injected at runtime, decoupling routing code from database engines.

### Violation Example
Open [diagnostic_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/diagnostic_service.py):
*   **Why**: Service classes instantiate concrete repositories (`DiagnosticRepository`) directly instead of depending on abstract interfaces. This tightly couples the business layer to the database framework.
