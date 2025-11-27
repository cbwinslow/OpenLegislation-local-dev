"""OpenStates MCP ingestion server and scraper hooks."""

import os
import shlex
import subprocess
from typing import Dict, List, Sequence

from .base import EndpointConfig, MCPBulkIngestor, PaginationConfig


def default_openstates_endpoints() -> List[EndpointConfig]:
    """
    Return a seeded list of EndpointConfig objects for the OpenStates v3 API.
    
    Each returned EndpointConfig represents one of the seeded collections: "people",
    "bills", and "committees". All endpoints are configured for page-based
    pagination using the `page` and `per_page` parameters and expect results under
    `results` with the total count at `pagination.total_items`.
    
    Returns:
        List[EndpointConfig]: A list containing three EndpointConfig instances for
            "people", "bills", and "committees", each with a PaginationConfig
            where `page_size` defaults to 50.
    
    Notes:
        - The pagination configuration uses `kind="page"`, `page_param="page"`,
          and `page_size_param="per_page"`.
        - The default `page_size` is 50 for all seeded endpoints.
    """
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
        """
        Initialize the OpenStatesServer with API configuration and endpoint definitions.
        
        Args:
            api_key (str | None): OpenStates API key to use. If None, the constructor reads the OPENSTATES_API_KEY environment variable.
        
        Side effects:
            - Configures the base API URL, API key header, and default rate limit for requests.
            - Populates `self.endpoints` with the default OpenStates v3 endpoint configurations.
        """
        super().__init__(
            base_url="https://v3.openstates.org",
            api_key=api_key or os.getenv("OPENSTATES_API_KEY"),
            api_key_header="X-Api-Key",
            default_rate_limit_per_sec=3,
        )
        self.endpoints = default_openstates_endpoints()

    def list_endpoints(self) -> List[Dict[str, str]]:
        """
        List metadata for each configured OpenStates endpoint.
        
        Returns:
            List[Dict[str, str]]: A list of dictionaries describing each endpoint. Each dictionary contains:
                - "name": The endpoint's name.
                - "path": The endpoint's API path.
                - "description": A short description of the endpoint.
                - "page_param": The query parameter name used for page number.
                - "page_size_param": The query parameter name used for page size.
        
        Side effects:
            None.
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

    def ingest_all(self, start_pages: Dict[str, int] | None = None) -> Dict[str, int]:
        """
        Ingest all configured OpenStates endpoints, optionally resuming from provided start pages.
        
        Args:
            start_pages (dict[str, int] | None): Optional mapping of endpoint name to starting page number to resume ingestion from.
        
        Returns:
            dict[str, int]: Mapping of endpoint name to ingestion result (counts or status codes returned by the underlying ingestor).
        """
        return self.ingest_endpoints(self.endpoints, start_offsets=start_pages)

    @staticmethod
    def build_scraper_command(states: Sequence[str] | None = None) -> List[str]:
        """
        Builds the command list for running OpenStates scrapers.
        
        Args:
            states (Sequence[str] | None): Optional sequence of state identifiers (e.g., state abbreviations or names)
                to pass to the scraper; when provided they are appended to the command in order.
        
        Returns:
            List[str]: A list of command components suitable for execution with subprocess (e.g., ["openstates", "scrape", ...]).
        
        """
        cmd = ["openstates", "scrape"]
        if states:
            cmd.extend(states)
        return cmd

    def run_scrapers(self, states: Sequence[str] | None = None) -> subprocess.CompletedProcess[str]:
        """
        Run the OpenStates scrapers as an external command.
        
        Args:
            states (Sequence[str] | None): Optional sequence of state identifiers to pass to the scraper command; if omitted, runs the scraper without state filters.
        
        Returns:
            subprocess.CompletedProcess[str]: The completed process with captured `stdout` and `stderr` as strings and the exit code in `returncode`.
        
        Raises:
            FileNotFoundError: If the `openstates` scraper executable is not available in the environment.
        
        Side effects:
            Prints the shell-escaped command to stdout and executes an external process which may perform network I/O and file system operations.
        """
        command = self.build_scraper_command(states)
        printable = " ".join(shlex.quote(part) for part in command)
        print(f"Executing scraper command: {printable}")
        return subprocess.run(command, check=False, text=True, capture_output=True)


__all__ = ["OpenStatesServer", "default_openstates_endpoints"]