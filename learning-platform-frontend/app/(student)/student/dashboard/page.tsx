"use client";

import React from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import {
  ArrowRight,
  BadgeCheck,
  Brain,
  Flame,
  Library,
  MessageSquareMore,
  Rocket,
  Sparkles,
  Star,
  Target,
  Trophy,
  Wand2,
} from "lucide-react";

import PageHeader from "@/components/layouts/PageHeader";
import { useRealtime } from "@/components/providers/RealtimeProvider";
import MetricCard from "@/components/ui/MetricCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import EmptyState from "@/components/ui/EmptyState";
import StatusPill from "@/components/ui/StatusPill";
import Skeleton from "@/components/ui/Skeleton";
import { useAdaptiveStudentUI } from "@/hooks/useAdaptiveStudentUI";
import { useAuth } from "@/hooks/useAuth";
import { useStudentDashboard } from "@/hooks/useDashboard";
import { getLearnerRoutes } from "@/utils/appRoutes";

const ActivityFeed = dynamic(() => import("@/components/dashboard/ActivityFeed"));
const RecommendationPanel = dynamic(() => import("@/components/dashboard/RecommendationPanel"));
const DistributionBarChart = dynamic(() => import("@/components/charts/DistributionBarChart"));
const ProgressLineChart = dynamic(() => import("@/components/charts/ProgressLineChart"));
const MasteryPieChart = dynamic(() => import("@/components/charts/MasteryPieChart"));
const DemoModeShowcase = dynamic(() => import("@/components/student/DemoModeShowcase"));
const AdaptiveGuidancePanel = dynamic(() => import("@/components/student/AdaptiveGuidancePanel"));
const ProgressStoryTimeline = dynamic(() => import("@/components/student/ProgressStoryTimeline"));

export default function StudentDashboardPage() {
  const { role } = useAuth();
  const learnerRoutes = getLearnerRoutes(role);
  const dashboard = useStudentDashboard();
  const { activeUsers, connectionStatus, liveEvents } = useRealtime();
  const isLoading = dashboard.queries.dashboardQuery.isLoading && !dashboard.queries.dashboardQuery.data;
  const topWeakTopic = dashboard.weakTopics[0];
  const nextReview = dashboard.retention.due_reviews[0];
  const activeBadges = dashboard.badges.slice(0, 3);
  const adaptiveUI = useAdaptiveStudentUI(dashboard);
  const focusShellClassName = adaptiveUI.focusMode
    ? "mx-auto max-w-5xl space-y-6 rounded-[40px] border border-white/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.96),rgba(248,250,252,0.98))] p-4 shadow-[0_40px_120px_rgba(15,23,42,0.12)] md:p-6"
    : "";

  const storyMoments = [
    {
      title: `${dashboard.kpis.completed} milestones already closed`,
      description: "Your completed roadmap steps are now compounding into stronger topic mastery and visible momentum.",
      tone: "complete" as const,
    },
    {
      title: topWeakTopic ? `Recover ${topWeakTopic.name} to unlock faster progress` : "Stay in the flow state",
      description: topWeakTopic
        ? `AI signals show the biggest upside is in ${topWeakTopic.name}. Closing that gap will improve confidence and roadmap velocity.`
        : "You are in a clean learning lane with no major weak-topic pressure right now.",
      tone: "active" as const,
    },
    {
      title: nextReview ? `Next retention moment: ${nextReview.topic_name}` : "Next unlock is already in motion",
      description: nextReview
        ? `Spaced review is due soon, giving you a timed opportunity to keep ${nextReview.topic_name} from fading.`
        : "Your review queue is under control, so the next opportunity is deeper progression rather than recovery.",
      tone: "upcoming" as const,
    },
  ];

  const demoSteps = [
    {
      accent: "Guided walkthrough",
      title: "Watch the platform narrate a learner’s journey in under 30 seconds",
      description: "Demo mode spotlights progress, AI coaching, and roadmap momentum with a polished investor-friendly sequence.",
    },
    {
      accent: "AI showcase",
      title: "Showcase explainability, coaching, and question generation in one click",
      description: "The mentor becomes the product hero by turning weak-topic insights into immediate high-value actions.",
    },
    {
      accent: "Gamification",
      title: "Turn achievement into a visible, emotional progression system",
      description: "XP, streaks, badges, and leaderboard momentum make this feel like a product people return to, not just finish.",
    },
  ];

  return (
    <div className={`space-y-7 ${focusShellClassName}`}>
      <PageHeader
        eyebrow={role === "independent_learner" ? "Independent learner workspace" : "Student workspace"}
        title={adaptiveUI.focusMode ? "Focus mode: one clear path forward" : "An adaptive learning command center"}
        description={
          adaptiveUI.focusMode
            ? "The interface has reduced noise and moved the highest-leverage action to the front."
            : "This dashboard adapts to learning behavior, highlights what matters now, and downranks features that are less relevant in the moment."
        }
        actions={
          <>
            <Link
              href={learnerRoutes.roadmap}
              onClick={() => adaptiveUI.recordFeatureUse("roadmap")}
              className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white/90 px-4 py-3 text-sm font-semibold text-slate-900 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            >
              View roadmap
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href={`${learnerRoutes.mentor}?prompt=${encodeURIComponent(
                topWeakTopic
                  ? `Coach me through ${topWeakTopic.name}. Explain why it matters, then give me 3 practice questions.`
                  : "Give me a high-impact study plan for today based on my current dashboard.",
              )}`}
              onClick={() => adaptiveUI.recordFeatureUse("mentor")}
              className="inline-flex items-center gap-2 rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white"
            >
              Launch AI mentor
              <Sparkles className="h-4 w-4 text-amber-300" />
            </Link>
          </>
        }
        meta={
          <>
            <StatusPill label={`${dashboard.kpis.completionPercent}% complete`} tone="success" />
            <StatusPill label={`${dashboard.kpis.streakDays} day streak`} tone="warning" />
            <StatusPill label={`${dashboard.kpis.focusScore} focus score`} tone="default" />
            <StatusPill
              label={
                connectionStatus === "live"
                  ? `${activeUsers} learners live`
                  : connectionStatus === "reconnecting"
                    ? "Reconnecting live sync"
                    : connectionStatus === "connecting"
                      ? "Connecting live sync"
                      : "Live sync offline"
              }
              tone={connectionStatus === "live" ? "success" : connectionStatus === "offline" ? "danger" : "warning"}
            />
            <StatusPill label={adaptiveUI.emotionalState.label} tone={adaptiveUI.emotionalState.tone === "supportive" ? "warning" : "default"} />
            <StatusPill label={`Level ${Math.max(1, Math.floor(dashboard.kpis.xp / 250) + 1)}`} tone="default" />
          </>
        }
      />

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-40" />
          ))}
        </div>
      ) : null}

      {!isLoading ? (
        <>
          {dashboard.roadmapStatus === "failed" ? (
            <EmptyState
              title="Roadmap refresh needs attention"
              description={dashboard.roadmapErrorMessage ?? "Your previous progress is still visible, but the latest roadmap refresh did not complete."}
            />
          ) : null}
          <AdaptiveGuidancePanel
            emotionalState={adaptiveUI.emotionalState}
            nextBestAction={adaptiveUI.nextBestAction}
            rankedFeatures={adaptiveUI.rankedFeatures}
            focusMode={adaptiveUI.focusMode}
            onToggleFocusMode={() => adaptiveUI.setFocusMode(!adaptiveUI.focusMode)}
          />

          {adaptiveUI.smartNotifications.length > 0 ? (
            <div className="grid gap-3 md:grid-cols-3">
              {adaptiveUI.smartNotifications.map((item, index) => (
                <div key={`${item.title}-${index}`} className="story-card">
                  <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">{item.title}</p>
                  <p className="mt-3 text-sm leading-7 text-slate-700">{item.message}</p>
                </div>
              ))}
            </div>
          ) : null}

          <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
            <motion.section
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, ease: "easeOut" }}
              className="premium-hero soft-ring relative overflow-hidden rounded-[38px] border border-white/70 p-7"
            >
              <div className="premium-orb -left-10 top-8 h-28 w-28 bg-teal-300/30" />
              <div className="premium-orb right-8 top-0 h-32 w-32 bg-orange-300/25" style={{ animationDelay: "1.3s" }} />
              <div className="premium-orb bottom-2 left-1/3 h-24 w-24 bg-cyan-300/25" style={{ animationDelay: "2.1s" }} />

              <div className="relative">
                <div className="inline-flex items-center gap-2 rounded-full border border-white/80 bg-white/70 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.26em] text-slate-700">
                  <Rocket className="h-3.5 w-3.5 text-brand-700" />
                  Investor-ready narrative
                </div>
                <h2 className="mt-5 max-w-2xl text-4xl font-semibold tracking-tight text-slate-950 md:text-5xl">
                  Progress feels alive when every signal tells one story.
                </h2>
                <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-600">
                  The learner has built <span className="font-semibold text-slate-950">{dashboard.kpis.xp} XP</span>, maintained a{" "}
                  <span className="font-semibold text-slate-950">{dashboard.kpis.streakDays}-day streak</span>, and is now one focused push away from
                  the next mastery leap.
                </p>

                <div className="mt-6 grid gap-3 md:grid-cols-3">
                  <div className="story-card">
                    <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">North star</p>
                    <p className="mt-3 text-xl font-semibold text-slate-950">{topWeakTopic?.name ?? "High focus mode"}</p>
                    <p className="mt-2 text-sm leading-6 text-slate-600">Biggest recovery opportunity with the strongest expected impact.</p>
                  </div>
                  <div className="story-card">
                    <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Momentum</p>
                    <p className="mt-3 text-xl font-semibold text-slate-950">{dashboard.kpis.leaderboardLead}</p>
                    <p className="mt-2 text-sm leading-6 text-slate-600">Social proof and visible progress push consistency higher.</p>
                  </div>
                  <div className="story-card">
                    <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Retention</p>
                    <p className="mt-3 text-xl font-semibold text-slate-950">{dashboard.retention.average_retention_score}%</p>
                    <p className="mt-2 text-sm leading-6 text-slate-600">Memory durability based on spaced review pressure and recovery timing.</p>
                  </div>
                </div>
              </div>
            </motion.section>

            {adaptiveUI.visibleSections.demoMode ? <DemoModeShowcase steps={demoSteps} /> : null}
          </div>

          <SurfaceCard
            title="Cognitive model"
            description="The platform now detects confusion, repeated misunderstanding patterns, and the teaching style most likely to help this learner."
          >
            <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
              <div className="rounded-[28px] border border-slate-200 bg-white/70 p-5 dark:border-slate-700 dark:bg-slate-900/70">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Current teaching mode</p>
                <p className="mt-3 text-2xl font-semibold text-slate-950 dark:text-slate-100">
                  {dashboard.cognitiveModel.confusion_level} confusion
                </p>
                <p className="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-400">
                  {dashboard.cognitiveModel.teaching_style}
                </p>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl bg-amber-50/80 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-700">Confusion signals</p>
                  <div className="mt-3 space-y-2 text-sm leading-7 text-amber-950">
                    {(dashboard.cognitiveModel.confusion_signals.length
                      ? dashboard.cognitiveModel.confusion_signals
                      : ["No major confusion signals detected right now."]).map((item, index) => (
                      <p key={`${item}-${index}`}>- {item}</p>
                    ))}
                  </div>
                </div>
                <div className="rounded-2xl bg-indigo-50/80 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-700">Misunderstanding patterns</p>
                  <div className="mt-3 space-y-2 text-sm leading-7 text-indigo-950">
                    {(dashboard.cognitiveModel.misunderstanding_patterns.length
                      ? dashboard.cognitiveModel.misunderstanding_patterns
                      : ["No repeated misunderstanding pattern is dominant yet."]).map((item, index) => (
                      <p key={`${item}-${index}`}>- {item}</p>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            <div className="mt-4 rounded-[24px] border border-emerald-200 bg-emerald-50/70 p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700">Adaptive teaching plan</p>
              <div className="mt-3 grid gap-2 text-sm leading-7 text-emerald-950 md:grid-cols-2">
                {(dashboard.cognitiveModel.adaptive_actions.length
                  ? dashboard.cognitiveModel.adaptive_actions
                  : ["Keep alternating explanation and practice."]).map((item, index) => (
                  <p key={`${item}-${index}`}>- {item}</p>
                ))}
              </div>
            </div>
          </SurfaceCard>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              eyebrow="Roadmap"
              title="Completion"
              value={`${dashboard.kpis.completionPercent}%`}
              description={`${dashboard.kpis.completed}/${dashboard.kpis.totalSteps} steps completed`}
              tone="info"
              icon={<Target className="h-5 w-5" />}
            />
            <MetricCard
              eyebrow="Now learning"
              title="Streak"
              value={`${dashboard.kpis.streakDays} days`}
              description={`${dashboard.kpis.inProgress} steps currently in motion`}
              tone="success"
              icon={<Flame className="h-5 w-5" />}
            />
            <MetricCard
              eyebrow="Attention"
              title="Focus score"
              value={dashboard.kpis.focusScore}
              description={`${dashboard.kpis.weakTopicCount} weak topics detected`}
              tone="warning"
              icon={<Brain className="h-5 w-5" />}
            />
            <MetricCard
              eyebrow="Gamification"
              title="Experience"
              value={`${dashboard.kpis.xp} XP`}
              description={dashboard.kpis.leaderboardLead}
              icon={<Trophy className="h-5 w-5" />}
            />
          </div>

          <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
            <SurfaceCard
              title="AI learning studio"
              description="Make the AI mentor the hero of the demo with direct, outcome-oriented actions."
              className="mesh-panel"
            >
              <div className="grid gap-3 md:grid-cols-3">
                <Link
                  href={`${learnerRoutes.mentor}?prompt=${encodeURIComponent(
                    topWeakTopic
                      ? `Explain ${topWeakTopic.name} to me like a top startup mentor: simple intuition, real-world analogy, and when learners usually get stuck.`
                      : "Explain the most important concept I should focus on next in simple terms.",
                  )}`}
                  onClick={() => adaptiveUI.recordFeatureUse("mentor")}
                  className="story-card block transition duration-200 hover:-translate-y-1.5"
                >
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-950 text-white">
                    <Brain className="h-5 w-5 text-emerald-300" />
                  </div>
                  <p className="mt-4 text-lg font-semibold text-slate-950">Explain topic</p>
                  <p className="mt-2 text-sm leading-6 text-slate-600">Turn a weak concept into a clean, memorable explanation.</p>
                </Link>
                <Link
                  href={`${learnerRoutes.mentor}?prompt=${encodeURIComponent(
                    topWeakTopic
                      ? `Generate 5 interview-style questions on ${topWeakTopic.name}, ordered from basic to advanced, with short answers after each one.`
                      : "Generate 5 high-signal practice questions for my current learning plan with short answers.",
                  )}`}
                  onClick={() => adaptiveUI.recordFeatureUse("mentor")}
                  className="story-card block transition duration-200 hover:-translate-y-1.5"
                >
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-700 text-white">
                    <Wand2 className="h-5 w-5 text-amber-200" />
                  </div>
                  <p className="mt-4 text-lg font-semibold text-slate-950">Generate questions</p>
                  <p className="mt-2 text-sm leading-6 text-slate-600">Create recruiter-ready practice and instantly show product depth.</p>
                </Link>
                <Link
                  href={`${learnerRoutes.mentor}?prompt=${encodeURIComponent(
                    "Act as my AI mentor. Review my dashboard, identify the highest-leverage next step, and give me a short game plan for the next 30 minutes.",
                  )}`}
                  onClick={() => adaptiveUI.recordFeatureUse("mentor")}
                  className="story-card block transition duration-200 hover:-translate-y-1.5"
                >
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-400 to-rose-400 text-slate-950">
                    <MessageSquareMore className="h-5 w-5" />
                  </div>
                  <p className="mt-4 text-lg font-semibold text-slate-950">AI mentor chat</p>
                  <p className="mt-2 text-sm leading-6 text-slate-600">Open the flagship conversational flow with context-aware coaching.</p>
                </Link>
              </div>
            </SurfaceCard>

            {adaptiveUI.visibleSections.gamification ? (
            <SurfaceCard title="Gamification loop" description="A visible reward system that increases emotional engagement.">
              <div className="grid gap-3 md:grid-cols-2">
                <div className="story-card">
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Current level</p>
                  <p className="mt-3 text-3xl font-semibold text-slate-950">Level {Math.max(1, Math.floor(dashboard.kpis.xp / 250) + 1)}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-600">
                    {250 - (dashboard.kpis.xp % 250 || 250)} XP to the next level unlock.
                  </p>
                </div>
                <div className="story-card">
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Streak shield</p>
                  <p className="mt-3 text-3xl font-semibold text-slate-950">{dashboard.kpis.streakDays} days</p>
                  <p className="mt-2 text-sm leading-6 text-slate-600">Consistency is framed as status, not just habit tracking.</p>
                </div>
                <div className="story-card">
                  <div className="flex items-center gap-2 text-amber-600">
                    <BadgeCheck className="h-4 w-4" />
                    <p className="text-xs font-semibold uppercase tracking-[0.24em]">Badge spotlight</p>
                  </div>
                  <p className="mt-3 text-xl font-semibold text-slate-950">{activeBadges[0]?.name ?? "Next badge incoming"}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-600">
                    {activeBadges[0]?.description ?? "Keep your streak alive and close one more step to unlock another achievement."}
                  </p>
                </div>
                <div className="story-card">
                  <div className="flex items-center gap-2 text-rose-500">
                    <Star className="h-4 w-4" />
                    <p className="text-xs font-semibold uppercase tracking-[0.24em]">Leaderboard energy</p>
                  </div>
                  <p className="mt-3 text-xl font-semibold text-slate-950">{dashboard.leaderboard.length} ranked learners</p>
                  <p className="mt-2 text-sm leading-6 text-slate-600">Competition creates a clean “come back tomorrow” trigger.</p>
                </div>
              </div>
            </SurfaceCard>
            ) : null}
          </div>

          {!adaptiveUI.focusMode ? <ProgressStoryTimeline items={storyMoments} /> : null}

          {adaptiveUI.visibleSections.livePulse ? (
          <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
            <SurfaceCard title="Live platform pulse" description="Tenant-wide presence and streaming activity make the product feel continuously alive.">
              <div className="grid gap-3 md:grid-cols-2">
                <div className="story-card">
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Active users</p>
                  <p className="mt-3 text-3xl font-semibold text-slate-950">{activeUsers}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-600">Real-time connected learners and operators in this tenant.</p>
                </div>
                <div className="story-card">
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Live events</p>
                  <p className="mt-3 text-3xl font-semibold text-slate-950">{liveEvents.length}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-600">Recent streamed actions from roadmap and collaboration flows.</p>
                </div>
              </div>
            </SurfaceCard>
            <SurfaceCard title="Live activity feed" description="A real-time stream of learner and collaboration events.">
              <div className="space-y-3">
                {liveEvents.length === 0 ? (
                  <p className="text-sm text-slate-600">Waiting for live activity...</p>
                ) : (
                  liveEvents.slice(0, 6).map((event) => (
                    <div key={event.id} className="story-card">
                      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">{event.eventType.replaceAll("_", " ")}</p>
                      <p className="mt-2 text-sm leading-7 text-slate-700">{event.message}</p>
                    </div>
                  ))
                )}
              </div>
            </SurfaceCard>
          </div>
          ) : null}

          <SurfaceCard
            title="This week at a glance"
            description="A quick summary of where momentum is building and where you need to intervene next."
            className="mesh-panel"
          >
            <div className="grid gap-4 lg:grid-cols-3">
              <div className="rounded-[24px] border border-white/70 bg-white/80 p-5 dark:border-slate-700 dark:bg-slate-900/70">
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Next checkpoint</p>
                <p className="mt-3 text-2xl font-semibold tracking-tight text-slate-950 dark:text-slate-100">
                  {topWeakTopic?.name ?? "Stay in flow"}
                </p>
                <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400">
                  Highest-priority recovery topic based on mastery and recent learning signals.
                </p>
              </div>
              <div className="rounded-[24px] border border-white/70 bg-white/80 p-5 dark:border-slate-700 dark:bg-slate-900/70">
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Mentor signal</p>
                <p className="mt-3 text-2xl font-semibold tracking-tight text-slate-950 dark:text-slate-100">
                  {dashboard.kpis.weakTopicCount} topics
                </p>
                <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400">
                  Focus on weak-topic recovery before adding harder concepts.
                </p>
              </div>
              <div className="rounded-[24px] border border-white/70 bg-white/80 p-5 dark:border-slate-700 dark:bg-slate-900/70">
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Leaderboard pace</p>
                <p className="mt-3 text-2xl font-semibold tracking-tight text-slate-950 dark:text-slate-100">
                  {dashboard.kpis.leaderboardLead}
                </p>
                <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400">
                  Tenant-level competition keeps consistency visible and motivating.
                </p>
              </div>
            </div>
          </SurfaceCard>

          {dashboard.kpis.totalSteps === 0 ? (
            <EmptyState
              title="No roadmap yet"
              description="Start a diagnostic to generate your learning roadmap, then come back here for progress, mentor guidance, and topic recommendations."
            />
          ) : (
            <>
              {adaptiveUI.visibleSections.reviewFirst ? (
                <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
                  <SurfaceCard
                    title="Spaced review queue"
                    description={`Average retention ${dashboard.retention.average_retention_score}% based on current forgetting-risk estimates.`}
                  >
                    <div className="space-y-3">
                      {dashboard.retention.due_reviews.length === 0 ? (
                        <p className="text-sm text-slate-600 dark:text-slate-400">No reviews are due right now.</p>
                      ) : (
                        dashboard.retention.due_reviews.map((review, index) => (
                          <div
                            key={`${review.topic_id}-${review.topic_name}-${index}`}
                            className="rounded-[22px] border border-white/70 bg-white/80 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70"
                          >
                            <div className="flex items-center justify-between gap-4">
                              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{review.topic_name}</p>
                              <StatusPill label={`${review.retention_score}% retention`} tone="warning" />
                            </div>
                            <p className="mt-2 text-xs uppercase tracking-[0.2em] text-slate-400">
                              Review every {review.review_interval_days} days
                            </p>
                          </div>
                        ))
                      )}
                    </div>
                  </SurfaceCard>
                  <SurfaceCard
                    title="Recommended resources"
                    description="Targeted materials chosen for topics with the highest review pressure."
                  >
                    <div className="space-y-3">
                      {dashboard.retention.recommended_resources.map((resource, index) => (
                        <a
                          key={`${resource.id ?? resource.title ?? "resource"}-${index}`}
                          href={resource.url}
                          target="_blank"
                          rel="noreferrer"
                          onClick={() => adaptiveUI.recordFeatureUse("review")}
                          className="flex items-start gap-3 rounded-[22px] border border-white/70 bg-white/80 px-4 py-3 transition hover:border-brand-300 dark:border-slate-700 dark:bg-slate-900/70"
                        >
                          <div className="flex h-10 w-10 items-center justify-center rounded-[18px] bg-brand-50 text-brand-700 dark:bg-slate-800 dark:text-brand-200">
                            <Library className="h-4 w-4" />
                          </div>
                          <div>
                            <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{resource.title}</p>
                            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                              {resource.topic_name} • {resource.resource_type} • {resource.difficulty}
                            </p>
                          </div>
                        </a>
                      ))}
                    </div>
                  </SurfaceCard>
                </div>
              ) : null}

              <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
                <ProgressLineChart
                  title="Learning velocity"
                  description="Daily study minutes and momentum across the last week."
                  data={dashboard.charts.velocityLine}
                />
                <MasteryPieChart
                  title="Topic mastery"
                  description="Current roadmap status across completed, active, and pending work."
                  data={dashboard.charts.masteryPie}
                />
              </div>

              <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
                <SurfaceCard
                  title="Weak topic heatmap"
                  description="Mastery, confidence, and improvement delta at the topic level."
                >
                  <div className="grid gap-3 sm:grid-cols-2">
                    {dashboard.heatmap.map((topic) => (
                      <div
                        key={topic.topic_id}
                        className="rounded-[24px] border border-white/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.88),rgba(248,250,255,0.74))] px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70"
                      >
                        <div className="flex items-center justify-between gap-4">
                          <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{topic.topic_name}</p>
                          <StatusPill
                            label={`${topic.score.toFixed(0)}%`}
                            tone={topic.score < 60 ? "danger" : topic.score < 75 ? "warning" : "success"}
                          />
                        </div>
                        <p className="mt-2 text-xs uppercase tracking-[0.2em] text-slate-400">
                          Delta {topic.mastery_delta.toFixed(1)} • Confidence {topic.confidence.toFixed(2)}
                        </p>
                      </div>
                    ))}
                  </div>
                </SurfaceCard>
                <div className="space-y-6">
                  <DistributionBarChart
                    title="Weak topic pressure"
                    description="How much each focus topic is dragging below mastery."
                    data={dashboard.weakTopics.map((topic) => ({
                      label: topic.name,
                      value: Math.max(0, Math.round(topic.gap)),
                    }))}
                  />
                  <SurfaceCard title="Skill graph unlocks" description="Progressive topic availability based on dependencies.">
                  <div className="space-y-3">
                    {dashboard.skillGraph.map((node) => (
                      <div
                        key={node.topic_id}
                        className="flex items-start justify-between gap-4 rounded-[22px] border border-white/70 bg-white/80 px-4 py-3 transition duration-200 hover:-translate-y-1 dark:border-slate-700 dark:bg-slate-900/70"
                      >
                        <div>
                          <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{node.topic_name}</p>
                            <p className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-400">
                              Depends on {node.dependencies.length || 0} topics
                            </p>
                          </div>
                          <StatusPill
                            label={node.status}
                            tone={node.status === "mastered" ? "success" : node.status === "available" ? "default" : "warning"}
                          />
                        </div>
                      ))}
                    </div>
                  </SurfaceCard>
                </div>
              </div>

              <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
                <ActivityFeed
                  title="Recent activity"
                  description="Recent learning signals flowing into the intelligence layer."
                  items={dashboard.recentActivity}
                />
                <RecommendationPanel
                  title="Contextual guidance"
                  description="Each recommendation includes the reason it surfaced now, so the next move feels obvious during the demo."
                  items={[
                    {
                      title: adaptiveUI.nextBestAction.title,
                      message: adaptiveUI.nextBestAction.description,
                      why: "This is the current highest-leverage action based on weak topics, retention timing, and active roadmap state.",
                      confidenceLabel: "Best next action",
                      tone: "success" as const,
                      href: "/student/roadmap",
                      ctaLabel: "Open roadmap",
                    },
                    ...dashboard.recommendations,
                  ].slice(0, 4)}
                />
              </div>

              {!adaptiveUI.visibleSections.reviewFirst ? (
              <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
                <SurfaceCard
                  title="Spaced review queue"
                  description={`Average retention ${dashboard.retention.average_retention_score}% based on current forgetting-risk estimates.`}
                >
                  <div className="space-y-3">
                    {dashboard.retention.due_reviews.length === 0 ? (
                      <p className="text-sm text-slate-600 dark:text-slate-400">No reviews are due right now.</p>
                    ) : (
                      dashboard.retention.due_reviews.map((review, index) => (
                        <div
                          key={`${review.topic_id}-${review.topic_name}-${index}`}
                          className="rounded-[22px] border border-white/70 bg-white/80 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70"
                        >
                          <div className="flex items-center justify-between gap-4">
                            <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{review.topic_name}</p>
                            <StatusPill label={`${review.retention_score}% retention`} tone="warning" />
                          </div>
                          <p className="mt-2 text-xs uppercase tracking-[0.2em] text-slate-400">
                            Review every {review.review_interval_days} days
                          </p>
                        </div>
                      ))
                    )}
                  </div>
                </SurfaceCard>
                <SurfaceCard
                  title="Recommended resources"
                  description="Targeted materials chosen for topics with the highest review pressure."
                >
                  <div className="space-y-3">
                    {dashboard.retention.recommended_resources.map((resource, index) => (
                      <a
                        key={`${resource.id ?? resource.title ?? "resource"}-${index}`}
                        href={resource.url}
                        target="_blank"
                        rel="noreferrer"
                        onClick={() => adaptiveUI.recordFeatureUse("review")}
                        className="flex items-start gap-3 rounded-[22px] border border-white/70 bg-white/80 px-4 py-3 transition hover:border-brand-300 dark:border-slate-700 dark:bg-slate-900/70"
                      >
                        <div className="flex h-10 w-10 items-center justify-center rounded-[18px] bg-brand-50 text-brand-700 dark:bg-slate-800 dark:text-brand-200">
                          <Library className="h-4 w-4" />
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{resource.title}</p>
                          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                            {resource.topic_name} • {resource.resource_type} • {resource.difficulty}
                          </p>
                        </div>
                      </a>
                    ))}
                  </div>
                </SurfaceCard>
              </div>
              ) : null}

              <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
                {adaptiveUI.visibleSections.leaderboard ? (
                <SurfaceCard title="Leaderboard" description="Tenant-scoped XP standings.">
                  <div className="space-y-3">
                    {dashboard.leaderboard.map((entry) => (
                      <div
                        key={entry.user_id}
                        className="flex items-center justify-between gap-4 rounded-[22px] border border-white/70 bg-white/80 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70"
                      >
                        <div>
                          <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                            #{entry.rank} {entry.name}
                          </p>
                          <p className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-400">
                            {entry.is_current_user ? "You" : "Peer"}
                          </p>
                        </div>
                        <p className="text-sm font-semibold text-brand-700 dark:text-brand-200">{entry.xp} XP</p>
                      </div>
                    ))}
                  </div>
                </SurfaceCard>
                ) : null}
                {adaptiveUI.visibleSections.badges ? (
                <SurfaceCard title="Badges earned" description="Milestones and recognition from your learning journey.">
                  <div className="grid gap-3 sm:grid-cols-2">
                    {dashboard.badges.map((badge, index) => (
                      <div
                        key={`${badge.name}-${badge.awarded_at ?? "badge"}-${index}`}
                        className="rounded-[22px] border border-amber-200/70 bg-[linear-gradient(135deg,rgba(255,251,235,0.95),rgba(254,243,199,0.68))] px-4 py-3 transition duration-200 hover:-translate-y-1 dark:border-amber-300/20 dark:bg-amber-300/10"
                      >
                        <div className="flex items-center gap-2 text-amber-700 dark:text-amber-200">
                          <Sparkles className="h-4 w-4" />
                          <p className="text-sm font-semibold">{badge.name}</p>
                        </div>
                        <p className="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-200">{badge.description}</p>
                      </div>
                    ))}
                  </div>
                </SurfaceCard>
                ) : null}
              </div>
            </>
          )}
        </>
      ) : null}
    </div>
  );
}
