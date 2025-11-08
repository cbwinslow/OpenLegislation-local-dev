"""
Political Metrics Analysis for OpenLegislation
==============================================

This script performs comprehensive political analysis using SQL queries,
embeddings, NLP, and BERT models to generate metrics and KPIs from
legislative data.
"""

import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import psycopg2
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Optional
import re

# AI/ML imports
from sentence_transformers import SentenceTransformer
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns

# CrewAI imports
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class PoliticalMetricsAnalyzer:
    """Main class for political metrics analysis"""

    def __init__(self, db_url: str = None):
        """Initialize the analyzer with database connection and ML models"""
        self.db_url = db_url or os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("Database URL not provided")

        # Database setup
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # ML models setup
        self.setup_ml_models()

        # CrewAI setup
        self.setup_crewai_agents()

        logger.info("Political Metrics Analyzer initialized")

    def setup_ml_models(self):
        """Setup machine learning models for text analysis"""
        try:
            # Sentence transformer for embeddings
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

            # Sentiment analysis pipeline
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest"
            )

            # Topic classification (using BERT)
            self.topic_classifier = pipeline(
                "text-classification",
                model="facebook/bart-large-mnli"
            )

            # Emotion detection
            self.emotion_detector = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base"
            )

            logger.info("ML models loaded successfully")

        except Exception as e:
            logger.error(f"Error loading ML models: {e}")
            raise

    def setup_crewai_agents(self):
        """Setup CrewAI agents for analysis"""
        # Initialize LLM
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        if openai_key:
            self.llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.1, api_key=openai_key)
        elif anthropic_key:
            self.llm = ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0.1, api_key=anthropic_key)
        else:
            raise ValueError("No API key found for LLM services")

        # Create analysis agent
        self.analysis_agent = Agent(
            role="Political Data Analyst",
            goal="Analyze legislative data and generate political insights",
            backstory="Expert in political science and data analysis with deep knowledge of legislative processes.",
            llm=self.llm,
            allow_delegation=False,
            verbose=True
        )

    def execute_sql_query(self, query: str, params: Dict = None) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                return pd.DataFrame(result.fetchall(), columns=result.keys())
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise

    def get_bill_metrics(self, session_year: int = None) -> Dict[str, Any]:
        """Calculate bill-related political metrics"""
        session_filter = f"WHERE session_year = {session_year}" if session_year else ""

        metrics = {}

        # Bill passage rates by status
        passage_query = f"""
        SELECT
            status,
            COUNT(*) as bill_count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
        FROM bill
        {session_filter}
        GROUP BY status
        ORDER BY bill_count DESC
        """

        metrics['bill_status_distribution'] = self.execute_sql_query(passage_query)

        # Bills by type
        type_query = f"""
        SELECT
            bill_type,
            COUNT(*) as count,
            ROUND(AVG(LENGTH(COALESCE(title, ''))), 2) as avg_title_length,
            ROUND(AVG(LENGTH(COALESCE(summary, ''))), 2) as avg_summary_length
        FROM bill
        {session_filter}
        GROUP BY bill_type
        ORDER BY count DESC
        """

        metrics['bill_types'] = self.execute_sql_query(type_query)

        # Most active sponsors
        sponsor_query = f"""
        SELECT
            m.member_name,
            m.party,
            m.chamber,
            COUNT(bs.bill_id) as bills_sponsored,
            COUNT(CASE WHEN b.status IN ('SIGNED_BY_GOV', 'PASSED') THEN 1 END) as bills_passed,
            ROUND(
                COUNT(CASE WHEN b.status IN ('SIGNED_BY_GOV', 'PASSED') THEN 1 END) * 100.0 / NULLIF(COUNT(bs.bill_id), 0),
                2
            ) as passage_rate
        FROM bill_sponsor bs
        JOIN member m ON bs.member_id = m.member_id
        JOIN bill b ON bs.bill_id = b.bill_id
        {session_filter.replace('WHERE', 'WHERE bs.session_year = b.session_year AND')}
        GROUP BY m.member_id, m.member_name, m.party, m.chamber
        ORDER BY bills_sponsored DESC
        LIMIT 20
        """

        metrics['top_sponsors'] = self.execute_sql_query(sponsor_query)

        # Legislative productivity over time
        productivity_query = f"""
        SELECT
            DATE_TRUNC('month', created_date) as month,
            COUNT(*) as bills_introduced,
            COUNT(CASE WHEN status IN ('SIGNED_BY_GOV', 'PASSED') THEN 1 END) as bills_passed
        FROM bill
        WHERE created_date IS NOT NULL
        {session_filter.replace('session_year', 'EXTRACT(year FROM created_date)')}
        GROUP BY DATE_TRUNC('month', created_date)
        ORDER BY month
        """

        metrics['legislative_productivity'] = self.execute_sql_query(productivity_query)

        return metrics

    def get_committee_metrics(self, session_year: int = None) -> Dict[str, Any]:
        """Calculate committee-related metrics"""
        session_filter = f"AND cm.session_year = {session_year}" if session_year else ""

        metrics = {}

        # Committee activity levels
        committee_query = f"""
        SELECT
            c.name as committee_name,
            c.chamber,
            COUNT(cm.member_id) as member_count,
            COUNT(DISTINCT a.agenda_id) as agendas_held,
            COUNT(DISTINCT b.bill_id) as bills_referred
        FROM committee c
        LEFT JOIN committee_member cm ON c.committee_id = cm.committee_id {session_filter}
        LEFT JOIN agenda a ON c.committee_id = a.committee_id
        LEFT JOIN bill b ON c.committee_id = b.current_committee_id
        GROUP BY c.committee_id, c.name, c.chamber
        ORDER BY agendas_held DESC
        """

        metrics['committee_activity'] = self.execute_sql_query(committee_query)

        # Committee referral patterns
        referral_query = f"""
        SELECT
            c.name as from_committee,
            c2.name as to_committee,
            COUNT(*) as referral_count
        FROM bill_action ba
        JOIN committee c ON ba.committee_id = c.committee_id
        LEFT JOIN committee c2 ON ba.to_committee_id = c2.committee_id
        WHERE ba.action_text LIKE '%referred%'
        GROUP BY c.committee_id, c.name, c2.committee_id, c2.name
        ORDER BY referral_count DESC
        LIMIT 20
        """

        metrics['committee_referrals'] = self.execute_sql_query(referral_query)

        return metrics

    def get_member_metrics(self, session_year: int = None) -> Dict[str, Any]:
        """Calculate member-related political metrics"""
        session_filter = f"WHERE session_year = {session_year}" if session_year else ""

        metrics = {}

        # Member productivity and effectiveness
        member_query = f"""
        SELECT
            m.member_name,
            m.party,
            m.chamber,
            m.district_code,
            COUNT(DISTINCT bs.bill_id) as bills_sponsored,
            COUNT(DISTINCT cm.committee_id) as committees_served,
            COUNT(DISTINCT ba.action_id) as actions_taken,
            AVG(CASE WHEN ba.action_text LIKE '%vote%' THEN 1 ELSE 0 END) as voting_participation
        FROM member m
        LEFT JOIN bill_sponsor bs ON m.member_id = bs.member_id
        LEFT JOIN committee_member cm ON m.member_id = cm.member_id
        LEFT JOIN bill_action ba ON m.member_id = ba.member_id
        {session_filter}
        GROUP BY m.member_id, m.member_name, m.party, m.chamber, m.district_code
        ORDER BY bills_sponsored DESC
        """

        metrics['member_productivity'] = self.execute_sql_query(member_query)

        # Party alignment analysis
        party_query = f"""
        SELECT
            party,
            chamber,
            COUNT(*) as member_count,
            AVG(bills_sponsored) as avg_bills_sponsored,
            AVG(committees_served) as avg_committees,
            AVG(voting_participation) as avg_voting_participation
        FROM ({member_query}) sub
        GROUP BY party, chamber
        ORDER BY party, chamber
        """

        metrics['party_alignment'] = self.execute_sql_query(party_query)

        return metrics

    def analyze_bill_text_with_embeddings(self, limit: int = 1000) -> Dict[str, Any]:
        """Analyze bill text using embeddings and NLP"""
        # Get bill texts
        bill_text_query = """
        SELECT
            bill_id,
            title,
            summary,
            full_text,
            bill_type,
            status
        FROM bill
        WHERE full_text IS NOT NULL
          AND LENGTH(full_text) > 100
        LIMIT :limit
        """

        bills_df = self.execute_sql_query(bill_text_query, {"limit": limit})

        if bills_df.empty:
            return {"error": "No bill text data available"}

        results = {}

        # Generate embeddings
        texts = bills_df['full_text'].fillna('').tolist()
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)

        results['embeddings'] = embeddings
        results['bill_data'] = bills_df

        # Topic clustering using K-means
        n_clusters = min(10, len(texts))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(embeddings)

        bills_df['cluster'] = clusters
        results['clusters'] = clusters

        # Analyze clusters
        cluster_analysis = []
        for i in range(n_clusters):
            cluster_bills = bills_df[bills_df['cluster'] == i]
            cluster_analysis.append({
                'cluster_id': i,
                'bill_count': len(cluster_bills),
                'common_types': cluster_bills['bill_type'].value_counts().head(3).to_dict(),
                'avg_title_length': cluster_bills['title'].str.len().mean(),
                'sample_titles': cluster_bills['title'].head(3).tolist()
            })

        results['cluster_analysis'] = cluster_analysis

        # Sentiment analysis
        sentiments = []
        for text in texts[:100]:  # Limit for performance
            try:
                sentiment = self.sentiment_analyzer(text[:512])  # Truncate for model limits
                sentiments.append(sentiment[0])
            except:
                sentiments.append({'label': 'UNKNOWN', 'score': 0.0})

        results['sentiment_analysis'] = sentiments

        # Topic classification
        topics = []
        for text in texts[:50]:  # Limit for performance
            try:
                # Use bill titles for topic classification as they're more concise
                title = bills_df.loc[bills_df['full_text'] == text, 'title'].iloc[0]
                topic = self.topic_classifier(
                    title,
                    candidate_labels=[
                        'healthcare', 'education', 'environment', 'economy', 'security',
                        'transportation', 'housing', 'taxes', 'civil rights', 'government'
                    ]
                )
                topics.append(topic)
            except:
                topics.append({'labels': [], 'scores': []})

        results['topic_classification'] = topics

        return results

    def generate_network_analysis(self) -> Dict[str, Any]:
        """Generate network analysis of legislative relationships"""
        # Co-sponsorship network
        cosponsor_query = """
        SELECT
            bs1.member_id as member1_id,
            m1.member_name as member1_name,
            bs1.bill_id,
            bs2.member_id as member2_id,
            m2.member_name as member2_name
        FROM bill_sponsor bs1
        JOIN bill_sponsor bs2 ON bs1.bill_id = bs2.bill_id AND bs1.member_id < bs2.member_id
        JOIN member m1 ON bs1.member_id = m1.member_id
        JOIN member m2 ON bs2.member_id = m2.member_id
        WHERE bs1.session_year = bs2.session_year
        """

        cosponsor_df = self.execute_sql_query(cosponsor_query)

        # Calculate co-sponsorship frequencies
        cosponsor_counts = cosponsor_df.groupby(['member1_id', 'member1_name', 'member2_id', 'member2_name']).size().reset_index(name='cosponsor_count')

        # Committee co-membership
        committee_query = """
        SELECT
            cm1.member_id as member1_id,
            m1.member_name as member1_name,
            cm1.committee_id,
            cm2.member_id as member2_id,
            m2.member_name as member2_name
        FROM committee_member cm1
        JOIN committee_member cm2 ON cm1.committee_id = cm2.committee_id AND cm1.member_id < cm2.member_id
        JOIN member m1 ON cm1.member_id = m1.member_id
        JOIN member m2 ON cm2.member_id = m2.member_id
        WHERE cm1.session_year = cm2.session_year
        """

        committee_df = self.execute_sql_query(committee_query)

        committee_counts = committee_df.groupby(['member1_id', 'member1_name', 'member2_id', 'member2_name']).size().reset_index(name='committee_count')

        return {
            'cosponsorship_network': cosponsor_counts.to_dict('records'),
            'committee_network': committee_counts.to_dict('records')
        }

    def create_comprehensive_report(self, session_year: int = None) -> Dict[str, Any]:
        """Generate comprehensive political metrics report"""
        logger.info("Generating comprehensive political metrics report...")

        report = {
            'generated_at': datetime.now().isoformat(),
            'session_year': session_year,
            'metrics': {}
        }

        # SQL-based metrics
        report['metrics']['bill_metrics'] = self.get_bill_metrics(session_year)
        report['metrics']['committee_metrics'] = self.get_committee_metrics(session_year)
        report['metrics']['member_metrics'] = self.get_member_metrics(session_year)

        # AI/ML analysis
        report['metrics']['text_analysis'] = self.analyze_bill_text_with_embeddings()
        report['metrics']['network_analysis'] = self.generate_network_analysis()

        # Generate insights using CrewAI
        insights = self.generate_ai_insights(report)
        report['insights'] = insights

        return report

    def generate_ai_insights(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Use CrewAI to generate insights from the metrics"""
        # Prepare data summary for AI analysis
        data_summary = f"""
        Political Metrics Analysis Summary:

        Bill Metrics:
        - Total bills: {len(report['metrics']['bill_metrics'].get('bill_status_distribution', []))}
        - Top bill statuses: {report['metrics']['bill_metrics'].get('bill_status_distribution', []).head(3).to_dict() if not report['metrics']['bill_metrics'].get('bill_status_distribution', pd.DataFrame()).empty else 'No data'}

        Member Productivity:
        - Top sponsors: {report['metrics']['member_metrics'].get('member_productivity', []).head(3).to_dict() if not report['metrics']['member_metrics'].get('member_productivity', pd.DataFrame()).empty else 'No data'}

        Text Analysis:
        - Clusters found: {len(report['metrics']['text_analysis'].get('cluster_analysis', []))}
        - Sentiment analysis: {len(report['metrics']['text_analysis'].get('sentiment_analysis', []))} bills analyzed

        Network Analysis:
        - Co-sponsorship relationships: {len(report['metrics']['text_analysis'].get('cosponsorship_network', []))}
        """

        insight_task = Task(
            description=f"""
            Analyze the following political metrics data and generate key insights:

            {data_summary}

            Provide insights on:
            1. Legislative productivity trends
            2. Key political actors and their influence
            3. Party dynamics and alignments
            4. Policy focus areas and emerging trends
            5. Network relationships and coalitions
            6. Recommendations for political strategy

            Focus on actionable insights that would be valuable for political consultants,
            policymakers, and stakeholders.
            """,
            agent=self.analysis_agent,
            expected_output="Comprehensive political insights report with key findings and recommendations"
        )

        crew = Crew(
            agents=[self.analysis_agent],
            tasks=[insight_task],
            process=Process.sequential,
            verbose=False
        )

        result = crew.kickoff()
        return {"ai_insights": str(result)}

    def save_report(self, report: Dict[str, Any], filename: str = None) -> str:
        """Save the analysis report to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"political_metrics_report_{timestamp}.json"

        with open(filename, 'w') as f:
            # Convert DataFrames to dict for JSON serialization
            serializable_report = self._make_serializable(report)
            json.dump(serializable_report, f, indent=2, default=str)

        logger.info(f"Report saved to {filename}")
        return filename

    def _make_serializable(self, obj):
        """Convert DataFrames and other non-serializable objects to serializable format"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj

def main():
    """Main execution function"""
    # Database URL from environment or command line
    db_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/openlegislation")

    # Initialize analyzer
    analyzer = PoliticalMetricsAnalyzer(db_url)

    # Generate comprehensive report
    session_year = 2023  # Adjust as needed
    report = analyzer.create_comprehensive_report(session_year)

    # Save report
    filename = analyzer.save_report(report)
    print(f"Analysis complete. Report saved to: {filename}")

    # Print key insights
    print("\n=== KEY INSIGHTS ===")
    if 'insights' in report and 'ai_insights' in report['insights']:
        print(report['insights']['ai_insights'][:1000] + "...")

if __name__ == "__main__":
    main()
