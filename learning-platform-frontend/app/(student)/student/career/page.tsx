"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { Briefcase, FileText, ShieldCheck, Sparkles } from "lucide-react";
import { useMemo } from "react";

import PageHeader from "@/components/layouts/PageHeader";
import MetricCard from "@/components/ui/MetricCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { getCareerOverview, getInterviewPrep } from "@/services/careerService";

export default function StudentCareerPage() {
  const overviewQuery = useQuery({ queryKey: ["career", "overview"], queryFn: getCareerOverview });
  const overview = overviewQuery.data;
  const topRole = overview?.readiness.top_role_matches[0];

  const interviewMutation = useMutation({
    mutationFn: () =>
      getInterviewPrep({
        role_name: topRole?.role_name ?? "Software Engineer",
        difficulty: "intermediate",
        count: 5,
      }),
  });

  const phaseEntries = useMemo(
    () => Object.entries(overview?.career_path.career_roadmap ?? {}),
    [overview?.career_path.career_roadmap],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Career engine"
        title="Connect learning to real-world hiring outcomes"
        description="This workspace translates roadmap progress, skill mastery, and practice evidence into job readiness, career paths, resume output, and interview preparation."
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Job readiness" value={`${overview?.readiness.readiness_percent ?? 0}%`} tone="info" icon={<ShieldCheck className="h-5 w-5" />} />
        <MetricCard title="Top role" value={topRole?.role_name ?? "No role mapped"} tone="success" icon={<Briefcase className="h-5 w-5" />} />
        <MetricCard title="Confidence" value={overview?.readiness.confidence_label ?? "early"} tone="warning" icon={<Sparkles className="h-5 w-5" />} />
        <MetricCard title="Resume skills" value={overview?.resume_preview.skills.length ?? 0} icon={<FileText className="h-5 w-5" />} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <SurfaceCard title="Role match intelligence" description="Roles suggested from mapped skills and demonstrated learning strength.">
          <div className="space-y-3">
            {(overview?.readiness.top_role_matches ?? []).map((role) => (
              <div key={role.role_id} className="story-card">
                <div className="flex items-center justify-between gap-4">
                  <p className="text-lg font-semibold text-slate-950">{role.role_name}</p>
                  <p className="text-sm font-semibold text-brand-700">{role.readiness_percent}% ready</p>
                </div>
                <p className="mt-2 text-sm text-slate-600">Matched: {role.matched_skills.join(", ") || "No mapped skills yet"}</p>
                <p className="mt-2 text-sm text-slate-600">Missing: {role.missing_skills.join(", ") || "Core profile covered"}</p>
              </div>
            ))}
          </div>
        </SurfaceCard>

        <SurfaceCard title="Resume builder" description="Auto-generated resume summary from actual learning progress.">
          <div className="story-card">
            <p className="text-xl font-semibold text-slate-950">{overview?.resume_preview.headline ?? "Resume preview"}</p>
            <p className="mt-3 text-sm leading-7 text-slate-600">{overview?.resume_preview.summary}</p>
            <p className="mt-4 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Skills</p>
            <p className="mt-2 text-sm text-slate-700">{overview?.resume_preview.skills.join(", ") || "No mastered skills yet"}</p>
            <p className="mt-4 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Projects</p>
            <p className="mt-2 text-sm text-slate-700">{overview?.resume_preview.projects.join(" • ") || "No projects yet"}</p>
          </div>
        </SurfaceCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <SurfaceCard title="Career path suggestions" description="A phased roadmap from current progress to employable specialization.">
          <div className="space-y-3">
            {phaseEntries.map(([phaseKey, phase]) => (
              <div key={phaseKey} className="story-card">
                <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">{phaseKey.replaceAll("_", " ")}</p>
                <p className="mt-2 text-sm text-slate-700">{phase.duration_months} months</p>
                <p className="mt-2 text-sm leading-7 text-slate-600">{phase.focus_areas.join(", ")}</p>
              </div>
            ))}
          </div>
        </SurfaceCard>

        <SurfaceCard
          title="Interview preparation"
          description="Generate interview questions and a mock interview prompt tailored to the most likely role."
          actions={
            <button
              type="button"
              onClick={() => interviewMutation.mutate()}
              className="rounded-2xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white"
            >
              Generate mock interview
            </button>
          }
        >
          {interviewMutation.data ? (
            <div className="space-y-3">
              <div className="story-card">
                <p className="text-sm font-semibold text-slate-950">{interviewMutation.data.role_name}</p>
                <p className="mt-2 text-sm leading-7 text-slate-600">{interviewMutation.data.mock_interview_prompt}</p>
              </div>
              {interviewMutation.data.questions.map((question, index) => (
                <div key={`${question.question_text}-${index}`} className="story-card">
                  <p className="text-sm font-semibold text-slate-950">{question.question_text}</p>
                  <p className="mt-2 text-sm text-slate-600">{question.explanation}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-600">Generate interview preparation to see role-specific mock questions.</p>
          )}
        </SurfaceCard>
      </div>
    </div>
  );
}
