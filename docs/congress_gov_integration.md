# Congress.gov Data Integration Guide

## Overview
This guide describes the complete workflow for bulk ingestion of congress.gov legislative data into the OpenLegislation system. The integration uses govinfo bulk XML data and maps it to existing OpenLegislation data models.

## Architecture

### Data Flow
```
Congress.gov Bulk Data → GovInfo XML → GovInfoBillProcessor → Bill Objects → Database
```

### Components
- **Data Source**: GovInfo bulk XML (https://www.govinfo.gov/bulkdata/)
- **Extraction**: Python crawler (`tools/fetch_govinfo_bulk.py`)
- **Processing**: Java XML parser (`GovInfoBillProcessor`)
- **Storage**: PostgreSQL with existing bill schema
- **Orchestration**: Shell script (`tools/bulk_ingest_congress_gov.sh`)

## Quick Start

### 1. Run Sample Ingestion
```bash
# Download and process sample congress.gov data
./tools/bulk_ingest_congress_gov.sh
```

### 2. Verify Results
```sql
-- Check ingested bills
SELECT congress, bill_number, title FROM bill WHERE congress = 119 LIMIT 10;

-- Check actions
SELECT ba.* FROM bill_action ba
JOIN bill b ON ba.bill_id = b.id
WHERE b.congress = 119 LIMIT 10;
```

## Detailed Workflow

### Step 1: Data Extraction
The Python crawler downloads XML files from govinfo bulk data:

```bash
python3 tools/fetch_govinfo_bulk.py \
    --collection BILLS \
    --congress 119 \
    --session 1 \
    --out /tmp/govinfo_data \
    --samples 5
```

**Output**: XML files in directory structure matching govinfo organization

### Step 2: XML Processing
GovInfoBillProcessor parses XML and creates Bill objects:

```java
// Key mapping logic
BillId billId = createBillIdFromGovInfo("H.R.1", 119); // → H1-119
Bill bill = getOrCreateBaseBill(billId, fragment);
setTitle(bill, title, fragment);
parseActionsFromGovInfo(bill, version, actionsElement, fragment);
```

**Features**:
- Maps federal bill numbers to state-style format
- Parses sponsors, actions, cosponsors, text versions
- Uses existing Bill model and helper methods
- Integrates with bill status analysis

### Step 3: Data Persistence
Processed bills are stored using existing DAO infrastructure:

- Bills → `bill` table
- Actions → `bill_action` table
- Text → `bill_amendment` table
- Sponsors → `bill_sponsor` table

## Data Mapping

### Bill Identity
| GovInfo | OpenLegislation | Example |
|---------|----------------|---------|
| `H.R.1` | `H1` | House Resolution 1 |
| `S.123` | `S123` | Senate Bill 123 |
| `congress: 119` | `session: 119` | 119th Congress |

### Key Fields
| GovInfo XML | Bill Field | Notes |
|-------------|------------|-------|
| `officialTitle` | `title` | Bill title |
| `introducedDate` | - | Not stored (could add) |
| `sponsor/name` | `sponsor` | Primary sponsor |
| `actions/action` | `actions` | Legislative history |
| `cosponsors` | `coSponsors` | Additional sponsors |
| `textVersions` | `billText` | Bill content |

### Chamber Mapping
| GovInfo | OpenLegislation |
|---------|----------------|
| House | ASSEMBLY |
| Senate | SENATE |

## Configuration

### Environment Variables
```bash
export CONGRESS=119          # Congress number
export SESSION=1             # Session number
export COLLECTION=BILLS      # Data collection
export OUTPUT_DIR=/tmp/data  # Working directory
```

### Application Properties
```properties
# Enable govinfo processing
processor.govinfo.enabled=true

# Database connection
spring.datasource.url=jdbc:postgresql://localhost:5432/openleg
```

## Monitoring & Troubleshooting

### Logs to Monitor
```
# Processor logs
tail -f logs/openleg.log | grep GovInfoBillProcessor

# Database changes
SELECT COUNT(*) FROM bill WHERE congress = 119;
SELECT COUNT(*) FROM bill_action WHERE bill_id IN (
    SELECT id FROM bill WHERE congress = 119
);
```

### Common Issues
1. **XML Parsing Errors**: Check XML schema compliance
2. **Bill ID Conflicts**: Handle duplicate federal/state bill numbers
3. **Sponsor Matching**: Federal members may not exist in state database
4. **Date Parsing**: Handle various date formats in XML

### Performance Tuning
- Batch XML processing in chunks
- Use connection pooling for database
- Implement retry logic for transient failures
- Monitor memory usage with large XML files

## Testing

### Unit Tests
```java
@Test
public void testGovInfoBillParsing() {
    String xml = "<bill><billNumber>H.R.1</billNumber>...</bill>";
    Bill bill = processor.parseGovInfoBillXml(xml, fragment);
    assertEquals("H1", bill.getBasePrintNo());
}
```

### Integration Tests
```bash
# Run with test data
mvn test -Dtest=GovInfoIntegrationTest

# Verify database state
./tools/verify_ingestion.sh
```

## Production Deployment

### Scheduling
```bash
# Cron job for daily updates
0 2 * * * /path/to/bulk_ingest_congress_gov.sh >> /var/log/congress_ingest.log 2>&1
```

### Scaling Considerations
- **Volume**: 200k+ bills across congresses
- **Frequency**: Daily updates during session
- **Storage**: ~50GB XML data per congress
- **Processing**: 10-100 bills/minute depending on complexity

### Backup & Recovery
- Backup XML source files
- Database snapshots before bulk operations
- Incremental processing with checkpointing
- Rollback procedures for failed ingests

## API Integration Alternative

For real-time updates, consider congress.gov API:

```java
// API client example
CongressApiClient client = new CongressApiClient(apiKey);
BillInfo bill = client.getBill(119, "hr", "1");
```

**Pros**: Real-time, structured JSON
**Cons**: Rate limits, API key required, less comprehensive data

## Future Enhancements

### Phase 2 Features
- [ ] Member data integration (federal legislators)
- [ ] Committee data synchronization
- [ ] Vote data ingestion
- [ ] Amendment tracking
- [ ] Cross-references between federal/state bills

### Advanced Processing
- [ ] Natural language processing for bill text
- [ ] Duplicate detection algorithms
- [ ] Change detection and diffing
- [ ] Automated categorization and tagging

## Support

### Documentation
- [GovInfo Bulk Data](https://www.govinfo.gov/bulkdata/)
- [Congress.gov API](https://api.congress.gov/)
- [OpenLegislation Wiki](https://github.com/nysenate/OpenLegislation/wiki)

### Issue Tracking
- GitHub Issues for bugs/features
- Internal ticketing for production issues
- Slack channel for real-time support

---

This integration enables OpenLegislation to include federal legislative data alongside state data, providing a comprehensive view of legislative activity across all levels of government.