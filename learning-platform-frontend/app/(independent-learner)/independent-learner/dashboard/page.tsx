"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import AccessState from "@/components/auth/AccessState";
import IndependentLearnerDashboard from "@/components/independent-learner/IndependentLearnerDashboard";
import { getIndependentLearnerDashboard } from "@/services/dashboardService";
import { getCurrentGoal } from "@/services/goalService";
import { appRoutes } from "@/utils/appRoutes";

export default function IndependentLearnerDashboardPage() {
  const router = useRouter();
  const currentGoalQuery = useQuery({
    queryKey: ["independent-learner", "goals", "current"],
    queryFn: getCurrentGoal,
  });
  const dashboardQuery = useQuery({
    queryKey: ["independent-learner", "dashboard"],
    queryFn: getIndependentLearnerDashboard,
    enabled: Boolean(currentGoalQuery.data),
  });

  useEffect(() => {
    if (currentGoalQuery.isLoading) {
      return;
    }
    if (!currentGoalQuery.data) {
      router.replace(appRoutes.independentLearner.goals);
    }
  }, [currentGoalQuery.data, currentGoalQuery.isLoading, router]);

  if (currentGoalQuery.isLoading) {
    return <AccessState mode="loading" description="Checking your active learning goal..." />;
  }

  if (!currentGoalQuery.data) {
    return <AccessState mode="redirecting" description="Redirecting to goal selection..." />;
  }

  if (dashboardQuery.isLoading) {
    return <AccessState mode="loading" description="Loading your dashboard..." />;
  }

  if (dashboardQuery.isError || !dashboardQuery.data) {
    return (
      <AccessState
        mode="unauthorized"
        title="Dashboard unavailable"
        description="We could not load your dashboard right now."
        redirectHref={appRoutes.independentLearner.roadmap}
        redirectLabel="Open roadmap"
      />
    );
  }

  return <IndependentLearnerDashboard payload={dashboardQuery.data} />;
}
