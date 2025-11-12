# Data Source Integration Specifications

## Overview

This document defines technical specifications for integrating OpenLegislation with four primary data sources: Congress.gov, GovInfo.gov, OpenStates, and NY State LBDC. Each source has unique characteristics, API patterns, and data formats that require specialized handling.

---

## 1. Congress.gov API Integration

### 1.1 API Characteristics
- **Base URL**: `https://api.congress.gov/v3/`
- **Authentication**: API Key required
- **Rate Limiting**: 1,000 requests per hour
- **Data Format**: JSON
- **Update Frequency**: Real-time for most endpoints

### 1.2 Supported Endpoints

#### Bills Endpoint
```
GET /bill/{congress}/{chamber}/{billNumber}
```
- **Purpose**: Retrieve detailed bill information
- **Parameters**: 
  - `congress`: Congress number (e.g., 118)
  - `chamber`: House or Senate
  - `billNumber`: Bill identifier
- **Response Fields**: title, summary, sponsor, cosponsors, actions, amendments, text versions
- **Update Frequency**: Real-time

#### Amendments Endpoint
```
GET /amendment/{congress}/{chamber}/{amendmentNumber}
```
- **Purpose**: Retrieve amendment details
- **Response Fields**: description, sponsor, chamber, status, text
- **Update Frequency**: Real-time

#### Members Endpoint
```
GET /member/{congress}/{chamber}/{memberCode}
```
- **Purpose**: Retrieve member biographical and service information
- **Response Fields**: name, party, state, district, service history, contact info
- **Update Frequency**: Daily

#### Committees Endpoint
```
GET /committee/{chamber}/{committeeCode}
```
- **Purpose**: Retrieve committee information and membership
- **Response Fields**: name, jurisdiction, subcommittees, members, leadership
- **Update Frequency**: Weekly

#### Votes Endpoint
```
GET /roll-call-vote/{congress}/{chamber}/{session/{rollCallNumber}
```
- **Purpose**: Retrieve roll call vote data
- **Response Fields**: question, date, result, votes by member
- **Update Frequency**: Real-time

### 1.3 Integration Requirements

#### Rate Limiting Strategy
```python
import time
from datetime import datetime, timedelta

class CongressGovRateLimiter:
    def __init__(self, requests_per_hour=1000):
        self.requests_per_hour = requests_per_hour
        self.requests = []
    
    def wait_if_needed(self):
        now = datetime.now()
        # Remove requests older than 1 hour
        self.requests = [req for req in self.requests if now - req < timedelta(hours=1)]
        
        if len(self.requests) >= self.requests_per_hour:
            sleep_time = 3600 - (now - self.requests[0]).seconds
            time.sleep(sleep_time)
        
        self.requests.append(now)
```

#### Error Handling
- **429 Too Many Requests**: Exponential backoff with jitter
- **5xx Server Errors**: Retry with exponential backoff (max 5 attempts)
- **Network Errors**: Circuit breaker pattern
- **Data Validation**: Schema validation for all responses

#### Data Mapping
| Congress.gov Field | Target Schema | Transformation |
|------------------|---------------|-----------------|
| bill.congress | bill.congress_number | Direct mapping |
| bill.billNumber | bill.bill_number | Direct mapping |
| bill.title | bill.title | Direct mapping |
| bill.sponsor | bill.sponsor_id | Lookup member table |
| bill.cosponsors | bill.cosponsors | Array of member IDs |
| bill.actions | bill.actions | Array with date sequencing |
| bill.textVersions | bill.text_versions | Array with URLs |

---

## 2. GovInfo.gov Bulk Data Integration

### 2.1 Data Characteristics
- **Base URL**: `https://www.govinfo.gov/`
- **Authentication**: None required (public data)
- **Data Format**: XML (primary), JSON (some collections)
- **Update Frequency**: Daily bulk packages
- **Volume**: Terabytes of historical data

### 2.2 Supported Collections

#### BILLS Collection
- **Path Pattern**: `/packages/BILLS/{congress}/{chamber}/{billType}/{billNumber}/`
- **File Types**: 
  - `{billType}{billNumber}.xml` - Bill metadata
  - `{billType}{billNumber}{version}.xml` - Bill text versions
  - `{billType}{billNumber}.pdf` - Bill PDF
- **Update Frequency**: Daily for active legislation

#### BILLSTATUS Collection
- **Path Pattern**: `/packages/BILLSTATUS/{congress}/`
- **File Types**: 
  - `BILLSTATUS-{congress}.xml` - Status history
- **Update Frequency**: Daily

#### COMMITTEEREPORTS Collection
- **Path Pattern**: `/packages/CRPT/{congress}/{chamber}/{committeeCode}/`
- **File Types**: Committee reports in XML and PDF
- **Update Frequency**: As published

#### CRPT (Congressional Record)
- **Path Pattern**: `/packages/CREC/{date}/`
- **File Types**: Daily Congressional Record
- **Update Frequency**: Daily

#### STATUTE Collection
- **Path Pattern**: `/packages/STATUTE-{volume}/`
- **File Types**: United States Statutes at Large
- **Update Frequency**: Annual

### 2.3 Integration Requirements

#### Bulk Download Strategy
```python
import requests
import os
from pathlib import Path

class GovInfoBulkDownloader:
    def __init__(self, base_url="https://www.govinfo.gov"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def download_collection(self, collection, congress=None):
        """Download entire collection with progress tracking"""
        if collection == "BILLS":
            return self.download_bills(congress)
        elif collection == "BILLSTATUS":
            return self.download_billstatus(congress)
        # ... other collections
    
    def download_with_resume(self, url, local_path):
        """Download with resume capability for large files"""
        # Implementation for resumable downloads
        pass
```

#### XML Processing Pipeline
```python
import xml.etree.ElementTree as ET
from lxml import etree  # For large files

class GovInfoXMLProcessor:
    def __init__(self):
        self.namespaces = {
            'ns': 'http://xml.house.gov/schemas/uslm/1.0'
        }
    
    def process_bill_xml(self, xml_file):
        """Process bill XML with validation"""
        try:
            tree = etree.parse(xml_file)
            root = tree.getroot()
            
            bill_data = {
                'congress': root.get('congress'),
                'session': root.get('session'),
                'legis-num': root.get('legis-num'),
                'legis-type': root.get('legis-type'),
                'title': self.extract_title(root),
                'sponsor': self.extract_sponsor(root),
                'cosponsors': self.extract_cosponsors(root),
                'actions': self.extract_actions(root),
                'text_versions': self.extract_text_versions(root)
            }
            
            return self.validate_bill_data(bill_data)
            
        except Exception as e:
            self.log_error(f"Error processing {xml_file}: {e}")
            return None
```

#### Data Validation
- **Schema Validation**: XSD schema validation for all XML files
- **Cross-Reference Validation**: Ensure references exist between collections
- **Completeness Checks**: Verify required fields are present
- **Format Validation**: Ensure dates, numbers, and codes are valid

---

## 3. OpenStates API Integration

### 3.1 API Characteristics
- **Base URL**: `https://v3.openstates.org/`
- **Authentication**: API Key required
- **Rate Limiting**: 1,000 requests per hour
- **Data Format**: JSON
- **Coverage**: All 50 states + DC and territories

### 3.2 Supported Endpoints

#### Bills Endpoint
```
GET /bills/?state={state}&session={session}&q={query}
```
- **Purpose**: Search and retrieve state legislation
- **Parameters**:
  - `state`: Two-letter state code
  - `session`: Legislative session identifier
  - `q`: Search query (optional)
  - `page`: Pagination (default: 1)
  - `per_page`: Results per page (max: 50)
- **Response Fields**: id, title, identifier, classification, subject, abstract, sponsor, actions, votes
- **Update Frequency**: Varies by state (daily to weekly)

#### Legislators Endpoint
```
GET /legislators/?state={state}&chamber={chamber}
```
- **Purpose**: Retrieve state legislator information
- **Response Fields**: id, name, party, chamber, district, contact_info, active
- **Update Frequency**: Daily

#### Committees Endpoint
```
GET /committees/?state={state}&chamber={chamber}
```
- **Purpose**: Retrieve state committee information
- **Response Fields**: id, name, chamber, parent, members, source
- **Update Frequency**: Weekly

#### Districts Endpoint
```
GET /districts/?state={state}&chamber={chamber}
```
- **Purpose**: Retrieve legislative district boundaries
- **Response Fields**: id, name, boundary_shape, num_seats
- **Update Frequency**: Annual

### 3.3 State-Specific Adaptations

#### Legislative Structure Variations
| State | Legislature Type | Session Pattern | Bill Numbering |
|--------|------------------|------------------|-----------------|
| California | Bicameral | 2-year sessions | AB/SB + number |
| Texas | Bicameral | Biennial sessions | HB/SB + number |
| Nebraska | Unicameral | 2-year sessions | LB + number |
| New York | Bicameral | 2-year sessions | A/S + number |

#### Session Calendar Handling
```python
class StateSessionHandler:
    def __init__(self):
        self.session_patterns = {
            'CA': r'(\d{4})-(\d{4})',  # 2023-2024
            'TX': r'(\d{1})[RS]',      # 88R, 89R
            'NE': r'(\d{4})',          # 2023, 2024
            'NY': r'(\d{4})-(\d{4})'   # 2023-2024
        }
    
    def parse_session(self, state, session_string):
        """Parse session identifier based on state pattern"""
        pattern = self.session_patterns.get(state)
        if pattern:
            match = re.match(pattern, session_string)
            return match.groups() if match else None
        return None
```

### 3.4 Integration Requirements

#### Multi-State Coordination
```python
class OpenStatesCoordinator:
    def __init__(self, api_key, max_workers=10):
        self.api_key = api_key
        self.max_workers = max_workers
        self.state_configs = self.load_state_configs()
    
    def sync_all_states(self):
        """Coordinate synchronization across all states"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for state in self.get_all_states():
                future = executor.submit(self.sync_state, state)
                futures.append(future)
            
            # Collect results and handle errors
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.log_error(f"State sync failed: {e}")
            
            return results
```

#### Data Harmonization
- **Bill Classification**: Map state-specific bill types to standard categories
- **Chamber Standardization**: Normalize chamber names (House/Senate/Assembly)
- **Party Codes**: Standardize party abbreviations across states
- **Date Formats**: Normalize date formats and time zones
- **Geographic Data**: Standardize district and boundary representations

---

## 4. NY State LBDC Integration

### 4.1 Data Characteristics
- **Source**: Legislative Bill Drafting Commission (LBDC)
- **Data Format**: XML, JSON, plain text
- **Update Frequency**: Real-time during session
- **Authentication**: Custom API with credentials
- **Volume**: Moderate (single state data)

### 4.2 Data Types

#### Bills and Resolutions
- **Content**: Bill text, amendments, resolutions
- **Format**: Structured XML with metadata
- **Update**: Real-time as introduced/amended
- **Fields**: Bill number, title, sponsor, status, text, actions

#### Laws and Codes
- **Content**: Consolidated laws of New York
- **Format**: Hierarchical XML structure
- **Update**: Annual consolidation
- **Fields**: Law code, section, text, effective date

#### Calendars and Schedules
- **Content**: Legislative floor calendars, committee schedules
- **Format**: XML with date/time information
- **Update**: Daily during session
- **Fields**: Calendar type, bill list, schedule, locations

### 4.3 Integration Requirements

#### Real-time Processing
```python
class LBDCCrawler:
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.last_update = None
    
    def monitor_updates(self):
        """Monitor LBDC for real-time updates"""
        while True:
            try:
                updates = self.check_for_updates()
                if updates:
                    self.process_updates(updates)
                    self.last_update = datetime.now()
                
                time.sleep(self.config['check_interval'])
                
            except Exception as e:
                self.log_error(f"Monitor error: {e}")
                time.sleep(60)  # Wait before retry
```

#### Legacy Compatibility
- **API Compatibility**: Maintain existing NY State API endpoints
- **Data Migration**: Gradual migration to unified schema
- **Backward Compatibility**: Support existing client applications
- **Transition Period**: Dual operation during migration

---

## 5. Data Harmonization Framework

### 5.1 Unified Data Model

#### Core Entities
```sql
-- Unified Bill Entity
CREATE TABLE unified_bills (
    id UUID PRIMARY KEY,
    source_system VARCHAR(50) NOT NULL,  -- congress.gov, govinfo, openstates, lbdc
    source_id VARCHAR(255) NOT NULL,     -- Original bill identifier
    jurisdiction VARCHAR(50) NOT NULL,    -- federal, state_code
    congress_number INTEGER,               -- For federal bills
    session VARCHAR(50),                  -- Legislative session
    bill_number VARCHAR(50) NOT NULL,
    bill_type VARCHAR(50),               -- HR, S, AB, SB, etc.
    title TEXT NOT NULL,
    summary TEXT,
    sponsor_id UUID REFERENCES people(id),
    cosponsors UUID[] REFERENCES people(id),
    status VARCHAR(100),
    introduced_date DATE,
    last_action_date DATE,
    text_content TEXT,
    text_versions JSONB,
    actions JSONB,
    subjects JSONB,
    committees JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_system, source_id)
);
```

#### Entity Resolution
```python
class EntityResolver:
    def __init__(self):
        self.match_threshold = 0.85
        self.blocking_keys = ['name', 'state', 'chamber']
    
    def resolve_legislator(self, legislator_data):
        """Resolve legislator across different sources"""
        # Generate blocking key for efficient matching
        blocking_key = self.generate_blocking_key(legislator_data)
        
        # Find potential matches
        candidates = self.find_candidates(blocking_key)
        
        # Score matches using fuzzy matching
        matches = []
        for candidate in candidates:
            score = self.calculate_similarity(legislator_data, candidate)
            if score >= self.match_threshold:
                matches.append((candidate, score))
        
        # Return best match or create new entity
        if matches:
            return max(matches, key=lambda x: x[1])[0]
        else:
            return self.create_new_entity(legislator_data)
```

### 5.2 Cross-Reference Linking

#### Federal-State Bill Linking
```python
class FederalStateLinker:
    def __init__(self):
        self.similarity_threshold = 0.8
        self.text_analyzer = TextAnalyzer()
    
    def find_related_bills(self, federal_bill, state_bills):
        """Find state bills related to federal legislation"""
        related = []
        
        for state_bill in state_bills:
            # Title similarity
            title_sim = self.text_analyzer.similarity(
                federal_bill['title'], 
                state_bill['title']
            )
            
            # Content similarity
            content_sim = self.text_analyzer.similarity(
                federal_bill['summary'] or '',
                state_bill['summary'] or ''
            )
            
            # Subject overlap
            subject_overlap = self.calculate_subject_overlap(
                federal_bill['subjects'],
                state_bill['subjects']
            )
            
            # Combined score
            combined_score = (
                title_sim * 0.4 + 
                content_sim * 0.4 + 
                subject_overlap * 0.2
            )
            
            if combined_score >= self.similarity_threshold:
                related.append({
                    'state_bill': state_bill,
                    'similarity_score': combined_score,
                    'title_similarity': title_sim,
                    'content_similarity': content_sim,
                    'subject_overlap': subject_overlap
                })
        
        return sorted(related, key=lambda x: x['similarity_score'], reverse=True)
```

---

## 6. Quality Assurance and Monitoring

### 6.1 Data Quality Metrics

#### Completeness Metrics
- **Field Completeness**: Percentage of required fields populated
- **Record Completeness**: Percentage of expected records present
- **Temporal Completeness**: Coverage of expected time periods
- **Geographic Completeness**: Coverage of all jurisdictions

#### Accuracy Metrics
- **Validation Pass Rate**: Percentage of records passing validation
- **Cross-Reference Accuracy**: Accuracy of entity linking
- **Duplicate Detection**: False positive/negative rates
- **Data Freshness**: Age of most recent updates

#### Consistency Metrics
- **Format Consistency**: Standardization of data formats
- **Naming Consistency**: Standardization of names and codes
- **Temporal Consistency**: Logical sequence of dates and events
- **Referential Integrity**: Accuracy of relationships and links

### 6.2 Monitoring and Alerting

#### System Health Monitoring
```python
class DataIngestionMonitor:
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
    
    def monitor_ingestion_health(self):
        """Monitor overall health of data ingestion"""
        metrics = {
            'ingestion_rate': self.calculate_ingestion_rate(),
            'error_rate': self.calculate_error_rate(),
            'latency': self.calculate_average_latency(),
            'data_quality': self.calculate_quality_score(),
            'system_resources': self.get_resource_usage()
        }
        
        # Check thresholds and send alerts
        for metric, value in metrics.items():
            if not self.is_healthy(metric, value):
                self.alert_manager.send_alert(metric, value)
        
        self.metrics_collector.record(metrics)
```

#### Alert Thresholds
| Metric | Warning Threshold | Critical Threshold | Action |
|---------|------------------|-------------------|---------|
| Ingestion Rate | <80% expected | <50% expected | Investigate bottlenecks |
| Error Rate | >5% | >10% | Immediate investigation |
| Latency | >2x baseline | >5x baseline | Performance analysis |
| Data Quality | <95% score | <90% score | Quality review |
| System Resources | >80% usage | >95% usage | Scale resources |

---

## 7. Implementation Timeline

### Phase 1: Foundation (Weeks 1-4)
- Set up development environments and infrastructure
- Implement basic API clients for all data sources
- Create data validation frameworks
- Establish monitoring and logging

### Phase 2: Core Integration (Weeks 5-8)
- Complete Congress.gov API integration
- Implement GovInfo.gov bulk data processing
- Develop OpenStates multi-state coordination
- Enhance NY State LBDC integration

### Phase 3: Harmonization (Weeks 9-12)
- Implement unified data model
- Develop entity resolution system
- Create cross-reference linking
- Build data quality assurance

### Phase 4: Optimization (Weeks 13-16)
- Performance tuning and optimization
- Implement advanced error handling
- Complete monitoring and alerting
- Documentation and testing

---

## 8. Success Criteria

### Technical Success Metrics
- **Coverage**: 100% of federal and state legislative data
- **Freshness**: Real-time updates within 15 minutes
- **Accuracy**: Data accuracy >99%
- **Performance**: API response time <200ms
- **Availability**: System uptime >99.9%

### Business Success Metrics
- **User Adoption**: >1000 active monthly users
- **Developer Usage**: >100 external API users
- **Data Usage**: >1M API calls per month
- **User Satisfaction**: >4.5/5 satisfaction score
- **Research Impact**: >50 academic citations

---

**Document Version**: 1.0  
**Last Updated**: November 2025  
**Next Review**: December 2025  
**Technical Contact**: OpenLegislation Development Team