"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { BrainCircuit, CalendarClock, MessagesSquare, Users, Zap } from "lucide-react";

import PageHeader from "@/components/layouts/PageHeader";
import Button from "@/components/ui/Button";
import MetricCard from "@/components/ui/MetricCard";
import Select from "@/components/ui/Select";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { useMentorWorkspace } from "@/hooks/useDashboard";
import { buildHybridSessionPlan, getHybridMentorNetwork } from "@/services/mentorService";

export default function MentorNetworkPage() {
  const [selectedLearnerId, setSelectedLearnerId] = useState<number | null>(null);
  const workspace = useMentorWorkspace(selectedLearnerId);

  useEffect(() => {
    if (!selectedLearnerId && workspace.learners.length > 0) {
      setSelectedLearnerId(workspace.learners[0].user_id);
    }
  }, [selectedLearnerId, workspace.learners]);

  const networkQuery = useQuery({
    queryKey: ["mentor", "hybrid-network", workspace.activeLearnerId],
    queryFn: () => getHybridMentorNetwork(workspace.activeLearnerId ?? undefined),
    enabled: Boolean(workspace.activeLearnerId),
  });

  const sessionPlanMutation = useMutation({
    mutationFn: (payload: { mentor_id?: number | null }) =>
      buildHybridSessionPlan({
        learner_id: workspace.activeLearnerId,
        mentor_id: payload.mentor_id,
      }),
  });

  const network = networkQuery.data;
  const learnerProfile = network?.learner_profile;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Hybrid mentorship"
        title="AI + human teaching network"
        description="The platform now pairs AI guidance with human expertise: AI watches signals, briefs the mentor, and keeps follow-through active between live sessions."
        actions={
          <div className="flex flex-wrap gap-3">
            {workspace.learners.length > 0 ? (
              <div className="min-w-[240px]">
                <Select
                  aria-label="Select learner"
                  value={workspace.activeLearnerId ?? ""}
                  onChange={(event) => setSelectedLearnerId(Number(event.target.value))}
                >
                  {workspace.learners.map((learner) => (
                    <option key={learner.user_id} value={learner.user_id}>
                      {learner.display_name} ({learner.email})
                    </option>
                  ))}
                </Select>
              </div>
            ) : null}
            <Link
              href={workspace.activeLearnerId ? `/mentor/chat?learner_id=${workspace.activeLearnerId}` : "/mentor/chat"}
              className="inline-flex items-center gap-2 rounded-2xl bg-gradient-to-r from-brand-700 via-brand-600 to-brand-500 px-4 py-3 text-sm font-semibold text-white shadow-glow"
            >
              Open AI mentor
              <MessagesSquare className="h-4 w-4" />
            </Link>
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard title="Readiness state" value={learnerProfile?.session_intensity ?? "loading"} tone="warning" icon={<Zap className="h-5 w-5" />} />
        <MetricCard title="Matched mentors" value={network?.mentor_matches.length ?? 0} tone="success" icon={<Users className="h-5 w-5" />} />
        <MetricCard title="Weak topics" value={learnerProfile?.weak_topics.length ?? 0} tone="warning" icon={<BrainCircuit className="h-5 w-5" />} />
        <MetricCard title="Live channels" value={network?.live_support_channels.length ?? 0} tone="info" icon={<CalendarClock className="h-5 w-5" />} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <SurfaceCard
          title="Learner twin for mentors"
          description="This brief is what the AI layer would hand to a human mentor before the session starts."
        >
          {networkQuery.isLoading ? <p className="text-sm text-slate-600">Loading hybrid mentorship intelligence...</p> : null}
          {networkQuery.isError ? <p className="text-sm text-rose-600">Unable to load the mentor network.</p> : null}
          {learnerProfile ? (
            <div className="space-y-4">
              <div className="rounded-[28px] border border-slate-200 bg-white/70 p-5 dark:border-slate-700 dark:bg-slate-900/70">
                <p className="text-sm leading-7 text-slate-700 dark:text-slate-300">{learnerProfile.summary}</p>
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <div className="rounded-2xl bg-slate-100/80 p-4 dark:bg-slate-800/80">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Weak topics</p>
                    <div className="mt-2 space-y-1 text-sm text-slate-700 dark:text-slate-300">
                      {(learnerProfile.weak_topics.length ? learnerProfile.weak_topics : ["No urgent weak-topic signal"]).map((topic) => (
                        <p key={topic}>- {topic}</p>
                      ))}
                    </div>
                  </div>
                  <div className="rounded-2xl bg-emerald-50/80 p-4 dark:bg-emerald-950/30">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700">Strong topics</p>
                    <div className="mt-2 space-y-1 text-sm text-emerald-900 dark:text-emerald-100">
                      {(learnerProfile.strong_topics.length ? learnerProfile.strong_topics : ["Strengths still emerging"]).map((topic) => (
                        <p key={topic}>- {topic}</p>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              <div className="rounded-[28px] border border-indigo-200 bg-indigo-50/70 p-5">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-700">AI + human collaboration</p>
                <p className="mt-3 text-sm font-semibold text-indigo-950">{network?.collaboration_brief.session_goal}</p>
                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-700">AI role</p>
                    <p className="mt-2 text-sm leading-7 text-indigo-950/80">{network?.collaboration_brief.ai_role}</p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-700">Human role</p>
                    <p className="mt-2 text-sm leading-7 text-indigo-950/80">{network?.collaboration_brief.human_role}</p>
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </SurfaceCard>

        <SurfaceCard title="Live support channels" description="The hybrid system keeps the learner moving between AI help, human mentoring, and community reinforcement.">
          <div className="space-y-4">
            {(network?.live_support_channels ?? []).map((channel) => (
              <div key={channel.channel_type} className="rounded-[24px] border border-slate-200 bg-white/70 p-4 dark:border-slate-700 dark:bg-slate-900/70">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{channel.title}</p>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                    {channel.realtime_enabled ? "Live" : "Async"}
                  </span>
                </div>
                <p className="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-400">{channel.description}</p>
                <p className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-500">{channel.why}</p>
                <Link href={channel.href} className="mt-4 inline-flex text-sm font-semibold text-brand-700 hover:text-brand-600">
                  Open channel
                </Link>
              </div>
            ))}
          </div>
        </SurfaceCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <SurfaceCard title="Best human mentor matches" description="Deterministic matching combines learner risk, learning style, and the mentor role to route the right kind of support.">
          <div className="space-y-4">
            {(network?.mentor_matches ?? []).map((match) => (
              <div key={match.mentor_id} className="rounded-[28px] border border-slate-200 bg-white/75 p-5 dark:border-slate-700 dark:bg-slate-900/75">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="text-base font-semibold text-slate-950 dark:text-slate-100">{match.display_name}</p>
                    <p className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-500">
                      {match.role} • {match.availability}
                    </p>
                  </div>
                  <div className="rounded-full bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-700">
                    {match.match_score}% match
                  </div>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {match.specialties.map((specialty) => (
                    <span key={specialty} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                      {specialty}
                    </span>
                  ))}
                </div>
                <div className="mt-4 space-y-1 text-sm leading-7 text-slate-600 dark:text-slate-400">
                  {match.reasons.map((reason) => (
                    <p key={reason}>- {reason}</p>
                  ))}
                </div>
                <div className="mt-4 rounded-2xl bg-slate-100/80 p-4 text-sm leading-7 text-slate-700 dark:bg-slate-800/80 dark:text-slate-300">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">AI handoff</p>
                  <p className="mt-2">{match.ai_handoff_summary}</p>
                </div>
                <div className="mt-4">
                  <Button
                    onClick={() => sessionPlanMutation.mutate({ mentor_id: match.mentor_id })}
                    disabled={sessionPlanMutation.isPending}
                  >
                    Generate live session plan
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </SurfaceCard>

        <SurfaceCard title="Session plan" description="AI prepares the context, then the human mentor takes over the judgment-heavy coaching work.">
          {sessionPlanMutation.data ? (
            <div className="space-y-5">
              <div className="rounded-[28px] border border-amber-200 bg-amber-50/80 p-5">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-700">Live session</p>
                <p className="mt-2 text-lg font-semibold text-amber-950">{sessionPlanMutation.data.session_title}</p>
                <p className="mt-2 text-sm text-amber-900/80">Lead mentor: {sessionPlanMutation.data.mentor_name}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Agenda</p>
                <div className="mt-3 space-y-2 text-sm leading-7 text-slate-700 dark:text-slate-300">
                  {sessionPlanMutation.data.agenda.map((item) => (
                    <p key={item}>- {item}</p>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">AI prep notes</p>
                <div className="mt-3 space-y-2 text-sm leading-7 text-slate-700 dark:text-slate-300">
                  {sessionPlanMutation.data.ai_prep_notes.map((item) => (
                    <p key={item}>- {item}</p>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Follow-up actions</p>
                <div className="mt-3 space-y-2 text-sm leading-7 text-slate-700 dark:text-slate-300">
                  {sessionPlanMutation.data.follow_up_actions.map((item) => (
                    <p key={item}>- {item}</p>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-[28px] border border-dashed border-slate-300 bg-slate-50/70 p-6 text-sm leading-7 text-slate-600 dark:border-slate-700 dark:bg-slate-900/60 dark:text-slate-400">
              Choose a mentor match to generate a live session plan with AI prep notes and post-session follow-up.
            </div>
          )}
        </SurfaceCard>
      </div>
    </div>
  );
}
