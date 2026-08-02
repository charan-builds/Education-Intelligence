"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { Camera, CheckCircle2, ChevronLeft, ChevronRight, GraduationCap, Link as LinkIcon, NotebookPen, Save, Sparkles } from "lucide-react";

import PageHeader from "@/components/layouts/PageHeader";
import { useToast } from "@/components/providers/ToastProvider";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { useAuth } from "@/hooks/useAuth";
import { getProfile, getProfileProgress, getProfileStatus, saveProfile, trackOnboardingEvent, uploadProfilePhoto } from "@/services/profileService";
import type { DailyStudyTime, ExperienceLevel, LearningStyle, TargetTimeline, UserProfilePayload } from "@/types/profile";
import { appRoutes } from "@/utils/appRoutes";

type WizardMode = "onboarding" | "profile";

type FormState = {
  full_name: string;
  profile_photo_url: string;
  bio: string;
  college_name: string;
  degree: string;
  year_of_study: string;
  github_url: string;
  leetcode_url: string;
  hackerrank_url: string;
  linkedin_url: string;
  experience_level: ExperienceLevel | "";
  daily_study_time: DailyStudyTime | "";
  learning_style: LearningStyle | "";
  learning_goal_note: string;
  target_timeline: TargetTimeline | "";
};

const STEPS = [
  { id: 0, label: "Basic Info", icon: Sparkles },
  { id: 1, label: "Academic Info", icon: GraduationCap },
  { id: 2, label: "Social Profiles", icon: LinkIcon },
  { id: 3, label: "Learning Preferences", icon: NotebookPen },
  { id: 4, label: "Confirmation", icon: CheckCircle2 },
] as const;

const EXPERIENCE_OPTIONS: Array<{ value: ExperienceLevel; label: string }> = [
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
];

const STUDY_TIME_OPTIONS: Array<{ value: DailyStudyTime; label: string }> = [
  { value: "less_than_30_min", label: "< 30 min" },
  { value: "30_to_60_min", label: "30 to 60 min" },
  { value: "1_to_2_hours", label: "1 to 2 hours" },
  { value: "2_to_4_hours", label: "2 to 4 hours" },
  { value: "4_plus_hours", label: "4+ hours" },
];

const LEARNING_STYLE_OPTIONS: Array<{ value: LearningStyle; label: string }> = [
  { value: "visual", label: "Visual" },
  { value: "reading", label: "Reading" },
  { value: "hands_on", label: "Hands-on" },
  { value: "video", label: "Video-first" },
  { value: "mixed", label: "Mixed" },
];

const TARGET_TIMELINE_OPTIONS: Array<{ value: TargetTimeline; label: string }> = [
  { value: "1_month", label: "1 month" },
  { value: "3_months", label: "3 months" },
  { value: "6_months", label: "6 months" },
  { value: "12_months", label: "12 months" },
  { value: "flexible", label: "Flexible" },
];

const EMPTY_STATE: FormState = {
  full_name: "",
  profile_photo_url: "",
  bio: "",
  college_name: "",
  degree: "",
  year_of_study: "",
  github_url: "",
  leetcode_url: "",
  hackerrank_url: "",
  linkedin_url: "",
  experience_level: "",
  daily_study_time: "",
  learning_style: "",
  learning_goal_note: "",
  target_timeline: "",
};

const ONBOARDING_DRAFT_STORAGE_KEY = "independent_learner_onboarding_draft";

function normalizeFormState(profile: Partial<FormState> & Record<string, unknown>): FormState {
  return {
    full_name: String(profile.full_name ?? ""),
    profile_photo_url: String(profile.profile_photo_url ?? ""),
    bio: String(profile.bio ?? ""),
    college_name: String(profile.college_name ?? ""),
    degree: String(profile.degree ?? ""),
    year_of_study: profile.year_of_study != null ? String(profile.year_of_study) : "",
    github_url: String(profile.github_url ?? ""),
    leetcode_url: String(profile.leetcode_url ?? ""),
    hackerrank_url: String(profile.hackerrank_url ?? ""),
    linkedin_url: String(profile.linkedin_url ?? ""),
    experience_level: (profile.experience_level as ExperienceLevel | "") ?? "",
    daily_study_time: (profile.daily_study_time as DailyStudyTime | "") ?? "",
    learning_style: (profile.learning_style as LearningStyle | "") ?? "",
    learning_goal_note: String(profile.learning_goal_note ?? ""),
    target_timeline: (profile.target_timeline as TargetTimeline | "") ?? "",
  };
}

function buildPayload(form: FormState, profileCompleted?: boolean): UserProfilePayload {
  return {
    full_name: form.full_name || null,
    profile_photo_url: form.profile_photo_url || null,
    bio: form.bio || null,
    college_name: form.college_name || null,
    degree: form.degree || null,
    year_of_study: form.year_of_study ? Number(form.year_of_study) : null,
    github_url: form.github_url || null,
    leetcode_url: form.leetcode_url || null,
    hackerrank_url: form.hackerrank_url || null,
    linkedin_url: form.linkedin_url || null,
    experience_level: form.experience_level || null,
    daily_study_time: form.daily_study_time || null,
    learning_style: form.learning_style || null,
    learning_goal_note: form.learning_goal_note || null,
    target_timeline: form.target_timeline || null,
    profile_completed: profileCompleted,
  };
}

function getStepValidation(step: number, form: FormState): string[] {
  if (step === 0) {
    return !form.full_name.trim() ? ["Full name is required."] : [];
  }
  if (step === 1) {
    const errors: string[] = [];
    if (!form.college_name.trim()) {
      errors.push("College name is required.");
    }
    if (!form.degree.trim()) {
      errors.push("Degree is required.");
    }
    if (!form.year_of_study.trim()) {
      errors.push("Year of study is required.");
    }
    return errors;
  }
  if (step === 3) {
    const errors: string[] = [];
    if (!form.experience_level) {
      errors.push("Experience level is required.");
    }
    if (!form.daily_study_time) {
      errors.push("Daily study time is required.");
    }
    if (!form.learning_style) {
      errors.push("Learning style is required.");
    }
    if (!form.learning_goal_note.trim()) {
      errors.push("Learning goal note is required.");
    }
    if (!form.target_timeline) {
      errors.push("Target timeline is required.");
    }
    return errors;
  }
  return [];
}

function StepPill({
  active,
  complete,
  label,
  icon: Icon,
}: {
  active: boolean;
  complete: boolean;
  label: string;
  icon: typeof Sparkles;
}) {
  return (
    <div
      className={[
        "flex items-center gap-3 rounded-2xl border px-4 py-3 text-sm font-semibold transition",
        active
          ? "border-violet-500 bg-violet-600 text-white"
          : complete
            ? "border-violet-200 bg-violet-50 text-violet-700"
            : "border-slate-200 bg-white text-slate-600",
      ].join(" ")}
    >
      <Icon className="h-4 w-4" />
      <span>{label}</span>
    </div>
  );
}

export default function OnboardingWizard({ mode }: { mode: WizardMode }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { refresh } = useAuth();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<FormState>(EMPTY_STATE);
  const [isHydrated, setIsHydrated] = useState(false);
  const formFieldsRef = useRef<HTMLDivElement | null>(null);
  const trackedStepRef = useRef<number | null>(null);
  const completionTriggeredRef = useRef(false);
  const hasLocalEditsRef = useRef(false);

  const profileQuery = useQuery({
    queryKey: ["independent-learner", "profile"],
    queryFn: getProfile,
  });
  const statusQuery = useQuery({
    queryKey: ["independent-learner", "profile", "status"],
    queryFn: getProfileStatus,
  });
  const progressQuery = useQuery({
    queryKey: ["independent-learner", "profile", "progress"],
    queryFn: getProfileProgress,
  });

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    const draft = window.sessionStorage.getItem(ONBOARDING_DRAFT_STORAGE_KEY);
    if (!draft) {
      return;
    }
    try {
      const parsed = JSON.parse(draft) as Partial<FormState>;
      hasLocalEditsRef.current = true;
      setForm((current) => ({ ...current, ...normalizeFormState(parsed as Record<string, unknown>) }));
    } catch {
      window.sessionStorage.removeItem(ONBOARDING_DRAFT_STORAGE_KEY);
    }
  }, []);

  useEffect(() => {
    if (!profileQuery.data) {
      return;
    }
    if (hasLocalEditsRef.current) {
      return;
    }
    setForm(normalizeFormState(profileQuery.data as Record<string, unknown>));
  }, [profileQuery.data]);

  useEffect(() => {
    if (!isHydrated || typeof window === "undefined") {
      return;
    }
    window.sessionStorage.setItem(ONBOARDING_DRAFT_STORAGE_KEY, JSON.stringify(form));
  }, [form, isHydrated]);

  useEffect(() => {
    const currentStep = STEPS[step];
    if (!currentStep || trackedStepRef.current === step) {
      return;
    }
    trackedStepRef.current = step;
    void trackOnboardingEvent({
      step_name: currentStep.label,
      event_type: "step_start",
      metadata: { mode, step_index: step + 1 },
    });
  }, [mode, step]);

  useEffect(() => {
    return () => {
      if (completionTriggeredRef.current) {
        return;
      }
      const currentStep = STEPS[trackedStepRef.current ?? step];
      if (!currentStep) {
        return;
      }
      void trackOnboardingEvent({
        step_name: currentStep.label,
        event_type: "drop_off",
        metadata: { mode, step_index: (trackedStepRef.current ?? step) + 1 },
      }).catch(() => undefined);
    };
  }, [mode, step]);

  const saveMutation = useMutation({
    mutationFn: (payload: UserProfilePayload) => saveProfile(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["independent-learner", "profile"] });
      await queryClient.invalidateQueries({ queryKey: ["independent-learner", "profile", "status"] });
      await queryClient.invalidateQueries({ queryKey: ["independent-learner", "profile", "progress"] });
      await refresh();
      toast({
        title: "Progress saved",
        description: "Your onboarding draft is safely stored.",
        variant: "success",
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Unable to save progress",
        description: error.message,
        variant: "error",
      });
    },
  });

  const completeMutation = useMutation({
    mutationFn: (payload: UserProfilePayload) => saveProfile(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["independent-learner", "profile"] });
      await queryClient.invalidateQueries({ queryKey: ["independent-learner", "profile", "status"] });
      await queryClient.invalidateQueries({ queryKey: ["independent-learner", "profile", "progress"] });
      await refresh();
      toast({
        title: "Onboarding complete",
        description: "Your learner profile is ready. Next up: choose the goal that should shape your diagnostic and roadmap.",
        variant: "success",
      });
      router.replace(appRoutes.independentLearner.goals);
    },
    onError: (error: Error) => {
      toast({
        title: "Unable to complete onboarding",
        description: error.message,
        variant: "error",
      });
    },
  });

  const photoMutation = useMutation({
    mutationFn: uploadProfilePhoto,
    onSuccess: (url) => {
      setForm((current) => ({ ...current, profile_photo_url: url }));
      toast({
        title: "Photo uploaded",
        description: "Your profile photo has been attached to this onboarding draft.",
        variant: "success",
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Photo upload failed",
        description: error.message,
        variant: "error",
      });
    },
  });

  const currentErrors = useMemo(() => getStepValidation(step, form), [form, step]);
  const stepCompletionPercent = Math.round(((step + 1) / STEPS.length) * 100);
  const completionPercent = Math.max(progressQuery.data?.completion_percent ?? 0, stepCompletionPercent);
  const missingFields = progressQuery.data?.missing_fields ?? statusQuery.data?.missing_required_fields ?? [];
  const isBootstrapping =
    !isHydrated
    || profileQuery.isLoading
    || statusQuery.isLoading
    || progressQuery.isLoading
    || (!profileQuery.data && !profileQuery.error);

  function updateField<Key extends keyof FormState>(key: Key, value: FormState[Key]) {
    hasLocalEditsRef.current = true;
    setForm((current) => {
      const nextForm = { ...current, [key]: value };
      if (typeof window !== "undefined") {
        window.sessionStorage.setItem(ONBOARDING_DRAFT_STORAGE_KEY, JSON.stringify(nextForm));
      }
      return nextForm;
    });
  }

  function syncFormFromDom(): FormState {
    const root = formFieldsRef.current;
    if (!root) {
      return form;
    }
    const nextForm = { ...form };
    const mutableForm = nextForm as Record<string, string>;
    const fields = root.querySelectorAll<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>("[name]");
    fields.forEach((field) => {
      const key = field.name as keyof FormState;
      if (!(key in nextForm)) {
        return;
      }
      mutableForm[key] = field.value;
    });
    if (JSON.stringify(nextForm) !== JSON.stringify(form)) {
      hasLocalEditsRef.current = true;
      if (typeof window !== "undefined") {
        window.sessionStorage.setItem(ONBOARDING_DRAFT_STORAGE_KEY, JSON.stringify(nextForm));
      }
      setForm(nextForm);
    }
    return nextForm;
  }

  async function saveDraft(nextForm: FormState = syncFormFromDom()) {
    await saveMutation.mutateAsync(buildPayload(nextForm));
  }

  async function nextStep() {
    const nextForm = syncFormFromDom();
    const nextErrors = getStepValidation(step, nextForm);
    if (nextErrors.length > 0) {
      toast({
        title: "Complete required fields",
        description: nextErrors.join(" "),
        variant: "error",
      });
      return;
    }
    await saveDraft(nextForm);
    await trackOnboardingEvent({
      step_name: STEPS[step].label,
      event_type: "step_completion",
      metadata: {
        mode,
        step_index: step + 1,
        completion_percent: completionPercent,
      },
    });
    setStep((current) => Math.min(current + 1, STEPS.length - 1));
  }

  async function submitCompletion() {
    const nextForm = syncFormFromDom();
    const finalErrors = [...getStepValidation(0, nextForm), ...getStepValidation(1, nextForm), ...getStepValidation(3, nextForm)];
    if (finalErrors.length > 0) {
      toast({
        title: "Profile is incomplete",
        description: finalErrors.join(" "),
        variant: "error",
      });
      return;
    }
    await trackOnboardingEvent({
      step_name: STEPS[step].label,
      event_type: "step_completion",
      metadata: {
        mode,
        step_index: step + 1,
        completion_percent: 100,
        final_submission: true,
      },
    });
    completionTriggeredRef.current = true;
    await completeMutation.mutateAsync(buildPayload(nextForm, true));
    if (typeof window !== "undefined") {
      window.sessionStorage.removeItem(ONBOARDING_DRAFT_STORAGE_KEY);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={mode === "onboarding" ? "Independent Learner Onboarding" : "Independent Learner Profile"}
        title={mode === "onboarding" ? "Build your learner profile" : "Refine your learner profile"}
        description={
          mode === "onboarding"
            ? "This guided setup captures the academic and learning context the platform needs before diagnostics, roadmaps, and recommendations become useful."
            : "Update the profile data that powers roadmap pacing, recommendation quality, and your personalized learner workspace."
        }
      />

      <div className="grid gap-4 xl:grid-cols-[0.88fr_1.12fr]">
        <SurfaceCard
          title="Progress"
          description="Five clear steps keep onboarding structured without trapping draft changes."
          className="border-violet-200 bg-violet-50/70 dark:border-violet-700 dark:bg-violet-900/20"
        >
          <div className="mb-5">
            <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-[0.18em] text-violet-600">
              <span>Dynamic completion</span>
              <span>{completionPercent}%</span>
            </div>
            <div className="mt-3 h-3 overflow-hidden rounded-full bg-violet-100 dark:bg-violet-900/50">
              <div
                className="h-full rounded-full bg-gradient-to-r from-violet-500 via-fuchsia-500 to-purple-500 transition-[width] duration-500"
                style={{ width: `${completionPercent}%` }}
              />
            </div>
          </div>
          <div className="space-y-3">
            {STEPS.map((item, index) => (
              <StepPill key={item.label} active={step === index} complete={step > index} label={item.label} icon={item.icon} />
            ))}
          </div>
          <div className="mt-6 rounded-[24px] border border-violet-200 bg-white/85 p-5 dark:border-violet-700 dark:bg-slate-950/60">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-violet-500">Completion Status</p>
            <p className="mt-3 text-lg font-semibold text-slate-950 dark:text-slate-50">
              {statusQuery.data?.profile_completed ? "Profile complete" : "Profile setup still in progress"}
            </p>
            <div className="mt-3 space-y-2 text-sm text-slate-600 dark:text-slate-300">
              {missingFields.map((field) => (
                <p key={field}>- Missing: {field.replaceAll("_", " ")}</p>
              ))}
              {missingFields.length === 0 ? <p>All required fields are complete.</p> : null}
            </div>
          </div>
        </SurfaceCard>

        <SurfaceCard
          title={STEPS[step].label}
          description="Draft changes can be saved at any time, and the final confirmation step unlocks the dashboard."
          className="border-violet-200 bg-[radial-gradient(circle_at_top_right,_rgba(168,85,247,0.14),_transparent_36%),linear-gradient(180deg,rgba(255,255,255,0.98),rgba(245,243,255,0.96))] dark:border-violet-700 dark:bg-[radial-gradient(circle_at_top_right,_rgba(168,85,247,0.2),_transparent_36%),linear-gradient(180deg,rgba(46,16,101,0.26),rgba(15,23,42,0.98))]"
        >
          {isBootstrapping ? (
            <div className="space-y-4 py-10">
              <div className="h-6 w-40 animate-pulse rounded-full bg-violet-100 dark:bg-violet-900/40" />
              <div className="h-14 w-full animate-pulse rounded-3xl bg-violet-100 dark:bg-violet-900/40" />
              <div className="h-32 w-full animate-pulse rounded-3xl bg-violet-100 dark:bg-violet-900/40" />
              <div className="h-32 w-full animate-pulse rounded-3xl bg-violet-100 dark:bg-violet-900/40" />
            </div>
          ) : null}

          <div ref={formFieldsRef}>
          {!isBootstrapping && step === 0 ? (
            <div className="space-y-4">
              <Input name="full_name" value={form.full_name} onChange={(event) => updateField("full_name", event.target.value)} placeholder="Full name" />
              <textarea
                name="bio"
                value={form.bio}
                onChange={(event) => updateField("bio", event.target.value)}
                rows={5}
                className="w-full rounded-2xl border border-violet-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-violet-500 dark:border-violet-700 dark:bg-slate-950 dark:text-slate-100"
                placeholder="Tell the platform who you are and what kind of learner you want to become."
              />
              <div className="rounded-[24px] border border-violet-200 bg-white/85 p-4 dark:border-violet-700 dark:bg-slate-950/60">
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Profile Photo</p>
                <div className="mt-3 flex flex-wrap items-center gap-4">
                  {form.profile_photo_url ? (
                    <Image
                      src={form.profile_photo_url}
                      alt="Profile preview"
                      width={80}
                      height={80}
                      className="h-20 w-20 rounded-3xl object-cover ring-2 ring-violet-200"
                    />
                  ) : (
                    <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-violet-100 text-violet-600">
                      <Camera className="h-6 w-6" />
                    </div>
                  )}
                  <label className="inline-flex cursor-pointer items-center rounded-2xl border border-violet-200 bg-violet-50 px-4 py-2 text-sm font-semibold text-violet-700 transition hover:bg-violet-100 dark:border-violet-700 dark:bg-violet-900/40 dark:text-violet-100">
                    <input
                      type="file"
                      accept="image/png,image/jpeg,image/webp"
                      className="hidden"
                      onChange={(event) => {
                        const file = event.target.files?.[0];
                        if (file) {
                          photoMutation.mutate(file);
                        }
                      }}
                    />
                    {photoMutation.isPending ? "Uploading..." : "Upload photo"}
                  </label>
                </div>
              </div>
            </div>
          ) : null}

          {!isBootstrapping && step === 1 ? (
            <div className="grid gap-4 md:grid-cols-2">
              <Input name="college_name" value={form.college_name} onChange={(event) => updateField("college_name", event.target.value)} placeholder="College / university" />
              <Input name="degree" value={form.degree} onChange={(event) => updateField("degree", event.target.value)} placeholder="Degree" />
              <Input name="year_of_study" value={form.year_of_study} onChange={(event) => updateField("year_of_study", event.target.value)} placeholder="Year of study" />
            </div>
          ) : null}

          {!isBootstrapping && step === 2 ? (
            <div className="grid gap-4">
              <Input name="github_url" value={form.github_url} onChange={(event) => updateField("github_url", event.target.value)} placeholder="https://github.com/username" />
              <Input name="linkedin_url" value={form.linkedin_url} onChange={(event) => updateField("linkedin_url", event.target.value)} placeholder="https://www.linkedin.com/in/username/" />
              <Input name="leetcode_url" value={form.leetcode_url} onChange={(event) => updateField("leetcode_url", event.target.value)} placeholder="https://leetcode.com/username" />
              <Input name="hackerrank_url" value={form.hackerrank_url} onChange={(event) => updateField("hackerrank_url", event.target.value)} placeholder="https://www.hackerrank.com/username" />
              {profileQuery.data?.github_repo_count ? (
                <div className="rounded-[24px] border border-violet-200 bg-white/85 p-4 text-sm text-slate-700 dark:border-violet-700 dark:bg-slate-950/60 dark:text-slate-300">
                  <p className="font-semibold text-slate-900 dark:text-slate-100">Detected GitHub signal</p>
                  <p className="mt-2">Repos: {profileQuery.data.github_repo_count}</p>
                  <p>Activity score: {profileQuery.data.github_activity_score ?? 0}</p>
                  <p>Languages: {(profileQuery.data.github_languages ?? []).join(", ") || "Not yet detected"}</p>
                </div>
              ) : null}
            </div>
          ) : null}

          {!isBootstrapping && step === 3 ? (
            <div className="grid gap-4">
              <select
                name="experience_level"
                value={form.experience_level}
                onChange={(event) => updateField("experience_level", event.target.value as ExperienceLevel | "")}
                className="w-full rounded-2xl border border-violet-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-violet-500 dark:border-violet-700 dark:bg-slate-950 dark:text-slate-100"
              >
                <option value="">Select experience level</option>
                {EXPERIENCE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <select
                name="daily_study_time"
                value={form.daily_study_time}
                onChange={(event) => updateField("daily_study_time", event.target.value as DailyStudyTime | "")}
                className="w-full rounded-2xl border border-violet-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-violet-500 dark:border-violet-700 dark:bg-slate-950 dark:text-slate-100"
              >
                <option value="">Select daily study time</option>
                {STUDY_TIME_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <select
                name="learning_style"
                value={form.learning_style}
                onChange={(event) => updateField("learning_style", event.target.value as LearningStyle | "")}
                className="w-full rounded-2xl border border-violet-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-violet-500 dark:border-violet-700 dark:bg-slate-950 dark:text-slate-100"
              >
                <option value="">Select learning style</option>
                {LEARNING_STYLE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <select
                name="target_timeline"
                value={form.target_timeline}
                onChange={(event) => updateField("target_timeline", event.target.value as TargetTimeline | "")}
                className="w-full rounded-2xl border border-violet-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-violet-500 dark:border-violet-700 dark:bg-slate-950 dark:text-slate-100"
              >
                <option value="">Select target timeline</option>
                {TARGET_TIMELINE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <textarea
                name="learning_goal_note"
                value={form.learning_goal_note}
                onChange={(event) => updateField("learning_goal_note", event.target.value)}
                rows={6}
                className="w-full rounded-2xl border border-violet-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-violet-500 dark:border-violet-700 dark:bg-slate-950 dark:text-slate-100"
                placeholder="What are you trying to achieve, and why does it matter right now?"
              />
            </div>
          ) : null}

          {!isBootstrapping && step === 4 ? (
            <div className="space-y-4">
              <div className="rounded-[28px] border border-violet-200 bg-white/90 p-5 dark:border-violet-700 dark:bg-slate-950/60">
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Ready to unlock the workspace?</p>
                <div className="mt-4 grid gap-3 text-sm text-slate-600 dark:text-slate-300">
                  <p><span className="font-semibold text-slate-900 dark:text-slate-100">Name:</span> {form.full_name || "Missing"}</p>
                  <p><span className="font-semibold text-slate-900 dark:text-slate-100">Academic:</span> {form.college_name || "Missing"} / {form.degree || "Missing"}</p>
                  <p><span className="font-semibold text-slate-900 dark:text-slate-100">Experience:</span> {form.experience_level || "Missing"}</p>
                  <p><span className="font-semibold text-slate-900 dark:text-slate-100">Goal:</span> {form.learning_goal_note || "Missing"}</p>
                  <p><span className="font-semibold text-slate-900 dark:text-slate-100">Completion:</span> {completionPercent}%</p>
                </div>
              </div>
            </div>
          ) : null}
          </div>

          <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-violet-200 pt-5 dark:border-violet-700">
            <div className="flex flex-wrap gap-3">
              <Button type="button" variant="ghost" onClick={() => void saveDraft()} disabled={isBootstrapping || saveMutation.isPending}>
                <Save className="h-4 w-4" />
                {saveMutation.isPending ? "Saving..." : "Save Draft"}
              </Button>
              {step > 0 ? (
                <Button type="button" variant="secondary" onClick={() => setStep((current) => Math.max(current - 1, 0))} disabled={isBootstrapping}>
                  <ChevronLeft className="h-4 w-4" />
                  Back
                </Button>
              ) : null}
            </div>
            {step < STEPS.length - 1 ? (
              <Button type="button" onClick={() => void nextStep()} disabled={isBootstrapping || saveMutation.isPending}>
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            ) : (
              <Button type="button" onClick={() => void submitCompletion()} disabled={isBootstrapping || completeMutation.isPending}>
                {completeMutation.isPending ? "Finishing..." : "Generate My Learning Path"}
              </Button>
            )}
          </div>
        </SurfaceCard>
      </div>
    </div>
  );
}
