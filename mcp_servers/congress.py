"""Congress.gov MCP ingestion server."""

import os
from typing import Dict, List

from .base import EndpointConfig, MCPBulkIngestor, PaginationConfig


def default_congress_endpoints() -> List[EndpointConfig]:
    """Seed endpoints for common Congress.gov collections."""
    return [
        EndpointConfig(
            name="bills",
            path="/v3/bill",
            description="All bills with pagination via offset + limit",
            pagination=PaginationConfig(
                kind="offset",
                page_param="offset",
                page_size_param="limit",
                results_path=("bills",),
                total_path=("pagination", "count"),
                page_size=250,
            ),
        ),
        EndpointConfig(
            name="amendments",
            path="/v3/amendment",
            description="Congressional amendments",
            pagination=PaginationConfig(
                kind="offset",
                page_param="offset",
                page_size_param="limit",
                results_path=("amendments",),
                total_path=("pagination", "count"),
                page_size=250,
            ),
        ),
        EndpointConfig(
            name="committees",
            path="/v3/committee",
            description="Committee roster and membership",
            pagination=PaginationConfig(
                kind="offset",
                page_param="offset",
                page_size_param="limit",
                results_path=("committees",),
                total_path=("pagination", "count"),
                page_size=250,
            ),
        ),
        EndpointConfig(
            name="members",
            path="/v3/member",
            description="Member directory",
            pagination=PaginationConfig(
                kind="offset",
                page_param="offset",
                page_size_param="limit",
                results_path=("members",),
                total_path=("pagination", "count"),
                page_size=250,
            ),
        ),
    ]


class CongressServer(MCPBulkIngestor):
    """Bulk ingestor for Congress.gov."""

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(
            base_url="https://api.congress.gov",
            api_key=api_key or os.getenv("CONGRESS_API_KEY"),
            api_key_header="X-Api-Key",
            default_rate_limit_per_sec=5,
        )
        self.endpoints = default_congress_endpoints()

    def list_endpoints(self) -> List[Dict[str, str]]:
        return [
            {
                "name": endpoint.name,
                "path": endpoint.path,
                "description": endpoint.description,
                "page_param": endpoint.pagination.page_param,
                "page_size_param": endpoint.pagination.page_size_param,
            }
            for endpoint in self.endpoints
        ]

    def ingest_all(self, start_offsets: Dict[str, int] | None = None) -> Dict[str, int]:
        return self.ingest_endpoints(self.endpoints, start_offsets=start_offsets)


__all__ = ["CongressServer", "default_congress_endpoints"]
