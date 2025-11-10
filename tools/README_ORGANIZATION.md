# Tools Directory Organization

This directory has been reorganized for better clarity and maintainability. Below is the new structure:

## 📁 Directory Structure

### `ingestion/` - Data Ingestion Scripts
Organized by data source for easy navigation:

- **`govinfo/`** - GovInfo.gov ingestion scripts
  - `fetch_govinfo_bulk.py` - Bulk data fetching from GovInfo
  - `govinfo_api.py` - GovInfo API client
  - `govinfo_bill_ingestion.py` - Bill-specific ingestion
  - `govinfo_data_connector.py` - Data connector utilities
  - `bulk_ingest_govinfo.py` - Bulk ingestion orchestrator
  - Shell scripts for enumeration and sample downloads

- **`congress/`** - Congress.gov ingestion scripts
  - `fetch_congress_members.py` - Congressional member data
  - `ingest_congress_api.py` - Congress.gov API ingestion
  - `bulk_ingest_congress_*.sh` - Bulk ingestion shell scripts

- **`members/`** - Member data ingestion
  - `fetch_govinfo_members.py` - Member data from GovInfo
  - `ingest_federal_members.py` - Federal member ingestion
  - `member_data_ingestion.py` - Member data processing
  - `member_ingestion_tracker.py` - Track ingestion progress
  - `ingest_member_tweets.py` - Social media ingestion

- **`core/`** - Core ingestion infrastructure
  - `base_ingestion_process.py` - Base classes for ingestion
  - `generic_ingestion_tracker.py` - Generic tracking system
  - `ingestion_progress.py` - Progress monitoring
  - `ingestion_scheduler.py` - Scheduling utilities
  - `manage_all_ingestion.py` - Centralized management
  - `resume_manager.py` - Resume interrupted ingestions
  - `validate_ingestion.py` - Validation utilities

### `installation/` - Infrastructure Setup Scripts
Scripts for installing and configuring system components:
- `install_core_app.sh` - Core application setup
- `install_elasticsearch.sh` - Elasticsearch installation
- `install_postgres.sh` - PostgreSQL setup
- `install_tomcat.sh` - Tomcat server setup
- `install_monitoring.sh` - Monitoring tools
- And more infrastructure scripts...

### `config/` - Configuration Files
Centralized configuration management:
- `settings.py` - Application settings
- `db_config.py` - Database configuration
- `db_config.json` - Database config (JSON)
- `db_config_template.json` - Config template
- `pyproject.toml` - Python project configuration

### `tests/` - Test Files
All test scripts and test data:
- `test_govinfo_ingestion.py`
- `test_member_ingestion.py`
- `test_comprehensive_suite.py`
- `test_end_to_end.py`
- And more test files...

### `utilities/` - Utility Scripts
Miscellaneous utility scripts:
- `bill_status_ingestion.py`
- `bill_vote_ingestion.py`
- `diagnostic_check.py`
- `production_ingest.sh`
- `federal_ingestion_demo.sh`
- And more utility scripts...

### `linear_tools/` - Linear Project Management Tools
Scripts for Linear integration and project tracking:
- `linear_api_import.py`
- `linear_import_batches.py`
- `apply_tracker_migration.py`
- `tasks_to_commits.py`

### `documentation/` - Tools Documentation
Documentation specific to the tools directory:
- `README.md` - Main tools documentation
- `README_member_ingestion.md` - Member ingestion guide
- `README_fetch_govinfo.md` - GovInfo fetching guide
- `README_universal_database.md` - Database documentation
- `SETUP_BULK_INGEST.md` - Bulk ingestion setup

### `archived_data/` - Historical Data Files
Old data files and logs kept for reference:
- Linear import run logs
- Old batch CSV files
- Historical ingestion logs
- Legacy data structures

**Note:** This directory is gitignored to prevent bloat in the repository.

### Existing Specialized Directories
These directories were already well-organized and remain unchanged:

- **`data_pipeline/`** - Data pipeline infrastructure
  - `clients/` - API clients (Congress, GovInfo, OpenStates)
  - `models/` - Data models
  - `scripts/` - Pipeline scripts
  - `migrations/` - Database migrations

- **`federal_ingest/`** - Federal data ingestion system
  - `cli/` - Command-line interfaces
  - `clients/` - Specialized federal data clients

- **`govdata_ingest/`** - Government data ingestion utilities

- **`embeddings/`** - Vector embeddings and semantic search

- **`research/`** - Reproducible analysis pipelines

- **`schemas/`** - Data schemas and validation

- **`storage/`** - Data storage utilities

- **`testing/`** - Testing infrastructure

- **`govinfo/`** - Additional GovInfo utilities

## 🎯 Key Benefits of This Organization

1. **Clear Separation of Concerns** - Ingestion, installation, testing, and utilities are now clearly separated
2. **Easy Navigation** - Find scripts by their purpose (govinfo, congress, members, etc.)
3. **Reduced Clutter** - Old data files moved to archived_data/
4. **Better Documentation** - READMEs grouped in documentation folder
5. **Maintainable** - Easier to add new scripts in the right location

## 🔍 Finding Scripts

To find a specific script:
- **Ingestion scripts**: Look in `ingestion/{source}/`
- **Setup/install scripts**: Look in `installation/`
- **Tests**: Look in `tests/`
- **Documentation**: Look in `documentation/`
- **Config files**: Look in `config/`

## 📝 Adding New Scripts

When adding new scripts, please place them in the appropriate directory:
- New ingestion script → `ingestion/{source}/`
- New installation script → `installation/`
- New test → `tests/`
- New utility → `utilities/`
- New documentation → `documentation/`
