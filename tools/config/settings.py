"""
Universal settings configuration for OpenLegislation tools using Pydantic.

This module provides centralized configuration management for all Python scripts
in the tools directory. Settings are loaded from environment variables and .env files.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"  # Allow extra fields from environment variables
    )

    # Database Configuration
    pghost: str = Field(default="localhost")
    pgport: int = Field(default=5432)
    pguser: str = Field(default="postgres")
    pgpassword: str = Field(default="")
    pgdatabase: str = Field(default="openleg")

    # JDBC URL (computed from DB settings)
    jdbc_database_url: Optional[str] = Field(default=None)

    # Test Database Configuration
    test_db_host: str = Field(default="localhost")
    test_db_port: int = Field(default=5432)
    test_db_name: str = Field(default="openleg_test")
    test_db_user: str = Field(default="postgres")
    test_db_password: str = Field(default="")

    # API Keys
    congress_api_key: str = Field(default="")
    govinfo_api_key: str = Field(default="")

    # GPU Configuration
    use_gpu: bool = Field(default=False)
    cuda_visible_devices: str = Field(default="")

    # Script Configuration - Updated for full data ingestion
    max_errors: int = Field(
        default=10000, description="Maximum number of errors before script fails (increased for full ingestion)"
    )
    request_timeout: int = Field(
        default=120, description="HTTP request timeout in seconds (increased for large datasets)"
    )
    rate_limit_delay: float = Field(
        default=0.1, description="Delay between API requests in seconds (reduced for faster ingestion)"
    )

    @property
    def db_config(self) -> dict:
        """Database configuration dict for psycopg2."""
        return {
            "host": self.pghost,
            "port": self.pgport,
            "user": self.pguser,
            "password": self.pgpassword,
            "database": self.pgdatabase,
        }

    @property
    def test_db_config(self) -> dict:
        """Test database configuration dict for psycopg2."""
        return {
            "host": self.test_db_host,
            "port": self.test_db_port,
            "user": self.test_db_user,
            "password": self.test_db_password,
            "database": self.test_db_name,
        }

    @property
    def jdbc_url(self) -> str:
        """JDBC URL, either from env or constructed from DB settings."""
        if self.jdbc_database_url:
            return self.jdbc_database_url
        return f"jdbc:postgresql://{self.pghost}:{self.pgport}/{self.pgdatabase}"


# Global settings instance
settings = Settings()
