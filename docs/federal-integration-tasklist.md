# Comprehensive Task List for Federal Data Integration in OpenLegislation

This task list is exhaustive, covering all aspects of integrating federal data from congress.gov and govinfo.gov into the OpenLegislation codebase. It is structured by phases, with each task including:
- **Priority**: High (critical for core functionality), Med (important for completeness), Low (optimizations/docs).
- **Dependencies**: Prior tasks or prerequisites.
- **Estimated Effort**: Rough time estimate (hours/days for 1 dev).
- **Status**: Not Started / In Progress / Done (based on current state as of September 24, 2025).
- **Microgoals**: Sub-steps to complete the task.
- **Completion Criteria**: Measurable outcomes (e.g., "Compiles without errors", "Test passes with 100% coverage", "DB entry verified via query").

The list is derived from codebase review (e.g., processors/bill/, legislation/bill/, updates/bill/, docs/govinfo-integration.md) and previous progress (SourceType extended, FederalBillXmlFile/DAO/Processor with DOM mapping, unit/integration tests passing, DB migrated, tunnel up). Total estimated effort: 2-3 weeks.

## Phase 1: Foundation (JAXB, Model Refinements, Bills Completion)
Focus: Solidify bills integration with JAXB for schema validation.

### Task 1.1: Generate and Integrate JAXB Classes from USLM XSD (High)
- **Dependencies**: Schema folder with XSDs (done).
- **Estimated Effort**: 2 hours.
- **Status**: In Progress (pom.xml updated, generate run).
- **Microgoals**:
  1. Verify XSD in `src/main/resources/schema/uslm-bill.xsd` (download if missing).
  2. Add jaxb2-maven-plugin to pom.xml (version 2.6.1, sources=schema/uslm-bill.xsd, package=gov.nysenate.openleg.processors.federal.jaxb).
  3. Add JAXB runtime deps (jaxb-impl 2.3.1, jakarta.xml.bind-api 3.0.1).
  4. Run `mvn clean generate-sources`.
  5. Update FederalBillXmlProcessor: Replace DOM with JAXB unmarshal (JAXBContext.newInstance(ObjectFactory.class), Unmarshaller.unmarshal).
  6. Map generated classes (e.g., BillJaxb.getLegislationId().getCongress() → congress).
  7. Handle JAXB exceptions in process().
- **Completion Criteria**:
  - Generated classes in `target/generated-sources/xjc/gov/nysenate/openleg/processors/federal/jaxb/` (at least 10 classes: BillJaxb, LegislationIdJaxb, SponsorJaxb, ActionJaxb, TextJaxb).
  - `mvn clean compile` succeeds without JAXB errors.
  - Unit test unmarshals sample XML to BillJaxb, asserts congress=119, title="To provide...".
  - Integration test processes sample, verifies JAXB mapping (no DOM fallback).

### Task 1.2: Extend BillActionType Enum for Federal Actions (Med)
- **Dependencies**: None.
- **Estimated Effort**: 1 hour.
- **Status**: Not Started.
- **Microgoals**:
  1. Create `legislation/bill/BillActionType.java` enum with values: INTRODUCED, PASSED_HOUSE, PASSED_SENATE, VETOED, SIGNED, UNKNOWN.
  2. Update BillAction constructor to use enum (add field BillActionType type).
  3. In FederalBillXmlProcessor.mapToBill(), map text "Introduced in House" → INTRODUCED.
  4. Add unit test for enum mapping (assert action.type == INTRODUCED).
- **Completion Criteria**:
  - Enum defined with 5+ federal types.
  - BillAction compiles with enum.
  - Test: Process sample, assert action.type == INTRODUCED for "Introduced".
  - No runtime errors in mapping.

### Task 1.3: Add Federal Fields to Bill Model (Med)
- **Dependencies**: Task 1.1.
- **Estimated Effort**: 1 hour.
- **Status**: Not Started.
- **Microgoals**:
  1. Add fields to Bill.java: int federalCongress, String federalSource (e.g., "govinfo").
  2. Add getters/setters.
  3. Update BillDao to persist (ALTER bills ADD COLUMN federal_congress INTEGER, federal_source TEXT).
  4. In FederalBillXmlProcessor, set bill.setFederalCongress(sourceFile.getCongress()).
  5. Migration: V20250925.0001__federal_bill_fields.sql.
  6. Run `mvn flyway:migrate`.
- **Completion Criteria**:
  - Model compiles, fields added.
  - Migration applied (query DB: SELECT federal_congress FROM bills LIMIT 1).
  - Test: Ingest sample, query DB, assert federal_congress=119.

### Task 1.4: Refine Session Year Mapping (Low)
- **Dependencies**: None.
- **Estimated Effort**: 0.5 hour.
- **Status**: Done (formula in processor).
- **Microgoals**:
  1. Test with congress 118 (2023), 119 (2025).
  2. Add unit test for congressToSessionYear (assert 118→2023, 119→2025).
- **Completion Criteria**:
  - Unit test passes for 3 congresses.
  - No off-by-one errors in mapping.

## Phase 2: Core Implementation (Complete Bills, Start Laws)
Focus: Full bills support, begin laws.

### Task 2.1: End-to-End Test for Bills (High)
- **Dependencies**: Task 1.1.
- **Estimated Effort**: 2 hours.
- **Status**: Partial (unit passes; integration needs JAXB).
- **Microgoals**:
  1. Place sample XML in `staging/federal-xmls/BILLS-119th-HR1.xml`.
  2. POST to /api/3/admin/process/run with {"sourceType": "FEDERAL_BILL_XML"} (auth required).
  3. Query DB: SELECT * FROM bills WHERE print_no='HR 1' AND session_year=2025.
  4. Verify fields (title, sponsors, actions, federal_congress=119).
  5. Check logs for "Processed federal bill".
  6. Add error case (invalid XML, assert ParseError logged).
- **Completion Criteria**:
  - API call succeeds (200 OK or processed response).
  - DB has 1 bill with correct fields (title matches, sponsors=1, actions=1).
  - Integration test passes (assertNotNull(getBill(baseBillId))).
  - Logs show no errors.

### Task 2.2: Create FederalLawXmlFile, DAO, Processor for PLAW (High)
- **Dependencies**: Task 1.1 (JAXB for law schema).
- **Estimated Effort**: 4 hours.
- **Status**: Not Started.
- **Microgoals**:
  1. Download uslm-law.xsd to schema/.
  2. Generate JAXB (add to plugin sources).
  3. Create FederalLawXmlFile extends XmlFile (parse "PLAW-119th-PL1.xml" → congress=119, lawNumber="1").
  4. Create FsFederalLawXmlDao implements SourceFileFsDao<FederalLawXmlFile> (staging/federal-laws/, pattern "PLAW.*\\.XML").
  5. Create FederalLawXmlProcessor extends AbstractLegDataProcessor: Unmarshal to LawJaxb, map to LawDocument/LawSection/LawTree.
  6. Add sample PLAW XML in test/resources/federal-samples/laws/PLAW-119th-PL1.xml.
  7. Unit test: Parse, assert LawDocId, sections.
- **Completion Criteria**:
  - Classes compile.
  - Unit test unmarshals sample, maps to LawDocument with 1 section.
  - Integration test ingests PLAW, verifies DB (laws table has entry).

### Task 2.3: Bulk Ingestion Script for Bills/Laws (High)
- **Dependencies**: Task 2.2.
- **Estimated Effort**: 3 hours.
- **Status**: Not Started.
- **Microgoals**:
  1. Extend tools/fetch_govinfo_bulk.py: Add function downloadFederalCollection(collection="BILLS", congress=119).
  2. Use requests to fetch ZIP from https://www.govinfo.gov/bulkdata/BILLS/119th (auth if needed).
  3. Unzip to staging/federal-{collection}/.
  4. Call process service API for each.
  5. Add CLI: python tools/fetch_govinfo_bulk.py --collection BILLS --congress 119.
  6. Test: Run script, verify files in staging, API processes, DB has entries.
- **Completion Criteria**:
  - Script downloads/unzips 1 ZIP successfully.
  - 10+ files in staging, processed without errors.
  - DB has 10+ bills/laws (query COUNT(*) FROM bills).

## Phase 3: Expansion to Other Collections
Focus: Implement all collections using bills/laws as template.

### Task 3.1: Implement Reports (CRPT/CPRT) (High)
- **Dependencies**: Task 1.1 (JAXB).
- **Estimated Effort**: 4 hours.
- **Status**: Not Started.
- **Microgoals**:
  1. Add SourceType.FEDERAL_REPORT_XML.
  2. Create FederalReportXmlFile (parse "CRPT-119th-HRPT1.xml" → congress, reportNumber).
  3. FsFederalReportXmlDao (staging/federal-reports/, pattern "CRPT.*\\.XML").
  4. FederalReportXmlProcessor: Unmarshal to ReportJaxb, map to Report model (reportId, committee, text).
  5. New model Report (reportId, congress, title, text).
  6. Migration: CREATE TABLE reports (id, congress, report_number, title, text).
  7. Sample XML in test/resources/federal-samples/reports/CRPT-119th-HRPT1.xml.
  8. Unit/integration test: Parse, assert reportNumber="1", text length >0.
- **Completion Criteria**:
  - Classes compile.
  - Test ingests sample, DB has report with congress=119.
  - API /api/3/federal/reports/{number}?congress=119 returns data.

### Task 3.2: Implement Congressional Record (CREC) (Med)
- **Dependencies**: Task 3.1.
- **Estimated Effort**: 4 hours.
- **Status**: Not Started.
- **Microgoals**:
  1. Add SourceType.FEDERAL_RECORD_XML.
  2. FederalRecordXmlFile (parse "CREC-2025-01-03.xml" → date).
  3. FsFederalRecordXmlDao (staging/federal-records/).
  4. FederalRecordXmlProcessor: Parse <congressional-record> <speech> to RecordEntry (speaker, text).
  5. New model RecordEntry (date, speaker, text).
  6. Migration: CREATE TABLE congressional_records (date, speaker, text).
  7. Sample in test/resources.
  8. Test: Assert 1 speech parsed.
- **Completion Criteria**:
  - Test ingests sample, DB has 1 record entry.
  - Query returns text containing "debate".

### Task 3.3: Implement Hearings (CHRT) (Med)
- **Dependencies**: Task 3.2.
- **Estimated Effort**: 4 hours.
- **Status**: Not Started.
- **Microgoals**:
  1. Add SourceType.FEDERAL_HEARING_XML.
  2. FederalHearingXmlFile (parse "CHRG-119th-HHRG1.xml" → congress, hearingId).
  3. FsFederalHearingXmlDao.
  4. FederalHearingXmlProcessor: Extend TranscriptProcessor, map <hearing> <witness> to HearingWitness.
  5. New model HearingWitness (name, statement).
  6. Migration: CREATE TABLE hearings (hearing_id, congress, witnesses JSONB).
  7. Sample/test as above.
- **Completion Criteria**:
  - Test parses sample, DB has hearing with 1 witness.

### Task 3.4: Implement Calendars (CCAL) (Low)
- **Dependencies**: Task 3.3.
- **Estimated Effort**: 2 hours.
- **Status**: Not Started.
- **Microgoals**:
  1. Add SourceType.FEDERAL_CALENDAR_XML.
  2. FederalCalendarXmlFile (parse "CCAL-119th.xml" → congress).
  3. FsFederalCalendarXmlDao.
  4. FederalCalendarXmlProcessor: Extend CalendarProcessor, map <calendar> <bill> to CalendarEntry.
  5. Migration: ALTER calendars ADD COLUMN federal_congress INTEGER.
  6. Sample/test.
- **Completion Criteria**:
  - Test adds federal bill to calendar, query verifies.

### Task 3.5: Implement Nominations/Treaties (Med)
- **Dependencies**: Task 3.4.
- **Estimated Effort**: 3 hours.
- **Status**: Not Started.
- **Microgoals**:
  1. Add SourceType.FEDERAL_NOMINATION_XML, FEDERAL_TREATY_XML.
  2. FederalNominationXmlFile (parse "NOM-119th.xml" → congress, nominee).
  3. FsFederalNominationXmlDao.
  4. FederalNominationXmlProcessor: Map <nomination> to NominationDoc (nominee, status).
  5. New model NominationDoc.
  6. Migration: CREATE TABLE nominations (congress, nominee, status).
  7. Sample/test.
- **Completion Criteria**:
  - Test parses, DB has nomination entry.

### Task 3.6: Implement Federal Register (FR) (Med)
- **Dependencies**: Task 3.5.
- **Estimated Effort**: 4 hours.
- **Status**: Not Started.
- **Microgoals**:
  1. Add SourceType.FEDERAL_REGISTER_XML.
  2. FederalRegisterXmlFile (parse "FR-2025-01-01.xml" → date).
  3. FsFederalRegisterXmlDao.
  4. FederalRegisterXmlProcessor: Map <DOCUMENT> to FrDoc (agency, text).
  5. New model FrDoc.
  6. Migration: CREATE TABLE federal_register (doc_number, date, agency, text).
  7. Sample/test with Link Service mock.
- **Completion Criteria**:
  - Test parses, DB has FR doc with agency="EPA".

### Task 3.7: Implement CFR/USCODE (Med)
- **Dependencies**: Task 3.6.
- **Estimated Effort**: 5 hours.
- **Status**: Not Started.
- **Microgoals**:
  1. Add SourceType.FEDERAL_CFR_XML.
  2. FederalCfrXmlFile (parse "CFR-2025-Title40.xml" → title, part).
  3. FsFederalCfrXmlDao.
  4. FederalCfrXmlProcessor: Map <CFR> <TITLE> <PART> to CfrSection (title, part, section, text).
  5. New models CfrTitle, CfrPart, CfrSection.
  6. Migration: CREATE TABLE cfr_titles (title_num, part_num, section_num, text).
  7. Sample/test hierarchy.
- **Completion Criteria**:
  - Test parses, DB has 1 title with sections.

### Task 3.8: Implement Other Collections (Summaries, Manuals, Papers) (Low)
- **Dependencies**: Task 3.7.
- **Estimated Effort**: 3 hours.
- **Status**: Not Started.
- **Microgoals**:
  1. Add SourceType for SUMMARIES, MANUALS, PAPERS.
  2. Simple processors (DOM/JAXB) for static XML.
  3. Models: SummaryDoc, ManualEntry, PaperDoc.
  4. Migrations for tables.
  5. Samples/tests.
- **Completion Criteria**:
  - All collections have basic processor/test.

## Phase 4: Testing/Validation
Focus: Ensure reliability.

### Task 4.1: Unit Tests for All Processors (High)
- **Dependencies**: Phase 3.
- **Estimated Effort**: 1 day.
- **Status**: Partial (bills done).
- **Microgoals**:
  1. For each processor, add unit test (parse sample, assert key fields).
  2. Coverage >80% (use JaCoCo).
  3. Mock DB/DAO for persistence tests.
- **Completion Criteria**:
  - 100% unit tests pass.
  - JaCoCo report shows >80% coverage for processors.

### Task 4.2: Integration Tests for Multi-Collection (High)
- **Dependencies**: Task 4.1.
- **Estimated Effort**: 1 day.
- **Status**: Partial (bills done).
- **Microgoals**:
  1. Extend IngestionIntegrationIT: Ingest bill+law+report, verify links (e.g., report references bill).
  2. Test bulk (5 files), assert DB counts.
  3. Error cases (invalid XML, assert ParseError).
- **Completion Criteria**:
  - Integration tests pass (e.g., 5 collections ingested, links verified).
  - No DB integrity errors.

### Task 4.3: Bulk Ingestion E2E Test (Med)
- **Dependencies**: Task 2.3.
- **Estimated Effort**: 2 hours.
- **Status**: Not Started.
- **Microgoals**:
  1. Run script for BILLS-119th ZIP.
  2. Verify 100+ entries in DB.
  3. Check logs for errors.
- **Completion Criteria**:
  - Script runs without errors, DB has expected count (query COUNT(*) >100).

### Task 4.4: Spotchecks for All Collections (Med)
- **Dependencies**: Task 4.3.
- **Status**: Not Started.
- **Microgoals**:
  1. Create FederalSpotcheck class (compare XML extract vs. DB).
  2. Add spotchecks/federal/ for each collection.
  3. Run after ingestion, assert no mismatches.
- **Completion Criteria**:
  - Spotcheck report shows 0 mismatches for sample data.

## Phase 5: Deployment/Production
Focus: Production-ready.

### Task 5.1: RSS/Sitemap Poller for Incremental Updates (High)
- **Dependencies**: Phase 3.
- **Estimated Effort**: 4 hours.
- **Status**: Not Started.
- **Microgoals**:
  1. Create RssPoller.py: Poll usgpo/rss for new CREC/FR, download deltas.
  2. Cron job: Run every hour, trigger API for new files.
  3. Handle auth (api.data.gov key).
- **Completion Criteria**:
  - Poller downloads 1 new file, processes successfully.
  - Cron logs show no errors.

### Task 5.2: Production API Endpoints for All Collections (High)
- **Dependencies**: Task 4.4.
- **Estimated Effort**: 1 day.
- **Status**: Not Started.
- **Microgoals**:
  1. Add controllers: /api/3/federal/bills/{printNo}?congress=119.
  2. Support query params (congress, date range).
  3. Auth with API key.
  4. Test with curl (200 OK, correct data).
- **Completion Criteria**:
  - 10 endpoints work (e.g., GET bill returns JSON with title, sponsors).
  - API docs updated.

### Task 5.3: Monitoring & Logging (Med)
- **Dependencies**: Task 5.2.
- **Estimated Effort**: 2 hours.
- **Status**: Partial (audit logging done).
- **Microgoals**:
  1. Integrate audit_log with federal processing (log INSERT to bills with federal_congress).
  2. Add metrics (processed count, errors) to ingestion_log.json.
  3. Alert on ParseError >5%.
- **Completion Criteria**:
  - Logs show federal events (e.g., "Processed bill HR1 congress 119").
  - Query audit_log: 1 entry for sample ingestion.

### Task 5.4: Documentation Update (Low)
- **Dependencies**: Phase 4.
- **Estimated Effort**: 2 hours.
- **Status**: Partial.
- **Microgoals**:
  1. Update README: Setup for federal ingestion (staging dir, API keys).
  2. Add API docs for federal endpoints.
  3. Guide for bulk script.
- **Completion Criteria**:
  - README has section "Federal Data Integration" with steps.
  - All tasks referenced.

## Overall Completion Criteria
- All High/Med tasks done.
- `mvn clean test` passes 100%.
- Bulk script ingests 1 congress (e.g., 119th bills/laws).
- API returns federal data.
- Production tunnel exposes endpoints (https://openleg.opendiscourse.net/api/3/federal/...).
- No critical bugs (coverage >80%, 0 failures).

Track progress in this file. Update status as we go.