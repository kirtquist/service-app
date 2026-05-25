"""Initialize database engine and schema."""

from __future__ import annotations

import logging
from pathlib import Path

from service_app.db.base import Base
from service_app.db.session import configure_engine, get_engine

logger = logging.getLogger(__name__)


def resolve_database_url(database_url: str | None) -> str:
    if database_url:
        return database_url
    return "sqlite:///./data/service_app.db"


def init_database(database_url: str | None) -> str:
    """Configure SQLAlchemy and create tables if needed."""
    url = resolve_database_url(database_url)
    if url.startswith("sqlite:///./"):
        db_path = url.removeprefix("sqlite:///./")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    configure_engine(url)
    Base.metadata.create_all(get_engine())
    logger.info("Database initialized (%s)", url.split("@")[-1])
    return url
