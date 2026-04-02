"use client";

import React, { ReactNode, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import AccessState from "@/components/auth/AccessState";
import { useAuth } from "@/hooks/useAuth";
import { appRoutes, buildAuthPath } from "@/utils/appRoutes";
import { getRoleRedirectPath, roleHasAccess } from "@/utils/roleRedirect";

type RequireRoleProps = {
  allowedRoles: string[];
  children: ReactNode;
};

export default function RequireRole({ allowedRoles, children }: RequireRoleProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { isReady, isAuthenticated, role, requiresProfileCompletion } = useAuth();

  useEffect(() => {
    if (!isReady) {
      return;
    }
    if (!isAuthenticated) {
      router.replace(buildAuthPath("login"));
      return;
    }
    if (requiresProfileCompletion && pathname !== appRoutes.student.profile) {
      router.replace(appRoutes.student.profile);
      return;
    }
    if (role && !roleHasAccess(role, allowedRoles)) {
      router.replace(getRoleRedirectPath(role));
    }
  }, [allowedRoles, isAuthenticated, isReady, pathname, requiresProfileCompletion, role, router]);

  if (!isReady) {
    return <AccessState mode="loading" />;
  }

  if (!isAuthenticated) {
    return <AccessState mode="redirecting" description="Redirecting to sign in..." />;
  }

  if (requiresProfileCompletion && pathname !== appRoutes.student.profile) {
    return <AccessState mode="redirecting" description="Redirecting to complete your profile..." />;
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
