# Design Patterns Catalog

This document details the software design patterns implemented across the codebase, explaining their purpose, locations, pros/cons, and alternatives.

---

## 1. The Repository Pattern

### Where It Appears
*   Implemented across all repositories inside [repositories/](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/).

### Why It Was Chosen
To isolate business services from database access details. Service classes read and write models using simple repository methods (e.g. `UserRepository.find_by_email`), keeping database queries out of service files.

### Advantages & Disadvantages
*   **Advantage**: Keeps database queries out of service files and simplifies unit testing by allowing developers to mock repositories easily.
*   **Disadvantage**: Adds boilerplate code; developers must write both repository files and service files to add new database queries.

### Alternatives Considered
*   **Active Record Pattern**: Let models handle their own save and query operations (like Django ORM). This was rejected because SQLAlchemy's Data Mapper pattern separates models from database sessions more cleanly.

### Repository Example
Open [user_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/user_repository.py):
```python
class UserRepository(BaseRepository[User]):
    async def find_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalars().first()
```

---

## 2. The Transactional Outbox Pattern

### Where It Appears
*   Implemented inside the outbox modules: [outbox_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/outbox_service.py) and [outbox_repository.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/infrastructure/repositories/outbox_repository.py).

### Why It Was Chosen
To solve the dual-write consistency problem. When data is saved to the database, the system must also notify external systems (like caches or search indexes). Writing to the database and publishing to a message broker in the same API route can lead to inconsistencies if network failures occur. The outbox pattern writes events to the database atomically in the same transaction, processing them asynchronously in a background loop.

### Advantages & Disadvantages
*   **Advantage**: Guarantees at-least-once message delivery and prevents broker failures from blocking database writes.
*   **Disadvantage**: Adds write overhead to database transactions and introduces eventual consistency delays.

### Alternatives Considered
*   **Synchronous Publishing**: Publish messages directly inside API routes. Rejected due to the risk of data drift if network connections fail.

### Repository Example
Open [outbox_service.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/application/services/outbox_service.py):
```python
async def save_outbox_event(session: AsyncSession, event_type: str, payload: dict) -> None:
    event = OutboxEvent(
        event_type=event_type,
        payload=payload,
        status="PENDING"
    )
    session.add(event)
```

---

## 3. The Supervisor-Specialist (Mediator) Pattern

### Where It Appears
*   Implemented inside the AI routing orchestrator [ai_service/service.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/service.py).

### Why It Was Chosen
To coordinate prompts across specialized AI agents. Instead of running a single generalist prompt, the supervisor agent routes inputs dynamically to specialized agents (Analytics, Motivation, Career Guide) based on intent keywords, merging their outputs into a single response.

### Advantages & Disadvantages
*   **Advantage**: Reduces hallucinations and improves output quality by using specialized prompts.
*   **Disadvantage**: Multiple agent runs increase API request latency and token costs.

### Alternatives Considered
*   **Single Prompt Agent**: Using a single system prompt to handle all roles. Rejected due to high hallucination rates and lower response quality.

### Repository Example
Open [ai_service/service.py](file:///home/charan_derangula/projects/intelligentSystems/ai_service/service.py):
```python
def _route_agents(self, payload: MentorResponseRequest) -> list[str]:
    routed = ["mentor_agent"]
    message = payload.message.lower()
    if "progress" in message:
        routed.append("analytics_agent")
    if "career" in message:
        routed.append("career_advisor_agent")
    return routed
```

---

## 4. The Dependency Injection Pattern

### Where It Appears
*   FastAPI dependencies declared inside [dependencies.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/core/dependencies.py).

### Why It Was Chosen
To manage resource Lifecycles (like database sessions and user auth states) cleanly. FastAPI's `Depends` decorator injects database sessions and verifies user roles before routing requests, keeping validation code out of service files.

### Advantages & Disadvantages
*   **Advantage**: Simplifies unit testing by allowing developers to override dependencies easily.
*   **Disadvantage**: Dependencies are resolved at runtime; errors in dependency configurations can pass compile checks and fail in production.

### Alternatives Considered
*   **Global Variables**: Using global database session objects. Rejected due to the risk of connection leaks and difficulties testing.

### Repository Example
Open [dependencies.py](file:///home/charan_derangula/projects/intelligentSystems/backend/app/core/dependencies.py):
```python
async def get_current_user(
    db: AsyncSession = Depends(get_db_session),
    token: str = Depends(oauth2_scheme)
) -> User:
    user = await UserService(db).get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user
```
