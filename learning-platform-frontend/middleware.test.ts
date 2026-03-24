import { describe, expect, it } from "vitest";
import { NextRequest } from "next/server";

import { middleware } from "@/middleware";

function createToken(payload: Record<string, unknown>): string {
  const encoded = Buffer.from(JSON.stringify(payload)).toString("base64url");
  return `header.${encoded}.signature`;
}

describe("middleware", () => {
  it("redirects unauthenticated protected requests to auth", () => {
    const request = new NextRequest("http://localhost:3000/student/dashboard");
    const response = middleware(request);

    expect(response?.status).toBe(307);
    expect(response?.headers.get("location")).toContain("/auth");
  });

  it("redirects users away from dashboards outside their role", () => {
    const token = createToken({ role: "student", exp: Math.floor(Date.now() / 1000) + 3600 });
    const request = new NextRequest("http://localhost:3000/admin/dashboard", {
      headers: { cookie: `access_token=${token}` },
    });
    const response = middleware(request);

    expect(response?.status).toBe(307);
    expect(response?.headers.get("location")).toContain("/student/dashboard");
  });
});
