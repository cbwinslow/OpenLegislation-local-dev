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
    """
    Retrieve the value of a required environment variable.
    
    Parameters:
        name (str): The name of the environment variable to read.
    
    Returns:
        str: The environment variable's value.
    
    Raises:
        RuntimeError: If the environment variable is missing or empty.
    """
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


@lru_cache()
def get_settings() -> FederalIngestSettings:
    """
    Provide a cached FederalIngestSettings instance populated from environment variables.
    
    Returns:
        FederalIngestSettings: Instance with `congress_api_key` from CONGRESS_GOV_API_KEY, `govinfo_api_key` from GOVINFO_API_KEY, and `database_url` from FEDERAL_INGEST_DATABASE_URL or `None`.
    """

    return FederalIngestSettings(
        congress_api_key=_require_env("CONGRESS_GOV_API_KEY"),
        govinfo_api_key=_require_env("GOVINFO_API_KEY"),
        database_url=os.getenv("FEDERAL_INGEST_DATABASE_URL"),
    )


__all__ = ["FederalIngestSettings", "get_settings"]