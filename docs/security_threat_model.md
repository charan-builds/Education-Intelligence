# Security Threat Model

This document outlines the security threat model for the platform. It details the assets, attack surfaces, trust boundaries, threat actors, abuse cases, mitigations, and residual risks, mapping findings to both **STRIDE** and **OWASP** frameworks.

---

## 1. Threat Modeling Parameters

### Core Assets
*   **Tenant Data**: Private learning content, student metrics, and course completions.
*   **User Credentials**: Email addresses, passwords, and multi-factor authentication (MFA) keys.
*   **Session Tokens**: Active JWT access and refresh tokens.
*   **Content Bank**: Topic graphs, quiz questions, and diagnostic answers.
*   **Audit Trails**: Immutable logs of administrative actions.

### Attack Surfaces
*   **Authentication Routes**: Login, registration, and password reset endpoints.
*   **Websocket Interfaces**: Real-time messaging connections.
*   **Mentor Chat Interface**: Text prompt inputs to the AI mentor.
*   **File Upload Routes**: Upload URLs and asset directories.

---

## 2. Trust Boundaries

```text
  [ Client Browser ] (Untrusted)
        │
  =========================== HTTP Request / SSL boundary ===========================
        ▼
  [ Nginx Proxy Gateway ] (Edge Trusted)
        │
  =========================== Internal Network boundary ===========================
        ▼
  [ FastAPI Monolith Backend ] (App Trusted)
        │
  =========================== Database Session boundary ============================
        ▼
  [ PostgreSQL Database (RLS active) ] (Fully Trusted)
```

---

## 3. STRIDE Threat Mapping

| Threat Category | Target Vector | Mitigation in Place |
| :--- | :--- | :--- |
| **S**poofing | Attacker logs in as a user. | MFA TOTP validation and password bcrypt checks. |
| **T**ampering | Modifying API headers during transmission. | HTTPS redirects and TLS 1.3 encryption. |
| **R**epudiation | Admin denies executing a change. | Immutable logs in the audit table. |
| **I**nformation Disclosure | Cross-tenant data leaks. | PostgreSQL RLS policies. |
| **D**enial of Service | API request spam. | Redis-backed token bucket rate limits. |
| **E**levation of Privilege | Student executes admin functions. | RBAC middleware checks. |

---

## 4. Abuse Cases & Mitigations

### Abuse Case: Prompt Injection Attack
*   **Scenario**: User prompt contains injection phrases (e.g. `ignore previous instructions`) to expose system prompts or system contexts.
*   **Mitigation**: Implement input sanitizers to check for injection indicators before calling the model.

### Abuse Case: Cross-Tenant Data Access
*   **Scenario**: Attacker updates query parameters to fetch data from other tenants.
*   **Mitigation**: Enable database-level RLS policies, automatically filtering queries based on the active connection's tenant context.

---

## 5. Residual Risks & OWASP Top 10 Mapping

*   **RLS Gaps (A01:2021-Broken Access Control)**: Operational tables (e.g. `ml_feature_snapshots`) currently bypass RLS, relying instead on manual query filters.
*   **XSS Vulnerability (A03:2021-Injection)**: Forum threads render user inputs without sanitization. DOMPurify libraries must be integrated into frontend renderers.
*   **Stateless Token Exceedance (A02:2021-Cryptographic Failures)**: If access tokens are compromised, they remain valid until they expire. Short access token lifespans (15 mins) must be enforced.
