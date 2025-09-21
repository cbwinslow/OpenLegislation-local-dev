This repository is a Java-based legislative data platform (Open Legislation) focused on ingesting, processing, indexing, and serving legislative content.

Keep responses concise and action-oriented. When making code changes, reference the concrete files below and follow existing patterns (DAO -> Processor -> Service -> API controllers). Prioritize minimal, focused edits and include unit tests when touching parsing logic.

Quick architecture notes
- Backend: Java (Maven) under `src/main/java/gov/nysenate/openleg/`.
- Data processing pipeline: `processors/` package. Source file DAOs live in `processors/sourcefile`; per-domain processors in `processors/{bill,law,calendar,agenda,committee}`.
- Source files: incoming XMLs are read from the `staging/xmls` directory via `processors/sourcefile/xml/FsXmlDao.java` and `processors/sourcefile/sobi` for older SOBI formats.
- Domain models and persistence: legislative models live under `legislation/` and search/update layers under `search/` and `updates/`.
- Web/API: controllers under `api/` expose data and admin endpoints (e.g. `ProcessService` endpoints used to trigger processing).

Developer workflows (important commands)
- Build & DB migrate: `mvn compile flyway:migrate` (project uses Java 17 and Flyway migrations in `src/main/resources/sql/migrations`).
- Run in Tomcat (typical dev): import as a Maven project in IntelliJ and run `legislation:war exploded` as described in `docs/backend/index.md`.
- Trigger processing (after placing XML files into `env.staging/xmls`):
  - POST to `http://localhost:8080/api/3/admin/process/run` with admin credentials set in `src/main/resources/app.properties`.

Project-specific patterns and conventions
- File naming & timestamp parsing: XML source filenames follow the pattern parsed by `processors/bill/xml/XmlFile.java` (regex with date/time and type). Use this class for any filename/time parsing.
- Source types: `SourceType` enum drives per-file routing. New ingestion should implement `SourceFileFsDao` for filesystem source access and a `LegDataProcessor` subclass to parse domain objects.
- Encoding edge-cases: files containing `_SENAGEN_` use `CP1252` encoding (see `FsXmlDao.toXmlFile`). Preserve this behavior for any new file ingestion.
- XML mapping libraries: project includes `jackson-dataformat-xml` and `jaxb` dependencies (see `pom.xml`). Follow existing JAXB/Jackson patterns used in `processors/*/xml/*`.
- Archiving: source archiving logic uses `environment.getArchiveDir()` in DAOs; prefer reusing `SourceFileFsDao.archiveSourceFile` behavior to move processed files.

Where to look for parsing examples (copy patterns)
- Bills: `src/main/java/gov/nysenate/openleg/processors/bill/xml/` (many `Xml*Processor` classes).
- Law: `src/main/java/gov/nysenate/openleg/processors/law/` and `legislation/law/` model classes.
- Calendars/Agendas: `processors/calendar/` and `legislation/calendar/`.
- Source file DAOs: `processors/sourcefile/xml/FsXmlDao.java` and `processors/sourcefile/sobi/*`.

Integration guidance for govinfo.gov / congress.gov bulk XML
- Big picture: govinfo and congress.gov provide XML schemas for federal legislative documents (bills, committee reports, CRs). OpenLegislation is structured around per-source file processors that parse XML into domain models and persist/update index. Treat govinfo/congress XML as a new SourceType and implement a processing pipeline that maps their elements to OpenLegislation domain models.
- Steps to integrate (practical, discoverable):
  1. Add a new `SourceType` value (if needed) and implement a `SourceFile` representation analogous to `XmlFile` (filename parsing, published date extraction).
  2. Implement a `SourceFileFsDao` to read govinfo files from a staging dir (reuse `FsXmlDao` logic).
  3. Create `processors/{bill,law,...}/govinfo/` or `processors/federal/` to house parsers that map govinfo/congress fields to existing models. Start by copying structure from `processors/bill/xml/XmlBillTextProcessor` and similar classes.
  4. Map id fields carefully: OpenLegislation uses specific identifiers (e.g. `BaseBillId`, `LawDocId`). Create small adapters that translate govinfo `bill/legislation-id`, `congress-bill-id`, or `report-number` into these models.
  5. Respect archiving & encoding conventions and use existing `LegDataProcessService` to wire new processors into the processing flow.

Schema analysis hints (where to compare)
- OpenLegislation examples to map fields from:
  - Filename/timestamp parsing: `processors/bill/xml/XmlFile.java`
  - Bill text and actions mapping: `processors/bill/xml/XmlBillTextProcessor.java`, `XmlBillActionAnalyzer.java`
  - Law document ids and tree: `legislation/law/LawDocId.java`, `legislation/law/LawTree.java`
- Govinfo/congress.gov schema locations (agent should fetch these live):
  - govinfo bulk data XML (package schema and sample XML files)
  - congress.gov bulk data (bill XML schema and sample files)
  - When analyzing schemas, produce a short mapping table (source XML path -> OpenLegislation model field) for the most important fields: identifiers, title, sponsors, actions, text, publication dates.

When to ask for human help
- If the source XML contains fields with unclear semantic equivalents (e.g., nested amendment histories, multi-version text deltas), summarize the ambiguity and propose a mapping; ask which OpenLegislation model should own the data.
- If new external dependencies are required for parsing (non-standard encodings, large streaming parsers), propose them and include CI/build impact.

Pull request style
- Keep changes small and testable. Include unit tests under `src/test/java` using existing test fixtures in `src/test/resources` (look at `testing_utils` and `processor` test resources).
- Update `docs/backend/index.md` only when adding new setup steps for federal data ingestion.

If you modify processing behavior, run or add tests that exercise `processors/*` classes. Reference example test utilities in `src/test/java/testing_utils/`.

Ask for feedback on any unclear repository-specific behavior or when you need access to sample govinfo/congress XML documents to produce concrete field mappings.
