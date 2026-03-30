import { redirect } from "next/navigation";

import AuthPageClient from "@/components/auth/AuthPageClient";
import { sanitizeAuthRedirectTarget } from "@/utils/appRoutes";

type LoginPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const nextParam = Array.isArray(resolvedSearchParams.next) ? resolvedSearchParams.next[0] : resolvedSearchParams.next;

  if (typeof nextParam === "string" && sanitizeAuthRedirectTarget(nextParam, "/login") === null) {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(resolvedSearchParams)) {
      if (key === "next" || value == null) {
        continue;
      }
      if (Array.isArray(value)) {
        for (const item of value) {
          params.append(key, item);
        }
        continue;
      }
      params.set(key, value);
    }
    redirect(params.size > 0 ? `/login?${params.toString()}` : "/login");
  }

  return <AuthPageClient initialMode="login" />;
}
