# Legislative Data Pipeline

This module organizes reusable clients, data models, database schema, and operational scripts for synchronizing legislative data from major public sources into PostgreSQL.

## Directory Overview

- `clients/` – Typed API clients that wrap `api.congress.gov`, `api.govinfo.gov`, OpenStates, and New York OpenLegislation endpoints with retry-aware HTTP helpers.
- `models/` – Pydantic models that normalize response payloads from each provider while preserving the original raw JSON for auditing.
- `scripts/` – Executable orchestration utilities for pulling, downloading, and storing data into PostgreSQL tables.
- `migrations/` – SQL files to initialize or update the target database schema.

## Environment Configuration

Populate a `.env` file or environment variables with the following keys:

```
PIPELINE_DATABASE_URL=postgresql+psycopg2://user:password@host:5432/database
CONGRESS_GOV_API_KEY=...
GOVINFO_API_KEY=...
OPENSTATES_API_KEY=...
NY_OPENLEG_API_KEY=...
PIPELINE_DEFAULT_STATE=ny
PIPELINE_DEFAULT_SESSION=2023
```

The `PipelineSettings` loader in `scripts/config.py` reads and validates these settings using Pydantic.

## Database Setup

Apply the baseline schema to your PostgreSQL instance:

```
psql "$PIPELINE_DATABASE_URL" -f tools/data_pipeline/migrations/0001_create_pipeline_schema.sql
```

Tables are designed to accept JSONB payloads for future-proof auditing while storing normalized columns for analytics.

## Running Ingestion Jobs

Use the `ingest.py` entrypoint to synchronize data. Examples:

```
python -m tools.data_pipeline.scripts.ingest openstates-people --state ny --chamber upper
python -m tools.data_pipeline.scripts.ingest openstates-bills --state ny --session 2023
python -m tools.data_pipeline.scripts.ingest congress-bills --congress 118
python -m tools.data_pipeline.scripts.ingest govinfo --collection BILLS
python -m tools.data_pipeline.scripts.ingest openleg-agendas --year 2024
```

All jobs accept `--batch-size` for write chunking and `--verbose` for debug logging.

## Bulk Download Support

To archive full data sets locally before ingestion, leverage the `bulk_download.py` helper:

```
python -m tools.data_pipeline.scripts.bulk_download govinfo --collection BILLS --output /data/bulk
python -m tools.data_pipeline.scripts.bulk_download openlegislation --session 2023 --output /data/bulk
```

GovInfo archives are retrieved via streaming downloads, while OpenLegislation payloads are saved as JSON snapshots using the preserved raw payload data.

## Extensibility

The package favors composition:

- Extend the SQLAlchemy schema in `scripts/schema.py` to accommodate new entities.
- Add new migration files in `migrations/` for schema evolution.
- Implement additional script modules that reuse the shared clients, models, and database helpers.

