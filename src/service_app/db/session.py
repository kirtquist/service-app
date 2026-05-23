"""Database session factory — opt-in via DATABASE_URL."""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker[Session]] = None


def configure_engine(database_url: str) -> None:
    """Create engine and session factory (SQLite file, Postgres URL, etc.)."""
    global _engine, _SessionLocal
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    _engine = create_engine(
        database_url,
        echo=False,
        future=True,
        connect_args=connect_args,
    )
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


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager for scripts and webhook handlers."""
    gen = get_session()
    session = next(gen)
    try:
        yield session
    finally:
        try:
            next(gen)
        except StopIteration:
            pass
