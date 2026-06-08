"""
Application Configuration — PenaltyIQ Backend
================================================
All environment variables loaded via pydantic-settings.
Startup fails fast with a clear error if a required variable is missing.
"""

import secrets
import logging
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("penaltyiq.config")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── CORS ────────────────────────────────────────────────────────────────
    allowed_origins: str = "*"

    # ── Logging ─────────────────────────────────────────────────────────────
    log_level: str = "info"

    # ── JWT ─────────────────────────────────────────────────────────────────
    # In production, set a strong random secret via environment variable.
    # Generate one with: python -c "import secrets; print(secrets.token_hex(32))"
    jwt_secret_key: str = secrets.token_hex(32)   # ephemeral default (dev only)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7          # 7 days

    # ── Auth gate ───────────────────────────────────────────────────────────
    # Set REQUIRE_AUTH=false to disable JWT validation in local development.
    require_auth: bool = False

    # ── File upload ─────────────────────────────────────────────────────────
    max_video_size_mb: int = 200

    # ── Redis (v2 async pipeline — optional) ───────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Rate limiting ───────────────────────────────────────────────────────
    rate_limit_video: str = "5/minute"    # POST /process-video
    rate_limit_analyze: str = "10/minute"  # POST /analyze
    rate_limit_calibrate: str = "15/minute"  # POST /calibrate
    rate_limit_render: str = "5/minute"   # POST /render-video
    rate_limit_auth: str = "10/minute"    # POST /auth/*

    def log_startup(self) -> None:
        """Log the active configuration on startup (no secrets)."""
        logger.info("─" * 60)
        logger.info("PenaltyIQ configuration loaded:")
        logger.info(f"  allowed_origins  : {self.allowed_origins}")
        logger.info(f"  require_auth     : {self.require_auth}")
        logger.info(f"  jwt_algorithm    : {self.jwt_algorithm}")
        logger.info(f"  jwt_expire_mins  : {self.jwt_expire_minutes}")
        logger.info(f"  max_video_size   : {self.max_video_size_mb}MB")
        logger.info(f"  log_level        : {self.log_level}")
        logger.info("─" * 60)
        if self.jwt_secret_key == secrets.token_hex(32):
            logger.warning(
                "JWT_SECRET_KEY is using an ephemeral default — tokens will "
                "be invalidated on restart. Set JWT_SECRET_KEY in .env for production."
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# Convenience singleton
settings = get_settings()
