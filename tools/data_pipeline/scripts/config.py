"""Configuration helpers for ingestion scripts."""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings, Field, PostgresDsn, validator


class PipelineSettings(BaseSettings):
    """Environment-driven configuration."""

    database_url: PostgresDsn = Field(..., env="PIPELINE_DATABASE_URL")
    congress_api_key: str = Field(..., env="CONGRESS_GOV_API_KEY")
    govinfo_api_key: str = Field(..., env="GOVINFO_API_KEY")
    openstates_api_key: str = Field(..., env="OPENSTATES_API_KEY")
    ny_openleg_api_key: str = Field(..., env="NY_OPENLEG_API_KEY")
    default_state: Optional[str] = Field(None, env="PIPELINE_DEFAULT_STATE")
    default_session: Optional[str] = Field(None, env="PIPELINE_DEFAULT_SESSION")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @validator("database_url")
    def ensure_postgres(cls, value: PostgresDsn) -> PostgresDsn:
        if not str(value).startswith("postgres"):
            raise ValueError("PIPELINE_DATABASE_URL must be a PostgreSQL DSN")
        return value


@lru_cache()
def get_settings() -> PipelineSettings:
    return PipelineSettings()  # type: ignore[call-arg]

