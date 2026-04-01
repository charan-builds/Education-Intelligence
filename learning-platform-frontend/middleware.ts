import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY } from "@/utils/authToken";
import { appRoutes, buildAuthPath, getRolePrefix, normalizeAppPath, sanitizeAuthRedirectTarget } from "@/utils/appRoutes";
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

const PUBLIC_ROUTES = ["/", appRoutes.auth, "/login", "/register"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname === "/auth/login" || pathname === "/auth/register") {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = appRoutes.auth;
    redirectUrl.searchParams.set("mode", pathname.endsWith("/register") ? "register" : "login");
    return NextResponse.redirect(redirectUrl);
  }

  const normalizedPath = normalizeAppPath(pathname);

  if (normalizedPath !== pathname) {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = normalizedPath;
    return NextResponse.redirect(redirectUrl);
  }

  if ((pathname === appRoutes.auth || pathname === "/login" || pathname === "/register") && request.nextUrl.searchParams.has("next")) {
    const sanitizedNext = sanitizeAuthRedirectTarget(request.nextUrl.searchParams.get("next"), pathname);
    if (!sanitizedNext) {
      const redirectUrl = request.nextUrl.clone();
      redirectUrl.searchParams.delete("next");
      return NextResponse.redirect(redirectUrl);
    }
  }

  if (pathname === "/login" || pathname === "/register") {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.href = new URL(
      buildAuthPath(pathname === "/register" ? "register" : "login", request.nextUrl.searchParams.get("next")),
      request.url,
    ).toString();
    return NextResponse.redirect(redirectUrl);
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
    // Workspace routes already enforce auth client-side via RequireAuth/RequireRole.
    // Avoid forcing a server-side redirect here because local token-first login flows
    // can complete before the cookie-backed middleware state is available.
    return NextResponse.next();
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
