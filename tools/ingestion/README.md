# Data Ingestion Scripts Organization

This directory contains all data ingestion scripts organized by data source.

## Directory Structure

### Data Source Directories

- **`congress/`** - Congress.gov bulk data ingestion
  - `bulk_ingest_congress_gov.sh` - Main bulk ingestion workflow
  - `bulk_ingest_congress_data.sh` - Alternative bulk ingestion script
  - `fetch_congress_members.py` - Member data fetcher
  - `ingest_congress_api.py` - Congress.gov API ingestion

- **`govinfo/`** - GovInfo.gov bulk data downloads
  - `fetch_govinfo_bulk.py` - Bulk XML downloader with sample/full modes
  - `bulk_ingest_govinfo.py` - Bulk ingestion orchestrator
  - `download_govinfo_samples.sh` - Quick sample download script
  - `govinfo_bill_ingestion.py` - Bill-specific ingestion
  - `govinfo_enumerate.sh` - Collection enumeration
  - Various parsers and connectors

- **`members/`** - Legislative member data ingestion
  - `ingest_federal_members.py` - Federal member ingestion
  - `fetch_govinfo_members.py` - GovInfo member fetcher
  - `member_data_ingestion.py` - Generic member data processor
  - `member_ingestion_tracker.py` - Ingestion progress tracking
  - `ingest_member_tweets.py` - Social media ingestion

- **`core/`** - Core ingestion engine and utilities
  - `ingestion_engine.py` - Main ingestion orchestration
  - `ingestion_scheduler.py` - Scheduled ingestion management
  - `ingestion_worker.py` - Worker processes
  - `generic_ingestion_tracker.py` - Universal progress tracking
  - `validate_ingestion.py` - Data validation
  - `resume_manager.py` - Resume capability for interrupted jobs
  - Various progress monitors and state management

## Sample Size Configuration

All ingestion scripts support configurable sample sizes for testing vs production:

### fetch_govinfo_bulk.py
```bash
# Download samples (default: 3 per subdirectory)
python3 tools/ingestion/govinfo/fetch_govinfo_bulk.py --samples 5

# Download all files (full production mode)
python3 tools/ingestion/govinfo/fetch_govinfo_bulk.py --full
```

### bulk_ingest_congress_gov.sh
```bash
# Sample mode (default)
FULL_DOWNLOAD=false ./tools/ingestion/congress/bulk_ingest_congress_gov.sh

# Full production mode
FULL_DOWNLOAD=true ./tools/ingestion/congress/bulk_ingest_congress_gov.sh
```

## Configuration Files

Most ingestion scripts accept a database configuration file:
```bash
--db-config tools/db_config.json
```

See `tools/db_config_template.json` for the configuration format.

## Adding New Ingestion Scripts

1. Determine the appropriate data source directory
2. Follow existing naming conventions
3. Support `--samples` or equivalent flag for testing
4. Support `--full` or equivalent flag for production
5. Add progress tracking using `generic_ingestion_tracker.py`
6. Document configuration options

## Related Directories

- **`tools/federal_ingest/`** - Federal data ingestion Python package (structured library)
- **`tools/utilities/`** - Standalone utility scripts (demos, production helpers)
- **`tools/tests/`** - Integration tests for ingestion systems

## Migration Notes

Scripts were previously scattered across:
- `tools/` (root level)
- `tools/govinfo/`
- `tools/congress/`
- `tools/utilities/`

All ingestion scripts are now consolidated under `tools/ingestion/` for better organization and maintainability.
