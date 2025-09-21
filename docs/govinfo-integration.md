GovInfo / Congress.gov Integration Notes

Purpose
- Describe how to map govinfo/congress bulk XML into OpenLegislation and provide starter artifacts (models and migration template).

Where to start
- Fetch sample govinfo package(s) for the collections you care about (e.g. `BILLS`, `BILLSTATUS`, `BILLSUM`). GovInfo provides package-level schema files in each bulk data directory.

High-level mapping suggestions
- Filesystem & DAO:
  - Reuse `processors/sourcefile/xml/FsXmlDao.java` behavior. Create a staging subdir (e.g. `staging/govinfo`) and a `GovInfoXmlFile` class similar to `processors/bill/xml/XmlFile.java` for filename -> published datetime parsing.
- Identifier mapping:
  - Map govinfo `billNumber`/`congress`/`session` info to `BaseBillId`.
  - Map `sponsor`/`cosponsors` to the existing bill sponsor model used by bill processors.
- Actions & status:
  - Map govinfo action history to the same structure used by `XmlBillActionAnalyzer`.
- Texts & versions:
  - GovInfo often contains multiple versions of bill text. Decide which to store in `bill_text` table or create a version table similar to existing `text_diff` usage.

Next concrete step: pull a small sample of govinfo bill XML and produce a mapping table: (source xpath -> OpenLegislation model/SQL column). Use that table to scaffold parsers and migrations.

***
