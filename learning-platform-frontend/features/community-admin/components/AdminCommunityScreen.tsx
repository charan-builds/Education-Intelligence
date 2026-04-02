"use client";

import PageHeader from "@/components/layouts/PageHeader";
import EmptyState from "@/components/ui/EmptyState";
import ErrorState from "@/components/ui/ErrorState";
import Skeleton from "@/components/ui/Skeleton";
import Button from "@/components/ui/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Modal } from "@/components/ui/modal";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import { useAdminCommunity } from "@/features/community-admin/hooks/useAdminCommunity";

function CommunityListSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 3 }).map((_, index) => (
        <div key={index} className="rounded-3xl border border-slate-200/70 p-4 dark:border-slate-700">
          <Skeleton className="h-5 w-40" />
          <Skeleton className="mt-3 h-4 w-full" />
          <Skeleton className="mt-2 h-4 w-3/4" />
          <div className="mt-4 flex gap-2">
            <Skeleton className="h-10 w-28" />
            <Skeleton className="h-10 w-24" />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function AdminCommunityScreen() {
  const community = useAdminCommunity();

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Admin"
        title="Community moderation"
        description="Create topic communities, watch moderation queues, and clean up stale discussion spaces from one workspace."
      />

      <div className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
        <Card>
          <CardHeader>
            <CardTitle>Create community</CardTitle>
            <CardDescription>Anchor a discussion space to a topic and publish it into the tenant community layer.</CardDescription>
          </CardHeader>
          <CardContent>
            <form
              className="space-y-4"
              onSubmit={(event) => {
                event.preventDefault();
                community.createCommunity();
              }}
            >
              <Select
                value={community.topicId}
                onChange={(event) => community.setTopicId(event.target.value)}
                disabled={community.bootstrapQuery.isLoading || !community.topics.length}
              >
                {!community.topics.length ? <option value="">No topics available</option> : null}
                {community.topics.map((topic) => (
                  <option key={topic.id} value={topic.id}>
                    {topic.name}
                  </option>
                ))}
              </Select>
              <Input
                value={community.name}
                onChange={(event) => community.setName(event.target.value)}
                placeholder="Community name"
                required
              />
              <Input
                value={community.description}
                onChange={(event) => community.setDescription(event.target.value)}
                placeholder="Description"
                required
              />
              {community.bootstrapQuery.isError ? (
                <ErrorState
                  title="Topics unavailable"
                  description="Topics could not be loaded for community creation."
                  onRetry={() => void community.bootstrapQuery.refetch()}
                />
              ) : null}
              <Button
                type="submit"
                disabled={community.createMutation.isPending || community.bootstrapQuery.isLoading || !community.topicId}
              >
                {community.createMutation.isPending ? "Creating..." : "Create community"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Communities</CardTitle>
            <CardDescription>Moderate tenant communities, filter the thread queue, and remove unused spaces.</CardDescription>
          </CardHeader>
          <CardContent>
            {community.bootstrapQuery.isLoading ? <CommunityListSkeleton /> : null}
            {community.bootstrapQuery.isError ? (
              <ErrorState
                description="Communities could not be loaded."
                onRetry={() => void community.bootstrapQuery.refetch()}
              />
            ) : null}
            {!community.bootstrapQuery.isLoading && !community.communities.length ? (
              <EmptyState
                title="No communities yet"
                description="Create the first tenant community from a topic to open discussion and moderation workflows."
              />
            ) : null}
            <div className="space-y-3">
              {community.communities.map((item) => {
                const isSelected = community.selectedCommunityId === String(item.id);
                return (
                  <div
                    key={item.id}
                    className={`rounded-3xl border px-4 py-4 transition ${
                      isSelected
                        ? "border-brand-400 bg-brand-50/80 dark:border-brand-400/50 dark:bg-brand-500/10"
                        : "border-slate-200 bg-white/70 dark:border-slate-700 dark:bg-slate-900/70"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{item.name}</p>
                        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{item.description}</p>
                        <p className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-400">
                          {item.member_count} members • {item.thread_count} threads • {item.topic_name ?? `Topic #${item.topic_id}`}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant={isSelected ? "primary" : "secondary"}
                          onClick={() => community.setSelectedCommunityId(isSelected ? "" : String(item.id))}
                        >
                          {isSelected ? "Viewing all" : "Filter threads"}
                        </Button>
                        <Button variant="danger" onClick={() => community.setDeleteTargetId(item.id)}>
                          Delete
                        </Button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Thread moderation</CardTitle>
          <CardDescription>Resolve open discussion items without leaving the admin workspace.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="mb-4 flex flex-wrap items-center gap-3">
            <Select value={community.selectedCommunityId} onChange={(event) => community.setSelectedCommunityId(event.target.value)}>
              <option value="">All communities</option>
              {community.communities.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </Select>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {community.selectedCommunityId
                ? "Showing threads for the selected community."
                : "Showing the latest moderation queue across all communities."}
            </p>
          </div>

          {community.threadsQuery.isLoading ? <CommunityListSkeleton /> : null}
          {community.threadsQuery.isError ? (
            <ErrorState
              description="Discussion threads could not be loaded."
              onRetry={() => void community.threadsQuery.refetch()}
            />
          ) : null}
          {!community.threadsQuery.isLoading && !community.threads.length ? (
            <EmptyState
              title="No moderation items"
              description="No discussion threads match the current filter right now."
            />
          ) : null}
          <div className="space-y-3">
            {community.threads.map((thread) => (
              <div
                key={thread.id}
                className="rounded-3xl border border-slate-200 bg-white/70 px-4 py-4 dark:border-slate-700 dark:bg-slate-900/70"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{thread.title}</p>
                    <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-400">
                      {thread.community_name ?? `Community #${thread.community_id}`} • {thread.author_email ?? `User #${thread.author_user_id}`}
                    </p>
                    <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{thread.body}</p>
                  </div>
                  {!thread.is_resolved ? (
                    <Button
                      variant="secondary"
                      onClick={() => community.resolveMutation.mutate(thread.id)}
                      disabled={community.resolveMutation.isPending}
                    >
                      {community.resolveMutation.isPending ? "Resolving..." : "Resolve"}
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
        </CardContent>
      </Card>

      <Modal
        open={community.deleteTargetId !== null}
        onClose={() => community.setDeleteTargetId(null)}
        title="Delete community"
        description="This removes the selected community from the tenant moderation surface."
        footer={
          <>
            <Button variant="ghost" onClick={() => community.setDeleteTargetId(null)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={community.confirmDeleteCommunity}
              disabled={community.deleteMutation.isPending}
            >
              {community.deleteMutation.isPending ? "Deleting..." : "Delete community"}
            </Button>
          </>
        }
      >
        <p className="text-sm leading-7 text-slate-600 dark:text-slate-400">
          This action is intended for cleanup and moderation. Make sure the discussion space is no longer needed before removing it.
        </p>
      </Modal>
    </div>
  );
}
