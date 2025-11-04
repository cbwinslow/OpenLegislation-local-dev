# Data Model Documentation by Source Site

This index points to existing references that describe how OpenLegislation models data from each legislative content source. Use it as a quick guide when you need to understand or extend the schema for a particular site.

## Reference Table

| Site / Source | Primary Documentation | Key Data Model Notes |
| --- | --- | --- |
| **NYSenate (State)** | [`docs/data_model.md`](data_model.md) | Core bill, amendment, action, sponsor, committee, vote, and member relationships for the state platform. |
| **GovInfo & Congress.gov (Federal)** | [`docs/data_model.md`](data_model.md), [`docs/federal_ingestion_system_README.md`](federal_ingestion_system_README.md) | Federal extensions including staging tables, member/committee/social models, and ingestion flow mapping GovInfo XML/JSON to OpenLeg entities. |
| **Database Schema Reference** | [`docs/database_schema_documentation.md`](database_schema_documentation.md) | Detailed PostgreSQL column definitions for bill, member, committee, vote, and related tables. |
| **Additional Sources (Assembly, CREC, FR, CFR)** | [`docs/federal-sources-mapping.md`](federal-sources-mapping.md), [`docs/government_data_sources_research.md`](government_data_sources_research.md) | Guidance for integrating new sites with mappings to existing or new entities. |

## NYSenate (State) Data Model

The core OpenLegislation data model describes state-level bills, amendments, actions, sponsors, members, committees, and votes. It documents entity identities, relationships, and ingestion flow from SOBI XML into the master tables, providing a foundation for any additional source integration. Refer to [`docs/data_model.md`](data_model.md) for the authoritative details on each entity and the relationships among them.【F:docs/data_model.md†L1-L85】

## GovInfo & Congress.gov (Federal) Data Model

Federal ingestion reuses the core OpenLegislation entities while adding staging tables and federal-specific models. The integration guide shows how GovInfo XML maps into bill, action, sponsor, and text entities before deduplication. The federal ingestion README elaborates on dedicated member, committee, social media, and extended bill tables introduced for federal coverage.【F:docs/data_model.md†L86-L128】【F:docs/federal_ingestion_system_README.md†L24-L111】

## Database Schema Reference

For precise column-level expectations, use the shared database schema reference. It lists each table, column, type, and constraints so developers can align ingest pipelines and data migrations with the production schema enforced by Flyway.【F:docs/database_schema_documentation.md†L1-L210】

## Additional State and Federal Sources

Planning documents capture how future sources (e.g., NY Assembly, Congressional Record, Federal Register, CFR) should map to existing entities or motivate new ones. These guides highlight parsing strategies, processor extensions, and schema updates necessary to onboard each site into the OpenLegislation data model portfolio.【F:docs/federal-sources-mapping.md†L1-L18】【F:docs/government_data_sources_research.md†L1-L69】

## How to Use This Index

1. Start with the reference table to identify the best documentation for the site you are working with.
2. Review the detailed sections above to understand the scope of the data model coverage and where new extensions may be needed.
3. Consult the linked documents for field-level specifications, ingestion pipelines, and schema definitions relevant to that site.
