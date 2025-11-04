"""Configuration helpers for federal ingestion pipelines."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional


@dataclass(frozen=True)
class FederalIngestSettings:
    """Settings loaded from environment for API access and database targets."""

    congress_api_key: str
    govinfo_api_key: str
    database_url: Optional[str]


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


@lru_cache()
def get_settings() -> FederalIngestSettings:
    """Return cached settings instance."""

    return FederalIngestSettings(
        congress_api_key=_require_env("CONGRESS_GOV_API_KEY"),
        govinfo_api_key=_require_env("GOVINFO_API_KEY"),
        database_url=os.getenv("FEDERAL_INGEST_DATABASE_URL"),
    )


__all__ = ["FederalIngestSettings", "get_settings"]
