"use client";

import { useEffect } from "react";

import Button from "@/components/ui/Button";
import ErrorState from "@/components/ui/ErrorState";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // eslint-disable-next-line no-console
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
        <Button variant="secondary" onClick={() => window.location.assign("/")}>
          Go home
        </Button>
      </div>
    </main>
  );
}
