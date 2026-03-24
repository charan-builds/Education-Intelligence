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
      masteryPie: [
        { name: "Completed", value: 4 },
        { name: "In Progress", value: 1 },
        { name: "Pending", value: 1 },
      ],
    },
    weakTopics: [{ topicId: 11, gap: 18, name: "Graph Algorithms" }],
    notifications: [{ title: "Deadline approaching", message: "Complete your next step today.", severity: "high" }],
    recommendations: ["Schedule a 30-minute practice block for Graph Algorithms."],
    recentActivity: [{ title: "Graph Algorithms", subtitle: "Priority 1", tone: "completed" }],
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

describe("StudentDashboardPage", () => {
  it("renders the new student workspace summary", () => {
    render(<StudentDashboardPage />);

    expect(screen.getByText("Stay on track with your adaptive learning plan")).toBeInTheDocument();
    expect(screen.getAllByText("Graph Algorithms").length).toBeGreaterThan(0);
    expect(screen.getByText("RoadmapFlow")).toBeInTheDocument();
    expect(screen.getByText("Recommended next moves")).toBeInTheDocument();
  });
});
