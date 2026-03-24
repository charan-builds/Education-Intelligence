"use client";

import React, { ReactNode, useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/hooks/useAuth";
import { getRoleRedirectPath, roleHasAccess } from "@/utils/roleRedirect";

type RequireRoleProps = {
  allowedRoles: string[];
  children: ReactNode;
};

export default function RequireRole({ allowedRoles, children }: RequireRoleProps) {
  const router = useRouter();
  const { isReady, isAuthenticated, role } = useAuth();

  useEffect(() => {
    if (!isReady) {
      return;
    }
    if (!isAuthenticated) {
      router.replace("/auth");
      return;
    }
    if (role && !roleHasAccess(role, allowedRoles)) {
      router.replace(getRoleRedirectPath(role));
    }
  }, [allowedRoles, isAuthenticated, isReady, role, router]);

  if (!isReady) {
    return <main className="mx-auto min-h-screen max-w-4xl px-6 py-12 text-slate-600">Loading session...</main>;
  }

  if (!isAuthenticated || (role && !roleHasAccess(role, allowedRoles))) {
    return <main className="mx-auto min-h-screen max-w-4xl px-6 py-12 text-slate-600">Redirecting...</main>;
  }

  return <>{children}</>;
}
