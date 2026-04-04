import type { UserRole } from "@/utils/roleRedirect";

export const appRoutes = {
  marketingHome: "/",
  workspaceHome: "/auth",
  auth: "/auth",
  student: {
    dashboard: "/student/dashboard",
    goals: "/student/goals",
    diagnostic: "/student/diagnostic",
    diagnosticResult: "/student/diagnostic/result",
    roadmap: "/student/roadmap",
    profile: "/student/profile",
    mentor: "/student/mentor",
    progress: "/student/progress",
    network: "/student/network",
    digitalTwin: "/student/digital-twin",
    career: "/student/career",
    notifications: "/student/notifications",
  },
  independentLearner: {
    dashboard: "/independent-learner/dashboard",
    goals: "/independent-learner/goals",
    diagnostic: "/independent-learner/diagnostic",
    diagnosticResult: "/independent-learner/diagnostic/result",
    roadmap: "/independent-learner/roadmap",
    profile: "/independent-learner/profile",
    mentor: "/independent-learner/mentor",
    progress: "/independent-learner/progress",
  },
  teacher: {
    dashboard: "/teacher/dashboard",
    students: "/teacher/students",
    insights: "/teacher/insights",
  },
  admin: {
    dashboard: "/admin/dashboard",
    users: "/admin/users",
    content: "/admin/content",
    goals: "/admin/goals",
    community: "/admin/community",
    ecosystem: "/admin/ecosystem",
    ml: "/admin/ml",
    featureFlags: "/admin/feature-flags",
  },
  mentor: {
    dashboard: "/mentor/dashboard",
    network: "/mentor/network",
    chat: "/mentor/chat",
  },
  superAdmin: {
    dashboard: "/super-admin/dashboard",
    tenants: "/super-admin/tenants",
    outbox: "/super-admin/outbox",
    health: "/super-admin/health",
  },
} as const;

const LEGACY_ROUTE_MAP: Record<string, string> = {
  "/auth": appRoutes.auth,
  "/dashboard": appRoutes.auth,
  "/student": appRoutes.student.dashboard,
  "/independent-learner": appRoutes.independentLearner.dashboard,
  "/teacher": appRoutes.teacher.dashboard,
  "/mentor": appRoutes.mentor.dashboard,
  "/admin": appRoutes.admin.dashboard,
  "/super-admin": appRoutes.superAdmin.dashboard,
  "/dashboard/student": appRoutes.student.dashboard,
  "/dashboard/independent-learner": appRoutes.independentLearner.dashboard,
  "/dashboard/teacher": appRoutes.teacher.dashboard,
  "/dashboard/admin": appRoutes.admin.dashboard,
  "/dashboard/super-admin": appRoutes.superAdmin.dashboard,
  "/goals": appRoutes.student.goals,
  "/goals/select": appRoutes.student.goals,
  "/diagnostic": appRoutes.student.diagnostic,
  "/diagnostic/test": appRoutes.student.diagnostic,
  "/diagnostic/result": appRoutes.student.diagnosticResult,
  "/roadmap": appRoutes.student.roadmap,
  "/roadmap/view": appRoutes.student.roadmap,
  "/progress": appRoutes.student.progress,
  "/profile": appRoutes.student.profile,
};

export function normalizeAppPath(path: string | null | undefined): string {
  if (!path || !path.startsWith("/")) {
    return appRoutes.workspaceHome;
  }

  const [pathname, query = ""] = path.split("?");
  const normalizedPath = LEGACY_ROUTE_MAP[pathname] ?? pathname;
  return query ? `${normalizedPath}?${query}` : normalizedPath;
}

export function isAuthEntryPath(path: string | null | undefined): boolean {
  if (!path) {
    return false;
  }

  return path === "/login" || path === "/register" || path === "/auth";
}

export function buildAuthPath(
  mode: "login" | "register" | "forgot-password" | "reset-password" | "email-verification" = "login",
  nextPath?: string | null,
  extraParams?: Record<string, string | number | null | undefined>,
): string {
  const params = new URLSearchParams();
  params.set("mode", mode);

  const sanitizedNext = sanitizeAuthRedirectTarget(nextPath, appRoutes.auth);
  if (sanitizedNext) {
    params.set("next", sanitizedNext);
  }

  if (extraParams) {
    Object.entries(extraParams).forEach(([key, value]) => {
      if (value === null || value === undefined || value === "") {
        return;
      }
      params.set(key, String(value));
    });
  }

  return `${appRoutes.auth}?${params.toString()}`;
}

export function sanitizeAuthRedirectTarget(
  rawNextPath: string | null | undefined,
  currentAuthPath: "/auth" | "/login" | "/register" = appRoutes.auth,
): string | null {
  if (!rawNextPath || !rawNextPath.startsWith("/")) {
    return null;
  }

  const normalizedPath = normalizeAppPath(rawNextPath);
  if (!normalizedPath.startsWith("/")) {
    return null;
  }

  const [pathname] = normalizedPath.split("?");
  if (isAuthEntryPath(pathname) || pathname === currentAuthPath) {
    return null;
  }

  return normalizedPath;
}

function normalizeRoleInput(role: string | null | undefined): UserRole | null {
  if (!role) {
    return null;
  }
  const normalized = role.replace("-", "_");
  if (
    normalized === "student" ||
    normalized === "independent_learner" ||
    normalized === "teacher" ||
    normalized === "mentor" ||
    normalized === "admin" ||
    normalized === "super_admin"
  ) {
    return normalized;
  }
  return null;
}

export function getRoleHomePath(role: string | null | undefined): string {
  switch (normalizeRoleInput(role)) {
    case "student":
      return appRoutes.student.dashboard;
    case "independent_learner":
      return appRoutes.independentLearner.dashboard;
    case "teacher":
      return appRoutes.teacher.dashboard;
    case "mentor":
      return appRoutes.mentor.dashboard;
    case "admin":
      return appRoutes.admin.dashboard;
    case "super_admin":
      return appRoutes.superAdmin.dashboard;
    default:
      return appRoutes.workspaceHome;
  }
}

export function getRoleProfilePath(role: string | null | undefined): string {
  switch (normalizeRoleInput(role)) {
    case "independent_learner":
      return appRoutes.independentLearner.profile;
    case "student":
      return appRoutes.student.profile;
    default:
      return appRoutes.student.profile;
  }
}

export function getLearnerRoutes(role: string | null | undefined) {
  return normalizeRoleInput(role) === "independent_learner" ? appRoutes.independentLearner : appRoutes.student;
}

export function getLearnerTopicPath(role: string | null | undefined, topicId: number | string): string {
  const normalizedTopicId = String(topicId);
  if (normalizeRoleInput(role) === "independent_learner") {
    return `/independent-learner/topics/${normalizedTopicId}`;
  }
  return `/student/topics/${normalizedTopicId}`;
}

export function getRolePrefix(pathname: string): UserRole | null {
  if (pathname.startsWith("/student")) {
    return "student";
  }
  if (pathname.startsWith("/independent-learner")) {
    return "independent_learner";
  }
  if (pathname.startsWith("/teacher")) {
    return "teacher";
  }
  if (pathname.startsWith("/mentor")) {
    return "mentor";
  }
  if (pathname.startsWith("/admin")) {
    return "admin";
  }
  if (pathname.startsWith("/super-admin")) {
    return "super_admin";
  }
  return null;
}
