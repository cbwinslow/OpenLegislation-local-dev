OpenLegislation
====================

`From the New York State Senate`

Dual BSD/GPL License. See the NYSenate licensing page http://www.nysenate.gov/Open-Source-Software-Licenses.

Open Legislation is an open source web service developed in-house by the New York State Senate to provide access to NYS legislative data including bills, resolutions, and laws. Developers can request a free key for the JSON API at http://legislation.nysenate.gov/. The JSON API is documented at http://legislation.nysenate.gov/static/docs/html/.

Updates to legislative data are distributed by the Legislative Bill drafting Commission (LBDC) in a raw, plain text format. Open Legislation parses the updates in real time and redistributes the data through the JSON API for integration with various web applications. It is developed and run using several open-source technologies and frameworks including:

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

OpenLegislation was created to:

1. **Democratize Legislative Data** - Provide free, open access to New York State legislative information through a modern JSON API

2. **Real-time Data Processing** - Parse and redistribute legislative updates in real time from the Legislative Bill Drafting Commission (LBDC)

3. **Federal Integration** - Extend capabilities to include federal legislative data from Congress.gov and GovInfo, enabling comprehensive legislative tracking

4. **Developer-Friendly API** - Offer a well-documented REST API for easy integration with web applications, research tools, and civic tech projects

5. **Open Source Collaboration** - Foster transparency and community contributions by maintaining dual BSD/GPL licensing

6. **Modern Technology Stack** - Leverage cutting-edge open-source technologies (Java 17, Spring 5, PostgreSQL, Elasticsearch 8, React) for reliability and performance

7. **AI-Enhanced Analysis** - Incorporate AI capabilities for legislative text analysis, semantic search, and automated code quality management

8. **Research & Analytics** - Support policy research through reproducible analysis pipelines for bill text, social media engagement, and member activity
