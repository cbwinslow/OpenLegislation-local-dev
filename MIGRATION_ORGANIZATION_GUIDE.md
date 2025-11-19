# SQL Migration and Ingestion Script Organization Guide

## Overview

This guide documents the reorganization of SQL migrations and ingestion scripts to improve maintainability and clarity.

## What Changed

### SQL Migrations - Organized by Data Model

**Before**: All 125 migrations in flat directory
```
src/main/resources/sql/migrations/
├── V1__openleg.db-init.sql
├── V20190205.0412__2019_budget_pdfs.sql
├── V20200527.1011__reset_member_data.sql
├── V20250921.0004__federal_member_schema.sql
└── ... 121 more files
```

**After**: Organized into 18 category folders
```
src/main/resources/sql/migrations/
├── README.md (organization guide)
├── core/ (4 files - V1, V2, V3, base schema)
├── members/ (65 files - state legislators)
├── bills/ (17 files - legislation)
├── federal/ (8 files - Congress.gov data)
├── transcripts/ (5 files)
├── notifications/ (4 files)
├── api/ (3 files)
├── hearings/ (3 files)
├── spotcheck/ (3 files)
├── source/ (3 files - ingestion tracking)
├── audit/ (2 files)
├── indexes/ (2 files)
├── laws/ (2 files)
├── agendas/ (1 file)
├── committees/ (1 file)
├── views/ (1 file)
├── misc/ (1 file)
└── calendars/ (0 files - reserved)
```

### Duplicate Location Consolidated

**Before**: Federal migrations in two locations
- `src/main/resources/sql/migrations/` (main location)
- `src/main/resources/db/migration/` (duplicate federal migrations)

**After**: Single location with clear organization
- All migrations in `src/main/resources/sql/migrations/{category}/`
- Duplicates archived in `db/migration/_archive_moved_to_sql_migrations/`

### Ingestion Scripts - Already Organized

The ingestion scripts were already well-organized under `tools/ingestion/`:
- `congress/` - Congress.gov bulk ingestion
- `govinfo/` - GovInfo downloads  
- `members/` - Member data ingestion
- `core/` - Ingestion engine

**Added**: Documentation and migration notices
- `tools/ingestion/README.md` - Complete guide with sample size configuration
- `tools/govinfo/README.md` - Notice about consolidation
- `tools/congress/README.md` - Notice about consolidation

### Standalone Schemas Organized

**Before**: Root-level SQL files
```
/
├── database_schema.sql
├── crawling_database_schema.sql
├── database_queue_system.sql
└── enhanced_telemetry_audit_schema.sql
```

**After**: Organized with documentation
```
schemas/standalone/
├── README.md (explains purpose and usage)
├── database_schema.sql
├── crawling_database_schema.sql
├── database_queue_system.sql
└── enhanced_telemetry_audit_schema.sql
```

## Why This Organization?

### Benefits

1. **Easier Navigation**: Find migrations by data model instead of date
2. **Better Context**: Related migrations grouped together
3. **Clearer Purpose**: Folder names indicate what each migration affects
4. **Reduced Confusion**: No duplicate migration locations
5. **Maintainability**: Easier to add new migrations in the right place

### Examples

Need to update member data? Look in `members/`  
Adding federal features? Add to `federal/`  
Fixing an index? Go to `indexes/`

## Flyway Compatibility

✅ **No Configuration Changes Required**

Flyway automatically scans subdirectories when using `classpath:` locations. The existing configuration works perfectly:

```properties
# flyway.conf
flyway.locations = classpath:sql/migrations
```

Flyway will find and execute all migrations in subdirectories in version order, regardless of which folder they're in.

## Sample Size Configuration for Ingestion

✅ **Already Configurable - No Changes Needed**

All ingestion scripts support flexible sample sizes via command-line flags:

### GovInfo Bulk Downloads

```bash
# Test mode - download samples (default: 3 per subdirectory)
python3 tools/ingestion/govinfo/fetch_govinfo_bulk.py --samples 5

# Production mode - download all files
python3 tools/ingestion/govinfo/fetch_govinfo_bulk.py --full
```

### Congress.gov Bulk Ingestion

```bash
# Test mode (default: 5 samples)
FULL_DOWNLOAD=false ./tools/ingestion/congress/bulk_ingest_congress_gov.sh

# Production mode
FULL_DOWNLOAD=true ./tools/ingestion/congress/bulk_ingest_congress_gov.sh
```

### Configuration Options

Sample sizes can be controlled via:
- Command-line flags: `--samples N` or `--full`
- Environment variables: `FULL_DOWNLOAD=true`
- Script parameters: Passed directly to download functions

**No hardcoded limits** were found that restrict production usage.

## For Developers

### Adding New Migrations

1. **Determine Category**: Which data model does your migration affect?
   - State members → `members/`
   - Federal data → `federal/`
   - Bills/legislation → `bills/`
   - System infrastructure → `core/`, `audit/`, `indexes/`, etc.

2. **Name Migration**: Follow Flyway convention
   ```
   V{YYYYMMDD}.{HHMM}__{description}.sql
   ```
   Example: `V20251110.1430__add_sponsor_tracking.sql`

3. **Place in Folder**: 
   ```bash
   src/main/resources/sql/migrations/{category}/V{version}__{desc}.sql
   ```

4. **Add Description**: Include comments at the top explaining the change

### Example

```sql
-- Migration: Add sponsor tracking to federal bills
-- Adds sponsor_id and sponsor_name columns to federal_bills table
-- Related to GitHub issue #123

ALTER TABLE federal_bills 
  ADD COLUMN sponsor_id INTEGER REFERENCES federal_members(id),
  ADD COLUMN sponsor_name VARCHAR(255);

CREATE INDEX idx_federal_bills_sponsor ON federal_bills(sponsor_id);
```

### Running Migrations

```bash
# Compile and run all pending migrations
mvn compile flyway:migrate

# Check migration status
mvn flyway:info

# Validate migrations
mvn flyway:validate
```

## Archive Directories

Two archive directories were created during reorganization:

### 1. `sql/migrations/_archive_pre_organization/`
- Contains original 120 migration files before organization
- Can be deleted after successful Flyway run and verification
- Kept for reference and rollback capability

### 2. `db/migration/_archive_moved_to_sql_migrations/`
- Contains duplicate 5 federal migrations from old location
- Can be deleted after verification
- No longer used by Flyway

**Recommended**: Keep archives for at least one release cycle before deletion.

## Verification Steps

To verify the organization is correct:

1. **Check File Count**: Should have 125 migrations total across 18 folders
   ```bash
   find src/main/resources/sql/migrations -name "V*.sql" -type f | wc -l
   ```
   Expected: 125

2. **Run Flyway Info**: Check all migrations are detected
   ```bash
   mvn flyway:info
   ```

3. **Run Migrations**: Execute on test database
   ```bash
   mvn compile flyway:migrate
   ```

4. **Verify Schema**: Check that all tables/columns exist as expected

5. **Delete Archives**: Once verified, remove `_archive_*` directories

## Documentation References

- `src/main/resources/sql/migrations/README.md` - Detailed migration organization
- `src/main/resources/db/migration/README.md` - Old location deprecation notice
- `schemas/standalone/README.md` - Standalone schema documentation
- `tools/ingestion/README.md` - Ingestion script guide and sample configuration
- `.github/copilot-instructions.md` - Updated with new paths

## Timeline

- **Date**: 2025-11-10
- **Issue**: Organize SQL migrations and ingestion scripts by data model
- **Approach**: Category-based organization with comprehensive documentation
- **Status**: Complete, pending verification on live database

## Questions?

See the individual README files in each directory for more details:
- SQL Migrations: `src/main/resources/sql/migrations/README.md`
- Ingestion Scripts: `tools/ingestion/README.md`
- Standalone Schemas: `schemas/standalone/README.md`
