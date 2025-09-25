# Task 2.2: Create FederalLawXmlFile, DAO, Processor for PLAW (High)

## Overview
This task implements support for PLAW (Public Laws) from govinfo.gov, mapping to the `LawDocument` model. PLAW XML contains enacted laws with sections/amendments. We'll create the file handler, DAO, and processor similar to bills, using JAXB for unmarshaling (from USLM law schema). This completes core legislative data (bills → laws).

## Dependencies
- Task 1.1 (JAXB generated for law schema).
- Task 1.2 (JAXB integrated).
- Task 1.4 (Federal fields in models).

## Estimated Effort
4 hours.

## Status
Not Started (as of September 24, 2025).

## Microgoals
1. **Download USLM Law Schema**:
   - Run `curl -o src/main/resources/schema/uslm-law.xsd https://raw.githubusercontent.com/usgpo/uslm/main/uslm-law.xsd`.
   - Verify in schema/ folder.

2. **Generate JAXB for Law Schema**:
   - Update pom.xml plugin: Add <source>src/main/resources/schema/uslm-law.xsd</source>.
   - Run `mvn clean generate-sources`.
   - Verify generated classes in target/generated-sources/xjc/ (e.g., LawDocumentJaxb, SectionJaxb).

3. **Create FederalLawXmlFile**:
   - Extend XmlFile in processors/federal/law/.
   - Parse filename "PLAW-119th-PUB-L-1.xml" → congress=119, lawNumber="1".
   - Override getSourceType() to FEDERAL_LAW_XML.

4. **Create FsFederalLawXmlDao**:
   - Implement SourceFileFsDao<FederalLawXmlFile>.
   - Staging dir: staging/federal-laws/.
   - Pattern: "PLAW.*\\.XML".
   - Archive to archive/federal-laws/<year>/plaw/.

5. **Create FederalLawXmlProcessor**:
   - Extend AbstractLegDataProcessor.
   - getSupportedType(): LegDataFragmentType.LAW (assume enum).
   - process(LegDataFragment): Unmarshal to LawDocumentJaxb, map to LawDocument/LawSection/LawTree.
   - Mapping: <public-law> number/date → LawDocId, <section> → LawSection (heading, content).
   - Save via LawDao or base.

6. **Add Sample PLAW XML**:
   - Create src/test/resources/federal-samples/laws/PLAW-119th-PUB-L-1.xml (minimal <public-law> with sections).

7. **Unit Test**:
   - FederalLawXmlProcessorTest: Unmarshal sample, assert LawDocId, 1 section.
   - Integration: Ingest to DB, verify laws table.

8. **Migration for Law Tables**:
   - V20250925.0002__federal_law_tables.sql: CREATE TABLE laws (doc_id, congress, title, effective_date); CREATE TABLE law_sections (law_id, section_num, heading, content).

9. **Verify**:
   - mvn clean compile (no errors).
   - mvn clean test (unit/integration pass).

## Completion Criteria
- Classes compile.
- JAXB unmarshals sample to LawDocumentJaxb.
- Processor maps to LawDocument with 1 section.
- Unit test asserts doc_id="PUB-L-1", congress=119.
- Integration test ingests, DB has law with sections (query COUNT(*) FROM laws =1).
- Migration applied (tables exist).

After completion, ready for Task 2.3 (Bulk Script).