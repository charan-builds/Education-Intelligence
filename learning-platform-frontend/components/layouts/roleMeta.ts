"use client";

export type WorkspaceRoleMeta = {
  label: string;
  headline: string;
  helper: string;
};

const ROLE_META: Record<string, WorkspaceRoleMeta> = {
  super_admin: {
    label: "Super Admin",
    headline: "Global platform operations",
    helper: "Manage tenants, monitor platform health, and review cross-tenant system analytics.",
  },
  admin: {
    label: "Institution Admin",
    headline: "Institution control center",
    helper: "Oversee learners, teachers, content operations, and institution-wide analytics.",
  },
  teacher: {
    label: "Teacher",
    headline: "Learning performance command",
    helper: "Track student progress, review diagnostics, and guide cohorts with timely interventions.",
  },
  mentor: {
    label: "Mentor",
    headline: "Mentor guidance workspace",
    helper: "Turn learner signals into support actions, roadmap coaching, and focused recommendations.",
  },
  student: {
    label: "Student",
    headline: "Personal learning intelligence",
    helper: "Take diagnostics, follow your roadmap, and build momentum through clear next steps.",
  },
  independent_learner: {
    label: "Independent Learner",
    headline: "Self-directed learning workspace",
    helper: "Choose goals, generate a personalized roadmap, and improve at your own pace.",
  },
};

export function getWorkspaceRoleMeta(role: string | null | undefined, fallbackLabel: string): WorkspaceRoleMeta {
  if (!role) {
    return {
      label: fallbackLabel,
      headline: "Adaptive learning workspace",
      helper: "Navigate your dashboard, review insights, and keep progress moving.",
    };
  }

  return ROLE_META[role] ?? {
    label: fallbackLabel,
    headline: `${fallbackLabel} workspace`,
    helper: "Navigate your dashboard, review insights, and keep progress moving.",
  };
}
