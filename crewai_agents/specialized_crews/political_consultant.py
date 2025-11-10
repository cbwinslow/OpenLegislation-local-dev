"""
Political Consultant Crew
========================

A specialized team of AI agents for political strategy, stakeholder analysis,
campaign management, and political communication.
"""

import os
from crewai import Agent, Task, Crew, Process
from crewai_tools import (
    SerperDevTool,
    ScrapeWebsiteTool,
    EXASearchTool,
    SeleniumScrapingTool,
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

def create_political_strategist(llm, tools: List = None):
    """Create the Political Strategist agent"""
    return Agent(
        role="Senior Political Strategist",
        goal="Develop comprehensive political strategies, messaging, and campaign plans",
        backstory="""You are a senior political strategist with 20+ years of experience in political campaigns,
        government affairs, and strategic communications. You've managed successful campaigns at federal,
        state, and local levels, advised elected officials, and led political organizations through
        complex policy battles and electoral challenges.

        Your expertise includes:
        - Campaign strategy and messaging development
        - Voter targeting and micro-targeting analysis
        - Coalition building and stakeholder engagement
        - Opposition research and counter-strategy
        - Media relations and earned media strategy
        - Digital campaigning and social media strategy
        - Fundraising strategy and donor relations
        - GOTV (Get Out The Vote) operations
        - Crisis communications and reputation management
        - Political risk assessment and mitigation

        You excel at understanding political dynamics, anticipating opponent moves, and developing
        winning strategies that resonate with target audiences while maintaining ethical standards.""",
        llm=llm,
        tools=tools or [],
        allow_delegation=True,
        verbose=True,
        memory=True,
        max_iter=30,
        max_execution_time=600,
    )

def create_public_opinion_analyst(llm, tools: List = None):
    """Create the Public Opinion Analyst agent"""
    return Agent(
        role="Public Opinion Analyst",
        goal="Analyze public sentiment, polling data, and voter behavior patterns",
        backstory="""You are a public opinion analyst specializing in political polling, voter behavior analysis,
        and sentiment tracking. With a background in political science, statistics, and data analysis,
        you've conducted research for political campaigns, think tanks, and media organizations,
        providing insights that shape political strategy and messaging.

        Your expertise includes:
        - Political polling design and analysis
        - Voter segmentation and targeting
        - Sentiment analysis and social media monitoring
        - Demographic trend analysis
        - Election forecasting and modeling
        - Message testing and optimization
        - Focus group facilitation and analysis
        - Public attitude tracking over time
        - Cultural and regional political analysis
        - Media consumption pattern analysis

        You provide data-driven insights about voter motivations, emerging trends, and effective
        communication strategies, helping campaigns connect authentically with target audiences.""",
        llm=llm,
        tools=tools or [],
        allow_delegation=True,
        verbose=True,
        memory=True,
        max_iter=30,
        max_execution_time=600,
    )

def create_stakeholder_engagement_specialist(llm, tools: List = None):
    """Create the Stakeholder Engagement Specialist agent"""
    return Agent(
        role="Stakeholder Engagement Specialist",
        goal="Build and maintain relationships with key stakeholders, coalitions, and interest groups",
        backstory="""You are a stakeholder engagement specialist with extensive experience in coalition building,
        grassroots organizing, and relationship management in political and policy environments. You've
        successfully built broad-based coalitions for legislative campaigns, ballot initiatives, and
        policy advocacy efforts across diverse stakeholder groups.

        Your expertise includes:
        - Coalition building and partnership development
        - Grassroots organizing and volunteer management
        - Interest group relations and advocacy coordination
        - Community leader engagement and relationship building
        - Labor union and business association relations
        - Faith-based organization partnerships
        - Ethnic and cultural community outreach
        - Environmental and social justice group coordination
        - Corporate and philanthropic stakeholder engagement
        - Crisis stakeholder communication

        You excel at identifying shared interests, building trust across diverse groups, and creating
        unified fronts for political and policy objectives.""",
        llm=llm,
        tools=tools or [],
        allow_delegation=True,
        verbose=True,
        memory=True,
        max_iter=30,
        max_execution_time=600,
    )

def create_digital_campaign_manager(llm, tools: List = None):
    """Create the Digital Campaign Manager agent"""
    return Agent(
        role="Digital Campaign Manager",
        goal="Manage digital strategy, social media, and online campaigning efforts",
        backstory="""You are a digital campaign manager specializing in online political engagement, digital
        advertising, and social media strategy. With expertise in digital marketing, data analytics,
        and online community building, you've led successful digital campaigns for political candidates,
        ballot measures, and advocacy organizations.

        Your expertise includes:
        - Social media strategy and content creation
        - Digital advertising and programmatic buying
        - Email marketing and CRM campaign management
        - SEO and content marketing for political campaigns
        - Online community building and engagement
        - Influencer and partnership campaigns
        - Viral content creation and meme strategy
        - Online reputation management
        - Digital analytics and performance tracking
        - Privacy and data protection compliance

        You understand the fast-paced nature of digital politics, viral potential, and the power of
        authentic online engagement to build movement momentum.""",
        llm=llm,
        tools=tools or [],
        allow_delegation=True,
        verbose=True,
        memory=True,
        max_iter=30,
        max_execution_time=600,
    )

def create_crisis_communications_specialist(llm, tools: List = None):
    """Create the Crisis Communications Specialist agent"""
    return Agent(
        role="Crisis Communications Specialist",
        goal="Manage crisis situations, reputation management, and rapid response communications",
        backstory="""You are a crisis communications specialist with extensive experience in political crisis
        management, reputation repair, and rapid response communications. You've handled high-stakes
        situations for political campaigns, elected officials, and organizations facing public scrutiny,
        media pressure, and stakeholder backlash.

        Your expertise includes:
        - Crisis communication strategy development
        - Rapid response protocol design and execution
        - Media relations during crisis situations
        - Stakeholder communication in crisis scenarios
        - Reputation management and image repair
        - Legal considerations in crisis communications
        - Social media crisis management
        - Internal communications during crises
        - Post-crisis recovery and relationship rebuilding
        - Crisis simulation and preparedness planning

        You remain calm under pressure, think strategically about long-term reputation implications,
        and communicate with empathy and transparency during difficult situations.""",
        llm=llm,
        tools=tools or [],
        allow_delegation=True,
        verbose=True,
        memory=True,
        max_iter=30,
        max_execution_time=600,
    )

class PoliticalConsultantCrew:
    """Factory class for political consultant crews"""

    @staticmethod
    def create_campaign_strategy_crew(candidate_info: str, district_info: str, opponent_info: str = None):
        """Create a crew for comprehensive campaign strategy development"""
        # Initialize enhanced tools for political research
        web_scraper = ScrapeWebsiteTool()
        search_tool = SerperDevTool() if os.getenv("SERPER_API_KEY") else None
        exa_search = EXASearchTool() if os.getenv("EXA_API_KEY") else None

        tools = [web_scraper, SeleniumScrapingTool()]
        if search_tool:
            tools.append(search_tool)
        if exa_search:
            tools.append(exa_search)

        # Create agents
        strategist = create_political_strategist(llm, tools)
        opinion_analyst = create_public_opinion_analyst(llm, tools)
        stakeholder_specialist = create_stakeholder_engagement_specialist(llm, tools)
        digital_manager = create_digital_campaign_manager(llm, tools)

        # Define tasks
        voter_analysis_task = Task(
            description=f"""
            Analyze the voting district and electorate for: {district_info}

            Conduct comprehensive voter analysis including:
            - Demographic breakdown and trends
            - Voting patterns and historical data
            - Key issues and voter priorities
            - Media consumption habits
            - Digital engagement levels
            - Cultural and community dynamics
            - Swing voter identification
            """,
            agent=opinion_analyst,
            expected_output="Comprehensive voter analysis report with targeting recommendations"
        )

        opponent_research_task = Task(
            description=f"""
            Conduct thorough opposition research on: {opponent_info or 'political opponents'}

            Analyze:
            - Opponent's voting record and positions
            - Campaign history and success patterns
            - Strengths, weaknesses, and vulnerabilities
            - Financial backing and donor network
            - Media presence and public perception
            - Potential attack vectors and defenses
            - Comparative advantage analysis
            """,
            agent=strategist,
            expected_output="Detailed opposition research report with strategic implications"
        )

        messaging_strategy_task = Task(
            description=f"""
            Develop comprehensive messaging strategy for candidate: {candidate_info}

            Create:
            - Core message platform and themes
            - Key talking points and sound bites
            - Emotional connection narratives
            - Attack and response messaging
            - Digital content strategy
            - Earned media messaging framework
            """,
            agent=strategist,
            expected_output="Complete messaging strategy with key communications materials"
        )

        coalition_building_task = Task(
            description=f"""
            Develop coalition building strategy for: {district_info}

            Identify and engage:
            - Key stakeholder groups and influencers
            - Community leaders and organizations
            - Business and labor associations
            - Cultural and faith-based groups
            - Environmental and advocacy organizations
            - Coalition maintenance and communication plans
            """,
            agent=stakeholder_specialist,
            expected_output="Coalition building strategy with engagement timelines and tactics"
        )

        digital_strategy_task = Task(
            description=f"""
            Create digital campaign strategy for candidate: {candidate_info}

            Develop:
            - Social media content calendar and themes
            - Digital advertising targeting strategy
            - Email marketing and CRM campaigns
            - Online community building approach
            - SEO and content marketing strategy
            - Digital volunteer recruitment tactics
            """,
            agent=digital_manager,
            expected_output="Comprehensive digital campaign strategy with implementation roadmap"
        )

        return Crew(
            agents=[strategist, opinion_analyst, stakeholder_specialist, digital_manager],
            tasks=[voter_analysis_task, opponent_research_task, messaging_strategy_task,
                  coalition_building_task, digital_strategy_task],
            process=Process.sequential,
            verbose=True
        )

    @staticmethod
    def create_crisis_management_crew(crisis_description: str, stakeholder_groups: List[str] = None):
        """Create a crew for crisis management and communications"""
        tools = [ScrapeWebsiteTool(), SerperDevTool() if os.getenv("SERPER_API_KEY") else None,
                SeleniumScrapingTool()]

        strategist = create_political_strategist(llm, tools)
        crisis_specialist = create_crisis_communications_specialist(llm, tools)
        stakeholder_specialist = create_stakeholder_engagement_specialist(llm, tools)
        digital_manager = create_digital_campaign_manager(llm, tools)

        crisis_assessment_task = Task(
            description=f"""
            Assess the political crisis: {crisis_description}

            Evaluate:
            - Immediate and long-term political damage
            - Media narrative and public perception
            - Stakeholder reactions and concerns
            - Legal and regulatory implications
            - Timeline for resolution and recovery
            - Comparative crisis analysis
            """,
            agent=strategist,
            expected_output="Crisis assessment report with severity analysis and initial recommendations"
        )

        response_strategy_task = Task(
            description=f"""
            Develop crisis response strategy for: {crisis_description}

            Create:
            - Key messages and talking points
            - Media response protocols
            - Stakeholder communication plans
            - Internal communication strategy
            - Timeline for response actions
            - Recovery and reputation rebuilding plan
            """,
            agent=crisis_specialist,
            expected_output="Comprehensive crisis response strategy with action timelines"
        )

        stakeholder_engagement_task = Task(
            description=f"""
            Develop stakeholder engagement plan for crisis: {crisis_description}

            For stakeholder groups: {', '.join(stakeholder_groups or ['media', 'supporters', 'opponents', 'public'])}

            Create:
            - Communication protocols for each group
            - Key message adaptation by audience
            - Engagement timeline and frequency
            - Feedback collection and response mechanisms
            - Relationship repair strategies
            """,
            agent=stakeholder_specialist,
            expected_output="Stakeholder engagement plan with communication protocols"
        )

        digital_response_task = Task(
            description=f"""
            Develop digital response strategy for crisis: {crisis_description}

            Plan:
            - Social media response and monitoring
            - Online reputation management
            - Digital advertising adjustments
            - Content creation and distribution strategy
            - Online community management during crisis
            - Digital damage control tactics
            """,
            agent=digital_manager,
            expected_output="Digital crisis response strategy with content and engagement plans"
        )

        return Crew(
            agents=[strategist, crisis_specialist, stakeholder_specialist, digital_manager],
            tasks=[crisis_assessment_task, response_strategy_task, stakeholder_engagement_task, digital_response_task],
            process=Process.sequential,
            verbose=True
        )

    @staticmethod
    def create_policy_advocacy_crew(policy_issue: str, target_audience: str, opposition_groups: List[str] = None):
        """Create a crew for policy advocacy and campaign management"""
        tools = [ScrapeWebsiteTool(), EXASearchTool() if os.getenv("EXA_API_KEY") else None,
                SerperDevTool() if os.getenv("SERPER_API_KEY") else None]

        strategist = create_political_strategist(llm, tools)
        opinion_analyst = create_public_opinion_analyst(llm, tools)
        stakeholder_specialist = create_stakeholder_engagement_specialist(llm, tools)
        digital_manager = create_digital_campaign_manager(llm, tools)

        public_opinion_task = Task(
            description=f"""
            Analyze public opinion on policy issue: {policy_issue}

            Assess:
            - Current public awareness and understanding
            - Support/opposition levels by demographic
            - Key concerns and misconceptions
            - Influencing factors and motivations
            - Messaging opportunities and challenges
            - Target audience: {target_audience}
            """,
            agent=opinion_analyst,
            expected_output="Public opinion analysis with messaging recommendations"
        )

        advocacy_strategy_task = Task(
            description=f"""
            Develop advocacy strategy for: {policy_issue}

            Create:
            - Campaign objectives and success metrics
            - Target audience segmentation and prioritization
            - Key messages and narrative framework
            - Opposition analysis and counter-strategy
            - Timeline and campaign phases
            - Resource requirements and budget considerations
            """,
            agent=strategist,
            expected_output="Comprehensive advocacy strategy with implementation plan"
        )

        coalition_development_task = Task(
            description=f"""
            Build advocacy coalition for: {policy_issue}

            Identify and engage:
            - Natural allies and supporting organizations
            - Influential individuals and opinion leaders
            - Opposition groups: {', '.join(opposition_groups or ['industry lobbyists', 'political opponents'])}
            - Coalition structure and governance
            - Communication and coordination mechanisms
            - Resource sharing and joint activities
            """,
            agent=stakeholder_specialist,
            expected_output="Coalition development plan with engagement strategy"
        )

        digital_advocacy_task = Task(
            description=f"""
            Create digital advocacy campaign for: {policy_issue}

            Develop:
            - Social media content and engagement strategy
            - Digital petition and action alert campaigns
            - Influencer and partnership outreach
            - Online advertising and targeting strategy
            - Email advocacy and supporter mobilization
            - Viral content and shareable media creation
            """,
            agent=digital_manager,
            expected_output="Digital advocacy campaign plan with content and engagement strategy"
        )

        return Crew(
            agents=[opinion_analyst, strategist, stakeholder_specialist, digital_manager],
            tasks=[public_opinion_task, advocacy_strategy_task, coalition_development_task, digital_advocacy_task],
            process=Process.sequential,
            verbose=True
        )