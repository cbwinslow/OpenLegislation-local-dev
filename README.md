OpenLegislation
====================

`From the New York State Senate`

Dual BSD/GPL License. See the NYSenate licensing page http://www.nysenate.gov/Open-Source-Software-Licenses.

OpenLegislation is a comprehensive platform for accessing and analyzing legislative data from multiple sources. Originally developed by the New York State Senate for NY State legislative data, it has evolved into a unified platform that aggregates federal and all 50 state legislative information.

**Core Mission**: Democratize access to legislative information through advanced technology, AI-powered analysis, and developer-friendly APIs.

**Data Sources**:
- **NY State LBDC**: Real-time NY State legislative data (original source)
- **Congress.gov**: Official U.S. Congress legislative information
- **GovInfo.gov**: Bulk federal legislative data and documents
- **OpenStates**: All 50 state legislative data in unified format

**Key Capabilities**:
- Multi-source data aggregation and harmonization
- Real-time data processing and updates
- AI-powered semantic search and content analysis
- Comprehensive analytics and trend identification
- Developer-friendly APIs and SDKs
- Advanced research and comparison tools

Updates to legislative data are processed in real-time from multiple sources and redistributed through unified APIs for integration with various web applications. The platform is developed and run using modern open-source technologies and frameworks including:

* Java 17
* Spring 5 Framework
* PostgreSQL
* Elasticsearch 8
* React
* Tomcat 9

![Bill page demo](https://raw.githubusercontent.com/nysenate/OpenLegislation/dev/src/main/webapp/static/img/bill-page.png)

## 🤖 PR Automation

This repository includes comprehensive automated PR management:

### GitHub Actions (Built-in)
- Auto-merges safe Dependabot updates
- Provides automated code review feedback
- Automatically labels and categorizes PRs
- Generates weekly PR dashboards
- Manages stale PRs

**📚 [Learn More](docs/pr-automation-README.md)** | **🚀 [Setup Guide](docs/pr-automation-setup.md)**

### AI Webhook Server (Self-hosted)
New! Deploy your own AI-powered code review webhook server:
- Uses OpenRouter AI agents (Claude, GPT-4, etc.) for intelligent code review
- Provides detailed analysis: security, bugs, style, performance
- Auto-merge capability based on AI review scores
- Designed for homelab deployment with Docker

**🚀 [Webhook Server Guide](webhook-server/README.md)** | **⚙️ [Setup Instructions](webhook-server/SETUP.md)**

Current Senate Developers
---------------------------

* Kevin Caseiras <caseiras@nysenate.gov>
* Ken Zalewski <zalewski@nysenate.gov>
* Anthony Calabrese <calabres@nysenate.gov>
* Jacob Keegan <keegan@nysenate.gov>

Past Developers
--------------------

* Nathan Freitas <nathanfreitas@gmail.com>
* Jared Williams <jared.mi.williams@gmail.com>
* Graylin Kim <kim@nysenate.gov>
* Ash Islam <islam@nysenate.gov>
* Sam Stouffer <stouffer@nysenate.gov>

## 📁 Project Structure

This repository is organized into several key directories, each serving a specific purpose in the OpenLegislation ecosystem:

### Core Application
- **`src/`** - Java source code for the OpenLegislation application
  - `main/` - Main application code including API controllers, data processors, and business logic
  - `test/` - Unit and integration tests
  - `db/` - Database migration scripts and SQL files
  - `pipeline/` - Data processing pipeline components
  - `vector/` - Vector database and semantic search components

- **`pom.xml`** - Maven build configuration for the Java application (Java 17, Spring 5, PostgreSQL, Elasticsearch 8)

### Frontend & User Interfaces
- **`frontend/`** - Next.js-based web interface for data ingestion management
  - Parameter-based filtering for downloading datasets
  - Real-time monitoring of ingestion progress
  - Data viewer for browsing ingested data
  - AI-enhanced processing capabilities

### Data Ingestion & Tools
- **`tools/`** - Python utilities and scripts for data ingestion and analysis
  - `ingest_*.py` - Scripts for pulling legislative data from Congress.gov, GovInfo, and other sources
  - `install_*.sh` - Infrastructure provisioning scripts (Elasticsearch, PostgreSQL, Tomcat, etc.)
  - `research/` - Reproducible analysis pipelines for legislative research
    - Bill text analysis (TF-IDF, topic modeling, sentiment analysis)
    - Social media research and engagement tracking
    - Member activity summaries and statistics
  - See [tools/README.md](tools/README.md) for detailed documentation

### Infrastructure & Operations
- **`bin/`** - Operational scripts for running the application
  - `run.sh` - Application startup script
  - `cron.sh` - Scheduled task management
  - `elasticsearch.sh` - Elasticsearch management utilities
  - `website_cron_*.sh` - Website synchronization scripts
  - `xferdata.sh` - Data transfer utilities

- **`infra/`** - Infrastructure as Code (IaC) configurations
  - `terraform/` - Terraform configurations for cloud infrastructure
  - `pulumi/` - Pulumi configurations for infrastructure management
  - `scripts/` - Infrastructure management scripts

- **`ansible/`** - Ansible playbooks for configuration management
  - Automated deployment configurations
  - GitLab integration setup
  - Server provisioning playbooks

### Automation & CI/CD
- **`webhook-server/`** - AI-powered PR review and auto-merge webhook server
  - OpenRouter AI integration (Claude, GPT-4, etc.)
  - Automated code review with security, bug, and style analysis
  - Quality scoring system (1-10) for PRs
  - Optional auto-merge based on thresholds
  - Designed for self-hosted deployment
  - See [webhook-server/README.md](webhook-server/README.md) for setup

- **`.github/`** - GitHub Actions workflows and automation
  - Auto-merge for safe Dependabot updates
  - Automated code review feedback
  - PR labeling and categorization
  - Weekly PR dashboards
  - Stale PR management

### Documentation
- **`docs/`** - Comprehensive project documentation
  - `backend/` - Backend development guides
  - `api/` - API documentation and reference
  - `external_docs/` - Third-party integration documentation
  - Federal data integration guides (Congress.gov, GovInfo)
  - Database schema documentation
  - Deployment and setup guides
  - See [docs/pr-automation-README.md](docs/pr-automation-README.md) for PR automation details

### Testing & Quality Assurance
- **`jmeter/`** - JMeter load testing configurations
  - API load test scripts
  - Performance benchmarking tools

### Data Models
- **`models/`** - Python data models for legislative entities
  - Bill, agenda, calendar, committee models
  - Member and person data structures
  - Spotcheck and quality assurance models

### Configuration
- **`.env.example`** - Environment variable template
- **`README_DEV.md`** - Local development quickstart guide
- **`requirements.txt`** - Python dependencies
- **`setup_user.sh`** - User environment setup script

## 🎯 Project Goals

OpenLegislation has evolved to address comprehensive legislative data needs:

1. **Comprehensive Data Coverage** - Provide free, open access to NY State, federal, and all 50 state legislative information through unified APIs

2. **Multi-Source Integration** - Aggregate and harmonize data from NY State LBDC, Congress.gov, GovInfo.gov, and OpenStates into a single platform

3. **Real-time Processing** - Parse and redistribute legislative updates in real-time from all sources with <15 minute latency

4. **AI-Powered Analysis** - Incorporate semantic search, ML-powered insights, and automated content analysis for legislative intelligence

5. **Developer-Friendly Platform** - Offer well-documented REST APIs, SDKs, and tools for easy integration with web applications and research projects

6. **Advanced Research Tools** - Support policy research through comparative analysis, trend identification, and predictive analytics across jurisdictions

7. **Open Source Collaboration** - Foster transparency and community contributions through dual BSD/GPL licensing and active community engagement

8. **Modern Infrastructure** - Leverage cloud-native technologies (Java 17, Spring 5, PostgreSQL, Elasticsearch, pgvector) for scalability and reliability

9. **Cross-Jurisdiction Analytics** - Enable comparative analysis between federal and state legislation, tracking policy diffusion and influence

10. **Enterprise-Grade Quality** - Maintain 99.9% uptime, >99% data accuracy, and comprehensive security compliance

---

## 🚀 Enhanced Capabilities & Documentation

### Multi-Source Data Integration
- **Comprehensive Coverage**: Federal + all 50 states legislative data
- **Real-time Synchronization**: Updates within 15 minutes from all sources
- **Data Harmonization**: Unified data model across different legislative structures
- **Intelligent Deduplication**: Advanced entity resolution and duplicate detection

### AI-Powered Features
- **Semantic Search**: Natural language queries with vector embeddings
- **Content Analysis**: Automated bill classification, sentiment analysis, and summarization
- **Predictive Analytics**: Bill passage probability and trend identification
- **Comparative Analysis**: Cross-jurisdiction legislation comparison and influence tracking

### Developer Resources
- **Comprehensive APIs**: RESTful APIs with OpenAPI documentation
- **SDKs & Tools**: Client libraries for popular programming languages
- **Sandbox Environment**: Safe testing environment for development
- **Community Support**: Developer forums, documentation, and tutorials

### Advanced Documentation
- **[Enhanced Tasks Management](docs/tasks-enhanced.md)**: Comprehensive project roadmap with microgoals and success criteria
- **[Software Requirements Specification](docs/srs-enhanced.md)**: Detailed technical requirements and validation criteria
- **[Data Source Integration](docs/data-source-integration.md)**: Technical specifications for all data sources
- **[Automation Guide](docs/AUTOMATION_README.md)**: Complete CI/CD and automation documentation
- **[API Reference](docs/api/)**: Comprehensive API documentation and examples

### Research & Analytics Platform
- **Comparative Analysis**: Track policy diffusion across states and federal levels
- **Trend Identification**: Identify emerging legislative trends and patterns
- **Impact Assessment**: Measure effectiveness and outcomes of legislation
- **Custom Reports**: Generate tailored analytics and visualizations

---

## 📊 Key Performance Metrics

### Technical Performance
- **API Response Time**: <200ms (95th percentile)
- **System Availability**: >99.9% uptime
- **Data Freshness**: <15 minute update latency
- **Search Accuracy**: >90% relevance score
- **Throughput**: 10,000+ concurrent users

### Data Quality
- **Coverage**: 100% federal and state legislative data
- **Accuracy**: >99% data accuracy across all sources
- **Completeness**: >98% field completeness
- **Consistency**: Unified data model across all sources

### User Engagement
- **Developer Adoption**: >100 external API users
- **Research Usage**: >50 academic citations annually
- **User Satisfaction**: >4.5/5 satisfaction score
- **Community Growth**: >30% year-over-year contributor growth
