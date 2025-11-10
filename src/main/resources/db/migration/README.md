# Migration Directory Deprecated

⚠️ **This directory is deprecated and should no longer be used.**

All SQL migrations have been consolidated into:
```
src/main/resources/sql/migrations/
```

The migrations that were previously in this directory have been moved to:
```
src/main/resources/sql/migrations/federal/
```

## Why the Change?

1. **Consistency**: All migrations are now in one location regardless of data source
2. **Organization**: Migrations are organized by data model (bills, members, federal, etc.)
3. **Maintainability**: Easier to find and manage related migrations
4. **No Duplication**: Prevents having multiple migration locations

## Flyway Configuration

Flyway is configured to scan `sql/migrations` and all its subdirectories, so the organized structure does not affect migration execution order or functionality.

See `src/main/resources/flyway.conf.example` for the configuration:
```
flyway.locations = classpath:sql/migrations
```

## For Developers

If you need to add new migrations:
1. Determine the appropriate data model category (bills, members, federal, etc.)
2. Create your migration file in the corresponding subdirectory under `sql/migrations/`
3. Follow the naming convention: `V{YYYYMMDD}.{HHMM}__{description}.sql`

See `src/main/resources/sql/migrations/README.md` for full documentation on the organized structure.
