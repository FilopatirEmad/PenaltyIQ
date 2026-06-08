"""
FastAPI Dependencies — PenaltyIQ Backend
==========================================
Re-usable Depends() callables injected into route handlers.

get_current_user:
    - Reads Authorization: Bearer <token> header.
    - Validates the JWT and returns a TokenData.
    - If REQUIRE_AUTH=false (dev mode), returns a default TokenData
      without validating any token.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import settings
from core.jwt_handler import decode_access_token, TokenData

logger = logging.getLogger("penaltyiq.dependencies")

_bearer_scheme = HTTPBearer(auto_error=False)

# Sentinel used in dev mode when auth is disabled
_DEV_USER = TokenData(user_id=0, role="user")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> TokenData:
    """
    Validate JWT bearer token and return the decoded TokenData.

    Behaviour:
        - REQUIRE_AUTH=false (default dev mode): always passes, returns
          a dummy TokenData(user_id=0, role="user").
        - REQUIRE_AUTH=true: requires a valid token; raises 401 otherwise.
    """
    if not settings.require_auth:
        return _DEV_USER

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide Authorization: Bearer <token>.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = decode_access_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_data


async def require_admin(
    current_user: TokenData = Depends(get_current_user),
) -> TokenData:
    """Dependency that additionally enforces admin role."""
    if not settings.require_auth:
        return current_user
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required for this operation.",
        )
    return current_user
