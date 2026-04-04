"use client";

import type { ReactNode } from "react";
import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import AccessState from "@/components/auth/AccessState";
import { useAuth } from "@/hooks/useAuth";
import { buildAuthPath, getRoleProfilePath } from "@/utils/appRoutes";

type RequireAuthProps = {
  children: ReactNode;
};

const PUBLIC_ROUTES = ["/", "/auth", "/login", "/register"];

export default function RequireAuth({ children }: RequireAuthProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { isReady, isAuthenticated, requiresProfileCompletion, role } = useAuth();

  useEffect(() => {
    if (!isReady) {
      return;
    }
    if (!isAuthenticated && pathname && !PUBLIC_ROUTES.includes(pathname)) {
      router.replace(buildAuthPath("login", pathname));
      return;
    }
    if (
      isAuthenticated &&
      requiresProfileCompletion &&
      pathname &&
      !PUBLIC_ROUTES.includes(pathname) &&
      pathname !== getRoleProfilePath(role)
    ) {
      router.replace(getRoleProfilePath(role));
    }
  }, [isAuthenticated, isReady, pathname, requiresProfileCompletion, role, router]);

  if (!isReady) {
    return <AccessState mode="loading" />;
  }

  if (!isAuthenticated && pathname && !PUBLIC_ROUTES.includes(pathname)) {
    return <AccessState mode="redirecting" description="Redirecting to sign in..." />;
  }

  if (isAuthenticated && requiresProfileCompletion && pathname && pathname !== getRoleProfilePath(role)) {
    return <AccessState mode="redirecting" description="Redirecting to complete your profile..." />;
  }

  return <>{children}</>;
}
