# Feature Dependency Map

This document maps the relationships, prerequisites, shared services, and database tables for the 9 core features of the platform.

---

## 1. Feature Dependency Matrix

| Feature | Prerequisites | Downstream Dependents | Shared Services | Shared Tables |
| :--- | :--- | :--- | :--- | :--- |
| **Multi-Tenancy** | None. | All features. | `TenantService` | `tenants`, `users` |
| **Diagnostic quiz** | Multi-Tenancy | Roadmaps, Progress | `DiagnosticService` | `diagnostic_tests`, `user_answers` |
| **Roadmap Generator** | Diagnostic quiz | Progress, Mentor AI | `RoadmapService` | `roadmaps`, `roadmap_steps` |
| **Mentor AI Chat** | Roadmaps | None. | `MentorService` | `mentor_chat_messages` |
| **Progress Dashboards** | Roadmaps | None. | `AnalyticsService` | `analytics_snapshots`, `topic_scores` |
| **Community Forums** | Multi-Tenancy | None. | `CommunityService` | `discussion_threads`, `discussion_replies` |
| **Gamification Engine** | Diagnostic quiz | None. | `GamificationService` | `badges`, `user_badges` |
| **Ecosystem Plugins** | Multi-Tenancy | None. | `EcosystemService` | `api_clients`, `plugin_registry` |
| **Content Editors** | Multi-Tenancy | Diagnostics, Roadmaps | `TopicService` | `topics`, `questions` |

---

## 2. Feature Dependency Graph

```mermaid
flowchart TD
    Tenant["Multi-Tenant Isolation\n(Shared Service: TenantService)"] --> Auth["User Authentication\n(Shared Table: users)"]
    Auth --> Diagnostics["Adaptive Diagnostics\n(Shared Service: DiagnosticService)"]
    Auth --> Community["Community Forums\n(Shared Service: CommunityService)"]
    Auth --> Ecosystem["Ecosystem Plugins\n(Shared Service: EcosystemService)"]
    
    Diagnostics --> Roadmaps["Personalized Roadmaps\n(Shared Service: RoadmapService)"]
    Diagnostics --> Gamification["Gamification Engine\n(Shared Service: GamificationService)"]
    
    Roadmaps --> Mentor["Mentor AI Chat\n(Shared Service: MentorService)"]
    Roadmaps --> Dashboards["Progress Dashboards\n(Shared Service: AnalyticsService)"]
    
    Editors["Content Editors\n(Shared Service: TopicService)"] --> Diagnostics
    Editors --> Roadmaps
```

---

## 3. Shared APIs & Integration Scopes

*   `/auth/login` — The main gateway API; initializes tenant contexts and issues roles.
*   `/analytics/event` — Aggregates user telemetry logs across dashboards and roadmaps.
*   `/ops/outbox` — Processes and dispatches outbox table items to keep databases and caches in sync.
