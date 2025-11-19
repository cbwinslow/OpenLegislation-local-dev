# GovInfo Scripts - Migration Notice

⚠️ **These scripts are being consolidated into `tools/ingestion/govinfo/`**

## Current Status

This directory contains some GovInfo-related scripts that have not yet been fully migrated to the organized `tools/ingestion/govinfo/` directory.

### Files in this directory:
- `agenda_ingestion.py` - Agenda-specific ingestion
- `calendar_ingestion.py` - Calendar-specific ingestion  
- `download_govinfo_bulk.sh` - Bulk download script (duplicate of tools/ingestion/govinfo/download_govinfo_samples.sh)
- `govinfo_bill_ingestion.py` - Bill ingestion (also exists in tools/ingestion/govinfo/)
- `models.py` - Data models
- `persistence.py` - Database persistence utilities

### Migration Path

For new development, use the scripts in `tools/ingestion/govinfo/` which include:
- `fetch_govinfo_bulk.py` - Enhanced bulk downloader with configurable samples
- `bulk_ingest_govinfo.py` - Main bulk ingestion orchestrator
- `govinfo_data_connector.py` - Data transformation and mapping
- `govinfo_api.py` - GovInfo API client
- Additional parsers and utilities

### Why Two Locations?

The `tools/ingestion/` directory structure is the new organized approach. These older scripts remain here temporarily for backward compatibility but should be consolidated.

## For Developers

**Recommended**: Use scripts from `tools/ingestion/govinfo/` for all new work.

If you need functionality from this directory:
1. Check if equivalent functionality exists in `tools/ingestion/govinfo/`
2. Consider porting unique functionality to the new location
3. Update references to use the consolidated location

See `tools/ingestion/README.md` for the full ingestion script organization.
