"""SQLAlchemy table metadata for federal ingestion targets."""
from __future__ import annotations

from sqlalchemy import JSON, Column, DateTime, MetaData, String, Table

from tools.data_pipeline.scripts.schema import (
    congress_bills,
    congress_members,
    congress_votes,
    govinfo_downloads,
    govinfo_packages,
)

metadata = MetaData(schema="public")

govinfo_bulk_resources = Table(
    "govinfo_bulk_resources",
    metadata,
    Column("resource_key", String, primary_key=True),
    Column("collection", String, nullable=False),
    Column("congress", String, nullable=True),
    Column("resource_path", String, nullable=False),
    Column("download_url", String, nullable=False),
    Column("retrieved_at", DateTime, nullable=False),
    Column("raw_payload", JSON, nullable=False),
)

TABLE_MAP = {
    "congress_bills": congress_bills,
    "congress_members": congress_members,
    "congress_votes": congress_votes,
    "govinfo_packages": govinfo_packages,
    "govinfo_downloads": govinfo_downloads,
    "govinfo_bulk_resources": govinfo_bulk_resources,
}

__all__ = ["TABLE_MAP", "govinfo_bulk_resources"]
