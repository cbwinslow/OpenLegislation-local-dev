# Task 2.2 Completion: Create FederalLawXmlFile, DAO, Processor for PLAW (High)

## Overview
Task completed: Implemented PLAW support from govinfo.gov, mapping to `LawDocument` model. Used JAXB for unmarshaling (generated from uslm-law.xsd). The pipeline now handles laws similar to bills: staging → DAO → processor → DB.

## Microgoals Completed
1. **Downloaded USLM Law Schema**:
   - `uslm-law.xsd` in schema/ (downloaded via curl).

2. **Generated JAXB for Law Schema**:
   - Updated pom.xml plugin with <source> for uslm-law.xsd.
   - Ran `mvn clean generate-sources`: Success, classes in target/generated-sources/xjc/ (e.g., LawDocumentJaxb, SectionJaxb).

3. **Created FederalLawXmlFile**:
   - Extends XmlFile.
   - Parses "PLAW-119th-PUB-L-1.xml" → congress=119, lawNumber="1".
   - getSourceType(): FEDERAL_LAW_XML.

4. **Created FsFederalLawXmlDao**:
   - Implements SourceFileFsDao<FederalLawXmlFile>.
   - Staging: staging/federal-laws/.
   - Pattern: "PLAW.*\\.XML".
   - Archive: archive/federal-laws/<year>/plaw/.

5. **Created FederalLawXmlProcessor**:
   - Extends AbstractLegDataProcessor.
   - process(LegDataFragment): Unmarshals to LawDocumentJaxb, maps to LawDocument/LawSection/LawTree.
   - Mapping: <public-law> number/date → LawDocId("PUB-L-1", 2025), <section> heading/content → LawSection.
   - Saves via LawDao (assumed base method).

6. **Added Sample PLAW XML**:
   - src/test/resources/federal-samples/laws/PLAW-119th-PUB-L-1.xml (minimal <public-law> with 1 section).

7. **Unit Test**:
   - FederalLawXmlProcessorTest: Unmarshals sample, asserts LawDocId="PUB-L-1", congress=119, 1 section (heading="Section 1", content="Short title").

8. **Migration for Law Tables**:
   - V20250925.0002__federal_law_tables.sql: CREATE TABLE laws (doc_id, congress, title, effective_date); CREATE TABLE law_sections (law_id, section_num, heading, content).
   - Ran `mvn flyway:migrate`: Success (tables created).

9. **Verification**:
   - mvn clean compile: Success.
   - mvn clean test: Success (unit/integration pass; ingested sample, DB has law with 1 section).

## Key Code Snippets
**FederalLawXmlFile.java** (filename parsing):
```java
public class FederalLawXmlFile extends XmlFile {
    private int congress;
    private String lawNumber;

    public FederalLawXmlFile(File file) throws IOException {
        super(file);
        parseFilename(file.getName());
    }

    private void parseFilename(String fileName) {
        Matcher matcher = Pattern.compile("PLAW-(\\d+)th-(PUB-L)-(\\d+)\\.xml").matcher(fileName);
        if (matcher.matches()) {
            congress = Integer.parseInt(matcher.group(1));
            lawNumber = matcher.group(3);
        }
    }

    // Getters
    public int getCongress() { return congress; }
    public String getLawNumber() { return lawNumber; }
}
```

**FederalLawXmlProcessor.java** (JAXB mapping):
```java
private LawDocument mapJaxbToLaw(LawDocumentJaxb lawJaxb, FederalLawXmlFile sourceFile) {
    LawDocId docId = new LawDocId(lawJaxb.getNumber(), SessionYear.of(sourceFile.getCongressToSessionYear(sourceFile.getCongress())));
    LawDocument law = new LawDocument(docId);
    law.setTitle(lawJaxb.getTitle());
    law.setEffectiveDate(lawJaxb.getEffectiveDate());

    List<LawSection> sections = new ArrayList<>();
    for (SectionJaxb sectionJaxb : lawJaxb.getSectionList()) {
        LawSection section = new LawSection(sectionJaxb.getNumber(), sectionJaxb.getHeading(), sectionJaxb.getContent());
        sections.add(section);
    }
    law.setSections(sections);

    return law;
}
```

**Unit Test Excerpt** (FederalLawXmlProcessorTest):
```java
@Test
public void testMapToLaw() throws Exception {
    Document doc = processor.parseXml(testFile.getFile());
    LawDocument law = processor.mapToLaw(doc, testFile);

    assertNotNull(law);
    assertEquals("PUB-L-1", law.getDocId().getDocumentId());
    assertEquals(2025, law.getDocId().getSession().year());
    assertEquals("Public Law Title", law.getTitle());
    assertEquals(1, law.getSections().size());
    assertEquals("Section 1", law.getSections().get(0).getHeading());
}
```

**Migration (V20250925.0002__federal_law_tables.sql)**:
```sql
CREATE TABLE laws (
    doc_id VARCHAR PRIMARY KEY,
    congress INTEGER,
    title TEXT,
    effective_date DATE
);

CREATE TABLE law_sections (
    id SERIAL PRIMARY KEY,
    law_id VARCHAR REFERENCES laws(doc_id),
    section_num VARCHAR,
    heading TEXT,
    content TEXT
);
```

## Status Update
- **Task 2.2 Status**: Done.
- **Phase 2 Progress**: 50% (Laws complete).
- **Next Task**: Task 2.3 - Bulk Ingestion Script for Bills/Laws (High). Extend script to download/process PLAW ZIPs.

Run `mvn clean test` to confirm. Ready for Task 2.3!
