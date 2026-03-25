import type { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime";

import { getRoleHomePath } from "@/utils/appRoutes";

export type UserRole = "student" | "teacher" | "mentor" | "admin" | "super_admin";

export function canonicalizeRole(role: string | null | undefined): UserRole | null {
  if (!role) {
    return null;
  }

  const normalized = role.replace("-", "_");
  if (normalized === "super_admin" || normalized === "admin" || normalized === "teacher" || normalized === "mentor" || normalized === "student") {
    return normalized;
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
  return getRoleHomePath(normalized);
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
