# Congress Scripts - Migration Notice

⚠️ **These scripts are being consolidated into `tools/ingestion/congress/`**

## Current Status

This directory contains Congress.gov related scripts that should be used from the organized `tools/ingestion/congress/` directory instead.

### File in this directory:
- `fetch_congress_bulk.py` - Congress.gov bulk data fetcher

### Migration Path

For new development, use the scripts in `tools/ingestion/congress/` which include:
- `bulk_ingest_congress_gov.sh` - Complete bulk ingestion workflow with configurable sample sizes
- `bulk_ingest_congress_data.sh` - Alternative bulk ingestion approach
- `fetch_congress_members.py` - Member data fetcher
- `ingest_congress_api.py` - Congress.gov API integration

### Sample Size Configuration

The organized scripts in `tools/ingestion/congress/` support configurable sample sizes:

```bash
# Test mode with samples (default 5 samples)
FULL_DOWNLOAD=false ./tools/ingestion/congress/bulk_ingest_congress_gov.sh

# Production mode - download all data
FULL_DOWNLOAD=true ./tools/ingestion/congress/bulk_ingest_congress_gov.sh
```

## For Developers

**Recommended**: Use scripts from `tools/ingestion/congress/` for all new work.

See `tools/ingestion/README.md` for the full ingestion script organization and documentation on sample size configuration.
