# Task 3.2: Implement Congressional Record (CREC) (Med)

## Overview
This task implements support for CREC (Congressional Record) from govinfo.gov, mapping to a new `CongressionalRecord` model. CREC XML contains daily congressional debates, speeches, and proceedings. We'll create the file handler, DAO, processor using JAXB (from USLM schema or generic), and add a migration for the congressional_records table. This expands to daily records.

## Dependencies
- Task 1.1 (JAXB generated).
- Task 3.1 (Reports complete).

## Estimated Effort
4 hours.

## Status
Not Started (as of September 25, 2025).

## Microgoals
1. **Download USLM CREC Schema**:
   - Run `curl -o src/main/resources/schema/uslm-crec.xsd https://raw.githubusercontent.com/usgpo/uslm/main/uslm-crec.xsd` (if available; use generic or bill.xsd fallback).
   - Verify in schema/ folder.

2. **Generate JAXB for CREC Schema**:
   - Update pom.xml plugin: Add <source>src/main/resources/schema/uslm-crec.xsd</source>.
   - Run `mvn clean generate-sources`.
   - Verify generated classes (e.g., CongressionalRecordJaxb, SpeechJaxb).

3. **Add SourceType.FEDERAL_RECORD_XML**:
   - Edit SourceType.java: Add FEDERAL_RECORD_XML("federal_record.*\\.XML").

4. **Create FederalRecordXmlFile**:
   - Extend XmlFile in processors/federal/record/.
   - Parse filename "CREC-2025-01-03-pt1.xml" → date=2025-01-03.
   - Override getSourceType() to FEDERAL_RECORD_XML.

5. **Create FsFederalRecordXmlDao**:
   - Implement SourceFileFsDao<FederalRecordXmlFile>.
   - Staging dir: staging/federal-records/.
   - Pattern: "CREC.*\\.XML".
   - Archive to archive/federal-records/<year>/crec/.

6. **Create CongressionalRecord Model**:
   - New class CongressionalRecord in legislation/record/ (recordId, date, volume, pages, speeches).
   - Fields: RecordId (date, part), LocalDate date, int volume, List<Speech> speeches.

7. **Create Speech Model**:
   - New class Speech (speaker, text, page).

8. **Create FederalRecordXmlProcessor**:
   - Extend AbstractLegDataProcessor.
   - getSupportedType(): LegDataFragmentType.RECORD (assume enum).
   - process(LegDataFragment): Unmarshal to CongressionalRecordJaxb, map to CongressionalRecord/Speech.
   - Save via RecordDao (assume base or new).

9. **Migration for Congressional Records Table**:
   - New file V20250925.0004__federal_congressional_records.sql: CREATE TABLE congressional_records (record_id VARCHAR PRIMARY KEY, date DATE, volume INTEGER, speeches JSONB); CREATE INDEX idx_records_date ON congressional_records (date).

10. **Add Sample CREC XML**:
    - Create src/test/resources/federal-samples/records/CREC-2025-01-03-pt1.xml (minimal <congressional-record> with <speech>).

11. **Unit Test**:
    - FederalRecordXmlProcessorTest: Unmarshal sample, assert RecordId date=2025-01-03, 1 speech (speaker="Speaker Name", text length >0).

12. **Integration Test**:
    - Extend IngestionIntegrationIT: Ingest sample, verify DB (congressional_records table has entry with 1 speech).

13. **Verify**:
    - mvn clean compile (no errors).
    - mvn clean test (unit/integration pass).

## Completion Criteria
- Classes compile.
- JAXB unmarshals sample to CongressionalRecordJaxb.
- Processor maps to CongressionalRecord with 1 speech.
- Unit test asserts date=2025-01-03, speeches size=1.
- Integration test ingests, DB has record with speeches JSONB (query COUNT(*) FROM congressional_records =1).
- Migration applied (table exists, index on date).

After completion, ready for Task 3.3 (Hearings).