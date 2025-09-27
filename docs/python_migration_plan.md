# Python Migration Plan

## Current State Overview
- Java sources: 915 `.java` files under `src/main/java`, including 193 classes in `legislation/*` relevant to bills, agendas, calendars, committees, laws, members, and transcripts.
- Python models: 20 Pydantic models in `models/` covering a subset of domain entities (bill ids, agendas, calendars, members, etc.) with many placeholder methods and missing enums.
- Ingestion utilities: Python scripts under `tools/` (e.g., `govinfo_bill_ingestion.py`, `bulk_ingest_govinfo.py`) already implement portions of the new pipeline but rely on incomplete domain models.
- Database schema: Flyway migrations in `src/main/resources/sql/migrations` define PostgreSQL tables (`master.*`, ingestion tracking tables, etc.).

## Migration Goals
1. Replace all Java model, enum, and utility classes required by ingestion and API layers with idiomatic Python modules.
2. Remove Java-only dependencies from ingestion pipeline so that GovInfo data can be processed end-to-end in Python.
3. Maintain parity with existing database schema and serialization formats to avoid breaking downstream consumers.

## Work Streams
1. **Domain Model Porting**
   - Target packages: `legislation/bill`, `legislation/committee`, `legislation/calendar`, `legislation/agenda`, `legislation/law`, `legislation/member`, `legislation/transcripts`.
   - Deliverables: Pydantic models/enums mirroring Java APIs (fields, helper methods, equality/hash semantics).
   - Approach: start with bill-related classes (`BillType`, `BillStatusType`, `BillStatus`, `BillAction`, `BillSponsor`, `BillVote*`, `BillAmendment`) then expand outward.

2. **Service/Utility Translation**
   - Identify Java services used by ingestion (XML processors, mappers, DAO helpers).
   - Port logic to Python modules placed under `src/pipeline/` or `tools/`.
   - Replace Spring components with functional/services patterns leveraging existing Python settings and DB utilities.

3. **API Alignment**
   - Document Java controller behaviors still required.
   - Decide whether to expose equivalent functionality via FastAPI/Flask (future milestone) or leave Java REST while ingestion migrates first.

4. **Test Coverage & Validation**
   - Mirror Java unit tests with `pytest` suites located in `tools/tests/`.
   - Add contract tests ensuring generated data matches schemas and DB constraints.

## Immediate Next Steps
1. Generate class inventory mapping Java -> Python modules with status (converted, pending, blocked).
2. Port critical enums and value objects for bills (`Chamber`, `BillType`, `BillStatusType`, `CommitteeId`, `BillStatus`, `BillAction`).
3. Replace placeholder Pydantic models with SQLAlchemy-backed entities under `src/db/models/` so Java POJOs (Bill, BillAmendment, Sponsor, Member, SessionMember, Committee) have full Python equivalents.
4. Finalize GovInfo ingestion scripts to exercise new models and hit the database (see `govinfo_bulkdata_ingestion.md`).

## Tooling Suggestions
- Write a helper script to parse Java class signatures (using `javalang` or simple regex) and scaffold Python Pydantic models to accelerate translation.
- Enforce type checking with `mypy` once models are complete.
- Configure linting (`ruff`) to keep Python style consistent.

## Risks / Open Questions
- Some Java classes depend on third-party libraries (Guava, Joda-Time, etc.) whose semantics must be matched carefully.
- Controllers and services form large graphs of dependencies; prioritization is required to avoid "boiling the ocean".
- Need clarity on decommission timeline for the Java API and how deployment environments will host the Python replacement.

## Tracking
- Maintain a checklist (e.g., `docs/python_migration_status.md`) so progress is measurable.
- Define acceptance criteria per package (e.g., "All enums ported", "All value objects ported", "All DAO helpers replaced").
