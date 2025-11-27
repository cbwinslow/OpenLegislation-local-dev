"""
MCP Server Integration for CrewAI
==================================

Integration with Anthropic's Model Context Protocol (MCP) servers
to provide enhanced tool capabilities for CrewAI agents.
"""

import os
import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from crewai import Agent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class MCPTool:
    """Represents an MCP tool"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str

@dataclass
class MCPServer:
    """Represents an MCP server"""
    name: str
    command: str
    args: List[str]
    env: Dict[str, str]
    tools: List[MCPTool]

class MCPClient:
    """Client for interacting with MCP servers"""

    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}
        self.available_tools: Dict[str, MCPTool] = {}

    def register_server(self, server: MCPServer):
        """Register an MCP server"""
        self.servers[server.name] = server
        for tool in server.tools:
            self.available_tools[tool.name] = tool

    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """Get a tool by name"""
        return self.available_tools.get(tool_name)

    def list_tools(self) -> List[MCPTool]:
        """List all available tools"""
        return list(self.available_tools.values())

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call an MCP tool"""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool {tool_name} not found")

        server = self.servers.get(tool.server_name)
        if not server:
            raise ValueError(f"Server {tool.server_name} not found")

        # In a real implementation, this would use the MCP protocol
        # For now, we'll simulate the tool call
        return await self._simulate_tool_call(tool, arguments)

    async def _simulate_tool_call(self, tool: MCPTool, arguments: Dict[str, Any]) -> Any:
        """Simulate a tool call for development purposes"""
        # This is a placeholder - real implementation would use MCP protocol
        print(f"Calling MCP tool: {tool.name} with args: {arguments}")

        # Simulate different tool responses based on tool name
        if "search" in tool.name.lower():
            return {
                "results": [
                    {"title": "Sample Result 1", "url": "https://example.com/1", "snippet": "Sample content..."},
                    {"title": "Sample Result 2", "url": "https://example.com/2", "snippet": "More content..."}
                ]
            }
        elif "read" in tool.name.lower():
            return {"content": "Sample file content from MCP tool"}
        elif "write" in tool.name.lower():
            return {"success": True, "message": "Content written successfully"}
        else:
            return {"result": "Generic MCP tool response"}

class MCPIntegration:
    """Integration layer for MCP servers in CrewAI"""

    def __init__(self):
        self.client = MCPClient()
        self._setup_servers()

    def _setup_servers(self):
        """Set up MCP servers"""
        # GitHub MCP Server
        github_server = MCPServer(
            name="github",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={
                "GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_TOKEN", "")
            },
            tools=[
                MCPTool(
                    name="github_search_code",
                    description="Search for code in GitHub repositories",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "repo": {"type": "string"}
                        },
                        "required": ["query"]
                    },
                    server_name="github"
                ),
                MCPTool(
                    name="github_read_file",
                    description="Read a file from a GitHub repository",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "repo": {"type": "string"},
                            "path": {"type": "string"},
                            "ref": {"type": "string"}
                        },
                        "required": ["repo", "path"]
                    },
                    server_name="github"
                )
            ]
        )

        # File System MCP Server
        filesystem_server = MCPServer(
            name="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            env={},
            tools=[
                MCPTool(
                    name="fs_read_file",
                    description="Read a file from the filesystem",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"}
                        },
                        "required": ["path"]
                    },
                    server_name="filesystem"
                ),
                MCPTool(
                    name="fs_list_dir",
                    description="List contents of a directory",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"}
                        },
                        "required": ["path"]
                    },
                    server_name="filesystem"
                ),
                MCPTool(
                    name="fs_search_files",
                    description="Search for files using glob patterns",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "pattern": {"type": "string"},
                            "path": {"type": "string"}
                        },
                        "required": ["pattern"]
                    },
                    server_name="filesystem"
                )
            ]
        )

        # Brave Search MCP Server
        brave_search_server = MCPServer(
            name="brave_search",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-brave-search"],
            env={
                "BRAVE_API_KEY": os.getenv("BRAVE_API_KEY", "")
            },
            tools=[
                MCPTool(
                    name="brave_web_search",
                    description="Search the web using Brave Search",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "count": {"type": "number"}
                        },
                        "required": ["query"]
                    },
                    server_name="brave_search"
                )
            ]
        )

        # Legislative Data MCP Servers

            command="python",
            args=["-m", "mcp_servers.cli", "congress", "list"],
            env={"CONGRESS_API_KEY": os.getenv("CONGRESS_API_KEY", "")},
            tools=[
                MCPTool(
                    name="congress_list_endpoints",

                    input_schema={"type": "object", "properties": {}},
                    server_name="congress_list",
                ),
            ],
        )

        congress_ingest_server = MCPServer(
            name="congress_ingest",
            command="python",
            args=["-m", "mcp_servers.cli", "congress", "ingest"],
            env={"CONGRESS_API_KEY": os.getenv("CONGRESS_API_KEY", "")},
            tools=[
                MCPTool(
                    name="congress_bulk_ingest",

                    input_schema={
                        "type": "object",
                        "properties": {
                            "start_offsets": {"type": "string", "description": "JSON map of offsets per endpoint"},
                            "page_sizes": {"type": "string", "description": "JSON map of page sizes per endpoint"},
                        },
                    },
                    server_name="congress_ingest",
                ),
            ],
        )

        # GovInfo servers
        govinfo_list_server = MCPServer(
            name="govinfo_list",
            command="python",
            args=["-m", "mcp_servers.cli", "govinfo", "list"],
            env={"GOVINFO_API_KEY": os.getenv("GOVINFO_API_KEY", "")},
            tools=[
                MCPTool(
                    name="govinfo_list_endpoints",

                    input_schema={"type": "object", "properties": {}},
                    server_name="govinfo_list",
                ),
            ],
        )

        govinfo_ingest_server = MCPServer(
            name="govinfo_ingest",
            command="python",
            args=["-m", "mcp_servers.cli", "govinfo", "ingest"],
            env={"GOVINFO_API_KEY": os.getenv("GOVINFO_API_KEY", "")},
            tools=[
                MCPTool(
                    name="govinfo_bulk_ingest",

                    input_schema={
                        "type": "object",
                        "properties": {
                            "start_offsets": {"type": "string", "description": "JSON map of offsets per endpoint"},
                            "page_sizes": {"type": "string", "description": "JSON map of page sizes per endpoint"},
                        },
                    },
                    server_name="govinfo_ingest",
                ),
            ],
        )

        # OpenStates servers
        openstates_list_server = MCPServer(
            name="openstates_list",
            command="python",
            args=["-m", "mcp_servers.cli", "openstates", "list"],
            env={"OPENSTATES_API_KEY": os.getenv("OPENSTATES_API_KEY", "")},
            tools=[
                MCPTool(
                    name="openstates_list_endpoints",

                    input_schema={"type": "object", "properties": {}},
                    server_name="openstates_list",
                ),
            ],
        )

        openstates_ingest_server = MCPServer(
            name="openstates_ingest",
            command="python",
            args=["-m", "mcp_servers.cli", "openstates", "ingest"],
            env={"OPENSTATES_API_KEY": os.getenv("OPENSTATES_API_KEY", "")},
            tools=[
                MCPTool(
                    name="openstates_bulk_ingest",

                    input_schema={
                        "type": "object",
                        "properties": {
                            "start_pages": {"type": "string", "description": "JSON map of starting pages per endpoint"},
                            "page_sizes": {"type": "string", "description": "JSON map of page sizes per endpoint"},
                        },
                    },
                    server_name="openstates_ingest",
                ),
            ],
        )

        openstates_scrape_server = MCPServer(
            name="openstates_scrape",
            command="python",
            args=["-m", "mcp_servers.cli", "openstates", "scrape"],
            env={"OPENSTATES_API_KEY": os.getenv("OPENSTATES_API_KEY", "")},
            tools=[
                MCPTool(
                    name="openstates_run_scrapers",

                    input_schema={
                        "type": "object",
                        "properties": {
                            "states": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "State abbreviations to scrape",
                            }
                        },
                    },
                    server_name="openstates_scrape",
                ),
            ],
        )

        # SQLite MCP Server
        sqlite_server = MCPServer(
            name="sqlite",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-sqlite", "--db-path", "/tmp/test.db"],
            env={},
            tools=[
                MCPTool(
                    name="sqlite_query",
                    description="Execute SQL queries on SQLite database",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"}
                        },
                        "required": ["query"]
                    },
                    server_name="sqlite"
                )
            ]
        )

        # Register all servers
        self.client.register_server(github_server)
        self.client.register_server(filesystem_server)
        self.client.register_server(brave_search_server)

        self.client.register_server(openstates_ingest_server)
        self.client.register_server(openstates_scrape_server)
        self.client.register_server(sqlite_server)

    def get_mcp_tools_for_agent(self, agent_role: str) -> List[MCPTool]:
        """Get relevant MCP tools for a specific agent role"""
        all_tools = self.client.list_tools()

        # Map agent roles to relevant tools
        role_tool_mapping = {
            "Database Architect": ["sqlite_query", "fs_read_file", "fs_list_dir"],
            "Performance Tuning Specialist": ["sqlite_query", "fs_search_files"],
            "Data Engineer": ["sqlite_query", "fs_read_file", "fs_list_dir", "fs_search_files"],
            "Database Security Specialist": ["sqlite_query", "fs_read_file"],
            "Backup and Recovery Specialist": ["fs_list_dir", "fs_search_files"],

            "Legislative Analyst": ["brave_web_search", "github_search_code", "fs_read_file", "congress_list_endpoints", "govinfo_list_endpoints", "openstates_list_endpoints"],
            "Policy Impact Assessor": ["brave_web_search", "github_read_file", "congress_bulk_ingest", "govinfo_bulk_ingest", "openstates_bulk_ingest"],
            "Constitutional Law Specialist": ["brave_web_search", "github_search_code", "congress_list_endpoints"],
            "Regulatory Compliance Specialist": ["brave_web_search", "fs_read_file", "govinfo_list_endpoints"],

            "Political Strategist": ["brave_web_search", "github_search_code"],
            "Public Opinion Analyst": ["brave_web_search", "github_read_file"],
            "Stakeholder Engagement Specialist": ["brave_web_search", "fs_read_file"],
            "Digital Campaign Manager": ["brave_web_search", "github_search_code"],
            "Crisis Communications Specialist": ["brave_web_search", "fs_read_file"],

            "Senior Software Architect": ["github_search_code", "github_read_file", "fs_read_file", "fs_list_dir"],
            "Backend Developer": ["github_search_code", "github_read_file", "fs_read_file"],
            "Frontend Developer": ["github_search_code", "github_read_file", "fs_read_file"],
            "QA Engineer": ["github_search_code", "fs_read_file", "fs_list_dir"],
            "DevOps Engineer": ["github_search_code", "fs_read_file", "fs_list_dir"],
            "Security Analyst": ["github_search_code", "github_read_file", "fs_read_file"],
            "Technical Writer": ["github_read_file", "fs_read_file"],
            "Project Manager": ["github_search_code", "fs_list_dir"]
        }

        relevant_tool_names = role_tool_mapping.get(agent_role, [])
        return [tool for tool in all_tools if tool.name in relevant_tool_names]

    def create_mcp_enhanced_agent(self, base_agent: Agent, agent_role: str) -> Agent:
        """Create an MCP-enhanced version of an existing agent"""
        mcp_tools = self.get_mcp_tools_for_agent(agent_role)

        # Convert MCP tools to CrewAI tool format
        crewai_tools = []
        for mcp_tool in mcp_tools:
            # Create a CrewAI-compatible tool wrapper
            tool_wrapper = self._create_crewai_tool_wrapper(mcp_tool)
            crewai_tools.append(tool_wrapper)

        # Add MCP tools to the agent
        enhanced_tools = (base_agent.tools or []) + crewai_tools

        # Create enhanced agent with MCP tools
        enhanced_agent = Agent(
            role=base_agent.role,
            goal=base_agent.goal,
            backstory=base_agent.backstory + "\n\nMCP Tool Integration: This agent has access to enhanced external tools via Model Context Protocol servers, including web search, file system operations, GitHub integration, and database access.",
            llm=base_agent.llm,
            tools=enhanced_tools,
            allow_delegation=base_agent.allow_delegation,
            verbose=base_agent.verbose,
            memory=base_agent.memory,
            max_iter=base_agent.max_iter,
            max_execution_time=base_agent.max_execution_time,
        )

        return enhanced_agent

    def _create_crewai_tool_wrapper(self, mcp_tool: MCPTool):
        """Create a CrewAI-compatible tool wrapper for an MCP tool"""
        from crewai_tools import BaseTool

        class MCPToolWrapper(BaseTool):
            name: str = mcp_tool.name
            description: str = mcp_tool.description

            def __init__(self, mcp_client: MCPClient, mcp_tool: MCPTool):
                super().__init__()
                self.mcp_client = mcp_client
                self.mcp_tool = mcp_tool

            def _run(self, **kwargs) -> str:
                """Run the MCP tool synchronously"""
                try:
                    # Run the async tool call in a new event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(
                        self.mcp_client.call_tool(self.mcp_tool.name, kwargs)
                    )
                    loop.close()
                    return json.dumps(result, indent=2)
                except Exception as e:
                    return f"Error calling MCP tool {self.mcp_tool.name}: {str(e)}"

        return MCPToolWrapper(self.client, mcp_tool)

# Global MCP integration instance
mcp_integration = MCPIntegration()

def enhance_crew_with_mcp(crew, agent_roles: List[str]):
    """Enhance a crew with MCP tools for specified agent roles"""
    enhanced_agents = []

    for i, agent in enumerate(crew.agents):
        if i < len(agent_roles):
            agent_role = agent_roles[i]
            enhanced_agent = mcp_integration.create_mcp_enhanced_agent(agent, agent_role)
            enhanced_agents.append(enhanced_agent)
        else:
            enhanced_agents.append(agent)

    # Create enhanced crew
    enhanced_crew = Crew(
        agents=enhanced_agents,
        tasks=crew.tasks,
        process=crew.process,
        verbose=crew.verbose
    )

    return enhanced_crew

# Example usage functions
def create_mcp_enhanced_database_crew(database_info: str):
    """Create an MCP-enhanced database administration crew"""
    from .database_admin import DatabaseAdminCrew

    crew = DatabaseAdminCrew.create_database_optimization_crew(database_info)
    agent_roles = ["Database Architect", "Performance Tuning Specialist", "Data Engineer"]

    return enhance_crew_with_mcp(crew, agent_roles)

def create_mcp_enhanced_legislative_crew(bill_info: str):
    """Create an MCP-enhanced legislative analysis crew"""
    from .legislative_analysis import LegislativeAnalysisCrew

    crew = LegislativeAnalysisCrew.create_bill_analysis_crew(bill_info)
    agent_roles = ["Legislative Analyst", "Policy Impact Assessor", "Constitutional Law Specialist", "Regulatory Compliance Specialist"]

    return enhance_crew_with_mcp(crew, agent_roles)

def create_mcp_enhanced_political_crew(campaign_info: str):
    """Create an MCP-enhanced political consultant crew"""
    from .political_consultant import PoliticalConsultantCrew

    crew = PoliticalConsultantCrew.create_campaign_strategy_crew(campaign_info)
    agent_roles = ["Political Strategist", "Public Opinion Analyst", "Stakeholder Engagement Specialist", "Digital Campaign Manager"]

    return enhance_crew_with_mcp(crew, agent_roles)

def create_mcp_enhanced_development_crew(project_info: str):
    """Create an MCP-enhanced software development crew"""
    from ..crewai import create_development_crew

    crew = create_development_crew(project_info)
    agent_roles = ["Senior Software Architect", "Backend Developer", "Frontend Developer", "QA Engineer", "DevOps Engineer", "Security Analyst", "Technical Writer", "Project Manager"]

    return enhance_crew_with_mcp(crew, agent_roles)