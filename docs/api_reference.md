# External API Reference

## Congress.gov API

### Base URL
`https://api.congress.gov/v3/`

### Authentication
- Requires API key from congress.gov
- Rate limits: 1000 requests/hour, 5000/day
- Header: `X-API-Key: YOUR_API_KEY`

### Endpoints

#### Bills
```
GET /bill/{congress}/{billType}/{billNumber}
GET /bill/{congress}/{billType}/{billNumber}/actions
GET /bill/{congress}/{billType}/{billNumber}/cosponsors
GET /bill/{congress}/{billType}/{billNumber}/text
GET /bill/{congress}/{billType}/{billNumber}/subjects
```

**Response Format**:
```json
{
  "bill": {
    "number": "1",
    "type": "HR",
    "congress": 119,
    "introducedDate": "2025-01-03",
    "title": "Example Bill",
    "sponsor": {
      "firstName": "John",
      "lastName": "Doe",
      "party": "D",
      "state": "NY"
    }
  }
}
```

#### Members
```
GET /member/{bioguideId}
GET /member
GET /member/congress/{congress}
```

#### Committees
```
GET /committee/{congress}/{chamber}
GET /committee/{congress}/{chamber}/{committeeCode}
```

### Rate Limiting
- 1000 requests per hour
- 5000 requests per day
- HTTP 429 when exceeded
- Retry-After header provided

## GovInfo Bulk Data

### Base URL
`https://www.govinfo.gov/bulkdata/`

### Structure
```
bulkdata/
├── BILLS/{congress}/{session}/
│   ├── hr/          # House Resolutions
│   ├── s/           # Senate Bills
│   ├── hres/        # House Resolutions
│   └── ...
├── BILLSTATUS/{congress}/{session}/
├── BILLSTATUSSUM/{congress}/{session}/
└── resources/      # XSD schemas
```

### File Naming Convention
- `{billType}{billNumber}.{congress}.xml`
- Example: `hr1.119.xml`

### XML Schema
Available in `resources/` directories:
- `bill.xsd` - Bill structure schema
- `billstatus.xsd` - Status information schema

### Sample Bill XML Structure
```xml
<bill xmlns="http://www.govinfo.gov/metadata/1.0/bill.xsd">
  <legislativeIdentifier>H.R.1</legislativeIdentifier>
  <congress>119</congress>
  <session>1</session>
  <billNumber>H.R.1</billNumber>
  <billType>H.R.</billType>
  <officialTitle>As enacted</officialTitle>
  <introducedDate>2025-01-03</introducedDate>
  <sponsor>
    <name>Rep. Example</name>
    <party>D</party>
    <state>NY</state>
    <district>1</district>
  </sponsor>
  <cosponsors>
    <cosponsor>
      <name>Rep. Co-Sponsor</name>
      <party>R</party>
      <state>CA</state>
      <dateAdded>2025-01-05</dateAdded>
    </cosponsor>
  </cosponsors>
  <actions>
    <action>
      <date>2025-01-03</date>
      <chamber>House</chamber>
      <text>Introduced in House</text>
      <type>Intro-H</type>
    </action>
  </actions>
  <textVersions>
    <textVersion>
      <versionId>ih</versionId>
      <format>xml</format>
      <date>2025-01-03</date>
      <url>https://www.govinfo.gov/content/pkg/BILLS-119hr1ih/xml/BILLS-119hr1ih.xml</url>
    </textVersion>
  </textVersions>
</bill>
```

## Data Fetching Strategy

### Bulk Data Approach (Recommended)
1. **Discovery**: Crawl directory listings to find new/updated files
2. **Download**: Fetch XML files with rate limiting
3. **Processing**: Parse XML and extract structured data
4. **Storage**: Insert into staging tables
5. **Deduplication**: Merge with existing data

### API Approach (Alternative)
1. **Search**: Use congress.gov API to find bills
2. **Detail Fetch**: Retrieve full bill information
3. **Text Fetch**: Download bill text separately
4. **Processing**: Parse JSON responses
5. **Storage**: Direct insertion with conflict resolution

### Hybrid Approach
- Use bulk data for initial load and large updates
- Use API for real-time updates and missing data
- Implement fallback mechanisms

## Error Handling

### HTTP Status Codes
- **200**: Success
- **404**: Resource not found
- **429**: Rate limit exceeded
- **500**: Server error

### Retry Strategy
- Exponential backoff for 429/500 errors
- Maximum retry attempts: 3
- Circuit breaker for persistent failures
- Alert on repeated failures

### Data Validation
- Validate XML against XSD schemas
- Check for required fields
- Verify date formats and ranges
- Cross-reference member/committee data

## Monitoring and Alerting

### Metrics to Track
- Request success/failure rates
- Response times
- Data freshness (last update times)
- Error rates by endpoint
- Rate limit usage

### Alerts
- Rate limit approaching threshold
- High error rates
- Data ingestion delays
- Schema validation failures

## Development Resources

### Documentation
- [Congress.gov API Documentation](https://api.congress.gov/)
- [GovInfo Bulk Data](https://www.govinfo.gov/bulkdata)
- [XML Schema Reference](https://www.govinfo.gov/metadata)

### Tools
- Postman collections for API testing
- XML validators for schema compliance
- Python scripts for bulk data crawling
- Test harnesses for data processing pipelines

### Testing
- Use sample data from govinfo bulk downloads
- Mock external APIs for unit testing
- Integration tests with rate limiting simulation
- End-to-end tests with realistic data volumes
