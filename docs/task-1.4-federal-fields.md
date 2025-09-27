# Task 1.4: Add Federal Fields to Bill Model (Med)

## Overview
This task adds federal-specific fields to the `Bill` model (e.g., `federalCongress` int, `federalSource` String) to store metadata like congress number and source (govinfo/congress.gov). This enables querying/filtering federal bills and supports the mapping in `FederalBillXmlProcessor`. From codebase review, `Bill.java` is in `legislation/bill/`, so we'll extend it with getters/setters. Add a Flyway migration to persist the fields in the `bills` table.

## Dependencies
- Task 1.1 (JAXB generated).
- Task 1.2 (JAXB integrated in processor).
- Task 1.3 (BillActionType extended).

## Estimated Effort
1 hour.

## Status
Not Started (as of September 24, 2025).

## Microgoals
1. **Add Fields to Bill.java**:
   - Open `src/main/java/gov/nysenate/openleg/legislation/bill/Bill.java`.
   - Add private fields: `private Integer federalCongress; private String federalSource = "unknown";`.
   - Add getters/setters: `public Integer getFederalCongress() { return federalCongress; } public void setFederalCongress(Integer federalCongress) { this.federalCongress = federalCongress; }` (similar for federalSource).

2. **Update FederalBillXmlProcessor**:
   - In `mapToBill()`, set `bill.setFederalCongress(sourceFile.getCongress()); bill.setFederalSource("govinfo");`.
   - Ensure it compiles (import Bill if needed).

3. **Create Flyway Migration**:
   - New file `src/main/resources/sql/migrations/V20250925.0001__federal_bill_fields.sql`:
     ```
     ALTER TABLE master.bills ADD COLUMN federal_congress INTEGER;
     ALTER TABLE master.bills ADD COLUMN federal_source TEXT DEFAULT 'unknown';
     CREATE INDEX idx_bills_federal_congress ON master.bills (federal_congress);
     ```
   - Run `mvn flyway:migrate` to apply.

4. **Update Tests**:
   - In `FederalBillXmlProcessorTest.java`, assert `bill.getFederalCongress() == 119`.
   - In integration test, query DB: `SELECT federal_congress FROM bills WHERE print_no = 'HR 1'`, assert =119.

5. **Verify Compilation & Tests**:
   - Run `mvn clean compile` (no errors).
   - Run `mvn clean test` (assertions pass, e.g., federalCongress=119 in unit/integration).

## Completion Criteria
- `Bill.java` compiles with new fields/getters/setters.
- Migration applied (query DB: `SELECT * FROM information_schema.columns WHERE table_name='bills' AND column_name IN ('federal_congress', 'federal_source')` returns rows).
- Processor sets fields (unit test: assert bill.getFederalCongress() == 119).
- Integration test verifies DB persistence (assert federal_congress=119 for ingested bill).
- No runtime errors in mapping/save.

After completion, Phase 1 is 100% done, ready for Phase 2 (Core Implementation: End-to-End Test for Bills).
