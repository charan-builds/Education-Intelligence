"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/hooks/useAuth";
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
  const { isReady, role } = useAuth();

  useEffect(() => {
    if (!isReady) {
      return;
    }

    router.replace(useRoleRedirect ? getRoleRedirectPath(role) : fallbackPath);
  }, [fallbackPath, isReady, role, router, useRoleRedirect]);

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl items-center justify-center px-6 py-12">
      <p className="text-sm text-slate-600 dark:text-slate-400">Redirecting...</p>
    </main>
  );
}
