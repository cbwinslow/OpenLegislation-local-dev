# OpenLegislation Project Summary

## Overview
OpenLegislation is a comprehensive legislative intelligence platform that aggregates, processes, and serves legislative data from multiple sources including New York State, federal government (Congress.gov, GovInfo.gov), and all 50 U.S. states via OpenStates. The platform provides real-time access to legislative information with AI-powered analysis, semantic search, and developer-friendly APIs.

## Core Mission
Democratize access to legislative information through advanced technology, AI-powered analysis, and developer-friendly APIs to support research, policy analysis, and civic engagement.

## Technology Stack
- **Backend**: Java 21, Spring 5 Framework, PostgreSQL, Elasticsearch 8.15.2
- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS
- **AI/ML**: Specialized AI agents for development, analysis, and automation
- **Infrastructure**: Docker, Ansible, Terraform, GitHub Actions CI/CD
- **Data Processing**: Real-time ingestion from XML/SOBI sources with <15 minute latency

## Key Capabilities
- **Multi-Source Data Integration**: Federal, state, and local legislative data harmonization
- **Real-Time Processing**: Continuous updates from all sources
- **AI-Powered Features**: Semantic search, content analysis, predictive analytics
- **Advanced APIs**: RESTful APIs with comprehensive documentation
- **Research Tools**: Comparative analysis, trend identification, impact assessment
- **Enterprise Features**: High availability (99.9% uptime), security compliance

## Data Sources
- **NY State LBDC**: Real-time NY legislative data (original source)
- **Congress.gov**: Official U.S. Congress legislative information
- **GovInfo.gov**: Bulk federal legislative data and documents
- **OpenStates**: All 50 state legislative data in unified format

## Architecture Components
- **Data Ingestion Pipeline**: XML/SOBI parsing, validation, and processing
- **Search & Indexing**: Elasticsearch for full-text and semantic search
- **API Layer**: REST APIs serving unified legislative data
- **Frontend**: Modern web interface for data exploration and management
- **AI Agents**: Specialized agents for development, analysis, and automation
- **Infrastructure**: Containerized deployment with monitoring and scaling

## Current Status
- **Data Coverage**: Complete federal and state legislative information
- **Performance**: <200ms API response time, >99.9% uptime
- **Users**: Developers, researchers, policymakers, and citizens
- **Licensing**: Dual BSD/GPL open source

## Development Workflow
- **Build**: Maven for Java compilation and packaging
- **Database**: Flyway migrations for schema management
- **Testing**: Unit and integration tests with JUnit
- **Deployment**: Tomcat 9 with automated CI/CD pipelines
- **Monitoring**: Comprehensive logging and performance monitoring

## Key Directories
- `src/`: Java source code (backend, processors, APIs)
- `frontend/`: Next.js web interface
- `docs/`: Comprehensive documentation
- `tools/`: Python utilities for data ingestion
- `infra/`: Infrastructure as Code configurations
- `ansible/`: Configuration management
- `crewai/`: AI agent implementations
- `staging/`: Data processing staging area
- `bin/`: Operational scripts

## Getting Started
1. Clone repository and set up environment
2. Configure PostgreSQL and Elasticsearch
3. Run `mvn compile flyway:migrate` to build and migrate DB
4. Start ingestion processes for data sources
5. Deploy frontend and backend services

For detailed setup instructions, see `README_DEV.md` and `docs/development.md`.

## Future Vision
- Enhanced AI capabilities for predictive analytics
- Global legislative data integration
- Advanced collaborative features
- Mobile applications
- Enterprise multi-tenant architecture

**Project Status**: Active and growing
**License**: BSD/GPL Dual License
**Repository**: https://github.com/nysenate/OpenLegislation</content>
<parameter name="filePath">/home/cbwinslow/OpenLegislation-local-dev/project_summary.md