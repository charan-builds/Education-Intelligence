import { describe, expect, it, vi } from "vitest";

const { redirectMock } = vi.hoisted(() => ({
  redirectMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  redirect: redirectMock,
}));

import TopicLearningPage from "@/app/topic/[topicId]/page";

describe("TopicLearningPage", () => {
  it("redirects the legacy topic route to the new student topic workspace", async () => {
    await TopicLearningPage({ params: Promise.resolve({ topicId: "12" }) });
    expect(redirectMock).toHaveBeenCalledWith("/student/topics/12");
  });
});
