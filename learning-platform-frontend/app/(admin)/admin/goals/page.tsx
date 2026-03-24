"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import PageHeader from "@/components/layouts/PageHeader";
import { useToast } from "@/components/providers/ToastProvider";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { createGoal, createGoalTopic, deleteGoal, getGoals } from "@/services/goalService";
import { getTopics } from "@/services/topicService";

export default function AdminGoalsPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [goalId, setGoalId] = useState("1");
  const [topicId, setTopicId] = useState("1");

  const goalsQuery = useQuery({
    queryKey: ["admin", "goals"],
    queryFn: getGoals,
  });

  const topicsQuery = useQuery({
    queryKey: ["admin", "goal-topics", "topics"],
    queryFn: getTopics,
  });

  const createGoalMutation = useMutation({
    mutationFn: createGoal,
    onSuccess: async () => {
      setName("");
      setDescription("");
      toast({ title: "Goal created", variant: "success" });
      await queryClient.invalidateQueries({ queryKey: ["admin", "goals"] });
    },
  });

  const linkMutation = useMutation({
    mutationFn: ({ selectedGoalId, selectedTopicId }: { selectedGoalId: number; selectedTopicId: number }) =>
      createGoalTopic(selectedGoalId, selectedTopicId),
    onSuccess: () => toast({ title: "Goal mapped to topic", variant: "success" }),
  });

  const goals = useMemo(() => goalsQuery.data?.items ?? [], [goalsQuery.data?.items]);
  const topics = useMemo(() => topicsQuery.data?.items ?? [], [topicsQuery.data?.items]);
  const selectedGoalId = useMemo(() => Number(goalId || goals[0]?.id || 1), [goalId, goals]);
  const selectedTopicId = useMemo(() => Number(topicId || topics[0]?.id || 1), [topicId, topics]);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Admin"
        title="Goals management"
        description="Create tenant goals and map them to topics to support diagnostics and roadmap generation."
      />

      <div className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
        <SurfaceCard title="Create goal" description="This writes directly to the goals API.">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              createGoalMutation.mutate({ name, description });
            }}
          >
            <Input value={name} onChange={(event) => setName(event.target.value)} placeholder="Goal name" required />
            <Input value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Goal description" required />
            <Button type="submit">Create goal</Button>
          </form>
        </SurfaceCard>

        <SurfaceCard title="Goal inventory" description="Active goals returned by `/goals`.">
          <div className="space-y-3">
            {goals.map((goal) => (
              <div
                key={goal.id}
                className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{goal.name}</p>
                    <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{goal.description}</p>
                  </div>
                  <Button
                    variant="ghost"
                    className="h-auto px-3 py-2"
                    onClick={() => deleteGoal(goal.id).then(async () => {
                      toast({ title: "Goal deleted", variant: "success" });
                      await queryClient.invalidateQueries({ queryKey: ["admin", "goals"] });
                    })}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </SurfaceCard>
      </div>

      <SurfaceCard title="Map goal to topic" description="Create a goal-topic link for roadmap generation.">
        <div className="grid gap-4 md:grid-cols-[1fr_1fr_auto]">
          <Select value={goalId} onChange={(event) => setGoalId(event.target.value)}>
            {goals.map((goal) => (
              <option key={goal.id} value={goal.id}>
                {goal.name}
              </option>
            ))}
          </Select>
          <Select value={topicId} onChange={(event) => setTopicId(event.target.value)}>
            {topics.map((topic) => (
              <option key={topic.id} value={topic.id}>
                {topic.name}
              </option>
            ))}
          </Select>
          <Button onClick={() => linkMutation.mutate({ selectedGoalId, selectedTopicId })}>Create link</Button>
        </div>
      </SurfaceCard>
    </div>
  );
}
