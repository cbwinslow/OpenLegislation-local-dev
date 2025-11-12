# 🤖 CrewAI Multi-Domain AI Ecosystem

A comprehensive AI-powered orchestration system using CrewAI framework, featuring specialized crews for software development, legislative analysis, political consulting, and database administration - all enhanced with Anthropic's Model Context Protocol (MCP) servers.

## Overview

This advanced CrewAI ecosystem creates multiple teams of specialized AI agents that collaborate through structured workflows to deliver high-quality outcomes across diverse domains. Each crew features domain-expert agents with sophisticated toolsets and MCP server integration for enhanced external tool access.

## 🏗️ Architecture

### Core Components

- **Agents**: Specialized AI personalities with deep domain expertise
- **Crews**: Orchestrated teams of agents working on domain-specific tasks
- **Tasks**: Structured work items with clear objectives and deliverables
- **MCP Integration**: Model Context Protocol servers for external tool access
- **Multi-Domain Support**: Software development, legislative analysis, political strategy, database administration

### Agent Specializations

#### Software Development Crew
1. **Senior Software Architect** - System design, architecture decisions, technical leadership
2. **Backend Developer** - Java/Spring development, API implementation, database operations
3. **Frontend Developer** - React development, UI/UX, modern web technologies
4. **QA Engineer** - Testing strategy, automation, quality assurance
5. **DevOps Engineer** - Infrastructure, deployment, CI/CD pipelines
6. **Security Analyst** - Security reviews, vulnerability assessment, threat modeling
7. **Technical Writer** - Documentation, API docs, knowledge base management
8. **Project Manager** - Coordination, planning, progress tracking, stakeholder management

#### Legislative Analysis Crew
1. **Legislative Analyst** - Bill analysis, legislative process expertise
2. **Policy Impact Assessor** - Policy analysis, stakeholder impact evaluation
3. **Constitutional Law Specialist** - Constitutional analysis, legal compliance
4. **Regulatory Compliance Specialist** - Regulatory requirements, compliance frameworks

#### Political Consultant Crew
1. **Political Strategist** - Campaign strategy, political messaging, voter analysis
2. **Public Opinion Analyst** - Public sentiment analysis, polling data interpretation
3. **Stakeholder Engagement Specialist** - Stakeholder mapping, relationship management
4. **Digital Campaign Manager** - Digital strategy, social media, online engagement
5. **Crisis Communications Specialist** - Crisis management, reputation protection

#### Database Administration Crew
1. **Database Architect** - Schema design, architecture planning, data modeling
2. **Performance Tuning Specialist** - Query optimization, bottleneck analysis, monitoring
3. **Data Engineer** - ETL pipelines, data integration, transformation processes
4. **Database Security Specialist** - Security implementation, compliance, audit logging
5. **Backup and Recovery Specialist** - Backup strategies, disaster recovery, business continuity

## 🚀 Quick Start

### Prerequisites

1. **Python 3.10+** installed
2. **API Keys** for OpenAI and/or Anthropic
3. **Git** and repository access
4. **Optional**: MCP server API keys (GitHub, Brave Search, etc.)

### Installation

1. **Run the setup script:**
   ```bash
   chmod +x setup_crewai.sh
   ./setup_crewai.sh
   ```

   This will:
   - Create a Python virtual environment
   - Install all dependencies
   - Set up MCP server integrations
   - Create configuration templates

2. **Configure environment:**
   ```bash
   cd crewai
   # Edit .env with your API keys
   nano .env
   ```

3. **Run a crew:**
   ```bash
   source crewai_env/bin/activate
   python crewai/run_crew.py development --project "Add new API endpoints"
   ```

## 📋 Available Crews

### 1. Software Development Crew
**Purpose:** Comprehensive software development and engineering
**Agents:** 8 specialized development agents
**MCP Tools:** GitHub integration, file system operations, code search

```bash
# Basic usage
python crewai/run_crew.py development --project "Implement user authentication"

# With MCP enhancement
python crewai/run_crew.py development --project "Add API endpoints" --mcp

# Save results to file
python crewai/run_crew.py development --project "Database optimization" --output results.json
```

### 2. Legislative Analysis Crew
**Purpose:** Bill analysis, policy impact assessment, regulatory compliance
**Agents:** 4 legislative and legal specialists
**MCP Tools:** Web search, document analysis, legal research

```bash
# Analyze specific legislation
python crewai/run_crew.py legislative --bill "Healthcare reform bill analysis"

# Constitutional impact assessment
python crewai/run_crew.py legislative --bill "Privacy legislation review" --mcp
```

### 3. Political Consultant Crew
**Purpose:** Political strategy, campaign management, stakeholder engagement
**Agents:** 5 political strategy and communications specialists
**MCP Tools:** Social media analysis, public opinion research, stakeholder mapping

```bash
# Campaign strategy development
python crewai/run_crew.py political --campaign "Healthcare advocacy campaign"

# Crisis management planning
python crewai/run_crew.py political --campaign "Crisis communications strategy" --mcp
```

### 4. Database Administration Crew
**Purpose:** Database optimization, security, backup/recovery
**Agents:** 5 database administration specialists
**MCP Tools:** Database query tools, file system monitoring, backup validation

```bash
# Performance optimization
python crewai/run_crew.py database --database "PostgreSQL performance tuning"

# Security audit and hardening
python crewai/run_crew.py database --database "Security assessment and compliance" --mcp
```

## 🔌 MCP Server Integration

### Available MCP Servers

1. **GitHub MCP Server**
   - Code search and analysis
   - Repository file access
   - Pull request management

2. **File System MCP Server**
   - Local file operations
   - Directory structure analysis
   - File content search

3. **Brave Search MCP Server**
   - Web search capabilities
   - Research and information gathering
   - Current events analysis

4. **SQLite MCP Server**
   - Database query execution
   - Schema analysis
   - Data validation

### MCP-Enhanced Agents

When using `--mcp` flag, agents gain access to:
- **External data sources** for research and analysis
- **Enhanced file operations** for comprehensive code analysis
- **Web search capabilities** for current information
- **Database access** for data-driven insights

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT models | No* |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude models | No* |
| `GITHUB_TOKEN` | GitHub token for repository analysis | No |
| `BRAVE_API_KEY` | Brave Search API key | No |
| `CREWAI_VERBOSE` | Enable verbose logging | No |

*At least one AI API key is required

### Advanced Configuration

Create custom configuration files:
```json
{
  "crew_type": "development",
  "project_info": "Custom project description",
  "focus_areas": ["security", "performance"],
  "technologies": ["Java", "PostgreSQL"],
  "mcp_enabled": true
}
```

Use with:
```bash
python crewai/run_crew.py development --config custom_config.json
```

## 🛠️ Tools and Capabilities

### Core CrewAI Tools
- **Code Analysis**: AST parsing, complexity analysis, pattern detection
- **File Operations**: Read, write, search, modify files
- **Git Integration**: Commit analysis, diff review, branch management
- **Documentation**: Automated doc generation, API documentation

### MCP-Enhanced Tools
- **Web Research**: Real-time information gathering
- **External APIs**: Integration with third-party services
- **Advanced Search**: Semantic code and document search
- **Database Operations**: Query execution and analysis

### Domain-Specific Tools
- **Legal Research**: Case law analysis, regulatory databases
- **Political Analysis**: Sentiment analysis, stakeholder mapping
- **Database Tools**: Performance monitoring, query optimization
- **Security Tools**: Vulnerability scanning, compliance checking

## 📊 Monitoring and Analytics

### Execution Tracking
- **Performance Metrics**: Execution time, token usage, success rates
- **Quality Metrics**: Code quality improvements, analysis depth
- **Cost Analysis**: API usage optimization, budget tracking

### Logging and Debugging
```bash
# Enable verbose logging
python crewai/run_crew.py development --verbose

# Save execution results
python crewai/run_crew.py legislative --bill "Analysis" --output results.json
```

## 🔒 Security and Best Practices

### API Key Security
- Environment variable storage only
- Regular key rotation
- Usage monitoring and alerts
- Least-privilege access principles

### Data Protection
- No sensitive data sent to external APIs
- Local processing preference
- Data anonymization for analysis
- Compliance with privacy regulations

### Code Security
- AI-generated code security review
- Automated vulnerability scanning
- Access controls on sensitive operations
- Audit trails for all AI activities

## 🚦 Troubleshooting

### Common Issues

1. **API Key Configuration**
   ```
   Error: No valid API keys found
   Solution: Check .env file and API key validity
   ```

2. **MCP Server Connection**
   ```
   Error: MCP server connection failed
   Solution: Verify MCP server credentials and network connectivity
   ```

3. **Memory/Resource Limits**
   ```
   Error: Maximum execution time exceeded
   Solution: Break complex tasks into smaller components
   ```

4. **Import Errors**
   ```
   ImportError: Module not found
   Solution: Activate virtual environment and verify installation
   ```

### Performance Optimization

- **Token Efficiency**: Use appropriate model sizes, implement context management
- **Parallel Processing**: Enable parallel task execution where possible
- **Caching**: Cache frequent queries and results
- **Batch Operations**: Group similar operations for efficiency

## 📈 Advanced Features

### Custom Crew Creation
```python
from crewai import Crew, Agent, Task
from mcp_integration import enhance_crew_with_mcp

# Create custom crew
agents = [custom_agent1, custom_agent2]
tasks = [custom_task1, custom_task2]
crew = Crew(agents=agents, tasks=tasks, process="sequential")

# Enhance with MCP
enhanced_crew = enhance_crew_with_mcp(crew, ["Custom Role 1", "Custom Role 2"])
```

### Multi-Crew Orchestration
Run multiple crews in sequence:
```bash
# Development followed by testing
python crewai/run_crew.py development --project "Feature implementation"
python crewai/run_crew.py development --project "Testing and validation"
```

### Integration with CI/CD
- **GitHub Actions**: Automated code review on PRs
- **Jenkins/GitLab**: Pipeline integration for automated tasks
- **Quality Gates**: AI-powered code quality assessment

## 🤝 Contributing

### Adding New Agents
1. Create agent file in `agents/` directory
2. Implement agent factory function
3. Add to crew configurations
4. Update MCP tool mappings
5. Test integration

### Creating New Crews
1. Define crew tasks and workflow
2. Select appropriate agents
3. Configure MCP tool integration
4. Add to CLI interface
5. Update documentation

### Extending MCP Integration
1. Add new MCP server configurations
2. Implement tool wrappers
3. Update agent tool mappings
4. Test external integrations

## 📚 Examples and Use Cases

### Software Development
```bash
# Full-stack feature implementation
python crewai/run_crew.py development --project "Implement OAuth2 authentication with JWT tokens" --mcp

# Security-focused development
python crewai/run_crew.py development --project "Security hardening and vulnerability remediation"
```

### Legislative Analysis
```bash
# Comprehensive bill analysis
python crewai/run_crew.py legislative --bill "Analyze impact of healthcare reform legislation" --mcp

# Regulatory compliance review
python crewai/run_crew.py legislative --bill "GDPR compliance assessment for data processing"
```

### Political Strategy
```bash
# Campaign development
python crewai/run_crew.py political --campaign "Develop advocacy campaign for environmental policy" --mcp

# Crisis management
python crewai/run_crew.py political --campaign "Crisis communications strategy for policy controversy"
```

### Database Administration
```bash
# Performance optimization
python crewai/run_crew.py database --database "PostgreSQL query optimization and indexing strategy" --mcp

# Security and compliance
python crewai/run_crew.py database --database "Implement security controls and audit logging"
```

## 📞 Support and Resources

### Documentation
- [CrewAI Official Documentation](https://docs.crewai.com/)
- [Anthropic MCP Documentation](https://modelcontextprotocol.io/)
- [OpenLegislation Project Docs](../docs/)

### Community
- [CrewAI Discord](https://discord.gg/crewai)
- [Anthropic Developer Community](https://console.anthropic.com/)
- [OpenLegislation Issues](../../issues)

---

*This CrewAI ecosystem represents the future of AI-powered multi-domain orchestration, combining specialized expertise with advanced tool integration for comprehensive problem-solving across technical, legal, political, and administrative domains.*