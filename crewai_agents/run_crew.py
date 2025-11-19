#!/usr/bin/env python3
"""
CrewAI Runner Script
===================

Command-line interface for running various CrewAI crews on the OpenLegislation project.
Supports software development, legislative analysis, political consulting, and database administration.
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Add the crewai directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv()

def load_crew_config(crew_type: str, config_file: Optional[str] = None) -> Dict[str, Any]:
    """Load crew configuration from file or use defaults"""
    if config_file and Path(config_file).exists():
        with open(config_file, 'r') as f:
            return json.load(f)

    # Default configurations
    configs = {
        "development": {
            "project_info": "OpenLegislation software development and enhancement",
            "focus_areas": ["backend", "frontend", "database", "security"],
            "technologies": ["Java", "Spring", "PostgreSQL", "Elasticsearch", "React"]
        },
        "legislative": {
            "bill_info": "Analysis of recent legislative bills and their impact on government operations",
            "analysis_scope": ["policy_impact", "constitutional", "regulatory", "implementation"],
            "data_sources": ["govinfo", "congress.gov", "state_legislation"]
        },
        "political": {
            "campaign_info": "Political strategy development for legislative advocacy and public policy campaigns",
            "strategy_focus": ["stakeholder_engagement", "public_opinion", "digital_campaigning", "crisis_management"],
            "target_audience": ["legislators", "public", "stakeholders", "media"]
        },
        "database": {
            "database_info": "OpenLegislation PostgreSQL database optimization and administration",
            "optimization_focus": ["performance", "security", "backup_recovery", "migration"],
            "database_type": "PostgreSQL",
            "schema_complexity": "high"
        }
    }

    return configs.get(crew_type, {})

def run_development_crew(project_info: str, use_mcp: bool = False) -> None:
    """Run the software development crew"""
    try:
        from crewai import create_development_crew
        from mcp_integration import create_mcp_enhanced_development_crew

        print("🏗️  Initializing Software Development Crew...")
        print(f"Project: {project_info}")

        if use_mcp:
            print("🔌 Using MCP-enhanced agents...")
            crew = create_mcp_enhanced_development_crew(project_info)
        else:
            crew = create_development_crew(project_info)

        print("🚀 Starting development tasks...")
        result = crew.kickoff()

        print("✅ Development crew completed!")
        print(f"Results: {result}")

    except Exception as e:
        print(f"❌ Error running development crew: {e}")
        sys.exit(1)

def run_legislative_crew(bill_info: str, use_mcp: bool = False) -> None:
    """Run the legislative analysis crew"""
    try:
        from specialized_crews.legislative_analysis import LegislativeAnalysisCrew
        from mcp_integration import create_mcp_enhanced_legislative_crew

        print("📜 Initializing Legislative Analysis Crew...")
        print(f"Analysis Focus: {bill_info}")

        if use_mcp:
            print("🔌 Using MCP-enhanced agents...")
            crew = create_mcp_enhanced_legislative_crew(bill_info)
        else:
            crew = LegislativeAnalysisCrew.create_bill_analysis_crew(bill_info)

        print("🚀 Starting legislative analysis...")
        result = crew.kickoff()

        print("✅ Legislative analysis completed!")
        print(f"Results: {result}")

    except Exception as e:
        print(f"❌ Error running legislative crew: {e}")
        sys.exit(1)

def run_political_crew(campaign_info: str, use_mcp: bool = False) -> None:
    """Run the political consultant crew"""
    try:
        from specialized_crews.political_consultant import PoliticalConsultantCrew
        from mcp_integration import create_mcp_enhanced_political_crew

        print("🏛️  Initializing Political Consultant Crew...")
        print(f"Campaign Focus: {campaign_info}")

        if use_mcp:
            print("🔌 Using MCP-enhanced agents...")
            crew = create_mcp_enhanced_political_crew(campaign_info)
        else:
            crew = PoliticalConsultantCrew.create_campaign_strategy_crew(campaign_info)

        print("🚀 Starting political strategy development...")
        result = crew.kickoff()

        print("✅ Political strategy completed!")
        print(f"Results: {result}")

    except Exception as e:
        print(f"❌ Error running political crew: {e}")
        sys.exit(1)

def run_database_crew(database_info: str, use_mcp: bool = False) -> None:
    """Run the database administration crew"""
    try:
        from specialized_crews.database_admin import DatabaseAdminCrew
        from mcp_integration import create_mcp_enhanced_database_crew

        print("🗄️  Initializing Database Administration Crew...")
        print(f"Database Focus: {database_info}")

        if use_mcp:
            print("🔌 Using MCP-enhanced agents...")
            crew = create_mcp_enhanced_database_crew(database_info)
        else:
            crew = DatabaseAdminCrew.create_database_optimization_crew(database_info)

        print("🚀 Starting database optimization...")
        result = crew.kickoff()

        print("✅ Database optimization completed!")
        print(f"Results: {result}")

    except Exception as e:
        print(f"❌ Error running database crew: {e}")
        sys.exit(1)

def list_available_crews() -> None:
    """List all available crew types and their descriptions"""
    crews = {
        "development": "Software development and engineering crew for coding, testing, and deployment",
        "legislative": "Legislative analysis crew for bill analysis, policy impact assessment, and compliance",
        "political": "Political consultant crew for campaign strategy, stakeholder engagement, and crisis management",
        "database": "Database administration crew for optimization, security, and backup/recovery"
    }

    print("Available CrewAI Crews:")
    print("=" * 50)
    for crew_type, description in crews.items():
        print(f"  {crew_type:<12} - {description}")
    print()
    print("Use --help with a specific crew type for more options")

def setup_environment():
    """Setup environment variables and validate configuration"""
    # Load environment variables
    load_dotenv()

    # Validate required API keys
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: Neither OPENAI_API_KEY nor ANTHROPIC_API_KEY found in environment")
        print("Please set at least one API key in your .env file or environment variables")
        sys.exit(1)

    # Set default model preference
    if os.getenv("OPENAI_API_KEY"):
        os.environ["DEFAULT_LLM"] = "openai"
        print("✅ Using OpenAI GPT models")
    else:
        os.environ["DEFAULT_LLM"] = "anthropic"
        print("✅ Using Anthropic Claude models")

def main():
    parser = argparse.ArgumentParser(
        description="CrewAI Runner for OpenLegislation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_crew.py development --project "Add new API endpoints"
  python run_crew.py legislative --bill "Analyze recent education bill"
  python run_crew.py political --campaign "Healthcare reform advocacy"
  python run_crew.py database --database "PostgreSQL performance optimization"
  python run_crew.py --list  # List all available crews
        """
    )

    parser.add_argument(
        "crew_type",
        nargs="?",
        choices=["development", "legislative", "political", "database"],
        help="Type of crew to run"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available crew types"
    )

    parser.add_argument(
        "--project", "-p",
        help="Project description for development crew"
    )

    parser.add_argument(
        "--bill", "-b",
        help="Bill or legislation to analyze"
    )

    parser.add_argument(
        "--campaign", "-c",
        help="Campaign or political strategy focus"
    )

    parser.add_argument(
        "--database", "-d",
        help="Database to optimize or administer"
    )

    parser.add_argument(
        "--config",
        help="Path to JSON configuration file"
    )

    parser.add_argument(
        "--mcp",
        action="store_true",
        help="Enable MCP (Model Context Protocol) server integration"
    )

    parser.add_argument(
        "--output",
        help="Output file for results (JSON format)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    # Setup environment
    setup_environment()

    # Handle list command
    if args.list or not args.crew_type:
        list_available_crews()
        return

    # Load configuration
    config = load_crew_config(args.crew_type, args.config)

    # Override config with command line arguments
    if args.project:
        config["project_info"] = args.project
    if args.bill:
        config["bill_info"] = args.bill
    if args.campaign:
        config["campaign_info"] = args.campaign
    if args.database:
        config["database_info"] = args.database

    # Set verbose mode
    if args.verbose:
        os.environ["CREWAI_VERBOSE"] = "true"

    print("🤖 CrewAI Multi-Domain Team")
    print("=" * 50)

    # Run the appropriate crew
    try:
        if args.crew_type == "development":
            project_info = config.get("project_info", "OpenLegislation development")
            run_development_crew(project_info, args.mcp)

        elif args.crew_type == "legislative":
            bill_info = config.get("bill_info", "General legislative analysis")
            run_legislative_crew(bill_info, args.mcp)

        elif args.crew_type == "political":
            campaign_info = config.get("campaign_info", "General political strategy")
            run_political_crew(campaign_info, args.mcp)

        elif args.crew_type == "database":
            database_info = config.get("database_info", "OpenLegislation database")
            run_database_crew(database_info, args.mcp)

        print("\n🎉 Crew execution completed successfully!")

        # Save results if output file specified
        if args.output:
            result_data = {
                "crew_type": args.crew_type,
                "config": config,
                "mcp_enabled": args.mcp,
                "timestamp": str(datetime.now())
            }
            with open(args.output, 'w') as f:
                json.dump(result_data, f, indent=2)
            print(f"📄 Results saved to {args.output}")

    except KeyboardInterrupt:
        print("\n⚠️  Crew execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during crew execution: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()