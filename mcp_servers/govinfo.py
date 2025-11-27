"""GovInfo.gov MCP ingestion server."""

import os
from typing import Dict, List

from .base import EndpointConfig, MCPBulkIngestor, PaginationConfig


def default_govinfo_endpoints() -> List[EndpointConfig]:
    """Seed endpoints for common GovInfo collections."""
    return [
        EndpointConfig(
            name="collections",
            path="/collections",
            description="Collections index with paging by offset",
            pagination=PaginationConfig(
                kind="offset",
                page_param="offset",
                page_size_param="pageSize",
                results_path=("collections",),
                total_path=("count",),
                page_size=100,
            ),
        ),
        EndpointConfig(
            name="packages",
            path="/packages",
            description="Package metadata across collections",
            pagination=PaginationConfig(
                kind="offset",
                page_param="offset",
                page_size_param="pageSize",
                results_path=("packages",),
                total_path=("count",),
                page_size=100,
            ),
        ),
        EndpointConfig(
            name="usc",
            path="/collections/USCODE",
            description="U.S. Code titles and amendments",
            pagination=PaginationConfig(
                kind="offset",
                page_param="offset",
                page_size_param="pageSize",
                results_path=("packages",),
                total_path=("count",),
                page_size=100,
            ),
        ),
    ]


class GovInfoServer(MCPBulkIngestor):
    """Bulk ingestor for GovInfo.gov."""

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(
            base_url="https://api.govinfo.gov",
            api_key=api_key or os.getenv("GOVINFO_API_KEY"),
            api_key_header="X-Api-Key",
            default_rate_limit_per_sec=5,
        )
        self.endpoints = default_govinfo_endpoints()

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


__all__ = ["GovInfoServer", "default_govinfo_endpoints"]
