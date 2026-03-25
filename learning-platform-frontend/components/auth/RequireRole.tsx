"use client";

import React, { ReactNode, useEffect } from "react";
import { useRouter } from "next/navigation";

import AccessState from "@/components/auth/AccessState";
import { useAuth } from "@/hooks/useAuth";
import { normalizeAppPath } from "@/utils/appRoutes";
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
      router.replace(normalizeAppPath("/auth"));
      return;
    }
    if (role && !roleHasAccess(role, allowedRoles)) {
      router.replace(getRoleRedirectPath(role));
    }
  }, [allowedRoles, isAuthenticated, isReady, role, router]);

  if (!isReady) {
    return <AccessState mode="loading" />;
  }

  if (!isAuthenticated) {
    return <AccessState mode="redirecting" description="Redirecting to sign in..." />;
  }

  if (role && !roleHasAccess(role, allowedRoles)) {
    return (
      <AccessState
        mode="unauthorized"
        redirectHref={getRoleRedirectPath(role)}
        redirectLabel="Open my workspace"
      />
    );
  }

  return <>{children}</>;
}
