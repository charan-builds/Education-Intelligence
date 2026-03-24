import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { ACCESS_TOKEN_KEY } from "@/utils/authToken";
import { getRoleRedirectPath, roleHasAccess } from "@/utils/roleRedirect";

const PROTECTED_PREFIXES = [
  "/student",
  "/teacher",
  "/admin",
  "/super-admin",
  "/mentor",
];

const ROLE_RULES: Array<{ prefix: string; roles: string[] }> = [
  { prefix: "/student", roles: ["student"] },
  { prefix: "/teacher", roles: ["teacher", "mentor", "admin", "super_admin"] },
  { prefix: "/admin", roles: ["admin", "super_admin"] },
  { prefix: "/super-admin", roles: ["super_admin"] },
  { prefix: "/mentor", roles: ["student", "teacher", "mentor", "admin", "super_admin"] },
];

function decodeTokenPayload(token: string): Record<string, unknown> | null {
  const parts = token.split(".");
  if (parts.length < 2) {
    return null;
  }
  try {
    const payload = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const normalized = payload.padEnd(Math.ceil(payload.length / 4) * 4, "=");
    const json = atob(normalized);
    return JSON.parse(json) as Record<string, unknown>;
  } catch {
    return null;
  }
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isProtected = PROTECTED_PREFIXES.some((prefix) => pathname.startsWith(prefix));
  if (!isProtected) {
    return NextResponse.next();
  }

  const token = request.cookies.get(ACCESS_TOKEN_KEY)?.value;
  if (!token) {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = "/auth";
    redirectUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(redirectUrl);
  }

  const payload = decodeTokenPayload(token);
  const role = typeof payload?.role === "string" ? payload.role : null;
  const exp = typeof payload?.exp === "number" ? payload.exp : null;

  if (!payload || !role || (exp !== null && Date.now() >= exp * 1000)) {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = "/auth";
    redirectUrl.searchParams.set("next", pathname);
    const response = NextResponse.redirect(redirectUrl);
    response.cookies.delete(ACCESS_TOKEN_KEY);
    return response;
  }

  const rule = ROLE_RULES.find((candidate) => pathname.startsWith(candidate.prefix));

  if (rule && !roleHasAccess(role, rule.roles)) {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = getRoleRedirectPath(role);
    redirectUrl.search = "";
    return NextResponse.redirect(redirectUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/student/:path*",
    "/teacher/:path*",
    "/admin/:path*",
    "/super-admin/:path*",
    "/mentor/:path*",
  ],
};
