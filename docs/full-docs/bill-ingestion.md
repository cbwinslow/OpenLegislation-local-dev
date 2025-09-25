# Bill Data Ingestion Procedures

## Overview

This document outlines the ingestion of federal bill data from GovInfo bulk XML into OpenLegislation. It uses Python ETL scripts leveraging the generic ingestion framework for resumeable processing, parsing XML with lxml, and upserting to PostgreSQL tables. Builds on GovInfo integration notes for mapping to Java models.

### Key Goals
- Handle bulk XML packages (BILLS, BILLSTATUS, BILLSUMMARY).
- Map congress/billNumber to BaseBillId, actions to BillAction.
- Stage data to avoid master conflicts; support resume on interruptions.
- Track progress/errors via JSON logs.

## Data Sources

### Primary Source
- **GovInfo Bulk Data**: XML packages from https://www.govinfo.gov/bulkdata (e.g., BILLS-119th Congress XML). Schema files per package.
  - Collections: BILLS (full text), BILLSTATUS (actions/status), BILLSUM (summaries).
  - Format: ZIP with XML files, e.g., BILLS-119hr1ih.xml.

### Fetching Samples
```bash
# Example download script (from tools/download_govinfo_samples.sh implied)
wget https://www.govinfo.gov/bulkdata/BILLS/119/BILLS-119hr1ih.zip -O data/govinfo/samples/119hr1ih.zip
unzip data/govinfo/samples/*.zip -d staging/govinfo/
```

## Database Schema References

Uses core tables with potential GovInfo extensions:
- **master.bill**: bill_print_no (e.g., H1-119), congress, title, bill_type (H/S), data_source='govinfo'.
- **master.bill_sponsor**: bill_id, sponsor_name, party, state.
- **master.bill_amendment_action**: bill_print_no, congress (as session_year), action_date, chamber, description, action_type.

Staging table example (from migrations):
```sql
-- Example staging for GovInfo bills (extend as needed via Flyway)
CREATE TABLE staging.govinfo_bill (
    xml_file_path TEXT,
    bill_number TEXT,
    congress INTEGER,
    title TEXT,
    sponsor JSONB,
    actions JSONB,
    ingested_at TIMESTAMP DEFAULT now()
);
```

## Ingestion Flow Diagram

```mermaid
flowchart TD
    A[Sources<br/>GovInfo Bulk XML<br/>ZIP packages] --> B[Discovery<br/>glob XML files<br/>Extract ID from filename (BILLS-119hr1ih.xml -> H1-119)]
    B --> C[Generic Framework<br/>BaseIngestionProcess<br/>discover_records, process_record]
    C --> D[Parse XML (lxml.etree)<br/>XPath: billNumber, congress, officialTitle<br/>Sponsor: fullName/party/state<br/>Actions: actionDate/text/chamber]
    D --> E[Transform<br/>Normalize ID (H.R. 1 -> H1)<br/>Map to schema fields]
    E --> F[Load to DB (psycopg2 upsert)<br/>INSERT ON CONFLICT bill_print_no/congress<br/>Sponsors/actions separate inserts]
    F --> G[Validation<br/>Check parsed data completeness<br/>Error logging]
    B -.->|Resume/Progress| H[Tracker JSON<br/>ingestion_log.json<br/>Record IDs processed]
    F -.->|Staging| I[Optional staging table<br/>Before master merge]
```

## Procedures

### Procedure 1: Setup & Discovery (GovInfoBillIngestor)

Extends BaseIngestionProcess for XML handling.

#### Initialization
Script: tools/govinfo_bill_ingestion.py
```python
class GovInfoBillIngestor(BaseIngestionProcess):
    def __init__(self, xml_dir=None, **kwargs):
        super().__init__(**kwargs)
        self.xml_dir = xml_dir or '/tmp/govinfo'  # From settings
        self.conn = psycopg2.connect(**self.db_config)
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)

    def discover_records(self) -> List[Dict]:
        xml_files = []
        for xml_file in glob.glob(os.path.join(self.xml_dir, '**', '*.xml'), recursive=True):
            bill_id = self._extract_bill_id_from_path(xml_file)
            if bill_id:
                xml_files.append({
                    'record_id': bill_id,
                    'file_path': xml_file,
                    'metadata': {'xml_file': xml_file}
                })
        return xml_files

    def _extract_bill_id_from_path(self, file_path: str) -> str:
        filename = os.path.basename(file_path)
        if filename.startswith('BILLS-') and filename.endswith('.xml'):
            parts = filename.replace('BILLS-', '').replace('.xml', '').split('h')
            if len(parts) >= 2:
                congress = parts[0]
                bill_num = parts[1].rstrip('ih')
                return f"H{bill_num}-{congress}"  # Adjust for S
        return None
```

Usage:
```bash
python3 tools/govinfo_bill_ingestion.py --xml-dir staging/govinfo --db-config db_config.json
```

### Procedure 2: Parsing XML

#### parse_govinfo_xml
```python
def _parse_govinfo_xml(self, xml_file: str) -> Dict:
    tree = etree.parse(xml_file)
    root = tree.getroot()
    bill_num = root.findtext('.//billNumber') or 'UNKNOWN'
    congress = int(root.findtext('.//congress') or '119')
    # Normalize
    if 'H.R.' in bill_num:
        bill_num = f"H{bill_num.replace('H.R.', '').strip()}"
    elif 'S.' in bill_num:
        bill_num = f"S{bill_num.replace('S.', '').strip()}"
    title = root.findtext('.//officialTitle') or ''
    # Sponsor
    sponsor_elem = root.find('.//sponsor')
    sponsor = {'name': sponsor_elem.findtext('fullName'), 'party': sponsor_elem.findtext('party'), 'state': sponsor_elem.findtext('state')} if sponsor_elem else None
    # Actions
    actions = []
    for action in root.findall('.//actions/action'):
        actions.append({
            'action_date': action.findtext('actionDate'),
            'chamber': action.findtext('chamber') or '',
            'description': action.findtext('text') or '',
            'action_type': action.findtext('actionCode') or ''
        })
    return {
        'bill_number': bill_num,
        'congress': congress,
        'title': title,
        'bill_type': bill_num[0],
        'sponsor': sponsor,
        'actions': actions,
        'data_source': 'govinfo'
    }
```

### Procedure 3: Transform & Load

#### In process_record & _insert_bill_data
```python
def process_record(self, record: Dict) -> bool:
    bill_data = self._parse_govinfo_xml(record['metadata']['xml_file'])
    if bill_data:
        return self._insert_bill_data(bill_data)
    return False

def _insert_bill_data(self, bill_data: Dict) -> bool:
    self.cursor.execute("""
        INSERT INTO master.bill (bill_print_no, congress, title, bill_type, data_source, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, now(), now())
        ON CONFLICT (bill_print_no, congress) DO UPDATE SET title = EXCLUDED.title, bill_type = EXCLUDED.bill_type, updated_at = now()
        RETURNING bill_id
    """, (bill_data['bill_number'], bill_data['congress'], bill_data['title'], bill_data['bill_type'], bill_data['data_source']))
    bill_result = self.cursor.fetchone()
    if not bill_result:
        return False
    bill_id = bill_result['bill_id']
    # Insert sponsor if present
    if bill_data.get('sponsor'):
        self.cursor.execute("""
            INSERT INTO master.bill_sponsor (bill_id, sponsor_name, party, state, created_at)
            VALUES (%s, %s, %s, %s, now()) ON CONFLICT (bill_id) DO NOTHING
        """, (bill_id, bill_data['sponsor']['name'], bill_data['sponsor'].get('party'), bill_data['sponsor'].get('state')))
    # Insert actions
    for action in bill_data.get('actions', []):
        self.cursor.execute("""
            INSERT INTO master.bill_amendment_action (bill_print_no, bill_session_year, action_date, chamber, description, action_type, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, now()) ON CONFLICT (...) DO NOTHING
        """, (bill_data['bill_number'], bill_data['congress'], action['action_date'], action['chamber'], action['description'], action['action_type']))
    self.conn.commit()
    return True
```

### Procedure 4: Mapping Details (from GovInfo Notes)
- **Identifier**: govinfo billNumber/congress/session -> BaseBillId (printNo= H1, sessionYear=119).
- **Sponsor/Cosponsors**: XPath //sponsor/fullName -> BillSponsor.name; party/state similarly.
- **Actions**: //actions/action -> XmlBillActionAnalyzer structure.
- **Texts**: Multiple versions; store in bill_text or version table (like text_diff).

## Automation & Monitoring

- **Framework**: BaseIngestionProcess handles resume via get_record_id_column="bill_print_no", logs to ingestion_log.json.
- **Scripts**: manage_ingestion_state.py for pausing/resuming; ingestion_progress.py for status.
- **Cron**: Run nightly for updates: `0 3 * * * python3 tools/manage_all_ingestion.py --govinfo`.

## Quality Assurance
- **Parsing Validation**: Check for required elements (billNumber, title); log errors.
- **Data Integrity**: Upsert prevents duplicates; spotcheck against samples.
- **Performance**: Process in batches; monitor XML size/congress volume.

This integrates with Java processors for further normalization (e.g., FsXmlDao, GovInfoXmlFile) if merging staged data.
