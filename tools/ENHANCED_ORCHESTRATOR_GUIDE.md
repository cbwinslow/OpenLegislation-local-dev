# Enhanced Ingestion Orchestrator Documentation

## Overview

The Enhanced Ingestion Orchestrator provides a unified interface for managing all data ingestion processes in OpenLegislation. It builds on the existing BaseIngestionProcess framework to provide automatic migration checking, parameter validation, and simplified execution of all data sources.

## Features

- **Unified Interface**: Single entry point for all 8 data sources
- **Automatic Migration Management**: Checks and applies database migrations automatically
- **Parameter Validation**: Validates all parameters before execution
- **Resume Capability**: Built on existing BaseIngestionProcess framework
- **Interactive Mode**: User-friendly configuration prompts
- **Status Tracking**: Real-time ingestion progress monitoring
- **Error Handling**: Comprehensive error reporting and validation

## Available Data Sources

### 1. Congress API (`congress_api`)
- **Description**: Federal legislation and committee data from congress.gov API
- **Script**: `tools/ingestion/core/ingest_federal_data.py`
- **Table**: `master.bill`
- **Key Parameters**:
  - `type`: bills or committees (default: bills)
  - `start_congress`: Starting congress number (default: 118)
  - `batch_size`: Records per batch (default: 250)

### 2. Federal Members (`federal_members`)
- **Description**: Federal member data from congress.gov API
- **Script**: `tools/ingestion/members/ingest_federal_members.py`
- **Table**: `master.federal_person`
- **Key Parameters**:
  - `api-key`: Congress.gov API key
  - `limit`: Limit number of members to process
  - `no-resume`: Start fresh instead of resuming
  - `reset`: Reset ingestion status before starting

### 3. GovInfo Bills (`govinfo_bills`)
- **Description**: Bill data from GovInfo XML files
- **Script**: `tools/ingestion/govinfo/govinfo_bill_ingestion.py`
- **Table**: `master.bill`
- **Key Parameters**:
  - `xml-dir`: Directory containing XML files (default: staging/govinfo/bills)
  - `pattern`: File patterns to match
  - `recursive`: Search directories recursively

### 4. GovInfo Agendas (`govinfo_agendas`)
- **Description**: Committee agendas from GovInfo JSON files
- **Script**: `tools/govinfo/agenda_ingestion.py`
- **Table**: `master.agenda`
- **Key Parameters**:
  - `json-dir`: Directory containing agenda JSON files
  - `limit`: Limit number of files to process

### 5. GovInfo Calendars (`govinfo_calendars`)
- **Description**: Calendar active lists from GovInfo JSON files
- **Script**: `tools/govinfo/calendar_ingestion.py`
- **Table**: `master.calendar`
- **Key Parameters**:
  - `json-dir`: Directory containing calendar JSON files
  - `limit`: Limit number of files to process

### 6. Member Data (`member_data`)
- **Description**: Member/session data from JSON files
- **Script**: `tools/ingestion/members/member_data_ingestion.py`
- **Table**: `public.session_member`
- **Key Parameters**:
  - `json-dir`: Directory containing member JSON files (default: staging/members)
  - `pattern`: File patterns to match

### 7. Bill Votes (`bill_votes`)
- **Description**: Bill vote data from JSON files
- **Script**: `tools/utilities/bill_vote_ingestion.py`
- **Table**: `master.bill_amendment_vote_info`
- **Key Parameters**:
  - `json-dir`: Directory containing vote JSON files (default: staging/govinfo/votes)
  - `pattern`: File patterns to match

### 8. Bill Status (`bill_status`)
- **Description**: Bill status/milestone data from JSON files
- **Script**: `tools/utilities/bill_status_ingestion.py`
- **Table**: `master.bill_milestone`
- **Key Parameters**:
  - `json-dir`: Directory containing status JSON files (default: staging/govinfo/status)
  - `pattern`: File patterns to match

## Usage Examples

### Basic Commands

```bash
# List all available data sources
python3 tools/enhanced_ingestion_orchestrator.py --list-sources

# Check migration status
python3 tools/enhanced_ingestion_orchestrator.py --check-migrations

# Check ingestion status
python3 tools/enhanced_ingestion_orchestrator.py --status

# Run all data sources with defaults
python3 tools/enhanced_ingestion_orchestrator.py --all
```

### Running Specific Data Sources

```bash
# Run congress API ingestion with custom parameters
python3 tools/enhanced_ingestion_orchestrator.py \
  --source congress_api \
  --start-congress 118 \
  --batch-size 100

# Run GovInfo bills ingestion
python3 tools/enhanced_ingestion_orchestrator.py \
  --source govinfo_bills \
  --xml-dir /path/to/xml/files \
  --recursive

# Run multiple specific sources
python3 tools/enhanced_ingestion_orchestrator.py \
  --source congress_api \
  --source federal_members \
  --api-key YOUR_API_KEY
```

### Migration Management

```bash
# Check what migrations are pending
python3 tools/enhanced_ingestion_orchestrator.py --check-migrations

# Run pending migrations (dry run)
python3 tools/enhanced_ingestion_orchestrator.py --dry-run-migrations

# Apply pending migrations
python3 tools/enhanced_ingestion_orchestrator.py --run-migrations
```

### Interactive Mode

```bash
# Launch interactive configuration mode
python3 tools/enhanced_ingestion_orchestrator.py --interactive
```

This will guide you through:
1. Selecting data sources to run
2. Configuring parameters for each source
3. Reviewing migration status
4. Executing the ingestion

### Testing and Validation

```bash
# Dry run (validate parameters and migrations without executing)
python3 tools/enhanced_ingestion_orchestrator.py \
  --source congress_api \
  --start-congress 118 \
  --dry-run

# Test with reset flag
python3 tools/enhanced_ingestion_orchestrator.py \
  --source member_data \
  --json-dir staging/members \
  --reset \
  --dry-run
```

## Command Line Options

### Global Options
- `--help`: Show help message
- `--all`: Run all data sources
- `--source SOURCE`: Specific data source(s) to run (can be used multiple times)
- `--check-migrations`: Check migration status
- `--run-migrations`: Run pending migrations
- `--dry-run-migrations`: Show pending migrations without applying
- `--status`: Show ingestion status
- `--interactive`: Interactive configuration mode
- `--list-sources`: List available data sources
- `--db-config DB_CONFIG`: Database configuration JSON file

### Common Parameters
- `--start-congress START_CONGRESS`: Starting congress number
- `--batch-size BATCH_SIZE`: Batch size for processing
- `--api-key API_KEY`: API key for external services
- `--xml-dir XML_DIR`: XML files directory
- `--json-dir JSON_DIR`: JSON files directory
- `--agenda-dir AGENDA_DIR`: Agenda files directory
- `--calendar-dir CALENDAR_DIR`: Calendar files directory
- `--pattern PATTERN`: File patterns to match
- `--file FILE`: Specific files to process
- `--recursive`: Search directories recursively
- `--reset`: Reset ingestion status
- `--limit LIMIT`: Limit number of records/files to process
- `--dry-run`: Simulate without making changes
- `--no-resume`: Start fresh instead of resuming

## Migration Management

The orchestrator automatically manages database migrations:

1. **Automatic Checking**: Before any ingestion, it checks for pending migrations
2. **Dependency Resolution**: Applies migrations in the correct order
3. **Safety**: Won't start ingestion if migrations fail
4. **Tracking**: Uses Flyway migration table for tracking

### Migration Files by Data Source

**Congress API & Federal Members**:
- `V20250921.0004__federal_member_schema.sql`
- `V20250921.0005__federal_member_ingestion_tracking.sql`

**GovInfo Bills**:
- `V20250921.0002__govinfo_bill_tables_expanded.sql`

## Error Handling

The orchestrator provides comprehensive error handling:

### Parameter Validation Errors
- Missing required parameters
- Invalid parameter values (e.g., negative congress numbers)
- Non-existent directories
- Invalid file patterns

### Migration Errors
- Missing migration files
- SQL execution failures
- Database connection issues

### Runtime Errors
- Script execution failures
- Database connection problems
- File system permission issues

All errors include:
- Clear description of the problem
- Context about which data source failed
- Suggestions for resolution

## Integration with Existing Framework

The orchestrator builds on existing OpenLegislation infrastructure:

### BaseIngestionProcess Integration
- Uses existing resume capability
- Leverages established error handling
- Maintains compatibility with current tracking

### GenericIngestionTracker Integration
- Provides status monitoring
- Tracks progress across all data sources
- Maintains session-based grouping

### Settings Integration
- Uses centralized configuration management
- Supports environment variables
- Integrates with existing .env file structure

## Best Practices

### 1. Before Running Ingestion
```bash
# Always check migrations first
python3 tools/enhanced_ingestion_orchestrator.py --check-migrations

# Verify data directories exist
ls -la staging/

# Check current status
python3 tools/enhanced_ingestion_orchestrator.py --status
```

### 2. Running Production Ingestion
```bash
# Use interactive mode for careful configuration
python3 tools/enhanced_ingestion_orchestrator.py --interactive

# Or run with explicit parameters
python3 tools/enhanced_ingestion_orchestrator.py \
  --source congress_api \
  --start-congress 118 \
  --batch-size 250
```

### 3. Testing and Development
```bash
# Always use dry-run first
python3 tools/enhanced_ingestion_orchestrator.py \
  --source congress_api \
  --start-congress 118 \
  --dry-run

# Test with small batches
python3 tools/enhanced_ingestion_orchestrator.py \
  --source congress_api \
  --start-congress 118 \
  --batch-size 10 \
  --dry-run
```

### 4. Monitoring Progress
```bash
# Check status during long-running ingestions
python3 tools/enhanced_ingestion_orchestrator.py --status

# Monitor specific data sources
python3 tools/enhanced_ingestion_orchestrator.py --status --source congress_api
```

## Troubleshooting

### Common Issues

1. **Migration Failures**
   - Check database connection
   - Verify migration file permissions
   - Review SQL syntax in migration files

2. **Parameter Validation Errors**
   - Ensure directories exist and are readable
   - Verify API keys are set correctly
   - Check file patterns are valid

3. **Script Execution Failures**
   - Verify Python dependencies are installed
   - Check script file permissions
   - Review script-specific requirements

4. **Database Connection Issues**
   - Verify database is running
   - Check connection parameters
   - Ensure proper permissions

### Debug Mode

For detailed debugging, you can modify the script to enable verbose logging or run individual scripts directly:

```bash
# Run individual script for debugging
python3 tools/ingestion/core/ingest_federal_data.py --help

# Check database connection
python3 -c "from tools.config.settings import settings; print(settings.db_config)"
```

## File Structure

```
tools/
├── enhanced_ingestion_orchestrator.py    # Main orchestrator script
├── config/
│   └── settings.py                       # Configuration management
└── ingestion/
    ├── core/
    │   ├── base_ingestion_process.py      # Base framework
    │   └── generic_ingestion_tracker.py   # Progress tracking
    ├── congress/
    │   └── ingest_congress_api.py         # Congress API ingestion
    ├── members/
    │   ├── ingest_federal_members.py      # Federal members
    │   └── member_data_ingestion.py       # Member data
    ├── govinfo/
    │   └── govinfo_bill_ingestion.py      # GovInfo bills
    └── utilities/
        ├── bill_vote_ingestion.py         # Bill votes
        └── bill_status_ingestion.py       # Bill status
```

This unified interface simplifies the management of all data ingestion processes while maintaining the power and flexibility of the existing BaseIngestionProcess framework.