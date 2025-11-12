# Federal Data Ingestion System - Complete Implementation

## Overview

This document describes the comprehensive federal legislative data ingestion system implemented for OpenLegislation. The system ingests data from congress.gov and govinfo.gov APIs, processes it through specialized Java processors, and stores it in a PostgreSQL database with full audit trails and social media integration.

## Architecture

### System Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│   Processors     │───▶│   Database      │
│                 │    │                  │    │                 │
│ • Congress.gov  │    │ • GovInfo API    │    │ • PostgreSQL    │
│ • GovInfo.gov   │    │ • Federal Member │    │ • Federal Tables│
│ • Social Media  │    │ • Social Media   │    │ • Audit Logs    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   API Endpoints  │
                       │                  │
                       │ • /api/3/federal │
                       │ • REST/JSON      │
                       └──────────────────┘
```

## Data Models

### Core Federal Models

#### FederalMember
- **Purpose**: Represents federal legislators (Senators/Representatives)
- **Key Fields**:
  - `bioguideId`: Unique identifier from congress.gov
  - `fullName`, `firstName`, `lastName`: Member name
  - `chamber`: HOUSE, SENATE, or JOINT
  - `state`, `district`: Geographic representation
  - `party`: Political party affiliation
  - `currentMember`: Whether currently serving
- **Relationships**:
  - One-to-many with `FederalMemberTerm`
  - One-to-many with `FederalMemberCommittee`
  - One-to-many with `FederalMemberSocialMedia`

#### FederalMemberTerm
- **Purpose**: Tracks terms served by federal legislators
- **Key Fields**:
  - `congress`: Congress number (e.g., 119)
  - `startYear`, `endYear`: Term duration
  - `party`, `state`, `district`: Term-specific info
  - `chamber`: Chamber served in

#### FederalMemberCommittee
- **Purpose**: Committee assignments for federal legislators
- **Key Fields**:
  - `committeeName`: Full committee name
  - `committeeCode`: Short committee code
  - `role`: Chair, Ranking Member, Member, etc.
  - `startDate`, `endDate`: Assignment duration
  - `subcommittee`: If applicable

#### FederalMemberSocialMedia
- **Purpose**: Social media accounts for federal legislators
- **Key Fields**:
  - `platform`: twitter, facebook, youtube, instagram
  - `handle`: Username or page identifier
  - `url`: Full profile URL
  - `followerCount`, `followingCount`: Engagement metrics
  - `isVerified`, `isOfficial`: Account validation

### Supporting Models

#### FederalCommittee
- **Purpose**: Federal committees and subcommittees
- **Key Fields**:
  - `committeeCode`: Unique committee identifier
  - `committeeName`: Full committee name
  - `chamber`: HOUSE, SENATE, or JOINT
  - `committeeType`: standing, select, joint, etc.
  - `jurisdiction`: Committee responsibilities

#### FederalBill (Extended)
- **Purpose**: Federal legislation with enhanced metadata
- **Extensions**:
  - `federalCongress`: Congress number
  - `federalSource`: Data source (govinfo/congress.gov)
  - Enhanced sponsor and cosponsor tracking
  - Federal-specific action types

## Database Schema

### Tables Created

```sql
-- Core member tables
master.federal_members
master.federal_member_terms
master.federal_member_committees
master.federal_member_social_media

-- Committee tables
master.federal_committees
master.federal_committee_members

-- Legislative tables
master.federal_bills (extended)
master.federal_laws
master.federal_law_sections
master.federal_reports
master.federal_congressional_records
master.federal_hearings
master.federal_register

-- Social media and analytics
master.federal_social_media_posts
```

### Key Features

1. **Comprehensive Indexing**: Optimized for common query patterns
2. **Audit Logging**: All changes tracked with timestamps
3. **Referential Integrity**: Foreign key constraints maintain data consistency
4. **JSONB Support**: Flexible metadata storage for API responses
5. **Partitioning Ready**: Designed for large-scale data growth

## Ingestion Processors

### GovInfoApiProcessor
- **Purpose**: Main processor for congress.gov API data
- **Features**:
  - Rate limiting and retry logic
  - JSON parsing with error handling
  - Batch processing with configurable sizes
  - Progress tracking and logging

### FederalMemberProcessor
- **Purpose**: Specialized processor for member data
- **Features**:
  - Member biographical information
  - Term and committee assignment tracking
  - Social media account discovery
  - Deduplication and validation

### FederalIngestionService
- **Purpose**: Unified orchestration service
- **Features**:
  - Parallel processing capabilities
  - Progress tracking and monitoring
  - Error recovery and retry logic
  - Comprehensive logging

## API Endpoints

### Federal Data Access

```http
# Member Information
GET  /api/3/federal/members                    # All members
GET  /api/3/federal/members/{bioguideId}       # Specific member
GET  /api/3/federal/members/search?name=smith # Search by name
GET  /api/3/federal/members/state/{state}      # Members by state
GET  /api/3/federal/members/stats              # Member statistics

# Data Ingestion
POST /api/3/federal/ingest?congress=119       # Trigger ingestion
GET  /api/3/federal/ingest/status/{congress}   # Check status
POST /api/3/federal/validate/{congress}        # Validate data
```

### Response Examples

#### Federal Member Response
```json
{
  "id": 1,
  "bioguideId": "P000197",
  "fullName": "Charles E. Schumer",
  "firstName": "Charles",
  "lastName": "Schumer",
  "chamber": "SENATE",
  "state": "NY",
  "party": "D",
  "currentMember": true,
  "terms": [
    {
      "congress": 119,
      "startYear": 2025,
      "endYear": 2027,
      "party": "D",
      "state": "NY",
      "chamber": "SENATE"
    }
  ],
  "socialMedia": [
    {
      "platform": "twitter",
      "handle": "SenSchumer",
      "url": "https://twitter.com/SenSchumer",
      "followerCount": 1250000,
      "isVerified": true,
      "isOfficial": true
    }
  ],
  "committees": [
    {
      "committeeName": "Senate Committee on Rules and Administration",
      "role": "Chair",
      "startDate": "2025-01-03"
    }
  ]
}
```

## Usage Instructions

### 1. Setup and Configuration

#### Database Setup
```bash
# Apply migrations
mvn flyway:migrate

# Verify tables created
psql -d openleg -c "\dt master.federal_*"
```

#### API Configuration
```properties
# src/main/resources/govinfo-api.properties
govinfo.api.key=your_api_key_here
govinfo.api.base-url=https://api.govinfo.gov/v1
govinfo.api.limit=50
govinfo.api.retry-max=3
govinfo.api.retry-delay-ms=1000
```

### 2. Running Ingestion

#### Command Line
```bash
# Build project
mvn clean compile

# Run member ingestion
java -cp target/classes:target/lib/* \
  gov.nysenate.openleg.processors.federal.FederalMemberProcessor \
  ingestCurrentMembers 119

# Run general data ingestion
java -cp target/classes:target/lib/* \
  gov.nysenate.openleg.processors.federal.GovInfoApiProcessor \
  --congress 119 --collection BILLS --limit 50
```

#### Using the Demo Script
```bash
# Run complete demo
chmod +x tools/federal_ingestion_demo.sh
./tools/federal_ingestion_demo.sh 119 BILLS 10
```

#### Using the Unified Service
```java
@Autowired
private FederalIngestionService federalIngestionService;

// Ingest all federal data
CompletableFuture<FederalIngestionResult> result =
    federalIngestionService.ingestFederalData(119);

// Ingest members only
CompletableFuture<FederalMemberIngestionResult> memberResult =
    federalIngestionService.ingestFederalMembers(119);
```

### 3. Verification

#### Database Verification
```sql
-- Check member count
SELECT COUNT(*) FROM master.federal_members WHERE current_member = true;

-- Check members by state
SELECT state, COUNT(*) FROM master.federal_members
WHERE current_member = true GROUP BY state ORDER BY COUNT(*) DESC;

-- Check social media accounts
SELECT platform, COUNT(*) FROM master.federal_member_social_media
GROUP BY platform;

-- Check recent ingestion
SELECT * FROM master.audit_log
WHERE table_name = 'federal_members'
ORDER BY changed_at DESC LIMIT 10;
```

#### API Verification
```bash
# Get all members
curl http://localhost:8080/api/3/federal/members

# Get specific member
curl http://localhost:8080/api/3/federal/members/P000197

# Search members
curl "http://localhost:8080/api/3/federal/members/search?name=schumer"

# Get member statistics
curl http://localhost:8080/api/3/federal/members/stats
```

### 4. Monitoring and Troubleshooting

#### Logs
```bash
# Federal ingestion logs
tail -f logs/ingestion-federal.log

# General application logs
tail -f logs/openleg.log | grep -i federal

# Database audit logs
psql -d openleg -c "SELECT * FROM master.audit_log WHERE table_name LIKE 'federal_%' ORDER BY changed_at DESC LIMIT 20;"
```

#### Health Checks
```sql
-- Check data freshness
SELECT table_name, MAX(created_at) as latest_insert
FROM master.audit_log
WHERE table_name LIKE 'federal_%'
GROUP BY table_name;

-- Check for errors
SELECT * FROM master.audit_log
WHERE table_name LIKE 'federal_%'
AND operation = 'ERROR'
ORDER BY changed_at DESC;
```

## Configuration Options

### Application Properties
```properties
# Federal ingestion settings
federal.ingestion.enabled=true
federal.ingestion.batch.size=50
federal.ingestion.parallel.enabled=false

# API settings
congress.api.key=your_congress_api_key
govinfo.api.key=your_govinfo_api_key

# Database settings
spring.datasource.url=jdbc:postgresql://localhost:5432/openleg
spring.jpa.hibernate.ddl-auto=validate
```

### Environment Variables
```bash
export CONGRESS_API_KEY="your_key"
export GOVINFO_API_KEY="your_key"
export DATABASE_URL="postgresql://user:pass@localhost:5432/openleg"
```

## Error Handling and Recovery

### Common Issues

1. **API Rate Limits**
   - Automatic retry with exponential backoff
   - Configurable retry limits and delays
   - Graceful degradation to cached data

2. **Data Quality Issues**
   - Validation at multiple stages
   - Deduplication logic for members
   - Schema validation for all collections

3. **Database Connection Issues**
   - Connection pooling with HikariCP
   - Automatic reconnection logic
   - Transaction rollback on failures

### Recovery Procedures

1. **Resume Failed Ingestion**
   ```bash
   # Check status
   curl http://localhost:8080/api/3/federal/ingest/status/119

   # Retry failed ingestion
   curl -X POST http://localhost:8080/api/3/federal/ingest?congress=119
   ```

2. **Data Validation and Repair**
   ```sql
   -- Validate member data
   SELECT COUNT(*) FROM master.federal_members WHERE bioguide_id IS NULL;

   -- Fix orphaned records
   DELETE FROM master.federal_member_social_media
   WHERE member_id NOT IN (SELECT id FROM master.federal_members);
   ```

## Performance Considerations

### Optimization Features

1. **Batch Processing**: Configurable batch sizes for database operations
2. **Parallel Processing**: Optional parallel ingestion for better performance
3. **Connection Pooling**: Efficient database connection management
4. **Indexing Strategy**: Optimized indexes for common query patterns
5. **Caching**: Intelligent caching of frequently accessed data

### Monitoring Metrics

- **Ingestion Speed**: Records processed per minute
- **Error Rates**: Percentage of failed operations
- **Data Freshness**: Time since last successful ingestion
- **API Usage**: Rate limit consumption tracking

## Security Considerations

### Data Protection

1. **API Keys**: Stored securely in configuration files
2. **Access Control**: Role-based access to ingestion endpoints
3. **Audit Logging**: Complete audit trail of all data changes
4. **Input Validation**: Comprehensive validation of all ingested data

### Compliance

1. **Terms of Service**: Compliance with congress.gov and govinfo.gov APIs
2. **Data Retention**: Configurable data retention policies
3. **Privacy**: Appropriate handling of personal information
4. **Transparency**: Clear data source attribution

## Future Enhancements

### Planned Features

1. **Real-time Updates**: WebSocket-based real-time ingestion monitoring
2. **Advanced Analytics**: Machine learning-based legislative analysis
3. **Multi-state Support**: Integration with state legislative systems
4. **Enhanced Social Media**: Advanced sentiment analysis and engagement tracking
5. **API Rate Optimization**: Intelligent rate limit management

### Extension Points

1. **Additional Collections**: Easy to add new data sources
2. **Custom Processors**: Pluggable processing architecture
3. **Analytics Integration**: Hooks for external analytics systems
4. **Export Capabilities**: Multiple export formats and destinations

## Support and Maintenance

### Regular Maintenance Tasks

1. **Daily**: Monitor ingestion logs and error rates
2. **Weekly**: Validate data integrity and run cleanup scripts
3. **Monthly**: Review and optimize database performance
4. **Quarterly**: Update API keys and review compliance

### Troubleshooting Guide

1. **Ingestion Failures**: Check API keys, rate limits, and network connectivity
2. **Data Quality Issues**: Review validation logs and source data
3. **Performance Problems**: Monitor database metrics and optimize queries
4. **API Issues**: Verify endpoint availability and response formats

## Conclusion

This federal data ingestion system provides a robust, scalable, and maintainable solution for integrating federal legislative data into OpenLegislation. The system supports comprehensive member information, social media integration, and multiple data sources with proper error handling, monitoring, and audit trails.

The modular architecture makes it easy to extend for additional data sources and analytics capabilities while maintaining data quality and system reliability.