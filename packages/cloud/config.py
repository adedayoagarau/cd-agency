"""Cloud configuration loaded from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass(frozen=True)
class CloudConfig:
    """Centralised configuration for the cd-agency cloud layer.

    Every value is sourced from the corresponding environment variable with
    a sensible local-development default.
    """

    # Database
    database_url: str = ""
    redis_url: str = ""

    # Auth (Clerk)
    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""

    # Billing (Stripe)
    stripe_api_key: str = ""
    stripe_webhook_secret: str = ""

    # Security
    encryption_key: str = ""

    # CORS
    cors_origins: list[str] = field(default_factory=list)


def _load_config() -> CloudConfig:
    """Build a :class:`CloudConfig` from the current environment."""
    cors_raw = os.environ.get("CORS_ORIGINS", "http://localhost:3000")
    cors_origins = [o.strip() for o in cors_raw.split(",") if o.strip()]

    return CloudConfig(
        database_url=os.environ.get(
            "DATABASE_URL",
            "postgresql://cdagency:cdagency_dev@localhost:5432/cdagency",
        ),
        redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        clerk_secret_key=os.environ.get("CLERK_SECRET_KEY", ""),
        clerk_publishable_key=os.environ.get("CLERK_PUBLISHABLE_KEY", ""),
        stripe_api_key=os.environ.get("STRIPE_API_KEY", ""),
        stripe_webhook_secret=os.environ.get("STRIPE_WEBHOOK_SECRET", ""),
        encryption_key=os.environ.get("ENCRYPTION_KEY", "default-dev-key"),
        cors_origins=cors_origins,
    )


@lru_cache(maxsize=1)
def get_cloud_config() -> CloudConfig:
    """Return the cached :class:`CloudConfig` singleton."""
    return _load_config()
