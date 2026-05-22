"""
Database session factory — opt-in via DATABASE_URL.

When DATABASE_URL is unset, no engine is created; call `configure_engine(url)` early in app startup.
"""

from collections.abc import Generator
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker[Session]] = None


def configure_engine(database_url: str) -> None:
    """Create engine and session factory (SQLite file, Postgres URL, etc.)."""
    global _engine, _SessionLocal
    _engine = create_engine(database_url, echo=False, future=True)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)


def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError(
            "Database not configured. Set DATABASE_URL in `.env` and call configure_engine(url) "
            "during application startup."
        )
    return _engine


def get_session() -> Generator[Session, None, None]:
    if _SessionLocal is None:
        raise RuntimeError("Database session factory missing — configure_engine first.")
    session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()
