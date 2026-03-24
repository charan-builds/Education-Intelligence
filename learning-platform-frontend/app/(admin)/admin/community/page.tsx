"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import PageHeader from "@/components/layouts/PageHeader";
import { useToast } from "@/components/providers/ToastProvider";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { createCommunity, getCommunities, getDiscussionThreads, resolveDiscussionThread } from "@/services/communityService";
import { getTopics } from "@/services/topicService";

export default function AdminCommunityPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [topicId, setTopicId] = useState("1");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const topicsQuery = useQuery({
    queryKey: ["admin", "community", "topics"],
    queryFn: getTopics,
  });
  const communitiesQuery = useQuery({
    queryKey: ["admin", "community", "communities"],
    queryFn: () => getCommunities({ limit: 10, offset: 0 }),
  });
  const threadsQuery = useQuery({
    queryKey: ["admin", "community", "threads"],
    queryFn: () => getDiscussionThreads({ limit: 10, offset: 0 }),
  });

  const createMutation = useMutation({
    mutationFn: createCommunity,
    onSuccess: async () => {
      setName("");
      setDescription("");
      toast({ title: "Community created", variant: "success" });
      await queryClient.invalidateQueries({ queryKey: ["admin", "community", "communities"] });
    },
  });

  const resolveMutation = useMutation({
    mutationFn: (threadId: number) => resolveDiscussionThread(threadId, { is_resolved: true }),
    onSuccess: async () => {
      toast({ title: "Thread resolved", variant: "success" });
      await queryClient.invalidateQueries({ queryKey: ["admin", "community", "threads"] });
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Admin"
        title="Community moderation"
        description="Create topic communities and resolve discussion threads from the moderation cockpit."
      />

      <div className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
        <SurfaceCard title="Create community" description="Use a topic anchor plus a short description.">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              createMutation.mutate({ topic_id: Number(topicId), name, description });
            }}
          >
            <Select value={topicId} onChange={(event) => setTopicId(event.target.value)}>
              {(topicsQuery.data?.items ?? []).map((topic) => (
                <option key={topic.id} value={topic.id}>
                  {topic.name}
                </option>
              ))}
            </Select>
            <Input value={name} onChange={(event) => setName(event.target.value)} placeholder="Community name" required />
            <Input value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Description" required />
            <Button type="submit">Create</Button>
          </form>
        </SurfaceCard>

        <SurfaceCard title="Communities" description="Tenant communities and thread counts from the community API.">
          <div className="space-y-3">
            {(communitiesQuery.data?.items ?? []).map((community) => (
              <div
                key={community.id}
                className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70"
              >
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{community.name}</p>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                  {community.member_count} members • {community.thread_count} threads
                </p>
              </div>
            ))}
          </div>
        </SurfaceCard>
      </div>

      <SurfaceCard title="Thread moderation" description="Resolve active threads without leaving the workspace.">
        <div className="space-y-3">
          {(threadsQuery.data?.items ?? []).map((thread) => (
            <div
              key={thread.id}
              className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{thread.title}</p>
                  <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{thread.body}</p>
                </div>
                {!thread.is_resolved ? (
                  <Button
                    variant="secondary"
                    onClick={() => resolveMutation.mutate(thread.id)}
                    disabled={resolveMutation.isPending}
                  >
                    Resolve
                  </Button>
                ) : (
                  <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200">
                    Resolved
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </SurfaceCard>
    </div>
  );
}
