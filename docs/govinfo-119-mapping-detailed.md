GovInfo BILLS (119th) — Detailed XPath -> OpenLegislation mapping (representative)

Notes
- GovInfo element names vary slightly between collections; this is a practical, ready-to-edit mapping you can refine with real sample XML files.
- Left column shows representative XPath or element path. Middle column shows the OpenLegislation model/field. Right column shows suggested SQL storage (new `govinfo_*` tables or mapping to existing `master.*`).

1) Identity & metadata
- `/bill/congress` -> `BaseBillId.congress` -> `govinfo_bill.congress`
- `/bill/billNumber` or `/bill/legislativeIdentifier` -> `BaseBillId.printNo` -> `govinfo_bill.bill_number`
- `/bill/billType` -> `Bill.type` -> `govinfo_bill.bill_type`
- `/bill/documentNumber` -> external doc ref -> `govinfo_doc_refs(external_id, type)`
- `/bill/packageNumber` -> package id -> `govinfo_doc_refs`

2) Titles & subjects
- `/bill/officialTitle` -> `Bill.title` -> `govinfo_bill.title`
- `/bill/shortTitle` -> `Bill.short_title` -> `govinfo_bill.short_title`
- `/bill/subjects/subject[]` -> `Bill.subjects` -> `govinfo_bill_subject(govinfo_bill_id, subject)`

3) Sponsors & membership
- `/bill/sponsor/name` -> `BillSponsor.member or name` -> `govinfo_bill.sponsor_name` (+ mapping to member ids when possible)
- `/bill/sponsor/party`, `/state`, `/district` -> `BillSponsor.party/state/district` -> `govinfo_bill.sponsor_party`, `sponsor_state`, `sponsor_district`
- `/bill/cosponsors/cosponsor[]` (with `name`, `sponsorType`, `date`) -> `Bill.coSponsors` -> `govinfo_bill_cosponsor(govinfo_bill_id, name, party, state, date_added, sponsor_type)`

4) Dates & key timestamps
- `/bill/introductionDate` or `/bill/introducedDate` -> `Bill.introducedDate` -> `govinfo_bill.introduced_date`
- `/bill/lastActionDate` -> `Bill.latest_action_date` -> `govinfo_bill.latest_action_date`
- `/bill/committeeReferralDate` (per committee) -> `Bill.committeeReferralDates` -> `govinfo_bill_committee(govinfo_bill_id, committee_name, referred_date)`

5) Actions & status history
- `/bill/actions/action[]` where each action has `/action/date`, `/action/chamber`, `/action/text`, `/action/type` -> `BillAction` list -> `govinfo_bill_action(govinfo_bill_id, action_date, chamber, description, action_type, sequence_no)`
- Use existing `XmlBillActionAnalyzer` logic as a guide to derive `status`, `milestones`, `publishStatuses` fields.

6) Texts / versions
- `/bill/textVersions/textVersion[]` with fields `versionId`, `format` (e.g., html, text), `date`, and either inline content or `href` -> `BillText` versions -> `govinfo_bill_text(govinfo_bill_id, version_id, text_format, content, created_at)`
- For large text bodies, store plain text and optionally an HTML rendition; consider storing content in `bytea` or as `text` depending on size.

7) Amendments & diffs
- `/bill/amendments/amendment[]` -> map to `BillAmendment` objects -> either `govinfo_bill_amendment` or reuse `master.bill_amendment_text_diff` patterns (see existing `V20200325.0913__add_text_diff_table.sql`).

8) Committee and procedural metadata
- `/bill/committees/committee[]` -> `Bill.pastCommittees` -> `govinfo_bill_committee` table
- `/bill/committeeReports/report[]` -> link to `govinfo_doc_refs` and `master.committee_reports` if integrating

9) Cross references & related documents
- `/bill/relatedDocuments/document[]` -> `govinfo_doc_refs(govinfo_bill_id, external_id, rel_type)`

10) Identifiers for mapping to OpenLeg models
- Create adapter helpers to map govinfo participant names -> OpenLeg `Member`/`Person` records (match by name + state + party + session). Store external ids on `person` rows for provenance.

Practical notes
- For first pass, ingest into `govinfo_*` tables to avoid accidental collisions with existing master data. Later create mappers to deduplicate/merge into `master.*` tables.
- Use the Python prototype (`tools/govinfo_etl_prototype.py`) to iterate on parsing XPaths quickly. Once mapping is stable, port logic to Java `processors/bill/govinfo/*` processors and add unit tests under `src/test/resources/processor/govinfo/`.
- When you provide a few sample XML files I will update this mapping to exact XPaths and generate a Flyway migration ready to apply.
