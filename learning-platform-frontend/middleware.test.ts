import { describe, expect, it } from "vitest";
import { NextRequest } from "next/server";

import { middleware } from "@/middleware";

describe("middleware", () => {
  it("redirects unauthenticated protected requests to login", () => {
    const request = new NextRequest("http://localhost:3000/student/dashboard");
    const response = middleware(request);

    expect(response?.status).toBe(307);
    expect(response?.headers.get("location")).toContain("/login");
  });

  it("allows protected requests when an auth cookie is present", () => {
    const request = new NextRequest("http://localhost:3000/admin/dashboard", {
      headers: { cookie: "access_token=session-cookie" },
    });
    const response = middleware(request);

    expect(response?.status).toBe(200);
  });

  it("redirects legacy routes to canonical role paths", () => {
    const request = new NextRequest("http://localhost:3000/dashboard/student");
    const response = middleware(request);

    expect(response?.status).toBe(307);
    expect(response?.headers.get("location")).toContain("/student/dashboard");
  });
});
