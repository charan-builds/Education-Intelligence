"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useToast } from "@/components/providers/ToastProvider";
import { getApiErrorMessage } from "@/lib/api";
import type { CreateCommunityPayload } from "@/types/community";
import {
  createAdminCommunity,
  deleteAdminCommunity,
  getAdminCommunityBootstrap,
  getAdminCommunityThreads,
  resolveAdminDiscussionThread,
} from "@/features/community-admin/services/adminCommunityService";

export function useAdminCommunity() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [topicId, setTopicId] = useState("");
  const [selectedCommunityId, setSelectedCommunityId] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [deleteTargetId, setDeleteTargetId] = useState<number | null>(null);

  const bootstrapQuery = useQuery({
    queryKey: ["admin", "community", "bootstrap"],
    queryFn: getAdminCommunityBootstrap,
  });

  const threadsQuery = useQuery({
    queryKey: ["admin", "community", "threads", selectedCommunityId || "all"],
    queryFn: () => getAdminCommunityThreads(selectedCommunityId ? Number(selectedCommunityId) : undefined),
  });

  useEffect(() => {
    if (!topicId && bootstrapQuery.data?.topics.length) {
      setTopicId(String(bootstrapQuery.data.topics[0].id));
    }
  }, [topicId, bootstrapQuery.data]);

  const topics = bootstrapQuery.data?.topics ?? [];
  const communities = useMemo(() => bootstrapQuery.data?.communities ?? [], [bootstrapQuery.data]);

  async function invalidateCommunityQueries() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["admin", "community", "bootstrap"] }),
      queryClient.invalidateQueries({ queryKey: ["admin", "community", "threads"] }),
    ]);
  }

  const createMutation = useMutation({
    mutationFn: (payload: CreateCommunityPayload) => createAdminCommunity(payload),
    onSuccess: async () => {
      setName("");
      setDescription("");
      toast({ title: "Community created", variant: "success" });
      await invalidateCommunityQueries();
    },
    onError: (error) => {
      toast({
        title: "Unable to create community",
        description: getApiErrorMessage(error),
        variant: "error",
      });
    },
  });

  const resolveMutation = useMutation({
    mutationFn: (threadId: number) => resolveAdminDiscussionThread(threadId, { is_resolved: true }),
    onSuccess: async () => {
      toast({ title: "Thread resolved", variant: "success" });
      await queryClient.invalidateQueries({ queryKey: ["admin", "community", "threads"] });
    },
    onError: (error) => {
      toast({
        title: "Unable to resolve thread",
        description: getApiErrorMessage(error),
        variant: "error",
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAdminCommunity,
    onSuccess: async (_, communityId) => {
      if (selectedCommunityId === String(communityId)) {
        setSelectedCommunityId("");
      }
      setDeleteTargetId(null);
      toast({ title: "Community deleted", variant: "success" });
      await invalidateCommunityQueries();
    },
    onError: (error) => {
      toast({
        title: "Unable to delete community",
        description: getApiErrorMessage(error),
        variant: "error",
      });
    },
  });

  const createCommunity = () => {
    if (!topicId) {
      toast({ title: "Select a topic first", variant: "error" });
      return;
    }
    createMutation.mutate({ topic_id: Number(topicId), name, description });
  };

  const confirmDeleteCommunity = () => {
    if (deleteTargetId == null) {
      return;
    }
    deleteMutation.mutate(deleteTargetId);
  };

  return {
    topicId,
    setTopicId,
    selectedCommunityId,
    setSelectedCommunityId,
    name,
    setName,
    description,
    setDescription,
    deleteTargetId,
    setDeleteTargetId,
    topics,
    communities,
    threads: threadsQuery.data?.items ?? [],
    bootstrapQuery,
    threadsQuery,
    createMutation,
    resolveMutation,
    deleteMutation,
    createCommunity,
    confirmDeleteCommunity,
  };
}
