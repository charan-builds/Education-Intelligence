from __future__ import annotations

import secrets

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import get_settings
from app.core.security import (
    ACCESS_TOKEN_COOKIE_NAME,
    AuthenticationError,
    decode_access_token,
    get_token_from_headers_and_cookies,
)


def _build_content_security_policy() -> str:
    settings = get_settings()
    origins = [origin.strip().rstrip("/") for origin in settings.cors_origins.split(",") if origin.strip()]
    connect_sources = {"'self'"}
    for origin in origins:
        connect_sources.add(origin)
        if origin.startswith("https://"):
            connect_sources.add("wss://" + origin.removeprefix("https://"))
        elif origin.startswith("http://"):
            connect_sources.add("ws://" + origin.removeprefix("http://"))

    directives = {
        "default-src": ["'self'"],
        "base-uri": ["'self'"],
        "frame-ancestors": ["'none'"],
        "object-src": ["'none'"],
        "img-src": ["'self'", "data:", "blob:"],
        "style-src": ["'self'", "'unsafe-inline'"],
        "script-src": ["'self'", "'unsafe-inline'"],
        "font-src": ["'self'", "data:"],
        "connect-src": sorted(connect_sources),
        "form-action": ["'self'"],
    }
    return "; ".join(f"{name} {' '.join(values)}" for name, values in directives.items()) + ";"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-site"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = _build_content_security_policy()
        return response


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        csrf_cookie = request.cookies.get(settings.csrf_cookie_name)
        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.cookies.get(ACCESS_TOKEN_COOKIE_NAME):
            csrf_header = request.headers.get(settings.csrf_header_name)
            if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
                from starlette.responses import JSONResponse

                return JSONResponse({"detail": "CSRF validation failed"}, status_code=403)
        response = await call_next(request)
        if not csrf_cookie:
            response.set_cookie(
                key=settings.csrf_cookie_name,
                value=secrets.token_urlsafe(32),
                httponly=False,
                secure=settings.auth_cookie_secure,
                samesite=settings.auth_cookie_samesite,
                path="/",
                domain=settings.auth_cookie_domain,
            )
        return response


class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        actor_tenant_id = settings.default_tenant_id
        tenant_id = settings.default_tenant_id

        token = get_token_from_headers_and_cookies(
            request.headers,
            request.cookies,
            cookie_name=ACCESS_TOKEN_COOKIE_NAME,
        )
        if token:
            try:
                payload = decode_access_token(token)
                token_tenant_id = payload.get("tenant_id")
                token_role = payload.get("role")
                if token_tenant_id is not None:
                    actor_tenant_id = int(token_tenant_id)
                    tenant_id = actor_tenant_id
                raw_tenant_id = request.headers.get("X-Tenant-ID")
                if raw_tenant_id is not None and token_role == "super_admin":
                    tenant_id = int(raw_tenant_id)
            except (AuthenticationError, TypeError, ValueError):
                actor_tenant_id = settings.default_tenant_id
                tenant_id = settings.default_tenant_id

        request.state.actor_tenant_id = actor_tenant_id
        request.state.tenant_id = tenant_id
        return await call_next(request)


def register_security_middleware(app: FastAPI) -> None:
    settings = get_settings()
    origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    if not origins:
        origins = ["http://localhost:3000"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TenantContextMiddleware)
    app.add_middleware(CSRFMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
