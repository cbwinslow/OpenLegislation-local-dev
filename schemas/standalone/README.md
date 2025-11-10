# Standalone Database Schemas

This directory contains standalone SQL schema files that are not part of the Flyway migration system.

## Files

### `database_schema.sql`
The main OpenLegislation database schema. This is a comprehensive schema file that defines the complete database structure.

**Purpose**: Reference schema or initial database setup  
**Usage**: Can be used to understand the overall database structure or for manual database initialization

### `crawling_database_schema.sql`
Schema for web crawling and data collection infrastructure.

**Purpose**: Supports web scraping and data extraction functionality  
**Usage**: Independent schema for crawling operations

### `database_queue_system.sql`
Queue system schema for asynchronous job processing.

**Purpose**: Job queue tables and management  
**Usage**: Enables distributed processing and background jobs

### `enhanced_telemetry_audit_schema.sql`
Advanced telemetry and audit logging schema.

**Purpose**: Comprehensive audit trails and system monitoring  
**Usage**: Enhanced tracking of system operations and data changes

## Relationship to Flyway Migrations

These standalone schemas are **separate from** the Flyway migrations in `src/main/resources/sql/migrations/`.

- **Flyway migrations**: Incremental, version-controlled changes applied automatically
- **Standalone schemas**: Complete schema definitions, typically for reference or manual setup

## When to Use These Files

### Use Flyway Migrations When:
- Making incremental changes to the database
- Working within the normal development workflow
- Need automatic version tracking and rollback capability

### Use Standalone Schemas When:
- Setting up a completely new database instance
- Need a reference for the complete database structure
- Working with subsystems (crawling, queue, telemetry) that may run independently

## Best Practices

1. **Don't modify these files directly** for schema changes. Use Flyway migrations instead.
2. If these schemas become outdated, regenerate them from the current database using `pg_dump` or similar tools.
3. Keep these as read-only reference documentation.

## Original Location

These files were previously in the repository root. They have been moved to `schemas/standalone/` for better organization, but the originals are kept in the root for backward compatibility.

## See Also

- `src/main/resources/sql/migrations/README.md` - Documentation on organized Flyway migrations
- `docs/backend/database.md` - Database architecture documentation
- `src/main/resources/flyway.conf.example` - Flyway configuration
