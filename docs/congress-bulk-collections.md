# Congress.gov Bulk Data Collections Guide

## Overview
Congress.gov provides bulk XML/JSON downloads at https://www.congress.gov/bulkdata (recent congresses, e.g., 118th+). Complements govinfo for historical. Use MODS schema for metadata; integrate via same pipeline as govinfo.

## Available Collections
- **BILLS**: Bill text/status (XML/JSON).
- **RESOLUTIONS**: Similar to bills.
- **REPORTS**: Committee reports (CRPT).
- **CONGRESSIONAL-RECORD**: Daily debates (CREC).
- **HEARINGS**: Committee hearings (CHRG).
- **CALENDARS**: Legislative calendars (CCAL).
- **NOMINATIONS**: Executive nominations.
- **TREATIES**: International treaties.
- **DOCUMENTS**: General docs (CDOC).
- **PRINTS**: Committee prints (CPRT).

## Access & Formats
- Download: ZIPs per congress/collection (e.g., BILLS-118.zip).
- Formats: XML (primary, MODS-wrapped); JSON available.
- Schemas: MODS extensions; samples in downloads.
- API Complement: Congress.gov API for search/retrieve (requires key).

## Integration Notes
- **Staging**: `staging/congress-<collection>/`.
- **SourceType**: FEDERAL_BILL (for BILLS/RESOLUTIONS), etc.
- **Processors**: Reuse federal processors; adapt MODS <mods> metadata.
- **Mapping Example (BILLS)**: <bill legislation-id> → BaseBillId; <mods titleInfo> → title.
- **Deltas**: Check last-modified; use API for recent.

## Tools/Scripts
- Download: Extend `tools/fetch_govinfo_bulk.py` to congress.gov (curl ZIPs).
- Validation: Compare schemas with govinfo uslm.

Reference govinfo-integration.md for shared pipeline; use prompts for code.