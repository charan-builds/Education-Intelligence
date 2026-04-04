"use client";

import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import PageHeader from "@/components/layouts/PageHeader";
import TopicGraph from "@/components/TopicGraph";
import Button from "@/components/ui/Button";
import ErrorState from "@/components/ui/ErrorState";
import MetricCard from "@/components/ui/MetricCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { useToast } from "@/components/providers/ToastProvider";
import { useAuth } from "@/hooks/useAuth";
import { normalizeRoadmapStatus } from "@/hooks/useDashboard";
import { getUserRoadmap, updateRoadmapStep } from "@/services/roadmapService";
import { getTopic, getTopicKnowledgeGraph, getTopicReasoning } from "@/services/topicService";

function difficultyLabel(level: number): string {
  if (level <= 1) {
    return "easy";
  }
  if (level === 2) {
    return "medium";
  }
  return "hard";
}

export default function StudentTopicPage() {
  const params = useParams<{ topicId: string }>();
  const topicId = Number(params.topicId);
  const { user, role } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const topicQuery = useQuery({
    queryKey: ["student", "topic", topicId],
    queryFn: () => getTopic(topicId),
    enabled: Number.isFinite(topicId) && topicId > 0,
  });

  const roadmapQuery = useQuery({
    queryKey: ["student", "topic", "roadmap", user?.user_id],
    queryFn: async () => {
      if (!user?.user_id) {
        throw new Error("Missing user id");
      }
      return getUserRoadmap(user.user_id);
    },
    enabled: Boolean(user?.user_id),
  });

  const graphQuery = useQuery({
    queryKey: ["student", "topic", "graph"],
    queryFn: getTopicKnowledgeGraph,
  });

  const reasoningQuery = useQuery({
    queryKey: ["student", "topic", "reasoning", topicId],
    queryFn: () => getTopicReasoning(topicId),
    enabled: Number.isFinite(topicId) && topicId > 0,
  });

  const roadmapStep = roadmapQuery.data?.items?.[0]?.steps.find((step) => step.topic_id === topicId) ?? null;

  const updateMutation = useMutation({
    mutationFn: (progressStatus: "in_progress" | "completed") =>
      updateRoadmapStep(roadmapStep!.id, { progress_status: progressStatus }),
    onSuccess: async () => {
      toast({
        title: "Progress synced",
        description: "This topic status has been updated on your roadmap.",
        variant: "success",
      });
      if (user?.user_id) {
        await queryClient.invalidateQueries({ queryKey: ["student", "topic", "roadmap", user.user_id] });
        await queryClient.invalidateQueries({ queryKey: ["dashboard", "student", "roadmap", user.user_id] });
      }
    },
  });

  if (!Number.isFinite(topicId) || topicId <= 0) {
    return <ErrorState description="A valid topic ID is required to render this learning page." />;
  }

  if (topicQuery.isError) {
    return <ErrorState description="The topic API did not return content for this topic." />;
  }

  const topic = topicQuery.data;
  const status = roadmapStep ? normalizeRoadmapStatus(roadmapStep.progress_status) : null;
  const graph = graphQuery.data;
  const reasoning = reasoningQuery.data;
  const weakTopicIds = (reasoning?.missing_foundations ?? []).map((item) => item.topic_id);
  const highlightedPathIds = (reasoning?.shortest_learning_path ?? []).map((item) => item.topic_id);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={role === "independent_learner" ? "Independent learner topic" : "Topic learning"}
        title={topic?.name ?? `Topic ${topicId}`}
        description={
          topic?.description ??
          (role === "independent_learner"
            ? "Loading detailed topic content and knowledge-graph reasoning for your personal workspace."
            : "Loading detailed topic content from the backend.")
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard title="Examples" value={topic?.examples.length ?? 0} tone="info" />
        <MetricCard title="Practice prompts" value={topic?.practice_questions.length ?? 0} tone="success" />
        <MetricCard title="Roadmap status" value={status ? status.replace("_", " ") : "Not tracked"} tone="warning" />
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard
          title="Readiness"
          value={reasoning ? `${Math.round(reasoning.readiness_percent)}%` : "..." }
          description="Confidence that foundations are in place for this topic."
          tone="default"
        />
        <MetricCard
          title="Dependencies"
          value={reasoning?.dependency_resolution.length ?? 0}
          description="Concepts the engine connects to this topic."
          tone="default"
        />
        <MetricCard
          title="Missing foundations"
          value={reasoning?.missing_foundations.length ?? 0}
          description="Prerequisites still below the mastery threshold."
          tone="warning"
        />
        <MetricCard
          title="Similarity cluster"
          value={reasoning?.clusters[0] ?? "General"}
          description="Semantic neighborhood for related topics and skills."
          tone="success"
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <SurfaceCard title="Explanation" description="Topic narrative and worked examples returned from `/topics/{topicId}`.">
          <div className="space-y-3">
            {(topic?.examples ?? []).map((example, index) => (
              <div
                key={`${example}-${index}`}
                className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 text-sm leading-7 text-slate-700 dark:border-slate-700 dark:bg-slate-900/70 dark:text-slate-300"
              >
                {example}
              </div>
            ))}
          </div>
        </SurfaceCard>

        <SurfaceCard title="Practice questions" description="Use these prompts as focused reinforcement after studying the concept.">
          <div className="space-y-3">
            {(topic?.practice_questions ?? []).map((question) => (
              <div
                key={question.id}
                className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70"
              >
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{question.question_text}</p>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                    {difficultyLabel(question.difficulty)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </SurfaceCard>
      </div>

      <SurfaceCard
        title="Knowledge graph"
        description="The platform now reasons over prerequisite structure, topic-skill mappings, and your current mastery state."
      >
        {graph ? (
          <TopicGraph
            topics={graph.nodes}
            prerequisites={graph.edges}
            weakTopicIds={weakTopicIds}
            highlightedPathIds={highlightedPathIds}
            focusTopicId={topicId}
            heightClassName="h-[620px]"
          />
        ) : (
          <p className="text-sm text-slate-600 dark:text-slate-400">Building graph snapshot...</p>
        )}
      </SurfaceCard>

      <div className="grid gap-6 xl:grid-cols-3">
        <SurfaceCard title="Shortest path" description="Fastest foundation-first route inferred from the prerequisite graph.">
          <div className="space-y-3">
            {(reasoning?.shortest_learning_path ?? []).map((item, index) => (
              <div key={`${item.topic_id}-${index}`} className="rounded-2xl border border-emerald-200 bg-emerald-50/80 px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-emerald-950">{item.topic_name}</p>
                  <span className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700">
                    {item.mastery_score != null ? `${Math.round(item.mastery_score)}%` : item.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </SurfaceCard>

        <SurfaceCard title="Knowledge gaps" description="Missing and inferred foundations the engine believes are blocking fluency.">
          <div className="space-y-3">
            {[...(reasoning?.missing_foundations ?? []), ...(reasoning?.inferred_missing_topics ?? [])]
              .filter((item, index, array) => array.findIndex((candidate) => candidate.topic_id === item.topic_id) === index)
              .map((item) => (
                <div key={item.topic_id} className="rounded-2xl border border-rose-200 bg-rose-50/80 px-4 py-3">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-rose-950">{item.topic_name}</p>
                    <span className="text-xs font-semibold uppercase tracking-[0.18em] text-rose-700">
                      {item.mastery_score != null ? `${Math.round(item.mastery_score)}%` : item.status}
                    </span>
                  </div>
                </div>
              ))}
            {reasoning && reasoning.missing_foundations.length === 0 && reasoning.inferred_missing_topics.length === 0 ? (
              <p className="text-sm leading-7 text-slate-600 dark:text-slate-400">
                Foundations look solid. The graph does not detect blocking gaps for this topic.
              </p>
            ) : null}
          </div>
        </SurfaceCard>

        <SurfaceCard title="Suggested next moves" description="Career-aware topic adjacency and semantic similarity drive these recommendations.">
          <div className="space-y-3">
            {(reasoning?.recommended_next_topics ?? []).map((item) => (
              <div key={item.topic_id} className="rounded-2xl border border-sky-200 bg-sky-50/80 px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-sky-950">{item.topic_name}</p>
                  <span className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-700">
                    {Math.round(item.readiness_percent)}% ready
                  </span>
                </div>
                <p className="mt-2 text-sm leading-6 text-sky-900/80">{item.reason}</p>
              </div>
            ))}
          </div>
        </SurfaceCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <SurfaceCard title="Dependency chain" description="Ordered prerequisite resolution for this topic.">
          <div className="space-y-3">
            {(reasoning?.dependency_resolution ?? []).map((item) => (
              <div key={item.topic_id} className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{item.topic_name}</p>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                    {item.mastery_score != null ? `${Math.round(item.mastery_score)}%` : item.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </SurfaceCard>

        <SurfaceCard title="Similar topics" description="Semantic similarity from descriptions and shared skill mappings.">
          <div className="space-y-3">
            {(reasoning?.similar_topics ?? []).map((item) => (
              <div key={item.topic_id} className="rounded-2xl border border-indigo-200 bg-indigo-50/80 px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-indigo-950">{item.topic_name}</p>
                    <p className="mt-1 text-xs uppercase tracking-[0.18em] text-indigo-700">{item.cluster}</p>
                  </div>
                  <span className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-700">
                    {Math.round(item.similarity_percent)}% similar
                  </span>
                </div>
              </div>
            ))}
          </div>
        </SurfaceCard>
      </div>

      {roadmapStep ? (
        <SurfaceCard
          title="Roadmap control"
          description="Update this topic directly on your learner roadmap."
          actions={
            <>
              {status === "pending" ? (
                <Button onClick={() => updateMutation.mutate("in_progress")} disabled={updateMutation.isPending}>
                  Start topic
                </Button>
              ) : null}
              {status !== "completed" ? (
                <Button onClick={() => updateMutation.mutate("completed")} disabled={updateMutation.isPending} variant="secondary">
                  Mark complete
                </Button>
              ) : null}
            </>
          }
        >
          <p className="text-sm leading-7 text-slate-600 dark:text-slate-400">
            Current status: <span className="font-semibold capitalize text-slate-900 dark:text-slate-100">{status?.replace("_", " ")}</span>
          </p>
        </SurfaceCard>
      ) : null}
    </div>
  );
}
