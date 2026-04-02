"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import PageHeader from "@/components/layouts/PageHeader";
import { useToast } from "@/components/providers/ToastProvider";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import SurfaceCard from "@/components/ui/SurfaceCard";
import {
  createCommunity,
  deleteCommunity,
  getCommunities,
  getDiscussionThreads,
  resolveDiscussionThread,
} from "@/services/communityService";
import { getTopics } from "@/services/topicService";

export default function AdminCommunityPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [topicId, setTopicId] = useState("");
  const [selectedCommunityId, setSelectedCommunityId] = useState("");
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
    queryKey: ["admin", "community", "threads", selectedCommunityId || "all"],
    queryFn: () =>
      getDiscussionThreads({
        limit: 10,
        offset: 0,
        community_id: selectedCommunityId ? Number(selectedCommunityId) : undefined,
      }),
  });

  useEffect(() => {
    if (!topicId && topicsQuery.data?.items?.length) {
      setTopicId(String(topicsQuery.data.items[0].id));
    }
  }, [topicId, topicsQuery.data]);

  const communityOptions = useMemo(
    () => communitiesQuery.data?.items ?? [],
    [communitiesQuery.data],
  );

  const createMutation = useMutation({
    mutationFn: createCommunity,
    onSuccess: async () => {
      setName("");
      setDescription("");
      toast({ title: "Community created", variant: "success" });
      await queryClient.invalidateQueries({ queryKey: ["admin", "community", "communities"] });
      await queryClient.invalidateQueries({ queryKey: ["admin", "community", "threads"] });
    },
    onError: (error: Error) => {
      toast({ title: "Unable to create community", description: error.message, variant: "error" });
    },
  });

  const resolveMutation = useMutation({
    mutationFn: (threadId: number) => resolveDiscussionThread(threadId, { is_resolved: true }),
    onSuccess: async () => {
      toast({ title: "Thread resolved", variant: "success" });
      await queryClient.invalidateQueries({ queryKey: ["admin", "community", "threads"] });
    },
    onError: (error: Error) => {
      toast({ title: "Unable to resolve thread", description: error.message, variant: "error" });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteCommunity,
    onSuccess: async (_, communityId) => {
      if (selectedCommunityId === String(communityId)) {
        setSelectedCommunityId("");
      }
      toast({ title: "Community deleted", variant: "success" });
      await queryClient.invalidateQueries({ queryKey: ["admin", "community", "communities"] });
      await queryClient.invalidateQueries({ queryKey: ["admin", "community", "threads"] });
    },
    onError: (error: Error) => {
      toast({ title: "Unable to delete community", description: error.message, variant: "error" });
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
              if (!topicId) {
                toast({ title: "Select a topic first", variant: "error" });
                return;
              }
              createMutation.mutate({ topic_id: Number(topicId), name, description });
            }}
          >
            <Select
              value={topicId}
              onChange={(event) => setTopicId(event.target.value)}
              disabled={topicsQuery.isLoading || !topicsQuery.data?.items?.length}
            >
              {!topicsQuery.data?.items?.length ? <option value="">No topics available</option> : null}
              {(topicsQuery.data?.items ?? []).map((topic) => (
                <option key={topic.id} value={topic.id}>
                  {topic.name}
                </option>
              ))}
            </Select>
            <Input value={name} onChange={(event) => setName(event.target.value)} placeholder="Community name" required />
            <Input value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Description" required />
            {topicsQuery.isError ? (
              <p className="text-sm text-rose-600 dark:text-rose-300">Topics could not be loaded for community creation.</p>
            ) : null}
            <Button type="submit" disabled={createMutation.isPending || topicsQuery.isLoading || !topicId}>
              {createMutation.isPending ? "Creating..." : "Create"}
            </Button>
          </form>
        </SurfaceCard>

        <SurfaceCard title="Communities" description="Tenant communities and thread counts from the community API.">
          <div className="space-y-3">
            {communitiesQuery.isLoading ? <p className="text-sm text-slate-500 dark:text-slate-400">Loading communities...</p> : null}
            {communitiesQuery.isError ? (
              <p className="text-sm text-rose-600 dark:text-rose-300">Communities could not be loaded.</p>
            ) : null}
            {!communitiesQuery.isLoading && !communityOptions.length ? (
              <p className="text-sm text-slate-500 dark:text-slate-400">No communities exist for this tenant yet.</p>
            ) : null}
            {communityOptions.map((community) => {
              const isSelected = selectedCommunityId === String(community.id);
              return (
                <div
                  key={community.id}
                  className={`rounded-2xl border px-4 py-3 transition ${
                    isSelected
                      ? "border-brand-400 bg-brand-50/80 dark:border-brand-400/50 dark:bg-brand-500/10"
                      : "border-slate-200 bg-white/70 dark:border-slate-700 dark:bg-slate-900/70"
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{community.name}</p>
                      <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{community.description}</p>
                      <p className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-400">
                        {community.member_count} members • {community.thread_count} threads
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant={isSelected ? "primary" : "secondary"}
                        onClick={() => setSelectedCommunityId(isSelected ? "" : String(community.id))}
                      >
                        {isSelected ? "Viewing all threads" : "Filter threads"}
                      </Button>
                      <Button
                        variant="ghost"
                        onClick={() => deleteMutation.mutate(community.id)}
                        disabled={deleteMutation.isPending}
                      >
                        {deleteMutation.isPending ? "Deleting..." : "Delete"}
                      </Button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </SurfaceCard>
      </div>

      <SurfaceCard title="Thread moderation" description="Resolve active threads without leaving the workspace.">
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <Select value={selectedCommunityId} onChange={(event) => setSelectedCommunityId(event.target.value)}>
            <option value="">All communities</option>
            {communityOptions.map((community) => (
              <option key={community.id} value={community.id}>
                {community.name}
              </option>
            ))}
          </Select>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {selectedCommunityId
              ? "Showing threads for the selected community."
              : "Showing the latest moderation queue across all communities."}
          </p>
        </div>
        <div className="space-y-3">
          {threadsQuery.isLoading ? <p className="text-sm text-slate-500 dark:text-slate-400">Loading discussion threads...</p> : null}
          {threadsQuery.isError ? (
            <p className="text-sm text-rose-600 dark:text-rose-300">Discussion threads could not be loaded.</p>
          ) : null}
          {!threadsQuery.isLoading && !(threadsQuery.data?.items?.length ?? 0) ? (
            <p className="text-sm text-slate-500 dark:text-slate-400">No discussion threads match this filter right now.</p>
          ) : null}
          {(threadsQuery.data?.items ?? []).map((thread) => (
            <div
              key={thread.id}
              className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{thread.title}</p>
                  <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-400">
                    {thread.community_name ?? `Community #${thread.community_id}`} • {thread.author_email ?? `User #${thread.author_user_id}`}
                  </p>
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
