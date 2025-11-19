"""
CrewAI Automation Framework for OpenLegislation

This module provides AI agent crews specialized in different aspects of the project:
- Software Development Crew
- Legislative/Policy Analysis Crew  
- Database Programming and Admin Crew
- Documentation Crew
"""

import os
from crewai import Agent, Task, Crew, Process
from langchain.llms import OpenAI
from typing import List, Dict, Any


class OpenLegislationCrews:
    """Manager for all OpenLegislation AI crews"""
    
    def __init__(self, model: str = "gpt-4"):
        self.model = model
        self.llm = OpenAI(temperature=0.7, model_name=model)
    
    def create_software_dev_crew(self) -> Crew:
        """
        Software Development Crew
        Specializes in code review, architecture, testing, and implementation
        """
        
        # Senior Developer Agent
        senior_dev = Agent(
            role="Senior Software Developer",
            goal="Review code, provide architectural guidance, and ensure best practices",
            backstory="""You are a senior software engineer with 10+ years of experience in 
            Java, Spring Framework, and enterprise application development. You excel at 
            code review, architecture design, and mentoring junior developers.""",
            verbose=True,
            allow_delegation=True,
            llm=self.llm
        )
        
        # Code Quality Agent
        quality_engineer = Agent(
            role="Quality Assurance Engineer",
            goal="Ensure code quality, write comprehensive tests, and maintain high coverage",
            backstory="""You are a QA engineer specialized in automated testing, test-driven 
            development, and continuous integration. You write thorough unit tests, integration 
            tests, and ensure code meets quality standards.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # DevOps Engineer Agent
        devops_engineer = Agent(
            role="DevOps Engineer",
            goal="Optimize CI/CD pipelines, infrastructure, and deployment processes",
            backstory="""You are a DevOps engineer experienced with GitHub Actions, Docker, 
            Kubernetes, and cloud infrastructure. You automate everything and ensure reliable, 
            scalable deployments.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Security Expert Agent
        security_expert = Agent(
            role="Security Engineer",
            goal="Identify vulnerabilities, enforce security best practices, and ensure compliance",
            backstory="""You are a security engineer specialized in application security, 
            secure coding practices, and vulnerability assessment. You perform security audits 
            and ensure code follows security guidelines.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        return Crew(
            agents=[senior_dev, quality_engineer, devops_engineer, security_expert],
            tasks=[],  # Tasks added dynamically
            process=Process.sequential,
            verbose=True
        )
    
    def create_legislative_policy_crew(self) -> Crew:
        """
        Legislative and Policy Analysis Crew
        Specializes in legislative data, policy analysis, and government systems
        """
        
        # Legislative Data Expert
        legislative_expert = Agent(
            role="Legislative Data Specialist",
            goal="Analyze legislative data structures, ensure accurate bill processing",
            backstory="""You are an expert in legislative processes, bill lifecycle, and 
            government data systems. You understand SOBI files, bill formatting, and 
            legislative metadata standards.""",
            verbose=True,
            allow_delegation=True,
            llm=self.llm
        )
        
        # Policy Analyst
        policy_analyst = Agent(
            role="Policy Analyst",
            goal="Analyze policy implications, categorize legislation, provide context",
            backstory="""You are a policy analyst with deep knowledge of government operations, 
            legislative categories, and policy domains. You can categorize bills, identify 
            related legislation, and provide policy context.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Data Integration Specialist
        integration_specialist = Agent(
            role="Data Integration Specialist",
            goal="Integrate federal and state data sources, ensure data consistency",
            backstory="""You specialize in data integration from multiple government sources 
            including Congress.gov, GovInfo, and state legislative systems. You ensure data 
            mapping accuracy and consistency.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        return Crew(
            agents=[legislative_expert, policy_analyst, integration_specialist],
            tasks=[],
            process=Process.sequential,
            verbose=True
        )
    
    def create_database_crew(self) -> Crew:
        """
        Database Programming and Administration Crew
        Specializes in PostgreSQL, Elasticsearch, data modeling, and optimization
        """
        
        # Database Architect
        db_architect = Agent(
            role="Database Architect",
            goal="Design efficient database schemas, optimize queries, ensure data integrity",
            backstory="""You are a database architect with expertise in PostgreSQL, database 
            design, normalization, and query optimization. You design scalable data models 
            and ensure optimal database performance.""",
            verbose=True,
            allow_delegation=True,
            llm=self.llm
        )
        
        # DBA - Operations
        dba = Agent(
            role="Database Administrator",
            goal="Maintain database health, perform backups, monitor performance",
            backstory="""You are a DBA responsible for database operations, monitoring, 
            maintenance, and troubleshooting. You ensure high availability and optimal 
            performance of database systems.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Search Engineer
        search_engineer = Agent(
            role="Search Engineer",
            goal="Optimize Elasticsearch indices, improve search relevance and performance",
            backstory="""You are an Elasticsearch expert specializing in search optimization, 
            index design, and full-text search. You ensure fast, accurate search results 
            and optimal index configuration.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Data Migration Specialist
        migration_specialist = Agent(
            role="Data Migration Specialist",
            goal="Plan and execute data migrations, ensure data consistency",
            backstory="""You specialize in database migrations, data transformations, and 
            ensuring data integrity during schema changes. You use Flyway and write reliable 
            migration scripts.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        return Crew(
            agents=[db_architect, dba, search_engineer, migration_specialist],
            tasks=[],
            process=Process.sequential,
            verbose=True
        )
    
    def create_documentation_crew(self) -> Crew:
        """
        Documentation Crew
        Specializes in technical writing, API documentation, and user guides
        """
        
        # Technical Writer
        tech_writer = Agent(
            role="Technical Writer",
            goal="Create clear, comprehensive documentation for users and developers",
            backstory="""You are a technical writer who excels at creating documentation 
            that is clear, accurate, and user-friendly. You write API docs, user guides, 
            and developer documentation.""",
            verbose=True,
            allow_delegation=True,
            llm=self.llm
        )
        
        # API Documentation Specialist
        api_doc_specialist = Agent(
            role="API Documentation Specialist",
            goal="Document REST APIs, generate OpenAPI specs, provide code examples",
            backstory="""You specialize in API documentation, creating OpenAPI/Swagger 
            specifications, and writing clear endpoint documentation with examples.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Content Organizer
        content_organizer = Agent(
            role="Documentation Content Organizer",
            goal="Organize documentation structure, maintain consistency, improve navigation",
            backstory="""You organize and structure documentation for easy navigation and 
            findability. You maintain consistent formatting and ensure documentation is 
            well-organized.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        return Crew(
            agents=[tech_writer, api_doc_specialist, content_organizer],
            tasks=[],
            process=Process.sequential,
            verbose=True
        )
    
    def execute_code_review(self, code_changes: str, file_path: str) -> Dict[str, Any]:
        """Execute a code review using the software development crew"""
        crew = self.create_software_dev_crew()
        
        review_task = Task(
            description=f"""Review the following code changes in {file_path}:
            
            {code_changes}
            
            Provide:
            1. Security analysis
            2. Code quality assessment
            3. Performance considerations
            4. Best practices compliance
            5. Testing recommendations
            """,
            agent=crew.agents[0]  # Senior Developer leads
        )
        
        crew.tasks = [review_task]
        result = crew.kickoff()
        
        return {
            "status": "completed",
            "review": result,
            "file": file_path
        }
    
    def analyze_legislative_data(self, data_sample: str) -> Dict[str, Any]:
        """Analyze legislative data using the policy crew"""
        crew = self.create_legislative_policy_crew()
        
        analysis_task = Task(
            description=f"""Analyze the following legislative data:
            
            {data_sample}
            
            Provide:
            1. Data structure assessment
            2. Policy categorization
            3. Related legislation identification
            4. Data quality evaluation
            """,
            agent=crew.agents[0]  # Legislative Expert leads
        )
        
        crew.tasks = [analysis_task]
        result = crew.kickoff()
        
        return {
            "status": "completed",
            "analysis": result
        }
    
    def optimize_database_query(self, query: str, context: str) -> Dict[str, Any]:
        """Optimize database queries using the database crew"""
        crew = self.create_database_crew()
        
        optimization_task = Task(
            description=f"""Optimize the following database query:
            
            Query: {query}
            Context: {context}
            
            Provide:
            1. Query performance analysis
            2. Optimization suggestions
            3. Index recommendations
            4. Alternative query approaches
            """,
            agent=crew.agents[0]  # DB Architect leads
        )
        
        crew.tasks = [optimization_task]
        result = crew.kickoff()
        
        return {
            "status": "completed",
            "optimization": result,
            "original_query": query
        }
    
    def generate_documentation(self, code_path: str, doc_type: str) -> Dict[str, Any]:
        """Generate documentation using the documentation crew"""
        crew = self.create_documentation_crew()
        
        doc_task = Task(
            description=f"""Generate {doc_type} documentation for code at {code_path}.
            
            Include:
            1. Clear descriptions
            2. Usage examples
            3. API references (if applicable)
            4. Configuration details
            """,
            agent=crew.agents[0]  # Technical Writer leads
        )
        
        crew.tasks = [doc_task]
        result = crew.kickoff()
        
        return {
            "status": "completed",
            "documentation": result,
            "type": doc_type,
            "path": code_path
        }


def main():
    """Example usage of the crews"""
    
    # Initialize crews manager
    crews = OpenLegislationCrews(model="gpt-4")
    
    # Example: Code review
    print("=" * 80)
    print("Software Development Crew - Code Review")
    print("=" * 80)
    
    sample_code = """
    public void processBill(String billId) {
        // Process bill data
        String query = "SELECT * FROM bills WHERE id = '" + billId + "'";
        executeQuery(query);
    }
    """
    
    review_result = crews.execute_code_review(sample_code, "BillProcessor.java")
    print(f"Review Result: {review_result}")
    
    # Example: Legislative data analysis
    print("\n" + "=" * 80)
    print("Legislative Policy Crew - Data Analysis")
    print("=" * 80)
    
    sample_data = """
    Bill S1234A - Education Funding Reform
    Sponsor: Senator Smith
    Committee: Education
    Status: In Committee
    """
    
    analysis_result = crews.analyze_legislative_data(sample_data)
    print(f"Analysis Result: {analysis_result}")


if __name__ == "__main__":
    main()
