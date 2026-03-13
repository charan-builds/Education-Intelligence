import type { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime";

export type UserRole = "student" | "teacher" | "admin" | "super_admin";

const ROLE_REDIRECT_MAP: Record<UserRole, string> = {
  student: "/dashboard/student",
  teacher: "/dashboard/teacher",
  admin: "/dashboard/admin",
  super_admin: "/dashboard/super-admin",
};

export function getRoleRedirectPath(role: string | null | undefined): string {
  if (!role) {
    return "/";
  }
  return ROLE_REDIRECT_MAP[role as UserRole] ?? "/";
}

export function redirectByRole(router: AppRouterInstance, role: string | null | undefined): void {
  router.replace(getRoleRedirectPath(role));
}
