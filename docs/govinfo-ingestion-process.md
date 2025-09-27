# GovInfo Ingestion Process Documentation

## Overview
This document outlines the process for ingesting data from GovInfo API into OpenLegislation. The process uses the GovInfoApiProcessor to fetch JSON data, map to Java models (Bill, LawDocument, etc.), and persist to PostgreSQL via JPA. All collections (BILLS, FR, CFR, CREC, etc.) are supported with mappings.

## Prerequisites
- API key in .env (GOVINFO_API_KEY=yourkey from api.govinfo.gov).
- PostgreSQL running (openlegdb DB).
- Elasticsearch for indexing (optional).
- Maven compiled project.

## Step-by-Step Process
1. **Load Config**: Source .env to set GOVINFO_API_KEY.
2. **Compile**: `mvn clean compile` (generates JAXB if needed).
3. **Run Processor**: `mvn exec:java -Dexec.mainClass="gov.nysenate.openleg.processors.federal.GovInfoApiProcessor" -Dexec.args="--collection BILLS --congress 119 --limit 10"`.
   - Fetches from /v1/search?collection=BILLS&congress=119.
   - Maps JSON to models (e.g., title → Bill.setTitle()).
   - Persists: BillDao.save(bill) → bill table.
4. **Verify**: Query DB (e.g., `psql openlegdb -c "SELECT * FROM bill WHERE congress_number=119;"`).
5. **Index**: Automatic via ElasticSearchService (if configured).

## Mappings (API JSON → Java → SQL)
- **BILLS**: {"results": [{"title": "HR 1", "sponsors": [...], "actions": [...]}]} → Bill (billNo="HR1", session=119, sponsors=BillSponsor list, actions=BillAction list). SQL: INSERT INTO bill (title, congress_number=119); INSERT INTO bill_sponsor (...).
- **BILLSTATUS**: {"status": {"actions": [...]}} → Append BillAction to existing Bill. SQL: UPDATE bill_action SET text=... WHERE bill_id=... .
- **FR**: {"notice": {"title": "Rule", "agency": "DOE"}} → LawDocument (lawId="FR-2025-123", metadata={"agency": "DOE"}). SQL: INSERT INTO law_document (title, metadata JSONB).
- **CFR**: {"title": {"parts": [...]}} → Law (title/part/section). SQL: INSERT INTO law (title, sections JSONB).
- **CREC**: {"record": {"date": "2025-09-25", "debates": "Text"}} → Transcript (date, content). SQL: INSERT INTO transcript (date, content).
- **PLAW**: {"law": {"sections": [...]}} → LawDocument. SQL: law_document.
- **Other**: HEARINGS → New Hearing model/table; similar for REPORTS, CALENDARS.

## Error Handling
- Rate limit: 1000/day—use --limit 50, paginate with offset.
- No key: Falls back to public metadata (no full data).
- Invalid JSON: Log and skip.

## Testing
- Unit: mvn test (mock API responses).
- Integration: Run with --limit 1, check DB counts.
- Bulk: --limit 1000 (requires key).

Update: Extend for new collections via processor methods.
