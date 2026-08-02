"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import ResultDashboard from "@/components/diagnostic/ResultDashboard";
import { getDiagnosticResult } from "@/services/diagnosticService";
import { getTopics } from "@/services/topicService";
import { useAuth } from "@/hooks/useAuth";

export default function StudentDiagnosticResultPage() {
  const { role } = useAuth();
  const [testId, setTestId] = useState<number>(NaN);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const testIdParam = params.get("test_id");
    setTestId(testIdParam ? Number(testIdParam) : NaN);
  }, []);

  const resultQuery = useQuery({
    queryKey: ["diagnostic-result", testId],
    queryFn: () => getDiagnosticResult(testId),
    enabled: Number.isFinite(testId) && testId > 0,
  });

  const topicsQuery = useQuery({
    queryKey: ["diagnostic-result", "topics"],
    queryFn: getTopics,
    enabled: resultQuery.isSuccess,
  });

  if (!Number.isFinite(testId) || testId <= 0) {
    return (
      <div className="min-h-screen bg-[linear-gradient(180deg,#020617_0%,#0f172a_36%,#111827_100%)] px-4 py-10 text-slate-100">
        <div className="mx-auto max-w-5xl rounded-[32px] border border-slate-800 bg-[#111827] p-8">
          Missing diagnostic test reference.
        </div>
      </div>
    );
  }

  if (resultQuery.isLoading || topicsQuery.isLoading) {
    return (
      <div className="min-h-screen bg-[linear-gradient(180deg,#020617_0%,#0f172a_36%,#111827_100%)] px-4 py-10 text-slate-100">
        <div className="mx-auto max-w-5xl rounded-[32px] border border-slate-800 bg-[#111827] p-8">
          Preparing post-test analysis...
        </div>
      </div>
    );
  }

  if (resultQuery.isError || !resultQuery.data) {
    return (
      <div className="min-h-screen bg-[linear-gradient(180deg,#020617_0%,#0f172a_36%,#111827_100%)] px-4 py-10 text-slate-100">
        <div className="mx-auto max-w-5xl rounded-[32px] border border-slate-800 bg-[#111827] p-8">
          Unable to load diagnostic results.
        </div>
      </div>
    );
  }

  return <ResultDashboard result={resultQuery.data} topics={topicsQuery.data?.items ?? []} role={role} />;
}
