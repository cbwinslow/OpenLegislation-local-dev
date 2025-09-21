GovInfo BILLS (119th) — Representative XPath -> OpenLegislation mapping

This document contains representative XPaths commonly found in GovInfo BILLS package XML files and suggested mappings to OpenLegislation models and SQL columns.

Note: exact element names may vary; use this as a template to create a precise mapping after downloading sample XML files.

- `/bill` (root)
  - map to: top-level bill package record

- `/bill/legislativeIdentifier` or `/bill/billNumber`
  - map to: `BaseBillId` (congress + bill_number)
  - SQL: `govinfo_bill.congress`, `govinfo_bill.bill_number`

- `/bill/officialTitle`
  - map to: `Bill.title`
  - SQL: `govinfo_bill.title`

- `/bill/shortTitle`
  - map to: `Bill.short_title`

- `/bill/introductionDate` or `/bill/introducedDate`
  - map to: `Bill.introduced_date`
  - SQL: `govinfo_bill.introduced_date`

- `/bill/sponsor` (with nested `name`, `party`, `state`, `district`)
  - map to: `Bill.sponsor` (BillSponsor)
  - SQL: `govinfo_bill.sponsor_name`, `sponsor_party`, `sponsor_state`

- `/bill/cosponsors/cosponsor[]`
  - map to: `Bill.coSponsors` — create `govinfo_bill_cosponsor` table

- `/bill/committees/committee[]`
  - map to: `Bill.past_committee` list

- `/bill/actions/action[]` (each has `date`, `chamber`, `text`, `type`)
  - map to: `BillAction` and analyzer (like `XmlBillActionAnalyzer`)
  - SQL: `govinfo_bill_action(govinfo_bill_id, action_date, chamber, description, action_type)`

- `/bill/textVersions/textVersion[]` (has `versionId`, `format`, `href` or content)
  - map to: `BillText` / `govinfo_bill_text`

After you fetch real sample files, replace these representative XPaths with exact XPaths and update the SQL migration to include constraints and indexes.
