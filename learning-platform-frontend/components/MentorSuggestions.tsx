"use client";

import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/services/apiClient";

type MentorSuggestionsResponse = {
  suggestions: string[];
};

async function getMentorSuggestions(): Promise<MentorSuggestionsResponse> {
  const { data } = await apiClient.get<MentorSuggestionsResponse>("/mentor/suggestions");
  return data;
}

export default function MentorSuggestions() {
  const suggestionsQuery = useQuery({
    queryKey: ["mentor-suggestions"],
    queryFn: getMentorSuggestions,
    staleTime: 60_000,
  });

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Mentor Suggestions</h2>

      {suggestionsQuery.isLoading && <p className="mt-3 text-sm text-slate-600">Loading suggestions...</p>}
      {suggestionsQuery.isError && <p className="mt-3 text-sm text-red-600">Failed to load mentor suggestions.</p>}

      {!suggestionsQuery.isLoading && !suggestionsQuery.isError && (
        <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-700">
          {(suggestionsQuery.data?.suggestions ?? []).map((suggestion, index) => (
            <li key={`${index}-${suggestion}`}>{suggestion}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
