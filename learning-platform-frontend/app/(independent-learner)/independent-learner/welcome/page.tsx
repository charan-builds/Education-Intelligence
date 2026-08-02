"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import PageHeader from "@/components/layouts/PageHeader";
import WelcomeCard from "@/components/independent-learner/WelcomeCard";
import MetricCard from "@/components/ui/MetricCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { useAuth } from "@/hooks/useAuth";
import { getCurrentGoal } from "@/services/goalService";
import { getProfileProgress, getProfileStatus } from "@/services/profileService";
import { appRoutes } from "@/utils/appRoutes";

const QUOTES = [
  "Small steps, repeated with intent, become real mastery.",
  "You do not need perfect momentum, only honest consistency.",
  "Every concept you clarify today makes tomorrow lighter.",
  "A focused learner can outperform a scattered expert.",
];

export default function IndependentLearnerWelcomePage() {
  const { user } = useAuth();
  const statusQuery = useQuery({
    queryKey: ["independent-learner", "profile", "status"],
    queryFn: getProfileStatus,
  });
  const progressQuery = useQuery({
    queryKey: ["independent-learner", "profile", "progress"],
    queryFn: getProfileProgress,
  });
  const currentGoalQuery = useQuery({
    queryKey: ["independent-learner", "goals", "current"],
    queryFn: getCurrentGoal,
  });

  const quote = useMemo(() => {
    const indexSeed = (user?.user_id ?? 1) + (statusQuery.data?.missing_required_fields.length ?? 0);
    return QUOTES[indexSeed % QUOTES.length];
  }, [statusQuery.data?.missing_required_fields.length, user?.user_id]);

  const profileCompleted = Boolean(statusQuery.data?.profile_completed);
  const continueHref = !profileCompleted
    ? appRoutes.independentLearner.onboarding
    : currentGoalQuery.data
      ? appRoutes.independentLearner.dashboard
      : appRoutes.independentLearner.goals;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Welcome"
        title="Your independent learner workspace is almost ready"
        description="This screen gives the learner a clear first moment after sign-in, reinforces momentum, and points to the next step."
        meta={
          <>
            <MetricCard title="Profile" value={profileCompleted ? "Ready" : "Setup"} tone={profileCompleted ? "success" : "warning"} />
            <MetricCard title="Completion" value={`${progressQuery.data?.completion_percent ?? 0}%`} tone="info" />
            <MetricCard title="Missing fields" value={statusQuery.data?.missing_required_fields.length ?? 0} tone="info" />
          </>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[1.08fr_0.92fr]">
        <WelcomeCard
          name={user?.full_name ?? user?.email ?? "Learner"}
          quote={quote}
          continueHref={continueHref}
          continueLabel={!profileCompleted ? "Continue Setup" : currentGoalQuery.data ? "Open Dashboard" : "Choose Goal"}
          completionPercent={progressQuery.data?.completion_percent ?? 0}
        />

        <SurfaceCard
          title="What happens next"
          description="The onboarding flow captures the signals the platform needs before it can pace diagnostics, roadmap steps, and recommendations intelligently."
          className="border-violet-200 bg-violet-50/70 dark:border-violet-700 dark:bg-violet-900/20"
        >
          <div className="space-y-3 text-sm leading-7 text-slate-700 dark:text-slate-300">
            <p>- Basic profile data personalizes your workspace identity and welcome state.</p>
            <p>- Academic context grounds roadmap difficulty and examples.</p>
            <p>- Social profile links make your learner identity richer and more portable.</p>
            <p>- Learning preferences control roadmap pacing and recommendation quality.</p>
            <p>- Smart onboarding completion creates a learning profile the backend can use for diagnostics and roadmap generation.</p>
            <p>- Goal selection locks in the destination before the adaptive diagnostic begins.</p>
          </div>
        </SurfaceCard>
      </div>
    </div>
  );
}
