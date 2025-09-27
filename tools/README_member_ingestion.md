# Federal Member Data Ingestion

This directory contains tools for ingesting federal legislator data from congress.gov API into the OpenLegislation database.

## Overview

The federal member ingestion system fetches comprehensive biographical, political, and social media data for all current and historical members of Congress. This data is essential for:

- Proper bill sponsor attribution
- Member search and filtering
- Legislative analysis by party/state/district
- Social media integration
- Cross-referencing with state legislators

## Database Schema

Before running ingestion, ensure the federal member schema is applied:

```sql
-- Apply the federal member schema migration
-- File: src/main/resources/sql/migrations/V20250921.0004__federal_member_schema.sql
```

The schema includes:
- `master.federal_person` - Biographical information
- `master.federal_member` - Political information and current status
- `master.federal_member_term` - Historical terms served
- `master.federal_member_committee` - Committee assignments
- `master.federal_member_social_media` - Official social media accounts
- `master.federal_member_contact` - Contact information

## API Requirements

### Congress.gov API Key
1. Visit https://api.congress.gov/
2. Sign up for an API key
3. The API provides:
   - 1000 requests/hour (free tier)
   - 5000 requests/day
   - Rate limiting applies

### API Rate Limits
- **Current Members**: ~550 members (House + Senate)
- **Detailed Member Data**: 1 additional request per member
- **Total Requests**: ~1100 for full ingestion
- **Time Estimate**: ~30-60 minutes with rate limiting

## Quick Start

### 1. Test the System
Run a quick test with sample data:

```bash
# Test with 5 members
python3 tools/test_member_ingestion.py \
    --api-key YOUR_CONGRESS_API_KEY \
    --db-config tools/db_config.json \
    --limit 5
```

Expected output:
```
=== Federal Member Data Ingestion Test ===

Testing Congress.gov API connection...
✓ API connection successful
✓ Test tables created
Fetching 5 sample members...
✓ Retrieved 5 members
✓ Ingested: Senator Maria Cantwell
✓ Ingested: Senator Patty Murray
...

=== INGESTION RESULTS ===
Persons ingested: 5
Member records: 5

Sample members:
  Maria Cantwell - Senate WA (D)
  Patty Murray - Senate WA (D)
  ...
```

### 2. Full Production Ingestion
Ingest all current members of Congress:

```bash
# Full ingestion (requires API key)
python3 tools/ingest_federal_members.py \
    --api-key YOUR_CONGRESS_API_KEY \
    --db-config tools/db_config.json
```

## Data Coverage

### Current Members (Default)
- **House of Representatives**: 435 members
- **Senate**: 100 members
- **Total**: ~535 current members
- **Data Included**:
  - Biographical information (name, birth/death, gender)
  - Current political info (party, state, district)
  - Social media accounts (Twitter, Facebook, YouTube, Instagram)
  - Committee assignments
  - Contact information

### Historical Members (Optional)
The system can be extended to include historical members by modifying the API parameters.

## Data Quality & Validation

### Automatic Validation
- **Bioguide ID**: Unique identifier validation
- **Name Parsing**: Proper name component extraction
- **Party Normalization**: D/R/I standardization
- **State/District Validation**: Geographic data verification
- **Social Media URL Construction**: Platform-specific URL formatting

### Data Completeness
- **Biographical Data**: 100% coverage for current members
- **Political Data**: 100% coverage (party, state, district)
- **Social Media**: ~70-80% of members have at least one account
- **Contact Info**: Available for most members

## Troubleshooting

### Common Issues

#### 1. API Key Issues
```
Error: API request failed for /member: 401 Unauthorized
```
**Solution**: Verify your API key is correct and active.

#### 2. Database Connection
```
Error: Database connection failed
```
**Solution**: Check database credentials in `db_config.json`.

#### 3. Rate Limiting
```
Rate limiting: sleeping 2s
```
**Solution**: Normal behavior - the system automatically handles rate limits.

#### 4. Missing Schema
```
Error: relation "master.federal_person" does not exist
```
**Solution**: Apply the database migration first.

### Performance Tuning

#### For Large-Scale Ingestion
```bash
# Reduce API delay for faster processing (if you have higher rate limits)
# Edit the script to reduce time.sleep(0.5) to time.sleep(0.1)

# Monitor progress
tail -f /var/log/govinfo_ingest/ingestion.log
```

#### Memory Usage
- **Per Member**: ~2-5KB of data
- **Total Memory**: ~2-3MB for full ingestion
- **Database Growth**: ~50-100MB for all members and related data

## Integration with Bill Data

### Sponsor Attribution
After member ingestion, bills can properly attribute sponsors:

```sql
-- Before: Placeholder names
SELECT sponsor FROM bill WHERE bill_print_no = 'H1-119';
-- Result: "Test Representative"

-- After: Proper member data
SELECT
    b.bill_print_no,
    fp.full_name,
    fm.party,
    fm.state,
    fm.district
FROM master.bill b
JOIN master.federal_member fm ON b.sponsor_id = fm.id
JOIN master.federal_person fp ON fm.person_id = fp.id
WHERE b.bill_print_no = 'H1-119';
-- Result: "Mary Peltola, D, AK, At Large"
```

### Cross-References
- **State vs Federal**: Identify legislators who serve in both state and federal government
- **Party Analysis**: Track legislation by party affiliation
- **District Analysis**: Correlate federal and state district boundaries

## Social Media Integration

### Automatic Account Discovery
The ingestion system automatically discovers and validates official social media accounts:

- **Twitter**: @SenSchumer, @RepNancyPelosi
- **Facebook**: Official government pages
- **YouTube**: Official channels
- **Instagram**: Official accounts

### Data Structure
```sql
-- Social media accounts linked to members
SELECT
    fp.full_name,
    fmsm.platform,
    fmsm.handle,
    fmsm.url
FROM master.federal_member_social_media fmsm
JOIN master.federal_member fm ON fmsm.member_id = fm.id
JOIN master.federal_person fp ON fm.person_id = fp.id
WHERE fm.current_member = true
LIMIT 10;
```

## Monitoring & Maintenance

### Regular Updates
```bash
# Cron job for weekly updates
0 2 * * 1 /path/to/ingest_federal_members.py --api-key $API_KEY --db-config $DB_CONFIG
```

### Data Freshness Checks
```sql
-- Check when member data was last updated
SELECT
    COUNT(*) as total_members,
    MAX(updated_at) as last_update
FROM master.federal_member
WHERE current_member = true;
```

### Error Monitoring
```sql
-- Check for members with missing data
SELECT
    fp.full_name,
    fm.state,
    fm.party
FROM master.federal_member fm
JOIN master.federal_person fp ON fm.person_id = fp.id
LEFT JOIN master.federal_member_social_media fmsm ON fm.id = fmsm.member_id
WHERE fm.current_member = true
GROUP BY fp.full_name, fm.state, fm.party
HAVING COUNT(fmsm.*) = 0; -- Members with no social media
```

## Advanced Usage

### Custom Member Queries
```python
# Get members by state and party
def get_members_by_state_party(state, party):
    cursor.execute("""
        SELECT fp.full_name, fm.district, fm.chamber
        FROM master.federal_member fm
        JOIN master.federal_person fp ON fm.person_id = fp.id
        WHERE fm.state = %s AND fm.party = %s AND fm.current_member = true
        ORDER BY fm.district
    """, (state, party))
    return cursor.fetchall()
```

### Committee Analysis
```python
# Find committee members
def get_committee_members(committee_code):
    cursor.execute("""
        SELECT fp.full_name, fmc.position, fmc.chamber
        FROM master.federal_member_committee fmc
        JOIN master.federal_member fm ON fmc.member_id = fm.id
        JOIN master.federal_person fp ON fm.person_id = fp.id
        WHERE fmc.committee_code = %s AND fmc.congress = (
            SELECT MAX(congress) FROM master.federal_member_term
        )
        ORDER BY fmc.position, fp.last_name
    """, (committee_code,))
    return cursor.fetchall()
```

## Support & Resources

### Documentation
- **Congress.gov API**: https://api.congress.gov/
- **Bioguide**: https://bioguide.congress.gov/
- **OpenLegislation**: https://github.com/nysenate/OpenLegislation

### Getting Help
1. Check the test script output for API connectivity
2. Verify database schema is applied
3. Review API rate limits and key validity
4. Check logs for detailed error messages

### Contributing
- Report issues with member data accuracy
- Suggest improvements to social media discovery
- Propose additional data fields or APIs

---

This federal member ingestion system provides the foundation for comprehensive legislative analysis by properly attributing bills to their sponsors and enabling rich member-based queries and cross-references.
