# AI Agents and Roles

## Kilo Code (Primary Development Agent)
**Role**: Software engineering and code implementation
**Capabilities**:
- Java development with Spring Framework
- SQL schema design and migrations
- XML/JSON parsing and data processing
- Database optimization and indexing
- Code refactoring and architecture design

**Responsibilities**:
- Implement new features and processors
- Create data models and DAOs
- Write unit and integration tests
- Optimize database queries and performance
- Maintain code quality and best practices

## Qwen (Analysis and Planning Agent)
**Role**: System analysis and strategic planning
**Capabilities**:
- Codebase analysis and understanding
- Technical documentation creation
- Requirements gathering and specification
- Architecture design and planning
- Data modeling and schema design

**Responsibilities**:
- Analyze existing systems and data flows
- Create technical specifications
- Design integration approaches
- Document APIs and data structures
- Plan migration and deployment strategies

## Claude (Research and Documentation Agent)
**Role**: Research and knowledge synthesis
**Capabilities**:
- External API research and documentation
- Data source analysis and mapping
- Technical writing and documentation
- Best practices research
- Comparative analysis of solutions

**Responsibilities**:
- Research external data sources (congress.gov, govinfo)
- Document API specifications and schemas
- Create mapping documents and guides
- Research industry best practices
- Maintain project documentation

## Grok (Problem Solving and Debugging Agent)
**Role**: Complex problem resolution and debugging
**Capabilities**:
- Root cause analysis of issues
- Performance bottleneck identification
- Data integrity validation
- Error handling and recovery design
- Algorithm optimization

**Responsibilities**:
- Debug complex integration issues
- Optimize data processing pipelines
- Design error recovery mechanisms
- Validate data quality and consistency
- Troubleshoot production issues

## Agent Collaboration Guidelines

### Communication Protocol
- Use clear, technical language in English
- Provide context and reasoning for decisions
- Document assumptions and constraints
- Use markdown for structured information
- Maintain consistent terminology

### Task Handover
- Complete analysis before implementation
- Document current state and decisions
- Provide clear next steps and requirements
- Include relevant code snippets and examples
- Note any blockers or dependencies

## Local Development Notes (Added)

- **Local git identity**: Developers may want to set their git identity for commits; a `.gitconfig.example` has been added at the repo root. Use `git config --global user.name "cbwinslow"` and `git config --global user.email "blaine.winslow@gmail.com"` or copy the example to `~/.gitconfig`.
- **Local env**: A `.env` file is included for convenience (DO NOT commit secrets). It contains `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`, and `JDBC_DATABASE_URL` for local testing against the Zerotier host.
- **Local app properties**: `src/main/resources/app.properties.local` is provided as a template to point the Java app at local DB settings. The application looks for `app.properties.local` when running locally (copy values from `.env` or export env vars before starting).

### Quality Assurance
- Peer review of code changes
- Test coverage for new functionality
- Performance benchmarking
- Documentation updates
- Integration testing validation

### Escalation Paths
- Technical blockers → Architecture review
- Performance issues → Optimization specialist
- Data quality problems → Data governance team
- Security concerns → Security review
