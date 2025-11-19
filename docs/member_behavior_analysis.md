# Member Behavior Analysis and Consistency Studies

## Overview

This document provides comprehensive methodologies for analyzing legislative member behavior patterns, including consistency assessment, bias detection, and honesty evaluation using voting records and text analysis.

## Theoretical Foundation

### Behavioral Consistency Metrics

#### DW-NOMINATE Methodology
```python
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

class DWNominateAnalyzer:
    """
    Implements DW-NOMINATE methodology for analyzing legislative voting patterns
    """
    def __init__(self, num_dimensions=2):
        self.num_dimensions = num_dimensions
        self.scaler = StandardScaler()
        
    def calculate_ideological_scores(self, voting_matrix):
        """
        Calculate ideological scores from voting matrix
        
        Args:
            voting_matrix: numpy array of shape (members, bills) with values -1, 0, 1
        """
        # Standardize voting data
        standardized_votes = self.scaler.fit_transform(voting_matrix)
        
        # Apply dimensionality reduction
        pca = PCA(n_components=self.num_dimensions)
        ideological_scores = pca.fit_transform(standardized_votes)
        
        # First dimension = liberal-conservative spectrum
        # Second dimension = other ideological dimensions
        
        return {
            'ideological_scores': ideological_scores,
            'explained_variance': pca.explained_variance_ratio_,
            'principal_components': pca.components_,
            'member_coordinates': ideological_scores[:, :self.num_dimensions]
        }
    
    def calculate_consistency_score(self, member_votes, time_window=30):
        """
        Calculate voting consistency over time windows
        """
        consistency_scores = []
        
        for i in range(len(member_votes) - time_window + 1):
            window = member_votes[i:i + time_window]
            
            # Calculate ideological position for window
            window_position = self.calculate_window_position(window)
            consistency_scores.append(window_position)
        
        # Overall consistency = inverse of variance
        overall_consistency = 1.0 / (1.0 + np.var(consistency_scores))
        
        return {
            'overall_consistency': overall_consistency,
            'time_series_consistency': consistency_scores,
            'consistency_variance': np.var(consistency_scores),
            'trend': self.calculate_trend(consistency_scores)
        }
    
    def calculate_window_position(self, window_votes):
        """Calculate ideological position for time window"""
        # Weight recent votes more heavily
        weights = np.exp(np.linspace(-1, 0, len(window_votes)))
        weighted_votes = window_votes * weights[:, np.newaxis]
        
        return np.mean(weighted_votes)
```

### Temporal Behavior Analysis

#### Time-Series Consistency
```python
import pandas as pd
from scipy import stats
from scipy.signal import find_peaks

class TemporalBehaviorAnalyzer:
    def __init__(self):
        self.consistency_threshold = 0.7
        self.significance_level = 0.05
    
    def analyze_temporal_patterns(self, member_data):
        """
        Analyze temporal patterns in member behavior
        """
        voting_history = member_data['voting_history']
        text_history = member_data['text_history']
        
        # Voting consistency over time
        voting_consistency = self.analyze_voting_consistency(voting_history)
        
        # Text consistency over time
        text_consistency = self.analyze_text_consistency(text_history)
        
        # Position shifts detection
        position_shifts = self.detect_position_shifts(voting_history)
        
        # Seasonal patterns
        seasonal_patterns = self.detect_seasonal_patterns(voting_history)
        
        return {
            'voting_consistency': voting_consistency,
            'text_consistency': text_consistency,
            'position_shifts': position_shifts,
            'seasonal_patterns': seasonal_patterns,
            'overall_stability': self.calculate_overall_stability(
                voting_consistency, text_consistency
            )
        }
    
    def detect_position_shifts(self, voting_history):
        """
        Detect significant shifts in voting positions
        """
        # Calculate rolling ideological position
        rolling_position = self.calculate_ideological_position(voting_history)
        
        # Find change points using statistical tests
        change_points = []
        
        for i in range(10, len(rolling_position) - 10):
            before = rolling_position[i-10:i]
            after = rolling_position[i:i+10]
            
            # T-test for significant change
            t_stat, p_value = stats.ttest_ind(before, after)
            
            if p_value < self.significance_level:
                change_points.append({
                    'timestamp': voting_history[i]['date'],
                    'position_before': np.mean(before),
                    'position_after': np.mean(after),
                    'significance': p_value,
                    'magnitude': abs(np.mean(after) - np.mean(before))
                })
        
        return {
            'change_points': change_points,
            'total_shifts': len(change_points),
            'shift_frequency': len(change_points) / len(voting_history),
            'average_shift_magnitude': np.mean([cp['magnitude'] for cp in change_points]) if change_points else 0
        }
    
    def detect_seasonal_patterns(self, voting_history):
        """
        Detect seasonal patterns in voting behavior
        """
        df = pd.DataFrame(voting_history)
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['year'] = df['date'].dt.year
        
        # Calculate average position by month
        monthly_patterns = df.groupby('month')['ideological_position'].agg(['mean', 'std']).to_dict('index')
        
        # Calculate average position by quarter
        quarterly_patterns = df.groupby('quarter')['ideological_position'].agg(['mean', 'std']).to_dict('index')
        
        # Test for seasonality using ANOVA
        monthly_groups = [group['ideological_position'].values for name, group in df.groupby('month')]
        f_stat, p_value = stats.f_oneway(*monthly_groups)
        
        return {
            'monthly_patterns': monthly_patterns,
            'quarterly_patterns': quarterly_patterns,
            'seasonality_significant': p_value < self.significance_level,
            'seasonality_strength': f_stat,
            'peak_months': self.find_peak_months(monthly_patterns),
            'low_months': self.find_low_months(monthly_patterns)
        }
```

## Network Analysis for Voting Blocs

### Graph-Based Relationship Analysis
```python
import networkx as nx
from community import community_louvain
import numpy as np

class VotingNetworkAnalyzer:
    def __init__(self):
        self.similarity_threshold = 0.8
        self.min_bloc_size = 3
    
    def build_voting_network(self, voting_data):
        """
        Build network of voting relationships
        """
        G = nx.Graph()
        
        # Add nodes (members)
        for member in voting_data['members']:
            G.add_node(member['id'], **member['attributes'])
        
        # Add edges based on voting similarity
        for i, member1 in enumerate(voting_data['members']):
            for j, member2 in enumerate(voting_data['members'][i+1:], i+1):
                similarity = self.calculate_voting_similarity(
                    member1['voting_record'], 
                    member2['voting_record']
                )
                
                if similarity > self.similarity_threshold:
                    G.add_edge(
                        member1['id'], 
                        member2['id'],
                        weight=similarity,
                        similarity=similarity
                    )
        
        return G
    
    def detect_voting_blocs(self, G):
        """
        Detect voting blocs using community detection
        """
        # Louvain community detection
        partition = community_louvain.best_partition(G, weight='weight')
        
        # Analyze each community
        blocs = {}
        for member_id, community_id in partition.items():
            if community_id not in blocs:
                blocs[community_id] = []
            blocs[community_id].append(member_id)
        
        # Filter small blocs
        significant_blocs = {
            comm_id: members for comm_id, members in blocs.items()
            if len(members) >= self.min_bloc_size
        }
        
        # Calculate bloc metrics
        bloc_analysis = {}
        for comm_id, members in significant_blocs.items():
            subgraph = G.subgraph(members)
            
            bloc_analysis[comm_id] = {
                'members': members,
                'size': len(members),
                'density': nx.density(subgraph),
                'average_similarity': self.calculate_bloc_average_similarity(G, members),
                'central_members': self.find_central_members(subgraph),
                'cohesion_score': self.calculate_cohesion_score(subgraph)
            }
        
        return {
            'blocs': bloc_analysis,
            'total_blocs': len(significant_blocs),
            'modularity': nx.algorithms.community.quality.modularity(G, partition),
            'largest_bloc_size': max(len(members) for members in significant_blocs.values()),
            'bloc_distribution': self.analyze_bloc_distribution(bloc_analysis)
        }
    
    def calculate_voting_similarity(self, votes1, votes2):
        """
        Calculate similarity between two voting records
        """
        # Ensure same bills
        common_bills = set(votes1.keys()) & set(votes2.keys())
        
        if len(common_bills) == 0:
            return 0.0
        
        # Calculate agreement rate
        agreements = 0
        for bill in common_bills:
            if votes1[bill] == votes2[bill]:
                agreements += 1
        
        similarity = agreements / len(common_bills)
        return similarity
    
    def find_central_members(self, subgraph):
        """
        Find most central members in voting bloc
        """
        centrality_metrics = {
            'degree': nx.degree_centrality(subgraph, weight='weight'),
            'betweenness': nx.betweenness_centrality(subgraph, weight='weight'),
            'closeness': nx.closeness_centrality(subgraph, weight='weight'),
            'eigenvector': nx.eigenvector_centrality(subgraph, weight='weight')
        }
        
        # Combine centrality scores
        central_members = []
        for node in subgraph.nodes():
            combined_score = (
                centrality_metrics['degree'][node] * 0.3 +
                centrality_metrics['betweenness'][node] * 0.3 +
                centrality_metrics['closeness'][node] * 0.2 +
                centrality_metrics['eigenvector'][node] * 0.2
            )
            
            central_members.append({
                'member_id': node,
                'centrality_score': combined_score,
                'individual_metrics': {
                    metric: centrality_metrics[metric][node]
                    for metric in centrality_metrics
                }
            })
        
        # Sort by centrality
        central_members.sort(key=lambda x: x['centrality_score'], reverse=True)
        
        return central_members[:5]  # Top 5 central members
```

## Honesty and Integrity Assessment

### Statement vs Voting Consistency
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class HonestyAssessment:
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.consistency_weight = 0.4
        self.transparency_weight = 0.3
        self.accountability_weight = 0.3
    
    def assess_honesty(self, member_data):
        """
        Comprehensive honesty assessment
        """
        # Extract positions from statements
        statement_positions = self.extract_statement_positions(member_data['statements'])
        
        # Extract positions from voting record
        voting_positions = self.extract_voting_positions(member_data['voting_record'])
        
        # Calculate consistency
        consistency_score = self.calculate_statement_vote_consistency(
            statement_positions, voting_positions
        )
        
        # Calculate transparency
        transparency_score = self.calculate_transparency(member_data['communications'])
        
        # Calculate accountability
        accountability_score = self.calculate_accountability(member_data['voting_record'])
        
        # Overall honesty score
        honesty_score = (
            consistency_score * self.consistency_weight +
            transparency_score * self.transparency_weight +
            accountability_score * self.accountability_weight
        )
        
        return {
            'overall_honesty_score': honesty_score,
            'consistency_score': consistency_score,
            'transparency_score': transparency_score,
            'accountability_score': accountability_score,
            'detailed_analysis': {
                'statement_positions': statement_positions,
                'voting_positions': voting_positions,
                'inconsistencies': self.identify_inconsistencies(
                    statement_positions, voting_positions
                ),
                'risk_factors': self.identify_risk_factors(member_data)
            }
        }
    
    def extract_statement_positions(self, statements):
        """
        Extract policy positions from public statements
        """
        positions = []
        
        for statement in statements:
            # Use NLP to extract position on issues
            position = self.analyze_statement_position(statement['text'])
            
            positions.append({
                'date': statement['date'],
                'issue': position['issue'],
                'stance': position['stance'],
                'confidence': position['confidence'],
                'text': statement['text'],
                'source': statement['source']
            })
        
        return positions
    
    def calculate_statement_vote_consistency(self, statement_positions, voting_positions):
        """
        Calculate consistency between statements and voting
        """
        consistency_scores = []
        
        for stmt_pos in statement_positions:
            # Find corresponding voting position
            matching_vote_pos = self.find_matching_voting_position(
                stmt_pos, voting_positions
            )
            
            if matching_vote_pos:
                # Calculate position alignment
                alignment = self.calculate_position_alignment(
                    stmt_pos['stance'], matching_vote_pos['stance']
                )
                
                consistency_scores.append({
                    'date': stmt_pos['date'],
                    'issue': stmt_pos['issue'],
                    'statement_stance': stmt_pos['stance'],
                    'voting_stance': matching_vote_pos['stance'],
                    'alignment': alignment,
                    'confidence': stmt_pos['confidence']
                })
        
        # Overall consistency
        if consistency_scores:
            overall_consistency = np.mean([cs['alignment'] for cs in consistency_scores])
        else:
            overall_consistency = 0.5  # Neutral if no data
        
        return {
            'overall_consistency': overall_consistency,
            'individual_consistencies': consistency_scores,
            'consistency_variance': np.var([cs['alignment'] for cs in consistency_scores]) if consistency_scores else 0,
            'trend': self.calculate_consistency_trend(consistency_scores)
        }
    
    def identify_inconsistencies(self, statement_positions, voting_positions):
        """
        Identify specific inconsistencies between statements and votes
        """
        inconsistencies = []
        
        for stmt_pos in statement_positions:
            matching_vote = self.find_matching_voting_position(stmt_pos, voting_positions)
            
            if matching_vote:
                alignment = self.calculate_position_alignment(
                    stmt_pos['stance'], matching_vote['stance']
                )
                
                # Flag significant misalignments
                if alignment < 0.3:  # Low alignment threshold
                    inconsistencies.append({
                        'date': stmt_pos['date'],
                        'issue': stmt_pos['issue'],
                        'statement': stmt_pos['stance'],
                        'vote': matching_vote['stance'],
                        'severity': 'high' if alignment < 0.1 else 'medium',
                        'description': self.generate_inconsistency_description(stmt_pos, matching_vote)
                    })
        
        return {
            'inconsistencies': inconsistencies,
            'total_inconsistencies': len(inconsistencies),
            'inconsistency_rate': len(inconsistencies) / len(statement_positions) if statement_positions else 0,
            'high_severity_count': sum(1 for inc in inconsistencies if inc['severity'] == 'high')
        }
```

## Bias Detection and Analysis

### Multi-dimensional Bias Analysis
```python
class BiasDetectionAnalyzer:
    def __init__(self):
        self.partisan_bias_threshold = 0.3
        self.geographic_bias_threshold = 0.25
        self.temporal_bias_threshold = 0.2
    
    def analyze_comprehensive_bias(self, member_data):
        """
        Comprehensive bias analysis across multiple dimensions
        """
        # Partisan bias
        partisan_bias = self.analyze_partisan_bias(member_data['voting_record'])
        
        # Geographic bias
        geographic_bias = self.analyze_geographic_bias(member_data['constituency_data'])
        
        # Temporal bias
        temporal_bias = self.analyze_temporal_bias(member_data['time_series_data'])
        
        # Text bias
        text_bias = self.analyze_text_bias(member_data['public_statements'])
        
        # Demographic bias
        demographic_bias = self.analyze_demographic_bias(member_data['voting_patterns'])
        
        # Combine bias scores
        overall_bias = self.calculate_overall_bias(
            partisan_bias, geographic_bias, temporal_bias, text_bias, demographic_bias
        )
        
        return {
            'overall_bias_score': overall_bias,
            'bias_dimensions': {
                'partisan_bias': partisan_bias,
                'geographic_bias': geographic_bias,
                'temporal_bias': temporal_bias,
                'text_bias': text_bias,
                'demographic_bias': demographic_bias
            },
            'bias_trend': self.calculate_bias_trend(member_data['historical_bias']),
            'risk_assessment': self.assess_bias_risk(overall_bias),
            'recommendations': self.generate_bias_recommendations(overall_bias)
        }
    
    def analyze_partisan_bias(self, voting_record):
        """
        Analyze partisan bias in voting patterns
        """
        # Calculate party-line voting rate
        party_line_votes = 0
        total_votes = len(voting_record)
        
        for vote in voting_record:
            if self.is_party_line_vote(vote):
                party_line_votes += 1
        
        party_line_rate = party_line_votes / total_votes if total_votes > 0 else 0
        
        # Calculate cross-party cooperation
        cross_party_votes = sum(1 for vote in voting_record if self.is_cross_party_vote(vote))
        cross_party_rate = cross_party_votes / total_votes if total_votes > 0 else 0
        
        # Calculate ideological extremity
        ideological_positions = [self.extract_ideological_position(vote) for vote in voting_record]
        extremity_score = self.calculate_ideological_extremity(ideological_positions)
        
        return {
            'party_line_rate': party_line_rate,
            'cross_party_rate': cross_party_rate,
            'ideological_extremity': extremity_score,
            'partisan_bias_score': (party_line_rate + extremity_score) / 2,
            'bias_level': self.categorize_bias_level(party_line_rate + extremity_score)
        }
    
    def analyze_text_bias(self, statements):
        """
        Analyze bias in public statements
        """
        if not statements:
            return {'text_bias_score': 0.5, 'bias_indicators': []}
        
        # Use bias detection model
        bias_scores = []
        emotional_language = []
        framing_techniques = []
        
        for statement in statements:
            # Bias detection
            bias_result = self.detect_statement_bias(statement['text'])
            bias_scores.append(bias_result['bias_score'])
            
            # Emotional language analysis
            emotion_result = self.analyze_emotional_language(statement['text'])
            emotional_language.append(emotion_result)
            
            # Framing analysis
            framing_result = self.analyze_framing_techniques(statement['text'])
            framing_techniques.append(framing_result)
        
        return {
            'text_bias_score': np.mean(bias_scores),
            'bias_variance': np.var(bias_scores),
            'emotional_language_avg': np.mean([el['intensity'] for el in emotional_language]),
            'framing_bias_count': sum(1 for ft in framing_techniques if ft['biased']),
            'bias_trend': self.calculate_text_bias_trend(bias_scores),
            'problematic_statements': self.identify_problematic_statements(
                statements, bias_scores, emotional_language, framing_techniques
            )
        }
```

## Implementation Examples

### Complete Member Analysis Pipeline
```python
class MemberBehaviorAnalyzer:
    def __init__(self):
        self.dw_nominate = DWNominateAnalyzer()
        self.temporal_analyzer = TemporalBehaviorAnalyzer()
        self.network_analyzer = VotingNetworkAnalyzer()
        self.honesty_assessor = HonestyAssessment()
        self.bias_detector = BiasDetectionAnalyzer()
    
    def comprehensive_member_analysis(self, member_id, analysis_period='2years'):
        """
        Complete behavioral analysis for a member
        """
        # Retrieve member data
        member_data = self.get_member_comprehensive_data(member_id, analysis_period)
        
        # 1. Ideological Analysis
        ideological_analysis = self.dw_nominate.calculate_ideological_scores(
            member_data['voting_matrix']
        )
        
        # 2. Temporal Consistency
        temporal_analysis = self.temporal_analyzer.analyze_temporal_patterns(member_data)
        
        # 3. Network Analysis
        voting_network = self.network_analyzer.build_voting_network(member_data['session_data'])
        network_analysis = self.network_analyzer.detect_voting_blocs(voting_network)
        
        # 4. Honesty Assessment
        honesty_analysis = self.honesty_assessor.assess_honesty(member_data)
        
        # 5. Bias Analysis
        bias_analysis = self.bias_detector.analyze_comprehensive_bias(member_data)
        
        # 6. Risk Assessment
        risk_assessment = self.conduct_risk_assessment(
            ideological_analysis, temporal_analysis, honesty_analysis, bias_analysis
        )
        
        # Compile comprehensive report
        comprehensive_report = {
            'member_id': member_id,
            'analysis_period': analysis_period,
            'analysis_timestamp': datetime.now().isoformat(),
            'ideological_analysis': ideological_analysis,
            'temporal_analysis': temporal_analysis,
            'network_analysis': network_analysis,
            'honesty_analysis': honesty_analysis,
            'bias_analysis': bias_analysis,
            'risk_assessment': risk_assessment,
            'overall_scores': self.calculate_overall_scores(
                ideological_analysis, temporal_analysis, honesty_analysis, bias_analysis
            ),
            'recommendations': self.generate_recommendations(risk_assessment)
        }
        
        # Store results
        self.store_analysis_results(comprehensive_report)
        
        return comprehensive_report
    
    def conduct_risk_assessment(self, ideological, temporal, honesty, bias):
        """
        Conduct comprehensive risk assessment
        """
        risk_factors = []
        
        # Ideological risk
        if ideological['consistency_variance'] > 0.5:
            risk_factors.append({
                'type': 'ideological_instability',
                'severity': 'high',
                'description': 'High variance in ideological positions'
            })
        
        # Temporal risk
        if temporal['overall_stability'] < 0.6:
            risk_factors.append({
                'type': 'temporal_inconsistency',
                'severity': 'medium',
                'description': 'Inconsistent behavior over time'
            })
        
        # Honesty risk
        if honesty['overall_honesty_score'] < 0.5:
            risk_factors.append({
                'type': 'integrity_concerns',
                'severity': 'high',
                'description': 'Low honesty assessment score'
            })
        
        # Bias risk
        if bias['overall_bias_score'] > 0.7:
            risk_factors.append({
                'type': 'high_bias',
                'severity': 'high',
                'description': 'Extremely biased behavior patterns'
            })
        
        # Overall risk level
        risk_level = self.calculate_overall_risk_level(risk_factors)
        
        return {
            'risk_factors': risk_factors,
            'overall_risk_level': risk_level,
            'high_risk_count': sum(1 for rf in risk_factors if rf['severity'] == 'high'),
            'medium_risk_count': sum(1 for rf in risk_factors if rf['severity'] == 'medium'),
            'risk_trend': self.calculate_risk_trend(risk_factors)
        }
```

This comprehensive methodology provides robust frameworks for analyzing legislative member behavior across multiple dimensions including consistency, bias, honesty, and integrity assessments.