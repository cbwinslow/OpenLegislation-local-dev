"""
Demo script for political metrics analysis with sample data
This demonstrates the analysis capabilities without requiring a live database
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DemoPoliticalMetricsAnalyzer:
    """Demo analyzer that generates sample legislative data for testing"""

    def __init__(self):
        """Initialize with sample data"""
        self.sample_data = self.generate_sample_data()
        logger.info("Demo analyzer initialized with sample data")

    def generate_sample_data(self) -> Dict[str, pd.DataFrame]:
        """Generate sample legislative data"""
        np.random.seed(42)  # For reproducible results

        # Generate sample bills
        n_bills = 1000
        bill_statuses = ['INTRODUCED', 'IN_COMMITTEE', 'PASSED_ASSEMBLY', 'PASSED_SENATE',
                        'DELIVERED_TO_GOV', 'SIGNED_BY_GOV', 'VETOED', 'STRICKEN']

        bills_data = []
        for i in range(n_bills):
            status = np.random.choice(bill_statuses, p=[0.3, 0.2, 0.15, 0.15, 0.05, 0.1, 0.03, 0.02])
            bill_type = np.random.choice(['RESOLUTION', 'BILL', 'CONCURRENT_RESOLUTION'], p=[0.4, 0.5, 0.1])

            bills_data.append({
                'bill_id': i + 1,
                'session_year': np.random.choice([2021, 2022, 2023, 2024]),
                'print_no': f'S{i+1:04d}',
                'title': f'Sample Bill {i+1} - {"Education" if i % 10 == 0 else "Healthcare" if i % 10 == 1 else "Environment" if i % 10 == 2 else "Economy" if i % 10 == 3 else "Security" if i % 10 == 4 else "Transportation"} Policy',
                'summary': f'This bill addresses {"educational reforms" if i % 10 == 0 else "healthcare improvements" if i % 10 == 1 else "environmental protection" if i % 10 == 2 else "economic development" if i % 10 == 3 else "public safety" if i % 10 == 4 else "infrastructure development"}.',
                'status': status,
                'bill_type': bill_type,
                'created_date': datetime.now() - timedelta(days=np.random.randint(1, 365)),
                'full_text': f'Full text of bill {i+1} containing legislative language about policy matters.'
            })

        # Generate sample members
        n_members = 200
        parties = ['DEMOCRAT', 'REPUBLICAN', 'INDEPENDENT']
        chambers = ['SENATE', 'ASSEMBLY']

        members_data = []
        for i in range(n_members):
            members_data.append({
                'member_id': i + 1,
                'member_name': f'Member {i+1}',
                'party': np.random.choice(parties, p=[0.55, 0.4, 0.05]),
                'chamber': np.random.choice(chambers),
                'district_code': f'District {i%50 + 1}'
            })

        # Generate bill sponsors
        sponsors_data = []
        for bill in bills_data:
            n_sponsors = np.random.poisson(2) + 1  # 1-3 sponsors typically
            sponsor_ids = np.random.choice([m['member_id'] for m in members_data],
                                          size=min(n_sponsors, len(members_data)), replace=False)
            for sponsor_id in sponsor_ids:
                sponsors_data.append({
                    'sponsor_id': len(sponsors_data) + 1,
                    'bill_id': bill['bill_id'],
                    'member_id': sponsor_id,
                    'session_year': bill['session_year'],
                    'sponsor_type': 'PRIMARY' if np.random.random() > 0.3 else 'COSPONSOR'
                })

        # Generate committees
        committees_data = [
            {'committee_id': 1, 'name': 'Education Committee', 'chamber': 'SENATE'},
            {'committee_id': 2, 'name': 'Health Committee', 'chamber': 'SENATE'},
            {'committee_id': 3, 'name': 'Finance Committee', 'chamber': 'SENATE'},
            {'committee_id': 4, 'name': 'Education Committee', 'chamber': 'ASSEMBLY'},
            {'committee_id': 5, 'name': 'Health Committee', 'chamber': 'ASSEMBLY'},
            {'committee_id': 6, 'name': 'Finance Committee', 'chamber': 'ASSEMBLY'},
            {'committee_id': 7, 'name': 'Transportation Committee', 'chamber': 'ASSEMBLY'},
            {'committee_id': 8, 'name': 'Environmental Conservation', 'chamber': 'SENATE'}
        ]

        # Generate committee members
        committee_members_data = []
        for committee in committees_data:
            n_members_committee = np.random.randint(5, 15)
            member_ids = np.random.choice([m['member_id'] for m in members_data
                                         if m['chamber'] == committee['chamber']],
                                         size=n_members_committee, replace=False)
            for member_id in member_ids:
                committee_members_data.append({
                    'committee_member_id': len(committee_members_data) + 1,
                    'committee_id': committee['committee_id'],
                    'member_id': member_id,
                    'session_year': 2023
                })

        return {
            'bills': pd.DataFrame(bills_data),
            'members': pd.DataFrame(members_data),
            'bill_sponsors': pd.DataFrame(sponsors_data),
            'committees': pd.DataFrame(committees_data),
            'committee_members': pd.DataFrame(committee_members_data)
        }

    def get_bill_metrics(self, session_year: int = None) -> Dict[str, Any]:
        """Calculate bill-related political metrics"""
        bills_df = self.sample_data['bills']
        if session_year:
            bills_df = bills_df[bills_df['session_year'] == session_year]

        metrics = {}

        # Bill passage rates by status
        status_counts = bills_df['status'].value_counts()
        total_bills = len(bills_df)
        status_distribution = pd.DataFrame({
            'status': status_counts.index,
            'bill_count': status_counts.values,
            'percentage': (status_counts.values / total_bills * 100).round(2)
        })

        metrics['bill_status_distribution'] = status_distribution

        # Bills by type
        type_stats = bills_df.groupby('bill_type').agg({
            'bill_id': 'count',
            'title': lambda x: x.str.len().mean(),
            'summary': lambda x: x.str.len().mean()
        }).round(2).reset_index()
        type_stats.columns = ['bill_type', 'count', 'avg_title_length', 'avg_summary_length']

        metrics['bill_types'] = type_stats

        # Most active sponsors
        sponsors_df = self.sample_data['bill_sponsors']
        members_df = self.sample_data['members']

        sponsor_stats = sponsors_df.groupby('member_id').agg({
            'bill_id': 'count'
        }).reset_index()

        sponsor_stats = sponsor_stats.merge(members_df, on='member_id', how='left')

        # Calculate passage rates
        bills_with_passage = bills_df[bills_df['status'].isin(['SIGNED_BY_GOV', 'PASSED'])]
        passed_bills = sponsors_df[sponsors_df['bill_id'].isin(bills_with_passage['bill_id'])]
        passed_stats = passed_bills.groupby('member_id').size().reset_index(name='bills_passed')

        sponsor_stats = sponsor_stats.merge(passed_stats, on='member_id', how='left').fillna(0)
        sponsor_stats['passage_rate'] = (sponsor_stats['bills_passed'] / sponsor_stats['bill_id'] * 100).round(2)
        sponsor_stats = sponsor_stats.rename(columns={'bill_id': 'bills_sponsored'})
        sponsor_stats = sponsor_stats.sort_values('bills_sponsored', ascending=False).head(20)

        metrics['top_sponsors'] = sponsor_stats[['member_name', 'party', 'chamber', 'bills_sponsored', 'bills_passed', 'passage_rate']]

        # Legislative productivity over time
        productivity = bills_df.groupby(bills_df['created_date'].dt.to_period('M')).size().reset_index(name='bills_introduced')
        productivity['month'] = productivity['created_date'].astype(str)
        productivity = productivity[['month', 'bills_introduced']].tail(12)

        # Add passed bills
        passed_productivity = bills_df[bills_df['status'].isin(['SIGNED_BY_GOV', 'PASSED'])]
        passed_monthly = passed_productivity.groupby(passed_productivity['created_date'].dt.to_period('M')).size().reset_index(name='bills_passed')
        passed_monthly['month'] = passed_monthly['created_date'].astype(str)

        productivity = productivity.merge(passed_monthly, on='month', how='left').fillna(0)
        metrics['legislative_productivity'] = productivity

        return metrics

    def get_member_metrics(self, session_year: int = None) -> Dict[str, Any]:
        """Calculate member-related political metrics"""
        members_df = self.sample_data['members']
        sponsors_df = self.sample_data['bill_sponsors']
        committees_df = self.sample_data['committee_members']

        metrics = {}

        # Member productivity
        member_stats = members_df.copy()

        # Bills sponsored
        sponsor_counts = sponsors_df.groupby('member_id').size().reset_index(name='bills_sponsored')
        member_stats = member_stats.merge(sponsor_counts, on='member_id', how='left').fillna(0)

        # Committees served
        committee_counts = committees_df.groupby('member_id').size().reset_index(name='committees_served')
        member_stats = member_stats.merge(committee_counts, on='member_id', how='left').fillna(0)

        # Mock voting participation (normally from bill_action table)
        member_stats['voting_participation'] = np.random.uniform(0.7, 1.0, len(member_stats))
        member_stats['actions_taken'] = (member_stats['bills_sponsored'] * np.random.uniform(2, 5, len(member_stats))).astype(int)

        metrics['member_productivity'] = member_stats.sort_values('bills_sponsored', ascending=False).head(20)

        # Party alignment analysis
        party_stats = member_stats.groupby(['party', 'chamber']).agg({
            'member_id': 'count',
            'bills_sponsored': 'mean',
            'committees_served': 'mean',
            'voting_participation': 'mean'
        }).round(2).reset_index()

        party_stats.columns = ['party', 'chamber', 'member_count', 'avg_bills_sponsored', 'avg_committees', 'avg_voting_participation']
        metrics['party_alignment'] = party_stats

        return metrics

    def get_committee_metrics(self, session_year: int = None) -> Dict[str, Any]:
        """Calculate committee-related metrics"""
        committees_df = self.sample_data['committees']
        committee_members_df = self.sample_data['committee_members']

        metrics = {}

        # Committee activity levels
        committee_stats = committees_df.copy()
        member_counts = committee_members_df.groupby('committee_id').size().reset_index(name='member_count')
        committee_stats = committee_stats.merge(member_counts, on='committee_id', how='left').fillna(0)

        # Mock agendas and bills referred
        committee_stats['agendas_held'] = np.random.poisson(10, len(committee_stats))
        committee_stats['bills_referred'] = np.random.poisson(20, len(committee_stats))

        metrics['committee_activity'] = committee_stats.sort_values('agendas_held', ascending=False)

        # Mock committee referrals
        referral_data = []
        for i in range(10):
            from_committee = np.random.choice(committees_df['name'].values)
            to_committee = np.random.choice(committees_df['name'].values)
            if from_committee != to_committee:
                referral_data.append({
                    'from_committee': from_committee,
                    'to_committee': to_committee,
                    'referral_count': np.random.randint(1, 20)
                })

        metrics['committee_referrals'] = pd.DataFrame(referral_data).sort_values('referral_count', ascending=False).head(10)

        return metrics

    def analyze_bill_text_with_embeddings(self, limit: int = 100) -> Dict[str, Any]:
        """Mock text analysis with embeddings"""
        bills_df = self.sample_data['bills'].head(limit)

        results = {
            'bill_data': bills_df,
            'embeddings': np.random.rand(len(bills_df), 384),  # Mock embeddings
            'clusters': np.random.randint(0, 5, len(bills_df)),
            'sentiment_analysis': [
                {'label': np.random.choice(['POSITIVE', 'NEGATIVE', 'NEUTRAL']), 'score': np.random.uniform(0.5, 1.0)}
                for _ in range(min(50, len(bills_df)))
            ],
            'topic_classification': [
                {'labels': ['policy'], 'scores': [0.8]}
                for _ in range(min(20, len(bills_df)))
            ]
        }

        # Cluster analysis
        cluster_analysis = []
        for i in range(5):
            cluster_bills = bills_df[results['clusters'] == i]
            cluster_analysis.append({
                'cluster_id': i,
                'bill_count': len(cluster_bills),
                'common_types': cluster_bills['bill_type'].value_counts().head(2).to_dict(),
                'avg_title_length': cluster_bills['title'].str.len().mean(),
                'sample_titles': cluster_bills['title'].head(2).tolist()
            })

        results['cluster_analysis'] = cluster_analysis

        return results

    def generate_network_analysis(self) -> Dict[str, Any]:
        """Generate mock network analysis"""
        sponsors_df = self.sample_data['bill_sponsors']
        members_df = self.sample_data['members']

        # Mock co-sponsorship network
        cosponsor_data = []
        for i in range(20):
            member1 = members_df.sample(1).iloc[0]
            member2 = members_df.sample(1).iloc[0]
            if member1['member_id'] != member2['member_id']:
                cosponsor_data.append({
                    'member1_id': member1['member_id'],
                    'member1_name': member1['member_name'],
                    'member2_id': member2['member_id'],
                    'member2_name': member2['member_name'],
                    'cosponsor_count': np.random.randint(1, 10)
                })

        # Mock committee network
        committee_members_df = self.sample_data['committee_members']
        committee_data = []
        for i in range(15):
            member1 = members_df.sample(1).iloc[0]
            member2 = members_df.sample(1).iloc[0]
            if member1['member_id'] != member2['member_id']:
                committee_data.append({
                    'member1_id': member1['member_id'],
                    'member1_name': member1['member_name'],
                    'member2_id': member2['member_id'],
                    'member2_name': member2['member_name'],
                    'committee_count': np.random.randint(1, 3)
                })

        return {
            'cosponsorship_network': cosponsor_data,
            'committee_network': committee_data
        }

    def create_comprehensive_report(self, session_year: int = None) -> Dict[str, Any]:
        """Generate comprehensive political metrics report"""
        logger.info("Generating comprehensive political metrics report...")

        report = {
            'generated_at': datetime.now().isoformat(),
            'session_year': session_year,
            'data_type': 'demo_sample_data',
            'metrics': {}
        }

        # Generate all metrics
        report['metrics']['bill_metrics'] = self.get_bill_metrics(session_year)
        report['metrics']['committee_metrics'] = self.get_committee_metrics(session_year)
        report['metrics']['member_metrics'] = self.get_member_metrics(session_year)
        report['metrics']['text_analysis'] = self.analyze_bill_text_with_embeddings()
        report['metrics']['network_analysis'] = self.generate_network_analysis()

        # Mock AI insights
        report['insights'] = {
            'ai_insights': """
            Based on the legislative data analysis:

            1. Legislative Productivity: The session shows moderate productivity with bills being introduced at a steady pace, though passage rates could be improved.

            2. Key Political Actors: Members from both parties are actively sponsoring legislation, with Democrats showing slightly higher sponsorship rates.

            3. Party Dynamics: Bipartisan cooperation appears in certain policy areas, particularly healthcare and education.

            4. Policy Focus Areas: The legislature is focusing on education reform, healthcare improvements, and economic development.

            5. Network Relationships: Strong co-sponsorship networks exist within parties, with some cross-party collaboration.

            6. Recommendations: Increase committee efficiency, encourage more bipartisan sponsorship, and focus on high-priority policy areas.
            """
        }

        return report

    def save_report(self, report: Dict[str, Any], filename: str = None) -> str:
        """Save the analysis report to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"demo_political_metrics_report_{timestamp}.json"

        with open(filename, 'w') as f:
            # Convert DataFrames to dict for JSON serialization
            serializable_report = self._make_serializable(report)
            json.dump(serializable_report, f, indent=2, default=str)

        logger.info(f"Demo report saved to {filename}")
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
    print("=== DEMO POLITICAL METRICS ANALYSIS ===")
    print("Generating sample legislative data and running analysis...")

    # Initialize demo analyzer
    analyzer = DemoPoliticalMetricsAnalyzer()

    # Generate comprehensive report
    session_year = 2023
    report = analyzer.create_comprehensive_report(session_year)

    # Save report
    filename = analyzer.save_report(report)
    print(f"Analysis complete. Demo report saved to: {filename}")

    # Print key metrics
    print("\n=== KEY METRICS SUMMARY ===")

    bill_metrics = report['metrics']['bill_metrics']
    print(f"Total Bills Analyzed: {len(bill_metrics['bill_status_distribution'])}")

    status_dist = bill_metrics['bill_status_distribution']
    if not status_dist.empty:
        top_status = status_dist.iloc[0]
        print(f"Most Common Status: {top_status['status']} ({top_status['bill_count']} bills, {top_status['percentage']}%)")

    member_metrics = report['metrics']['member_metrics']
    if 'member_productivity' in member_metrics and not member_metrics['member_productivity'].empty:
        top_sponsor = member_metrics['member_productivity'].iloc[0]
        print(f"Top Sponsor: {top_sponsor['member_name']} ({top_sponsor['bills_sponsored']} bills)")

    print("\n=== AI INSIGHTS ===")
    print(report['insights']['ai_insights'][:500] + "...")

if __name__ == "__main__":
    main()
