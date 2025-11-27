"""Congress.gov MCP ingestion server."""

import os
from typing import Dict, List

from .base import EndpointConfig, MCPBulkIngestor, PaginationConfig


def default_congress_endpoints() -> List[EndpointConfig]:
    """
    Return a list of preconfigured EndpointConfig objects for common Congress.gov collections.
    
    Provides EndpointConfig entries for the following collections: bills, amendments, committees, and members. Each entry is configured with offset-based pagination (page parameter "offset", page size parameter "limit") and a default page size of 250; results and total-count response paths are set per-collection.
    
    Returns:
        List[EndpointConfig]: A list containing EndpointConfig instances for
            "bills", "amendments", "committees", and "members".
    
    """
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
        """
        Initialize a Congress.gov bulk ingestor configured with default endpoints and rate limits.
        
        Args:
            api_key (str | None): Optional API key to authenticate with the Congress.gov API.
                If omitted, the constructor will read the key from the CONGRESS_API_KEY environment variable.
        
        Side effects:
            - Configures the base URL, API key header, and default rate limit on the underlying MCPBulkIngestor.
            - Initializes the default set of Congress.gov endpoints (bills, amendments, committees, members).
        """
        super().__init__(
            base_url="https://api.congress.gov",
            api_key=api_key or os.getenv("CONGRESS_API_KEY"),
            api_key_header="X-Api-Key",
            default_rate_limit_per_sec=5,
        )
        self.endpoints = default_congress_endpoints()

    def list_endpoints(self) -> List[Dict[str, str]]:
        """
        List available endpoint configurations as simplified dictionaries.
        
        Returns:
            List[Dict[str, str]]: A list where each item describes an endpoint with the keys:
                - name: endpoint identifier
                - path: API path for the endpoint
                - description: human-readable description
                - page_param: query parameter name used for paging offset
                - page_size_param: query parameter name used for page size
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
        Ingest all configured endpoints from their respective Congress.gov collections.
        
        Args:
            start_offsets (Dict[str, int] | None): Optional mapping of endpoint names to starting offset values; when provided ingestion for each named endpoint begins from the given offset, otherwise ingestion starts from the default starting point for that endpoint.
        
        Returns:
            Dict[str, int]: Mapping from endpoint name to the last offset processed for that endpoint.
        
        Side effects:
            Performs network requests and writes ingested data via the ingestor's configured ingestion pipeline.
        """
        return self.ingest_endpoints(self.endpoints, start_offsets=start_offsets)


__all__ = ["CongressServer", "default_congress_endpoints"]