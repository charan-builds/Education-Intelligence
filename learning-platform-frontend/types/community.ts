export type Community = {
  id: number;
  tenant_id: number;
  topic_id: number;
  name: string;
  description: string;
  created_at: string;
  topic_name?: string | null;
  member_count: number;
  thread_count: number;
  is_member: boolean;
};

export type CommunityMember = {
  id: number;
  tenant_id: number;
  community_id: number;
  user_id: number;
  role: string;
  joined_at: string;
  user_email?: string | null;
};

export type DiscussionThread = {
  id: number;
  tenant_id: number;
  community_id: number;
  author_user_id: number;
  title: string;
  body: string;
  is_resolved: boolean;
  created_at: string;
  author_email?: string | null;
  community_name?: string | null;
};

export type DiscussionReply = {
  id: number;
  tenant_id: number;
  thread_id: number;
  author_user_id: number;
  body: string;
  created_at: string;
  author_email?: string | null;
};

export type Badge = {
  id: number;
  tenant_id: number;
  user_id: number;
  name: string;
  description: string;
  awarded_for: string;
  awarded_at: string;
  user_email?: string | null;
};

export type PageMeta = {
  total: number;
  limit: number;
  offset: number;
  next_offset: number | null;
  next_cursor: string | null;
};

export type CommunityPageResponse = {
  items: Community[];
  meta: PageMeta;
};

export type CommunityMemberPageResponse = {
  items: CommunityMember[];
  meta: PageMeta;
};

export type DiscussionThreadPageResponse = {
  items: DiscussionThread[];
  meta: PageMeta;
};

export type DiscussionReplyPageResponse = {
  items: DiscussionReply[];
  meta: PageMeta;
};

export type BadgePageResponse = {
  items: Badge[];
  meta: PageMeta;
};

export type CreateCommunityPayload = {
  topic_id: number;
  name: string;
  description: string;
};

export type CommunityQuery = {
  topic_id?: number;
  limit?: number;
  offset?: number;
};

export type JoinCommunityPayload = {
  community_id: number;
};

export type CreateDiscussionThreadPayload = {
  community_id: number;
  title: string;
  body: string;
};

export type ResolveDiscussionThreadPayload = {
  is_resolved: boolean;
};

export type CreateDiscussionReplyPayload = {
  thread_id: number;
  body: string;
};

export type CreateBadgePayload = {
  user_id: number;
  name: string;
  description: string;
  awarded_for: string;
};

export type BadgeQuery = {
  user_id?: number;
  limit?: number;
  offset?: number;
};

export type ThreadQuery = {
  community_id?: number;
  limit?: number;
  offset?: number;
};
