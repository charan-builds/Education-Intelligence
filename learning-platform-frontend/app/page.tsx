"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import LandingExperience from "@/components/marketing/LandingExperience";
import { useAuth } from "@/hooks/useAuth";
import { getRoleRedirectPath } from "@/utils/roleRedirect";

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, isReady, role } = useAuth();

  useEffect(() => {
    if (isReady && isAuthenticated) {
      router.replace(getRoleRedirectPath(role));
    }
  }, [isAuthenticated, isReady, role, router]);

  return <LandingExperience />;
}
