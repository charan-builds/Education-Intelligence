# React Component Intelligence Catalog

This document details the React components in the Next.js frontend (`learning-platform-frontend/`) of the **Learning Intelligence Platform**. It outlines component layout structures, React properties, state flows, hooks, and performance parameters.

---

## 1. Design Tokens (`components/ui/`)

| Component Class | Source File | Parent Component | Core Purpose |
| :--- | :--- | :--- | :--- |
| `Button` | [Button.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/components/ui/Button.tsx) | Global imports | Renders standard buttons with loading indicators. |
| `Input` | [Input.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/components/ui/Input.tsx) | Forms | Custom wrapper for text input layouts. |
| `Select` | [Select.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/components/ui/Select.tsx) | Forms | Renders select dropdown dropdown elements. |
| `Skeleton` | [Skeleton.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/components/ui/Skeleton.tsx) | SmartLoadingState | Loading animation placeholders. |
| `StatusPill` | [StatusPill.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/components/ui/StatusPill.tsx) | RoadmapStepCard | Visual state indicators (e.g. active, complete). |
| `ThemeToggle` | [ThemeToggle.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/components/ui/ThemeToggle.tsx) | SidebarNav | Toggles Light vs. Dark modes. |
| `Card` | [card.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/components/ui/card.tsx) | Dashboards | Structured information container frames. |
| `Modal` | [modal.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/components/ui/modal.tsx) | Dialog grids | Pop-up overlay frames. |

### Primary Component Detail: `Button`
*   **Purpose**: Renders uniform, interactive button components with variant-based tailwind states and loading indicators.
*   **Props**:
    ```typescript
    interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
      variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
      size?: 'sm' | 'md' | 'lg';
      isLoading?: boolean;
    }
    ```
*   **State**: None (controlled component).
*   **Hooks**: None.
*   **Children**: Text labels or SVG icons.
*   **Parent**: Importer parent page views.
*   **API Calls**: None.
*   **Performance**: Renders in under 0.5ms; uses memoization to prevent rendering calculations if properties match.
*   **Reusability**: Highly reusable; acts as the primary action trigger throughout the UI.
*   **Accessibility**: Implements keyboard tab indexing and includes target descriptions (`aria-label`, `aria-busy` when loading).
*   **Testing**: Asserts click actions and loading state disabled locks in `Button.test.tsx`.

---

## 2. Dashboard Widgets (`components/dashboard/`)

| Component Class | Source File | Parent Component | Core Purpose |
| :--- | :--- | :--- | :--- |
| `ActivityFeed` | [ActivityFeed.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/components/dashboard/ActivityFeed.tsx) | Dashboard layout | Logs student timeline events. |
| `RecommendationPanel` | [RecommendationPanel.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/components/dashboard/RecommendationPanel.tsx) | Dashboard layout | Suggests revision topics based on scores. |

### Primary Component Detail: `ActivityFeed`
*   **Purpose**: Renders a vertical list showing a student's learning timeline (e.g. topic completions, quizzes taken).
*   **Props**: `activities: ActivityItem[]`
*   **State**: None.
*   **Hooks**: `useTranslation` (supports multilingual formatting).
*   **Children**: Individual log items.
*   **Parent**: Dashboard wrapper components.
*   **API Calls**: None (reads cached query values).
*   **Performance**: Limits renders using viewport virtualization rules if feeds exceed 50 entries.
*   **Reusability**: Shared across student and teacher dashboard views.
*   **Accessibility**: Outlines timeline events inside standard screen reader containers (`role="log"`).
*   **Testing**: Asserts that logs are sorted by date parameters in `ActivityFeed.test.tsx`.

---

## 3. Assessment Components (`features/diagnostic/`)

| Component Class | Source File | Parent Component | Core Purpose |
| :--- | :--- | :--- | :--- |
| `DiagnosticQuiz` | [DiagnosticQuiz.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/features/diagnostic/DiagnosticQuiz.tsx) | Student layout | Orchestrates timed quiz questions. |

### Primary Component Detail: `DiagnosticQuiz`
*   **Purpose**: Handles multi-step, timed question renders for student diagnostic sessions.
*   **Props**: `goalId: number`
*   **State**: `currentQuestionIndex: number`, `selectedOption: number | null`
*   **Hooks**: `useDiagnosticTestStore`, `useDiagnosticCountdown`
*   **Children**: `DiagnosticTimer`, `QuestionRenderer`, `Button`
*   **Parent**: Diagnostic assessment page.
*   **API Calls**: `diagnosticService.submitAnswer`, `diagnosticService.finalizeTest`
*   **Performance**: Renders conditionally to prevent updating unrelated layout nodes on timer ticks.
*   **Reusability**: Isolated to the diagnostic test page.
*   **Accessibility**: Implements keyboard navigation listeners to select options (using number keys) and submits options (using the enter key).
*   **Testing**: E2E Playwright verification scenarios in `learner-journey.spec.ts`.

---

## 4. Learning Roadmaps (`features/roadmap/`)

| Component Class | Source File | Parent Component | Core Purpose |
| :--- | :--- | :--- | :--- |
| `RoadmapViewer` | [RoadmapViewer.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/features/roadmap/RoadmapViewer.tsx) | Roadmap layout | Displays steps in the student learning path. |

### Primary Component Detail: `RoadmapViewer`
*   **Purpose**: Renders a step-by-step pathway showing student goals and completed topics.
*   **Props**: `roadmap: RoadmapData`
*   **State**: `expandedStepId: string | null`
*   **Hooks**: `useMutation` (submits completed steps to the backend).
*   **Children**: `RoadmapStepCard`, `PrerequisiteList`, `StatusPill`
*   **Parent**: Learning roadmap viewer page.
*   **API Calls**: `roadmapService.completeStep`
*   **Performance**: Uses CSS transitions for expansion panels to avoid layout shifting.
*   **Reusability**: Shared across student dashboards and teacher overview pages.
*   **Accessibility**: Includes keyboard accordion controls (`aria-expanded`, `aria-controls` for step details).
*   **Testing**: Asserts step complete mutations in `RoadmapViewer.test.tsx`.

---

## 5. AI Chat & Mentors (`components/chat/` & `components/mentor/`)

| Component Class | Source File | Parent Component | Core Purpose |
| :--- | :--- | :--- | :--- |
| `MentorChatBox` | [MentorChatBox.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/components/mentor/MentorChatBox.tsx) | Mentor layout | Chat console interface for student prompts. |

### Primary Component Detail: `MentorChatBox`
*   **Purpose**: Exposes a chat interface to send text queries and stream AI advice logs.
*   **Props**: None.
*   **State**: `inputMessage: string`, `isTyping: boolean`
*   **Hooks**: `useMutation` (dispatches chat prompt data).
*   **Children**: `ChatHistoryList`, `MentorMessageListItem`, `Button`
*   **Parent**: Chat panel container.
*   **API Calls**: `mentorService.sendChatMessage`
*   **Performance**: Renders incoming chat threads asynchronously; scrolls layout views to the bottom on updates.
*   **Reusability**: Used in student mentor sidebars.
*   **Accessibility**: Focuses the input box on load; includes aria-live alerts to read out incoming AI messages.
*   **Testing**: Asserts message updates and list rendering states in `MentorChatBox.test.tsx`.

---

## 6. Community Forums (`components/community/`)

| Component Class | Source File | Parent Component | Core Purpose |
| :--- | :--- | :--- | :--- |
| `ThreadList` | [ThreadList.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/components/community/ThreadList.tsx) | Forums page | Displays forum discussion titles. |

### Primary Component Detail: `ThreadList`
*   **Purpose**: Renders threads registered under the student's active tenant community workspace.
*   **Props**: `threads: DiscussionThread[]`
*   **State**: `filterTag: string`
*   **Hooks**: `useQuery` (fetches community threads).
*   **Children**: `ThreadCard`, `StatusPill`
*   **Parent**: Community page views.
*   **API Calls**: `communityService.fetchThreads`
*   **Performance**: Memoizes filtered lists to avoid recalculations.
*   **Reusability**: Shared across tenant student forum pages.
*   **Accessibility**: Implements structured keyboard lists (`role="list"`, `role="listitem"`).
*   **Testing**: Asserts thread tag filtering in `ThreadList.test.tsx`.

---

## 7. System Layout Shells (`components/layout/`)

| Component Class | Source File | Parent Component | Core Purpose |
| :--- | :--- | :--- | :--- |
| `DashboardLayoutShell` | [DashboardLayoutShell.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/components/layouts/DashboardLayoutShell.tsx) | Layout routes | Renders headers, sidebars, and grid containers. |

### Primary Component Detail: `DashboardLayoutShell`
*   **Purpose**: Renders sidebars, header blocks, and scrollable container frames across dashboard pages.
*   **Props**: `children: React.ReactNode`
*   **State**: `isSidebarOpen: boolean`
*   **Hooks**: `useAuth`
*   **Children**: `SidebarNav`, `HeaderBar`
*   **Parent**: Router groups layout context.
*   **API Calls**: None.
*   **Performance**: Uses CSS flex columns to adjust layout sizes without trigger re-renders.
*   **Reusability**: Wrapper layout used by all role-based folders.
*   **Accessibility**: Skip-to-content links bypass nav menus; includes landmark outlines (`<header>`, `<main>`, `<nav>`).
*   **Testing**: Asserts sidebar toggle transitions in `DashboardLayoutShell.test.tsx`.

---

## 8. Operational & Admin Controls (`components/ops/`)

| Component Class | Source File | Parent Component | Core Purpose |
| :--- | :--- | :--- | :--- |
| `FeatureFlagManager` | [FeatureFlagManager.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/components/ops/FeatureFlagManager.tsx) | Admin page | Toggles application feature states. |

### Primary Component Detail: `FeatureFlagManager`
*   **Purpose**: Renders flag variables (active, inactive) and coordinates changes.
*   **Props**: None.
*   **State**: `flagSearchQuery: string`
*   **Hooks**: `useMutation`, `useQuery`
*   **Children**: `MetricCard`, `Button`
*   **Parent**: Operations settings page.
*   **API Calls**: `opsService.updateFeatureFlag`
*   **Performance**: Implements text inputs debounce timeouts to prevent redundant queries on key presses.
*   **Reusability**: Shared across admin and super admin dashboards.
*   **Accessibility**: Implements standard toggle controls (`role="switch"`, `aria-checked`).
*   **Testing**: Asserts update confirm modal boxes in E2E tests.

---

## 9. Interactive Marketing Views (`components/landing/`)

| Component Class | Source File | Parent Component | Core Purpose |
| :--- | :--- | :--- | :--- |
| `HeroSection` | [HeroSection.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/components/landing/HeroSection.tsx) | Landing page | Visual landing interface. |

### Primary Component Detail: `HeroSection`
*   **Purpose**: Renders marketing headings, introductory text, and sign-up action paths.
*   **Props**: None.
*   **State**: None.
*   **Hooks**: None.
*   **Children**: `Button`
*   **Parent**: Main index layout page.
*   **API Calls**: None.
*   **Performance**: Serves static HTML structures to optimize SEO scores.
*   **Reusability**: Static landing section.
*   **Accessibility**: Contrasts heading sizes and color variables (`h1`, `h2` semantic layout flow).
*   **Testing**: Verifies visual heading elements in smoke testing routines.

---

## 10. State & Guard Routing Wrappers (`components/providers/`)

| Component Class | Source File | Parent Component | Core Purpose |
| :--- | :--- | :--- | :--- |
| `AuthProvider` | [AuthProvider.tsx](file:///home/charan_derangula/projects/intelligentSystems/learning-platform-frontend/components/providers/AuthProvider.tsx) | Root layout | Manages user access credentials. |

### Primary Component Detail: `AuthProvider`
*   **Purpose**: Wraps page layout structures to validate JWT access keys and manage login status variables.
*   **Props**: `children: React.ReactNode`
*   **State**: `user: UserProfile | null`, `tokenState: string`
*   **Hooks**: `useQuery` (validates active user profiles).
*   **Children**: Rendered page elements.
*   **Parent**: Global root layouts.
*   **API Calls**: `authService.getProfile`
*   **Performance**: Renders loading spinners on routing checks to prevent layout shifts.
*   **Reusability**: Global root provider wrapper.
*   **Accessibility**: None.
*   **Testing**: Asserts route redirection policies on auth token validation failures in `AuthProvider.test.tsx`.
