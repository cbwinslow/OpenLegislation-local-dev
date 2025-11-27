# MCP Ingestion Servers

This guide describes the three Model Context Protocol (MCP) ingestion servers that fetch bulk data from Congress.gov, GovInfo.gov, and OpenStates.

## Overview
- **CongressServer**: Pulls bill, amendment, committee, and member records with offset-based pagination.
- **GovInfoServer**: Retrieves collection and package metadata with offset-based pagination.
- **OpenStatesServer**: Supports the v3 API (page-based pagination) and optional `openstates-scrapers` execution for regional coverage.

Each server relies on the shared `MCPBulkIngestor` for throttling, pagination, and consistent result handling.

## CLI Structure

The CLI uses explicit subcommands that map directly to MCP tool definitions:

```
python -m mcp_servers.cli <provider> <action> [options]
```

Where:
- `<provider>` is one of: `congress`, `govinfo`, `openstates`
- `<action>` is one of: `list`, `ingest`, or `scrape` (openstates only)

### Usage Examples

```bash
# List endpoints
python -m mcp_servers.cli congress list
python -m mcp_servers.cli govinfo list
python -m mcp_servers.cli openstates list

# Ingest data with optional pagination control
python -m mcp_servers.cli congress ingest --start-offsets '{"bills":0}' --page-sizes '{"bills":250}'
python -m mcp_servers.cli govinfo ingest --start-offsets '{"collections":0}'
python -m mcp_servers.cli openstates ingest --start-offsets '{"bills":1}' --page-sizes '{"bills":50}'

# Run OpenStates scrapers
python -m mcp_servers.cli openstates scrape --states ny ca
```

### API Keys
- `CONGRESS_API_KEY` for Congress.gov
- `GOVINFO_API_KEY` for GovInfo.gov
- `OPENSTATES_API_KEY` for OpenStates API

CLI flags allow overriding keys per invocation with `--api-key`.

If API keys are not set, requests will fail with authentication errors. Set the appropriate environment variable before running ingestion commands.

### Pagination Semantics
- **Offset mode**: uses `offset` + `limit` (Congress.gov, GovInfo.gov). The ingestor advances by the number of results, ensuring no duplicates and full coverage until totals are exhausted.
- **Page mode**: uses `page` + `per_page` (OpenStates API). The ingestor increments pages sequentially until a short page is returned.

### Error Handling

The CLI includes JSON validation for `--start-offsets` and `--page-sizes` arguments. Invalid JSON will result in a clear error message and non-zero exit code.

For scraper commands, non-zero exit codes from the underlying scraper are propagated to the CLI.

### Extending Endpoints
Add new `EndpointConfig` entries to the respective `default_*_endpoints` helpers. They expose:
- `results_path` to control where items are read from the JSON payload.
- `total_path` to stop automatically when totals are known.
- `page_param`/`page_size_param` to match provider conventions.

### Scraper Support (OpenStates)
The CLI exposes `openstates scrape` to run `openstates-scrapers` if installed. Use `--states` to scope runs (e.g., `ny`, `ca`). Output is captured and printed for log visibility.

## Agent Integration

`crewai_agents/mcp_integration.py` registers separate MCP servers for each tool action. Each tool maps directly to a CLI subcommand:

| Tool Name | CLI Command |
|-----------|-------------|
| `congress_list_endpoints` | `congress list` |
| `congress_bulk_ingest` | `congress ingest` |
| `govinfo_list_endpoints` | `govinfo list` |
| `govinfo_bulk_ingest` | `govinfo ingest` |
| `openstates_list_endpoints` | `openstates list` |
| `openstates_bulk_ingest` | `openstates ingest` |
| `openstates_run_scrapers` | `openstates scrape` |

This direct mapping ensures AI agents can invoke tools without ambiguity about CLI argument translation.
