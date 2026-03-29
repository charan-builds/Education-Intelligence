"use client";

import Link from "next/link";
import React, { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/hooks/useAuth";
import { useHealthCheck } from "@/hooks/use-health-check";
import { appRoutes, normalizeAppPath } from "@/utils/appRoutes";
import { getRoleRedirectPath } from "@/utils/roleRedirect";

export default function DashboardShell() {
  const router = useRouter();
  const { data, isLoading, isError } = useHealthCheck();
  const { isAuthenticated, role, login, logout, user } = useAuth();
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("Admin@123");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [nextPath, setNextPath] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const rawNextPath = params.get("next");
    setNextPath(rawNextPath && rawNextPath.startsWith("/") ? normalizeAppPath(rawNextPath) : null);
  }, []);

  const connectionLabel = useMemo(() => {
    if (isLoading) {
      return "Checking backend connectivity";
    }
    if (isError) {
      return "Backend unavailable";
    }
    return data?.status === "ok" ? "Backend connected" : data?.status ?? "Backend connected";
  }, [data?.status, isError, isLoading]);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      const authenticatedUser = await login(email, password);
      router.replace(nextPath ?? getRoleRedirectPath(authenticatedUser?.role ?? role));
    } catch {
      setError("Login failed. Check credentials and backend availability.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(14,165,233,0.18),_transparent_30%),linear-gradient(180deg,_#f8fafc_0%,_#e2e8f0_100%)]">
      <div className="mx-auto max-w-7xl px-6 py-10">
        <header className="flex flex-col gap-6 rounded-[32px] border border-white/70 bg-white/80 p-8 shadow-[0_30px_80px_rgba(15,23,42,0.12)] backdrop-blur md:flex-row md:items-start md:justify-between">
          <div className="max-w-2xl">
            <p className="text-sm font-semibold uppercase tracking-[0.3em] text-sky-700">Learnova AI Platform</p>
            <h1 className="mt-4 text-4xl font-semibold tracking-tight text-slate-950 md:text-5xl">
              Multi-tenant learning operations, diagnostics, and roadmap intelligence in one workspace.
            </h1>
            <p className="mt-4 text-lg leading-8 text-slate-600">
              The frontend is now wired directly to FastAPI services for authentication, diagnostics, roadmap generation,
              admin curation, tenant management, and mentor insights.
            </p>
            <div className="mt-6 flex flex-wrap gap-3 text-sm">
              <span className="rounded-full bg-sky-100 px-4 py-2 font-medium text-sky-800">FastAPI connected</span>
              <span className="rounded-full bg-emerald-100 px-4 py-2 font-medium text-emerald-800">JWT auth ready</span>
              <span className="rounded-full bg-amber-100 px-4 py-2 font-medium text-amber-800">Role dashboards active</span>
            </div>
          </div>

          <div className="w-full max-w-md rounded-[28px] border border-slate-200 bg-slate-950 p-6 text-white shadow-2xl">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-300">Platform Status</p>
                <p className="mt-1 text-xl font-semibold">{connectionLabel}</p>
              </div>
              <span
                className={[
                  "rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em]",
                  isError ? "bg-rose-500/20 text-rose-200" : "bg-emerald-500/20 text-emerald-200",
                ].join(" ")}
              >
                {isError ? "offline" : "online"}
              </span>
            </div>

            {isAuthenticated ? (
              <div className="mt-6 space-y-4">
                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
                  <p className="text-sm text-slate-400">Active session</p>
                  <p className="mt-2 text-lg font-semibold text-white">User #{user?.user_id ?? "-"}</p>
                  <p className="mt-1 text-sm capitalize text-slate-300">Role: {role?.replace("_", " ") ?? "unknown"}</p>
                </div>
                <div className="flex gap-3">
                  <Link
                    href={getRoleRedirectPath(role)}
                    className="flex-1 rounded-xl bg-sky-500 px-4 py-3 text-center text-sm font-semibold text-white transition hover:bg-sky-400"
                  >
                    Open Dashboard
                  </Link>
                  <button
                    type="button"
                    onClick={logout}
                    className="rounded-xl border border-slate-700 px-4 py-3 text-sm font-semibold text-slate-200 transition hover:bg-slate-800"
                  >
                    Logout
                  </button>
                </div>
              </div>
            ) : (
              <form className="mt-6 space-y-4" onSubmit={onSubmit}>
                <div>
                  <label className="text-sm font-medium text-slate-300" htmlFor="home-email">
                    Email
                  </label>
                  <input
                    id="home-email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-white outline-none ring-0 placeholder:text-slate-500 focus:border-sky-400"
                    placeholder="you@example.com"
                    type="email"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-300" htmlFor="home-password">
                    Password
                  </label>
                  <input
                    id="home-password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-white outline-none placeholder:text-slate-500 focus:border-sky-400"
                    type="password"
                  />
                </div>
                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full rounded-xl bg-sky-500 px-4 py-3 text-sm font-semibold text-white transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {submitting ? "Signing in..." : "Sign in"}
                </button>
                {error ? <p className="text-sm text-rose-300">{error}</p> : null}
              </form>
            )}
          </div>
        </header>

        <section className="mt-8 grid gap-4 md:grid-cols-3">
          {[
            {
              title: "Student Panel",
              description: "Diagnostic flow, roadmap progress, mentor insights, and next learning actions.",
              href: appRoutes.student.dashboard,
            },
            {
              title: "Teacher Panel",
              description: "Student progress rollups, mastery snapshots, and instructional monitoring.",
              href: appRoutes.teacher.dashboard,
            },
            {
              title: "Admin + Super Admin",
              description: "Users, tenants, topics, questions, goals, and graph curation in connected control panels.",
              href: appRoutes.admin.dashboard,
            },
          ].map((item) => (
            <article key={item.title} className="rounded-[24px] border border-white/70 bg-white/85 p-6 shadow-lg">
              <h2 className="text-xl font-semibold text-slate-950">{item.title}</h2>
              <p className="mt-3 text-sm leading-7 text-slate-600">{item.description}</p>
              <Link
                href={item.href}
                className="mt-5 inline-flex rounded-full border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-sky-400 hover:text-sky-700"
              >
                Explore panel
              </Link>
            </article>
          ))}
        </section>
      </div>
    </main>
  );
}
