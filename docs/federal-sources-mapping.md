# Additional Federal/State Data Sources & Java Model Mappings

## New Sources
- **Congressional Record (CREC)**: GovInfo API (`/collections/CREC`). XML with `<speech>`, `<debate>`. Ingest: Extend `tools/fetch_govinfo_bulk.py --collection CREC`. Map to new `Transcript` class (fields: `date`, `chamber`, `content` via `@XmlElement`).
- **Federal Register (FR)**: GovInfo (`/collections/FR`). XML `<fr-notice><title>`. Map to `LawDocument` (add `regulationType=FR`, parse `<sections>` to `LawTreeNode`).
- **CFR**: Bulk XML from GovInfo. Map to `Law` (title/part/section hierarchy matches existing `law/` structure).
- **NY Assembly**: XML from `https://nyassembly.gov/leg/`. Mirror Senate; map `<bill>` to `Bill` (align `billNo`, `sponsors`).

## Mapping Patterns
Follow `processors/bill/xml/XmlBillTextProcessor.java`:
1. Parse filename/timestamp → `SourceFile` (e.g., `crec-2025-09-25.xml` → `SourceType.FEDERAL_CREC`).
2. JAXB unmarshal → Model (e.g., `<actions><action date="...">` → `BillAction.setDate(...)`).
3. Persist via `BillDao.insertBill(bill)`.
4. Index: `ElasticSearchService.index(bill)`.

Examples:
- CREC `<page>` → `TranscriptPage` (new subclass of `BaseObject` with `pageNumber`, `content`).
- FR `<agency>` → `BillSponsor` (adapt for regulatory authors).

Update Flyway: Add migrations for new fields (e.g., `ALTER TABLE bill ADD COLUMN federal_source VARCHAR`).

Test: Use `src/test/resources/federal-samples/`; run `mvn test`.
