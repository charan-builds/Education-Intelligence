"use client";

export const dynamic = "force-dynamic";

import React from "react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import RequireRole from "@/components/auth/RequireRole";
import RoleDashboardLayout from "@/components/layout/RoleDashboardLayout";
import MetricCard from "@/components/ui/MetricCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { useRealtime } from "@/components/providers/RealtimeProvider";
import { useAuth } from "@/hooks/useAuth";
import { useTenantScope } from "@/hooks/useTenantScope";
import {
  createDiscussionReply,
  createDiscussionThread,
  getBadges,
  getCommunities,
  getDiscussionReplies,
  getDiscussionThreads,
  joinCommunity,
} from "@/services/communityService";

export default function CommunityPage() {
  const queryClient = useQueryClient();
  const { role, user } = useAuth();
  const { subscribeCommunity, subscribeThread, sendTyping, typingByThread, activeUsers } = useRealtime();
  const { activeTenantScope, clearActiveTenantScope } = useTenantScope();
  const [selectedCommunityId, setSelectedCommunityId] = useState<number | null>(null);
  const [threadTitle, setThreadTitle] = useState("");
  const [threadBody, setThreadBody] = useState("");
  const [replyBody, setReplyBody] = useState("");
  const [selectedThreadId, setSelectedThreadId] = useState<number | null>(null);
  const [formMessage, setFormMessage] = useState("");

  const communitiesQuery = useQuery({
    queryKey: ["community-communities"],
    queryFn: () => getCommunities(),
  });

  const badgesQuery = useQuery({
    queryKey: ["community-badges"],
    queryFn: () => getBadges(),
  });

  const communities = useMemo(() => communitiesQuery.data?.items ?? [], [communitiesQuery.data?.items]);
  const selectedCommunity = useMemo(
    () => communities.find((community) => community.id === selectedCommunityId) ?? communities[0] ?? null,
    [communities, selectedCommunityId],
  );

  useEffect(() => {
    if (!selectedCommunityId && communities.length > 0) {
      setSelectedCommunityId(communities[0].id);
    }
  }, [communities, selectedCommunityId]);

  useEffect(() => {
    if (selectedCommunity?.id) {
      subscribeCommunity(selectedCommunity.id);
    }
  }, [selectedCommunity?.id, subscribeCommunity]);

  const threadsQuery = useQuery({
    queryKey: ["community-threads", selectedCommunity?.id],
    queryFn: () => getDiscussionThreads({ community_id: selectedCommunity?.id }),
    enabled: Boolean(selectedCommunity?.id),
  });

  useEffect(() => {
    const firstThreadId = threadsQuery.data?.items?.[0]?.id ?? null;
    if (selectedThreadId === null && firstThreadId !== null) {
      setSelectedThreadId(firstThreadId);
    }
  }, [selectedThreadId, threadsQuery.data?.items]);

  useEffect(() => {
    if (selectedThreadId !== null) {
      subscribeThread(selectedThreadId);
    }
  }, [selectedThreadId, subscribeThread]);

  const repliesQuery = useQuery({
    queryKey: ["community-replies", selectedThreadId],
    queryFn: () => getDiscussionReplies(selectedThreadId as number),
    enabled: selectedThreadId !== null,
  });

  const joinMutation = useMutation({
    mutationFn: joinCommunity,
    onSuccess: async () => {
      setFormMessage("Joined community successfully.");
      await queryClient.invalidateQueries({ queryKey: ["community-communities"] });
      await queryClient.invalidateQueries({ queryKey: ["community-threads"] });
    },
    onError: () => setFormMessage("Unable to join this community."),
  });

  const threadMutation = useMutation({
    mutationFn: createDiscussionThread,
    onSuccess: async () => {
      setFormMessage("Discussion thread posted.");
      setThreadTitle("");
      setThreadBody("");
      await queryClient.invalidateQueries({ queryKey: ["community-threads", selectedCommunity?.id] });
      await queryClient.invalidateQueries({ queryKey: ["community-communities"] });
    },
    onError: () => setFormMessage("Unable to create discussion thread."),
  });

  const replyMutation = useMutation({
    mutationFn: createDiscussionReply,
    onSuccess: async () => {
      setFormMessage("Reply posted.");
      setReplyBody("");
      await queryClient.invalidateQueries({ queryKey: ["community-replies", selectedThreadId] });
    },
    onError: () => setFormMessage("Unable to post reply."),
  });

  const canCreateThread = Boolean(
    selectedCommunity && (selectedCommunity.is_member || ["teacher", "admin", "super_admin"].includes(role ?? "")),
  );

  async function handleJoin(): Promise<void> {
    if (!selectedCommunity) {
      return;
    }
    setFormMessage("");
    await joinMutation.mutateAsync({ community_id: selectedCommunity.id });
  }

  async function handleCreateThread(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!selectedCommunity || !threadTitle.trim() || !threadBody.trim()) {
      return;
    }
    setFormMessage("");
    await threadMutation.mutateAsync({
      community_id: selectedCommunity.id,
      title: threadTitle.trim(),
      body: threadBody.trim(),
    });
  }

  async function handleCreateReply(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!selectedThreadId || !replyBody.trim()) {
      return;
    }
    setFormMessage("");
    await replyMutation.mutateAsync({
      thread_id: selectedThreadId,
      body: replyBody.trim(),
    });
  }

  return (
    <RequireRole allowedRoles={["student", "teacher", "admin", "super_admin"]}>
      <RoleDashboardLayout
        roleLabel="Community"
        title="Community Learning"
        description="Communities, memberships, discussions, and mentor badges are now loaded from the backend community APIs with tenant isolation."
        navItems={[
          { label: "Student Dashboard", href: "/dashboard/student" },
          { label: "Mentor", href: "/mentor" },
          { label: "Roadmap", href: "/roadmap/view" },
          { label: "Progress", href: "/progress" },
        ]}
      >
        <section className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
          <p className="font-semibold text-slate-900">Tenant Scope</p>
          <p>
            Communities and mentor badges are rendered for tenant {user?.tenant_id ?? "unknown"} only. Discussion
            threads inherit the current tenant from your authenticated session.
          </p>
          {user?.role === "super_admin" && activeTenantScope ? (
            <div className="mt-2 flex flex-wrap items-center gap-3">
              <p className="text-amber-800">
                Super-admin inspection mode is active. Community data is currently scoped to tenant #{activeTenantScope}.
              </p>
              <button
                type="button"
                onClick={clearActiveTenantScope}
                className="rounded-xl border border-amber-300 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-amber-800 hover:bg-amber-100"
              >
                Return to My Tenant
              </button>
            </div>
          ) : null}
        </section>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard title="Communities" value={communities.length} description="Live communities in the current tenant." tone="info" />
          <MetricCard
            title="Joined"
            value={communities.filter((community) => community.is_member).length}
            description="Communities the current user has joined."
            tone="success"
          />
          <MetricCard
            title="Threads"
            value={communities.reduce((sum, community) => sum + community.thread_count, 0)}
            description="Total discussion threads across visible communities."
            tone="warning"
          />
          <MetricCard
            title="Mentor Badges"
            value={badgesQuery.data?.items.length ?? 0}
            description="Recognition badges loaded from the backend."
          />
          <MetricCard title="Active Now" value={activeUsers} description="Live users connected to this tenant." tone="info" />
        </div>

        <div className="grid gap-6 xl:grid-cols-[1.05fr_1.35fr]">
          <SurfaceCard title="Communities" description="Topic communities are persisted in PostgreSQL and isolated per tenant.">
            {communitiesQuery.isLoading ? <p className="text-slate-600">Loading communities...</p> : null}
            {communitiesQuery.isError ? <p className="text-red-600">Failed to load communities.</p> : null}

            {!communitiesQuery.isLoading && !communitiesQuery.isError ? (
              communities.length === 0 ? (
                <p className="text-slate-600">No communities are available in this tenant yet.</p>
              ) : (
                <ul className="space-y-3">
                  {communities.map((community) => {
                    const active = community.id === selectedCommunity?.id;
                    return (
                      <li key={community.id}>
                        <button
                          type="button"
                          onClick={() => setSelectedCommunityId(community.id)}
                          className={[
                            "w-full rounded-2xl border p-4 text-left transition",
                            active ? "border-sky-400 bg-sky-50" : "border-slate-200 bg-white hover:border-slate-300",
                          ].join(" ")}
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div>
                              <p className="text-sm font-semibold text-slate-950">{community.name}</p>
                              <p className="mt-1 text-sm text-slate-600">{community.topic_name ?? `Topic ${community.topic_id}`}</p>
                            </div>
                            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                              {community.is_member ? "Joined" : "Open"}
                            </span>
                          </div>
                          <p className="mt-3 text-sm leading-7 text-slate-600">{community.description}</p>
                          <p className="mt-3 text-xs uppercase tracking-[0.18em] text-slate-500">
                            {community.member_count} members • {community.thread_count} threads
                          </p>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )
            ) : null}
          </SurfaceCard>

          <div className="space-y-6">
            <SurfaceCard
              title={selectedCommunity ? selectedCommunity.name : "Discussion Threads"}
              description="Threads are loaded from `/community/threads` for the selected community."
              actions={
                selectedCommunity && !selectedCommunity.is_member ? (
                  <button
                    type="button"
                    onClick={handleJoin}
                    disabled={joinMutation.isPending}
                    className="rounded-xl bg-sky-500 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-400 disabled:opacity-60"
                  >
                    {joinMutation.isPending ? "Joining..." : "Join Community"}
                  </button>
                ) : undefined
              }
            >
              {formMessage ? <p className="mb-4 text-sm text-sky-700">{formMessage}</p> : null}

              {threadsQuery.isLoading ? <p className="text-slate-600">Loading discussion threads...</p> : null}
              {threadsQuery.isError ? <p className="text-red-600">Failed to load discussion threads.</p> : null}

              {!threadsQuery.isLoading && !threadsQuery.isError ? (
                <div className="space-y-6">
                  <ul className="space-y-3">
                    {(threadsQuery.data?.items ?? []).length === 0 ? (
                      <li className="rounded-2xl border border-slate-200 px-4 py-4 text-sm text-slate-600">
                        No discussion threads yet for this community.
                      </li>
                    ) : (
                      (threadsQuery.data?.items ?? []).map((thread) => (
                        <li
                          key={thread.id}
                          className={[
                            "rounded-2xl border px-4 py-4",
                            selectedThreadId === thread.id ? "border-sky-300 bg-sky-50/50" : "border-slate-200",
                          ].join(" ")}
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div>
                              <button
                                type="button"
                                onClick={() => setSelectedThreadId(thread.id)}
                                className="text-left text-sm font-semibold text-slate-950 hover:text-sky-700"
                              >
                                {thread.title}
                              </button>
                              <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                                {thread.author_email ?? `User ${thread.author_user_id}`} • {new Date(thread.created_at).toLocaleString()}
                              </p>
                            </div>
                            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                              {thread.is_resolved ? "Resolved" : "Open"}
                            </span>
                          </div>
                          <p className="mt-3 text-sm leading-7 text-slate-700">{thread.body}</p>
                        </li>
                      ))
                    )}
                  </ul>

                  <form className="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4" onSubmit={handleCreateThread}>
                    <h3 className="text-sm font-semibold text-slate-950">Start a Discussion</h3>
                    <input
                      type="text"
                      value={threadTitle}
                      onChange={(event) => setThreadTitle(event.target.value)}
                      placeholder="Thread title"
                      disabled={!canCreateThread || threadMutation.isPending}
                      className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none ring-sky-500 focus:ring-2 disabled:bg-slate-100"
                    />
                    <textarea
                      value={threadBody}
                      onChange={(event) => setThreadBody(event.target.value)}
                      placeholder="Ask your question or share a learning insight..."
                      disabled={!canCreateThread || threadMutation.isPending}
                      rows={4}
                      className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none ring-sky-500 focus:ring-2 disabled:bg-slate-100"
                    />
                    <button
                      type="submit"
                      disabled={!canCreateThread || threadMutation.isPending}
                      className="rounded-xl bg-slate-950 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60"
                    >
                      {threadMutation.isPending ? "Posting..." : "Post Thread"}
                    </button>
                    {!canCreateThread ? (
                      <p className="text-xs text-slate-500">Join the community first, unless your role already has moderator-level posting rights.</p>
                    ) : null}
                  </form>

                  <div className="rounded-2xl border border-slate-200 bg-white p-4">
                    <h3 className="text-sm font-semibold text-slate-950">Replies</h3>
                    {selectedThreadId === null ? <p className="mt-3 text-sm text-slate-600">Select a thread to view replies.</p> : null}
                    {repliesQuery.isLoading ? <p className="mt-3 text-sm text-slate-600">Loading replies...</p> : null}
                    {repliesQuery.isError ? <p className="mt-3 text-sm text-red-600">Failed to load replies.</p> : null}
                    {!repliesQuery.isLoading && !repliesQuery.isError && selectedThreadId !== null ? (
                      <div className="mt-3 space-y-3">
                        {(repliesQuery.data?.items ?? []).length === 0 ? (
                          <p className="text-sm text-slate-600">No replies yet.</p>
                        ) : (
                          (repliesQuery.data?.items ?? []).map((reply) => (
                            <div key={reply.id} className="rounded-xl border border-slate-200 px-3 py-3">
                              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">
                                {reply.author_email ?? `User ${reply.author_user_id}`} • {new Date(reply.created_at).toLocaleString()}
                              </p>
                              <p className="mt-2 text-sm leading-7 text-slate-700">{reply.body}</p>
                            </div>
                          ))
                        )}

                        <form className="space-y-3" onSubmit={handleCreateReply}>
                          <textarea
                            value={replyBody}
                            onChange={(event) => {
                              setReplyBody(event.target.value);
                              if (selectedThreadId !== null) {
                                sendTyping(selectedThreadId);
                              }
                            }}
                            placeholder="Reply to this discussion..."
                            disabled={!canCreateThread || replyMutation.isPending || selectedThreadId === null}
                            rows={3}
                            className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none ring-sky-500 focus:ring-2 disabled:bg-slate-100"
                          />
                          {(typingByThread[selectedThreadId] ?? []).filter((id) => id !== user?.user_id).length > 0 ? (
                            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-700">Someone is typing...</p>
                          ) : null}
                          <button
                            type="submit"
                            disabled={!canCreateThread || replyMutation.isPending || selectedThreadId === null}
                            className="rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-500 disabled:opacity-60"
                          >
                            {replyMutation.isPending ? "Replying..." : "Post Reply"}
                          </button>
                        </form>
                      </div>
                    ) : null}
                  </div>
                </div>
              ) : null}
            </SurfaceCard>

            <SurfaceCard title="Mentor Badges" description="Badges are loaded from the backend and recognize mentor participation inside the tenant.">
              {badgesQuery.isLoading ? <p className="text-slate-600">Loading badges...</p> : null}
              {badgesQuery.isError ? <p className="text-red-600">Failed to load badges.</p> : null}

              {!badgesQuery.isLoading && !badgesQuery.isError ? (
                (badgesQuery.data?.items ?? []).length === 0 ? (
                  <p className="text-slate-600">No mentor badges have been awarded yet.</p>
                ) : (
                  <ul className="space-y-3">
                    {(badgesQuery.data?.items ?? []).map((badge) => (
                      <li key={badge.id} className="rounded-2xl border border-slate-200 px-4 py-4">
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <p className="text-sm font-semibold text-slate-950">{badge.user_email ?? `User ${badge.user_id}`}</p>
                            <p className="mt-1 text-sm text-slate-600">{badge.description}</p>
                          </div>
                          <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
                            {badge.name}
                          </span>
                        </div>
                      </li>
                    ))}
                  </ul>
                )
              ) : null}
            </SurfaceCard>
          </div>
        </div>
      </RoleDashboardLayout>
    </RequireRole>
  );
}
