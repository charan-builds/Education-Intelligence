"use client";

import React from "react";
import type { FormEvent } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
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
  setupMfa,
} from "@/services/authService";
import { appRoutes, buildAuthPath, getRoleProfilePath, sanitizeAuthRedirectTarget } from "@/utils/appRoutes";
import { getRoleRedirectPath } from "@/utils/roleRedirect";

type AuthPageClientProps = {
  initialMode?: AuthMode;
};

type AuthMode = "login" | "register" | "invite" | "forgot-password" | "reset-password" | "email-verification";

function getLocalEmailInboxHint(): string {
  if (typeof window === "undefined") {
    return "";
  }

  const hostname = window.location.hostname;
  if (hostname === "127.0.0.1" || hostname === "localhost") {
    return " Local Docker email is routed to Mailpit at http://127.0.0.1:8025.";
  }

  return "";
}

export default function AuthPageClient({ initialMode = "login" }: AuthPageClientProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isReady, login, role, requiresProfileCompletion } = useAuth();
  const [manualMode, setManualMode] = useState<AuthMode | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [tenantContext, setTenantContext] = useState("");
  const [token, setToken] = useState("");
  const [mfaCode, setMfaCode] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [nextPath, setNextPath] = useState<string | null>(null);
  const autoVerifiedTokenRef = useRef<string | null>(null);
  const inviteToken = useMemo(() => searchParams.get("invite"), [searchParams]);
  const modeParam = useMemo(() => searchParams.get("mode") as AuthMode | null, [searchParams]);
  const nextParam = useMemo(() => searchParams.get("next"), [searchParams]);
  const emailParam = useMemo(() => searchParams.get("email"), [searchParams]);
  const tenantIdParam = useMemo(() => searchParams.get("tenant_id"), [searchParams]);
  const tenantSubdomainParam = useMemo(() => searchParams.get("tenant"), [searchParams]);
  const verificationTokenParam = useMemo(
    () => searchParams.get("token") ?? searchParams.get("verification"),
    [searchParams],
  );
  const mode = inviteToken ? "invite" : (manualMode ?? modeParam ?? initialMode);

  useEffect(() => {
    setNextPath(sanitizeAuthRedirectTarget(nextParam, appRoutes.auth));
    setTenantContext(tenantIdParam ?? tenantSubdomainParam ?? "");
    setEmail(emailParam ?? "");
    setToken(inviteToken ?? verificationTokenParam ?? "");
    setManualMode(null);
  }, [emailParam, inviteToken, modeParam, nextParam, tenantIdParam, tenantSubdomainParam, verificationTokenParam]);

  useEffect(() => {
    if (!isReady || !isAuthenticated) {
      return;
    }
    if (requiresProfileCompletion) {
      router.replace(getRoleProfilePath(role));
      return;
    }
    router.replace(nextPath ?? getRoleRedirectPath(role));
  }, [isAuthenticated, isReady, nextPath, requiresProfileCompletion, role, router]);

  useEffect(() => {
    async function autoVerifyEmailLink(): Promise<void> {
      if (mode !== "email-verification" || !token || autoVerifiedTokenRef.current === token) {
        return;
      }
      autoVerifiedTokenRef.current = token;
      setIsSubmitting(true);
      setError("");
      setSuccess("Verifying your email and preparing sign in...");
      try {
        await confirmEmailVerification(token);
        const loginPath = buildAuthPath("login", null, {
          email,
          tenant_id: tenantIdParam ?? tenantContext,
        });
        if (typeof window !== "undefined") {
          window.location.assign(loginPath);
          return;
        }
        router.replace(loginPath);
      } catch (verificationError) {
        setError(
          verificationError instanceof Error ? verificationError.message : "Unable to verify this email link.",
        );
      } finally {
        setIsSubmitting(false);
      }
    }

    void autoVerifyEmailLink();
  }, [email, mode, router, tenantContext, tenantIdParam, token]);

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
        const session = await login(email, password, {
          tenant_id: tenantId,
          tenant_subdomain: tenantSubdomain,
        }, mfaCode);
        if (session.requires_profile_completion) {
          setSuccess("Profile completion is required before diagnostic, roadmap, and dashboard access.");
          router.replace(getRoleProfilePath(session.user.role));
          return;
        }
        router.replace(nextPath ?? getRoleRedirectPath(session.user.role));
        return;
      }

      if (mode === "register") {
        const registeredUser = await register(email, password);
        setSuccess(
          `Account created. Your personal workspace tenant ID is ${registeredUser.tenant_id}. Check your email for the verification link before signing in.${getLocalEmailInboxHint()}`,
        );
        const verificationPath = buildAuthPath("email-verification", null, {
          email: registeredUser.email,
          tenant_id: registeredUser.tenant_id,
        });
        if (typeof window !== "undefined") {
          window.location.assign(verificationPath);
        } else {
          router.replace(verificationPath);
        }
        return;
      }

      if (mode === "invite") {
        if (!token) {
          throw new Error("Invite token is missing.");
        }
        await acceptInvite(email, password, token);
        setSuccess("Invite accepted. Sign in to continue.");
        setManualMode("login");
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
        setManualMode("login");
        return;
      }

      if (mode === "email-verification") {
        if (token) {
          await confirmEmailVerification(token);
        } else {
          if (!tenantId) {
            throw new Error("A numeric tenant ID is required to resend a verification email.");
          }
          await requestEmailVerification(tenantId, email);
        }
        setSuccess(
          token
            ? "Email verified. You can sign in now."
            : `Verification email sent. Open the link in your inbox to finish account activation.${getLocalEmailInboxHint()}`,
        );
        if (token) {
          const loginPath = buildAuthPath("login", null, {
            email,
            tenant_id: tenantIdParam ?? tenantId,
          });
          if (typeof window !== "undefined") {
            window.location.assign(loginPath);
          } else {
            router.replace(loginPath);
          }
        }
      }
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to complete the requested auth action.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleMfaQuickSetup(): Promise<void> {
    setError("");
    setSuccess("");
    try {
      const setup = await setupMfa();
      setSuccess(`MFA setup secret: ${setup.manual_entry_code}`);
    } catch (setupError) {
      setError(setupError instanceof Error ? setupError.message : "Unable to prepare MFA.");
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

  const modeLinks: Array<{ id: AuthMode; label: string }> = [
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
                    setManualMode(item.id);
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
                {mode === "login" ? (
                  <p className="mt-2 text-xs leading-5 text-slate-400">
                    Institution users can enter tenant context here. Independent learners can leave this blank and sign in with their email directly.
                  </p>
                ) : null}
              </div>
            ) : null}

            {["invite", "reset-password"].includes(mode) || (mode === "email-verification" && Boolean(token)) ? (
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

            {mode !== "email-verification" ? (
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

            {mode === "login" ? (
              <div>
                <label className="text-sm font-medium text-slate-300" htmlFor="auth-mfa">
                  MFA code
                </label>
                <Input
                  id="auth-mfa"
                  value={mfaCode}
                  onChange={(event) => setMfaCode(event.target.value)}
                  placeholder="Optional unless MFA is enabled"
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
                    : "Resend verification email"}
              <ArrowRight className="h-4 w-4" />
            </Button>

            {mode === "login" ? (
              <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                <p className="text-sm font-semibold text-white">Security quick setup</p>
                <p className="mt-1 text-xs leading-6 text-slate-400">
                  Already signed in on another tab? Generate an authenticator secret here, then finish setup from your profile page.
                </p>
                <button
                  type="button"
                  onClick={() => void handleMfaQuickSetup()}
                  className="mt-3 inline-flex items-center gap-2 rounded-xl border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-200 transition hover:bg-slate-800"
                >
                  <ShieldCheck className="h-4 w-4" />
                  Generate MFA secret
                </button>
              </div>
            ) : null}

            {error ? <p className="text-sm text-rose-300">{error}</p> : null}
            {success ? <p className="text-sm text-emerald-300">{success}</p> : null}
          </form>

          <div className="mt-8 grid gap-3 md:grid-cols-3">
            <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-4">
              <MailCheck className="h-5 w-5 text-brand-300" />
              <p className="mt-3 text-sm font-semibold">Email ownership</p>
              <p className="mt-2 text-sm leading-6 text-slate-400">New accounts stay locked until the inbox verification link is opened.</p>
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
