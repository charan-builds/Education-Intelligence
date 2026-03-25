"use client";

import React, { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, ShieldCheck, Sparkles, Users } from "lucide-react";

import Logo from "@/components/brand/Logo";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";
import { normalizeAppPath } from "@/utils/appRoutes";
import { getRoleRedirectPath } from "@/utils/roleRedirect";

export default function AuthPage() {
  const router = useRouter();
  const { isAuthenticated, isReady, login, role } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [nextPath, setNextPath] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const rawNextPath = params.get("next");
    setNextPath(rawNextPath && rawNextPath.startsWith("/") ? normalizeAppPath(rawNextPath) : null);
  }, []);

  useEffect(() => {
    if (!isReady || !isAuthenticated) {
      return;
    }
    router.replace(nextPath ?? getRoleRedirectPath(role));
  }, [isAuthenticated, isReady, nextPath, role, router]);

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const user = await login(email, password);
      router.replace(nextPath ?? getRoleRedirectPath(user?.role));
    } catch {
      setError("Unable to sign in. Verify the backend is running and the credentials are valid.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen px-6 py-10">
      <div className="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[1.12fr_440px]">
        <section className="mesh-panel relative overflow-hidden rounded-[40px] border border-white/60 p-8 shadow-panel dark:border-slate-700/80">
          <Logo />
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-brand-700 dark:text-brand-100">Secure Access</p>
          <h1 className="mt-4 text-4xl font-semibold tracking-tight text-slate-950 dark:text-slate-50">
            Sign in to your Learning Intelligence workspace
          </h1>
          <p className="mt-4 max-w-2xl text-lg leading-8 text-slate-600 dark:text-slate-300">
            The frontend authenticates against FastAPI with secure server-managed sessions, respects tenant scope, and routes each user to the correct role workspace automatically.
          </p>
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {[
              {
                title: "Student",
                description: "Diagnostics, roadmaps, mentor signals, and progress tracking.",
                icon: Sparkles,
              },
              {
                title: "Teacher",
                description: "Cohort performance, mastery analytics, and batch insights.",
                icon: Users,
              },
              {
                title: "Admin",
                description: "Content operations, feature flags, and community moderation.",
                icon: ShieldCheck,
              },
            ].map((item) => (
              <article key={item.title} className="rounded-[28px] border border-slate-200 bg-white/75 p-5 dark:border-slate-700 dark:bg-slate-900/70">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-brand-100 text-brand-700 dark:bg-brand-900/50 dark:text-brand-100">
                  <item.icon className="h-5 w-5" />
                </div>
                <h2 className="mt-4 text-lg font-semibold text-slate-900 dark:text-slate-100">{item.title}</h2>
                <p className="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-400">{item.description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="rounded-[36px] border border-slate-200 bg-slate-950 p-8 text-white shadow-2xl dark:border-slate-700">
          <div className="flex items-center gap-3">
            <Logo showWordmark={false} />
            <div>
              <h2 className="text-2xl font-semibold">Account Login</h2>
              <p className="mt-1 text-sm leading-6 text-slate-300">Use your tenant credentials to open the correct role dashboard.</p>
            </div>
          </div>

          <form className="mt-8 space-y-5" onSubmit={onSubmit}>
            <div>
              <label className="text-sm font-medium text-slate-300" htmlFor="auth-email">
                Email
              </label>
              <Input
                id="auth-email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="mt-2 border-slate-700 bg-slate-900 text-white placeholder:text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
              />
            </div>

            <div>
              <label className="text-sm font-medium text-slate-300" htmlFor="auth-password">
                Password
              </label>
              <Input
                id="auth-password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="mt-2 border-slate-700 bg-slate-900 text-white placeholder:text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
              />
            </div>

            <Button type="submit" disabled={isSubmitting} className="w-full">
              {isSubmitting ? "Signing in..." : "Sign in"}
              <ArrowRight className="h-4 w-4" />
            </Button>

            {error ? <p className="text-sm text-rose-300">{error}</p> : null}
          </form>
        </section>
      </div>
    </main>
  );
}
