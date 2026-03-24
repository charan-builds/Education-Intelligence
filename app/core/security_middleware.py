from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import get_settings
from app.core.security import AuthenticationError, decode_access_token


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src * data: blob: 'unsafe-inline' 'unsafe-eval';"
        return response


class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        tenant_id = settings.default_tenant_id

        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()
            try:
                payload = decode_access_token(token)
                token_tenant_id = payload.get("tenant_id")
                token_role = payload.get("role")
                if token_tenant_id is not None:
                    tenant_id = int(token_tenant_id)
                raw_tenant_id = request.headers.get("X-Tenant-ID")
                if raw_tenant_id is not None and token_role == "super_admin":
                    tenant_id = int(raw_tenant_id)
            except (AuthenticationError, TypeError, ValueError):
                tenant_id = settings.default_tenant_id

        raw_tenant_id = request.headers.get("X-Tenant-ID")
        try:
            if raw_tenant_id is not None and auth_header == "":
                tenant_id = int(raw_tenant_id)
        except ValueError:
            tenant_id = tenant_id or settings.default_tenant_id
        request.state.actor_tenant_id = tenant_id
        request.state.tenant_id = tenant_id
        return await call_next(request)


def register_security_middleware(app: FastAPI) -> None:
    settings = get_settings()
    origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    if not origins:
        origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TenantContextMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
