# Archive: Pre-Organization Migration Files

⚠️ **This directory contains archived migration files from before the organization.**

## What's Here

These are the original migration files from `src/main/resources/sql/migrations/` before they were organized into category subdirectories.

**Total files**: 120 migrations

## Why Archive?

These files have been copied to appropriate category subdirectories:
- members/
- bills/
- federal/
- core/
- etc.

This archive is kept temporarily for reference and verification purposes.

## Verification

To verify that all migrations were properly organized, compare:
1. The files in this archive directory
2. The files in the organized subdirectories

All files should be accounted for with no data loss.

## Can This Be Deleted?

**Yes, eventually.** Once you've verified that:
1. Flyway successfully runs migrations from the new organized structure
2. No migration files are missing
3. The database schema is correct

You can safely delete this archive directory.

## Timeline

- **Created**: 2025-11-10 (during SQL migration organization)
- **Can be deleted**: After successful Flyway migration run and verification
- **Recommended retention**: Keep for at least one release cycle

## See Also

- `../README.md` - Documentation on the new organized structure
- `../../db/migration/_archive_moved_to_sql_migrations/` - Archive of duplicate federal migrations
