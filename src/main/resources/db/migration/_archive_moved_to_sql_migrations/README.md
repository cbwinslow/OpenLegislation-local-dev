# Archive: Federal Migrations Moved to sql/migrations

⚠️ **This directory contains archived duplicate migration files.**

## What's Here

These are the original federal migration files that were in `src/main/resources/db/migration/` before consolidation.

**Files archived**:
- V20250928.0001__ingestion_optimizations.sql
- V20250928.0002__federal_social_media_posts.sql
- V20250929.0001__federal_bills_table.sql
- V20250929.0001__federal_data_model.sql
- V20250930.0001__federal_all_tables.sql

## New Location

All these migrations have been moved to:
```
src/main/resources/sql/migrations/federal/
```

This consolidates all migrations in one location organized by data model.

## Flyway Configuration

The Flyway configuration now points to `sql/migrations` exclusively:
```
flyway.locations = classpath:sql/migrations
```

This directory (`db/migration`) is no longer used by Flyway.

## Can This Be Deleted?

**Yes, eventually.** Once you've verified that:
1. All migrations run successfully from the new location
2. The database schema is correct
3. No migration files are missing

You can safely delete this archive directory.

## Timeline

- **Created**: 2025-11-10 (during SQL migration organization)
- **Can be deleted**: After successful Flyway migration run and verification
- **Recommended retention**: Keep for at least one release cycle

## See Also

- `../README.md` - Deprecation notice for this directory
- `../../sql/migrations/README.md` - Documentation on the new organized structure
- `../../sql/migrations/federal/` - New location of these migrations
