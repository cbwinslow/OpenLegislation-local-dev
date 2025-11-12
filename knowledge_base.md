# OpenLegislation Knowledge Base

## Essential Project Information

### Project Identity
- **Name**: OpenLegislation
- **Purpose**: Comprehensive legislative data platform for NY State, federal, and all 50 states
- **License**: Dual BSD/GPL
- **Origin**: New York State Senate project, evolved to national platform
- **API Endpoint**: legislation.nysenate.gov (JSON API docs available)

### Core Technologies
- **Java Version**: 21 (updated from 17)
- **Framework**: Spring 5
- **Database**: PostgreSQL with Flyway migrations
- **Search**: Elasticsearch 8.15.2
- **Frontend**: Next.js 15, React 19, TypeScript
- **Build Tool**: Maven
- **Server**: Tomcat 9
- **AI Integration**: CrewAI agents, OpenRouter API

### Data Sources & Processing
- **Primary Sources**:
  - NY State LBDC (real-time)
  - Congress.gov (federal legislation)
  - GovInfo.gov (bulk federal data)
  - OpenStates (50 state data)
- **File Formats**: XML (SOBI, GovInfo), JSON
- **Processing Pipeline**: Ingest → Parse → Validate → Store → Index → API
- **Update Frequency**: <15 minute latency for real-time sources

### Key Data Entities
- **Bill**: Core legislative document with amendments, actions, sponsors
- **BillAmendment**: Version-specific bill content
- **BillAction**: Legislative actions and status changes
- **SessionMember**: Legislator information per session
- **Committee**: Committee structure and membership
- **BillVote**: Roll call voting records

### Development Workflow
- **Build Command**: `mvn compile flyway:migrate`
- **Run Locally**: Import as Maven project in IntelliJ, run Tomcat
- **Trigger Processing**: POST to `/api/3/admin/process/run` with admin credentials
- **Test Execution**: `mvn test` (unit tests), integration tests with Failsafe
- **Database Setup**: Flyway migrations in `src/main/resources/sql/migrations`

### File Structure Conventions
- **XML Filenames**: Regex pattern for date/time/type parsing
- **Source Types**: Enum routing files to appropriate processors
- **Encoding**: CP1252 for `_SENAGEN_` files
- **Archiving**: Use `SourceFileFsDao.archiveSourceFile` with environment archive dir

### Federal Integration Patterns
- **New SourceType**: Extend enum for federal sources (e.g., FEDERAL_BILL)
- **DAO Implementation**: Create FsFederalBillDao for `env.staging/federal-<collection>/`
- **Processor Creation**: Add processors in `processors/federal/<type>/`
- **Model Extension**: Extend Bill/LawDocument models, add congress_number fields
- **API Endpoints**: `/api/3/federal/<type>` for federal data
- **ID Mapping**: Translate govinfo IDs to BaseBillId format

### XML Processing
- **Libraries**: Jackson-dataformat-xml, JAXB
- **Schema Validation**: USLM XSD schemas in `src/main/resources/schema/uslm/`
- **Mapping**: Follow patterns in `processors/*/xml/*`
- **Streaming**: Use for large files to prevent memory issues

### AI Agent Ecosystem
- **CrewAI Integration**: Python-based agents in `crewai/` directory
- **Specialized Agents**:
  - Kilo Code: Development and code generation
  - Qwen: Data processing specialist
  - Claude: Documentation expert
  - Grok: Monitoring and alerts
  - Nova: Research and content generation
  - Intelli: Analytics engine
  - Sentinel: Security monitoring
  - Atlas: Data mapping specialist

### Infrastructure & Deployment
- **Containerization**: Docker with Docker Compose
- **Configuration Management**: Ansible playbooks
- **IaC**: Terraform/Pulumi configurations
- **CI/CD**: GitHub Actions with automated PR management
- **Monitoring**: Comprehensive logging and performance tracking
- **Security**: OWASP practices, JWT authentication

### Performance Requirements
- **API Response Time**: <200ms (95th percentile)
- **System Availability**: >99.9% uptime
- **Data Freshness**: <15 minute update latency
- **Search Accuracy**: >90% relevance score
- **Concurrent Users**: 10,000+ supported

### Quality Standards
- **Data Accuracy**: >99% across all sources
- **Completeness**: >98% field completeness
- **Consistency**: Unified data model across jurisdictions
- **Test Coverage**: Target 90%+ code coverage

### Common Patterns
- **Error Handling**: Comprehensive logging with Log4j2
- **Caching**: Ehcache for performance optimization
- **Connection Pooling**: C3P0 for database connections
- **Async Processing**: Queue-based processing for heavy operations
- **Validation**: Bean validation with custom validators

### Troubleshooting
- **XML Validation**: Use USLM XSD for federal documents
- **Encoding Issues**: Check CP1252 encoding for legacy files
- **Memory Issues**: Use streaming parsers for large XML files
- **Database Connections**: Monitor connection pool usage
- **Search Issues**: Check Elasticsearch cluster health and mappings

### Development Best Practices
- **Code Style**: Follow existing patterns in processors and models
- **Testing**: Write unit tests for new processors, integration tests for data flow
- **Documentation**: Update docs/backend/index.md for new features
- **Migrations**: Use Flyway for database schema changes
- **API Design**: Follow REST conventions, document with OpenAPI

### Key Configuration Files
- `pom.xml`: Maven dependencies and build configuration
- `src/main/resources/app.properties`: Application settings
- `src/main/resources/flyway.conf`: Database migration config
- `src/main/resources/log4j2.xml`: Logging configuration
- `.env`: Environment variables (use .env.example as template)

### Important Directories
- `src/main/java/gov/nysenate/openleg/`: Main Java packages
- `src/main/resources/`: Configuration and static resources
- `src/test/`: Test files and fixtures
- `staging/`: Data processing staging area
- `target/`: Build output directory
- `docs/`: All documentation
- `tools/`: Python ingestion scripts
- `frontend/`: Web interface code
- `infra/`: Infrastructure configurations
- `ansible/`: Deployment automation

### Getting Help
- **Documentation**: Comprehensive docs in `docs/` directory
- **API Docs**: Available at legislation.nysenate.gov static docs
- **Community**: GitHub issues for bugs and feature requests
- **Development**: See `README_DEV.md` for local setup
- **Federal Integration**: Reference `docs/govinfo-integration.md` and mapping docs

This knowledge base contains the essential information needed to understand and contribute to the OpenLegislation project. For detailed implementation guides, refer to the `docs/` directory and specific README files in subdirectories.</content>
<parameter name="filePath">/home/cbwinslow/OpenLegislation-local-dev/knowledge_base.md