# Entity Relationship Model (ERM)

## Overview
The OpenLegislation database follows a normalized relational schema designed to efficiently store and query legislative data from multiple sources.

## Core Entities

### Bill Entity
```sql
Bill {
    bill_id: SERIAL (PK)
    session_year: INTEGER
    print_no: VARCHAR(20)
    title: TEXT
    summary: TEXT
    status: VARCHAR(50)
    bill_type: VARCHAR(20)
    created_date: TIMESTAMP
    modified_date: TIMESTAMP

    -- Federal extensions
    congress_number: INTEGER
    federal_bill_type: VARCHAR(10)
    govinfo_id: VARCHAR(50)
    congressdotgov_url: TEXT
}
```

### BillAction Entity
```sql
BillAction {
    action_id: SERIAL (PK)
    bill_id: INTEGER (FK → Bill.bill_id)
    action_date: DATE
    chamber: VARCHAR(20)
    action_text: TEXT
    sequence_no: INTEGER
}
```

### BillSponsor Entity
```sql
BillSponsor {
    sponsor_id: SERIAL (PK)
    bill_id: INTEGER (FK → Bill.bill_id)
    member_id: INTEGER (FK → Member.member_id)
    sponsor_type: VARCHAR(20) -- 'PRIME', 'COSPONSOR'
    sequence_no: INTEGER
}
```

### BillAmendment Entity
```sql
BillAmendment {
    amendment_id: SERIAL (PK)
    bill_id: INTEGER (FK → Bill.bill_id)
    version: VARCHAR(5)
    memo: TEXT
    full_text: TEXT
    publish_date: DATE
}
```

## Legislative Entities

### Law Entity
```sql
Law {
    law_id: SERIAL (PK)
    law_id_str: VARCHAR(20) -- 'ABC001'
    title: TEXT
    chapter: VARCHAR(10)
    created_date: TIMESTAMP
    modified_date: TIMESTAMP
}
```

### LawDocument Entity
```sql
LawDocument {
    document_id: SERIAL (PK)
    law_id: INTEGER (FK → Law.law_id)
    document_type: VARCHAR(20)
    title: TEXT
    text: TEXT
    publish_date: DATE
}
```

### Committee Entity
```sql
Committee {
    committee_id: SERIAL (PK)
    session_year: INTEGER
    chamber: VARCHAR(20)
    name: VARCHAR(100)
    committee_type: VARCHAR(20)
}
```

### CommitteeMember Entity
```sql
CommitteeMember {
    member_id: SERIAL (PK)
    committee_id: INTEGER (FK → Committee.committee_id)
    session_year: INTEGER
    chamber: VARCHAR(20)
    member_name: VARCHAR(100)
    title: VARCHAR(50)
}
```

## Member Data Entities

### Member Entity
```sql
Member {
    member_id: SERIAL (PK)
    session_year: INTEGER
    chamber: VARCHAR(20)
    district_code: VARCHAR(10)
    member_name: VARCHAR(100)
    party: VARCHAR(20)
    email: VARCHAR(100)
    website: TEXT
}
```

### MemberBiography Entity
```sql
MemberBiography {
    bio_id: SERIAL (PK)
    member_id: INTEGER (FK → Member.member_id)
    bio_type: VARCHAR(20) -- 'OFFICIAL', 'CAMPAIGN'
    bio_text: TEXT
    source_url: TEXT
}
```

## Calendar and Agenda Entities

### Calendar Entity
```sql
Calendar {
    calendar_id: SERIAL (PK)
    session_year: INTEGER
    calendar_number: INTEGER
    calendar_date: DATE
    release_date_time: TIMESTAMP
}
```

### CalendarEntry Entity
```sql
CalendarEntry {
    entry_id: SERIAL (PK)
    calendar_id: INTEGER (FK → Calendar.calendar_id)
    bill_id: INTEGER (FK → Bill.bill_id)
    bill_print_no: VARCHAR(20)
    bill_amend_version: VARCHAR(5)
    entry_type: VARCHAR(20)
}
```

### Agenda Entity
```sql
Agenda {
    agenda_id: SERIAL (PK)
    session_year: INTEGER
    agenda_number: INTEGER
    committee_id: INTEGER (FK → Committee.committee_id)
    meeting_date_time: TIMESTAMP
}
```

## Transcript Entities

### Transcript Entity
```sql
Transcript {
    transcript_id: SERIAL (PK)
    session_year: INTEGER
    date: DATE
    location: VARCHAR(100)
    transcript_type: VARCHAR(20) -- 'FLOOR', 'COMMITTEE'
}
```

### TranscriptFile Entity
```sql
TranscriptFile {
    file_id: SERIAL (PK)
    transcript_id: INTEGER (FK → Transcript.transcript_id)
    file_name: VARCHAR(100)
    text: TEXT
    sequence_no: INTEGER
}
```

## Processing and Source Entities

### SourceFile Entity
```sql
SourceFile {
    file_id: SERIAL (PK)
    file_name: VARCHAR(255)
    source_type: VARCHAR(20) -- 'SOBI', 'XML', 'FEDERAL_XML'
    staging_path: TEXT
    archive_path: TEXT
    processed_date: TIMESTAMP
    error_message: TEXT
}
```

### DataProcessRun Entity
```sql
DataProcessRun {
    run_id: SERIAL (PK)
    start_time: TIMESTAMP
    end_time: TIMESTAMP
    status: VARCHAR(20) -- 'SUCCESS', 'FAILED', 'PARTIAL'
    records_processed: INTEGER
    errors_count: INTEGER
}
```

## Relationships

### Bill Relationships
```
Bill (1) ──── (M) BillAction
Bill (1) ──── (M) BillSponsor
Bill (1) ──── (M) BillAmendment
Bill (1) ──── (M) CalendarEntry
```

### Committee Relationships
```
Committee (1) ──── (M) CommitteeMember
Committee (1) ──── (M) Agenda
```

### Member Relationships
```
Member (1) ──── (M) BillSponsor
Member (1) ──── (M) CommitteeMember
Member (1) ──── (M) MemberBiography
```

### Calendar Relationships
```
Calendar (1) ──── (M) CalendarEntry
CalendarEntry (M) ──── (1) Bill
```

### Law Relationships
```
Law (1) ──── (M) LawDocument
```

### Transcript Relationships
```
Transcript (1) ──── (M) TranscriptFile
```

## Indexes and Constraints

### Primary Keys
- All entities have SERIAL primary keys
- Composite primary keys where appropriate (e.g., session_year + print_no for bills)

### Foreign Keys
- Cascading deletes for dependent data
- Restrict deletes for critical relationships
- Indexed foreign key columns

### Unique Constraints
```sql
-- Bill uniqueness
ALTER TABLE bill ADD CONSTRAINT uk_bill_session_print
    UNIQUE (session_year, print_no);

-- Committee member uniqueness
ALTER TABLE committee_member ADD CONSTRAINT uk_committee_member
    UNIQUE (committee_id, session_year, member_name);
```

### Performance Indexes
```sql
-- Bill search indexes
CREATE INDEX idx_bill_session_year ON bill(session_year);
CREATE INDEX idx_bill_status ON bill(status);
CREATE INDEX idx_bill_modified ON bill(modified_date DESC);

-- Action indexes
CREATE INDEX idx_bill_action_bill_id ON bill_action(bill_id);
CREATE INDEX idx_bill_action_date ON bill_action(action_date DESC);

-- Sponsor indexes
CREATE INDEX idx_bill_sponsor_bill_id ON bill_sponsor(bill_id);
CREATE INDEX idx_bill_sponsor_member_id ON bill_sponsor(member_id);

-- Full-text search
CREATE INDEX idx_bill_fulltext ON bill
USING gin(to_tsvector('english', title || ' ' || summary));
```

## Data Integrity Rules

### Business Rules
1. Bills must have unique print numbers within a session year
2. Bill actions must be chronological within a bill
3. Committee members cannot serve on the same committee multiple times per session
4. Calendar entries must reference valid bills
5. Amendments must belong to existing bills

### Validation Constraints
```sql
-- Session year validation
ALTER TABLE bill ADD CONSTRAINT chk_session_year
    CHECK (session_year >= 1900 AND session_year <= 2100);

-- Chamber validation
ALTER TABLE bill_action ADD CONSTRAINT chk_chamber
    CHECK (chamber IN ('SENATE', 'ASSEMBLY', 'CONGRESS'));

-- Status validation
ALTER TABLE bill ADD CONSTRAINT chk_status
    CHECK (status IN ('INTRODUCED', 'IN_COMMITTEE', 'PASSED', 'SIGNED', 'VETOED'));
```

## Extension Points

### Federal Data Extensions
- Additional fields for Congress.gov integration
- GovInfo document linking
- Federal committee mappings
- Congressional record integration

### Social Media Extensions
- Member social media account linking
- Post content storage
- Engagement metrics
- Sentiment analysis results

### Analytics Extensions
- Bill text analysis results
- Voting pattern data
- Committee activity metrics
- Performance statistics

## Schema Evolution

### Migration Strategy
- Use Flyway for versioned migrations
- Backward compatible changes when possible
- Data migration scripts for schema changes
- Rollback scripts for critical changes

### Version History
- V1.0: Initial NYS legislative schema
- V1.1: Federal bill extensions
- V1.2: Member biography and social media
- V1.3: Analytics and reporting tables
- V1.4: Performance optimizations and indexes