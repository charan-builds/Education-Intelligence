# Master Product Document

This document outlines the product vision, market positioning, user journeys, success metrics, and product roadmap for the **Learning Intelligence Platform**.

---

## 1. Executive Summary & Problem Statement

### The Problem
Traditional Learning Management Systems (LMS) treat learning as a linear process, serving the same content to all students regardless of their background knowledge. This results in high dropout rates (often exceeding 90% in self-paced courses) and choice paralysis, as students struggle to identify what to study next.

### Our Solution
The platform provides a **personalized, adaptive learning experience**:
1.  **Adaptive Diagnostics**: Evaluates student understanding dynamically to map knowledge gaps.
2.  **Personalized Roadmaps**: Generates step-by-step learning paths based on prerequisite graphs.
3.  **On-Demand AI Mentoring**: Provides real-time guidance tailored to the student's progress.

---

## 2. User Roles & Personas

### Student (The Directed Learner)
*   **Need**: Needs clear, step-by-step guidance to pass courses and complete study milestones.
*   **Pain Point**: Overwhelmed by large curricula; gets stuck on exercises outside of classroom hours.
*   **Journey**: Starts diagnostics $\rightarrow$ reviews roadmap steps $\rightarrow$ takes quizzes $\rightarrow$ completes milestones.

### Teacher (The Curator)
*   **Need**: Needs to monitor student progress and update course materials.
*   **Pain Point**: Hard to identify which students are falling behind in large classes.
*   **Journey**: Accesses dashboard $\rightarrow$ reviews student metrics $\rightarrow$ updates topic prerequisites.

### Enterprise Administrator (The Buyer)
*   **Need**: Needs to manage corporate workspaces and verify training ROI.
*   **Pain Point**: Lack of visibility into training effectiveness and data security concerns.
*   **Journey**: Provisions tenant $\rightarrow$ configures SSO parameters $\rightarrow$ reviews compliance reports.

---

## 3. Product Philosophy & Design Core

*   **Diagnostics Before Content**: Assess student baseline understanding before serving learning materials.
*   **Graph-Driven Progression**: Guide student study paths using database-enforced topic prerequisite relationships.
*   **On-Demand AI Guidance**: Position the AI as a supportive mentor that explains errors and guides studies rather than simply giving answers.

---

## 4. Feature Roadmap

```text
========================================================================
[V1: Core Personalization]           │ [V2: Enterprise Scale]
------------------------------------ │ ----------------------------------
- Multi-Tenant Workspace Isolation   │ - Self-Service SSO Integrations
- Adaptive Diagnostic Quizzes        │ - Automated Gradebook Sync (LTI)
- Personal Learning Roadmaps         │ - Local AI Model Registries
- Interactive AI Mentor Chat         │ - Visual Prerequisite Graph Editors
========================================================================
```

### V1: Core Personalization (Current Base)
*   Multi-tenant workspace isolation.
*   Adaptive diagnostic assessments using Item Response Theory.
*   Personalized learning roadmaps with locked and unlocked step states.
*   On-demand AI mentor chat with safety guardrails and fallback modes.

### V2: Enterprise Scale (6-12 Months)
*   Self-service single sign-on (SSO) integrations for tenant admins.
*   Automated gradebook sync with external LMS systems (Canvas, Moodle).
*   Visual, drag-and-drop prerequisite graph editors for teachers.
*   Local LLM deployments to guarantee data privacy and lower API token bills.

---

## 5. Competitor Comparison

| Product Vector | Traditional LMS (Canvas/Moodle) | Online Course Platforms (Coursera/Udemy) | Our Platform |
| :--- | :--- | :--- | :--- |
| **Learning Path** | Linear / Uniform. | Static / Self-selected. | **Dynamic / Adaptive**. |
| **Diagnostics** | Static entry exams. | None. | **Real-Time Ability Scoring**. |
| **Tutoring Support**| Human forums only. | None. | **Interactive AI Mentor**. |
| **Data Isolation** | Single-tenant server clusters. | Shared database. | **PostgreSQL Database RLS**. |

---

## 6. Success Metrics & KPIs

*   **User Activation Rate**: Percentage of registered users starting their roadmaps within 24 hours of completing diagnostics.
*   **Roadmap Completion Rate**: Percentage of created roadmaps completed by users.
*   **Chat Session Resolution Rate**: Percentage of chat sessions ending in helpful ratings.
*   **Tenant Churn Rate**: Percentage of organizations canceling workspace subscriptions.
*   **Monthly Active Users (MAU)**: Count of unique active users logging in each month.

---

## 7. Product Risks & Opportunities

### Risks
*   **External LLM Dependencies**: High reliance on external LLM APIs exposes the platform to provider downtime and latency issues.
*   **Data Leakage Liability**: A data breach in a shared-database multi-tenant platform can lead to immediate customer churn and legal liability.

### Opportunities
*   **AI Curriculum Generation**: Build tools to automatically generate lessons, quiz questions, and prerequisite paths from textbook uploads.
*   **Predictive Attrition Modeling**: Use machine learning to identify students at risk of dropping out before they abandon their courses.
