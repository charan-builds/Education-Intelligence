"use client";

import { ChangeEvent, FormEvent, useCallback, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React from "react";

import RequireRole from "@/components/auth/RequireRole";
import { useAuth } from "@/hooks/useAuth";
import { useTenantScope } from "@/hooks/useTenantScope";
import RoleDashboardLayout from "@/components/layout/RoleDashboardLayout";
import MetricCard from "@/components/ui/MetricCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { getAnalyticsOverview, getRoadmapProgressSummary } from "@/services/analyticsService";
import {
  createTopic,
  createTopicPrerequisite,
  createQuestion,
  deleteTopic,
  deleteTopicPrerequisite,
  deleteQuestion,
  exportQuestions,
  exportQuestionsCsv,
  getQuestions,
  getTopicPrerequisites,
  getTopics,
  importQuestions,
  importQuestionsCsv,
  updateTopic,
  updateQuestion,
} from "@/services/topicService";
import {
  createBadge,
  createCommunity,
  deleteBadge,
  deleteCommunity,
  getBadges,
  getCommunities,
  getDiscussionThreads,
  resolveDiscussionThread,
} from "@/services/communityService";
import { createUser, getUsers } from "@/services/userService";
import {
  createGoal,
  createGoalTopic,
  deleteGoal,
  deleteGoalTopic,
  getGoalTopics,
  getGoals,
  updateGoal,
} from "@/services/goalService";
import type {
  CreateTopicPayload,
  CreateTopicPrerequisitePayload,
  CreateQuestionPayload,
  Question,
  TopicPrerequisite,
  TopicSummary,
  UpdateTopicPayload,
  UpdateQuestionPayload,
} from "@/types/topic";
import type { CreateGoalPayload, Goal, GoalTopic, UpdateGoalPayload } from "@/types/goal";
import type { Badge, Community, DiscussionThread } from "@/types/community";
import type { AssignableUserRole, UserRole } from "@/types/user";

const ROLE_OPTIONS: AssignableUserRole[] = ["student", "teacher", "mentor", "admin"];
const QUESTION_TYPE_OPTIONS = ["multiple_choice", "short_text"] as const;

type DashboardNotice = {
  tone: "success" | "error";
  message: string;
};

function NoticeBanner({ notice }: { notice: DashboardNotice | null }) {
  if (!notice) {
    return null;
  }

  const toneClasses =
    notice.tone === "success"
      ? "border-emerald-200 bg-emerald-50 text-emerald-800"
      : "border-red-200 bg-red-50 text-red-700";

  return <div className={`rounded-lg border px-4 py-3 text-sm ${toneClasses}`}>{notice.message}</div>;
}

function downloadTextFile(content: string, filename: string, type: string): void {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function confirmAction(message: string): boolean {
  if (typeof window === "undefined" || typeof window.confirm !== "function") {
    return true;
  }
  return window.confirm(message);
}

export default function AdminDashboardClient() {
  const { user } = useAuth();
  const { activeTenantScope, clearActiveTenantScope } = useTenantScope();
  const queryClient = useQueryClient();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<AssignableUserRole>("student");
  const [formError, setFormError] = useState("");

  const [questionFormError, setQuestionFormError] = useState("");
  const [questionNotice, setQuestionNotice] = useState<DashboardNotice | null>(null);
  const [goalFormError, setGoalFormError] = useState("");
  const [goalNotice, setGoalNotice] = useState<DashboardNotice | null>(null);
  const [topicFormError, setTopicFormError] = useState("");
  const [topicNotice, setTopicNotice] = useState<DashboardNotice | null>(null);
  const [prerequisiteNotice, setPrerequisiteNotice] = useState<DashboardNotice | null>(null);
  const [prerequisiteFormError, setPrerequisiteFormError] = useState("");
  const [communityNotice, setCommunityNotice] = useState<DashboardNotice | null>(null);
  const [communityFormError, setCommunityFormError] = useState("");
  const [badgeNotice, setBadgeNotice] = useState<DashboardNotice | null>(null);
  const [communityFilterTopicId, setCommunityFilterTopicId] = useState("all");
  const [communityPageOffset, setCommunityPageOffset] = useState(0);
  const [badgeFilterUserId, setBadgeFilterUserId] = useState("all");
  const [badgePageOffset, setBadgePageOffset] = useState(0);
  const [threadFilterCommunityId, setThreadFilterCommunityId] = useState("all");
  const [threadPageOffset, setThreadPageOffset] = useState(0);
  const [communityTopicId, setCommunityTopicId] = useState("1");
  const [communityName, setCommunityName] = useState("");
  const [communityDescription, setCommunityDescription] = useState("");
  const [badgeUserId, setBadgeUserId] = useState("1");
  const [badgeName, setBadgeName] = useState("");
  const [badgeDescription, setBadgeDescription] = useState("");
  const [badgeAwardedFor, setBadgeAwardedFor] = useState("mentorship");
  const [goalName, setGoalName] = useState("");
  const [goalDescription, setGoalDescription] = useState("");
  const [editingGoalId, setEditingGoalId] = useState<number | null>(null);
  const [goalTopicGoalId, setGoalTopicGoalId] = useState("1");
  const [goalTopicTopicId, setGoalTopicTopicId] = useState("1");
  const [topicName, setTopicName] = useState("");
  const [topicDescription, setTopicDescription] = useState("");
  const [editingTopicId, setEditingTopicId] = useState<number | null>(null);
  const [prerequisiteTopicId, setPrerequisiteTopicId] = useState("1");
  const [dependentTopicId, setDependentTopicId] = useState("1");
  const [topicId, setTopicId] = useState("1");
  const [difficulty, setDifficulty] = useState("2");
  const [questionType, setQuestionType] = useState<(typeof QUESTION_TYPE_OPTIONS)[number]>("multiple_choice");
  const [questionText, setQuestionText] = useState("");
  const [correctAnswer, setCorrectAnswer] = useState("");
  const [acceptedAnswers, setAcceptedAnswers] = useState("");
  const [answerOptions, setAnswerOptions] = useState("");
  const [editingQuestionId, setEditingQuestionId] = useState<number | null>(null);

  const [filterTopicId, setFilterTopicId] = useState("all");
  const [filterQuestionType, setFilterQuestionType] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [questionPageOffset, setQuestionPageOffset] = useState(0);

  const [bulkJson, setBulkJson] = useState("");
  const [bulkCsv, setBulkCsv] = useState("");
  const [bulkNotice, setBulkNotice] = useState<DashboardNotice | null>(null);

  const usersQuery = useQuery({
    queryKey: ["admin-users"],
    queryFn: getUsers,
  });

  const analyticsOverviewQuery = useQuery({
    queryKey: ["admin-analytics-overview"],
    queryFn: getAnalyticsOverview,
  });

  const roadmapProgressSummaryQuery = useQuery({
    queryKey: ["admin-roadmap-progress-summary"],
    queryFn: getRoadmapProgressSummary,
  });

  const topicsQuery = useQuery({
    queryKey: ["admin-topics"],
    queryFn: getTopics,
  });

  const goalsQuery = useQuery({
    queryKey: ["admin-goals"],
    queryFn: getGoals,
  });

  const goalTopicsQuery = useQuery({
    queryKey: ["admin-goal-topics"],
    queryFn: () => getGoalTopics(),
  });

  const questionsQuery = useQuery({
    queryKey: ["admin-questions", filterTopicId, filterQuestionType, searchQuery, questionPageOffset],
    queryFn: () =>
      getQuestions({
        topic_id: filterTopicId === "all" ? undefined : Number(filterTopicId),
        question_type: filterQuestionType === "all" ? undefined : filterQuestionType,
        search: searchQuery.trim() || undefined,
        limit: 10,
        offset: questionPageOffset,
      }),
  });

  const prerequisitesQuery = useQuery({
    queryKey: ["admin-prerequisites"],
    queryFn: () => getTopicPrerequisites(),
  });

  const communitiesQuery = useQuery({
    queryKey: ["admin-communities", communityFilterTopicId, communityPageOffset],
    queryFn: () =>
      getCommunities({
        topic_id: communityFilterTopicId === "all" ? undefined : Number(communityFilterTopicId),
        limit: 5,
        offset: communityPageOffset,
      }),
  });

  const badgesQuery = useQuery({
    queryKey: ["admin-community-badges", badgeFilterUserId, badgePageOffset],
    queryFn: () =>
      getBadges({
        user_id: badgeFilterUserId === "all" ? undefined : Number(badgeFilterUserId),
        limit: 5,
        offset: badgePageOffset,
      }),
  });

  const threadsQuery = useQuery({
    queryKey: ["admin-community-threads", threadFilterCommunityId, threadPageOffset],
    queryFn: () =>
      getDiscussionThreads({
        community_id: threadFilterCommunityId === "all" ? undefined : Number(threadFilterCommunityId),
        limit: 5,
        offset: threadPageOffset,
      }),
  });

  const createUserMutation = useMutation({
    mutationFn: createUser,
    onSuccess: async () => {
      setEmail("");
      setPassword("");
      setRole("student");
      setFormError("");
      await queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
    onError: () => {
      setFormError("Failed to create user.");
    },
  });

  const createQuestionMutation = useMutation({
    mutationFn: createQuestion,
    onSuccess: async () => {
      resetQuestionForm();
      setQuestionNotice({ tone: "success", message: "Question created successfully." });
      setQuestionPageOffset(0);
      await queryClient.invalidateQueries({ queryKey: ["admin-questions"] });
    },
    onError: () => {
      setQuestionNotice({ tone: "error", message: "Failed to create question." });
      setQuestionFormError("Failed to create question.");
    },
  });

  const createGoalMutation = useMutation({
    mutationFn: createGoal,
    onSuccess: async () => {
      resetGoalForm();
      setGoalNotice({ tone: "success", message: "Goal created successfully." });
      await queryClient.invalidateQueries({ queryKey: ["admin-goals"] });
    },
    onError: () => {
      setGoalNotice({ tone: "error", message: "Failed to create goal." });
      setGoalFormError("Failed to create goal.");
    },
  });

  const updateGoalMutation = useMutation({
    mutationFn: ({ goalId, payload }: { goalId: number; payload: UpdateGoalPayload }) =>
      updateGoal(goalId, payload),
    onSuccess: async () => {
      resetGoalForm();
      setGoalNotice({ tone: "success", message: "Goal updated successfully." });
      await queryClient.invalidateQueries({ queryKey: ["admin-goals"] });
    },
    onError: () => {
      setGoalNotice({ tone: "error", message: "Failed to update goal." });
      setGoalFormError("Failed to update goal.");
    },
  });

  const deleteGoalMutation = useMutation({
    mutationFn: deleteGoal,
    onSuccess: async () => {
      setGoalNotice({ tone: "success", message: "Goal deleted successfully." });
      await queryClient.invalidateQueries({ queryKey: ["admin-goals"] });
    },
    onError: () => {
      setGoalNotice({ tone: "error", message: "Failed to delete goal." });
    },
  });

  const createGoalTopicMutation = useMutation({
    mutationFn: ({ goalId, topicId }: { goalId: number; topicId: number }) => createGoalTopic(goalId, topicId),
    onSuccess: async () => {
      setGoalNotice({ tone: "success", message: "Goal topic mapping created successfully." });
      await queryClient.invalidateQueries({ queryKey: ["admin-goal-topics"] });
    },
    onError: () => {
      setGoalNotice({ tone: "error", message: "Failed to create goal topic mapping." });
    },
  });

  const deleteGoalTopicMutation = useMutation({
    mutationFn: deleteGoalTopic,
    onSuccess: async () => {
      setGoalNotice({ tone: "success", message: "Goal topic mapping deleted successfully." });
      await queryClient.invalidateQueries({ queryKey: ["admin-goal-topics"] });
    },
    onError: () => {
      setGoalNotice({ tone: "error", message: "Failed to delete goal topic mapping." });
    },
  });

  const createTopicMutation = useMutation({
    mutationFn: createTopic,
    onSuccess: async () => {
      resetTopicForm();
      setTopicNotice({ tone: "success", message: "Topic created successfully." });
      await queryClient.invalidateQueries({ queryKey: ["admin-topics"] });
    },
    onError: () => {
      setTopicNotice({ tone: "error", message: "Failed to create topic." });
      setTopicFormError("Failed to create topic.");
    },
  });

  const updateTopicMutation = useMutation({
    mutationFn: ({ topicId, payload }: { topicId: number; payload: UpdateTopicPayload }) =>
      updateTopic(topicId, payload),
    onSuccess: async () => {
      resetTopicForm();
      setTopicNotice({ tone: "success", message: "Topic updated successfully." });
      await queryClient.invalidateQueries({ queryKey: ["admin-topics"] });
    },
    onError: () => {
      setTopicNotice({ tone: "error", message: "Failed to update topic." });
      setTopicFormError("Failed to update topic.");
    },
  });

  const deleteTopicMutation = useMutation({
    mutationFn: deleteTopic,
    onSuccess: async () => {
      setTopicNotice({ tone: "success", message: "Topic deleted successfully." });
      await queryClient.invalidateQueries({ queryKey: ["admin-topics"] });
    },
    onError: () => {
      setTopicNotice({ tone: "error", message: "Failed to delete topic. Remove its questions first." });
    },
  });

  const createPrerequisiteMutation = useMutation({
    mutationFn: createTopicPrerequisite,
    onSuccess: async () => {
      setPrerequisiteNotice({ tone: "success", message: "Prerequisite link created successfully." });
      setPrerequisiteFormError("");
      await queryClient.invalidateQueries({ queryKey: ["admin-prerequisites"] });
    },
    onError: () => {
      setPrerequisiteNotice({ tone: "error", message: "Failed to create prerequisite link." });
      setPrerequisiteFormError("Failed to create prerequisite link.");
    },
  });

  const deletePrerequisiteMutation = useMutation({
    mutationFn: deleteTopicPrerequisite,
    onSuccess: async () => {
      setPrerequisiteNotice({ tone: "success", message: "Prerequisite link deleted successfully." });
      await queryClient.invalidateQueries({ queryKey: ["admin-prerequisites"] });
    },
    onError: () => {
      setPrerequisiteNotice({ tone: "error", message: "Failed to delete prerequisite link." });
    },
  });

  const createCommunityMutation = useMutation({
    mutationFn: createCommunity,
    onSuccess: async () => {
      setCommunityName("");
      setCommunityDescription("");
      setCommunityFormError("");
      setCommunityNotice({ tone: "success", message: "Community created successfully." });
      await queryClient.invalidateQueries({ queryKey: ["admin-communities"] });
    },
    onError: () => {
      setCommunityFormError("Failed to create community.");
      setCommunityNotice({ tone: "error", message: "Failed to create community." });
    },
  });

  const createBadgeMutation = useMutation({
    mutationFn: createBadge,
    onSuccess: async () => {
      setBadgeName("");
      setBadgeDescription("");
      setBadgeAwardedFor("mentorship");
      setBadgeNotice({ tone: "success", message: "Badge awarded successfully." });
      await queryClient.invalidateQueries({ queryKey: ["admin-community-badges"] });
    },
    onError: () => {
      setBadgeNotice({ tone: "error", message: "Failed to award badge." });
    },
  });

  const resolveThreadMutation = useMutation({
    mutationFn: ({ threadId, isResolved }: { threadId: number; isResolved: boolean }) =>
      resolveDiscussionThread(threadId, { is_resolved: isResolved }),
    onSuccess: async (_, variables) => {
      setCommunityNotice({
        tone: "success",
        message: variables.isResolved ? "Thread marked as resolved." : "Thread reopened successfully.",
      });
      await queryClient.invalidateQueries({ queryKey: ["admin-community-threads"] });
    },
    onError: () => {
      setCommunityNotice({ tone: "error", message: "Failed to update thread resolution." });
    },
  });

  const deleteCommunityMutation = useMutation({
    mutationFn: deleteCommunity,
    onSuccess: async () => {
      setCommunityNotice({ tone: "success", message: "Community deleted successfully." });
      await queryClient.invalidateQueries({ queryKey: ["admin-communities"] });
      await queryClient.invalidateQueries({ queryKey: ["admin-community-threads"] });
    },
    onError: () => {
      setCommunityNotice({ tone: "error", message: "Failed to delete community." });
    },
  });

  const deleteBadgeMutation = useMutation({
    mutationFn: deleteBadge,
    onSuccess: async () => {
      setBadgeNotice({ tone: "success", message: "Badge revoked successfully." });
      await queryClient.invalidateQueries({ queryKey: ["admin-community-badges"] });
    },
    onError: () => {
      setBadgeNotice({ tone: "error", message: "Failed to revoke badge." });
    },
  });

  const updateQuestionMutation = useMutation({
    mutationFn: ({ questionId, payload }: { questionId: number; payload: UpdateQuestionPayload }) =>
      updateQuestion(questionId, payload),
    onSuccess: async () => {
      resetQuestionForm();
      setQuestionNotice({ tone: "success", message: "Question updated successfully." });
      await queryClient.invalidateQueries({ queryKey: ["admin-questions"] });
    },
    onError: () => {
      setQuestionNotice({ tone: "error", message: "Failed to update question." });
      setQuestionFormError("Failed to update question.");
    },
  });

  const deleteQuestionMutation = useMutation({
    mutationFn: deleteQuestion,
    onSuccess: async () => {
      setQuestionNotice({ tone: "success", message: "Question deleted successfully." });
      await queryClient.invalidateQueries({ queryKey: ["admin-questions"] });
    },
    onError: () => {
      setQuestionNotice({ tone: "error", message: "Failed to delete question." });
    },
  });

  const importQuestionsMutation = useMutation({
    mutationFn: importQuestions,
    onSuccess: async (result) => {
      setBulkJson("");
      setBulkNotice({ tone: "success", message: `Imported ${result.created} questions from JSON.` });
      setQuestionPageOffset(0);
      await queryClient.invalidateQueries({ queryKey: ["admin-questions"] });
    },
    onError: () => {
      setBulkNotice({ tone: "error", message: "Failed to import questions from JSON." });
    },
  });

  const importQuestionsCsvMutation = useMutation({
    mutationFn: importQuestionsCsv,
    onSuccess: async (result) => {
      setBulkCsv("");
      setBulkNotice({ tone: "success", message: `Imported ${result.created} questions from CSV.` });
      setQuestionPageOffset(0);
      await queryClient.invalidateQueries({ queryKey: ["admin-questions"] });
    },
    onError: () => {
      setBulkNotice({ tone: "error", message: "Failed to import questions from CSV." });
    },
  });

  const tenantId = user?.tenant_id ?? null;

  const filterTenantOwned = useCallback(<T extends { tenant_id?: number | null }>(items: T[]): T[] => {
    if (tenantId === null) {
      return items;
    }

    return items.filter((item) => item.tenant_id === undefined || item.tenant_id === null || item.tenant_id === tenantId);
  }, [tenantId]);

  const users = useMemo(() => filterTenantOwned(usersQuery.data?.items ?? []), [filterTenantOwned, usersQuery.data?.items]);
  const goals = useMemo<Goal[]>(() => filterTenantOwned(goalsQuery.data?.items ?? []), [filterTenantOwned, goalsQuery.data?.items]);
  const topics = useMemo<TopicSummary[]>(() => filterTenantOwned(topicsQuery.data?.items ?? []), [filterTenantOwned, topicsQuery.data?.items]);
  const goalTopics = useMemo<GoalTopic[]>(
    () =>
      (goalTopicsQuery.data?.items ?? []).filter(
        (link) => goals.some((goal) => goal.id === link.goal_id) && topics.some((topic) => topic.id === link.topic_id),
      ),
    [goalTopicsQuery.data?.items, goals, topics],
  );
  const questions = useMemo<Question[]>(
    () => (questionsQuery.data?.items ?? []).filter((question) => topics.some((topic) => topic.id === question.topic_id)),
    [questionsQuery.data?.items, topics],
  );
  const prerequisites = useMemo<TopicPrerequisite[]>(
    () =>
      (prerequisitesQuery.data?.items ?? []).filter(
        (link) =>
          topics.some((topic) => topic.id === link.topic_id) &&
          topics.some((topic) => topic.id === link.prerequisite_topic_id),
      ),
    [prerequisitesQuery.data?.items, topics],
  );
  const communities = useMemo<Community[]>(
    () => filterTenantOwned(communitiesQuery.data?.items ?? []),
    [filterTenantOwned, communitiesQuery.data?.items],
  );
  const communityBadges = useMemo<Badge[]>(
    () => filterTenantOwned(badgesQuery.data?.items ?? []),
    [filterTenantOwned, badgesQuery.data?.items],
  );
  const discussionThreads = useMemo<DiscussionThread[]>(
    () => filterTenantOwned(threadsQuery.data?.items ?? []),
    [filterTenantOwned, threadsQuery.data?.items],
  );
  const questionMeta = questionsQuery.data?.meta;
  const communityMeta = communitiesQuery.data?.meta;
  const badgeMeta = badgesQuery.data?.meta;
  const threadMeta = threadsQuery.data?.meta;
  const learnerProgressRows = useMemo(() => roadmapProgressSummaryQuery.data?.learners ?? [], [roadmapProgressSummaryQuery.data?.learners]);

  const analytics = useMemo(() => {
    const byRole: Record<UserRole, number> = {
      student: 0,
      teacher: 0,
      mentor: 0,
      admin: 0,
      super_admin: 0,
    };

    for (const user of users) {
      byRole[user.role] += 1;
    }

    return {
      totalUsers: users.length,
      roleDistribution: byRole,
      diagnosticCompletionRate: analyticsOverviewQuery.data?.diagnostic_completion_rate ?? 0,
      roadmapCompletionRate: analyticsOverviewQuery.data?.roadmap_completion_rate ?? 0,
      studentCount: roadmapProgressSummaryQuery.data?.student_count ?? byRole.student,
    };
  }, [analyticsOverviewQuery.data?.diagnostic_completion_rate, analyticsOverviewQuery.data?.roadmap_completion_rate, roadmapProgressSummaryQuery.data?.student_count, users]);

  function resetQuestionForm(): void {
    setQuestionFormError("");
    setTopicId(topics[0] ? String(topics[0].id) : "1");
    setDifficulty("2");
    setQuestionType("multiple_choice");
    setQuestionText("");
    setCorrectAnswer("");
    setAcceptedAnswers("");
    setAnswerOptions("");
    setEditingQuestionId(null);
  }

  function resetGoalForm(): void {
    setGoalFormError("");
    setGoalName("");
    setGoalDescription("");
    setEditingGoalId(null);
  }

  function resetTopicForm(): void {
    setTopicFormError("");
    setTopicName("");
    setTopicDescription("");
    setEditingTopicId(null);
  }

  function getTopicName(questionTopicId: number): string {
    return topics.find((topic) => topic.id === questionTopicId)?.name ?? `Topic ${questionTopicId}`;
  }

  function getGoalName(goalId: number): string {
    return goals.find((goal) => goal.id === goalId)?.name ?? `Goal ${goalId}`;
  }

  function getUserEmail(userId: number): string {
    return users.find((user) => user.id === userId)?.email ?? `User ${userId}`;
  }

  async function onPrerequisiteSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setPrerequisiteFormError("");
    setPrerequisiteNotice(null);

    const payload: CreateTopicPrerequisitePayload = {
      topic_id: Number(dependentTopicId),
      prerequisite_topic_id: Number(prerequisiteTopicId),
    };

    if (!payload.topic_id || !payload.prerequisite_topic_id) {
      setPrerequisiteFormError("Both topic selections are required.");
      return;
    }

    await createPrerequisiteMutation.mutateAsync(payload);
  }

  async function onCommunitySubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setCommunityFormError("");
    setCommunityNotice(null);

    if (!communityName.trim() || !communityDescription.trim()) {
      setCommunityFormError("Community name and description are required.");
      return;
    }

    await createCommunityMutation.mutateAsync({
      topic_id: Number(communityTopicId),
      name: communityName.trim(),
      description: communityDescription.trim(),
    });
  }

  async function onBadgeSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setBadgeNotice(null);

    if (!badgeName.trim() || !badgeDescription.trim()) {
      setBadgeNotice({ tone: "error", message: "Badge name and description are required." });
      return;
    }

    await createBadgeMutation.mutateAsync({
      user_id: Number(badgeUserId),
      name: badgeName.trim(),
      description: badgeDescription.trim(),
      awarded_for: badgeAwardedFor.trim() || "mentorship",
    });
  }

  async function onGoalSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setGoalFormError("");
    setGoalNotice(null);

    if (!goalName.trim() || !goalDescription.trim()) {
      setGoalFormError("Goal name and description are required.");
      return;
    }

    const payload: CreateGoalPayload = {
      name: goalName.trim(),
      description: goalDescription.trim(),
    };

    if (editingGoalId !== null) {
      await updateGoalMutation.mutateAsync({ goalId: editingGoalId, payload });
      return;
    }

    await createGoalMutation.mutateAsync(payload);
  }

  async function onGoalTopicSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setGoalNotice(null);
    await createGoalTopicMutation.mutateAsync({
      goalId: Number(goalTopicGoalId),
      topicId: Number(goalTopicTopicId),
    });
  }

  async function handleExportQuestions(): Promise<void> {
    try {
      const topicFilter = filterTopicId === "all" ? undefined : Number(filterTopicId);
      const content = await exportQuestions(topicFilter);
      downloadTextFile(content, "questions-export.json", "application/json");
      setBulkNotice({ tone: "success", message: "Question export downloaded as JSON." });
    } catch {
      setBulkNotice({ tone: "error", message: "Failed to export questions as JSON." });
    }
  }

  async function handleExportQuestionsCsv(): Promise<void> {
    try {
      const topicFilter = filterTopicId === "all" ? undefined : Number(filterTopicId);
      const content = await exportQuestionsCsv(topicFilter);
      downloadTextFile(content, "questions-export.csv", "text/csv");
      setBulkNotice({ tone: "success", message: "Question export downloaded as CSV." });
    } catch {
      setBulkNotice({ tone: "error", message: "Failed to export questions as CSV." });
    }
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setFormError("");

    if (!email || !password) {
      setFormError("Email and password are required.");
      return;
    }

    await createUserMutation.mutateAsync({ email, password, role });
  }

  async function onQuestionSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setQuestionFormError("");
    setQuestionNotice(null);

    const parsedTopicId = Number(topicId);
    const parsedDifficulty = Number(difficulty);
    const parsedAcceptedAnswers = acceptedAnswers
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
    const parsedAnswerOptions =
      questionType === "multiple_choice"
        ? answerOptions
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean)
        : [];

    if (!parsedTopicId || !questionText || !correctAnswer) {
      setQuestionFormError("Topic, question text, and correct answer are required.");
      return;
    }

    if (questionType === "multiple_choice" && parsedAnswerOptions.length === 0) {
      setQuestionFormError("Multiple choice questions require at least one answer option.");
      return;
    }

    if (questionType === "short_text" && answerOptions.trim()) {
      setQuestionFormError("Short text questions cannot include answer options.");
      return;
    }

    const payload: CreateQuestionPayload = {
      topic_id: parsedTopicId,
      difficulty: parsedDifficulty,
      question_type: questionType,
      question_text: questionText,
      correct_answer: correctAnswer,
      accepted_answers: parsedAcceptedAnswers,
      answer_options: parsedAnswerOptions,
    };

    if (editingQuestionId !== null) {
      await updateQuestionMutation.mutateAsync({
        questionId: editingQuestionId,
        payload,
      });
      return;
    }

    await createQuestionMutation.mutateAsync(payload);
  }

  async function onTopicSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setTopicFormError("");
    setTopicNotice(null);

    if (!topicName.trim() || !topicDescription.trim()) {
      setTopicFormError("Topic name and description are required.");
      return;
    }

    const payload: CreateTopicPayload = {
      name: topicName.trim(),
      description: topicDescription.trim(),
    };

    if (editingTopicId !== null) {
      await updateTopicMutation.mutateAsync({
        topicId: editingTopicId,
        payload,
      });
      return;
    }

    await createTopicMutation.mutateAsync(payload);
  }

  function startEditingQuestion(question: Question): void {
    setQuestionNotice(null);
    setQuestionFormError("");
    setEditingQuestionId(question.id);
    setTopicId(String(question.topic_id));
    setDifficulty(String(question.difficulty));
    setQuestionType(question.question_type === "short_text" ? "short_text" : "multiple_choice");
    setQuestionText(question.question_text);
    setCorrectAnswer(question.correct_answer);
    setAcceptedAnswers(question.accepted_answers.join(", "));
    setAnswerOptions(question.answer_options.join(", "));
  }

  function startEditingTopic(topic: TopicSummary): void {
    setTopicNotice(null);
    setTopicFormError("");
    setEditingTopicId(topic.id);
    setTopicName(topic.name);
    setTopicDescription(topic.description);
  }

  function startEditingGoal(goal: Goal): void {
    setGoalNotice(null);
    setGoalFormError("");
    setEditingGoalId(goal.id);
    setGoalName(goal.name);
    setGoalDescription(goal.description);
  }

  async function onBulkImportSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setBulkNotice(null);

    try {
      const parsed = JSON.parse(bulkJson) as unknown;
      if (!Array.isArray(parsed)) {
        setBulkNotice({ tone: "error", message: "Bulk import JSON must be an array of question objects." });
        return;
      }
      await importQuestionsMutation.mutateAsync({
        items: parsed as CreateQuestionPayload[],
      });
    } catch {
      setBulkNotice({ tone: "error", message: "Bulk import JSON is invalid." });
    }
  }

  async function onCsvImportSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setBulkNotice(null);

    if (!bulkCsv.trim()) {
      setBulkNotice({ tone: "error", message: "Paste CSV content before importing." });
      return;
    }

    await importQuestionsCsvMutation.mutateAsync(bulkCsv);
  }

  async function onCsvFileChange(event: ChangeEvent<HTMLInputElement>): Promise<void> {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    const content = await file.text();
    setBulkCsv(content);
    setBulkNotice({ tone: "success", message: `Loaded CSV file: ${file.name}` });
  }

  function applyQuestionFilters(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    setQuestionPageOffset(0);
  }

  function clearQuestionFilters(): void {
    setFilterTopicId("all");
    setFilterQuestionType("all");
    setSearchQuery("");
    setQuestionPageOffset(0);
  }

  function handleDeleteCommunity(community: Community): void {
    const confirmed = confirmAction(
      `Delete community "${community.name}"? This will remove its membership and discussion context.`,
    );
    if (!confirmed) {
      return;
    }
    deleteCommunityMutation.mutate(community.id);
  }

  function handleDeleteGoal(goal: Goal): void {
    const confirmed = confirmAction(`Delete goal "${goal.name}"? This may affect roadmap and diagnostic curation.`);
    if (!confirmed) {
      return;
    }
    deleteGoalMutation.mutate(goal.id);
  }

  function handleDeleteGoalTopic(link: GoalTopic): void {
    const confirmed = confirmAction(
      `Remove topic "${getTopicName(link.topic_id)}" from goal "${getGoalName(link.goal_id)}"?`,
    );
    if (!confirmed) {
      return;
    }
    deleteGoalTopicMutation.mutate(link.id);
  }

  function handleDeleteBadge(badge: Badge): void {
    const confirmed = confirmAction(`Revoke badge "${badge.name}" from ${badge.user_email ?? getUserEmail(badge.user_id)}?`);
    if (!confirmed) {
      return;
    }
    deleteBadgeMutation.mutate(badge.id);
  }

  function handleDeletePrerequisite(link: TopicPrerequisite): void {
    const confirmed = confirmAction(
      `Delete prerequisite link "${getTopicName(link.prerequisite_topic_id)} -> ${getTopicName(link.topic_id)}"?`,
    );
    if (!confirmed) {
      return;
    }
    deletePrerequisiteMutation.mutate(link.id);
  }

  function handleResolveThread(thread: DiscussionThread): void {
    const actionLabel = thread.is_resolved ? "reopen" : "resolve";
    const confirmed = confirmAction(`Do you want to ${actionLabel} the thread "${thread.title}"?`);
    if (!confirmed) {
      return;
    }
    resolveThreadMutation.mutate({ threadId: thread.id, isResolved: !thread.is_resolved });
  }

  function handleDeleteTopic(topic: TopicSummary): void {
    const confirmed = confirmAction(`Delete topic "${topic.name}"? Questions and graph links may block this action.`);
    if (!confirmed) {
      return;
    }
    deleteTopicMutation.mutate(topic.id);
  }

  function handleDeleteQuestion(question: Question): void {
    const confirmed = confirmAction(`Delete question "${question.question_text}"?`);
    if (!confirmed) {
      return;
    }
    deleteQuestionMutation.mutate(question.id);
  }

  const questionTypeHelp =
    questionType === "multiple_choice"
      ? "Multiple choice questions require comma-separated answer options. The correct answer should match one of them."
      : "Short text questions must not include answer options. Add aliases as accepted answers when needed.";

  return (
    <RequireRole allowedRoles={["admin", "super_admin"]}>
      <RoleDashboardLayout
        roleLabel="Admin"
        title="Admin Dashboard"
        description="Manage tenant users, topics, questions, goals, and graph relationships through the connected backend administration APIs."
        navItems={[
          { label: "Admin Overview", href: "/dashboard/admin" },
          { label: "Student Panel", href: "/dashboard/student" },
          { label: "Teacher Panel", href: "/dashboard/teacher" },
          { label: "Super Admin", href: "/dashboard/super-admin" },
        ]}
      >

      <section className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <MetricCard title="Total Users" value={analytics.totalUsers} description="Users returned from the tenant-scoped `/users` API." tone="info" />
        </div>

        {ROLE_OPTIONS.map((roleName) => (
          <MetricCard
            key={roleName}
            title={roleName.replace("_", " ")}
            value={analytics.roleDistribution[roleName]}
            description="Role distribution"
          />
        ))}
      </section>

      <section className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="font-semibold text-slate-900">Tenant Scope</p>
            <p>Admin data is rendered for tenant {tenantId ?? "unknown"} only. Cross-tenant rows are ignored in the UI as a safety check.</p>
            {user?.role === "super_admin" && activeTenantScope ? (
              <div className="mt-2 flex flex-wrap items-center gap-3">
                <p className="text-amber-800">
                  Super-admin inspection mode is active. This workspace is currently rendering tenant #{activeTenantScope}.
                </p>
                <button
                  type="button"
                  onClick={clearActiveTenantScope}
                  className="rounded-xl border border-amber-300 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-amber-800 hover:bg-amber-100"
                >
                  Return to My Tenant
                </button>
              </div>
            ) : null}
          </div>
        </div>
      </section>

      <section className="mt-4 grid gap-4 md:grid-cols-3">
        <MetricCard title="Students with Roadmaps" value={analytics.studentCount} description="Learner progress returned from `/analytics/roadmap-progress`." tone="info" />
        <MetricCard title="Diagnostic Completion" value={`${analytics.diagnosticCompletionRate}%`} description="Tenant-wide completion rate from the analytics service." tone="success" />
        <MetricCard title="Roadmap Completion" value={`${analytics.roadmapCompletionRate}%`} description="Tenant-wide roadmap completion rate from persisted step statuses." tone="warning" />
      </section>

      <SurfaceCard
        title={editingGoalId !== null ? "Edit Goal" : "Create Goal"}
        description="Manage learning outcomes and map them to the topics used by diagnostics and roadmaps."
      >
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-lg font-semibold">Goal Management</h2>
          </div>
        </div>

        <div className="mt-4">
          <NoticeBanner notice={goalNotice} />
        </div>

        <form className="mt-4 grid gap-4 md:grid-cols-2" onSubmit={onGoalSubmit}>
          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="goalName">
              Goal Name
            </label>
            <input
              id="goalName"
              type="text"
              value={goalName}
              onChange={(event) => setGoalName(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
              required
            />
          </div>

          <div className="flex items-end">
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={createGoalMutation.isPending || updateGoalMutation.isPending}
                className="rounded-lg bg-brand-600 px-4 py-2 text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {createGoalMutation.isPending || updateGoalMutation.isPending
                  ? "Saving..."
                  : editingGoalId !== null
                    ? "Update Goal"
                    : "Create Goal"}
              </button>
              {editingGoalId !== null && (
                <button
                  type="button"
                  onClick={resetGoalForm}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-slate-700 transition hover:bg-slate-50"
                >
                  Cancel
                </button>
              )}
            </div>
          </div>

          <div className="md:col-span-2">
            <label className="text-sm font-medium text-slate-700" htmlFor="goalDescription">
              Description
            </label>
            <textarea
              id="goalDescription"
              value={goalDescription}
              onChange={(event) => setGoalDescription(event.target.value)}
              rows={3}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
              required
            />
          </div>
        </form>

        {goalFormError && <p className="mt-3 text-sm text-red-600">{goalFormError}</p>}

        <div className="mt-6 overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-3 font-medium">ID</th>
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">Description</th>
                <th className="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white text-slate-800">
              {goals.map((goal) => (
                <tr key={goal.id}>
                  <td className="px-4 py-3">{goal.id}</td>
                  <td className="px-4 py-3">{goal.name}</td>
                  <td className="px-4 py-3">{goal.description}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => startEditingGoal(goal)}
                        className="rounded-lg border border-slate-300 px-3 py-1.5 text-slate-700 transition hover:bg-slate-50"
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteGoal(goal)}
                        aria-label={`Delete Goal ${goal.name}`}
                        disabled={deleteGoalMutation.isPending}
                        className="rounded-lg border border-red-200 px-3 py-1.5 text-red-700 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <form className="mt-6 grid gap-4 md:grid-cols-3" onSubmit={onGoalTopicSubmit}>
          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="goalTopicGoalId">
              Goal
            </label>
            <select
              id="goalTopicGoalId"
              value={goalTopicGoalId}
              onChange={(event) => setGoalTopicGoalId(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
            >
              {goals.map((goal) => (
                <option key={goal.id} value={String(goal.id)}>
                  {goal.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="goalTopicTopicId">
              Topic
            </label>
            <select
              id="goalTopicTopicId"
              value={goalTopicTopicId}
              onChange={(event) => setGoalTopicTopicId(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
            >
              {topics.map((topic) => (
                <option key={topic.id} value={String(topic.id)}>
                  {topic.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={createGoalTopicMutation.isPending}
              className="rounded-lg bg-brand-600 px-4 py-2 text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {createGoalTopicMutation.isPending ? "Saving..." : "Add Goal Topic"}
            </button>
          </div>
        </form>

        <div className="mt-6 overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-3 font-medium">Goal</th>
                <th className="px-4 py-3 font-medium">Topic</th>
                <th className="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white text-slate-800">
              {goalTopics.map((link) => (
                <tr key={link.id}>
                  <td className="px-4 py-3">{getGoalName(link.goal_id)}</td>
                  <td className="px-4 py-3">{getTopicName(link.topic_id)}</td>
                  <td className="px-4 py-3">
                      <button
                        type="button"
                        onClick={() => handleDeleteGoalTopic(link)}
                        aria-label={`Delete Goal Topic ${link.id}`}
                        disabled={deleteGoalTopicMutation.isPending}
                        className="rounded-lg border border-red-200 px-3 py-1.5 text-red-700 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SurfaceCard>

      <section className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold">Create User</h2>
        <form className="mt-4 grid gap-4 md:grid-cols-2" onSubmit={onSubmit}>
          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
              required
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
              required
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="role">
              Role
            </label>
            <select
              id="role"
              value={role}
              onChange={(event) => setRole(event.target.value as AssignableUserRole)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
            >
              {ROLE_OPTIONS.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={createUserMutation.isPending}
              className="rounded-lg bg-brand-600 px-4 py-2 text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {createUserMutation.isPending ? "Creating..." : "Create User"}
            </button>
          </div>
        </form>

        {formError && <p className="mt-3 text-sm text-red-600">{formError}</p>}
      </section>

      <section className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-lg font-semibold">Topic Prerequisites</h2>
            <p className="mt-1 text-sm text-slate-500">
              Define dependency order so diagnostics and roadmaps follow the knowledge graph correctly.
            </p>
          </div>
        </div>

        <div className="mt-4">
          <NoticeBanner notice={prerequisiteNotice} />
        </div>

        <form className="mt-4 grid gap-4 md:grid-cols-3" onSubmit={onPrerequisiteSubmit}>
          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="dependentTopicId">
              Topic
            </label>
            <select
              id="dependentTopicId"
              value={dependentTopicId}
              onChange={(event) => setDependentTopicId(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
            >
              {topics.map((topic) => (
                <option key={topic.id} value={String(topic.id)}>
                  {topic.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="prerequisiteTopicId">
              Requires
            </label>
            <select
              id="prerequisiteTopicId"
              value={prerequisiteTopicId}
              onChange={(event) => setPrerequisiteTopicId(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
            >
              {topics.map((topic) => (
                <option key={topic.id} value={String(topic.id)}>
                  {topic.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={createPrerequisiteMutation.isPending}
              className="rounded-lg bg-brand-600 px-4 py-2 text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {createPrerequisiteMutation.isPending ? "Saving..." : "Add Link"}
            </button>
          </div>
        </form>

        {prerequisiteFormError && <p className="mt-3 text-sm text-red-600">{prerequisiteFormError}</p>}

        {prerequisitesQuery.isLoading && <p className="mt-4 text-slate-600">Loading prerequisite links...</p>}
        {prerequisitesQuery.isError && <p className="mt-4 text-red-600">Failed to load prerequisite links.</p>}

        {!prerequisitesQuery.isLoading && !prerequisitesQuery.isError && prerequisites.length === 0 && (
          <p className="mt-4 text-slate-600">No prerequisite links defined yet.</p>
        )}

        {prerequisites.length > 0 && (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-medium">Topic</th>
                  <th className="px-4 py-3 font-medium">Prerequisite</th>
                  <th className="px-4 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white text-slate-800">
                {prerequisites.map((link) => (
                  <tr key={link.id}>
                    <td className="px-4 py-3">{getTopicName(link.topic_id)}</td>
                    <td className="px-4 py-3">{getTopicName(link.prerequisite_topic_id)}</td>
                    <td className="px-4 py-3">
                      <button
                        type="button"
                        onClick={() => handleDeletePrerequisite(link)}
                        aria-label={`Delete Prerequisite ${link.id}`}
                        disabled={deletePrerequisiteMutation.isPending}
                        className="rounded-lg border border-red-200 px-3 py-1.5 text-red-700 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold">Users</h2>

        {usersQuery.isLoading && <p className="mt-4 text-slate-600">Loading users...</p>}
        {usersQuery.isError && <p className="mt-4 text-red-600">Failed to load users.</p>}

        {!usersQuery.isLoading && !usersQuery.isError && users.length === 0 && (
          <p className="mt-4 text-slate-600">No users found.</p>
        )}

        {users.length > 0 && (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-medium">ID</th>
                  <th className="px-4 py-3 font-medium">Email</th>
                  <th className="px-4 py-3 font-medium">Role</th>
                  <th className="px-4 py-3 font-medium">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white text-slate-800">
                {users.map((user) => (
                  <tr key={user.id}>
                    <td className="px-4 py-3">{user.id}</td>
                    <td className="px-4 py-3">{user.email}</td>
                    <td className="px-4 py-3 capitalize">{user.role.replace("_", " ")}</td>
                    <td className="px-4 py-3">{new Date(user.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold">Learner Roadmap Progress</h2>
        <p className="mt-1 text-sm text-slate-500">Student summaries returned directly from the tenant analytics endpoint.</p>

        {roadmapProgressSummaryQuery.isLoading ? <p className="mt-4 text-slate-600">Loading learner progress...</p> : null}
        {roadmapProgressSummaryQuery.isError ? <p className="mt-4 text-red-600">Failed to load learner progress.</p> : null}
        {!roadmapProgressSummaryQuery.isLoading && !roadmapProgressSummaryQuery.isError && learnerProgressRows.length === 0 ? (
          <p className="mt-4 text-slate-600">No student roadmap data available yet.</p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-medium">Student</th>
                  <th className="px-4 py-3 font-medium">Completion</th>
                  <th className="px-4 py-3 font-medium">Status Breakdown</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white text-slate-800">
                {learnerProgressRows.map((row) => (
                  <tr key={row.user_id}>
                    <td className="px-4 py-3">{row.email}</td>
                    <td className="px-4 py-3">
                      {row.completion_percent}% ({row.completed_steps}/{row.total_steps})
                    </td>
                    <td className="px-4 py-3">
                      {row.completed_steps} completed / {row.in_progress_steps} active / {row.pending_steps} pending
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-lg font-semibold">{editingTopicId !== null ? "Edit Topic" : "Create Topic"}</h2>
            <p className="mt-1 text-sm text-slate-500">
              Manage topic metadata used across diagnostics, roadmaps, and question libraries.
            </p>
          </div>
        </div>

        <div className="mt-4">
          <NoticeBanner notice={topicNotice} />
        </div>

        <form className="mt-4 grid gap-4 md:grid-cols-2" onSubmit={onTopicSubmit}>
          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="topicName">
              Topic Name
            </label>
            <input
              id="topicName"
              type="text"
              value={topicName}
              onChange={(event) => setTopicName(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
              required
            />
          </div>

          <div className="flex items-end">
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={createTopicMutation.isPending || updateTopicMutation.isPending}
                className="rounded-lg bg-brand-600 px-4 py-2 text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {createTopicMutation.isPending || updateTopicMutation.isPending
                  ? "Saving..."
                  : editingTopicId !== null
                    ? "Update Topic"
                    : "Create Topic"}
              </button>
              {editingTopicId !== null && (
                <button
                  type="button"
                  onClick={resetTopicForm}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-slate-700 transition hover:bg-slate-50"
                >
                  Cancel
                </button>
              )}
            </div>
          </div>

          <div className="md:col-span-2">
            <label className="text-sm font-medium text-slate-700" htmlFor="topicDescription">
              Description
            </label>
            <textarea
              id="topicDescription"
              value={topicDescription}
              onChange={(event) => setTopicDescription(event.target.value)}
              rows={3}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
              required
            />
          </div>
        </form>

        {topicFormError && <p className="mt-3 text-sm text-red-600">{topicFormError}</p>}

        <div className="mt-6 overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-3 font-medium">ID</th>
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">Description</th>
                <th className="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white text-slate-800">
              {topics.map((topic) => (
                <tr key={topic.id}>
                  <td className="px-4 py-3">{topic.id}</td>
                  <td className="px-4 py-3">{topic.name}</td>
                  <td className="px-4 py-3">{topic.description}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => startEditingTopic(topic)}
                        className="rounded-lg border border-slate-300 px-3 py-1.5 text-slate-700 transition hover:bg-slate-50"
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteTopic(topic)}
                        aria-label={`Delete Topic ${topic.name}`}
                        disabled={deleteTopicMutation.isPending}
                        className="rounded-lg border border-red-200 px-3 py-1.5 text-red-700 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-lg font-semibold">{editingQuestionId !== null ? "Edit Question" : "Create Question"}</h2>
            <p className="mt-1 text-sm text-slate-500">
              Build multiple-choice or short-text questions with answer validation rules.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={handleExportQuestions}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 transition hover:bg-slate-50"
            >
              Export JSON
            </button>
            <button
              type="button"
              onClick={handleExportQuestionsCsv}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 transition hover:bg-slate-50"
            >
              Export CSV
            </button>
          </div>
        </div>

        <div className="mt-4">
          <NoticeBanner notice={questionNotice} />
        </div>

        <form className="mt-4 grid gap-4 md:grid-cols-2" onSubmit={onQuestionSubmit}>
          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="topicId">
              Topic
            </label>
            <select
              id="topicId"
              value={topicId}
              onChange={(event) => setTopicId(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
              required
            >
              {topics.map((topic) => (
                <option key={topic.id} value={String(topic.id)}>
                  {topic.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="difficulty">
              Difficulty
            </label>
            <input
              id="difficulty"
              type="number"
              min={1}
              max={3}
              value={difficulty}
              onChange={(event) => setDifficulty(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
              required
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="questionType">
              Question Type
            </label>
            <select
              id="questionType"
              value={questionType}
              onChange={(event) => setQuestionType(event.target.value as (typeof QUESTION_TYPE_OPTIONS)[number])}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
            >
              {QUESTION_TYPE_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option.replace("_", " ")}
                </option>
              ))}
            </select>
            <p className="mt-2 text-xs text-slate-500">{questionTypeHelp}</p>
          </div>

          <div className="md:col-span-2">
            <label className="text-sm font-medium text-slate-700" htmlFor="questionText">
              Question Text
            </label>
            <textarea
              id="questionText"
              value={questionText}
              onChange={(event) => setQuestionText(event.target.value)}
              rows={3}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
              required
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="correctAnswer">
              Correct Answer
            </label>
            <input
              id="correctAnswer"
              type="text"
              value={correctAnswer}
              onChange={(event) => setCorrectAnswer(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
              required
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700" htmlFor="acceptedAnswers">
              Accepted Answers
            </label>
            <input
              id="acceptedAnswers"
              type="text"
              value={acceptedAnswers}
              onChange={(event) => setAcceptedAnswers(event.target.value)}
              placeholder="comma, separated, aliases"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
            />
          </div>

          {questionType === "multiple_choice" && (
            <div className="md:col-span-2">
              <label className="text-sm font-medium text-slate-700" htmlFor="answerOptions">
                Answer Options
              </label>
              <input
                id="answerOptions"
                type="text"
                value={answerOptions}
                onChange={(event) => setAnswerOptions(event.target.value)}
                placeholder="comma, separated, options"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
                required
              />
            </div>
          )}

          <div className="flex items-end">
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={createQuestionMutation.isPending || updateQuestionMutation.isPending}
                className="rounded-lg bg-brand-600 px-4 py-2 text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {createQuestionMutation.isPending || updateQuestionMutation.isPending
                  ? "Saving..."
                  : editingQuestionId !== null
                    ? "Update Question"
                    : "Create Question"}
              </button>
              {editingQuestionId !== null && (
                <button
                  type="button"
                  onClick={resetQuestionForm}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-slate-700 transition hover:bg-slate-50"
                >
                  Cancel
                </button>
              )}
            </div>
          </div>
        </form>

        {questionFormError && <p className="mt-3 text-sm text-red-600">{questionFormError}</p>}
      </section>

      <section className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-lg font-semibold">Question Library</h2>
            <p className="mt-1 text-sm text-slate-500">Browse, filter, and edit question content by topic and type.</p>
          </div>
          <form className="grid gap-3 md:grid-cols-[1fr_220px_220px_auto_auto]" onSubmit={applyQuestionFilters}>
            <input
              type="text"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search question text or correct answer"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none ring-brand-600 focus:ring-2"
            />

            <select
              value={filterTopicId}
              onChange={(event) => setFilterTopicId(event.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none ring-brand-600 focus:ring-2"
            >
              <option value="all">All topics</option>
              {topics.map((topic) => (
                <option key={topic.id} value={String(topic.id)}>
                  {topic.name}
                </option>
              ))}
            </select>

            <select
              value={filterQuestionType}
              onChange={(event) => setFilterQuestionType(event.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none ring-brand-600 focus:ring-2"
            >
              <option value="all">All question types</option>
              {QUESTION_TYPE_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option.replace("_", " ")}
                </option>
              ))}
            </select>

            <button
              type="submit"
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm text-white transition hover:bg-brand-700"
            >
              Apply
            </button>

            <button
              type="button"
              onClick={clearQuestionFilters}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 transition hover:bg-slate-50"
            >
              Reset
            </button>
          </form>
        </div>

        {questionMeta && (
          <p className="mt-4 text-sm text-slate-500">
            Showing {questionMeta.offset + 1}-{questionMeta.offset + questions.length} of {questionMeta.total} questions
          </p>
        )}

        {questionsQuery.isLoading && <p className="mt-4 text-slate-600">Loading questions...</p>}
        {questionsQuery.isError && <p className="mt-4 text-red-600">Failed to load questions.</p>}

        {!questionsQuery.isLoading && !questionsQuery.isError && questions.length === 0 && (
          <p className="mt-4 text-slate-600">No questions match the current filters.</p>
        )}

        {questions.length > 0 && (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-medium">Topic</th>
                  <th className="px-4 py-3 font-medium">Type</th>
                  <th className="px-4 py-3 font-medium">Difficulty</th>
                  <th className="px-4 py-3 font-medium">Question</th>
                  <th className="px-4 py-3 font-medium">Answer</th>
                  <th className="px-4 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white text-slate-800">
                {questions.map((question) => (
                  <tr key={question.id}>
                    <td className="px-4 py-3">{getTopicName(question.topic_id)}</td>
                    <td className="px-4 py-3 capitalize">{question.question_type.replace("_", " ")}</td>
                    <td className="px-4 py-3">{question.difficulty}</td>
                    <td className="px-4 py-3">{question.question_text}</td>
                    <td className="px-4 py-3">{question.correct_answer}</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => startEditingQuestion(question)}
                          className="rounded-lg border border-slate-300 px-3 py-1.5 text-slate-700 transition hover:bg-slate-50"
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteQuestion(question)}
                          aria-label={`Delete Question ${question.id}`}
                          disabled={deleteQuestionMutation.isPending}
                          className="rounded-lg border border-red-200 px-3 py-1.5 text-red-700 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {questionMeta && questionMeta.total > questionMeta.limit && (
          <div className="mt-4 flex items-center justify-between">
            <button
              type="button"
              onClick={() => setQuestionPageOffset(Math.max(0, questionPageOffset - questionMeta.limit))}
              disabled={questionPageOffset === 0}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              Previous
            </button>
            <p className="text-sm text-slate-500">
              Page {Math.floor(questionMeta.offset / questionMeta.limit) + 1} of{" "}
              {Math.max(1, Math.ceil(questionMeta.total / questionMeta.limit))}
            </p>
            <button
              type="button"
              onClick={() => setQuestionPageOffset(questionMeta.next_offset ?? questionMeta.offset)}
              disabled={questionMeta.next_offset === null}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              Next
            </button>
          </div>
        )}
      </section>

      <section className="mt-8 grid gap-6 lg:grid-cols-2">
        <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold">Bulk Import JSON</h2>
          <p className="mt-1 text-sm text-slate-500">
            Paste an array of question objects using the same shape as the JSON export.
          </p>
          <form className="mt-4" onSubmit={onBulkImportSubmit}>
            <textarea
              value={bulkJson}
              onChange={(event) => setBulkJson(event.target.value)}
              rows={10}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm outline-none ring-brand-600 focus:ring-2"
              placeholder='[{"topic_id":1,"difficulty":1,"question_type":"multiple_choice","question_text":"...","correct_answer":"...","accepted_answers":[],"answer_options":["A","B"]}]'
            />
            <button
              type="submit"
              disabled={importQuestionsMutation.isPending}
              className="mt-4 rounded-lg bg-brand-600 px-4 py-2 text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {importQuestionsMutation.isPending ? "Importing..." : "Import JSON"}
            </button>
          </form>
        </article>

        <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold">Bulk Import CSV</h2>
          <p className="mt-1 text-sm text-slate-500">
            Use CSV headers: <code>topic_id,difficulty,question_type,question_text,correct_answer,accepted_answers,answer_options</code>.
          </p>
          <form className="mt-4" onSubmit={onCsvImportSubmit}>
            <input
              type="file"
              accept=".csv,text/csv"
              onChange={onCsvFileChange}
              className="block w-full text-sm text-slate-600 file:mr-4 file:rounded-lg file:border-0 file:bg-slate-100 file:px-4 file:py-2 file:text-slate-700"
            />
            <textarea
              value={bulkCsv}
              onChange={(event) => setBulkCsv(event.target.value)}
              rows={10}
              className="mt-4 w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm outline-none ring-brand-600 focus:ring-2"
              placeholder={"topic_id,difficulty,question_type,question_text,correct_answer,accepted_answers,answer_options\n1,1,multiple_choice,What is 2 + 2?,4,four,3|4|5"}
            />
            <button
              type="submit"
              disabled={importQuestionsCsvMutation.isPending}
              className="mt-4 rounded-lg bg-brand-600 px-4 py-2 text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {importQuestionsCsvMutation.isPending ? "Importing..." : "Import CSV"}
            </button>
          </form>
        </article>
      </section>

      <section className="mt-6">
        <NoticeBanner notice={bulkNotice} />
      </section>

      <SurfaceCard
        title="Community Administration"
        description="Create tenant communities tied to topics, moderate discussion threads, and award mentor/community badges."
      >
        <div className="grid gap-4 md:grid-cols-3">
          <MetricCard title="Communities" value={communities.length} description="Topic communities in this tenant." tone="info" />
          <MetricCard title="Threads" value={discussionThreads.length} description="Open and resolved discussion threads." tone="warning" />
          <MetricCard title="Badges" value={communityBadges.length} description="Awarded mentor/community recognition badges." tone="success" />
        </div>

        <div className="mt-5 space-y-4">
          <NoticeBanner notice={communityNotice} />
          <NoticeBanner notice={badgeNotice} />
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-2">
          <section className="rounded-xl border border-slate-200 bg-slate-50 p-5">
            <h3 className="text-lg font-semibold text-slate-900">Create Community</h3>
            <form className="mt-4 space-y-4" onSubmit={onCommunitySubmit}>
              <div>
                <label className="text-sm font-medium text-slate-700" htmlFor="community-topic-id">
                  Topic
                </label>
                <select
                  id="community-topic-id"
                  value={communityTopicId}
                  onChange={(event) => setCommunityTopicId(event.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
                >
                  {topics.map((topic) => (
                    <option key={topic.id} value={String(topic.id)}>
                      {topic.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700" htmlFor="community-name">
                  Community Name
                </label>
                <input
                  id="community-name"
                  type="text"
                  value={communityName}
                  onChange={(event) => setCommunityName(event.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700" htmlFor="community-description">
                  Community Description
                </label>
                <textarea
                  id="community-description"
                  rows={3}
                  value={communityDescription}
                  onChange={(event) => setCommunityDescription(event.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
                />
              </div>
              {communityFormError && <p className="text-sm text-red-600">{communityFormError}</p>}
              <button
                type="submit"
                disabled={createCommunityMutation.isPending}
                className="rounded-lg bg-brand-600 px-4 py-2 text-white transition hover:bg-brand-700 disabled:opacity-60"
              >
                {createCommunityMutation.isPending ? "Creating..." : "Create Community"}
              </button>
            </form>
          </section>

          <section className="rounded-xl border border-slate-200 bg-slate-50 p-5">
            <h3 className="text-lg font-semibold text-slate-900">Award Badge</h3>
            <form className="mt-4 space-y-4" onSubmit={onBadgeSubmit}>
              <div>
                <label className="text-sm font-medium text-slate-700" htmlFor="badge-user-id">
                  User
                </label>
                <select
                  id="badge-user-id"
                  value={badgeUserId}
                  onChange={(event) => setBadgeUserId(event.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
                >
                  {users.map((user) => (
                    <option key={user.id} value={String(user.id)}>
                      {user.email} ({user.role})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700" htmlFor="badge-name">
                  Badge Name
                </label>
                <input
                  id="badge-name"
                  type="text"
                  value={badgeName}
                  onChange={(event) => setBadgeName(event.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700" htmlFor="badge-awarded-for">
                  Awarded For
                </label>
                <input
                  id="badge-awarded-for"
                  type="text"
                  value={badgeAwardedFor}
                  onChange={(event) => setBadgeAwardedFor(event.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700" htmlFor="badge-description">
                  Badge Description
                </label>
                <textarea
                  id="badge-description"
                  rows={3}
                  value={badgeDescription}
                  onChange={(event) => setBadgeDescription(event.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
                />
              </div>
              <button
                type="submit"
                disabled={createBadgeMutation.isPending}
                className="rounded-lg bg-brand-600 px-4 py-2 text-white transition hover:bg-brand-700 disabled:opacity-60"
              >
                {createBadgeMutation.isPending ? "Awarding..." : "Award Badge"}
              </button>
            </form>
          </section>
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-2">
          <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900">Existing Communities</h3>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <select
                aria-label="Filter Communities by Topic"
                value={communityFilterTopicId}
                onChange={(event) => {
                  setCommunityFilterTopicId(event.target.value);
                  setCommunityPageOffset(0);
                }}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none ring-brand-600 focus:ring-2"
              >
                <option value="all">All topics</option>
                {topics.map((topic) => (
                  <option key={topic.id} value={String(topic.id)}>
                    {topic.name}
                  </option>
                ))}
              </select>
              {communityMeta ? (
                <p className="text-sm text-slate-500">
                  Showing {communityMeta.offset + 1}-{communityMeta.offset + communities.length} of {communityMeta.total}
                </p>
              ) : null}
            </div>
            <ul className="mt-4 space-y-3">
              {communities.map((community) => (
                <li key={community.id} className="rounded-lg border border-slate-200 px-4 py-3">
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div>
                      <p className="font-medium text-slate-900">{community.name}</p>
                      <p className="text-sm text-slate-600">
                        {community.topic_name ?? `Topic ${community.topic_id}`} • {community.member_count} members • {community.thread_count} threads
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleDeleteCommunity(community)}
                      aria-label="Delete Community"
                      disabled={deleteCommunityMutation.isPending}
                      className="rounded-lg border border-red-200 px-3 py-2 text-sm text-red-700 transition hover:bg-red-50 disabled:opacity-60"
                    >
                      Delete
                    </button>
                  </div>
                </li>
              ))}
              {communities.length === 0 && <li className="text-sm text-slate-600">No communities created yet.</li>}
            </ul>
            {communityMeta && communityMeta.total > communityMeta.limit ? (
              <div className="mt-4 flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => setCommunityPageOffset(Math.max(0, communityPageOffset - communityMeta.limit))}
                  disabled={communityPageOffset === 0}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 transition hover:bg-slate-50 disabled:opacity-60"
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => setCommunityPageOffset(communityMeta.next_offset ?? communityMeta.offset)}
                  disabled={communityMeta.next_offset === null}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 transition hover:bg-slate-50 disabled:opacity-60"
                >
                  Next
                </button>
              </div>
            ) : null}
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900">Awarded Badges</h3>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <select
                aria-label="Filter Badges by User"
                value={badgeFilterUserId}
                onChange={(event) => {
                  setBadgeFilterUserId(event.target.value);
                  setBadgePageOffset(0);
                }}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none ring-brand-600 focus:ring-2"
              >
                <option value="all">All users</option>
                {users.map((user) => (
                  <option key={user.id} value={String(user.id)}>
                    {user.email}
                  </option>
                ))}
              </select>
              {badgeMeta ? (
                <p className="text-sm text-slate-500">
                  Showing {badgeMeta.offset + 1}-{badgeMeta.offset + communityBadges.length} of {badgeMeta.total}
                </p>
              ) : null}
            </div>
            <ul className="mt-4 space-y-3">
              {communityBadges.map((badge) => (
                <li key={badge.id} className="rounded-lg border border-slate-200 px-4 py-3">
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div>
                      <p className="font-medium text-slate-900">{badge.name}</p>
                      <p className="text-sm text-slate-600">
                        {badge.user_email ?? getUserEmail(badge.user_id)} • {badge.awarded_for}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleDeleteBadge(badge)}
                      aria-label="Revoke Badge"
                      disabled={deleteBadgeMutation.isPending}
                      className="rounded-lg border border-red-200 px-3 py-2 text-sm text-red-700 transition hover:bg-red-50 disabled:opacity-60"
                    >
                      Revoke
                    </button>
                  </div>
                </li>
              ))}
              {communityBadges.length === 0 && <li className="text-sm text-slate-600">No badges awarded yet.</li>}
            </ul>
            {badgeMeta && badgeMeta.total > badgeMeta.limit ? (
              <div className="mt-4 flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => setBadgePageOffset(Math.max(0, badgePageOffset - badgeMeta.limit))}
                  disabled={badgePageOffset === 0}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 transition hover:bg-slate-50 disabled:opacity-60"
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => setBadgePageOffset(badgeMeta.next_offset ?? badgeMeta.offset)}
                  disabled={badgeMeta.next_offset === null}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 transition hover:bg-slate-50 disabled:opacity-60"
                >
                  Next
                </button>
              </div>
            ) : null}
          </section>
        </div>

        <section className="mt-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-900">Thread Moderation</h3>
          <p className="mt-1 text-sm text-slate-500">Resolve or reopen discussion threads using the moderation endpoint.</p>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <select
              aria-label="Filter Threads by Community"
              value={threadFilterCommunityId}
              onChange={(event) => {
                setThreadFilterCommunityId(event.target.value);
                setThreadPageOffset(0);
              }}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none ring-brand-600 focus:ring-2"
            >
              <option value="all">All communities</option>
              {communities.map((community) => (
                <option key={community.id} value={String(community.id)}>
                  {community.name}
                </option>
              ))}
            </select>
            {threadMeta ? (
              <p className="text-sm text-slate-500">
                Showing {threadMeta.offset + 1}-{threadMeta.offset + discussionThreads.length} of {threadMeta.total}
              </p>
            ) : null}
          </div>
          <ul className="mt-4 space-y-3">
            {discussionThreads.map((thread) => (
              <li key={thread.id} className="rounded-lg border border-slate-200 px-4 py-4">
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <p className="font-medium text-slate-900">{thread.title}</p>
                    <p className="mt-1 text-sm text-slate-600">
                      {thread.community_name ?? `Community ${thread.community_id}`} • {thread.author_email ?? getUserEmail(thread.author_user_id)}
                    </p>
                    <p className="mt-2 text-sm text-slate-700">{thread.body}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleResolveThread(thread)}
                    disabled={resolveThreadMutation.isPending}
                    className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 transition hover:bg-slate-50 disabled:opacity-60"
                  >
                    {thread.is_resolved ? "Reopen Thread" : "Resolve Thread"}
                  </button>
                </div>
              </li>
            ))}
            {discussionThreads.length === 0 && <li className="text-sm text-slate-600">No threads available for moderation.</li>}
          </ul>
          {threadMeta && threadMeta.total > threadMeta.limit ? (
            <div className="mt-4 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setThreadPageOffset(Math.max(0, threadPageOffset - threadMeta.limit))}
                disabled={threadPageOffset === 0}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 transition hover:bg-slate-50 disabled:opacity-60"
              >
                Previous
              </button>
              <button
                type="button"
                onClick={() => setThreadPageOffset(threadMeta.next_offset ?? threadMeta.offset)}
                disabled={threadMeta.next_offset === null}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 transition hover:bg-slate-50 disabled:opacity-60"
              >
                Next
              </button>
            </div>
          ) : null}
        </section>
      </SurfaceCard>
      </RoleDashboardLayout>
    </RequireRole>
  );
}
