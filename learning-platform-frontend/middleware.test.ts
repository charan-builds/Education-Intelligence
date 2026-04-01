import { describe, expect, it } from "vitest";
import { NextRequest } from "next/server";

import { middleware } from "@/middleware";

describe("middleware", () => {
  it("lets protected requests continue and relies on client auth guards when no auth cookie is present", () => {
    const request = new NextRequest("http://localhost:3000/student/dashboard");
    const response = middleware(request);

    expect(response?.status).toBe(200);
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

  it("redirects legacy login routes to canonical auth mode routes", () => {
    const request = new NextRequest("http://localhost:3000/login?next=/student/roadmap");
    const response = middleware(request);

    expect(response?.status).toBe(307);
    expect(response?.headers.get("location")).toContain("/auth?mode=login");
    expect(response?.headers.get("location")).toContain("next=%2Fstudent%2Froadmap");
  });
});
