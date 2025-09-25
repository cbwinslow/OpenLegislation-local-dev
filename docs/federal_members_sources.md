# Federal Members/Entities Data Sources: Congress.gov and GovInfo.gov

This document outlines data sources for fetching U.S. Congress members (senators, representatives) and related entities (committees, leadership) from official federal sources. Focus is on structured data suitable for ingestion into OpenLegislation's entity model (e.g., [Member](src/main/java/gov/nysenate/openleg/legislation/member/Member.java), [Committee](src/main/java/gov/nysenate/openleg/legislation/committee/Committee.java)). Data includes biographies, terms, committees, contact info.

## 1. Congress.gov API
Congress.gov provides a free REST API (v3) for legislative data, including members. Requires API key (register at https://api.congress.gov/). Rate limit: 1000 requests/day.

### Base URL
- `https://api.congress.gov/v3/`

### Authentication
- Header: `X-API-KEY: your_api_key`
- No key for basic queries, but recommended for production.

### Key Endpoints for Members/Entities
- **Members List/Search**:
  - GET `/member?api_key={key}&congress={congress_number}&format=json` (e.g., congress=118 for current).
  - Returns: JSON array of members with bioguide_id, name, party, state, chamber (senate/house).
  - Example: `https://api.congress.gov/v3/member?api_key=DEMO_KEY&congress=118&chamber=senate&format=json`
  - Fields: member.bioguide_id, member.name, member.party, member.state, member.chamber, member.contactWebsite.

- **Single Member Details**:
  - GET `/member/{bioguide_id}?api_key={key}&format=json`
  - Returns: Full profile including biography, terms, committees, roles.
  - Example: `https://api.congress.gov/v3/member/P000197?api_key=DEMO_KEY&format=json` (for Sen. Schumer).
  - Key Fields:
    - biography: dateOfBirth, placeOfBirth, education, profession, family.
    - terms: congress, chamber, party, state, district, startDate, endDate, url.
    - committees: name, chamber, url, leadershipRole.
    - contact: office (address, phone, fax), website.

- **Committees**:
  - GET `/committee?api_key={key}&congress={congress}&chamber={senate|house}&format=json`
  - Returns: Committee list with id, name, type (standing, joint), office.
  - Single: `/committee/{committee_id}`
  - Mapping: To project CommitteeId (chamber, committeeName), members via roles.

- **Leadership/Entities**:
  - Use member roles in `/member/{id}/roles` for leadership (e.g., majority leader).
  - Entities like caucuses: Limited; use committees or search `/search?q={term}`.

### Formats
- JSON (default), XML.
- Pagination: `limit={num}&offset={start}` (max 250 per page).

### Limitations
- Historical data back to 1789, but full details from 1993.
- No bulk download; paginate for all members (~535 current).
- Updates: Real-time for current Congress.

### Python Fetch Example
```python
import requests

API_KEY = 'your_key'
BASE_URL = 'https://api.congress.gov/v3'

def fetch_members(congress=118, chamber='senate'):
    url = f"{BASE_URL}/member"
    params = {'api_key': API_KEY, 'congress': congress, 'chamber': chamber, 'format': 'json', 'limit': 20}
    response = requests.get(url, params=params)
    return response.json()['members']

# Usage
members = fetch_members()
for member in members:
    print(member['name'])
```

## 2. GovInfo.gov Bulk Data
GovInfo provides bulk downloads of official publications, including member directories and biographies in XML/JSON/PDF. No API for members; use bulk packages. Free, no auth.

### Base URL
- `https://www.govinfo.gov/bulkdata/`

### Key Packages for Members/Entities
- **Congressional Directory (Biographies)**:
  - Path: `LIV/{congress}/CONGRESSIONAL-DIRECTORY` (e.g., LIV/118 for 118th Congress).
  - Files: XML/JSON with member bios, committees, staff.
  - Example: Download `CD-{date}.xml` from https://www.govinfo.gov/bulkdata/LIV/118/CONGRESSIONAL-DIRECTORY.
  - Fields: member_id, full_name, title, state, district, party, address, phone, email, committees (name, role), biography.
  - Update Frequency: Quarterly or as needed.

- **Committee Information**:
  - Path: `LIV/{congress}/COMMITTEE-INFORMATION`.
  - Files: XML with committee rosters, hearings, jurisdiction.
  - Example: `CI-{date}.xml`.
  - Mapping: Committee name, members, chair/ranking.

- **Member Rosters**:
  - Part of bulk legislative data: `LEGISLATIVE/{congress}/BILLS` includes sponsor info, but for full members, use Directory.
  - Historical: Archives back to 103rd Congress.

### Download Method
- Direct HTTP: `wget https://www.govinfo.gov/content/pkg/{package}/{file}.zip`
- Formats: XML (primary), JSON, PDF (bios).
- Size: ~10-50MB per package.

### Python Fetch Example (Bulk)
```python
import requests
import zipfile
import io

def download_bulk(congress=118, package_type='CONGRESSIONAL-DIRECTORY'):
    base_url = f'https://www.govinfo.gov/bulkdata/LIV/{congress}/{package_type}'
    # List files via API or known names
    files_url = f'{base_url}/?format=json'  # GovInfo has metadata API
    # Download latest ZIP
    zip_url = f'{base_url}/CD-118thCongress-1stSession.xml.zip'  # Example
    resp = requests.get(zip_url)
    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        z.extractall('/tmp/govinfo_members')
    # Parse XML with lxml/etree

# Usage
download_bulk()
```

### Limitations
- Bulk only; no real-time API.
- XML-heavy; requires parsing (use lxml or xml.etree).
- Coverage: Current + historical, but formats vary pre-2000s.

## Mapping to Project Models
- **Member**: Use bioguide_id as guid; map name, party, state, chamber to Member; terms to MemberTerm; bio to notes.
- **Committee**: Map name/chamber to Committee; members/roles to CommitteeMember.
- **Ingestion**: Scripts in tools/ will fetch/parse, transform to project's Spotcheck/Entity DAO format, insert via JDBC to remote DB.
- **Entities Page**: Assume /members endpoint; populate from ingested data.

## Next Steps
- Obtain congress.gov API key.
- Scripts: Fetch API for real-time, bulk for historical.
- Tests: Mock responses, validate mappings.
- Remote: Connect to 100.90.23.59 (Tailscale) for DB inserts (update app.properties with host).

References:
- Congress.gov API: https://projects.propublica.org/api-docs/congress-api/members/
- GovInfo Bulk: https://www.govinfo.gov/bulkdata
- ProPublica Congress API (alternative): https://www.propublica.org/datastore/api/propublica-congress-api (no key, but limited).

Update this doc as sources evolve.