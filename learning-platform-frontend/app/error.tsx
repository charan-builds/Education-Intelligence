"use client";

import { useEffect } from "react";

import Button from "@/components/ui/Button";
import ErrorState from "@/components/ui/ErrorState";
import { appRoutes } from "@/utils/appRoutes";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="mx-auto max-w-4xl px-6 py-12">
      <ErrorState
        title="Application error"
        description="The page crashed while rendering. You can retry immediately or return to the dashboard root."
      />
      <div className="mt-4 flex gap-3">
        <Button onClick={reset}>Retry</Button>
        <Button variant="secondary" onClick={() => window.location.assign(appRoutes.workspaceHome)}>
          Go to sign in
        </Button>
        <Button variant="ghost" onClick={() => window.location.assign(appRoutes.marketingHome)}>
          Open landing page
        </Button>
      </div>
    </main>
  );
}
