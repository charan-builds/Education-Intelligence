"use client";

import type { ReactNode } from "react";
import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import AccessState from "@/components/auth/AccessState";
import { useAuth } from "@/hooks/useAuth";

type RequireAuthProps = {
  children: ReactNode;
};

const PUBLIC_ROUTES = ["/", "/login", "/register"];

export default function RequireAuth({ children }: RequireAuthProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { isReady, isAuthenticated } = useAuth();

  useEffect(() => {
    if (!isReady) {
      return;
    }
    if (!isAuthenticated && pathname && !PUBLIC_ROUTES.includes(pathname)) {
      const next = pathname ? `?next=${encodeURIComponent(pathname)}` : "";
      router.replace(`/login${next}`);
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
