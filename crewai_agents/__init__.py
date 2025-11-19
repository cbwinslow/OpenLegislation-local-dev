"""
CrewAI Software Development Team for OpenLegislation
===================================================

This module defines a comprehensive AI-powered software development team
using CrewAI framework. The team consists of specialized agents that work
together to analyze, develop, test, and maintain the OpenLegislation codebase.

Agents:
- Senior Software Architect: High-level design and architecture decisions
- Backend Developer: Java/Spring development and API implementation
- Frontend Developer: React/JavaScript development and UI/UX
- QA Engineer: Testing strategy, test automation, and quality assurance
- DevOps Engineer: Infrastructure, deployment, and CI/CD optimization
- Security Analyst: Security reviews and vulnerability assessments
- Technical Writer: Documentation and knowledge base management
- Project Manager: Coordination, planning, and progress tracking

Crews:
- Code Review Crew: Comprehensive code analysis and improvement
- Feature Development Crew: End-to-end feature implementation
- Bug Fix Crew: Rapid bug identification and resolution
- Documentation Crew: Technical documentation maintenance
- Security Audit Crew: Security assessment and hardening
"""

import os
from crewai import Agent, Task, Crew, Process
from crewai_tools import (
    CodeDocsSearchTool,
    DirectorySearchTool,
    FileReadTool,
    GithubSearchTool,
    SeleniumScrapingTool
)
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize AI models
try:
    openai_model = ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=0.1,
        api_key=os.getenv("OPENAI_API_KEY")
    )
except Exception as e:
    print(f"Warning: OpenAI model initialization failed: {e}")
    print("Using dummy model for development")
    openai_model = None

try:
    anthropic_model = ChatAnthropic(
        model="claude-3-sonnet-20240229",
        temperature=0.1,
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
except Exception as e:
    print(f"Warning: Anthropic model initialization failed: {e}")
    print("Using dummy model for development")
    anthropic_model = None

# Default to OpenAI, fallback to Anthropic
llm = openai_model if os.getenv("OPENAI_API_KEY") else anthropic_model

# Initialize tools
code_search = CodeDocsSearchTool()
dir_search = DirectorySearchTool()
file_reader = FileReadTool()
github_search = GithubSearchTool()
web_scraper = SeleniumScrapingTool()

# Import agent definitions
from .agents.architect import create_senior_architect
from .agents.backend_dev import create_backend_developer
from .agents.frontend_dev import create_frontend_developer
from .agents.qa_engineer import create_qa_engineer
from .agents.devops_engineer import create_devops_engineer
from .agents.security_analyst import create_security_analyst
from .agents.technical_writer import create_technical_writer
from .agents.project_manager import create_project_manager

# Create agents
senior_architect = create_senior_architect(llm, [code_search, dir_search, file_reader])
backend_developer = create_backend_developer(llm, [code_search, file_reader, github_search])
frontend_developer = create_frontend_developer(llm, [code_search, file_reader, web_scraper])
qa_engineer = create_qa_engineer(llm, [code_search, dir_search, file_reader])
devops_engineer = create_devops_engineer(llm, [dir_search, file_reader, github_search])
security_analyst = create_security_analyst(llm, [code_search, file_reader, web_scraper])
technical_writer = create_technical_writer(llm, [code_search, dir_search, file_reader])
project_manager = create_project_manager(llm, [github_search, dir_search])

# Define crews for different purposes
class DevelopmentCrews:
    """Factory class for creating different types of development crews"""

    @staticmethod
    def create_code_review_crew():
        """Create a crew focused on code review and quality improvement"""
        review_task = Task(
            description="""
            Perform comprehensive code review on recent changes in the OpenLegislation repository.
            Analyze code quality, identify potential bugs, suggest improvements, and ensure
            adherence to best practices. Focus on:
            - Code readability and maintainability
            - Performance optimizations
            - Security vulnerabilities
            - Test coverage gaps
            - Documentation completeness
            """,
            agent=senior_architect,
            expected_output="Detailed code review report with specific recommendations"
        )

        security_review_task = Task(
            description="""
            Conduct security analysis on the reviewed code. Identify potential security
            vulnerabilities, authentication/authorization issues, and data protection concerns.
            Provide specific remediation steps and security best practices recommendations.
            """,
            agent=security_analyst,
            expected_output="Security assessment report with vulnerability findings and fixes"
        )

        testing_review_task = Task(
            description="""
            Analyze the testing strategy and coverage. Identify missing test cases,
            suggest improvements to test quality, and recommend automation opportunities.
            """,
            agent=qa_engineer,
            expected_output="Testing analysis report with coverage recommendations"
        )

        return Crew(
            agents=[senior_architect, security_analyst, qa_engineer],
            tasks=[review_task, security_review_task, testing_review_task],
            process=Process.sequential,
            verbose=True
        )

    @staticmethod
    def create_feature_development_crew(feature_description: str):
        """Create a crew for end-to-end feature development"""
        planning_task = Task(
            description=f"""
            Analyze the feature request: {feature_description}
            Break down requirements, estimate complexity, and create a detailed implementation plan.
            Consider architectural implications, database changes, API design, and testing strategy.
            """,
            agent=project_manager,
            expected_output="Detailed feature implementation plan with tasks and timeline"
        )

        design_task = Task(
            description="""
            Design the technical solution based on the feature requirements.
            Create detailed specifications for backend APIs, database schema changes,
            frontend components, and integration points.
            """,
            agent=senior_architect,
            expected_output="Technical design document with architecture diagrams and specifications"
        )

        backend_implementation_task = Task(
            description="""
            Implement the backend components according to the technical design.
            Write clean, well-documented Java code following Spring Boot best practices.
            Include proper error handling, logging, and API documentation.
            """,
            agent=backend_developer,
            expected_output="Complete backend implementation with unit tests"
        )

        frontend_implementation_task = Task(
            description="""
            Implement the frontend components using React and modern JavaScript practices.
            Create responsive UI components, implement state management, and ensure
            proper integration with backend APIs.
            """,
            agent=frontend_developer,
            expected_output="Complete frontend implementation with component tests"
        )

        testing_task = Task(
            description="""
            Create comprehensive test suites for the new feature. Include unit tests,
            integration tests, and end-to-end tests. Ensure proper test coverage and
            automated testing setup.
            """,
            agent=qa_engineer,
            expected_output="Complete test suite with high coverage and automation"
        )

        deployment_task = Task(
            description="""
            Prepare deployment configurations, update CI/CD pipelines, and ensure
            proper infrastructure setup for the new feature. Include monitoring,
            logging, and rollback strategies.
            """,
            agent=devops_engineer,
            expected_output="Deployment configuration and infrastructure updates"
        )

        documentation_task = Task(
            description="""
            Create comprehensive documentation for the new feature including API docs,
            user guides, and technical specifications. Update existing documentation
            to reflect the changes.
            """,
            agent=technical_writer,
            expected_output="Complete documentation package for the feature"
        )

        return Crew(
            agents=[project_manager, senior_architect, backend_developer,
                   frontend_developer, qa_engineer, devops_engineer, technical_writer],
            tasks=[planning_task, design_task, backend_implementation_task,
                  frontend_implementation_task, testing_task, deployment_task, documentation_task],
            process=Process.sequential,
            verbose=True
        )

    @staticmethod
    def create_bug_fix_crew(bug_description: str):
        """Create a crew specialized in rapid bug identification and resolution"""
        analysis_task = Task(
            description=f"""
            Analyze the bug report: {bug_description}
            Reproduce the issue, identify root cause, and assess impact.
            Gather relevant logs, error messages, and system state information.
            """,
            agent=qa_engineer,
            expected_output="Bug analysis report with reproduction steps and root cause"
        )

        fix_design_task = Task(
            description="""
            Design the bug fix solution. Consider minimal changes, backward compatibility,
            and potential side effects. Create a detailed fix plan with testing strategy.
            """,
            agent=senior_architect,
            expected_output="Fix design document with implementation approach"
        )

        implementation_task = Task(
            description="""
            Implement the bug fix according to the design. Write clean, focused code
            that addresses the root cause without introducing new issues.
            """,
            agent=backend_developer,
            expected_output="Bug fix implementation with code changes"
        )

        verification_task = Task(
            description="""
            Verify the fix works correctly. Create test cases that reproduce the bug,
            confirm the fix resolves the issue, and ensure no regressions were introduced.
            """,
            agent=qa_engineer,
            expected_output="Verification report with test results and regression analysis"
        )

        return Crew(
            agents=[qa_engineer, senior_architect, backend_developer],
            tasks=[analysis_task, fix_design_task, implementation_task, verification_task],
            process=Process.sequential,
            verbose=True
        )

    @staticmethod
    def create_documentation_crew():
        """Create a crew focused on documentation maintenance and improvement"""
        audit_task = Task(
            description="""
            Audit existing documentation for completeness, accuracy, and currency.
            Identify gaps, outdated information, and areas needing improvement.
            """,
            agent=technical_writer,
            expected_output="Documentation audit report with identified issues"
        )

        update_task = Task(
            description="""
            Update documentation based on recent code changes and feature additions.
            Ensure API docs, README files, and technical guides are current and accurate.
            """,
            agent=technical_writer,
            expected_output="Updated documentation reflecting current codebase"
        )

        improvement_task = Task(
            description="""
            Improve documentation quality, structure, and usability. Add examples,
            tutorials, and troubleshooting guides where needed.
            """,
            agent=technical_writer,
            expected_output="Enhanced documentation with better structure and examples"
        )

        return Crew(
            agents=[technical_writer, senior_architect],
            tasks=[audit_task, update_task, improvement_task],
            process=Process.sequential,
            verbose=True
        )

    @staticmethod
    def create_security_audit_crew():
        """Create a crew for comprehensive security assessment"""
        vulnerability_scan_task = Task(
            description="""
            Perform comprehensive security vulnerability scanning. Check for common
            vulnerabilities, insecure dependencies, and potential security misconfigurations.
            """,
            agent=security_analyst,
            expected_output="Vulnerability scan report with identified issues"
        )

        code_security_review_task = Task(
            description="""
            Review code for security best practices. Check for SQL injection, XSS,
            authentication bypasses, and other security vulnerabilities in the codebase.
            """,
            agent=security_analyst,
            expected_output="Code security review with specific findings and recommendations"
        )

        infrastructure_security_task = Task(
            description="""
            Assess infrastructure security including container configurations, network security,
            secrets management, and deployment security practices.
            """,
            agent=devops_engineer,
            expected_output="Infrastructure security assessment report"
        )

        remediation_plan_task = Task(
            description="""
            Create detailed remediation plans for identified security issues.
            Prioritize fixes by severity and provide step-by-step implementation guides.
            """,
            agent=security_analyst,
            expected_output="Security remediation roadmap with prioritized action items"
        )

        return Crew(
            agents=[security_analyst, devops_engineer, senior_architect],
            tasks=[vulnerability_scan_task, code_security_review_task,
                  infrastructure_security_task, remediation_plan_task],
            process=Process.sequential,
            verbose=True
        )

# Utility functions
def get_available_crews():
    """Return list of available crew types"""
    return [
        "code_review",
        "feature_development",
        "bug_fix",
        "documentation",
        "security_audit"
    ]

def create_crew_by_type(crew_type: str, **kwargs):
    """Factory function to create crews by type"""
    crews = DevelopmentCrews()

    if crew_type == "code_review":
        return crews.create_code_review_crew()
    elif crew_type == "feature_development":
        return crews.create_feature_development_crew(kwargs.get("feature_description", ""))
    elif crew_type == "bug_fix":
        return crews.create_bug_fix_crew(kwargs.get("bug_description", ""))
    elif crew_type == "documentation":
        return crews.create_documentation_crew()
    elif crew_type == "security_audit":
        return crews.create_security_audit_crew()
    else:
        raise ValueError(f"Unknown crew type: {crew_type}")

if __name__ == "__main__":
    # Example usage
    print("CrewAI Software Development Team initialized!")
    print(f"Available crews: {get_available_crews()}")

    # Create a code review crew as example
    review_crew = DevelopmentCrews.create_code_review_crew()
    print(f"Code review crew created with {len(review_crew.agents)} agents")