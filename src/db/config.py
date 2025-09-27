from __future__ import annotations

import os
from functools import lru_cache

from sqlalchemy.engine import URL

DEFAULT_DB_HOST = os.getenv("DB_HOST", "localhost")
DEFAULT_DB_PORT = int(os.getenv("DB_PORT", "5432"))
DEFAULT_DB_NAME = os.getenv("DB_NAME", "openleg")
DEFAULT_DB_USER = os.getenv("DB_USER", "openleg")
DEFAULT_DB_PASS = os.getenv("DB_PASS", "openleg")


@lru_cache(maxsize=1)
def get_database_url() -> URL:
    """Return a SQLAlchemy URL built from environment variables."""
    return URL.create(
        "postgresql+psycopg2",
        username=DEFAULT_DB_USER,
        password=DEFAULT_DB_PASS,
        host=DEFAULT_DB_HOST,
        port=DEFAULT_DB_PORT,
        database=DEFAULT_DB_NAME,
    )
