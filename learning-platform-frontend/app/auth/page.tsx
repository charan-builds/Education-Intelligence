"use client";

import React, { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowRight, KeyRound, MailCheck, ShieldCheck, Sparkles, Users } from "lucide-react";

import Logo from "@/components/brand/Logo";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";
import {
  acceptInvite,
  confirmEmailVerification,
  confirmPasswordReset,
  register,
  requestEmailVerification,
  requestPasswordReset,
} from "@/services/authService";
import { normalizeAppPath } from "@/utils/appRoutes";

export default function AuthPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isReady, login } = useAuth();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [tenantContext, setTenantContext] = useState("");
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [nextPath, setNextPath] = useState<string | null>(null);
  const inviteToken = useMemo(() => searchParams.get("invite"), [searchParams]);

  useEffect(() => {
    const rawMode = searchParams.get("mode") ?? "login";
    const rawNextPath = searchParams.get("next");
    setNextPath(rawNextPath && rawNextPath.startsWith("/") ? normalizeAppPath(rawNextPath) : null);
    const tenantId = searchParams.get("tenant_id");
    const tenantSubdomain = searchParams.get("tenant");
    const verificationToken = searchParams.get("token") ?? searchParams.get("verification");
    setTenantContext(tenantId ?? tenantSubdomain ?? "");
    setMode(inviteToken ? "invite" : rawMode);
    setToken(inviteToken ?? verificationToken ?? "");
  }, [inviteToken, searchParams]);

  useEffect(() => {
    if (!isReady || !isAuthenticated) {
      return;
    }
    router.replace(nextPath ?? "/dashboard");
  }, [isAuthenticated, isReady, nextPath, router]);

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError("");
    setSuccess("");
    setIsSubmitting(true);

    try {
      const trimmedTenantContext = tenantContext.trim();
      const numericTenantId = Number(trimmedTenantContext);
      const tenantId = Number.isInteger(numericTenantId) && numericTenantId > 0 ? numericTenantId : null;
      const tenantSubdomain = Number.isInteger(numericTenantId) && numericTenantId > 0 ? null : (trimmedTenantContext || null);

      if (mode === "login") {
        await login(email, password, {
          tenant_id: tenantId,
          tenant_subdomain: tenantSubdomain,
        });
        router.replace(nextPath ?? "/dashboard");
        return;
      }

      if (mode === "register") {
        await register(email, password);
        setSuccess("Account created. Sign in with your new credentials.");
        setMode("login");
        return;
      }

      if (mode === "invite") {
        if (!token) {
          throw new Error("Invite token is missing.");
        }
        await acceptInvite(email, password, token);
        setSuccess("Invite accepted. Sign in to continue.");
        setMode("login");
        return;
      }

      if (mode === "forgot-password") {
        if (!tenantId) {
          throw new Error("A numeric tenant ID is required for password reset.");
        }
        await requestPasswordReset(tenantId, email);
        setSuccess("Password reset instructions were issued. Use the reset token to set a new password.");
        return;
      }

      if (mode === "reset-password") {
        if (!token) {
          throw new Error("Reset token is missing.");
        }
        await confirmPasswordReset(token, password);
        setSuccess("Password updated. Sign in with the new password.");
        setMode("login");
        return;
      }

      if (mode === "email-verification") {
        if (token) {
          await confirmEmailVerification(token);
        } else {
          if (!tenantId) {
            throw new Error("A numeric tenant ID is required to issue a verification token.");
          }
          await requestEmailVerification(tenantId, email);
        }
        setSuccess(token ? "Email verified. You can sign in now." : "Verification token issued for this account.");
        if (token) {
          setMode("login");
        }
      }
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to complete the requested auth action.");
    } finally {
      setIsSubmitting(false);
    }
  }

  const pageTitle =
    mode === "register"
      ? "Create your workspace account"
      : mode === "invite"
        ? "Accept your invitation"
        : mode === "forgot-password"
              ? "Request a password reset"
              : mode === "reset-password"
                ? "Set a new password"
                : mode === "email-verification"
                  ? "Verify your email"
                  : "Sign in to your Learnova AI workspace";

  const pageDescription =
    mode === "invite"
      ? "Complete your invited account setup and join the correct tenant securely."
      : mode === "forgot-password"
        ? "Issue a reset token for the right tenant and restore access without admin help."
        : mode === "reset-password"
          ? "Apply a valid reset token and rotate your password safely."
          : mode === "email-verification"
            ? "Confirm ownership of your email address or request a fresh verification token."
            : "The frontend authenticates against FastAPI with secure server-managed sessions, respects tenant scope, and routes each user to the correct role workspace automatically.";

  const modeLinks = [
    { id: "login", label: "Sign in" },
    { id: "register", label: "Register" },
    { id: "forgot-password", label: "Forgot password" },
    { id: "reset-password", label: "Reset password" },
    { id: "email-verification", label: "Verify email" },
  ];

  return (
    <main className="min-h-screen px-6 py-10">
      <div className="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[1.12fr_440px]">
        <section className="mesh-panel relative overflow-hidden rounded-[40px] border border-white/60 p-8 shadow-panel dark:border-slate-700/80">
          <Logo />
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-brand-700 dark:text-brand-100">Secure Access</p>
          <h1 className="mt-4 text-4xl font-semibold tracking-tight text-slate-950 dark:text-slate-50">{pageTitle}</h1>
          <p className="mt-4 max-w-2xl text-lg leading-8 text-slate-600 dark:text-slate-300">{pageDescription}</p>
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
              <h2 className="text-2xl font-semibold">
                {mode === "login" ? "Account Login" : mode === "invite" ? "Invitation Setup" : "Account Recovery"}
              </h2>
              <p className="mt-1 text-sm leading-6 text-slate-300">Complete secure account access, invite onboarding, and recovery from one place.</p>
            </div>
          </div>

          {!inviteToken ? (
            <div className="mt-6 flex flex-wrap gap-2">
              {modeLinks.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => {
                    setMode(item.id);
                    setError("");
                    setSuccess("");
                  }}
                  className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                    mode === item.id ? "bg-white text-slate-950" : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          ) : null}

          <form className="mt-8 space-y-5" onSubmit={onSubmit}>
            {mode !== "reset-password" ? (
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
            ) : null}

            {["login", "forgot-password", "email-verification"].includes(mode) ? (
              <div>
                <label className="text-sm font-medium text-slate-300" htmlFor="auth-tenant">
                  Tenant ID or Workspace
                </label>
                <Input
                  id="auth-tenant"
                  value={tenantContext}
                  onChange={(event) => setTenantContext(event.target.value)}
                  placeholder="e.g. 7 or northwind"
                  className="mt-2 border-slate-700 bg-slate-900 text-white placeholder:text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                />
              </div>
            ) : null}

            {["invite", "reset-password", "email-verification"].includes(mode) ? (
              <div>
                <label className="text-sm font-medium text-slate-300" htmlFor="auth-token">
                  {mode === "invite" ? "Invite token" : mode === "reset-password" ? "Reset token" : "Verification token"}
                </label>
                <Input
                  id="auth-token"
                  value={token}
                  onChange={(event) => setToken(event.target.value)}
                  className="mt-2 border-slate-700 bg-slate-900 text-white placeholder:text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                />
              </div>
            ) : null}

            {mode !== "email-verification" || token ? (
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
            ) : null}

            <Button type="submit" disabled={isSubmitting} className="w-full">
              {isSubmitting
                ? "Submitting..."
                : mode === "login"
                  ? "Sign in"
                  : mode === "register"
                    ? "Create account"
                    : mode === "invite"
                      ? "Accept invite"
                      : mode === "forgot-password"
                        ? "Issue reset token"
                        : mode === "reset-password"
                          ? "Update password"
                          : token
                            ? "Verify email"
                            : "Issue verification token"}
              <ArrowRight className="h-4 w-4" />
            </Button>

            {error ? <p className="text-sm text-rose-300">{error}</p> : null}
            {success ? <p className="text-sm text-emerald-300">{success}</p> : null}
          </form>

          <div className="mt-8 grid gap-3 md:grid-cols-3">
            <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-4">
              <MailCheck className="h-5 w-5 text-brand-300" />
              <p className="mt-3 text-sm font-semibold">Email ownership</p>
              <p className="mt-2 text-sm leading-6 text-slate-400">Verification can be requested or confirmed from the same surface.</p>
            </div>
            <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-4">
              <KeyRound className="h-5 w-5 text-brand-300" />
              <p className="mt-3 text-sm font-semibold">Password recovery</p>
              <p className="mt-2 text-sm leading-6 text-slate-400">Tenant-aware reset flows avoid cross-tenant confusion and dead links.</p>
            </div>
            <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-4">
              <ShieldCheck className="h-5 w-5 text-brand-300" />
              <p className="mt-3 text-sm font-semibold">Invite onboarding</p>
              <p className="mt-2 text-sm leading-6 text-slate-400">Invite tokens now land on a page that can actually finish registration.</p>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
