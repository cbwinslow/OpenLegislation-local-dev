# SQL Migrations Organization

This directory contains all Flyway database migrations organized by data model.

## Directory Structure

Each subdirectory contains migrations related to a specific data model or functional area:

### Data Models
- **`members/`** - Member-related tables and data (state legislators, incumbents, resignations)
  - Contains 65 migrations for NY State Senate and Assembly members
  
- **`bills/`** - Bill-related tables (votes, sponsors, amendments, budget bills)
  - Contains 17 migrations for state bill data
  
- **`federal/`** - Federal legislative data (Congress.gov, GovInfo)
  - Contains 8 migrations for federal bills, members, and bulk data ingestion
  - Includes social media posts and tracking tables
  
- **`laws/`** - Law documents and legal code
  - Contains 2 migrations for law parsing and dummy data
  
- **`agendas/`** - Committee agendas and meeting information
  - Contains 1 migration for agenda alerts
  
- **`calendars/`** - Legislative calendars
  - Currently empty, reserved for future calendar-related migrations
  
- **`committees/`** - Committee structure and membership
  - Contains 1 migration for committee schema changes
  
- **`transcripts/`** - Session transcripts
  - Contains 5 migrations for transcript schema and types
  
- **`hearings/`** - Public hearings
  - Contains 3 migrations for hearing schema and comments

### System & Infrastructure
- **`core/`** - Core database schema and initial data
  - Contains 4 migrations including V1, V2, V3 (initial schema) and V9999 (master combined)
  - These are foundational migrations that establish the base database structure
  
- **`source/`** - Source document ingestion and tracking
  - Contains 3 migrations for document tables and generic ingestion tracking
  
- **`audit/`** - Audit logging and tracking
  - Contains 2 migrations for audit tables and triggers
  
- **`indexes/`** - Database performance indexes
  - Contains 2 migrations for index creation and optimization
  
- **`views/`** - Database views and PL/SQL
  - Contains 1 migration for federal member views

### Application Features
- **`api/`** - API user management and request tracking
  - Contains 3 migrations for API users and request indexes
  
- **`notifications/`** - Notification and subscription system
  - Contains 4 migrations for alerts and user subscriptions
  
- **`spotcheck/`** - Data quality and spotcheck system
  - Contains 3 migrations for mismatch tracking and content types

### Other
- **`misc/`** - Miscellaneous migrations that don't fit other categories
  - Contains 1 migration for foreign key refactoring

## Migration Naming Convention

Migrations follow Flyway's versioned migration naming pattern:
```
V{YYYYMMDD}.{HHMM}__{description}.sql
```

Example: `V20250921.0001__add_source_documents_table.sql`

## Adding New Migrations

1. Determine which data model your migration affects
2. Create the migration file in the appropriate subdirectory
3. Follow the naming convention above
4. Include descriptive comments at the top of the file

## Note on Federal Migrations

Federal data migrations were previously in `src/main/resources/db/migration/` but have been consolidated here under the `federal/` directory for consistency.

## Migration Execution

Flyway will execute migrations from all subdirectories in version order, regardless of which folder they're in. The folder structure is purely for organizational purposes and maintainability.
