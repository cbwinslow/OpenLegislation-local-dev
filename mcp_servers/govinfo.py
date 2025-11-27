"""GovInfo.gov MCP ingestion server."""

import os
from typing import Dict, List

from .base import EndpointConfig, MCPBulkIngestor, PaginationConfig


def default_govinfo_endpoints() -> List[EndpointConfig]:
    """
    Return a list of default EndpointConfig objects for common GovInfo.gov collections.
    
    Provides preconfigured endpoints for the GovInfo API:
    - "collections": collections index (offset pagination).
    - "packages": package metadata across collections (offset pagination).
    - "usc": U.S. Code titles and amendments (offset pagination).
    
    Returns:
        List[EndpointConfig]: A list of three EndpointConfig instances configured
            with offset-based PaginationConfig objects (page param "offset",
            page size param "pageSize", results and total paths, page_size=100).
    """
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
        """
        Create a GovInfoServer configured for the GovInfo.gov API.
        
        Args:
            api_key (str | None): Optional API key to authenticate requests. If not provided,
                the constructor will use the GOVINFO_API_KEY environment variable.
        
        Side effects:
            - Configures the base URL, API key header, and default rate limit on the instance.
            - Populates `self.endpoints` with the default GovInfo endpoint configurations.
        """
        super().__init__(
            base_url="https://api.govinfo.gov",
            api_key=api_key or os.getenv("GOVINFO_API_KEY"),
            api_key_header="X-Api-Key",
            default_rate_limit_per_sec=5,
        )
        self.endpoints = default_govinfo_endpoints()

    def list_endpoints(self) -> List[Dict[str, str]]:
        """
        Return metadata for each configured endpoint.
        
        Args:
            None
        
        Returns:
            List[dict]: A list where each item is a dictionary describing an endpoint with the following keys:
                - "name": endpoint name.
                - "path": endpoint HTTP path.
                - "description": human-readable description of the endpoint.
                - "page_param": query parameter name used for paging.
                - "page_size_param": query parameter name used for page size.
        
        Raises:
            None
        
        Side effects:
            None
        """
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
        """
        Ingest all configured GovInfo endpoints.
        
        Args:
            start_offsets (dict[str, int] | None): Optional mapping of endpoint name to starting
                offset to resume ingestion from. If omitted, ingestion starts from each endpoint's
                default starting position.
        
        Returns:
            dict[str, int]: Mapping from endpoint identifier (name or configured id) to the number
            of items ingested for that endpoint.
        
        Side effects:
            Performs network requests and writes ingested data via the ingestor's configured
            handlers.
        """
        return self.ingest_endpoints(self.endpoints, start_offsets=start_offsets)


__all__ = ["GovInfoServer", "default_govinfo_endpoints"]