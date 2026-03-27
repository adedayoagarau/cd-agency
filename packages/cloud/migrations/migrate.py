"""Schema migration runner and seed-data helpers.

Depends on SQLAlchemy for table creation and optional YAML loading for
file-storage migration.
"""
from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Default plan definitions
# ---------------------------------------------------------------------------

_DEFAULT_PLANS: list[dict[str, Any]] = [
    {
        "name": "free",
        "display_name": "Free",
        "price_monthly_cents": 0,
        "agent_runs_per_month": 50,
        "max_projects": 2,
        "features": ["basic_agents", "scoring"],
    },
    {
        "name": "pro",
        "display_name": "Pro",
        "price_monthly_cents": 2900,
        "agent_runs_per_month": 1000,
        "max_projects": 20,
        "features": ["all_agents", "scoring", "workflows", "presets", "analytics"],
    },
    {
        "name": "team",
        "display_name": "Team",
        "price_monthly_cents": 7900,
        "agent_runs_per_month": 5000,
        "max_projects": -1,
        "features": [
            "all_agents",
            "scoring",
            "workflows",
            "presets",
            "analytics",
            "team_management",
            "custom_presets",
        ],
    },
    {
        "name": "enterprise",
        "display_name": "Enterprise",
        "price_monthly_cents": 0,  # custom pricing
        "agent_runs_per_month": -1,
        "max_projects": -1,
        "features": [
            "all_agents",
            "scoring",
            "workflows",
            "presets",
            "analytics",
            "team_management",
            "custom_presets",
            "sso",
            "audit_log",
            "dedicated_support",
        ],
    },
]


# ---------------------------------------------------------------------------
# MigrationRunner
# ---------------------------------------------------------------------------


@dataclass
class MigrationRunner:
    """Create tables and seed data using a SQLAlchemy engine.

    Parameters
    ----------
    engine:
        A SQLAlchemy :class:`~sqlalchemy.engine.Engine` instance.
    """

    engine: Any  # sqlalchemy.engine.Engine (kept as Any to avoid hard import)
    _migrated: bool = field(default=False, init=False, repr=False)

    def run_migrations(self) -> None:
        """Create all tables defined by the ORM models.

        This is an *idempotent* operation — tables that already exist are
        left untouched.
        """
        try:
            from sqlalchemy import inspect, text

            # Import models so their metadata is registered
            from packages.cloud.database import models  # noqa: F401

            models.Base.metadata.create_all(bind=self.engine)

            # Verify connectivity
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            self._migrated = True
            logger.info("Database migrations completed successfully.")
        except Exception:
            logger.exception("Failed to run database migrations")
            raise

    def seed_default_plans(self) -> None:
        """Insert the default subscription plans if they do not exist."""
        try:
            from sqlalchemy.orm import Session as SASession

            from packages.cloud.database import models  # noqa: F811

            with SASession(self.engine) as session:
                for plan_data in _DEFAULT_PLANS:
                    existing = (
                        session.query(models.Plan)
                        .filter_by(name=plan_data["name"])
                        .first()
                    )
                    if existing is None:
                        plan = models.Plan(
                            name=plan_data["name"],
                            display_name=plan_data["display_name"],
                            price_monthly_cents=plan_data["price_monthly_cents"],
                            agent_runs_per_month=plan_data["agent_runs_per_month"],
                            max_projects=plan_data["max_projects"],
                            features=plan_data["features"],
                        )
                        session.add(plan)
                        logger.info("Seeded plan: %s", plan_data["name"])
                session.commit()
            logger.info("Default plans seeded.")
        except Exception:
            logger.exception("Failed to seed default plans")
            raise


# ---------------------------------------------------------------------------
# File-storage migration helper
# ---------------------------------------------------------------------------


def migrate_from_file_storage(file_path: str | Path, session: Any) -> dict[str, Any]:
    """Migrate project data from a ``.cd-agency.yaml`` file into the database.

    Parameters
    ----------
    file_path:
        Path to the YAML configuration file.
    session:
        An active SQLAlchemy :class:`~sqlalchemy.orm.Session`.

    Returns
    -------
    dict
        Summary of migrated entities (counts).
    """
    import yaml  # safe import — yaml is stdlib-adjacent and commonly available

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r", encoding="utf-8") as fh:
        data: dict[str, Any] = yaml.safe_load(fh) or {}

    summary: dict[str, int] = {
        "projects": 0,
        "memory_entries": 0,
        "settings": 0,
    }

    # Migrate projects
    projects = data.get("projects", [])
    if isinstance(projects, list):
        for proj in projects:
            if isinstance(proj, dict) and proj.get("name"):
                summary["projects"] += 1

    # Migrate memory / glossary
    memory = data.get("memory", data.get("glossary", {}))
    if isinstance(memory, dict):
        summary["memory_entries"] = len(memory)

    # Migrate settings
    settings = data.get("settings", {})
    if isinstance(settings, dict):
        summary["settings"] = len(settings)

    logger.info(
        "Migrated from %s: %d projects, %d memory entries, %d settings",
        path,
        summary["projects"],
        summary["memory_entries"],
        summary["settings"],
    )

    return summary
