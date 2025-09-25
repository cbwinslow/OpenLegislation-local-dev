# OpenLegislation Architecture Overview

## High-Level Architecture

OpenLegislation is a comprehensive system for ingesting, processing, and serving legislative data, focusing on New York State with extensions for federal data via GovInfo/Congress.gov.

### Core Components
- **Backend**: Java with Spring Framework for processing, DAOs for DB ops.
- **Database**: PostgreSQL with Flyway migrations for schema management.
- **Data Sources**: SOBI/XML feeds, web scraping, GovInfo bulk XML, APIs (Congress.gov, OpenStates).
- **Processing Pipeline**: Python ETL scripts for fetching/parsing external data, Java processors for normalization/storage.
- **API**: REST endpoints for querying bills, members, agendas, etc.
- **Tools**: Python scripts in `/tools/` for ingestion, testing, monitoring.

### Data Flow Diagram

```mermaid
graph TD
    A[External Sources<br/>- GovInfo XML Bulk<br/>- Congress.gov API<br/>- OpenStates API<br/>- NY State Feeds] --> B[Python ETL Tools<br/>- Fetch (requests, glob)<br/>- Parse (lxml.etree, json)<br/>- Transform (custom mappings)]
    B --> C[Java Processors/DAOs<br/>- XmlFile/GovInfoXmlFile<br/>- Bill processors<br/>- Action/Sponsor analyzers<br/>- Event-driven handling]
    C --> D[PostgreSQL Database<br/>- Master schema (bill, member, action, etc.)<br/>- Staging tables for GovInfo<br/>- Migrations (Flyway)]
    D --> E[REST API<br/>- Query endpoints<br/>- Search, aggregation]
    E --> F[Frontend/Web Access<br/>- Static site<br/>- External integrations]
    B -.->|Resume/Progress| G[Ingestion Tracker<br/>- BaseIngestionProcess<br/>- JSON logs]
    C -.->|Spotchecks/Validation| H[Testing Utils<br/>- JUnit, resources/]
```

### Key Directories
- **src/main/java/gov/nysenate/openleg**: Core Java code.
  - `processors/`: Bill, agenda, transcript processors.
  - `legislation/bill/`: Models (Bill, BillId, Action, Sponsor), GovInfo-specific (GovInfoDocRef).
  - `dao/`: Data access objects.
- **tools/**: Python scripts (govinfo_bill_ingestion.py, ingest_federal_members.py, base_ingestion_process.py).
- **src/main/resources/sql/migrations/**: DB schema evolutions.
- **docs/**: Existing partial docs; this full-docs/ expands them.

### Design Patterns
- **Event-Driven**: Processors handle source file events (e.g., new XML -> BillUpdateEvent).
- **Staging Approach**: GovInfo data stages before merging to master to avoid conflicts.
- **Resumeable Ingestion**: Python framework tracks progress in JSON, allows interruption recovery.
- **Modular Mapping**: XML XPaths map to models (e.g., sponsor/fullName -> BillSponsor.name).

### Challenges & Considerations
- Data Volume: Bulk XML handling with chunking/resume.
- Mapping Complexities: Federal vs. state models (e.g., congress/session -> year).
- Integrity: Deduplication, validation, spotchecks.
