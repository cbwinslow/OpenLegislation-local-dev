# Federal Ingestion Utilities

This directory provides Python clients and command line interfaces for working
with the primary public data services maintained by the United States federal
legislative branch:

* [`congress.gov`](https://api.congress.gov) – the official Congress REST API.
* [`api.govinfo.gov`](https://api.govinfo.gov) – the GovInfo REST API for
  document metadata and package details.
* [`govinfo.gov/bulkdata`](https://www.govinfo.gov/bulkdata) – static ZIP
  archives distributed via the GovInfo bulk data service.

The layout mirrors the existing ingestion helpers that live under
`tools/govinfo` and follows the same conventions for configuration, logging,
and exporting data.

## Installation

1. Ensure Python 3.11+ is available on your system.
2. Install the shared tool dependencies:

   ```bash
   pip install -r tools/requirements.txt
   ```

3. Optionally install the repository as an editable package to make the CLI
   entry points importable from anywhere:

   ```bash
   pip install -e tools
   ```

## Authentication

The `congress.gov` and `api.govinfo.gov` clients require API keys. Create a
free key for each service and expose them via environment variables before
running the CLI tools:

```bash
export CONGRESS_API_KEY="your-congress-api-key"
export GOVINFO_API_KEY="your-govinfo-api-key"
```

The PostgreSQL integration reads from `FEDERAL_DB_URL` (preferred) or `DB_URL`
if it is defined. The value should be a libpq connection string:

```bash
export FEDERAL_DB_URL="postgresql://user:password@host:5432/database"
```

All configuration options can be overridden at runtime by passing explicit
flags (for example `--api-key` or `--db-url`).

## Command Line Interfaces

Each data source ships with a dedicated CLI that exposes a consistent set of
capabilities:

* Export normalised JSON documents to disk.
* Optionally download additional artefacts (PDF, XML, ZIP).
* Upsert records into PostgreSQL using the same `ON CONFLICT` strategy as the
  existing ingestion tooling.

### congress.gov (REST)

```bash
python -m tools.federal_ingest.cli_congress bill \
  --param congress=118 \
  --limit 25 \
  --output-dir data/congress-json \
  --download-dir data/congress-assets \
  --table master.federal_documents
```

Important flags:

* `collection` (positional): API collection name (`bill`, `member`, etc.).
* `--param KEY=VALUE`: arbitrary query parameters forwarded to the API.
* `--limit`: stop after retrieving *n* records (defaults to all available).
* `--page-size`: adjust the page size (maximum 250 as enforced by the API).

### GovInfo REST API

```bash
python -m tools.federal_ingest.cli_govinfo_api BILLSTATUS \
  --filter congress=118 \
  --limit 100 \
  --output-dir data/govinfo-json \
  --download-dir data/govinfo-assets \
  --table master.federal_documents
```

Important flags:

* `collection` (positional): GovInfo collection identifier (`BILLSTATUS`,
  `FR`, etc.).
* `--filter KEY=VALUE`: extra filters supported by `api.govinfo.gov` such as
  `congress`, `fromDate`, or `modifiedSince`.

### GovInfo Bulk Data

```bash
python -m tools.federal_ingest.cli_govinfo_bulk BILLSTATUS \
  --congress 118 \
  --output-dir data/bulk-index \
  --download-dir data/bulk-zips \
  --table master.federal_documents
```

Important flags:

* `collection` (positional): bulk collection identifier (`BILLSTATUS`, `BILLS`,
  `PLAW`, etc.).
* `--congress`: optional congress or session component appended to the bulk
  path.
* `--doc-class`: optional document class component for nested directories.

## PostgreSQL Upserts

All CLIs accept `--table` and `--db-url` arguments. When supplied, the
`PostgresUpserter` helper writes the normalised documents to the destination
using an `ON CONFLICT` clause keyed by `(source, collection, external_id)`. The
expected schema is:

```sql
CREATE TABLE master.federal_documents (
  source TEXT NOT NULL,
  collection TEXT NOT NULL,
  external_id TEXT NOT NULL,
  title TEXT,
  summary TEXT,
  document_date TEXT,
  retrieved_at TIMESTAMPTZ NOT NULL,
  data JSONB NOT NULL,
  resources JSONB NOT NULL,
  PRIMARY KEY (source, collection, external_id)
);
```

Adjust the table name to align with your deployment.

## Scheduling Hooks

The new pipelines can be integrated with the existing orchestration helpers in
`tools/manage_ingestion_state.py` or the TUI by invoking the modules via
`python -m tools.federal_ingest.<cli_name>`. Each script supports a `--dry-run`
mode which emits the normalised payloads without touching disk or the
database, making it easy to validate new configurations in CI or during
development.

