"""
API Key Authentication Middleware — PenaltyIQ Backend
======================================================
Simple API-key gate. All endpoints except /health, /docs, and /openapi.json
require a valid X-API-Key header.

Configuration:
    Set the API_KEYS environment variable as a comma-separated list:
        API_KEYS=flutter-prod-key,admin-key,dev-key-local

    In Flutter (Dart):
        headers: {"X-API-Key": "flutter-prod-key"}
"""

import os
import logging

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("penaltyiq.auth")

# Paths that do NOT require authentication
_PUBLIC_PATHS: frozenset[str] = frozenset({
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
})


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware that validates the X-API-Key header on every protected request.

    Keys are loaded from the API_KEYS environment variable at startup.
    An empty API_KEYS disables the gate entirely (development mode).
    """

    def __init__(self, app, api_keys: set[str] | None = None):
        super().__init__(app)
        if api_keys is not None:
            self._keys = api_keys
        else:
            raw = os.getenv("API_KEYS", "").strip()
            self._keys = {k.strip() for k in raw.split(",") if k.strip()}

        if not self._keys:
            logger.warning(
                "API_KEYS is not set — authentication middleware is DISABLED. "
                "Set API_KEYS in your .env file before deploying to production."
            )
        else:
            logger.info(f"API key middleware active: {len(self._keys)} key(s) registered.")

    async def dispatch(self, request: Request, call_next):
        # Always allow public paths (OPTIONS for CORS preflight, health, docs)
        if request.url.path in _PUBLIC_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        # Skip auth entirely if no keys are configured (dev mode)
        if not self._keys:
            return await call_next(request)

        key = request.headers.get("X-API-Key", "").strip()
        if not key or key not in self._keys:
            logger.warning(
                f"Rejected request to {request.url.path} — "
                f"invalid or missing X-API-Key"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key. Provide a valid X-API-Key header.",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        return await call_next(request)
