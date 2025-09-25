# Federal Members Ingestion: Scripts and Usage Guide

This guide covers the Python scripts in `tools/` for fetching and mapping U.S. Congress members data from congress.gov API and GovInfo.gov bulk downloads. Data is mapped to a JSON entity model compatible with OpenLegislation's Member/Committee structures. Includes tests and remote DB integration via Tailscale IP 100.90.23.59.

## Prerequisites
- Python 3.8+.
- Install dependencies: `pip install requests pytest pytest-mock psycopg2-binary` (for DB).
- Congress.gov API key: Register at https://api.congress.gov/; set `CONGRESS_API_KEY` env or pass `--api_key`.
- Tailscale: Ensure connected to network; server at 100.90.23.59 allows PG connections on 5432.
- DB: PostgreSQL on remote server (opendiscourse DB, opendiscourse user/pass – update in db_config.py).
- Output: Scripts save JSON to `tools/output/` (create if needed: `mkdir tools/output`).

**Security**: Use env vars for API/DB secrets. Test locally first.

## Scripts Overview
- `fetch_congress_members.py`: Real-time API fetch (paginated), optional details, map to JSON.
- `fetch_govinfo_members.py`: Bulk ZIP download, XML parse, map to JSON.
- `test_fetch_members.py`: Pytest for mapping/fetch logic (mocked; no network).
- `db_config.py`: PostgreSQL connection to remote server (URI/params).

## Running Scripts

### 1. Fetch from Congress.gov API
```bash
cd tools
python3 fetch_congress_members.py --congress 118 --chamber senate --api_key YOUR_KEY --details --output output/members_senate.json
```
- `--congress`: Session (default 118).
- `--chamber`: senate/house/joint (optional).
- `--details`: Fetch full bio/terms (slower, ~535 calls).
- Output: JSON array of entities (e.g., {'guid': 'P000197', 'fullName': '...', 'terms': [...]}).
- Example: Fetches ~100 senators; maps bioguide_id to guid, includes committees.

### 2. Fetch from GovInfo Bulk
```bash
cd tools
python3 fetch_govinfo_members.py --congress 118 --output output/members_govinfo.json
```
- Downloads/parses XML ZIP (e.g., CD-118thCongress-1stSession.xml.zip).
- Output: JSON with ~535 members; guid from XML id or fallback, includes office/committees.
- Note: Bulk is historical/static; use for initial load.

### 3. Run Tests
```bash
cd tools
pytest test_fetch_members.py -v
```
- Unit: map_to_entity (assert fields from samples).
- Mocked Integration: fetch_all_members, parse_members_xml (no real calls).
- Coverage: Basic/edge cases (None values, empty lists).
- Run specific: `pytest -k test_map_congress_entity`.

### 4. DB Integration (Remote Insert)
Update scripts to insert JSON to DB (example below; add to main() after mapping).

**Example Insert Function** (add to both fetch scripts):
```python
import psycopg2
from db_config import get_connection_params

def insert_members_to_db(entities, table='federal_members'):
    """Insert mapped entities to remote PostgreSQL (upsert on guid)."""
    params = get_connection_params()
    conn = psycopg2.connect(**params)
    cur = conn.cursor()
    
    # Assume table schema: guid (PK), fullName, chamber, party, state, json_data
    for entity in entities:
        guid = entity['guid']
        json_data = json.dumps({k: v for k, v in entity.items() if k not in ['guid']})
        cur.execute("""
            INSERT INTO %s (guid, fullName, chamber, party, state, json_data)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (guid) DO UPDATE SET json_data = EXCLUDED.json_data
        """, (table, guid, entity.get('fullName'), entity.get('chamber'), entity.get('party'), entity.get('state'), json_data))
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"Inserted/updated {len(entities)} members to remote DB.")

# In main(): after entities = [...]; insert_members_to_db(entities)
```

- Create table on server: `CREATE TABLE federal_members (guid VARCHAR PRIMARY KEY, fullName VARCHAR, chamber VARCHAR, party VARCHAR, state VARCHAR, json_data JSONB);`
- Run: After fetch, calls insert (uses Tailscale IP).
- Error Handling: Add try/except for conn.

## End-to-End Flow
1. Connect Tailscale: `tailscale up` (ensure 100.90.23.59 reachable: `ping 100.90.23.59`).
2. Test DB: `python3 -c "import psycopg2; from db_config import get_connection_params; conn=psycopg2.connect(**get_connection_params()); print('Connected!'); conn.close()"`
3. Fetch & Map: Run congress/govinfo scripts (add insert as above).
4. Verify: On server, `psql -h 100.90.23.59 -U opendiscourse -d opendiscourse -c "SELECT COUNT(*) FROM federal_members;"`
5. Merge Sources: Load both JSONs, dedupe by guid (e.g., prefer congress.gov details).
6. Entities Page: In app, query DB for /members; display from json_data.

## Troubleshooting
- API Rate Limit: Use key; sleep(1) if throttled.
- Bulk Download Fail: Check URL (GovInfo changes filenames); manual download to /tmp/.
- DB Connection: Firewall (ufw allow 5432 from Tailscale IPs), pg_hba.conf allows user.
- Tests Fail: Install pytest-mock; check mocks.
- Extend: Add cron for updates; handle historical congresses.

Integrate with Java backend: Read JSON, use DAO to upsert (e.g., extend FsFederalBillXmlDao for members).

See [federal_members_sources.md](federal_members_sources.md) for data details.