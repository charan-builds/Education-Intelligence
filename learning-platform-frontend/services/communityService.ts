import { apiClient } from "@/services/apiClient";
import type {
  Badge,
  BadgePageResponse,
  BadgeQuery,
  Community,
  CommunityMember,
  CommunityMemberPageResponse,
  CommunityPageResponse,
  CommunityQuery,
  CreateCommunityPayload,
  CreateBadgePayload,
  CreateDiscussionReplyPayload,
  CreateDiscussionThreadPayload,
  DiscussionReply,
  DiscussionReplyPageResponse,
  DiscussionThread,
  DiscussionThreadPageResponse,
  JoinCommunityPayload,
  ResolveDiscussionThreadPayload,
  ThreadQuery,
} from "@/types/community";

export async function getCommunities(params?: CommunityQuery): Promise<CommunityPageResponse> {
  const { data } = await apiClient.get<CommunityPageResponse>("/community/communities", {
    params: {
      ...(params?.topic_id ? { topic_id: params.topic_id } : {}),
      ...(params?.limit ? { limit: params.limit } : {}),
      ...(params?.offset !== undefined ? { offset: params.offset } : {}),
    },
  });
  return data;
}

export async function createCommunity(payload: CreateCommunityPayload): Promise<Community> {
  const { data } = await apiClient.post<Community>("/community/communities", payload);
  return data;
}

export async function deleteCommunity(communityId: number): Promise<void> {
  await apiClient.delete(`/community/communities/${communityId}`);
}

export async function getCommunityMembers(community_id?: number): Promise<CommunityMemberPageResponse> {
  const { data } = await apiClient.get<CommunityMemberPageResponse>("/community/members", {
    params: community_id ? { community_id } : undefined,
  });
  return data;
}

export async function joinCommunity(payload: JoinCommunityPayload): Promise<CommunityMember> {
  const { data } = await apiClient.post<CommunityMember>("/community/members", payload);
  return data;
}

export async function getDiscussionThreads(params?: ThreadQuery): Promise<DiscussionThreadPageResponse> {
  const { data } = await apiClient.get<DiscussionThreadPageResponse>("/community/threads", {
    params: {
      ...(params?.community_id ? { community_id: params.community_id } : {}),
      ...(params?.limit ? { limit: params.limit } : {}),
      ...(params?.offset !== undefined ? { offset: params.offset } : {}),
    },
  });
  return data;
}

export async function createDiscussionThread(payload: CreateDiscussionThreadPayload): Promise<DiscussionThread> {
  const { data } = await apiClient.post<DiscussionThread>("/community/threads", payload);
  return data;
}

export async function getDiscussionReplies(thread_id: number): Promise<DiscussionReplyPageResponse> {
  const { data } = await apiClient.get<DiscussionReplyPageResponse>("/community/replies", {
    params: { thread_id },
  });
  return data;
}

export async function createDiscussionReply(payload: CreateDiscussionReplyPayload): Promise<DiscussionReply> {
  const { data } = await apiClient.post<DiscussionReply>("/community/replies", payload);
  return data;
}

export async function resolveDiscussionThread(
  threadId: number,
  payload: ResolveDiscussionThreadPayload,
): Promise<DiscussionThread> {
  const { data } = await apiClient.patch<DiscussionThread>(`/community/threads/${threadId}/resolve`, payload);
  return data;
}

export async function getBadges(params?: BadgeQuery): Promise<BadgePageResponse> {
  const { data } = await apiClient.get<BadgePageResponse>("/community/badges", {
    params: {
      ...(params?.user_id ? { user_id: params.user_id } : {}),
      ...(params?.limit ? { limit: params.limit } : {}),
      ...(params?.offset !== undefined ? { offset: params.offset } : {}),
    },
  });
  return data;
}

export async function createBadge(payload: CreateBadgePayload): Promise<Badge> {
  const { data } = await apiClient.post<Badge>("/community/badges", payload);
  return data;
}

export async function deleteBadge(badgeId: number): Promise<void> {
  await apiClient.delete(`/community/badges/${badgeId}`);
}
