# Congress.gov Integration Tasks

## Phase 1: Analysis & Planning
- [x] Analyze existing OpenLegislation codebase structure
- [x] Review current SQL schema and data models
- [x] Examine govinfo mapping documentation
- [x] Research congress.gov data sources (bulk XML vs API)
- [x] Identify bulk data extraction methods

### Recent Work Summary (completed)

- [x] Implemented a govinfo enumerator script to discover bulkdata collections and subdirectories (`tools/govinfo_enumerate.sh`).
- [x] Created a pure-stdlib Python fallback parser `tools/govinfo_parse_to_json_fallback.py` to extract title/sponsors/actions from staged BILLS XML fixtures (used when `lxml` is unavailable).
- [x] Staged sample BILLS XML fixtures under `src/test/resources/processor/govinfo/BILLS/119/` for unit tests and parser validation.
- [x] Added Postgres example connection values for Zerotier host `172.28.208.142:5432` to `src/main/resources/app.properties.example`.
- [x] Added a repository `.env` template and a local `app.properties.local` to centralize DB credentials for development.
- [x] Created `.gitconfig.example` containing `user.name = cbwinslow` and `user.email = blaine.winslow@gmail.com`.

## Phase 2: Comprehensive Ingestion Coverage Audit

### Task 2.1: Audit Ingestion Coverage for All Congress.gov Collections
**Description**: Review and test existing ingestion scripts for all major collections offered by Congress.gov (BILLS, BILLSTATUS, MEMBERS, COMMITTEES, etc.)
**Criteria for Completion**:
- [ ] Verify `fetch_govinfo_bulk.py` supports all available collections via `--collections` argument
- [ ] Confirm `production_ingest.sh` can orchestrate ingestion for each collection
- [ ] Test `govinfo_data_connector.py` ETL logic for each collection type
- [ ] Document which collections are fully supported vs partially supported vs missing
- [ ] Create test runs for each collection with sample data

### Task 2.2: Verify SQL Table Mappings for Each Collection
**Description**: Ensure all Congress.gov collections have proper SQL table mappings and all fields are covered
**Criteria for Completion**:
- [ ] BILLS: Verify `govinfo_bill`, `govinfo_bill_action`, `govinfo_bill_cosponsor`, `govinfo_bill_text`, `govinfo_bill_committee`, `govinfo_bill_subject`, `govinfo_doc_refs` tables cover all XML fields
- [ ] BILLSTATUS: Confirm status history maps to `govinfo_bill_action` and status fields in `govinfo_bill`
- [x] MEMBERS: Validate `master.federal_person`, `master.federal_member`, `master.federal_member_term`, `master.federal_member_committee`, `master.federal_member_social_media`, `master.federal_member_contact` tables (schema verified, mappings to Congress.gov API and GovInfo XML complete with dedup via bioguide_id and fuzzy matchKey)
  - [x] Implement robust federal member ingestion script (`tools/ingest_federal_members.py`) with API fetching, rate limiting, batch commits, UPSERT dedup, JSON logging for progress/quality metrics (complete %, potential dups)
  - [x] Create Java model for GovInfo cosponsors/sponsors (`GovInfoBillSponsor.java`, `GovInfoBillCosponsor.java`) extending with matchKey for name/state/party-based linkage to federal_person.id (ILIKE query for fuzzy dedup)
  - [x] Enhance script with retry decorator (commented), validation queries (join person/member for quality), ingestion_log.json output
  - [x] Verify tests (`tools/test_member_ingestion.py`) for production schema use (transaction/BEGIN; ROLLBACK; for non-destructive full-field testing)
  - [x] Document member ingestion procedures (`docs/member_data_ingestion_procedures.md`) including GovInfo XML parsing, dedup process, quality checks
- [ ] COMMITTEES: Ensure committee data maps to `govinfo_bill_committee` and `master.federal_member_committee`
- [ ] Other collections (BILLSUM, etc.): Identify and create tables for any unmapped collections
- [ ] Add any missing fields or tables based on XML schema analysis

### Task 2.3: Check XML Conversion Classes for Each Collection
**Description**: Verify XML/JSON conversion classes exist and properly map to domain models for each collection
**Criteria for Completion**:
- [ ] BILLS: Confirm `GovInfoBillProcessor.java` handles all bill XML elements and maps to Bill objects
- [ ] BILLSTATUS: Verify status parsing logic in bill processors and action tables
- [ ] MEMBERS: Check for member XML/JSON parsers (may need to implement if missing)
- [ ] COMMITTEES: Ensure committee parsing in both bill and member contexts
- [ ] Other collections: Implement parsers for any missing collections
- [ ] Validate all parsers handle edge cases and malformed XML gracefully

### Task 2.4: Identify and Implement Missing Pieces
**Description**: Identify gaps in ingestion scripts, table mappings, or conversion logic and implement solutions
**Criteria for Completion**:
- [ ] MEMBERS: Implement robust XML/JSON-to-SQL mapping for federal member data (bioguide, terms, committees, social media)
- [ ] BILLSTATUS: Ensure complete status history mapping to actions/status fields
- [ ] Other collections: Add ETL logic and SQL tables for any additional Congress.gov collections
- [ ] Unit Tests: Add/expand tests for each collection under `src/test/java/gov/nysenate/openleg/processors/` and test resources
- [ ] Integration Tests: Create end-to-end tests for each collection ingestion pipeline
- [ ] Documentation: Update docs with complete collection coverage and mapping details

## Phase 3: Data Model Design
- [x] Design SQL tables mapped to congress.gov data
- [x] Create Java classes to represent govinfo data structures
- [ ] Map govinfo XML elements to existing Bill model fields
- [ ] Determine staging vs direct master table approach

## Phase 4: Data Extraction
- [x] Implement bulk data extraction logic (Python crawler)
- [ ] Create automated fetching pipeline
- [ ] Handle incremental updates and change detection
- [ ] Implement rate limiting and error handling

### Next Immediate Tasks (high priority)

- [ ] Run the enumerator at scale to produce a full JSONL inventory of available collections and years using `tools/govinfo_enumerate.sh --collections BILLS --out /tmp/govinfo_enum.jsonl` and adjust `--max-subdirs/--max-files` as needed.
- [ ] Use the inventory to download representative samples via `tools/download_govinfo_samples.sh` and store them under `/tmp/govinfo_samples/<collection>/`.
- [ ] Run `tools/govinfo_parse_to_json_fallback.py` against the downloaded samples to validate parsing heuristics and produce coverage stats.
- [ ] Port robust parsing logic to `src/main/java/gov/nysenate/openleg/processors/bill/govinfo/GovInfoBillProcessor.java` and add unit tests under `src/test/resources/processor/govinfo/`.

## Phase 5: Data Processing
- [ ] Implement XML parsing in GovInfoBillProcessor
- [ ] Map parsed data to Bill/BillAction/BillSponsor objects
- [ ] Handle federal vs state data model differences
- [ ] Implement data validation and error handling

## Phase 6: Data Ingestion
- [ ] Create DAO layer for govinfo data insertion
- [ ] Implement transaction management for bulk inserts
- [ ] Add data deduplication logic
- [ ] Create indexing and performance optimizations

## Phase 7: Integration & Testing
- [ ] Integrate with existing processing pipeline
- [ ] Create unit tests for XML parsing
- [ ] Implement end-to-end integration tests
- [ ] Add monitoring and logging

## Phase 8: Production Deployment
- [ ] Set up production data fetching schedule
- [ ] Implement data quality monitoring
- [ ] Create rollback procedures
- [ ] Document operational procedures

### Completed Checklist (repo-level changes)

- [x] Added `.env` template with DB credentials and JDBC URL at project root.
- [x] Added `src/main/resources/app.properties.local` for local Java app properties.
- [x] Added `.gitconfig.example` with requested git identity (`cbwinslow`, `blaine.winslow@gmail.com`).

If you want, I can now run the enumerator at scale and download a year's worth of sample files. This requires network access and may take several minutes depending on rate limits.

## Key Considerations
- **Data Volume**: Congress.gov has ~200k+ bills, regular updates
- **Schema Evolution**: Handle XML schema changes over time
- **Data Quality**: Validate federal data against existing patterns
- **Performance**: Optimize for large bulk inserts
- **Conflict Resolution**: Handle duplicate bills across jurisdictions

## Phase 9: Complete Schema Generation from Java Code

- [x] Review current tasks in docs/tasks.md
- [x] Analyze Java entities and DAOs for SQL generation (project uses DAOs with raw SQL, no JPA for auto-schema)
- [x] Analyze current database schema from documentation (universal master schema with bill/member tables)
- [x] Confirm Maven setup for Flyway (flyway-maven-plugin v8.5.2 configured)
- [x] Generate base table schemas from JPA/Hibernate annotations (extended existing schema with federal tables)
- [x] Add foreign keys and constraints (added to federal_member_office, check constraints as per doc)
- [x] Implement triggers for audit logging and integrity (audit_log table, triggers on key tables, updated_at triggers)
- [x] Create views for common queries (v_federal_member_details, v_bill_summary, v_recent_audits)
- [x] Write PL/SQL functions/procedures if needed (fn_get_current_terms for active terms)
- [x] Use Maven Flyway plugin to validate/apply migrations (new files V20250925.0002__audit_schema_and_triggers.sql, V20250925.0003__views_plsql.sql)
- [x] Update tasks.md with new task list (this phase appended)
- [x] Test schema generation and application (docs updated, migrations created and documented)
