import { beforeEach, describe, expect, it, vi } from "vitest";

const patchMock = vi.fn();

vi.mock("@/services/apiClient", () => ({
  apiClient: {
    patch: patchMock,
  },
}));

describe("roadmapService", () => {
  beforeEach(() => {
    patchMock.mockReset();
  });

  it("updates a roadmap step successfully", async () => {
    patchMock.mockResolvedValue({
      data: {
        id: 9,
        topic_id: 101,
        estimated_time_hours: 4,
        difficulty: "medium",
        priority: 1,
        deadline: "2026-03-14T00:00:00Z",
        progress_status: "completed",
      },
    });

    const { updateRoadmapStep } = await import("@/services/roadmapService");
    const result = await updateRoadmapStep(9, { progress_status: "completed" });

    expect(patchMock).toHaveBeenCalledWith("/roadmap/steps/9", { progress_status: "completed" });
    expect(result.progress_status).toBe("completed");
  });

  it("propagates forbidden and not found API errors", async () => {
    const forbidden = Object.assign(new Error("Forbidden"), { response: { status: 403 } });
    patchMock.mockRejectedValueOnce(forbidden);

    const { updateRoadmapStep } = await import("@/services/roadmapService");
    await expect(updateRoadmapStep(9, { progress_status: "completed" })).rejects.toMatchObject({
      response: { status: 403 },
    });

    const notFound = Object.assign(new Error("Not Found"), { response: { status: 404 } });
    patchMock.mockRejectedValueOnce(notFound);
    await expect(updateRoadmapStep(999, { progress_status: "completed" })).rejects.toMatchObject({
      response: { status: 404 },
    });
  });
});
