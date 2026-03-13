"use client";

import { useHealthCheck } from "@/hooks/use-health-check";

export default function DashboardShell() {
  const { data, isLoading, isError } = useHealthCheck();

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-6 py-10">
      <h1 className="text-3xl font-semibold tracking-tight">Learning Platform Frontend</h1>
      <p className="mt-2 text-slate-600">Next.js App Router + TypeScript + Tailwind + React Query</p>

      <section className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-medium">Backend Connectivity</h2>
        {isLoading && <p className="mt-3 text-slate-500">Checking API...</p>}
        {isError && <p className="mt-3 text-red-600">API unavailable</p>}
        {data && (
          <p className="mt-3 text-emerald-700">
            API OK: <span className="font-medium">{data.message}</span>
          </p>
        )}
      </section>
    </main>
  );
}
