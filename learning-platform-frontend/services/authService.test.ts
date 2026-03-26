import { beforeEach, describe, expect, it, vi } from "vitest";

const postMock = vi.fn();
const getMock = vi.fn();

vi.mock("@/services/apiClient", () => ({
  apiClient: {
    post: postMock,
    get: getMock,
  },
}));

describe("authService", () => {
  beforeEach(() => {
    postMock.mockReset();
    getMock.mockReset();
    localStorage.clear();
  });

  it("returns the session payload from login", async () => {
    postMock.mockResolvedValue({
      data: {
        authenticated: true,
        token_type: "cookie",
        access_token_expires_in: 3600,
        refresh_token_expires_in: 86400,
        user: { id: 5, tenant_id: 7, email: "student@example.com", role: "student", created_at: "2026-03-24T00:00:00Z" },
      },
    });
    const { login } = await import("@/services/authService");

    const result = await login("student@example.com", "password", { tenant_id: 7 });

    expect(result.authenticated).toBe(true);
    expect(result.user.role).toBe("student");
    expect(postMock).toHaveBeenCalledWith("/auth/login", {
      email: "student@example.com",
      password: "password",
      tenant_id: 7,
      tenant_subdomain: undefined,
    });
  });

  it("loads current user from the backend session endpoint", async () => {
    getMock.mockResolvedValue({
      data: { id: 5, tenant_id: 7, email: "student@example.com", role: "student", created_at: "2026-03-24T00:00:00Z" },
    });
    const { getCurrentUser } = await import("@/services/authService");

    await expect(getCurrentUser()).resolves.toEqual({
      id: 5,
      tenant_id: 7,
      email: "student@example.com",
      role: "student",
      created_at: "2026-03-24T00:00:00Z",
    });
  });
});
