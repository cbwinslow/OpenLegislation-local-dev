# MCP Ingestion Servers

This guide describes the three Model Context Protocol (MCP) ingestion servers that fetch bulk data from Congress.gov, GovInfo.gov, and OpenStates.

## Overview
- **CongressServer**: Pulls bill, amendment, committee, and member records with offset-based pagination.
- **GovInfoServer**: Retrieves collection and package metadata with offset-based pagination.
- **OpenStatesServer**: Supports the v3 API (page-based pagination) and optional `openstates-scrapers` execution for regional coverage.

Each server relies on the shared `MCPBulkIngestor` for throttling, pagination, and consistent result handling.

## Usage
Run the CLI via the module entrypoint:

```bash
python -m mcp_servers.cli congress --list
python -m mcp_servers.cli congress --start-offsets '{"bills":0}' --page-sizes '{"bills":250}'
python -m mcp_servers.cli govinfo --list
python -m mcp_servers.cli govinfo --start-offsets '{"collections":0}'
python -m mcp_servers.cli openstates --list
python -m mcp_servers.cli openstates --start-offsets '{"bills":1}' --page-sizes '{"bills":50}'
python -m mcp_servers.cli openstates --scrape --states ny ca
```

### API Keys
- `CONGRESS_API_KEY` for Congress.gov
- `GOVINFO_API_KEY` for GovInfo.gov
- `OPENSTATES_API_KEY` for OpenStates API

CLI flags allow overriding keys per invocation.

### Pagination Semantics
- **Offset mode**: uses `offset` + `limit` (Congress.gov, GovInfo.gov). The ingestor advances by the number of results, ensuring no duplicates and full coverage until totals are exhausted.
- **Page mode**: uses `page` + `per_page` (OpenStates API). The ingestor increments pages sequentially until a short page is returned.

### Extending Endpoints
Add new `EndpointConfig` entries to the respective `default_*_endpoints` helpers. They expose:
- `results_path` to control where items are read from the JSON payload.
- `total_path` to stop automatically when totals are known.
- `page_param`/`page_size_param` to match provider conventions.

### Scraper Support (OpenStates)
The CLI exposes `--scrape` to run `openstates-scrapers` if installed. Use `--states` to scope runs (e.g., `ny`, `ca`). Output is captured and printed for log visibility.

## Agent Integration
`crewai_agents/mcp_integration.py` registers three new MCP servers pointing at the CLI entrypoints. Tools expose schemas for bulk ingestion and endpoint enumeration so AI agents can plan pulls programmatically.
