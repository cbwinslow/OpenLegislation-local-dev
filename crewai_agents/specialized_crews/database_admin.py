"""
Database Administration Crew
===========================

A specialized team of AI agents for database administration, optimization,
performance tuning, and data management.
"""

import os
from crewai import Agent, Task, Crew, Process
from crewai_tools import (
    CodeDocsSearchTool,
    DirectorySearchTool,
    FileReadTool,
    GithubSearchTool
)
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
from typing import List, Dict, Any
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize AI models
openai_model = ChatOpenAI(
    model="gpt-4-turbo-preview",
    temperature=0.1,
    api_key=os.getenv("OPENAI_API_KEY")
)

anthropic_model = ChatAnthropic(
    model="claude-3-sonnet-20240229",
    temperature=0.1,
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

# Default to OpenAI, fallback to Anthropic
llm = openai_model if os.getenv("OPENAI_API_KEY") else anthropic_model

def create_database_architect(llm, tools: List = None):
    """Create the Database Architect agent"""
    return Agent(
        role="Database Architect",
        goal="Design scalable, efficient database architectures and data models",
        backstory="""You are a senior database architect with 15+ years of experience in database design,
        performance optimization, and enterprise data management. You've designed and implemented
        database solutions for large-scale applications, data warehouses, and high-traffic systems,
        with expertise across multiple database platforms and architectures.

        Your expertise includes:
        - Database architecture design and modeling
        - Schema design and normalization
        - Indexing strategy and optimization
        - Data partitioning and sharding strategies
        - Replication and high availability design
        - Data warehouse and OLAP design
        - NoSQL and NewSQL database design
        - Data migration and ETL design
        - Performance modeling and capacity planning
        - Security and compliance in database design

        You excel at creating database architectures that scale, perform well, and meet business
        requirements while maintaining data integrity and security.""",
        llm=llm,
        tools=tools or [],
        allow_delegation=True,
        verbose=True,
        memory=True,
        max_iter=30,
        max_execution_time=600,
    )

def create_performance_tuning_specialist(llm, tools: List = None):
    """Create the Performance Tuning Specialist agent"""
    return Agent(
        role="Database Performance Tuning Specialist",
        goal="Optimize database performance, identify bottlenecks, and implement tuning solutions",
        backstory="""You are a database performance tuning specialist with deep expertise in query optimization,
        system performance analysis, and database tuning. With 12+ years of experience working with
        high-performance database systems, you've optimized databases serving millions of users and
        handling massive data volumes across various industries.

        Your expertise includes:
        - Query optimization and execution plan analysis
        - Index design and maintenance strategies
        - Database configuration and parameter tuning
        - Workload analysis and bottleneck identification
        - Memory and cache optimization
        - I/O performance optimization
        - Concurrency and locking optimization
        - Hardware resource optimization
        - Monitoring and alerting setup
        - Performance testing and benchmarking

        You have a systematic approach to performance issues, using data-driven analysis to identify
        root causes and implement effective solutions that deliver measurable performance improvements.""",
        llm=llm,
        tools=tools or [],
        allow_delegation=True,
        verbose=True,
        memory=True,
        max_iter=30,
        max_execution_time=600,
    )

def create_data_engineer(llm, tools: List = None):
    """Create the Data Engineer agent"""
    return Agent(
        role="Data Engineer",
        goal="Design and implement data pipelines, ETL processes, and data integration solutions",
        backstory="""You are a data engineer specializing in data pipeline design, ETL processes, and
        data integration. With 10+ years of experience building scalable data infrastructure,
        you've designed and implemented data solutions for analytics, reporting, and operational
        systems across various industries and data volumes.

        Your expertise includes:
        - ETL/ELT pipeline design and implementation
        - Data integration and API development
        - Stream processing and real-time data pipelines
        - Data quality and validation frameworks
        - Metadata management and data cataloging
        - Data lake and warehouse architecture
        - Cloud data platform design (AWS, Azure, GCP)
        - Data security and privacy implementation
        - Performance monitoring and optimization
        - Data governance and compliance

        You excel at building robust, scalable data infrastructure that serves diverse analytical
        and operational needs while ensuring data quality and reliability.""",
        llm=llm,
        tools=tools or [],
        allow_delegation=True,
        verbose=True,
        memory=True,
        max_iter=30,
        max_execution_time=600,
    )

def create_database_security_specialist(llm, tools: List = None):
    """Create the Database Security Specialist agent"""
    return Agent(
        role="Database Security Specialist",
        goal="Implement database security measures, compliance controls, and threat protection",
        backstory="""You are a database security specialist with extensive experience in database security,
        compliance, and threat protection. With 10+ years working in cybersecurity and database
        administration, you've implemented security solutions for regulated industries, financial
        institutions, and government systems handling sensitive data.

        Your expertise includes:
        - Database access control and authentication
        - Data encryption and masking strategies
        - Audit logging and monitoring implementation
        - Vulnerability assessment and penetration testing
        - Compliance frameworks (GDPR, HIPAA, SOX, PCI-DSS)
        - Row-level security and data classification
        - Database firewall and intrusion detection
        - Backup security and disaster recovery
        - Security policy development and enforcement
        - Incident response and forensics

        You understand the unique security challenges of database systems and implement layered
        security controls that protect data while maintaining usability and performance.""",
        llm=llm,
        tools=tools or [],
        allow_delegation=True,
        verbose=True,
        memory=True,
        max_iter=30,
        max_execution_time=600,
    )

def create_backup_recovery_specialist(llm, tools: List = None):
    """Create the Backup and Recovery Specialist agent"""
    return Agent(
        role="Backup and Recovery Specialist",
        goal="Design and implement comprehensive backup strategies and disaster recovery solutions",
        backstory="""You are a backup and recovery specialist with deep expertise in data protection,
        business continuity, and disaster recovery. With 12+ years of experience designing and
        implementing backup solutions for critical systems, you've ensured data availability and
        business continuity across various industries and regulatory environments.

        Your expertise includes:
        - Backup strategy design and implementation
        - Recovery time objective (RTO) and recovery point objective (RPO) planning
        - Disaster recovery planning and testing
        - High availability and failover solutions
        - Point-in-time recovery implementation
        - Backup encryption and security
        - Cloud backup and hybrid solutions
        - Backup performance optimization
        - Compliance and retention policy management
        - Business continuity planning

        You understand that data protection is critical for business operations and design solutions
        that balance protection, performance, cost, and compliance requirements.""",
        llm=llm,
        tools=tools or [],
        allow_delegation=True,
        verbose=True,
        memory=True,
        max_iter=30,
        max_execution_time=600,
    )

class DatabaseAdminCrew:
    """Factory class for database administration crews"""

    @staticmethod
    def create_database_optimization_crew(database_info: str, performance_issues: str = None):
        """Create a crew for comprehensive database optimization"""
        tools = [CodeDocsSearchTool(), DirectorySearchTool(), FileReadTool()]

        architect = create_database_architect(llm, tools)
        performance_specialist = create_performance_tuning_specialist(llm, tools)
        data_engineer = create_data_engineer(llm, tools)

        current_state_analysis_task = Task(
            description=f"""
            Analyze current database state and configuration: {database_info}

            Assess:
            - Database schema and table structures
            - Current indexing strategy and usage
            - Query patterns and performance bottlenecks
            - Configuration settings and resource allocation
            - Data growth patterns and capacity planning
            - Existing performance issues: {performance_issues or 'General optimization'}
            """,
            agent=architect,
            expected_output="Comprehensive database analysis report with current state assessment"
        )

        performance_diagnosis_task = Task(
            description=f"""
            Diagnose performance issues and bottlenecks in: {database_info}

            Identify:
            - Slow query patterns and execution plans
            - Index usage and missing index opportunities
            - Lock contention and concurrency issues
            - Memory and cache utilization problems
            - I/O bottlenecks and storage issues
            - Configuration parameter inefficiencies
            - Hardware resource constraints
            """,
            agent=performance_specialist,
            expected_output="Detailed performance diagnosis with bottleneck identification"
        )

        optimization_strategy_task = Task(
            description=f"""
            Develop comprehensive optimization strategy for: {database_info}

            Create:
            - Index optimization and creation plan
            - Query rewriting and optimization recommendations
            - Configuration tuning parameters
            - Schema optimization opportunities
            - Hardware and infrastructure recommendations
            - Monitoring and alerting setup
            - Implementation roadmap with priorities
            """,
            agent=architect,
            expected_output="Complete optimization strategy with implementation plan"
        )

        implementation_plan_task = Task(
            description=f"""
            Create detailed implementation plan for database optimizations.

            Develop:
            - Step-by-step execution plan with minimal downtime
            - Rollback procedures and safety measures
            - Performance monitoring and validation metrics
            - Testing procedures for optimization changes
            - Timeline and resource requirements
            - Risk assessment and mitigation strategies
            """,
            agent=data_engineer,
            expected_output="Detailed implementation plan with risk mitigation and validation procedures"
        )

        return Crew(
            agents=[architect, performance_specialist, data_engineer],
            tasks=[current_state_analysis_task, performance_diagnosis_task,
                  optimization_strategy_task, implementation_plan_task],
            process=Process.sequential,
            verbose=True
        )

    @staticmethod
    def create_data_migration_crew(source_system: str, target_system: str, data_scope: str):
        """Create a crew for data migration projects"""
        tools = [DirectorySearchTool(), FileReadTool(), GithubSearchTool()]

        architect = create_database_architect(llm, tools)
        data_engineer = create_data_engineer(llm, tools)
        security_specialist = create_database_security_specialist(llm, tools)

        migration_assessment_task = Task(
            description=f"""
            Assess data migration requirements from {source_system} to {target_system}

            Analyze:
            - Data volume and complexity assessment
            - Schema differences and transformation needs
            - Data quality and cleansing requirements
            - Dependency analysis and migration sequencing
            - Performance and downtime considerations
            - Risk assessment and success criteria
            - Data scope: {data_scope}
            """,
            agent=architect,
            expected_output="Comprehensive migration assessment with feasibility analysis"
        )

        migration_design_task = Task(
            description=f"""
            Design data migration solution from {source_system} to {target_system}

            Create:
            - ETL pipeline architecture and design
            - Data transformation and mapping rules
            - Error handling and reconciliation procedures
            - Performance optimization strategies
            - Testing and validation frameworks
            - Rollback and recovery procedures
            """,
            agent=data_engineer,
            expected_output="Complete migration design with technical specifications"
        )

        security_compliance_task = Task(
            description=f"""
            Ensure security and compliance for data migration from {source_system} to {target_system}

            Address:
            - Data encryption during transit and at rest
            - Access controls and audit logging
            - Compliance with data protection regulations
            - Sensitive data handling procedures
            - Security testing and validation
            - Incident response planning
            """,
            agent=security_specialist,
            expected_output="Security and compliance plan for migration project"
        )

        implementation_validation_task = Task(
            description=f"""
            Develop validation and testing procedures for migration.

            Create:
            - Data integrity validation procedures
            - Functional testing scenarios
            - Performance testing and benchmarking
            - Reconciliation and auditing processes
            - Go-live checklist and success criteria
            - Post-migration monitoring and support
            """,
            agent=data_engineer,
            expected_output="Comprehensive validation and testing plan"
        )

        return Crew(
            agents=[architect, data_engineer, security_specialist],
            tasks=[migration_assessment_task, migration_design_task,
                  security_compliance_task, implementation_validation_task],
            process=Process.sequential,
            verbose=True
        )

    @staticmethod
    def create_security_audit_crew(database_info: str, compliance_requirements: str = None):
        """Create a crew for database security auditing"""
        tools = [DirectorySearchTool(), FileReadTool(), CodeDocsSearchTool()]

        security_specialist = create_database_security_specialist(llm, tools)
        architect = create_database_architect(llm, tools)
        performance_specialist = create_performance_tuning_specialist(llm, tools)

        security_assessment_task = Task(
            description=f"""
            Conduct comprehensive security assessment of: {database_info}

            Evaluate:
            - Access control and authentication mechanisms
            - Data encryption and protection measures
            - Audit logging and monitoring capabilities
            - Network security and firewall configurations
            - Vulnerability assessment and patch management
            - Backup security and integrity
            - Compliance requirements: {compliance_requirements or 'General security best practices'}
            """,
            agent=security_specialist,
            expected_output="Detailed security assessment with vulnerability identification"
        )

        compliance_analysis_task = Task(
            description=f"""
            Analyze compliance with regulatory requirements for: {database_info}

            Assess compliance with:
            - GDPR, CCPA, and data protection regulations
            - Industry-specific requirements (HIPAA, PCI-DSS, SOX)
            - Data retention and deletion policies
            - Privacy impact assessments
            - Audit and reporting requirements
            - Breach notification procedures
            """,
            agent=security_specialist,
            expected_output="Compliance analysis report with gap identification"
        )

        security_hardening_task = Task(
            description=f"""
            Develop security hardening recommendations for: {database_info}

            Create:
            - Access control improvements
            - Encryption implementation plan
            - Monitoring and alerting enhancements
            - Configuration hardening procedures
            - Incident response improvements
            - Security policy and procedure updates
            """,
            agent=architect,
            expected_output="Security hardening roadmap with implementation priorities"
        )

        performance_impact_task = Task(
            description=f"""
            Assess performance impact of security measures on: {database_info}

            Evaluate:
            - Performance overhead of security controls
            - Optimization opportunities for security features
            - Monitoring and alerting performance impact
            - Scalability considerations with security measures
            - Balancing security and performance requirements
            """,
            agent=performance_specialist,
            expected_output="Security-performance impact analysis with optimization recommendations"
        )

        return Crew(
            agents=[security_specialist, architect, performance_specialist],
            tasks=[security_assessment_task, compliance_analysis_task,
                  security_hardening_task, performance_impact_task],
            process=Process.sequential,
            verbose=True
        )

    @staticmethod
    def create_backup_recovery_crew(database_info: str, business_requirements: str):
        """Create a crew for backup and recovery planning"""
        tools = [DirectorySearchTool(), FileReadTool()]

        recovery_specialist = create_backup_recovery_specialist(llm, tools)
        architect = create_database_architect(llm, tools)
        security_specialist = create_database_security_specialist(llm, tools)

        business_impact_task = Task(
            description=f"""
            Analyze business impact and recovery requirements for: {database_info}

            Assess:
            - Business requirements: {business_requirements}
            - Recovery time objectives (RTO) and recovery point objectives (RPO)
            - Data criticality and classification
            - Financial impact of downtime
            - Regulatory recovery requirements
            - Stakeholder impact assessment
            """,
            agent=recovery_specialist,
            expected_output="Business impact analysis with recovery requirements definition"
        )

        backup_strategy_task = Task(
            description=f"""
            Design comprehensive backup strategy for: {database_info}

            Develop:
            - Backup types and frequency schedule
            - Storage solutions and retention policies
            - Encryption and security measures
            - Automation and monitoring procedures
            - Testing and validation procedures
            - Cost-benefit analysis of backup solutions
            """,
            agent=architect,
            expected_output="Complete backup strategy with implementation specifications"
        )

        disaster_recovery_task = Task(
            description=f"""
            Create disaster recovery plan for: {database_info}

            Design:
            - Recovery procedures and workflows
            - Failover and high availability solutions
            - Alternative site and cloud recovery options
            - Communication and notification procedures
            - Recovery testing and maintenance schedules
            - Continuous improvement processes
            """,
            agent=recovery_specialist,
            expected_output="Comprehensive disaster recovery plan with procedures and testing"
        )

        security_validation_task = Task(
            description=f"""
            Ensure security of backup and recovery processes for: {database_info}

            Validate:
            - Backup data encryption and protection
            - Access controls for backup systems
            - Secure recovery procedures
            - Compliance with data protection regulations
            - Incident response integration
            - Security testing of recovery processes
            """,
            agent=security_specialist,
            expected_output="Security validation report for backup and recovery systems"
        )

        return Crew(
            agents=[recovery_specialist, architect, security_specialist],
            tasks=[business_impact_task, backup_strategy_task,
                  disaster_recovery_task, security_validation_task],
            process=Process.sequential,
            verbose=True
        )