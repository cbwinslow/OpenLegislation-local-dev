# Government Data Sources Research & Integration Plan

## Overview

This document outlines research into additional government data sources beyond congress.gov/govinfo and NYSenate OpenLegislation. The goal is to create a comprehensive data ingestion framework that includes member information, multi-state legislation, and social media analysis.

## Primary Data Sources (Current)

### 1. Congress.gov / GovInfo (Federal)
- **Data Types**: Bills, resolutions, committee reports, member info
- **Format**: Bulk XML, REST API
- **Coverage**: 93rd Congress (1973) to present
- **Volume**: ~300k bills, ~1.35TB XML data
- **Status**: ✅ Implemented (basic ingestion)

### 2. NYSenate OpenLegislation (State)
- **Data Types**: NY bills, resolutions, laws, transcripts
- **Format**: JSON API, XML processing
- **Coverage**: Current legislative sessions
- **Status**: ✅ Core system

## Additional Government Data Sources

### Federal Member & Biographical Data

#### 1. Congress.gov Member API
- **URL**: `https://api.congress.gov/v3/member`
- **Data**: Biographical info, terms served, committees, social media
- **Format**: JSON
- **Rate Limits**: 1000/hour, 5000/day
- **Coverage**: All current and historical members
- **Integration Priority**: 🔴 High

#### 2. Biographical Directory of Congress
- **URL**: `https://bioguide.congress.gov/`
- **Data**: Detailed biographies, photos, committee assignments
- **Format**: HTML scraping, some structured data
- **Coverage**: All members since 1774
- **Integration Priority**: 🟡 Medium

#### 3. House/Senate Committee Data
- **URL**: `https://www.congress.gov/committees`
- **Data**: Committee memberships, jurisdictions, reports
- **Format**: HTML, some JSON APIs
- **Integration Priority**: 🟡 Medium

### State Legislative Data Sources

#### 1. Open States API
- **URL**: `https://openstates.org/api/v1/`
- **Coverage**: 50 states + DC + territories
- **Data**: Bills, legislators, committees, votes
- **Format**: JSON API
- **Rate Limits**: 1000/day free, paid plans available
- **Integration Priority**: 🔴 High

#### 2. State Legislature Websites
- **California**: `https://leginfo.legislature.ca.gov/`
- **Texas**: `https://capitol.texas.gov/`
- **Florida**: `https://www.flsenate.gov/`
- **Illinois**: `https://www.ilga.gov/`
- **Data**: Bills, member info, committee data
- **Format**: HTML scraping, some APIs
- **Integration Priority**: 🟡 Medium

#### 3. NCSL (National Conference of State Legislatures)
- **URL**: `https://www.ncsl.org/`
- **Data**: State legislative tracking, policy data
- **Format**: HTML, reports
- **Integration Priority**: 🟢 Low

### Government Document Repositories

#### 1. Federal Register / Regulations.gov
- **URL**: `https://www.federalregister.gov/`, `https://www.regulations.gov/`
- **Data**: Federal regulations, notices, comments
- **Format**: Bulk XML, APIs
- **Volume**: Millions of documents
- **Integration Priority**: 🟡 Medium

#### 2. USA.gov Data
- **URL**: `https://www.data.gov/`
- **Data**: Federal datasets, APIs
- **Format**: JSON, CSV, XML
- **Coverage**: All federal agencies
- **Integration Priority**: 🟡 Medium

#### 3. FOIA.gov
- **URL**: `https://www.foia.gov/`
- **Data**: FOIA request data, agency information
- **Format**: HTML, some structured data
- **Integration Priority**: 🟢 Low

#### 4. GovWin IQ (Deltek)
- **URL**: `https://www.govwin.com/`
- **Data**: Government contracting, RFPs
- **Format**: Commercial API/database
- **Cost**: Subscription required
- **Integration Priority**: 🟢 Low

### International & Intergovernmental

#### 1. United Nations Documents
- **URL**: `https://documents.un.org/`
- **Data**: UN resolutions, reports
- **Format**: PDF, some structured data
- **Integration Priority**: 🟢 Low

#### 2. European Union Legislation
- **URL**: `https://eur-lex.europa.eu/`
- **Data**: EU laws, directives
- **Format**: HTML, XML
- **Integration Priority**: 🟢 Low

## Social Media Data Sources

### Legislator Social Media

#### 1. Congress.gov Social Media Links
- **Data**: Official social media accounts (Twitter, Facebook, etc.)
- **Format**: Available in member API responses
- **Coverage**: Current members
- **Integration Priority**: 🔴 High

#### 2. Twitter API (X)
- **URL**: `https://developer.twitter.com/en/docs/twitter-api`
- **Data**: Tweets, followers, engagement metrics
- **Rate Limits**: V2 API with academic access
- **Cost**: Free tier available
- **Integration Priority**: 🔴 High

#### 3. Facebook Graph API
- **URL**: `https://developers.facebook.com/docs/graph-api/`
- **Data**: Posts, engagement, page metrics
- **Rate Limits**: Based on app permissions
- **Integration Priority**: 🟡 Medium

#### 4. YouTube Data API
- **URL**: `https://developers.google.com/youtube/v3`
- **Data**: Videos, comments, channel analytics
- **Rate Limits**: 10,000 units/day free
- **Integration Priority**: 🟡 Medium

#### 5. Instagram Basic Display API
- **URL**: `https://developers.facebook.com/docs/instagram-basic-display-api/`
- **Data**: Posts, stories, profile info
- **Integration Priority**: 🟡 Medium

### Social Media Analysis Platforms

#### 1. CrowdTangle (Meta)
- **Data**: Facebook/Instagram content analysis
- **Cost**: Academic/research access available
- **Integration Priority**: 🟡 Medium

#### 2. Brandwatch/Hootsuite
- **Data**: Multi-platform social monitoring
- **Cost**: Commercial subscription
- **Integration Priority**: 🟢 Low

## Data Ingestion Architecture

### Unified Framework Components

#### 1. Data Source Adapters
```python
class DataSourceAdapter(ABC):
    @abstractmethod
    def fetch_data(self, params: Dict) -> Iterator[Dict]:
        pass

    @abstractmethod
    def transform_data(self, raw_data: Dict) -> Dict:
        pass

    @abstractmethod
    def get_schema(self) -> Dict:
        pass
```

#### 2. Member Data Integration
- **Federal Members**: Congress API → Unified member schema
- **State Members**: OpenStates API → Unified schema
- **Social Media**: Twitter/Facebook APIs → Member social profiles
- **Biographical**: Congress biographies → Extended member data

#### 3. Social Media Analysis Pipeline
1. **Collection**: Harvest posts from legislator accounts
2. **Processing**: NLP analysis, sentiment, topic modeling
3. **Storage**: Time-series social media data
4. **Analytics**: Engagement metrics, constituent interaction

### Database Schema Extensions

#### Member Social Media Table
```sql
CREATE TABLE member_social_media (
    member_id TEXT REFERENCES person(id),
    platform TEXT CHECK (platform IN ('twitter', 'facebook', 'youtube', 'instagram')),
    handle TEXT,
    url TEXT,
    follower_count INTEGER,
    last_updated TIMESTAMP,
    is_official BOOLEAN DEFAULT true
);
```

#### Social Media Posts Table
```sql
CREATE TABLE social_media_post (
    id BIGSERIAL PRIMARY KEY,
    member_id TEXT REFERENCES person(id),
    platform TEXT,
    post_id TEXT UNIQUE,
    content TEXT,
    posted_at TIMESTAMP,
    engagement_metrics JSONB,
    sentiment_score DECIMAL,
    topics TEXT[],
    created_at TIMESTAMP DEFAULT now()
);
```

## Implementation Roadmap

### Phase 1: Member Data Integration (Priority: High)
1. **Congress Member API Integration**
   - Fetch current/historical member data
   - Map to unified member schema
   - Include social media links

2. **OpenStates Member Data**
   - Multi-state legislator information
   - Committee assignments
   - Contact information

3. **Member Deduplication**
   - Cross-reference federal/state members
   - Handle name variations
   - Maintain data provenance

### Phase 2: Social Media Integration (Priority: High)
1. **Social Media Account Discovery**
   - Extract handles from congress.gov
   - Validate account authenticity
   - Monitor account changes

2. **Content Collection**
   - Twitter API integration
   - Facebook/Instagram Graph API
   - Rate limit management

3. **Content Analysis**
   - Sentiment analysis
   - Topic modeling
   - Engagement metrics
   - Constituency interaction analysis

### Phase 3: Extended State Data (Priority: Medium)
1. **OpenStates API Integration**
   - Multi-state bill data
   - Committee information
   - Voting records

2. **State Website Scraping**
   - Fallback for states without APIs
   - Structured data extraction
   - Change detection

### Phase 4: Government Documents (Priority: Medium)
1. **Federal Register Integration**
   - Regulation tracking
   - Public comment data
   - Agency actions

2. **FOIA Request Data**
   - Transparency metrics
   - Agency response times
   - Public interest analysis

## Technical Considerations

### API Rate Limiting
- Implement exponential backoff
- Cache frequently accessed data
- Use webhooks where available

### Data Quality & Validation
- Schema validation for all sources
- Duplicate detection and merging
- Data freshness monitoring

### Privacy & Compliance
- Respect platform terms of service
- Handle PII appropriately
- Maintain data usage transparency

### Scalability
- Distributed processing for large datasets
- GPU acceleration for NLP tasks
- Database optimization for social media data

## Success Metrics

### Data Coverage
- Federal members: 100% current + historical
- State legislators: Top 10-15 states
- Social media: 90%+ of active legislators
- Document repositories: Key federal sources

### Data Freshness
- Member data: Daily updates
- Social media: Real-time collection
- Legislation: Hourly during sessions

### System Performance
- Ingestion latency: < 1 hour for daily updates
- Query response: < 100ms for common requests
- API uptime: 99.9%

This research provides a foundation for expanding the OpenLegislation system into a comprehensive government data platform covering federal, state, and social media dimensions.
