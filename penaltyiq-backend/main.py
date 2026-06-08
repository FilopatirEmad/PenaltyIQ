"""
PenaltyIQ Backend — FastAPI Application
========================================
Entry point. Registers routes, configures CORS, wires middleware,
global error handlers, rate limiter, and JWT auth.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from config import settings
from core.rate_limiter import limiter
from db.user_store import init_db
from api.routes.auth_routes import router as auth_router
from api.routes.calibration_routes import router as calibration_router
from api.routes.analysis_routes import router as analysis_router
from api.routes.video_routes import router as video_router

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("penaltyiq")

APP_VERSION = "1.1.0"


# ─── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info(f"PenaltyIQ API v{APP_VERSION} starting …")
    settings.log_startup()
    init_db()                  # create SQLite users table if not exists
    yield
    # ── Shutdown ─────────────────────────────────────────────────────────────
    logger.info("PenaltyIQ API shutting down.")


# ─── Application Factory ──────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="PenaltyIQ API",
        description=(
            "Physics-Based Biomechanical Coaching Engine for Soccer Penalty Kicks. "
            "Implements: Static Calibration Gate, 2nd-Order Butterworth LPF (6Hz), "
            "Inverse Projectile Physics, Constrained IK Solver (SciPy SLSQP), "
            "and Digital Twin verification. "
            "Scientific basis: Winter (2009), Arguz et al. (2021), FIFA (2024)."
        ),
        version=APP_VERSION,
        lifespan=lifespan,
        # Hide schema routes in production if needed
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── Rate limiter ────────────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ── CORS ─────────────────────────────────────────────────────────────────
    raw_origins = settings.allowed_origins
    origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
    use_credentials = raw_origins.strip() != "*"

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins else ["*"],
        allow_credentials=use_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # ── Global exception handlers ────────────────────────────────────────────

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception(
            f"Unhandled exception on {request.method} {request.url.path}: {exc}"
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "An unexpected internal error occurred. "
                         "The team has been notified.",
                "data": None,
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": str(exc),
                "data": None,
            },
        )

    # ── Routes ───────────────────────────────────────────────────────────────
    app.include_router(auth_router)                                          # /auth/*
    app.include_router(calibration_router, prefix="/api/v1", tags=["Calibration"])
    app.include_router(analysis_router,    prefix="/api/v1", tags=["Analysis"])
    app.include_router(video_router,       prefix="/api/v1", tags=["Video"])

    # ── Health ───────────────────────────────────────────────────────────────
    @app.get("/health", tags=["System"], include_in_schema=True)
    async def health_check():
        """
        GET /health

        Public health-check used by load balancers, Flutter connectivity check,
        and Docker health probes.
        """
        return {
            "status": "ok",
            "service": f"PenaltyIQ API v{APP_VERSION}",
            "auth_required": settings.require_auth,
        }

    return app


app = create_app()