import { redirect } from "next/navigation";

import { buildAuthPath } from "@/utils/appRoutes";

type RegisterPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function RegisterPage({ searchParams }: RegisterPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const nextParam = Array.isArray(resolvedSearchParams.next) ? resolvedSearchParams.next[0] : resolvedSearchParams.next;
  redirect(buildAuthPath("register", typeof nextParam === "string" ? nextParam : null));
}
