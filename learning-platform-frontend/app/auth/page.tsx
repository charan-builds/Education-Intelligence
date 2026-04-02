import AuthPageClient from "@/components/auth/AuthPageClient";

type AuthPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

type AuthMode = "login" | "register" | "invite" | "forgot-password" | "reset-password" | "email-verification";

function resolveAuthMode(rawMode: string | undefined): AuthMode {
  switch (rawMode) {
    case "register":
    case "invite":
    case "forgot-password":
    case "reset-password":
    case "email-verification":
      return rawMode;
    default:
      return "login";
  }
}

export default async function AuthPage({ searchParams }: AuthPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const modeParam = Array.isArray(resolvedSearchParams.mode) ? resolvedSearchParams.mode[0] : resolvedSearchParams.mode;
  return <AuthPageClient initialMode={resolveAuthMode(modeParam)} />;
}
