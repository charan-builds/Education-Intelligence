import { beforeEach, describe, expect, it, vi } from "vitest";

const getMock = vi.fn();
const postMock = vi.fn();

vi.mock("@/services/apiClient", () => ({
  apiClient: {
    get: getMock,
    post: postMock,
  },
}));

describe("opsService", () => {
  beforeEach(() => {
    getMock.mockReset();
    postMock.mockReset();
  });

  it("loads feature flags with query params", async () => {
    getMock.mockResolvedValue({
      data: {
        items: [{ id: 1, tenant_id: 4, feature_name: "ai_mentor_enabled", enabled: true, created_at: "2026-01-01" }],
        meta: { limit: 50, offset: 0, returned: 1, total: 1, has_more: false, next_offset: null },
      },
    });

    const { getFeatureFlags } = await import("@/services/opsService");
    const result = await getFeatureFlags({ tenant_id: 4, limit: 50, offset: 0 });

    expect(getMock).toHaveBeenCalledWith("/ops/feature-flags", {
      params: { tenant_id: 4, limit: 50, offset: 0 },
    });
    expect(result.items[0].feature_name).toBe("ai_mentor_enabled");
  });

  it("updates a feature flag through the ops API", async () => {
    postMock.mockResolvedValue({
      data: {
        id: 2,
        tenant_id: 4,
        feature_name: "ml_recommendation_enabled",
        enabled: false,
        created_at: "2026-01-02",
      },
    });

    const { updateFeatureFlag } = await import("@/services/opsService");
    const result = await updateFeatureFlag("ml_recommendation_enabled", {
      enabled: false,
      tenant_id: 4,
    });

    expect(postMock).toHaveBeenCalledWith("/ops/feature-flags/ml_recommendation_enabled", {
      enabled: false,
      tenant_id: 4,
    });
    expect(result.enabled).toBe(false);
  });
});
