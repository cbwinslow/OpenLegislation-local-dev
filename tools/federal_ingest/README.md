# Federal Ingestion Toolkit

This package provides Python clients and command line utilities for working with
federal legislative data sources. The layout mirrors the legacy
`tools/govdata_ingest` toolkit and offers consistent interfaces for fetching,
normalizing, exporting, and loading data from the following services:

- [`Congress.gov`](https://api.congress.gov/) (REST v3 API)
- [`api.govinfo.gov`](https://api.govinfo.gov/) (GovInfo REST API)
- [`govinfo.gov/bulkdata`](https://www.govinfo.gov/bulkdata) (bulk ZIP archives)

The clients share helpers for writing normalized JSON to disk, downloading
resources, and upserting rows into PostgreSQL using the configuration provided
by `tools/settings.py`.

## Prerequisites

1. **Python environment** – the repository's tooling environment already
   includes the following dependencies:
   - `requests`
   - `psycopg2-binary`
   - `pydantic` / `pydantic-settings`

   Install via the existing tooling requirements if needed:

   ```bash
   pip install -r tools/requirements.txt
   ```

2. **PostgreSQL access** – configure the connection using environment variables
   consumed by `tools.settings.Settings`:

   ```bash
   export PGHOST=localhost
   export PGPORT=5432
   export PGUSER=openleg
   export PGPASSWORD=secret
   export PGDATABASE=openleg
   ```

3. **API keys** – obtain credentials for each service and export them as
   environment variables (they are optional for public endpoints but required
   for higher rate limits):

   ```bash
   export CONGRESS_API_KEY="<your-congress-gov-key>"
   export GOVINFO_API_KEY="<your-govinfo-key>"
   ```

   The CLI tools will automatically read these values from `tools.settings`.

## Directory Overview

```
federal_ingest/
├── README.md                # This document
├── __init__.py              # Package marker
├── clients/                 # HTTP clients for each service
│   ├── base_client.py
│   ├── congress_api_client.py
│   ├── govinfo_api_client.py
│   └── govinfo_bulk_client.py
├── cli/                     # Command line entry points
│   ├── congress_cli.py
│   ├── govinfo_api_cli.py
│   └── govinfo_bulk_cli.py
├── common.py                # Shared JSON export and upsert helpers
└── postgres.py              # Batched PostgreSQL upsert implementation
```

## Usage

All CLIs follow a similar pattern:

1. Fetch a set of records
2. Normalize responses into a consistent JSON structure
3. Optionally persist normalized data to disk (`--output-dir`)
4. Optionally upsert the records into PostgreSQL (`--upsert --table <schema.table>`)
5. Optionally download supplemental resources (bulk ZIP archives)

### Congress.gov CLI

List resources such as bills or members:

```bash
python -m tools.federal_ingest.cli.congress_cli bills \
  --limit 50 \
  --filters '{"congress": "118"}' \
  --output-dir /tmp/congress
```

Upsert results into PostgreSQL:

```bash
python -m tools.federal_ingest.cli.congress_cli bills \
  --filters '{"congress": "118"}' \
  --upsert \
  --table staging.congress_bills \
  --conflict-columns record_id
```

### GovInfo REST CLI

Enumerate packages within a collection:

```bash
python -m tools.federal_ingest.cli.govinfo_api_cli BILLS \
  --page-size 500 \
  --output-dir /tmp/govinfo_api
```

Fetch a single package detail and insert into the database:

```bash
python -m tools.federal_ingest.cli.govinfo_api_cli BILLS \
  --package-id BILLS-118hr1 \
  --upsert \
  --table staging.govinfo_packages
```

### GovInfo Bulk CLI

Discover available bulk ZIP files and download them locally:

```bash
python -m tools.federal_ingest.cli.govinfo_bulk_cli BILLS \
  --year 2024 \
  --download \
  --download-dir /data/govinfo/bills \
  --output-dir /tmp/govinfo_bulk_inventory
```

Upsert bulk inventory metadata without downloading the assets:

```bash
python -m tools.federal_ingest.cli.govinfo_bulk_cli BILLS \
  --year 2024 \
  --upsert \
  --table staging.govinfo_bulk_inventory \
  --conflict-columns record_id
```

## Configuration Hooks

- **Environment variables** – rely on the existing `Settings` model. No
  additional configuration files are required.
- **Logging** – clients share a base logger (`federal_ingest.clients.base_client`)
  that can be configured through Python's standard logging module in the parent
  application or CLI wrapper.
- **Database schema** – the PostgreSQL helper performs batched UPSERTS using the
  provided conflict columns. Ensure the target table exists with matching column
  names (JSON columns should be declared as `jsonb`).

## Extending the Toolkit

- Add new clients inside `clients/` and expose CLI wrappers in `cli/`.
- Reuse `write_json_records` and `upsert_to_postgres` helpers to stay consistent
  with the rest of the ingestion pipeline.
- When new dependencies are required, update `tools/requirements.txt` or
  `tools/pyproject.toml` accordingly.

## Testing

At present the CLIs are thin wrappers. They can be exercised with mocked HTTP
responses using the repository's existing testing infrastructure under
`tools/tests/` when expanded in the future.
