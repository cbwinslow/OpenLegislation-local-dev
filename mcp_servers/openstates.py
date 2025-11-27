"""OpenStates MCP ingestion server and scraper hooks."""

import os
import shlex
import subprocess
from typing import Dict, List, Sequence

from .base import EndpointConfig, MCPBulkIngestor, PaginationConfig


def default_openstates_endpoints() -> List[EndpointConfig]:
    """Seed endpoints for OpenStates v3 API collections."""
    return [
        EndpointConfig(
            name="people",
            path="/people",
            description="Legislator directory",
            pagination=PaginationConfig(
                kind="page",
                page_param="page",
                page_size_param="per_page",
                results_path=("results",),
                total_path=("pagination", "total_items"),
                page_size=50,
            ),
        ),
        EndpointConfig(
            name="bills",
            path="/bills",
            description="State bills and actions",
            pagination=PaginationConfig(
                kind="page",
                page_param="page",
                page_size_param="per_page",
                results_path=("results",),
                total_path=("pagination", "total_items"),
                page_size=50,
            ),
        ),
        EndpointConfig(
            name="committees",
            path="/committees",
            description="Committee rosters",
            pagination=PaginationConfig(
                kind="page",
                page_param="page",
                page_size_param="per_page",
                results_path=("results",),
                total_path=("pagination", "total_items"),
                page_size=50,
            ),
        ),
    ]


class OpenStatesServer(MCPBulkIngestor):
    """Bulk ingestor for the OpenStates API and scraper entrypoints."""

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(
            base_url="https://v3.openstates.org",
            api_key=api_key or os.getenv("OPENSTATES_API_KEY"),
            api_key_header="X-Api-Key",
            default_rate_limit_per_sec=3,
        )
        self.endpoints = default_openstates_endpoints()

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

    def ingest_all(self, start_pages: Dict[str, int] | None = None) -> Dict[str, int]:
        return self.ingest_endpoints(self.endpoints, start_offsets=start_pages)

    @staticmethod
    def build_scraper_command(states: Sequence[str] | None = None) -> List[str]:
        """Construct an openstates-scrapers command for regional scraping."""
        cmd = ["openstates", "scrape"]
        if states:
            cmd.extend(states)
        return cmd

    def run_scrapers(self, states: Sequence[str] | None = None) -> subprocess.CompletedProcess[str]:
        """Invoke openstates-scrapers if it is installed in the environment."""
        command = self.build_scraper_command(states)
        printable = " ".join(shlex.quote(part) for part in command)
        print(f"Executing scraper command: {printable}")
        return subprocess.run(command, check=False, text=True, capture_output=True)


__all__ = ["OpenStatesServer", "default_openstates_endpoints"]
