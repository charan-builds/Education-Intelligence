"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, BarChart3, Bot, ShieldCheck, Sparkles } from "lucide-react";

import ThemeToggle from "@/components/ui/ThemeToggle";
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

  return (
    <main className="min-h-screen px-6 py-8">
      <div className="mx-auto max-w-7xl">
        <div className="flex justify-end">
          <ThemeToggle />
        </div>
        <section className="mesh-panel relative mt-6 overflow-hidden rounded-[40px] border border-white/60 px-8 py-10 shadow-panel dark:border-slate-700/80 md:px-12 md:py-14">
          <div className="absolute inset-y-0 right-0 hidden w-[42%] bg-[radial-gradient(circle_at_top_right,_rgba(255,255,255,0.28),_transparent_55%)] lg:block" />
          <div className="relative grid gap-10 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-brand-700 dark:text-brand-100">
                Learning Intelligence Platform
              </p>
              <h1 className="mt-4 text-balance text-4xl font-semibold tracking-tight text-slate-950 dark:text-slate-50 md:text-6xl">
                Multi-tenant learning operations with roadmap intelligence and role-aware workspaces.
              </h1>
              <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-600 dark:text-slate-300">
                A polished SaaS control plane for learners, teachers, admins, mentors, and platform operators built on Next.js and FastAPI.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link
                  href="/auth"
                  className="inline-flex items-center gap-2 rounded-2xl bg-gradient-to-r from-brand-700 via-brand-600 to-brand-500 px-5 py-3 text-sm font-semibold text-white shadow-glow"
                >
                  Sign in
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  href="/auth?next=/student/dashboard"
                  className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white/90 px-5 py-3 text-sm font-semibold text-slate-900 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                >
                  Explore workspaces
                </Link>
              </div>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              {[
                {
                  title: "Adaptive learner dashboards",
                  description: "Roadmaps, weak-topic watchlists, mentor guidance, and progress visibility.",
                  icon: Sparkles,
                },
                {
                  title: "Teacher analytics",
                  description: "Cohort completion, mastery distribution, and instructional watchlists.",
                  icon: BarChart3,
                },
                {
                  title: "Admin controls",
                  description: "Users, topics, questions, goals, community moderation, and feature flags.",
                  icon: ShieldCheck,
                },
                {
                  title: "Mentor experience",
                  description: "Guidance panels, notifications, and chat workflows ready for AI upgrades.",
                  icon: Bot,
                },
              ].map((item) => (
                <article
                  key={item.title}
                  className="rounded-[28px] border border-white/60 bg-white/75 p-5 shadow-panel dark:border-slate-700/80 dark:bg-slate-900/70"
                >
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-100 text-brand-700 dark:bg-brand-900/50 dark:text-brand-100">
                    <item.icon className="h-5 w-5" />
                  </div>
                  <h2 className="mt-4 text-xl font-semibold text-slate-950 dark:text-slate-100">{item.title}</h2>
                  <p className="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-400">{item.description}</p>
                </article>
              ))}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
