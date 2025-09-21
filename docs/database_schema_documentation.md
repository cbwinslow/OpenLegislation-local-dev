# OpenLegislation Database Schema Documentation

## Overview

The OpenLegislation database uses a universal schema that supports both state and federal legislative data. The schema is designed to handle complex legislative workflows while maintaining data integrity and performance.

## Architecture

### Multi-Tenant Design
- **Schema**: `master` (contains all legislative data)
- **Data Sources**: `state` and `federal` legislative bodies
- **Universal Tables**: Support both state and federal data with source discrimination

### Key Design Principles
- **Normalized Structure**: Reduces redundancy and improves consistency
- **Temporal Data**: Tracks changes over time with full audit trails
- **Extensible**: Easy to add new legislative features
- **Performance Optimized**: Indexed for common query patterns

## Core Tables

### Bill Tables

#### `master.bill`
Primary bill information table.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `bill_print_no` | TEXT | Bill number (e.g., "S123", "A456") | Primary Key |
| `bill_session_year` | SMALLINT | Session year (e.g., 2023) | Primary Key |
| `title` | TEXT | Bill title | Not Null |
| `summary` | TEXT | Bill summary | |
| `data_source` | TEXT | 'state' or 'federal' | Check constraint |
| `congress` | INTEGER | Congress number (federal only) | |
| `bill_type` | TEXT | Bill type (HR, S, A, etc.) | |
| `short_title` | TEXT | Short title | |
| `sponsor_party` | TEXT | Primary sponsor party | |
| `sponsor_state` | TEXT | Primary sponsor state | |
| `sponsor_district` | TEXT | Primary sponsor district | |
| `status` | TEXT | Current status | |
| `committee` | TEXT | Committee assignment | |
| `law_code` | TEXT | Resulting law code | |
| `law_chapter` | TEXT | Law chapter | |
| `same_as` | TEXT | Same-as bill reference | |
| `created_date_time` | TIMESTAMP | Creation timestamp | Default now() |
| `last_fragment_id` | TEXT | Last update fragment | |

#### `master.bill_amendment`
Bill amendment information.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `bill_print_no` | TEXT | Bill number | Primary Key (FK) |
| `bill_session_year` | SMALLINT | Session year | Primary Key (FK) |
| `bill_amend_version` | CHAR(1) | Amendment version | Primary Key |
| `data_source` | TEXT | Data source | Check constraint |
| `version_id` | TEXT | External version ID | |
| `memo` | TEXT | Amendment memo | |
| `full_text` | TEXT | Full amendment text | |
| `created_date_time` | TIMESTAMP | Creation timestamp | Default now() |

#### `master.bill_text`
Bill text content (deprecated - use bill_amendment).

### Sponsor Tables

#### `master.bill_sponsor`
Bill sponsors and cosponsors.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `bill_print_no` | TEXT | Bill number | Primary Key (FK) |
| `bill_session_year` | SMALLINT | Session year | Primary Key (FK) |
| `session_member_id` | TEXT | Member identifier | Primary Key |
| `data_source` | TEXT | Data source | Check constraint |
| `sponsor_type` | TEXT | 'sponsor', 'cosponsor', 'multisponsor' | Check constraint |
| `created_date_time` | TIMESTAMP | Creation timestamp | Default now() |

#### `master.bill_amendment_cosponsor`
Amendment-specific cosponsors.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `bill_print_no` | TEXT | Bill number | Primary Key (FK) |
| `bill_session_year` | SMALLINT | Session year | Primary Key (FK) |
| `bill_amend_version` | CHAR(1) | Amendment version | Primary Key (FK) |
| `session_member_id` | TEXT | Member identifier | Primary Key |
| `data_source` | TEXT | Data source | Check constraint |
| `sponsor_type` | TEXT | Sponsor type | Default 'cosponsor' |

### Action Tables

#### `master.bill_amendment_action`
Legislative actions on bills.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `bill_print_no` | TEXT | Bill number | Primary Key (FK) |
| `bill_session_year` | SMALLINT | Session year | Primary Key (FK) |
| `bill_amend_version` | CHAR(1) | Amendment version | Primary Key (FK) |
| `sequence_no` | INTEGER | Action sequence number | Primary Key |
| `effect_date` | DATE | Action date | |
| `chamber` | TEXT | Chamber (ASSEMBLY, SENATE) | |
| `text` | TEXT | Action description | Not Null |
| `data_source` | TEXT | Data source | Check constraint |
| `action_type` | TEXT | Action type code | |
| `created_date_time` | TIMESTAMP | Creation timestamp | Default now() |

### Committee Tables

#### `master.bill_committee`
Committee assignments and referrals.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `bill_print_no` | TEXT | Bill number | Primary Key (FK) |
| `bill_session_year` | SMALLINT | Session year | Primary Key (FK) |
| `committee_name` | TEXT | Committee name | Primary Key |
| `action_date` | DATE | Assignment date | |
| `data_source` | TEXT | Data source | Check constraint |
| `created_date_time` | TIMESTAMP | Creation timestamp | Default now() |

### Vote Tables

#### `master.bill_vote`
Bill vote records.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `vote_id` | TEXT | Vote identifier | Primary Key |
| `bill_print_no` | TEXT | Bill number | Foreign Key |
| `bill_session_year` | SMALLINT | Session year | Foreign Key |
| `vote_date` | DATE | Vote date | |
| `vote_type` | TEXT | Vote type | |
| `committee` | TEXT | Committee name | |
| `chamber` | TEXT | Chamber | |
| `ayes` | INTEGER | Ayes count | |
| `nays` | INTEGER | Nays count | |
| `abstains` | INTEGER | Abstains count | |
| `excused` | INTEGER | Excused count | |
| `data_source` | TEXT | Data source | Check constraint |

#### `master.bill_vote_roll`
Individual vote records.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `vote_id` | TEXT | Vote ID | Primary Key (FK) |
| `session_member_id` | TEXT | Member ID | Primary Key |
| `vote` | TEXT | Vote value (Yea, Nay, etc.) | |
| `data_source` | TEXT | Data source | Check constraint |

## Federal-Specific Tables

### Member Tables

#### `master.federal_person`
Federal person biographical information.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | BIGSERIAL | Person ID | Primary Key |
| `bioguide_id` | TEXT | Bioguide identifier | Unique |
| `full_name` | TEXT | Full name | Not Null |
| `first_name` | TEXT | First name | |
| `middle_name` | TEXT | Middle name | |
| `last_name` | TEXT | Last name | |
| `suffix` | TEXT | Name suffix | |
| `nickname` | TEXT | Nickname | |
| `birth_year` | INTEGER | Birth year | |
| `death_year` | INTEGER | Death year | |
| `gender` | TEXT | Gender (M/F) | |
| `created_at` | TIMESTAMP | Creation timestamp | Default now() |
| `updated_at` | TIMESTAMP | Last update | Default now() |

#### `master.federal_member`
Federal member political information.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | BIGSERIAL | Member ID | Primary Key |
| `person_id` | INTEGER | Person ID | Foreign Key |
| `chamber` | TEXT | House/Senate | Not Null |
| `state` | TEXT | State code | |
| `district` | TEXT | District number | |
| `party` | TEXT | Party (D/R/I) | |
| `current_member` | BOOLEAN | Currently serving | Default true |
| `created_at` | TIMESTAMP | Creation timestamp | Default now() |
| `updated_at` | TIMESTAMP | Last update | Default now() |

#### `master.federal_member_term`
Federal member terms served.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | BIGSERIAL | Term ID | Primary Key |
| `member_id` | INTEGER | Member ID | Foreign Key |
| `congress` | INTEGER | Congress number | Not Null |
| `start_year` | INTEGER | Term start year | |
| `end_year` | INTEGER | Term end year | |
| `party` | TEXT | Party during term | |
| `state` | TEXT | State during term | |
| `district` | TEXT | District during term | |
| `chamber` | TEXT | Chamber during term | |
| `created_at` | TIMESTAMP | Creation timestamp | Default now() |

### Social Media Tables

#### `master.federal_member_social_media`
Federal member social media accounts.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | BIGSERIAL | Social media ID | Primary Key |
| `member_id` | INTEGER | Member ID | Foreign Key |
| `platform` | TEXT | Platform (twitter, facebook, etc.) | Not Null |
| `handle` | TEXT | Account handle | |
| `url` | TEXT | Full URL | |
| `is_official` | BOOLEAN | Official account | Default true |
| `created_at` | TIMESTAMP | Creation timestamp | Default now() |
| `updated_at` | TIMESTAMP | Last update | Default now() |

### Content Tables

#### `master.federal_bill_subject`
Bill legislative subjects.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | BIGSERIAL | Subject ID | Primary Key |
| `bill_print_no` | TEXT | Bill number | Foreign Key |
| `bill_session_year` | SMALLINT | Session year | Foreign Key |
| `subject` | TEXT | Subject tag | Not Null |
| `created_date_time` | TIMESTAMP | Creation timestamp | Default now() |

#### `master.federal_bill_text`
Federal bill text versions.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | BIGSERIAL | Text ID | Primary Key |
| `bill_print_no` | TEXT | Bill number | Foreign Key |
| `bill_session_year` | SMALLINT | Session year | Foreign Key |
| `bill_amend_version` | CHAR(1) | Amendment version | Foreign Key |
| `version_id` | TEXT | Version identifier | Not Null |
| `text_format` | TEXT | Format (html/xml/plain) | Check constraint |
| `content` | TEXT | Text content | |
| `created_date_time` | TIMESTAMP | Creation timestamp | Default now() |

## Relationships

### Entity Relationship Diagram

```
┌─────────────────┐     ┌──────────────────┐
│  federal_person │     │ federal_member   │
│                 │     │                  │
│  id (PK)        │◄────┤ person_id (FK)   │
│  bioguide_id    │     │ id (PK)          │
│  full_name      │     │ chamber          │
│  birth_year     │     │ state            │
│  ...            │     │ district         │
└─────────────────┘     │ party            │
                        │ current_member   │
                        └──────────────────┘
                                │
                                │ 1:N
                                ▼
                        ┌──────────────────┐
                        │ federal_member   │
                        │ _term            │
                        │                  │
                        │ member_id (FK)   │
                        │ congress         │
                        │ start_year       │
                        │ end_year         │
                        │ party            │
                        │ state            │
                        │ district         │
                        └──────────────────┘
```

### Bill Relationships

```
┌─────────────┐     ┌─────────────────┐
│    bill     │     │ bill_amendment  │
│             │     │                 │
│ bill_print_no│────►│ bill_print_no  │
│ session_year│     │ session_year    │
│ title       │     │ version         │
│ data_source │     │ memo            │
│ congress    │     │ full_text       │
└─────────────┘     └─────────────────┘
        │                     │
        │ 1:N                │ 1:N
        ▼                     ▼
┌─────────────┐     ┌─────────────────┐
│ bill_sponsor│     │ bill_action     │
│             │     │                 │
│ bill_print_no│     │ bill_print_no  │
│ session_year│     │ session_year    │
│ member_id   │     │ sequence_no     │
│ sponsor_type│     │ effect_date     │
└─────────────┘     │ chamber         │
                    │ text            │
                    │ action_type     │
                    └─────────────────┘
```

## Indexes

### Performance Indexes

```sql
-- Bill lookup indexes
CREATE INDEX idx_bill_print_no_session ON master.bill(bill_print_no, bill_session_year);
CREATE INDEX idx_bill_data_source ON master.bill(data_source);
CREATE INDEX idx_bill_congress ON master.bill(congress);
CREATE INDEX idx_bill_status ON master.bill(status);

-- Action indexes
CREATE INDEX idx_bill_action_date ON master.bill_amendment_action(effect_date);
CREATE INDEX idx_bill_action_chamber ON master.bill_amendment_action(chamber);
CREATE INDEX idx_bill_action_type ON master.bill_amendment_action(action_type);

-- Sponsor indexes
CREATE INDEX idx_bill_sponsor_member ON master.bill_sponsor(session_member_id);
CREATE INDEX idx_bill_sponsor_type ON master.bill_sponsor(sponsor_type);

-- Federal member indexes
CREATE INDEX idx_federal_person_bioguide ON master.federal_person(bioguide_id);
CREATE INDEX idx_federal_member_person ON master.federal_member(person_id);
CREATE INDEX idx_federal_member_current ON master.federal_member(current_member);
CREATE INDEX idx_federal_member_state ON master.federal_member(state);

-- Social media indexes
CREATE INDEX idx_federal_social_member ON master.federal_member_social_media(member_id);
CREATE INDEX idx_federal_social_platform ON master.federal_member_social_media(platform);
```

## Data Integrity Constraints

### Check Constraints

```sql
-- Data source validation
ALTER TABLE master.bill ADD CONSTRAINT chk_bill_data_source
    CHECK (data_source IN ('state', 'federal'));

-- Party code validation
ALTER TABLE master.federal_member ADD CONSTRAINT chk_federal_party
    CHECK (party IN ('D', 'R', 'I'));

-- Chamber validation
ALTER TABLE master.federal_member ADD CONSTRAINT chk_federal_chamber
    CHECK (chamber IN ('house', 'senate'));

-- Text format validation
ALTER TABLE master.federal_bill_text ADD CONSTRAINT chk_text_format
    CHECK (text_format IN ('html', 'xml', 'plain'));
```

### Foreign Key Constraints

```sql
-- Bill amendment references bill
ALTER TABLE master.bill_amendment ADD CONSTRAINT fk_bill_amendment_bill
    FOREIGN KEY (bill_print_no, bill_session_year)
    REFERENCES master.bill(bill_print_no, bill_session_year);

-- Federal member references person
ALTER TABLE master.federal_member ADD CONSTRAINT fk_federal_member_person
    FOREIGN KEY (person_id) REFERENCES master.federal_person(id);

-- Social media references member
ALTER TABLE master.federal_member_social_media ADD CONSTRAINT fk_social_member
    FOREIGN KEY (member_id) REFERENCES master.federal_member(id);
```

## Data Migration Strategy

### Schema Evolution

1. **Additive Changes**: New columns/tables are added without breaking existing functionality
2. **Migration Scripts**: Versioned SQL scripts in `src/main/resources/sql/migrations/`
3. **Backward Compatibility**: Old code continues to work with new schema
4. **Data Preservation**: Existing data is never lost during migrations

### Migration Example

```sql
-- Migration: Add federal member support
-- File: V20250921.0004__federal_member_schema.sql

-- Create federal person table
CREATE TABLE master.federal_person (
    id BIGSERIAL PRIMARY KEY,
    bioguide_id TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    -- ... other fields
);

-- Create federal member table
CREATE TABLE master.federal_member (
    id BIGSERIAL PRIMARY KEY,
    person_id INTEGER REFERENCES master.federal_person(id),
    -- ... other fields
);

-- Add indexes
CREATE INDEX idx_federal_person_bioguide ON master.federal_person(bioguide_id);
CREATE INDEX idx_federal_member_person ON master.federal_member(person_id);
```

## Performance Considerations

### Query Optimization

#### Common Query Patterns

1. **Bill Lookup by Number**
   ```sql
   SELECT * FROM master.bill
   WHERE bill_print_no = ? AND bill_session_year = ?
   ```

2. **Bills by Sponsor**
   ```sql
   SELECT b.* FROM master.bill b
   JOIN master.bill_sponsor bs ON b.bill_print_no = bs.bill_print_no
   WHERE bs.session_member_id = ?
   ```

3. **Recent Actions**
   ```sql
   SELECT * FROM master.bill_amendment_action
   WHERE effect_date >= ?
   ORDER BY effect_date DESC, sequence_no DESC
   ```

#### Partitioning Strategy

For large datasets, consider partitioning by session year:

```sql
-- Partition bill table by session year
CREATE TABLE master.bill_y2023 PARTITION OF master.bill
    FOR VALUES FROM (2023) TO (2024);

CREATE TABLE master.bill_y2024 PARTITION OF master.bill
    FOR VALUES FROM (2024) TO (2025);
```

### Monitoring Queries

```sql
-- Table sizes
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'master'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index usage
SELECT indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'master'
ORDER BY idx_scan DESC;

-- Slow queries
SELECT query, total_time, calls, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

## Backup and Recovery

### Backup Strategy

```bash
# Full database backup
pg_dump -h localhost -U openleg -d openleg > openleg_backup.sql

# Schema-only backup
pg_dump -h localhost -U openleg -d openleg --schema-only > openleg_schema.sql

# Data-only backup
pg_dump -h localhost -U openleg -d openleg --data-only > openleg_data.sql
```

### Point-in-Time Recovery

```sql
-- Enable WAL archiving
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET archive_mode = on;
ALTER SYSTEM SET archive_command = 'cp %p /var/lib/postgresql/archive/%f';

-- Create base backup
SELECT pg_start_backup('base_backup');
-- Copy data directory
SELECT pg_stop_backup();
```

## Security Considerations

### Access Control

```sql
-- Create read-only user for applications
CREATE USER openleg_app WITH PASSWORD 'app_password';
GRANT CONNECT ON DATABASE openleg TO openleg_app;
GRANT USAGE ON SCHEMA master TO openleg_app;
GRANT SELECT ON ALL TABLES IN SCHEMA master TO openleg_app;

-- Create read-write user for ingestion
CREATE USER openleg_ingest WITH PASSWORD 'ingest_password';
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA master TO openleg_ingest;
```

### Data Encryption

```sql
-- Enable encryption at rest
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = '/etc/ssl/certs/postgresql.crt';
ALTER SYSTEM SET ssl_key_file = '/etc/ssl/private/postgresql.key';
```

## Maintenance Procedures

### Regular Maintenance

```sql
-- Update statistics
ANALYZE master.bill;
ANALYZE master.federal_member;

-- Reindex if needed
REINDEX TABLE master.bill;
REINDEX TABLE master.federal_member;

-- Vacuum for space reclamation
VACUUM FULL master.bill_amendment_action;
```

### Monitoring Setup

```sql
-- Enable query logging
ALTER SYSTEM SET log_statement = 'ddl';
ALTER SYSTEM SET log_duration = on;
ALTER SYSTEM SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';

-- Create monitoring views
CREATE VIEW master.database_stats AS
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    n_tup_ins, n_tup_upd, n_tup_del
FROM pg_stat_user_tables
JOIN pg_tables ON pg_stat_user_tables.relname = pg_tables.tablename
WHERE schemaname = 'master';
```

This comprehensive schema documentation provides the foundation for understanding and maintaining the OpenLegislation database system.