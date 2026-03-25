"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  getAnalyticsOverview,
  getPlatformAnalyticsOverview,
  getRetentionAnalytics,
  getRoadmapProgressSummary,
  getTopicMasteryAnalytics,
} from "@/services/analyticsService";
import { getCommunities, getDiscussionThreads } from "@/services/communityService";
import { getStudentDashboard, getTeacherDashboard } from "@/services/dashboardService";
import { getGoals } from "@/services/goalService";
import { getHealth } from "@/services/healthService";
import {
  getAutonomousAgentStatus,
  getMentorNotifications,
  getMentorProgressAnalysis,
  getMentorSuggestions,
} from "@/services/mentorInsightsService";
import { getFeatureFlagCatalog, getFeatureFlags, getOutboxEvents, getOutboxStats } from "@/services/opsService";
import { getUserRoadmap } from "@/services/roadmapService";
import { getTenants } from "@/services/tenantService";
import { getQuestions, getTopics } from "@/services/topicService";
import { getUsers } from "@/services/userService";
import { useAuth } from "@/hooks/useAuth";
import { useTenantScope } from "@/hooks/useTenantScope";

export function normalizeRoadmapStatus(status: string): "completed" | "in_progress" | "pending" {
  const normalized = status.toLowerCase();
  if (normalized === "completed") {
    return "completed";
  }
  if (normalized === "in_progress") {
    return "in_progress";
  }
  return "pending";
}

export function normalizeRoadmapGenerationStatus(status: string | null | undefined): "generating" | "ready" | "failed" {
  if ((status ?? "").toLowerCase() === "failed") {
    return "failed";
  }
  if ((status ?? "").toLowerCase() === "ready") {
    return "ready";
  }
  return "generating";
}

export function useStudentDashboard() {
  const { user } = useAuth();
  const { activeTenantScope } = useTenantScope();
  const tenantScope = activeTenantScope ?? String(user?.tenant_id ?? "current");
  const dashboardQuery = useQuery({
    queryKey: ["dashboard", "student", "intelligence", tenantScope],
    queryFn: getStudentDashboard,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
  const roadmapQuery = useQuery({
    queryKey: ["dashboard", "student", "roadmap", tenantScope, user?.user_id],
    queryFn: async () => {
      if (!user?.user_id) {
        throw new Error("Missing user id");
      }
      return getUserRoadmap(user.user_id);
    },
    enabled: Boolean(user?.user_id),
    staleTime: 15_000,
    refetchOnWindowFocus: false,
    refetchInterval: (query) => {
      const roadmap = query.state.data?.items?.[0];
      return roadmap && normalizeRoadmapGenerationStatus(roadmap.status) === "generating" ? 2500 : false;
    },
  });
  const topicsQuery = useQuery({
    queryKey: ["dashboard", "student", "topics", tenantScope],
    queryFn: getTopics,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  return useMemo(() => {
    const payload = dashboardQuery.data;
    const roadmap = roadmapQuery.data?.items?.[0] ?? null;
    const roadmapStatus = normalizeRoadmapGenerationStatus(roadmap?.status);
    const steps = [...(roadmap?.steps ?? [])].sort((a, b) => a.priority - b.priority);
    const topicMap = new Map((topicsQuery.data?.items ?? []).map((topic) => [topic.id, topic.name]));
    const weakTopics = (payload?.weak_topics ?? []).map((item) => ({
      topicId: item.topic_id,
      name: item.topic_name,
      gap: Math.max(0, 100 - item.score),
      score: item.score,
      masteryDelta: item.mastery_delta,
      confidence: item.confidence,
    }));
    const leaderboard = payload?.gamification.leaderboard ?? [];
    const topLeaderboard = leaderboard[0] ?? null;

    return {
      queries: {
        dashboardQuery,
        roadmapQuery,
        topicsQuery,
      },
      roadmap,
      roadmapStatus,
      roadmapErrorMessage: roadmap?.error_message ?? null,
      steps,
      topicMap,
      kpis: {
        completionPercent: Math.round(payload?.completion_percent ?? 0),
        totalSteps: payload?.roadmap_progress.total_steps ?? 0,
        completed: payload?.roadmap_progress.completed_steps ?? 0,
        inProgress: payload?.roadmap_progress.in_progress_steps ?? 0,
        weakTopicCount: weakTopics.length,
        streakDays: payload?.streak_days ?? 0,
        focusScore: payload?.focus_score ?? 0,
        xp: payload?.xp ?? 0,
        leaderboardLead: topLeaderboard ? `${topLeaderboard.name} • ${topLeaderboard.xp} XP` : "No leaderboard data",
        highPriorityNotifications: 0,
      },
      charts: {
        velocityLine: (payload?.learning_velocity ?? []).map((point) => ({
          label: point.label,
          progress: point.minutes,
        })),
        progressLine: (payload?.learning_velocity ?? []).map((point) => ({
          label: point.label,
          progress: point.minutes,
        })),
        masteryPie: payload
          ? [
              { name: "Completed", value: payload.roadmap_progress.completed_steps },
              { name: "In Progress", value: payload.roadmap_progress.in_progress_steps },
              {
                name: "Pending",
                value: Math.max(
                  payload.roadmap_progress.total_steps -
                    payload.roadmap_progress.completed_steps -
                    payload.roadmap_progress.in_progress_steps,
                  0,
                ),
              },
            ]
          : [],
      },
      weakTopics,
      leaderboard,
      cognitiveModel: payload?.cognitive_model ?? {
        confusion_level: "low",
        confusion_signals: [],
        misunderstanding_patterns: [],
        teaching_style: "Blend concept explanation with practice.",
        adaptive_actions: [],
      },
      mentorSuggestions: payload?.mentor_suggestions ?? [],
      retention: payload?.retention ?? {
        tenant_id: 0,
        user_id: 0,
        average_retention_score: 0,
        due_reviews: [],
        upcoming_reviews: [],
        recommended_resources: [],
      },
      skillGraph: payload?.skill_graph ?? [],
      badges: payload?.gamification.badges ?? [],
      notifications: (payload?.mentor_suggestions ?? []).map((item) => ({
        title: item.title,
        message: item.message,
        severity: item.is_ai_generated ? "success" : "warning",
      })),
      recommendations: (payload?.mentor_suggestions ?? []).map((item) => ({
        title: item.title,
        message: item.message,
        why: item.why,
        confidenceLabel: item.is_ai_generated ? "AI generated" : "Platform rule",
        tone: item.is_ai_generated ? "success" : "default",
        href: item.topic_id ? `/student/topics/${item.topic_id}` : "/student/roadmap",
        ctaLabel: item.topic_id ? "Open topic" : "Open roadmap",
      })),
      recentActivity: (payload?.recent_activity ?? []).map((item) => ({
        title: item.event_type.replaceAll("_", " "),
        subtitle: item.topic_id
          ? `${topicMap.get(item.topic_id) ?? `Topic ${item.topic_id}`} updated in the learning graph`
          : "New platform signal captured",
        tone:
          item.event_type === "topic_completed"
            ? "completed"
            : item.event_type === "question_answered"
              ? "in_progress"
              : "info",
        tag: item.topic_id ? "Topic signal" : "System",
      })),
      heatmap: payload?.weak_topic_heatmap ?? [],
    };
  }, [dashboardQuery, roadmapQuery.data?.items, topicsQuery.data?.items, user?.user_id]);
}

export function useTeacherDashboard() {
  const { activeTenantScope } = useTenantScope();
  const tenantScope = activeTenantScope ?? "current";
  const teacherDashboardQuery = useQuery({
    queryKey: ["dashboard", "teacher", "intelligence", tenantScope],
    queryFn: getTeacherDashboard,
  });
  const retentionQuery = useQuery({
    queryKey: ["dashboard", "teacher", "retention", tenantScope],
    queryFn: getRetentionAnalytics,
  });

  return useMemo(() => {
    const payload = teacherDashboardQuery.data;
    const riskSegments = payload?.performance_distribution ?? { critical: 0, watch: 0, strong: 0 };
    const retention = retentionQuery.data;
    const learners = [
      ...(payload?.top_students ?? []),
      ...(payload?.bottom_students ?? []),
      ...(payload?.risk_students ?? []),
    ].map((item) => ({
      user_id: item.user_id,
      email: item.email,
      pending_steps: item.risk_level === "critical" ? 4 : item.risk_level === "watch" ? 2 : 1,
      mastery_percent: item.average_score,
      completion_percent: item.completion_percent,
      completed_steps: Math.round((item.completion_percent / 100) * 6),
      in_progress_steps: item.risk_level === "critical" ? 1 : 2,
      total_steps: 6,
    })).map((item) => ({
      ...item,
      pending_steps: Math.max(item.total_steps - item.completed_steps - item.in_progress_steps, item.pending_steps),
    }));

    return {
      queries: {
        teacherDashboardQuery,
        retentionQuery,
      },
      kpis: {
        studentCount: payload?.student_count ?? 0,
        criticalCount: riskSegments.critical,
        watchCount: riskSegments.watch,
        strongCount: riskSegments.strong,
        dueReviewCount: retention?.due_review_count ?? 0,
      },
      topStudents: payload?.top_students ?? [],
      bottomStudents: payload?.bottom_students ?? [],
      riskStudents: payload?.risk_students ?? [],
      learners,
      charts: {
        progressLine: (payload?.weak_topic_clusters ?? []).map((cluster) => ({
          label: cluster.topic_name,
          progress: 100 - cluster.average_score,
        })),
        masteryPie: [
          { name: "Critical", value: riskSegments.critical },
          { name: "Watch", value: riskSegments.watch },
          { name: "Strong", value: riskSegments.strong },
        ],
        clusteringBar: [
          { label: "Critical", value: riskSegments.critical },
          { label: "Watch", value: riskSegments.watch },
          { label: "Strong", value: riskSegments.strong },
        ],
        retentionLine: (retention?.retention_curve ?? []).map((point) => ({
          label: point.label,
          progress: point.average_retention_score,
        })),
      },
      retentionTopics: retention?.weak_retention_topics ?? [],
      recommendations: [
        {
          title: "Immediate intervention queue",
          message: `${riskSegments.critical} learners currently need direct intervention.`,
          why: "This count reflects the highest urgency cohort and should anchor the demo narrative around measurable need.",
          confidenceLabel: "Urgent",
          tone: "warning" as const,
        },
        {
          title: "Weakest cluster",
          message: `${payload?.weak_topic_clusters[0]?.topic_name ?? "Top weak topic"} is the largest shared mastery gap right now.`,
          why: "Showing a single weakest cluster helps investors understand how the system converts raw analytics into action.",
          confidenceLabel: "Cohort signal",
          tone: "default" as const,
        },
        {
          title: "Retention workload",
          message: `${retention?.due_review_count ?? 0} spaced reviews are currently due across the tenant.`,
          why: "Review pressure is a strong proxy for churn risk and product stickiness.",
          confidenceLabel: "Retention",
          tone: "success" as const,
        },
      ],
    };
  }, [retentionQuery.data, teacherDashboardQuery]);
}

export function useAdminDashboard() {
  const { activeTenantScope } = useTenantScope();
  const tenantScope = activeTenantScope ?? "current";
  const usersQuery = useQuery({
    queryKey: ["dashboard", "admin", "users", tenantScope],
    queryFn: getUsers,
  });
  const topicsQuery = useQuery({
    queryKey: ["dashboard", "admin", "topics", tenantScope],
    queryFn: getTopics,
  });
  const questionsQuery = useQuery({
    queryKey: ["dashboard", "admin", "questions", tenantScope],
    queryFn: () => getQuestions({ limit: 25, offset: 0 }),
  });
  const goalsQuery = useQuery({
    queryKey: ["dashboard", "admin", "goals", tenantScope],
    queryFn: getGoals,
  });
  const communitiesQuery = useQuery({
    queryKey: ["dashboard", "admin", "communities", tenantScope],
    queryFn: () => getCommunities({ limit: 10, offset: 0 }),
  });
  const threadsQuery = useQuery({
    queryKey: ["dashboard", "admin", "threads", tenantScope],
    queryFn: () => getDiscussionThreads({ limit: 10, offset: 0 }),
  });
  const overviewQuery = useQuery({
    queryKey: ["dashboard", "admin", "overview", tenantScope],
    queryFn: getAnalyticsOverview,
  });
  const roadmapProgressQuery = useQuery({
    queryKey: ["dashboard", "admin", "roadmap-progress", tenantScope],
    queryFn: getRoadmapProgressSummary,
  });
  const featureFlagsQuery = useQuery({
    queryKey: ["dashboard", "admin", "feature-flags", tenantScope],
    queryFn: () => getFeatureFlags({ limit: 20, offset: 0 }),
  });
  const featureCatalogQuery = useQuery({
    queryKey: ["dashboard", "admin", "feature-flags-catalog", tenantScope],
    queryFn: getFeatureFlagCatalog,
  });

  return useMemo(() => {
    const flags = featureFlagsQuery.data?.items ?? [];
    const enabledFlags = flags.filter((flag) => flag.enabled);

    return {
      queries: {
        usersQuery,
        topicsQuery,
        questionsQuery,
        goalsQuery,
        communitiesQuery,
        threadsQuery,
        overviewQuery,
        roadmapProgressQuery,
        featureFlagsQuery,
        featureCatalogQuery,
      },
      kpis: {
        users: usersQuery.data?.items.length ?? 0,
        topics: topicsQuery.data?.items.length ?? 0,
        questions: questionsQuery.data?.items.length ?? 0,
        goals: goalsQuery.data?.items.length ?? 0,
        communityThreads: threadsQuery.data?.items.length ?? 0,
        enabledFlags: enabledFlags.length,
      },
      charts: {
        progressLine: (roadmapProgressQuery.data?.learners ?? []).slice(0, 8).map((learner) => ({
          label: learner.email.split("@")[0],
          progress: learner.completion_percent,
        })),
        masteryPie: [
          { name: "Mastered", value: overviewQuery.data?.topic_mastery_distribution.mastered ?? 0 },
          { name: "Needs Practice", value: overviewQuery.data?.topic_mastery_distribution.needs_practice ?? 0 },
          { name: "Beginner", value: overviewQuery.data?.topic_mastery_distribution.beginner ?? 0 },
        ],
      },
      flags,
      flagCatalog: featureCatalogQuery.data?.items ?? [],
      communities: communitiesQuery.data?.items ?? [],
      threads: threadsQuery.data?.items ?? [],
      users: usersQuery.data?.items ?? [],
      topics: topicsQuery.data?.items ?? [],
      goals: goalsQuery.data?.items ?? [],
      questions: questionsQuery.data?.items ?? [],
    };
  }, [
    communitiesQuery,
    featureCatalogQuery.data?.items,
    featureFlagsQuery,
    goalsQuery,
    overviewQuery,
    questionsQuery,
    roadmapProgressQuery,
    threadsQuery,
    topicsQuery,
    usersQuery,
  ]);
}

export function useSuperAdminDashboard() {
  const { activeTenantScope } = useTenantScope();
  const tenantScope = activeTenantScope ?? "current";
  const platformOverviewQuery = useQuery({
    queryKey: ["dashboard", "super-admin", "platform-overview", tenantScope],
    queryFn: getPlatformAnalyticsOverview,
    refetchInterval: 60_000,
  });
  const tenantsQuery = useQuery({
    queryKey: ["dashboard", "super-admin", "tenants"],
    queryFn: getTenants,
  });
  const outboxStatsQuery = useQuery({
    queryKey: ["dashboard", "super-admin", "outbox-stats"],
    queryFn: getOutboxStats,
    refetchInterval: 60_000,
  });
  const outboxEventsQuery = useQuery({
    queryKey: ["dashboard", "super-admin", "outbox-events"],
    queryFn: () => getOutboxEvents({ event_status: "dead", limit: 10, offset: 0 }),
  });
  const healthQuery = useQuery({
    queryKey: ["dashboard", "super-admin", "health"],
    queryFn: getHealth,
    refetchInterval: 30_000,
  });
  const featureFlagsQuery = useQuery({
    queryKey: ["dashboard", "super-admin", "feature-flags"],
    queryFn: () => getFeatureFlags({ limit: 50, offset: 0 }),
  });

  return useMemo(() => {
    const tenants = tenantsQuery.data?.items ?? [];
    const platformOverview = platformOverviewQuery.data;
    const tenantBreakdown = platformOverview?.tenant_breakdown ?? [];
    const byType = tenants.reduce<Record<string, number>>((accumulator, tenant) => {
      accumulator[tenant.type] = (accumulator[tenant.type] ?? 0) + 1;
      return accumulator;
    }, {});

    return {
      queries: {
        platformOverviewQuery,
        tenantsQuery,
        outboxStatsQuery,
        outboxEventsQuery,
        healthQuery,
        featureFlagsQuery,
      },
      tenants,
      tenantBreakdown,
      platformOverview,
      byType,
      kpis: {
        totalTenants: platformOverview?.tenant_count ?? tenants.length,
        totalLearners: platformOverview?.student_count ?? 0,
        averageCompletion: platformOverview?.average_completion_percent ?? 0,
        averageMastery: platformOverview?.average_mastery_percent ?? 0,
        deadOutbox: outboxStatsQuery.data?.dead ?? 0,
        pendingOutbox: outboxStatsQuery.data?.pending ?? 0,
        enabledFlags: (featureFlagsQuery.data?.items ?? []).filter((flag) => flag.enabled).length,
      },
      charts: {
        tenantPerformanceLine: tenantBreakdown.slice(0, 8).map((tenant) => ({
          label: tenant.tenant_name.slice(0, 12),
          progress: tenant.average_mastery_percent,
        })),
        growthLine: [...tenants]
          .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
          .map((tenant, index) => ({
            label: tenant.name.slice(0, 10),
            progress: index + 1,
          })),
        tenantPie: Object.entries(byType).map(([name, value]) => ({ name, value })),
        masteryPie: [
          {
            name: "Mastered",
            value: platformOverview?.topic_mastery_distribution.mastered ?? 0,
          },
          {
            name: "Needs Practice",
            value: platformOverview?.topic_mastery_distribution.needs_practice ?? 0,
          },
          {
            name: "Beginner",
            value: platformOverview?.topic_mastery_distribution.beginner ?? 0,
          },
        ],
        roleMixBar: [
          { label: "Students", value: platformOverview?.student_count ?? 0 },
          { label: "Mentors", value: platformOverview?.mentor_count ?? 0 },
          { label: "Teachers", value: platformOverview?.teacher_count ?? 0 },
          { label: "Admins", value: platformOverview?.admin_count ?? 0 },
        ],
      },
      deadEvents: outboxEventsQuery.data?.items ?? [],
    };
  }, [featureFlagsQuery, healthQuery, outboxEventsQuery, outboxStatsQuery, platformOverviewQuery, tenantsQuery]);
}

export function useMentorWorkspace() {
  const { user } = useAuth();

  const suggestionsQuery = useQuery({
    queryKey: ["dashboard", "mentor", "suggestions"],
    queryFn: getMentorSuggestions,
  });
  const notificationsQuery = useQuery({
    queryKey: ["dashboard", "mentor", "notifications"],
    queryFn: getMentorNotifications,
  });
  const progressAnalysisQuery = useQuery({
    queryKey: ["dashboard", "mentor", "progress"],
    queryFn: getMentorProgressAnalysis,
  });
  const agentQuery = useQuery({
    queryKey: ["dashboard", "mentor", "agent"],
    queryFn: getAutonomousAgentStatus,
  });
  const featureFlagsQuery = useQuery({
    queryKey: ["dashboard", "mentor", "flags"],
    queryFn: () => getFeatureFlags({ limit: 20, offset: 0 }),
  });
  const roadmapQuery = useQuery({
    queryKey: ["dashboard", "mentor", "roadmap", user?.user_id],
    queryFn: async () => {
      if (!user?.user_id) {
        throw new Error("Missing user id");
      }
      return getUserRoadmap(user.user_id);
    },
    enabled: Boolean(user?.user_id),
    refetchInterval: (query) => {
      const roadmap = query.state.data?.items?.[0];
      return roadmap && normalizeRoadmapGenerationStatus(roadmap.status) === "generating" ? 2500 : false;
    },
  });

  return useMemo(() => {
    const roadmap = roadmapQuery.data?.items?.[0] ?? null;
    const roadmapStatus = normalizeRoadmapGenerationStatus(roadmap?.status);
    const steps = [...(roadmap?.steps ?? [])].sort((a, b) => a.priority - b.priority);
    const aiMentorEnabled = (featureFlagsQuery.data?.items ?? []).some(
      (flag) => flag.feature_name === "ai_mentor_enabled" && flag.enabled,
    );

    return {
      queries: {
        suggestionsQuery,
        notificationsQuery,
        progressAnalysisQuery,
        agentQuery,
        featureFlagsQuery,
        roadmapQuery,
      },
      kpis: {
        aiMentorEnabled,
        recommendationCount: suggestionsQuery.data?.suggestions.length ?? 0,
        notificationCount: notificationsQuery.data?.notifications.length ?? 0,
        trackedWeakTopics: Object.keys(progressAnalysisQuery.data?.topic_improvements ?? {}).length,
        agentDecisions: agentQuery.data?.decisions.length ?? 0,
      },
      charts: {
        progressLine: progressAnalysisQuery.data?.weekly_progress.map((item) => ({
          label: item.week,
          progress: item.completion_percent,
        })) ?? [],
        masteryPie: [
          {
            name: "Focus Topics",
            value: (progressAnalysisQuery.data?.recommended_focus ?? []).length,
          },
          {
            name: "Completed Roadmap",
            value: steps.filter((step) => normalizeRoadmapStatus(step.progress_status) === "completed").length,
          },
          {
            name: "Pending Support",
            value: steps.filter((step) => normalizeRoadmapStatus(step.progress_status) !== "completed").length,
          },
        ],
      },
      suggestions: (suggestionsQuery.data?.suggestions ?? []).map((item, index) => ({
        title: `Mentor suggestion ${index + 1}`,
        message: item,
        why: "This prompt is preloaded to accelerate the mentor conversation during the demo.",
        confidenceLabel: "Ready to use",
        tone: "success" as const,
      })),
      notifications: notificationsQuery.data?.notifications ?? [],
      roadmap,
      roadmapStatus,
      roadmapErrorMessage: roadmap?.error_message ?? null,
      agent: agentQuery.data
        ? {
            ...agentQuery.data,
            cycleSummary: agentQuery.data.cycle_summary,
            memorySummary: agentQuery.data.memory_summary,
          }
        : null,
      focusTopics: Object.entries(progressAnalysisQuery.data?.topic_improvements ?? {})
        .map(([topicId, gap]) => ({
          topicId: Number(topicId),
          gap: Number(gap),
        }))
        .sort((a, b) => b.gap - a.gap),
      recommendedFocus: (progressAnalysisQuery.data?.recommended_focus ?? []).map((item, index) => ({
        title: `Focus area ${index + 1}`,
        message: item,
        why: "Recommended focus comes from current topic-improvement gaps and weekly progress analysis.",
        confidenceLabel: "Progress signal",
        tone: "default" as const,
      })),
    };
  }, [agentQuery.data, featureFlagsQuery, notificationsQuery, progressAnalysisQuery, roadmapQuery, suggestionsQuery]);
}
