import type { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime";

export type UserRole = "student" | "teacher" | "mentor" | "admin" | "super_admin";

const ROLE_REDIRECT_MAP: Record<UserRole, string> = {
  student: "/student/dashboard",
  teacher: "/teacher/dashboard",
  mentor: "/mentor/dashboard",
  admin: "/admin/dashboard",
  super_admin: "/super-admin/dashboard",
};

export function canonicalizeRole(role: string | null | undefined): UserRole | null {
  if (!role) {
    return null;
  }

  if (role in ROLE_REDIRECT_MAP) {
    return role as UserRole;
  }

  return null;
}

export function normalizeAccessRole(role: string | null | undefined): UserRole | null {
  return canonicalizeRole(role);
}

export function getRoleRedirectPath(role: string | null | undefined): string {
  const normalized = canonicalizeRole(role);
  if (!normalized) {
    return "/";
  }
  return ROLE_REDIRECT_MAP[normalized] ?? "/";
}

export function roleHasAccess(
  role: string | null | undefined,
  allowedRoles: string[],
): boolean {
  const activeRole = normalizeAccessRole(role);
  if (!activeRole) {
    return false;
  }

  return allowedRoles
    .map((item) => normalizeAccessRole(item))
    .filter((item): item is UserRole => item !== null)
    .includes(activeRole);
}

export function redirectByRole(router: AppRouterInstance, role: string | null | undefined): void {
  router.replace(getRoleRedirectPath(role));
}
