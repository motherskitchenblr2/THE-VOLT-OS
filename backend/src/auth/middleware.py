"""VOLT OS — Clerk Auth Middleware for all API routes."""
from fastapi import Request, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from src.auth.clerk import decode_token


class ClerkAuthMiddleware(BaseHTTPMiddleware):
    """JWT verification middleware for all routes except health and docs."""

    EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return await call_next(request)  # Allow anonymous for public routes

        token = auth_header.replace("Bearer ", "")
        try:
            payload = decode_token(token)
            request.state.user = {
                "id": payload.get("sub"),
                "email": payload.get("email"),
                "org_id": payload.get("org_id"),
                "org_role": payload.get("org_role"),
            }
        except Exception:
            pass  # Let individual routes handle auth requirements

        return await call_next(request)
