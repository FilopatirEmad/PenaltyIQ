"""
JWT Handler — PenaltyIQ Backend
=================================
Creates and validates HS256 JWT tokens using python-jose.

Token payload structure:
    {
        "sub": "<user_id>",      # subject (user ID as string)
        "role": "user"|"admin",
        "exp": <unix_timestamp>   # auto-set by create_access_token
    }
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from dataclasses import dataclass

from jose import JWTError, jwt

from config import settings

logger = logging.getLogger("penaltyiq.jwt_handler")


@dataclass
class TokenData:
    user_id: int
    role: str


def create_access_token(user_id: int, role: str) -> str:
    """
    Create a signed JWT access token.

    Parameters
    ----------
    user_id : int
        Database user ID (stored in 'sub' claim).
    role : str
        User role string stored in 'role' claim.

    Returns
    -------
    str — compact JWT string
    """
    expire = datetime.now(tz=timezone.utc) + timedelta(
        minutes=settings.jwt_expire_minutes
    )
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
    }
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    logger.debug(f"JWT issued for user_id={user_id}, role={role}, exp={expire}")
    return token


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Decode and validate a JWT token.

    Returns TokenData on success, None if the token is invalid or expired.
    Callers must treat None as an authentication failure.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        user_id_str: str = payload.get("sub")
        role: str = payload.get("role", "user")
        if user_id_str is None:
            return None
        return TokenData(user_id=int(user_id_str), role=role)
    except JWTError as e:
        logger.debug(f"JWT decode failed: {e}")
        return None
