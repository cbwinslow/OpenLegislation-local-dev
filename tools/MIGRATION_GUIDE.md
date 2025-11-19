# Migration Guide: Tools Directory Reorganization

## Overview
The tools directory has been reorganized from a flat structure with 100+ files to a hierarchical structure organized by function. This guide helps you update any scripts or workflows that reference the old paths.

## Quick Reference: Old Path → New Path

### Configuration Files
```
tools/settings.py              → tools/config/settings.py
tools/db_config.py             → tools/config/db_config.py
tools/db_config.json           → tools/config/db_config.json
tools/db_config_template.json  → tools/config/db_config_template.json
tools/pyproject.toml           → tools/config/pyproject.toml
```

### Ingestion Scripts - GovInfo
```
tools/fetch_govinfo_bulk.py           → tools/ingestion/govinfo/fetch_govinfo_bulk.py
tools/govinfo_api.py                  → tools/ingestion/govinfo/govinfo_api.py
tools/govinfo_bill_ingestion.py       → tools/ingestion/govinfo/govinfo_bill_ingestion.py
tools/govinfo_data_connector.py       → tools/ingestion/govinfo/govinfo_data_connector.py
tools/bulk_ingest_govinfo.py          → tools/ingestion/govinfo/bulk_ingest_govinfo.py
tools/download_govinfo_samples.sh     → tools/ingestion/govinfo/download_govinfo_samples.sh
```

### Ingestion Scripts - Congress
```
tools/fetch_congress_members.py       → tools/ingestion/congress/fetch_congress_members.py
tools/ingest_congress_api.py          → tools/ingestion/congress/ingest_congress_api.py
tools/bulk_ingest_congress_gov.sh     → tools/ingestion/congress/bulk_ingest_congress_gov.sh
tools/bulk_ingest_congress_data.sh    → tools/ingestion/congress/bulk_ingest_congress_data.sh
```

### Ingestion Scripts - Members
```
tools/fetch_govinfo_members.py        → tools/ingestion/members/fetch_govinfo_members.py
tools/ingest_federal_members.py       → tools/ingestion/members/ingest_federal_members.py
tools/member_data_ingestion.py        → tools/ingestion/members/member_data_ingestion.py
tools/member_ingestion_tracker.py     → tools/ingestion/members/member_ingestion_tracker.py
tools/ingest_member_tweets.py         → tools/ingestion/members/ingest_member_tweets.py
tools/member_utils.py                 → tools/ingestion/members/member_utils.py
```

### Ingestion Scripts - Core
```
tools/base_ingestion_process.py       → tools/ingestion/core/base_ingestion_process.py
tools/generic_ingestion_tracker.py    → tools/ingestion/core/generic_ingestion_tracker.py
tools/ingestion_progress.py           → tools/ingestion/core/ingestion_progress.py
tools/ingestion_scheduler.py          → tools/ingestion/core/ingestion_scheduler.py
tools/manage_all_ingestion.py         → tools/ingestion/core/manage_all_ingestion.py
tools/resume_manager.py               → tools/ingestion/core/resume_manager.py
tools/validate_ingestion.py           → tools/ingestion/core/validate_ingestion.py
```

### Installation Scripts
```
tools/install_*.sh                    → tools/installation/install_*.sh
```

### Test Files
```
tools/test_*.py                       → tools/tests/test_*.py
tools/test_*.sh                       → tools/tests/test_*.sh
```

### Utility Scripts
```
tools/bill_status_ingestion.py        → tools/utilities/bill_status_ingestion.py
tools/bill_vote_ingestion.py          → tools/utilities/bill_vote_ingestion.py
tools/diagnostic_check.py             → tools/utilities/diagnostic_check.py
tools/production_ingest.sh            → tools/utilities/production_ingest.sh
```

### Linear Tools
```
tools/linear_api_import.py            → tools/linear_tools/linear_api_import.py
tools/apply_tracker_migration.py      → tools/linear_tools/apply_tracker_migration.py
```

### Documentation
```
tools/README*.md                      → tools/documentation/README*.md
tools/SETUP_*.md                      → tools/documentation/SETUP_*.md
```

### Archived Data
```
tools/linear_import_run_*.json        → tools/archived_data/ (gitignored)
tools/batches/                        → tools/archived_data/batches/
tools/ingestion_log.json              → Removed (should be gitignored)
```

## Python Import Changes

All Python imports have been automatically updated. If you have external scripts that import from tools, update them as follows:

### Old Imports
```python
from tools.settings import settings
from tools.db_config import get_connection_string
from tools.fetch_congress_members import fetch_all_members
from tools.govinfo_bill_ingestion import ingest_bills
```

### New Imports
```python
from tools.config.settings import settings
from tools.config.db_config import get_connection_string
from tools.ingestion.congress.fetch_congress_members import fetch_all_members
from tools.ingestion.govinfo.govinfo_bill_ingestion import ingest_bills
```

## Shell Script Changes

If you have shell scripts that reference old paths:

```bash
# Old
python3 tools/fetch_govinfo_bulk.py

# New
python3 tools/ingestion/govinfo/fetch_govinfo_bulk.py
```

## Backward Compatibility

There is no backward compatibility layer. All references must be updated to the new paths.

## Benefits

1. **Better Organization**: Related files are grouped together
2. **Easier Navigation**: Find files by purpose/category
3. **Reduced Clutter**: Old data files archived
4. **Clearer Dependencies**: Import paths show relationships
5. **Scalability**: Easy to add new scripts in the right place

## Getting Help

- See `README_ORGANIZATION.md` for the full directory structure
- Check `documentation/` folder for specific guides
- Run `tree -L 2 tools/` to see the current structure
