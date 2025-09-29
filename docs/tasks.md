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
- [x] MEMBERS: Validate `master.federal_person`, `master.federal_member`, `master.federal_member_term`, `master.federal_member_social_media` tables (schema verified, mappings to Congress.gov API and GovInfo XML complete with dedup via bioguide_id)
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
- [ ] BILLSTATUS
