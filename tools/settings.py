"""
Universal settings configuration for OpenLegislation tools using Pydantic.

This module provides centralized configuration management for all Python scripts
in the tools directory. Settings are loaded from environment variables and .env files.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # Database Configuration
    pghost: str = Field(default="localhost", env="PGHOST")
    pgport: int = Field(default=5432, env="PGPORT")
    pguser: str = Field(default="postgres", env="PGUSER")
    pgpassword: str = Field(default="", env="PGPASSWORD")
    pgdatabase: str = Field(default="openleg", env="PGDATABASE")

    # JDBC URL (computed from DB settings)
    jdbc_database_url: Optional[str] = Field(default=None, env="JDBC_DATABASE_URL")

    # Test Database Configuration
    test_db_host: str = Field(default="localhost", env="TEST_DB_HOST")
    test_db_port: int = Field(default=5432, env="TEST_DB_PORT")
    test_db_name: str = Field(default="openleg_test", env="TEST_DB_NAME")
    test_db_user: str = Field(default="postgres", env="TEST_DB_USER")
    test_db_password: str = Field(default="", env="TEST_DB_PASSWORD")

    # API Keys
    congress_api_key: str = Field(default="", env="CONGRESS_API_KEY")
    govinfo_api_key: str = Field(default="", env="GOVINFO_API_KEY")

    # GPU Configuration
    use_gpu: bool = Field(default=False, env="USE_GPU")
    cuda_visible_devices: str = Field(default="", env="CUDA_VISIBLE_DEVICES")

    # Script Configuration
    max_errors: int = Field(default=100, description="Maximum number of errors before script fails")
    request_timeout: int = Field(default=30, description="HTTP request timeout in seconds")
    rate_limit_delay: float = Field(default=0.5, description="Delay between API requests in seconds")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

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
