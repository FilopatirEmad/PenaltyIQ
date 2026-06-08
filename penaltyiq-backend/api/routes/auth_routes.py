"""
Auth Routes — POST /auth/register, POST /auth/login
=====================================================
Provides JWT-based registration and login.

Both endpoints are public (no authentication required).
All other /api/v1/* endpoints require a valid Bearer token
when REQUIRE_AUTH=true.
"""

import logging

from fastapi import APIRouter, HTTPException, Request, status

from api.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse, UserOut
from api.schemas.response import ok, err
from core.jwt_handler import create_access_token
from core.rate_limiter import limiter
from config import settings
from db.user_store import create_user, authenticate_user

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger("penaltyiq.routes.auth")


@router.post(
    "/register",
    summary="Register a new user account",
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(settings.rate_limit_auth)
async def register(request: Request, body: RegisterRequest):
    """
    POST /auth/register

    Create a new user account and return a JWT token.
    Password must be ≥ 8 chars, contain a letter and a digit.
    """
    try:
        user = create_user(
            name=body.name,
            email=body.email,
            password=body.password,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to an internal error.",
        )

    token = create_access_token(user_id=user.id, role=user.role)
    logger.info(f"New user registered: id={user.id}, email={user.email}")

    return ok(
        data=TokenResponse(
            token=token,
            user=UserOut(
                id=user.id,
                name=user.name,
                email=user.email,
                role=user.role,
            ),
        ).model_dump(),
        message="Account created successfully.",
    )


@router.post(
    "/login",
    summary="Log in and receive a JWT token",
    status_code=status.HTTP_200_OK,
)
@limiter.limit(settings.rate_limit_auth)
async def login(request: Request, body: LoginRequest):
    """
    POST /auth/login

    Authenticate with email and password.
    Returns a JWT Bearer token valid for 7 days.
    """
    user = authenticate_user(body.email, body.password)
    if user is None:
        # Identical error for wrong email and wrong password (prevent enumeration)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user_id=user.id, role=user.role)
    logger.info(f"User logged in: id={user.id}, email={user.email}")

    return ok(
        data=TokenResponse(
            token=token,
            user=UserOut(
                id=user.id,
                name=user.name,
                email=user.email,
                role=user.role,
            ),
        ).model_dump(),
        message="Login successful.",
    )


@router.get(
    "/me",
    summary="Get current user info",
    status_code=status.HTTP_200_OK,
)
async def me(request: Request):
    """
    GET /auth/me

    Returns current user info from the JWT token.
    Requires Authorization: Bearer <token>.
    """
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from core.jwt_handler import decode_access_token
    from db.user_store import get_user_by_id

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required.",
        )

    token_data = decode_access_token(auth_header.removeprefix("Bearer ").strip())
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    user = get_user_by_id(token_data.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return ok(
        data=UserOut(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
        ).model_dump()
    )
