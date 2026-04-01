"use client";

import { useEffect } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import AccessState from "@/components/auth/AccessState";
import { useAuth } from "@/hooks/useAuth";
import { normalizeAppPath } from "@/utils/appRoutes";
import { getRoleRedirectPath } from "@/utils/roleRedirect";

type ClientRouteRedirectProps = {
  fallbackPath: string;
  useRoleRedirect?: boolean;
};

export default function ClientRouteRedirect({
  fallbackPath,
  useRoleRedirect = false,
}: ClientRouteRedirectProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { isReady, role } = useAuth();

  useEffect(() => {
    if (!isReady) {
      return;
    }
    const query = searchParams.toString();
    const targetBase = useRoleRedirect && role ? getRoleRedirectPath(role) : normalizeAppPath(fallbackPath);
    const target = query ? `${targetBase}?${query}` : targetBase;
    if (target !== `${pathname}${query ? `?${query}` : ""}`) {
      router.replace(target);
    }
  }, [fallbackPath, isReady, pathname, role, router, searchParams, useRoleRedirect]);

  return <AccessState mode="redirecting" />;
}
