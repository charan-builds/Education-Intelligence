"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuthContext } from "@/components/providers/AuthProvider";
import { getRoleRedirectPath } from "@/utils/roleRedirect";

declare global {
  interface Window {
    __learnovaLandingHandlers?: {
      onStart?: () => void;
      onLogin?: () => void;
      onDemo?: () => void;
      onSubscribe?: () => void;
      skipIntro?: boolean;
    };
    __learnovaLandingState?: {
      isAuthenticated: boolean;
      role: string | null;
    };
  }
}

const PREMIUM_SCRIPT_ID = "premium-landing-script";
const PREMIUM_SCRIPT_SRC = "/premium/assets/index-CI_zc4A4.js";

export default function PremiumLandingMount() {
  const router = useRouter();
  const { isAuthenticated, role } = useAuthContext();

  useEffect(() => {
    window.__learnovaLandingState = {
      isAuthenticated,
      role,
    };
  }, [isAuthenticated, role]);

  useEffect(() => {
    const originalScrollBehavior = document.documentElement.style.scrollBehavior;
    const originalHtmlLandingFlag = document.documentElement.getAttribute("data-landing-route");
    const originalBodyLandingFlag = document.body.getAttribute("data-landing-route");
    const hadDarkClass = document.documentElement.classList.contains("dark");
    document.documentElement.style.scrollBehavior = "smooth";
    document.documentElement.setAttribute("data-landing-route", "true");
    document.body.setAttribute("data-landing-route", "true");
    document.documentElement.classList.remove("dark");

    window.__learnovaLandingHandlers = {
      onStart: () => {
        const current = window.__learnovaLandingState;
        router.push(current?.isAuthenticated ? getRoleRedirectPath(current.role) : "/register");
      },
      onLogin: () => {
        const current = window.__learnovaLandingState;
        router.push(current?.isAuthenticated ? getRoleRedirectPath(current.role) : "/login");
      },
      onDemo: () => {
        document.getElementById("pricing")?.scrollIntoView({ behavior: "smooth", block: "start" });
      },
      onSubscribe: () => {
        const current = window.__learnovaLandingState;
        router.push(current?.isAuthenticated ? getRoleRedirectPath(current.role) : "/register");
      },
      skipIntro: false,
    };

    let script = document.getElementById(PREMIUM_SCRIPT_ID) as HTMLScriptElement | null;
    if (!script) {
      script = document.createElement("script");
      script.id = PREMIUM_SCRIPT_ID;
      script.type = "module";
      script.crossOrigin = "anonymous";
      script.src = PREMIUM_SCRIPT_SRC;
      document.body.appendChild(script);
    }

    return () => {
      document.documentElement.style.scrollBehavior = originalScrollBehavior;
      if (originalHtmlLandingFlag === null) {
        document.documentElement.removeAttribute("data-landing-route");
      } else {
        document.documentElement.setAttribute("data-landing-route", originalHtmlLandingFlag);
      }
      if (originalBodyLandingFlag === null) {
        document.body.removeAttribute("data-landing-route");
      } else {
        document.body.setAttribute("data-landing-route", originalBodyLandingFlag);
      }
      if (hadDarkClass) {
        document.documentElement.classList.add("dark");
      }
    };
  }, [router]);

  return <div id="root" suppressHydrationWarning />;
}
