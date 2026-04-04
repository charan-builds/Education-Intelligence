import Link from "next/link";

import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import { appRoutes } from "@/utils/appRoutes";

export default function NotFoundPage() {
  return (
    <main className="mx-auto max-w-4xl px-6 py-12">
      <EmptyState
        title="This page doesn't exist"
        description="The route may have moved as part of the new role-based workspace structure."
      />
      <div className="mt-4 flex justify-center gap-3">
        <Link href={appRoutes.workspaceHome}>
          <Button>Return home</Button>
        </Link>
        <Link href={appRoutes.marketingHome}>
          <Button variant="secondary">Open landing page</Button>
        </Link>
      </div>
    </main>
  );
}
