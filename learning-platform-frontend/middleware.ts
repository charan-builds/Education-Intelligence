import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY } from "@/utils/authToken";
import { getRolePrefix, normalizeAppPath, sanitizeAuthRedirectTarget } from "@/utils/appRoutes";
import { canonicalizeRole, getRoleRedirectPath } from "@/utils/roleRedirect";

const PROTECTED_PREFIXES = [
  "/student",
  "/teacher",
  "/admin",
  "/super-admin",
  "/mentor",
  "/community",
  "/dashboard",
  "/goals",
  "/diagnostic",
  "/roadmap",
  "/progress",
];

const PUBLIC_ROUTES = ["/", "/login", "/register"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const normalizedPath = normalizeAppPath(pathname);

  if (normalizedPath !== pathname) {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = normalizedPath;
    return NextResponse.redirect(redirectUrl);
  }

  if ((pathname === "/login" || pathname === "/register") && request.nextUrl.searchParams.has("next")) {
    const sanitizedNext = sanitizeAuthRedirectTarget(request.nextUrl.searchParams.get("next"), pathname);
    if (!sanitizedNext) {
      const redirectUrl = request.nextUrl.clone();
      redirectUrl.searchParams.delete("next");
      return NextResponse.redirect(redirectUrl);
    }
  }

  if (PUBLIC_ROUTES.includes(pathname)) {
    return NextResponse.next();
  }

  const isProtected = PROTECTED_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
  if (!isProtected) {
    return NextResponse.next();
  }

  const accessToken = request.cookies.get(ACCESS_TOKEN_KEY)?.value;
  const refreshToken = request.cookies.get(REFRESH_TOKEN_KEY)?.value;
  if (!accessToken && !refreshToken) {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = "/login";
    redirectUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(redirectUrl);
  }

  const routeRole = getRolePrefix(pathname);
  const tokenRole = canonicalizeRole(extractRoleFromToken(accessToken ?? refreshToken));
  if (routeRole && tokenRole && routeRole !== tokenRole) {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = getRoleRedirectPath(tokenRole);
    return NextResponse.redirect(redirectUrl);
  }

  return NextResponse.next();
}

function extractRoleFromToken(token: string | undefined): string | null {
  if (!token || !token.includes(".")) {
    return null;
  }

  try {
    const payload = token.split(".")[1];
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
    const decoded = JSON.parse(atob(padded));
    return typeof decoded?.role === "string" ? decoded.role : null;
  } catch {
    return null;
  }
}

export const config = {
  matcher: ["/((?!_next|favicon.ico).*)"],
};
