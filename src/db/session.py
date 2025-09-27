from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .base import Base
from .config import get_database_url

_engine = create_engine(get_database_url(), echo=False, future=True)
SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False, class_=Session)


def init_db() -> None:
    """Create all tables defined on the Base metadata."""
    Base.metadata.create_all(bind=_engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:  # pragma: no cover - safety rollback
        session.rollback()
        raise
    finally:
        session.close()
