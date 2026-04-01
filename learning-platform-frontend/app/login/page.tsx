import { redirect } from "next/navigation";

import { buildAuthPath } from "@/utils/appRoutes";

type LoginPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const nextParam = Array.isArray(resolvedSearchParams.next) ? resolvedSearchParams.next[0] : resolvedSearchParams.next;
  redirect(buildAuthPath("login", typeof nextParam === "string" ? nextParam : null));
}
