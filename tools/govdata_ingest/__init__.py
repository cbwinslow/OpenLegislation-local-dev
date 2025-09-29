"""Utilities for streaming ingestion of data.gov datasets."""

from .extract_govdata import ingest_to_postgres

__all__ = ["ingest_to_postgres"]
