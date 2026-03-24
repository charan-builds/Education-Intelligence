import { beforeEach, describe, expect, it, vi } from "vitest";

const postMock = vi.fn();
const jwtDecodeMock = vi.fn();

vi.mock("@/services/apiClient", () => ({
  apiClient: {
    post: postMock,
  },
}));

vi.mock("jwt-decode", () => ({
  jwtDecode: jwtDecodeMock,
}));

describe("authService", () => {
  beforeEach(() => {
    postMock.mockReset();
    jwtDecodeMock.mockReset();
    localStorage.clear();
    document.cookie = "access_token=; Path=/; Max-Age=0";
  });

  it("stores access token in localStorage and cookie on login", async () => {
    postMock.mockResolvedValue({ data: { access_token: "header.payload.signature" } });
    const { login } = await import("@/services/authService");

    const result = await login("student@example.com", "password");

    expect(result.access_token).toBe("header.payload.signature");
    expect(localStorage.getItem("access_token")).toBe("header.payload.signature");
    expect(document.cookie).toContain("access_token=header.payload.signature");
  });

  it("decodes current user from stored token", async () => {
    localStorage.setItem("access_token", "header.payload.signature");
    jwtDecodeMock.mockReturnValue({ sub: "5", tenant_id: 7, role: "student" });
    const { getCurrentUser } = await import("@/services/authService");

    expect(getCurrentUser()).toEqual({ sub: "5", tenant_id: 7, role: "student" });
  });
});
