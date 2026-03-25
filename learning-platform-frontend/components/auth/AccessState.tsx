"use client";

import Link from "next/link";

import Button from "@/components/ui/Button";
import ErrorState from "@/components/ui/ErrorState";
import Skeleton from "@/components/ui/Skeleton";

type AccessStateProps = {
  mode: "loading" | "redirecting" | "unauthorized";
  title?: string;
  description?: string;
  redirectHref?: string;
  redirectLabel?: string;
};

export default function AccessState({
  mode,
  title,
  description,
  redirectHref = "/auth",
  redirectLabel = "Open sign in",
}: AccessStateProps) {
  if (mode === "loading") {
    return (
      <main className="mx-auto min-h-screen max-w-5xl px-6 py-12">
        <div className="space-y-4">
          <Skeleton className="h-12 w-48" />
          <Skeleton className="h-40 w-full" />
          <Skeleton className="h-28 w-full" />
        </div>
      </main>
    );
  }

  if (mode === "unauthorized") {
    return (
      <main className="mx-auto min-h-screen max-w-4xl px-6 py-12">
        <ErrorState
          title={title ?? "You do not have access to this page"}
          description={description ?? "Your account is signed in, but this route belongs to a different workspace."}
        />
        <div className="mt-6">
          <Link href={redirectHref}>
            <Button>{redirectLabel}</Button>
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto min-h-screen max-w-4xl px-6 py-12 text-slate-600">
      {description ?? "Redirecting to the correct workspace..."}
    </main>
  );
}
