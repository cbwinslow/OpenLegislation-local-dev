# Entity Relationship Diagram (ERP)

## Overview
This document provides visual representations of the OpenLegislation database schema and data processing workflows.

## Core Legislative Data Model

```
┌─────────────────┐       ┌──────────────────┐
│      Bill       │       │   BillAction     │
├─────────────────┤       ├──────────────────┤
│ bill_id (PK)    │◄────┐ │ action_id (PK)   │
│ session_year    │      │ │ bill_id (FK)    │
│ print_no        │      │ │ action_date     │
│ title           │      │ │ chamber         │
│ summary         │      │ │ action_text     │
│ status          │      │ │ sequence_no     │
│ bill_type       │      └──────────────────┘
│ created_date    │              │
│ modified_date   │              │
└─────────────────┘              │
         │                       │
         │ 1                     │ M
         │                       │
         ▼                       ▼
┌─────────────────┐       ┌──────────────────┐
│  BillSponsor    │       │ BillAmendment    │
├─────────────────┤       ├──────────────────┤
│ sponsor_id (PK) │       │ amendment_id (PK)│
│ bill_id (FK)    │       │ bill_id (FK)     │
│ member_id (FK)  │       │ version          │
│ sponsor_type    │       │ memo             │
│ sequence_no     │       │ full_text        │
└─────────────────┘       │ publish_date     │
                          └──────────────────┘
```

## Member and Committee Model

```
┌─────────────────┐       ┌──────────────────┐
│     Member      │       │ CommitteeMember │
├─────────────────┤       ├──────────────────┤
│ member_id (PK)  │◄────┐ │ member_id (PK)   │
│ session_year    │      │ │ committee_id (FK│
│ chamber         │      │ │ session_year    │
│ district_code   │      │ │ chamber         │
│ member_name     │      │ │ member_name     │
│ party           │      │ │ title           │
│ email           │      │ └──────────────────┘
│ website         │              │
└─────────────────┘              │
         │                       │
         │ 1                     │ M
         │                       │
         ▼                       ▼
┌─────────────────┐       ┌──────────────────┐
│MemberBiography  │       │    Committee     │
├─────────────────┤       ├──────────────────┤
│ bio_id (PK)     │       │ committee_id (PK)│
│ member_id (FK)  │       │ session_year     │
│ bio_type        │       │ chamber          │
│ bio_text        │       │ name             │
│ source_url      │       │ committee_type   │
└─────────────────┘       └──────────────────┘
```

## Calendar and Agenda Model

```
┌─────────────────┐       ┌──────────────────┐
│    Calendar     │       │ CalendarEntry    │
├─────────────────┤       ├──────────────────┤
│ calendar_id (PK)│◄────┐ │ entry_id (PK)    │
│ session_year    │      │ │ calendar_id (FK)│
│ calendar_number │      │ │ bill_id (FK)    │
│ calendar_date   │      │ │ bill_print_no   │
│ release_date_time│     │ │ bill_amend_ver  │
└─────────────────┘      │ │ entry_type      │
         │               └──────────────────┘
         │                       │
         │ 1                     │ M
         │                       │
         ▼                       ▼
┌─────────────────┐       ┌──────────────────┐
│     Agenda      │       │   Transcript     │
├─────────────────┤       ├──────────────────┤
│ agenda_id (PK)  │       │ transcript_id (PK│
│ session_year    │       │ session_year     │
│ agenda_number   │       │ date             │
│ committee_id (FK│       │ location         │
│ meeting_date_time│      │ transcript_type  │
└─────────────────┘       └──────────────────┘
                         │
                         │ 1
                         │
                         ▼
                  ┌──────────────────┐
                  │ TranscriptFile   │
                  ├──────────────────┤
                  │ file_id (PK)     │
                  │ transcript_id (FK│
                  │ file_name        │
                  │ text             │
                  │ sequence_no      │
                  └──────────────────┘
```

## Law and Document Model

```
┌─────────────────┐       ┌──────────────────┐
│      Law        │       │  LawDocument     │
├─────────────────┤       ├──────────────────┤
│ law_id (PK)     │◄────┐ │ document_id (PK) │
│ law_id_str      │      │ │ law_id (FK)     │
│ title           │      │ │ document_type   │
│ chapter         │      │ │ title           │
│ created_date    │      │ │ text            │
│ modified_date   │      │ │ publish_date    │
└─────────────────┘      └──────────────────┘
```

## Data Processing Model

```
┌─────────────────┐       ┌──────────────────┐
│   SourceFile    │       │ DataProcessRun   │
├─────────────────┤       ├──────────────────┤
│ file_id (PK)    │       │ run_id (PK)      │
│ file_name       │       │ start_time       │
│ source_type     │       │ end_time         │
│ staging_path    │       │ status           │
│ archive_path    │       │ records_processed│
│ processed_date  │       │ errors_count     │
│ error_message   │       └──────────────────┘
└─────────────────┘
```

## Data Flow Diagrams

### Bill Processing Flow

```
Raw XML/SOBI Files
        │
        ▼
   SourceFile DAO
        │
        ▼
  XML/SOBI Parser
        │
        ▼
   Bill Processor
        │
        ▼
Bill Model Objects
        │
        ▼
   Bill DAO
        │
        ▼
  PostgreSQL DB
        │
        ▼
 Elasticsearch
        │
        ▼
    REST API
        │
        ▼
   Web Client
```

### Federal Data Integration Flow

```
Congress.gov API ──┐
                   │
GovInfo.gov API ───┼──► Federal Data Processor
                   │
XML Bulk Files ────┘
        │
        ▼
Federal Bill Models
        │
        ▼
   Bill DAO
        │
        ▼
PostgreSQL (Federal Fields)
        │
        ▼
   Search Index
        │
        ▼
Federal API Endpoints
```

### Research Data Flow

```
Bill Text Data ───► NLP Processor ───► Topic Analysis
        │                                       │
        └────────────► Sentiment Analysis ──────┘
                                │
                                ▼
                        Research Reports
                                │
                                ▼
                     JSON Output Files
```

## Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenLegislation System                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Web UI    │    │   REST API  │    │  Admin API  │     │
│  │  (React)    │    │  (Spring)   │    │  (Spring)   │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│           │                   │                   │         │
├───────────┼───────────────────┼───────────────────┼─────────┤
│           │                   │                   │         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ Data Access │    │   Business  │    │   Process   │     │
│  │   Layer     │    │   Services  │    │  Services   │     │
│  │   (DAO)     │    │  (Spring)   │    │  (Spring)   │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│           │                   │                   │         │
├───────────┼───────────────────┼───────────────────┼─────────┤
│           │                   │                   │         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ PostgreSQL  │    │ Elasticsearch│    │   Tools    │     │
│  │   Database  │    │    Search    │    │ (Python)   │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Production Environment                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Load      │    │ Application │    │   Database  │     │
│  │  Balancer   │    │   Servers   │    │   Servers   │     │
│  │             │    │  (Tomcat)   │    │ (PostgreSQL)│     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│           │                   │                   │         │
├───────────┼───────────────────┼───────────────────┼─────────┤
│           │                   │                   │         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Search    │    │   File      │    │   Backup    │     │
│  │   Cluster   │    │  Storage    │    │   Storage   │     │
│  │(Elasticsearch│    │             │    │             │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Data Processing Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Ingest    │───▶│  Process   │───▶│   Store     │
│             │    │             │    │             │
│ • XML Files │    │ • Parse XML │    │ • PostgreSQL│
│ • SOBI Files│    │ • Validate  │    │ • Index     │
│ • API Data  │    │ • Transform │    │ • Cache     │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Index     │───▶│   Search   │───▶│   Serve     │
│             │    │             │    │             │
│ • Elasticsearch│  │ • Full-text│    │ • REST API  │
│ • Facets     │    │ • Filters  │    │ • JSON      │
│ • Analytics  │    │ • Sort     │    │ • CORS      │
└─────────────┘    └─────────────┘    └─────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Security Layers                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │Application  │    │ Database    │    │   Network   │     │
│  │   Layer     │    │   Layer     │    │   Layer     │     │
│  │             │    │             │    │             │     │
│  │ • Input Val │    │ • RLS       │    │ • SSL/TLS   │     │
│  │ • Auth      │    │ • Grants    │    │ • Firewall  │     │
│  │ • XSS Prot  │    │ • Audit     │    │ • VPN       │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Performance Optimization

### Database Indexing Strategy

```
Bill Table Indexes:
├── PRIMARY KEY (bill_id)
├── UNIQUE (session_year, print_no)
├── INDEX (session_year)
├── INDEX (status)
├── INDEX (modified_date DESC)
├── FULLTEXT (title, summary)
└── COMPOSITE (session_year, status, modified_date)

Action Table Indexes:
├── PRIMARY KEY (action_id)
├── FOREIGN KEY (bill_id)
├── INDEX (bill_id)
├── INDEX (action_date DESC)
└── COMPOSITE (bill_id, action_date)

Sponsor Table Indexes:
├── PRIMARY KEY (sponsor_id)
├── FOREIGN KEY (bill_id)
├── FOREIGN KEY (member_id)
├── INDEX (bill_id)
└── INDEX (member_id)
```

### Query Optimization Patterns

```
Common Query Patterns:
├── Bill search by session/year
├── Recent bill actions
├── Bills by sponsor
├── Committee membership
└── Calendar entries

Optimization Techniques:
├── Index-only scans
├── Query result caching
├── Connection pooling
├── Read replicas
└── Query plan analysis
```

This ERD documentation provides a comprehensive view of the OpenLegislation data architecture, processing flows, and system interactions. The diagrams help developers understand the relationships between entities and the flow of data through the system.