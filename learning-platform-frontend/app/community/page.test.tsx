import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import CommunityPage from "@/app/community/page";

const {
  joinCommunityMock,
  createDiscussionThreadMock,
  createDiscussionReplyMock,
  getCommunitiesMock,
  getDiscussionRepliesMock,
  getDiscussionThreadsMock,
  getBadgesMock,
} = vi.hoisted(() => ({
  joinCommunityMock: vi.fn().mockResolvedValue({
    id: 9,
    tenant_id: 5,
    community_id: 7,
    user_id: 4,
    role: "student",
    joined_at: "2026-03-14T00:00:00Z",
    user_email: "student@example.com",
  }),
  createDiscussionThreadMock: vi.fn().mockResolvedValue({
    id: 11,
    tenant_id: 5,
    community_id: 7,
    author_user_id: 4,
    title: "Need help with gradients",
    body: "How should I practice this topic?",
    is_resolved: false,
    created_at: "2026-03-14T00:00:00Z",
    author_email: "student@example.com",
    community_name: "ML Community",
  }),
  createDiscussionReplyMock: vi.fn().mockResolvedValue({
    id: 13,
    tenant_id: 5,
    thread_id: 5,
    author_user_id: 4,
    body: "Start with one practice set and review mistakes.",
    created_at: "2026-03-14T00:00:00Z",
    author_email: "teacher@example.com",
  }),
  getCommunitiesMock: vi.fn().mockResolvedValue({
    items: [{ id: 7, tenant_id: 5, topic_id: 1, name: "ML Community", description: "Peer discussion", created_at: "2026-03-14T00:00:00Z", topic_name: "Machine Learning", member_count: 4, thread_count: 2, is_member: false }],
  }),
  getDiscussionThreadsMock: vi.fn().mockResolvedValue({
    items: [{ id: 5, tenant_id: 5, community_id: 7, author_user_id: 3, title: "Existing thread", body: "What should I study first?", is_resolved: false, created_at: "2026-03-14T00:00:00Z", author_email: "learner@example.com", community_name: "ML Community" }],
  }),
  getDiscussionRepliesMock: vi.fn().mockResolvedValue({
    items: [{ id: 12, tenant_id: 5, thread_id: 5, author_user_id: 2, body: "Break the topic into smaller study blocks.", created_at: "2026-03-14T00:00:00Z", author_email: "mentor@example.com" }],
  }),
  getBadgesMock: vi.fn().mockResolvedValue({
    items: [{ id: 3, tenant_id: 5, user_id: 2, name: "Top Mentor", description: "Great mentor", awarded_for: "mentorship", awarded_at: "2026-03-14T00:00:00Z", user_email: "teacher@example.com" }],
  }),
}));

vi.mock("@/components/auth/RequireRole", () => ({
  default: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({
    user: { user_id: 4, tenant_id: 5, role: "teacher" },
    isAuthenticated: true,
    isReady: true,
    role: "teacher",
    logout: vi.fn(),
  }),
}));

vi.mock("@/components/providers/RealtimeProvider", () => ({
  useRealtime: () => ({
    subscribeCommunity: vi.fn(),
    subscribeThread: vi.fn(),
    sendTyping: vi.fn(),
    typingByThread: {},
    activeUsers: 0,
  }),
}));

vi.mock("@/hooks/useTenantScope", () => ({
  useTenantScope: () => ({
    activeTenantScope: null,
    clearActiveTenantScope: vi.fn(),
  }),
}));

vi.mock("@/services/communityService", () => ({
  getCommunities: getCommunitiesMock,
  getBadges: getBadgesMock,
  getDiscussionThreads: getDiscussionThreadsMock,
  getDiscussionReplies: getDiscussionRepliesMock,
  joinCommunity: joinCommunityMock,
  createDiscussionThread: createDiscussionThreadMock,
  createDiscussionReply: createDiscussionReplyMock,
}));

describe("CommunityPage", () => {
  it("supports joining communities and posting a discussion thread", async () => {
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <CommunityPage />
      </QueryClientProvider>,
    );

    await waitFor(() => expect(screen.getByRole("button", { name: /ML Community/i })).toBeInTheDocument());
    expect(screen.getByText("Tenant Scope")).toBeInTheDocument();
    expect(screen.getByText(/tenant 5 only/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Join Community" }));
    await waitFor(() => expect(joinCommunityMock).toHaveBeenCalled());
    expect(joinCommunityMock.mock.calls[0]?.[0]).toEqual({ community_id: 7 });

    fireEvent.change(screen.getByPlaceholderText("Thread title"), {
      target: { value: "Need help with gradients" },
    });
    fireEvent.change(screen.getByPlaceholderText("Ask your question or share a learning insight..."), {
      target: { value: "How should I practice this topic?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Post Thread" }));

    await waitFor(() => expect(createDiscussionThreadMock).toHaveBeenCalled());
    expect(createDiscussionThreadMock.mock.calls[0]?.[0]).toEqual({
      community_id: 7,
      title: "Need help with gradients",
      body: "How should I practice this topic?",
    });
  });
});
