import Link from "next/link";

import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";

export default function NotFoundPage() {
  return (
    <main className="mx-auto max-w-4xl px-6 py-12">
      <EmptyState
        title="This page doesn't exist"
        description="The route may have moved as part of the new role-based workspace structure."
      />
      <div className="mt-4 flex justify-center">
        <Link href="/">
          <Button>Return home</Button>
        </Link>
      </div>
    </main>
  );
}
