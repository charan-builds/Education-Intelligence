"use client";

import { useEffect, useMemo, useState } from "react";

type WeakTopic = {
  topicId: number;
  name: string;
  gap: number;
  score: number;
};

type DueReview = {
  topic_id: number;
  topic_name: string;
  retention_score: number;
};

type StudentDashboardView = {
  kpis: {
    completionPercent: number;
    weakTopicCount: number;
    streakDays: number;
    focusScore: number;
    inProgress: number;
    totalSteps: number;
    xp: number;
  };
  weakTopics: WeakTopic[];
  retention: {
    average_retention_score: number;
    due_reviews: DueReview[];
  };
  mentorSuggestions: Array<{ title: string; message: string; why: string }>;
  recentActivity: Array<{ title: string; subtitle: string; tone?: string }>;
};

type FeatureKey = "mentor" | "review" | "roadmap" | "career" | "community";

type AdaptiveFeature = {
  key: FeatureKey;
  title: string;
  reason: string;
  score: number;
};

export function useAdaptiveStudentUI(dashboard: StudentDashboardView) {
  const [focusMode, setFocusMode] = useState(false);
  const [featureUsage, setFeatureUsage] = useState<Record<FeatureKey, number>>({
    mentor: 0,
    review: 0,
    roadmap: 0,
    career: 0,
    community: 0,
  });

  useEffect(() => {
    const raw = window.localStorage.getItem("adaptive-student-ui");
    if (!raw) {
      return;
    }
    try {
      const parsed = JSON.parse(raw) as { focusMode?: boolean; featureUsage?: Record<FeatureKey, number> };
      setFocusMode(Boolean(parsed.focusMode));
      if (parsed.featureUsage) {
        setFeatureUsage((current) => ({ ...current, ...parsed.featureUsage }));
      }
    } catch {
      return;
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem("adaptive-student-ui", JSON.stringify({ focusMode, featureUsage }));
  }, [featureUsage, focusMode]);

  const emotionalState = useMemo(() => {
    if (dashboard.kpis.focusScore < 45 || dashboard.kpis.weakTopicCount >= 3 || dashboard.kpis.streakDays === 0) {
      return {
        tone: "supportive",
        label: "Frustration risk",
        message: "The interface is simplifying the next step and reducing noise because progress signals look strained.",
      };
    }
    if (dashboard.retention.due_reviews.length >= 2 || dashboard.retention.average_retention_score < 65) {
      return {
        tone: "urgent",
        label: "Recovery mode",
        message: "Memory pressure is rising, so the UI is pushing revision and recovery actions to the front.",
      };
    }
    if (dashboard.kpis.completionPercent >= 60 && dashboard.kpis.weakTopicCount <= 1) {
      return {
        tone: "celebratory",
        label: "High momentum",
        message: "You are moving well, so the UI is surfacing stretch features and visible progress signals.",
      };
    }
    return {
      tone: "balanced",
      label: "Steady progress",
      message: "The interface is balancing execution, review, and AI guidance based on your current learning rhythm.",
    };
  }, [dashboard.kpis.completionPercent, dashboard.kpis.focusScore, dashboard.kpis.streakDays, dashboard.kpis.weakTopicCount, dashboard.retention.average_retention_score, dashboard.retention.due_reviews.length]);

  const nextBestAction = useMemo(() => {
    const topWeakTopic = dashboard.weakTopics[0];
    const nextReview = dashboard.retention.due_reviews[0];
    const topSuggestion = dashboard.mentorSuggestions[0];

    if (nextReview) {
      return {
        kind: "review",
        title: `Reinforce ${nextReview.topic_name}`,
        description: `Retention dipped to ${Math.round(nextReview.retention_score)}%, so a short review now is higher leverage than new content.`,
        ctaLabel: "Enter focus review",
        prompt: `Coach me through a fast recovery session for ${nextReview.topic_name}. Keep it focused and practical.`,
      };
    }
    if (topWeakTopic) {
      return {
        kind: "recover",
        title: `Recover ${topWeakTopic.name}`,
        description: `This topic has the largest mastery gap at ${Math.round(topWeakTopic.score)}%, so improving it unlocks the most downstream progress.`,
        ctaLabel: "Ask AI mentor",
        prompt: `Help me recover ${topWeakTopic.name}. Explain the concept simply and then give me a 20-minute study plan.`,
      };
    }
    if (topSuggestion) {
      return {
        kind: "guidance",
        title: topSuggestion.title,
        description: topSuggestion.why,
        ctaLabel: "Open guided step",
        prompt: `Use this suggestion as context and guide me: ${topSuggestion.message}`,
      };
    }
    return {
      kind: "continue",
      title: "Keep the current streak alive",
      description: "No urgent gaps were detected, so the best move is a small focused session to preserve momentum.",
      ctaLabel: "Start focus mode",
      prompt: "Give me a 25-minute focus session for my current roadmap.",
    };
  }, [dashboard.mentorSuggestions, dashboard.retention.due_reviews, dashboard.weakTopics]);

  const rankedFeatures = useMemo<AdaptiveFeature[]>(() => {
    const topWeakTopic = dashboard.weakTopics[0];
    const features: AdaptiveFeature[] = [
      {
        key: "mentor",
        title: "AI mentor",
        reason: topWeakTopic ? `Best for resolving ${topWeakTopic.name} quickly.` : "Best for translating current signals into one clear study move.",
        score: 70 + (dashboard.kpis.weakTopicCount * 6) + (featureUsage.mentor * 3),
      },
      {
        key: "review",
        title: "Review queue",
        reason: dashboard.retention.due_reviews.length > 0 ? "Retention pressure is building right now." : "Use this when memory durability starts to slip.",
        score: 45 + (dashboard.retention.due_reviews.length * 20),
      },
      {
        key: "roadmap",
        title: "Roadmap",
        reason: dashboard.kpis.inProgress === 0 ? "No active step is in motion, so roadmap guidance matters more." : "Track the next unlock and execution sequence.",
        score: 50 + (dashboard.kpis.inProgress === 0 ? 20 : 0) + (featureUsage.roadmap * 2),
      },
      {
        key: "career",
        title: "Career engine",
        reason: dashboard.kpis.completionPercent >= 45 ? "Readiness and resume value are becoming more credible." : "Unlock this once progress has more signal behind it.",
        score: 30 + (dashboard.kpis.completionPercent >= 45 ? 25 : 0) + (featureUsage.career * 3),
      },
      {
        key: "community",
        title: "Live community",
        reason: emotionalState.tone === "supportive" ? "Lower priority while the UI is reducing noise." : "Useful when momentum is stable and you want social energy.",
        score: 20 + (featureUsage.community * 3) - (emotionalState.tone === "supportive" ? 18 : 0),
      },
    ];

    return features.sort((left, right) => right.score - left.score);
  }, [dashboard.kpis.completionPercent, dashboard.kpis.inProgress, dashboard.kpis.weakTopicCount, dashboard.retention.due_reviews.length, emotionalState.tone, featureUsage]);

  const visibleSections = useMemo(() => {
    const hideAmbient = focusMode || emotionalState.tone === "supportive";
    return {
      demoMode: !hideAmbient,
      livePulse: !hideAmbient,
      leaderboard: emotionalState.tone === "celebratory" || featureUsage.community > 0,
      badges: emotionalState.tone !== "supportive",
      gamification: emotionalState.tone !== "supportive" && !focusMode,
      weakTopicsFirst: emotionalState.tone === "supportive" || emotionalState.tone === "urgent",
      reviewFirst: dashboard.retention.due_reviews.length > 0,
    };
  }, [dashboard.retention.due_reviews.length, emotionalState.tone, featureUsage.community, focusMode]);

  const smartNotifications = useMemo(() => {
    const items = [];
    if (dashboard.retention.due_reviews.length > 0) {
      items.push({
        title: `Review ${dashboard.retention.due_reviews[0].topic_name} today`,
        message: "The system moved this up because your retention signal is dropping now, not later.",
        severity: "warning",
      });
    }
    if (dashboard.kpis.streakDays === 0) {
      items.push({
        title: "Restart momentum with one short win",
        message: "A 15-minute focused session is enough to get the adaptive coach back into a high-confidence state.",
        severity: "high",
      });
    }
    if (dashboard.kpis.completionPercent >= 60) {
      items.push({
        title: "You are close to a visible milestone",
        message: "The interface is surfacing career and mastery features because your progress is now meaningful enough to showcase.",
        severity: "success",
      });
    }
    return items.slice(0, 3);
  }, [dashboard.kpis.completionPercent, dashboard.kpis.streakDays, dashboard.retention.due_reviews]);

  const recordFeatureUse = (key: FeatureKey) => {
    setFeatureUsage((current) => ({ ...current, [key]: current[key] + 1 }));
  };

  return {
    focusMode,
    setFocusMode,
    emotionalState,
    nextBestAction,
    rankedFeatures,
    visibleSections,
    smartNotifications,
    recordFeatureUse,
  };
}
