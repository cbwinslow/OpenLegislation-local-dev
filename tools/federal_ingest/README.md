# Federal Ingestion Toolkit

This package bundles lightweight API clients and command-line utilities for
collecting federal legislative data from three upstream sources:

* [`api.congress.gov`](https://api.congress.gov) (bills, members, votes)
* [`api.govinfo.gov`](https://api.govinfo.gov) (package metadata and downloads)
* [`govinfo.gov/bulkdata`](https://www.govinfo.gov/bulkdata) (bulk ZIP/XML resources)

The folder mirrors the layout of the legacy `govdata_ingest` utilities and provides
consistent helpers for exporting normalized JSON, optionally downloading assets, and
upserting the results into PostgreSQL.

## Environment setup

1. **Python dependencies** – ensure the shared tooling environment is installed:

   ```bash
   pip install -r tools/requirements.txt
   ```

   The new scripts rely on `requests`, `pydantic`, `sqlalchemy`, `tenacity`, and
   `beautifulsoup4`. These libraries are declared in `tools/requirements.txt` and
   `tools/pyproject.toml`.

2. **API credentials** – configure the required environment variables. You can keep
   them in a root-level `.env` file and load it with your preferred tooling (for
   example `dotenv`, `direnv`, or `set -a; source .env`), or export the values
   directly in your shell session before running the CLI.

   ```bash
   export CONGRESS_GOV_API_KEY="your-congress-api-key"
   export GOVINFO_API_KEY="your-govinfo-api-key"
   # Optional: overrides psycopg2/sqlalchemy connection target
   export FEDERAL_INGEST_DATABASE_URL="postgresql://user:pass@host:5432/database"
   ```

   The `CONGRESS_GOV_API_KEY` and `GOVINFO_API_KEY` values are required for REST calls.

3. **Database connectivity** – by default the scripts reuse `tools/db_config.py` to
   build the PostgreSQL connection string. Override the target with
   `FEDERAL_INGEST_DATABASE_URL` when needed.

## Database schema

Normalized records are written into existing ingestion tables defined in
`tools/data_pipeline/scripts/schema.py`. Bulk resource metadata is persisted in a new
`govinfo_bulk_resources` table. Create it manually before running upserts:

```sql
CREATE TABLE IF NOT EXISTS public.govinfo_bulk_resources (
    resource_key TEXT PRIMARY KEY,
    collection TEXT NOT NULL,
    congress TEXT NULL,
    resource_path TEXT NOT NULL,
    download_url TEXT NOT NULL,
    retrieved_at TIMESTAMPTZ NOT NULL,
    raw_payload JSONB NOT NULL
);
```

Ensure the database user has permission to insert into these tables.

## Command-line usage

All commands are routed through a unified entrypoint:

```bash
python -m tools.federal_ingest.cli.main <source> [options]
```

Available sources and representative invocations:

### Congress.gov REST API

Fetch bills and export them to disk, while also writing into PostgreSQL:

```bash
python -m tools.federal_ingest.cli.main congress bills \
  --congress 118 \
  --limit 100 \
  --export data/congress_bills.jsonl \
  --upsert
```

List Senate members without persistence (stdout logging only):

```bash
python -m tools.federal_ingest.cli.main congress members \
  --congress 118 \
  --chamber senate
```

### GovInfo REST API

Store package metadata for the `BILLS` collection:

```bash
python -m tools.federal_ingest.cli.main govinfo-api packages \
  --collection BILLS \
  --export data/govinfo_packages.jsonl
```

Download metadata for all artifacts in a package and upsert them:

```bash
python -m tools.federal_ingest.cli.main govinfo-api downloads \
  --package-id BILLS-118hr1 \
  --upsert
```

### GovInfo bulk data

Enumerate all available resources for the 118th Congress `BILLSTATUS` collection,
write the manifest to disk, download the ZIP/XML payloads, and upsert metadata:

```bash
python -m tools.federal_ingest.cli.main govinfo-bulk \
  --collection BILLSTATUS \
  --congress 118 \
  --export data/govinfo_bulk_status.jsonl \
  --download-dir downloads/billstatus \
  --upsert
```

Downloads are optional—omit `--download-dir` to only capture metadata.

## Configuration hooks

* The clients reuse the retry-aware HTTP session provided by `tools/data_pipeline`.
* Normalized records store source payloads under the `raw_payload` key, enabling audit
  trails.
* CLI utilities honor `--database-url` to override the connection string on a per-run
  basis.

For automation, invoke these scripts from cron or orchestrators using the same flags
shown above. The normalized JSONL exports provide reproducible manifests that can be
archived alongside the raw downloads.
