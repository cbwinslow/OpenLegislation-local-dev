# Universal Database Integration for Congress.gov Data

This document describes the universal database schema and data connector system that enables OpenLegislation to handle both state and federal legislative data in a unified manner.

## Overview

The universal database extends the existing OpenLegislation schema to support federal legislative data from congress.gov alongside existing state legislative data. This creates a "singular universal database" that can handle both data sources seamlessly.

## Architecture

### Database Schema Extensions

The universal schema adds the following key features:

1. **Data Source Column**: All existing tables now include a `data_source` column to distinguish between 'state' and 'federal' data.

2. **Federal-Specific Columns**: Added columns to existing tables for federal data:
   - `congress`: Federal congress number
   - `bill_type`: Federal bill type (H.R., S., etc.)
   - `short_title`: Federal bill short title
   - `sponsor_party`, `sponsor_state`, `sponsor_district`: Federal sponsor information

3. **Federal-Specific Tables**: New tables for federal data that doesn't map directly to state schema:
   - `federal_bill_subject`: Legislative subjects/tags
   - `federal_bill_text`: Multiple text versions per bill
   - `federal_doc_reference`: External document references
   - `federal_bill_relationship`: Bill relationships (same-as, companion bills)

### Data Flow

```
Congress.gov API → GovInfo Bulk XML → Data Connector → Universal Database
```

## Setup

### 1. Database Migration

Run the universal schema migration:

```bash
# Apply the universal schema migration
mvn flyway:migrate
```

Or manually apply the migration file:
```sql
-- Run: src/main/resources/sql/migrations/V20250921.0003__universal_bill_schema.sql
```

### 2. Database Configuration

Create a database configuration file from the template:

```bash
cp tools/db_config_template.json tools/db_config.json
```

Edit `tools/db_config.json` with your database credentials:

```json
{
  "host": "localhost",
  "port": 5432,
  "database": "openleg",
  "user": "openleg_user",
  "password": "your_password_here",
  "schema": "master"
}
```

### 3. Python Dependencies

Install required Python packages:

```bash
pip install psycopg2-binary
```

## Usage

### Bulk Data Ingestion

Use the updated bulk ingestion script:

```bash
# Set environment variables (optional)
export CONGRESS=119
export SESSION=1
export COLLECTION=BILLS
export OUTPUT_DIR=/tmp/govinfo_ingest
export DB_CONFIG=tools/db_config.json

# Run the complete pipeline
./tools/bulk_ingest_congress_gov.sh
```

This script will:
1. Download sample govinfo bulk data
2. Transform XML data using the Python connector
3. Ingest into the universal database schema
4. Verify the ingestion

### Manual Data Connector Usage

You can also run the data connector directly:

```bash
python3 tools/govinfo_data_connector.py \
    --input-dir /path/to/xml/files \
    --db-config tools/db_config.json \
    --log-level INFO
```

### Data Verification

After ingestion, verify the data:

```sql
-- Count federal vs state bills
SELECT data_source, COUNT(*) as bill_count
FROM master.bill
GROUP BY data_source;

-- View sample federal bill
SELECT bill_print_no, title, congress, bill_type, data_source
FROM master.bill
WHERE data_source = 'federal'
LIMIT 5;

-- Check federal bill subjects
SELECT b.bill_print_no, s.subject
FROM master.bill b
JOIN master.federal_bill_subject s ON b.bill_print_no = s.bill_print_no
WHERE b.data_source = 'federal'
LIMIT 10;
```

## Data Mapping

### Bill Number Conversion

Federal bill numbers are converted to match state format:
- `H.R. 123` → `H123`
- `S. 456` → `S456`
- `H.Res. 789` → `HRES789`

### Sponsor/Cosponsor Handling

Federal sponsors and cosponsors are initially stored with names as placeholders. For full functionality, implement member ID mapping:

```sql
-- Current placeholder approach
SELECT bill_print_no, session_member_id, sponsor_type
FROM master.bill_sponsor
WHERE data_source = 'federal';

-- Future: Map to actual member IDs
-- This would require a federal member mapping table
```

### Actions and Committees

Federal actions and committee references are mapped to existing tables with federal-specific metadata.

### Text Versions

Multiple text versions per bill are stored in `federal_bill_text` table, supporting different formats (HTML, XML, plain text).

## API Integration

The universal schema allows existing OpenLegislation APIs to serve both state and federal data:

```java
// Example: Query bills by data source
List<Bill> federalBills = billDao.getBillsByDataSource("federal");
List<Bill> stateBills = billDao.getBillsByDataSource("state");
```

## Performance Considerations

### Indexing

The schema includes indexes for:
- `data_source` columns for efficient filtering
- Federal-specific fields (`congress`, bill numbers)
- Foreign key relationships

### Partitioning

For large-scale deployments, consider partitioning by `data_source`:

```sql
-- Example partitioning strategy
CREATE TABLE master.bill_y2024 PARTITION OF master.bill
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

## Monitoring and Maintenance

### Data Quality Checks

```sql
-- Check for data consistency
SELECT data_source, COUNT(*) as records
FROM master.bill
GROUP BY data_source;

-- Verify federal bill relationships
SELECT
    b.bill_print_no,
    COUNT(s.*) as sponsors,
    COUNT(c.*) as cosponsors,
    COUNT(a.*) as actions
FROM master.bill b
LEFT JOIN master.bill_sponsor s ON b.bill_print_no = s.bill_print_no
LEFT JOIN master.bill_amendment_cosponsor c ON b.bill_print_no = c.bill_print_no
LEFT JOIN master.bill_amendment_action a ON b.bill_print_no = a.bill_print_no
WHERE b.data_source = 'federal'
GROUP BY b.bill_print_no
LIMIT 10;
```

### Change Logging

All federal data changes are logged using the existing change log triggers, maintaining audit trails.

## Future Enhancements

### Federal Member Mapping

Implement a federal member mapping system to convert sponsor/cosponsor names to standardized member IDs.

### Full Text Search

Extend full-text search capabilities to include federal bill content.

### API Extensions

Add federal-specific API endpoints for congress-specific queries.

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify `db_config.json` credentials
   - Ensure PostgreSQL is running and accessible

2. **XML Parsing Errors**
   - Check XML file format matches expected govinfo schema
   - Review logs for specific parsing failures

3. **Data Integrity Issues**
   - Run verification queries to check data consistency
   - Check foreign key constraints

### Logs

The data connector provides detailed logging. Increase verbosity for debugging:

```bash
python3 tools/govinfo_data_connector.py \
    --input-dir /path/to/xml \
    --db-config tools/db_config.json \
    --log-level DEBUG
```

## Support

For issues with the universal database integration:

1. Check the logs for error messages
2. Verify database schema is up to date
3. Test with sample data before full bulk processing
4. Review the data mapping documentation in `docs/data_model.md`