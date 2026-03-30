import type { UserRole } from "@/utils/roleRedirect";

export const appRoutes = {
  auth: "/login",
  student: {
    dashboard: "/student/dashboard",
    goals: "/student/goals",
    diagnostic: "/student/diagnostic",
    diagnosticResult: "/student/diagnostic/result",
    roadmap: "/student/roadmap",
    mentor: "/student/mentor",
    progress: "/student/progress",
    network: "/student/network",
    digitalTwin: "/student/digital-twin",
    career: "/student/career",
    notifications: "/student/notifications",
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
  "/auth/login": appRoutes.auth,
  "/auth/register": "/register",
  "/dashboard": appRoutes.auth,
  "/dashboard/student": appRoutes.student.dashboard,
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
  "/mentor": appRoutes.mentor.dashboard,
};

export function normalizeAppPath(path: string | null | undefined): string {
  if (!path || !path.startsWith("/")) {
    return appRoutes.auth;
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

export function sanitizeAuthRedirectTarget(
  rawNextPath: string | null | undefined,
  currentAuthPath: "/login" | "/register",
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

export function getRoleHomePath(role: UserRole | null | undefined): string {
  switch (role) {
    case "student":
      return appRoutes.student.dashboard;
    case "teacher":
      return appRoutes.teacher.dashboard;
    case "mentor":
      return appRoutes.mentor.dashboard;
    case "admin":
      return appRoutes.admin.dashboard;
    case "super_admin":
      return appRoutes.superAdmin.dashboard;
    default:
      return "/";
  }
}

export function getRolePrefix(pathname: string): UserRole | null {
  if (pathname.startsWith("/student")) {
    return "student";
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
