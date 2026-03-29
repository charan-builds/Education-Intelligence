import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import StudentDashboardPage from "@/app/(student)/student/dashboard/page";

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}));

vi.mock("@/hooks/useDashboard", () => ({
  useStudentDashboard: () => ({
    queries: {
      dashboardQuery: { isLoading: false },
      roadmapQuery: { isLoading: false },
      notificationsQuery: { isLoading: false },
      suggestionsQuery: { isLoading: false },
    },
    kpis: {
      completionPercent: 72,
      completed: 4,
      totalSteps: 6,
      inProgress: 1,
      weakTopicCount: 2,
      streakDays: 5,
      focusScore: 78,
      xp: 520,
      leaderboardLead: "Top 12% this week",
      activeStepLabel: "Graph Algorithms",
      highPriorityNotifications: 1,
    },
    steps: [
      {
        id: 1,
        topic_id: 11,
        priority: 1,
        progress_status: "completed",
        estimated_time_hours: 2,
        difficulty: "easy",
        deadline: "",
      },
    ],
    topicMap: new Map([[11, "Graph Algorithms"]]),
    charts: {
      progressLine: [{ label: "Graph Algorithms", progress: 72 }],
      masteryDistribution: [{ label: "Graph Algorithms", value: 72 }],
      masteryPie: [
        { name: "Completed", value: 4 },
        { name: "In Progress", value: 1 },
        { name: "Pending", value: 1 },
      ],
    },
    weakTopics: [{ topicId: 11, gap: 18, name: "Graph Algorithms", score: 54 }],
    notifications: [{ title: "Deadline approaching", message: "Complete your next step today.", severity: "high" }],
    mentorSuggestions: [
      {
        title: "Schedule a 30-minute practice block",
        message: "Start with graph traversal warmups.",
        why: "This is the highest-leverage recovery area right now.",
      },
    ],
    recommendations: ["Schedule a 30-minute practice block for Graph Algorithms."],
    recentActivity: [{ title: "Graph Algorithms", subtitle: "Priority 1", tone: "completed" }],
    retention: {
      average_retention_score: 74,
      due_reviews: [{ topic_id: 11, topic_name: "Graph Algorithms", retention_score: 62, review_interval_days: 3 }],
      recommended_resources: [
        {
          id: 201,
          title: "Graph review set",
          topic_name: "Graph Algorithms",
          resource_type: "quiz",
          difficulty: "intermediate",
          reason: "Strengthen retention",
          href: "/student/roadmap",
          url: "https://example.com/graph-review",
        },
      ],
    },
    badges: [{ name: "Consistency", description: "Maintained your streak.", icon: "star", awarded_at: "2026-03-28T00:00:00Z" }],
    cognitiveModel: {
      confusion_level: "low",
      confusion_signals: ["Keeps momentum after feedback"],
      misunderstanding_patterns: ["Occasional traversal mix-ups"],
      teaching_style: "Blend concept explanation with guided practice.",
      adaptive_actions: ["Increase retrieval practice"],
    },
    heatmap: [{ topic_id: 11, topic_name: "Graph Algorithms", score: 54, mastery_delta: 6, confidence: 0.82 }],
    leaderboard: [{ rank: 4, user_id: 1, name: "Alex", xp: 860, is_current_user: true }],
    skillGraph: [{ topic_id: 11, topic_name: "Graph Algorithms", status: "in_progress", dependencies: [] }],
  }),
}));

vi.mock("@/hooks/useAdaptiveStudentUI", () => ({
  useAdaptiveStudentUI: () => ({
    focusMode: false,
    setFocusMode: vi.fn(),
    emotionalState: {
      label: "Steady progress",
      tone: "balanced",
      message: "Momentum is healthy.",
    },
    nextBestAction: {
      kind: "recover",
      title: "Recover Graph Algorithms",
      description: "Close the biggest mastery gap next.",
      ctaLabel: "Ask AI mentor",
      prompt: "Help me recover Graph Algorithms.",
    },
    rankedFeatures: [{ key: "mentor", title: "AI mentor", reason: "Best next step", score: 90 }],
    visibleSections: {
      demoMode: true,
      livePulse: true,
      leaderboard: true,
      badges: true,
      gamification: true,
      weakTopicsFirst: true,
      reviewFirst: true,
    },
    smartNotifications: [{ title: "Review Graph Algorithms today", message: "Retention is slipping." }],
    recordFeatureUse: vi.fn(),
  }),
}));

vi.mock("@/components/providers/RealtimeProvider", () => ({
  useRealtime: () => ({
    activeUsers: 8,
    liveEvents: [{ id: 1, message: "Learners are active now.", eventType: "activity.created" }],
  }),
}));

vi.mock("@/components/student/RoadmapFlow", () => ({
  default: () => <div>RoadmapFlow</div>,
}));

vi.mock("@/components/charts/ProgressLineChart", () => ({
  default: ({ title }: { title: string }) => <div>{title}</div>,
}));

vi.mock("@/components/charts/MasteryPieChart", () => ({
  default: ({ title }: { title: string }) => <div>{title}</div>,
}));

vi.mock("@/components/charts/DistributionBarChart", () => ({
  default: () => <div>DistributionBarChart</div>,
}));

vi.mock("@/components/student/DemoModeShowcase", () => ({
  default: () => <div>DemoModeShowcase</div>,
}));

vi.mock("@/components/student/AdaptiveGuidancePanel", () => ({
  default: () => <div>AdaptiveGuidancePanel</div>,
}));

vi.mock("@/components/student/ProgressStoryTimeline", () => ({
  default: () => <div>ProgressStoryTimeline</div>,
}));

vi.mock("@/components/dashboard/ActivityFeed", () => ({
  default: () => <div>ActivityFeed</div>,
}));

vi.mock("@/components/dashboard/RecommendationPanel", () => ({
  default: ({ title }: { title?: string }) => <div>{title ?? "RecommendationPanel"}</div>,
}));

describe("StudentDashboardPage", () => {
  it("renders the new student workspace summary", () => {
    render(<StudentDashboardPage />);

    expect(screen.getByText("An adaptive learning command center")).toBeInTheDocument();
    expect(screen.getAllByText("Graph Algorithms").length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: /View roadmap/i })).toHaveAttribute("href", "/student/roadmap");
    expect(screen.getByText("Progress feels alive when every signal tells one story.")).toBeInTheDocument();
  });
});
