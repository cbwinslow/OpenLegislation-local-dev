# Task 3.1: Implement Reports (CRPT/CPRT) (High)

## Overview
This task implements support for CRPT/CPRT (Committee Reports) from congress.gov and govinfo.gov, mapping to a new `Report` model. Reports contain committee analysis of bills. We'll create the file handler, DAO, processor using JAXB (from USLM schema), and add a migration for the reports table. This expands the integration to committee reports.

## Dependencies
- Task 1.1 (JAXB generated for report schema).
- Phase 2 (Bills/Laws complete).

## Estimated Effort
4 hours.

## Status
Not Started (as of September 25, 2025).

## Microgoals
1. **Download USLM Report Schema**:
   - Run `curl -o src/main/resources/schema/uslm-report.xsd https://raw.githubusercontent.com/usgpo/uslm/main/uslm-report.xsd` (if available; use bill.xsd if no specific).
   - Verify in schema/ folder.

2. **Generate JAXB for Report Schema**:
   - Update pom.xml plugin: Add <source>src/main/resources/schema/uslm-report.xsd</source>.
   - Run `mvn clean generate-sources`.
   - Verify generated classes (e.g., ReportJaxb, CommitteeJaxb).

3. **Add SourceType.FEDERAL_REPORT_XML**:
   - Edit SourceType.java: Add FEDERAL_REPORT_XML("federal_report.*\\.XML").

4. **Create FederalReportXmlFile**:
   - Extend XmlFile in processors/federal/report/.
   - Parse filename "CRPT-119th-HRPT1.xml" → congress=119, reportNumber="1".
   - Override getSourceType() to FEDERAL_REPORT_XML.

5. **Create FsFederalReportXmlDao**:
   - Implement SourceFileFsDao<FederalReportXmlFile>.
   - Staging dir: staging/federal-reports/.
   - Pattern: "CRPT.*\\.XML" or "CPRT.*\\.XML".
   - Archive to archive/federal-reports/<year>/crpt/.

6. **Create Report Model**:
   - New class Report in legislation/report/ (reportId, congress, title, text, committee).
   - Fields: ReportId (congress, reportNumber), String title, String text, String committee.

7. **Create FederalReportXmlProcessor**:
   - Extend AbstractLegDataProcessor.
   - getSupportedType(): LegDataFragmentType.REPORT (assume enum).
   - process(LegDataFragment): Unmarshal to ReportJaxb, map to Report (reportId, title, text).
   - Save via ReportDao (assume base or new).

8. **Migration for Reports Table**:
   - New file V20250925.0003__federal_reports.sql: CREATE TABLE reports (report_id VARCHAR PRIMARY KEY, congress INTEGER, title TEXT, text TEXT, committee TEXT); CREATE INDEX idx_reports_congress ON reports (congress).

9. **Add Sample Report XML**:
   - Create src/test/resources/federal-samples/reports/CRPT-119th-HRPT1.xml (minimal <report> with title, text).

10. **Unit Test**:
    - FederalReportXmlProcessorTest: Unmarshal sample, assert ReportId="HRPT1", congress=119, text length >0.

11. **Integration Test**:
    - Extend IngestionIntegrationIT: Ingest sample, verify DB (reports table has entry).

12. **Verify**:
    - mvn clean compile (no errors).
    - mvn clean test (unit/integration pass).

## Completion Criteria
- Classes compile.
- JAXB unmarshals sample to ReportJaxb.
- Processor maps to Report with title, text.
- Unit test asserts reportNumber="1", congress=119.
- Integration test ingests, DB has report (query COUNT(*) FROM reports =1).
- Migration applied (table exists, index on congress).

After completion, ready for Task 3.2 (Congressional Record).
