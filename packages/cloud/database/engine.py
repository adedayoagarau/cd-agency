"""Database engine setup and session management for CD Agency Cloud."""
from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

_engine: Engine | None = None

DEFAULT_DATABASE_URL = "postgresql://localhost/cd_agency"


def get_engine() -> Engine:
    """Return a singleton SQLAlchemy engine.

    The connection string is read from the ``DATABASE_URL`` environment
    variable, falling back to a local PostgreSQL default.
    """
    global _engine
    if _engine is None:
        database_url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
        _engine = create_engine(
            database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=os.environ.get("SQL_ECHO", "").lower() in ("1", "true"),
        )
    return _engine


SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=None,  # Bound lazily via get_session / init_db
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Provide a transactional database session as a context manager.

    Usage::

        with get_session() as session:
            org = session.get(Organization, org_id)
    """
    engine = get_engine()
    SessionLocal.configure(bind=engine)
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Create all tables defined in :pydata:`Base.metadata`.

    Intended for development and testing. Production should use Alembic
    migrations instead.
    """
    engine = get_engine()
    SessionLocal.configure(bind=engine)
    Base.metadata.create_all(bind=engine)
