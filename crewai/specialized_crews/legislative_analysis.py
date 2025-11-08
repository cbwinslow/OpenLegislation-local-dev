"""
Legislative Analysis Crew
========================

A specialized team of AI agents for comprehensive legislative analysis,
policy impact assessment, and legal document processing.
"""

import os
from crewai import Agent, Task, Crew, Process
from crewai_tools import (
    CodeDocsSearchTool,
    DirectorySearchTool,
    FileReadTool,
    GithubSearchTool,
    SeleniumScrapingTool,
    SerperDevTool,
    ScrapeWebsiteTool,
    EXASearchTool
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

def create_legislative_analyst(llm, tools: List = None):
    """Create the Legislative Analyst agent"""
    return Agent(
        role="Senior Legislative Analyst",
        goal="Analyze legislation, assess policy impacts, and provide comprehensive legal analysis",
        backstory="""You are a senior legislative analyst with 15+ years of experience in government affairs,
        policy analysis, and legislative research. You've worked for congressional committees, think tanks,
        and government agencies analyzing complex legislation including appropriations bills, regulatory
        frameworks, and constitutional law.

        Your expertise includes:
        - Statutory interpretation and legal analysis
        - Policy impact assessment and cost-benefit analysis
        - Regulatory compliance and implementation analysis
        - Legislative history research and intent analysis
        - Stakeholder impact assessment
        - Fiscal analysis and budget impact evaluation
        - Comparative policy analysis across jurisdictions
        - Legislative drafting and amendment analysis
        - Congressional procedure and parliamentary law
        - Executive branch implementation analysis

        You excel at breaking down complex legislative text into clear, actionable insights
        and identifying potential unintended consequences or implementation challenges.""",
        llm=llm,
        tools=tools or [],
        allow_delegation=True,
        verbose=True,
        memory=True,
        max_iter=30,
        max_execution_time=600,
    )

def create_policy_impact_analyst(llm, tools: List = None):
    """Create the Policy Impact Analyst agent"""
    return Agent(
        role="Policy Impact Analyst",
        goal="Assess the real-world impacts of legislation on various stakeholders and sectors",
        backstory="""You are a policy impact analyst specializing in evaluating how legislation affects
        different communities, industries, and government operations. With a background in economics,
        sociology, and public policy, you've conducted impact assessments for major federal and state
        legislation affecting healthcare, education, transportation, and environmental policy.

        Your expertise includes:
        - Economic impact modeling and forecasting
        - Social equity and justice impact analysis
        - Environmental impact assessment
        - Healthcare policy analysis and outcomes
        - Education policy evaluation
        - Transportation and infrastructure impact studies
        - Labor market and employment analysis
        - Small business and economic development impact
        - Intergovernmental relations and federalism analysis
        - Long-term vs short-term impact assessment

        You use data-driven approaches to quantify policy effects and identify winners/losers
        from legislative changes, providing evidence-based recommendations for policy improvements.""",
        llm=llm,
        tools=tools or [],
        allow_delegation=True,
        verbose=True,
        memory=True,
        max_iter=30,
        max_execution_time=600,
    )

def create_constitutional_lawyer(llm, tools: List = None):
    """Create the Constitutional Law Specialist agent"""
    return Agent(
        role="Constitutional Law Specialist",
        goal="Analyze legislation for constitutional compliance and separation of powers issues",
        backstory="""You are a constitutional law specialist with extensive experience in constitutional
        litigation, Supreme Court practice, and separation of powers analysis. You've served as counsel
        in constitutional challenges to federal and state legislation, with particular expertise in
        First Amendment, Due Process, Equal Protection, and federalism issues.

        Your expertise includes:
        - Constitutional interpretation and original intent analysis
        - Separation of powers and checks and balances
        - Federalism and state-federal relations
        - First Amendment rights and restrictions
        - Due Process and Equal Protection analysis
        - Commerce Clause and federal power limitations
        - Judicial review and standing analysis
        - Preemption and conflict preemption doctrine
        - Administrative law and agency authority
        - International law and treaty implications

        You provide rigorous constitutional analysis, identifying potential legal challenges
        and ensuring legislation complies with constitutional requirements.""",
        llm=llm,
        tools=tools or [],
        allow_delegation=True,
        verbose=True,
        memory=True,
        max_iter=30,
        max_execution_time=600,
    )

def create_regulatory_compliance_specialist(llm, tools: List = None):
    """Create the Regulatory Compliance Specialist agent"""
    return Agent(
        role="Regulatory Compliance Specialist",
        goal="Analyze regulatory implications and compliance requirements of legislation",
        backstory="""You are a regulatory compliance specialist with deep expertise in federal regulatory
        processes, administrative law, and implementation analysis. You've worked in government agencies
        and private sector compliance roles, ensuring legislative mandates are properly implemented
        through regulatory frameworks.

        Your expertise includes:
        - Administrative Procedure Act (APA) compliance
        - Notice-and-comment rulemaking analysis
        - Regulatory impact analysis and cost-benefit assessment
        - Agency authority and delegation doctrine
        - Federal Register and regulatory publication requirements
        - Implementation timelines and phase-in analysis
        - Enforcement mechanisms and penalty structures
        - Compliance monitoring and reporting requirements
        - Interagency coordination and consultation requirements
        - International regulatory harmonization

        You ensure legislation can be effectively implemented through proper regulatory frameworks,
        identifying potential implementation barriers and suggesting compliance strategies.""",
        llm=llm,
        tools=tools or [],
        allow_delegation=True,
        verbose=True,
        memory=True,
        max_iter=30,
        max_execution_time=600,
    )

class LegislativeAnalysisCrew:
    """Factory class for legislative analysis crews"""

    @staticmethod
    def create_comprehensive_bill_analysis_crew(bill_text: str, bill_number: str = None):
        """Create a crew for comprehensive bill analysis"""
        # Initialize enhanced tools
        web_scraper = ScrapeWebsiteTool()
        search_tool = SerperDevTool() if os.getenv("SERPER_API_KEY") else None
        exa_search = EXASearchTool() if os.getenv("EXA_API_KEY") else None

        tools = [web_scraper, GithubSearchTool(), DirectorySearchTool()]
        if search_tool:
            tools.append(search_tool)
        if exa_search:
            tools.append(exa_search)

        # Create agents
        legislative_analyst = create_legislative_analyst(llm, tools)
        policy_analyst = create_policy_impact_analyst(llm, tools)
        constitutional_lawyer = create_constitutional_lawyer(llm, tools)
        compliance_specialist = create_regulatory_compliance_specialist(llm, tools)

        # Define tasks
        bill_summary_task = Task(
            description=f"""
            Provide a comprehensive summary of bill {bill_number}: {bill_text[:500]}...

            Analyze:
            - Main purpose and objectives
            - Key provisions and changes
            - Affected parties and stakeholders
            - Implementation timeline and requirements
            - Budgetary implications
            """,
            agent=legislative_analyst,
            expected_output="Detailed bill summary with key provisions and implications"
        )

        constitutional_analysis_task = Task(
            description=f"""
            Conduct constitutional analysis of bill {bill_number}.

            Evaluate:
            - Constitutional authority for the legislation
            - Potential separation of powers issues
            - Individual rights implications
            - Federalism and state authority concerns
            - Due process and equal protection analysis
            - Potential legal challenges and precedents
            """,
            agent=constitutional_lawyer,
            expected_output="Constitutional analysis report with legal risks and recommendations"
        )

        policy_impact_task = Task(
            description=f"""
            Assess policy impacts of bill {bill_number}.

            Analyze:
            - Economic costs and benefits
            - Social equity implications
            - Industry and sector effects
            - Government operations impact
            - Long-term vs short-term consequences
            - Unintended consequences and externalities
            """,
            agent=policy_analyst,
            expected_output="Comprehensive policy impact assessment with quantitative analysis"
        )

        implementation_analysis_task = Task(
            description=f"""
            Analyze implementation requirements for bill {bill_number}.

            Evaluate:
            - Regulatory authority and rulemaking needs
            - Agency resource requirements
            - Compliance monitoring mechanisms
            - Enforcement strategies and penalties
            - Implementation timeline and phasing
            - Training and capacity building needs
            """,
            agent=compliance_specialist,
            expected_output="Implementation roadmap with regulatory requirements and timelines"
        )

        stakeholder_analysis_task = Task(
            description=f"""
            Identify and analyze stakeholder impacts for bill {bill_number}.

            Assess impacts on:
            - Federal, state, and local governments
            - Private sector and industry groups
            - Non-profit organizations and advocacy groups
            - Individual citizens and communities
            - International partners and foreign governments
            - Recommendations for stakeholder engagement
            """,
            agent=policy_analyst,
            expected_output="Stakeholder impact analysis with engagement recommendations"
        )

        return Crew(
            agents=[legislative_analyst, constitutional_lawyer, policy_analyst, compliance_specialist],
            tasks=[bill_summary_task, constitutional_analysis_task, policy_impact_task,
                  implementation_analysis_task, stakeholder_analysis_task],
            process=Process.sequential,
            verbose=True
        )

    @staticmethod
    def create_policy_comparison_crew(policy_area: str, jurisdictions: List[str] = None):
        """Create a crew for comparing policies across jurisdictions"""
        tools = [ScrapeWebsiteTool(), SerperDevTool() if os.getenv("SERPER_API_KEY") else None,
                EXASearchTool() if os.getenv("EXA_API_KEY") else None, GithubSearchTool()]

        legislative_analyst = create_legislative_analyst(llm, tools)
        policy_analyst = create_policy_impact_analyst(llm, tools)

        jurisdictions = jurisdictions or ["federal", "california", "new_york", "texas"]

        comparison_task = Task(
            description=f"""
            Compare {policy_area} policies across jurisdictions: {', '.join(jurisdictions)}

            For each jurisdiction, analyze:
            - Current legal framework and statutes
            - Implementation approaches and effectiveness
            - Stakeholder impacts and outcomes
            - Best practices and lessons learned
            - Potential for harmonization or improvement

            Provide recommendations for policy improvements based on comparative analysis.
            """,
            agent=legislative_analyst,
            expected_output="Comprehensive policy comparison report with recommendations"
        )

        impact_assessment_task = Task(
            description=f"""
            Assess the real-world impacts of different {policy_area} approaches across jurisdictions.

            Evaluate:
            - Effectiveness metrics and outcomes
            - Cost-benefit analysis
            - Equity and access considerations
            - Innovation and adaptation patterns
            - Transferable best practices
            """,
            agent=policy_analyst,
            expected_output="Cross-jurisdictional impact assessment with best practice recommendations"
        )

        return Crew(
            agents=[legislative_analyst, policy_analyst],
            tasks=[comparison_task, impact_assessment_task],
            process=Process.sequential,
            verbose=True
        )

    @staticmethod
    def create_regulatory_impact_analysis_crew(regulation_text: str, agency: str = None):
        """Create a crew for regulatory impact analysis"""
        tools = [ScrapeWebsiteTool(), DirectorySearchTool(), FileReadTool()]

        compliance_specialist = create_regulatory_compliance_specialist(llm, tools)
        policy_analyst = create_policy_impact_analyst(llm, tools)
        constitutional_lawyer = create_constitutional_lawyer(llm, tools)

        impact_analysis_task = Task(
            description=f"""
            Conduct regulatory impact analysis for: {regulation_text[:500]}...

            Agency: {agency or 'Federal agency'}

            Analyze:
            - Economic impacts on regulated entities
            - Benefits and costs quantification
            - Alternative regulatory approaches
            - Small business impact assessment
            - Paperwork and compliance burden analysis
            - Implementation and enforcement costs
            """,
            agent=compliance_specialist,
            expected_output="Detailed regulatory impact analysis with cost-benefit assessment"
        )

        legal_compliance_task = Task(
            description=f"""
            Assess legal and constitutional compliance of the proposed regulation.

            Evaluate:
            - Statutory authority for the regulation
            - Administrative procedure compliance
            - Constitutional concerns and challenges
            - Preemption and federalism issues
            - Judicial review considerations
            """,
            agent=constitutional_lawyer,
            expected_output="Legal compliance assessment with risk analysis"
        )

        stakeholder_impact_task = Task(
            description=f"""
            Analyze impacts on different stakeholder groups.

            Assess effects on:
            - Industry and business sectors
            - Consumers and citizens
            - State and local governments
            - Non-profit and advocacy organizations
            - International trade and commerce
            """,
            agent=policy_analyst,
            expected_output="Stakeholder impact analysis with mitigation recommendations"
        )

        return Crew(
            agents=[compliance_specialist, constitutional_lawyer, policy_analyst],
            tasks=[impact_analysis_task, legal_compliance_task, stakeholder_impact_task],
            process=Process.sequential,
            verbose=True
        )