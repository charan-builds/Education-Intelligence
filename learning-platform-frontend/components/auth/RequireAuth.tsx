"use client";

import type { ReactNode } from "react";
import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import AccessState from "@/components/auth/AccessState";
import { useAuth } from "@/hooks/useAuth";
import { buildAuthPath } from "@/utils/appRoutes";

type RequireAuthProps = {
  children: ReactNode;
};

const PUBLIC_ROUTES = ["/", "/auth", "/login", "/register"];

export default function RequireAuth({ children }: RequireAuthProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { isReady, isAuthenticated } = useAuth();

  useEffect(() => {
    if (!isReady) {
      return;
    }
    if (!isAuthenticated && pathname && !PUBLIC_ROUTES.includes(pathname)) {
      router.replace(buildAuthPath("login", pathname));
    }
  }, [isAuthenticated, isReady, pathname, router]);

  if (!isReady) {
    return <AccessState mode="loading" />;
  }

  if (!isAuthenticated && pathname && !PUBLIC_ROUTES.includes(pathname)) {
    return <AccessState mode="redirecting" description="Redirecting to sign in..." />;
  }

  return <>{children}</>;
}
