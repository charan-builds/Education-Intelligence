# Master User Flows Document

This document details the step-by-step lifecycles, features, user friction points, dead ends, and improvements for all 5 user roles on the platform.

---

## 1. Student User Journey

### A. Login & Onboarding Journeys
1.  **Login**: Enters email and password on the tenant subdomain login page.
2.  **Onboarding**: Selects a primary goal (e.g. "Full Stack Developer"), which triggers an **Adaptive Diagnostic Assessment** to establish baseline understanding.

### B. Dashboard & Daily Workflow
1.  **Dashboard**: Displays the active learning roadmap, completion progress bar, next recommended topic card, active streak counter, and direct chat mentor launcher.
2.  **Daily Workflow**:
    *   Clicks the next unlocked roadmap step.
    *   Reads the lesson content and completes practice questions.
    *   If stuck, launches the AI chat mentor to ask for clarification.
    *   Submits topic reviews to unlock subsequent roadmap steps.

### C. UX Friction & Future Improvements
*   **Dead Ends**: If a student exhausts the question pool, the diagnostic quiz returns a raw index error rather than a clean message.
*   **Missing Screens**: Lack of an interactive visual prerequisite graph view on the dashboard.
*   **Future Improvements**: Implement drag-and-drop roadmap rescheduling.

---

## 2. Teacher User Journey

### A. Login & Onboarding Journeys
1.  **Login**: Authenticates via the administrator portal.
2.  **Onboarding**: Selects assigned class cohorts and reviews default course syllabus graphs.

### B. Dashboard & Daily Workflow
1.  **Dashboard**: Displays class average mastery scores, student risk alerts (identifying students falling behind), and active course graphs.
2.  **Daily Workflow**:
    *   Reviews cohort progress and performance metrics.
    *   Responds to study questions in community discussion boards.
    *   Modifies topic prerequisite graphs or adds questions to pools.

### C. UX Friction & Future Improvements
*   **Dead Ends**: Modifying a prerequisite graph does not validate circular dependencies, which can lock student roadmaps.
*   **Missing Screens**: Lack of an interactive preview dashboard to view roadmaps from a student's perspective.
*   **Future Improvements**: Integrate AI distractor recommendations in question creation forms.

---

## 3. Administrator User Journey

### A. Login & Onboarding Journeys
1.  **Login**: Authenticates via the secure tenant administrator route.
2.  **Onboarding**: Configures corporate branding and invites student directories.

### B. Dashboard & Daily Workflow
1.  **Dashboard**: Displays active subscription seats, platform engagement rates, and integration sync statuses.
2.  **Daily Workflow**:
    *   Manages user licenses and permissions.
    *   Reviews platform activity logs and analytics.
    *   Configures ecosystem integrations and directory sync rules.

### C. UX Friction & Future Improvements
*   **Dead Ends**: Deactivating a user does not immediately revoke their active JWT access tokens, creating a 30-minute security window.
*   **Missing Screens**: Lack of self-service single sign-on (SSO) configuration portals.
*   **Future Improvements**: Build dashboard compliance audits.

---

## 4. Mentor User Journey

### A. Login & Onboarding Journeys
1.  **Login**: Authenticates using mentor credentials.
2.  **Onboarding**: Configures availability times and expertise domains.

### B. Dashboard & Daily Workflow
1.  **Dashboard**: Displays pending chat escalation queues and active student help requests.
2.  **Daily Workflow**:
    *   Intercepts escalated chat sessions when the AI mentor fails to resolve a query.
    *   Provides direct guidance to students via chat interfaces.
    *   Logs student study recommendations.

### C. UX Friction & Future Improvements
*   **Dead Ends**: Handing a session back to the AI mentor can result in context desynchronization.
*   **Missing Screens**: Lack of a shared whiteboard view to explain diagrams in real-time.
*   **Future Improvements**: Build dashboard integration widgets.

---

## 5. Super Administrator User Journey

### A. Login & Onboarding Journeys
1.  **Login**: Authenticates via the primary global management portal.
2.  **Onboarding**: Accesses tenant lists.

### B. Dashboard & Daily Workflow
1.  **Dashboard**: Displays global platform server health metrics, database connection pool loads, and tenant list dashboards.
2.  **Daily Workflow**:
    *   Provisions new tenant workspaces.
    *   Manages database schema updates and migrations.
    *   Monitors security logs and system alerts.

### C. UX Friction & Future Improvements
*   **Dead Ends**: Running schema updates on active databases can block concurrent tenant transactions.
*   **Missing Screens**: Lack of a global tenant billing management portal.
*   **Future Improvements**: Enforce automated read-only database locks during updates.
