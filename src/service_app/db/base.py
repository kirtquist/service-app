"""SQLAlchemy declarative base for future persistence (customers, jobs, invoices)."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
