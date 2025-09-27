# OpenLegislation Project Summary

## Overview
OpenLegislation is a Java-based system for processing and storing legislative data, primarily focused on New York State legislation. The system ingests data from various sources, processes it through specialized parsers, and stores it in a PostgreSQL database.

## Architecture
- **Language**: Java with Spring Framework
- **Database**: PostgreSQL with Flyway migrations
- **Data Sources**: SOBI files, XML feeds, scraping
- **Processing**: Event-driven processors for bills, agendas, transcripts
- **Storage**: Master schema with tables for bills, amendments, actions, sponsors, etc.

## Key Components
- **Processors**: Handle different data types (bills, agendas, transcripts)
- **DAOs**: Data Access Objects for database operations
- **Models**: Domain objects (Bill, BillAction, BillSponsor, etc.)
- **APIs**: REST endpoints for data access
- **Tools**: Python scripts for data fetching and ETL

## Congress.gov Integration Goal
The project aims to integrate federal legislative data from congress.gov to complement the state-level data. This involves:

1. **Data Source**: GovInfo bulk XML data from congress.gov
2. **Mapping**: Map XML elements to existing OpenLegislation models
3. **Processing**: Extend processors to handle federal data
4. **Storage**: Create staging tables or extend master schema
5. **Ingestion**: Parse XML and store structured data

## Current Status
- GovInfo integration framework exists with processors and documentation
- Python tools for bulk data fetching
- Mapping documents for XML to model conversion
- Staging approach recommended to avoid master data conflicts

## Challenges
- Federal vs State data model differences
- XML parsing complexity
- Data volume and update frequency
- Maintaining data integrity across sources
