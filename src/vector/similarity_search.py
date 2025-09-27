"""
Vector Similarity Search Implementation

This module provides comprehensive vector similarity search capabilities with multiple
distance metrics, hybrid search, and performance optimization for enterprise-scale
semantic search operations.
"""

import time
import math
from typing import List, Dict, Optional, Any, Tuple, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging

import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, desc, func
import psycopg2
import psycopg2.extras

from models.vector_document import VectorDocument, SearchResult
from src.audit.audit_manager import get_audit_manager, AuditContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DistanceMetric(str, Enum):
    """Available distance metrics for vector similarity"""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    MANHATTAN = "manhattan"
    DOT_PRODUCT = "dot_product"
    HAMMING = "hamming"

class SearchType(str, Enum):
    """Types of search operations"""
    SEMANTIC = "semantic"           # Pure vector similarity
    HYBRID = "hybrid"              # Vector + keyword search
    KEYWORD = "keyword"            # Traditional full-text search
    FILTERED = "filtered"          # Vector search with metadata filters

@dataclass
class SearchQuery:
    """Search query parameters"""
    text: str
    search_type: SearchType = SearchType.SEMANTIC
    limit: int = 10
    threshold: float = 0.7
    collection_filter: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    metadata_filters: Dict[str, Any] = field(default_factory=dict)
    distance_metric: DistanceMetric = DistanceMetric.COSINE

@dataclass
class SearchResult:
    """Individual search result"""
    document: VectorDocument
    similarity_score: float
    rank: int
    search_type: SearchType
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_relevant(self, threshold: float = 0.7) -> bool:
        """Check if result meets relevance threshold"""
        return self.similarity_score >= threshold

@dataclass
class SearchResponse:
    """Complete search response"""
    query: SearchQuery
    results: List[SearchResult] = field(default_factory=list)
    total_found: int = 0
    execution_time_ms: float = 0.0
    search_metadata: Dict[str, Any] = field(default_factory=dict)

class VectorSearchEngine:
    """Enterprise-grade vector similarity search engine"""

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.connection = None
        self._initialize_connection()

    def _initialize_connection(self) -> None:
        """Initialize database connection"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            logger.info("Vector search engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize vector search engine: {e}")
            raise

    def _generate_query_embedding(self, query_text: str) -> Optional[List[float]]:
        """Generate embedding for search query"""
        # This would integrate with our embedding generator
        # For now, return a placeholder
        return None

    def _calculate_similarity(
        self,
        vector1: List[float],
        vector2: List[float],
        metric: DistanceMetric = DistanceMetric.COSINE
    ) -> float:
        """Calculate similarity between two vectors"""
        try:
            v1 = np.array(vector1)
            v2 = np.array(vector2)

            if metric == DistanceMetric.COSINE:
                # Cosine similarity: (A·B) / (|A|·|B|)
                dot_product = np.dot(v1, v2)
                norm1 = np.linalg.norm(v1)
                norm2 = np.linalg.norm(v2)
                if norm1 == 0 or norm2 == 0:
                    return 0.0
                return float(dot_product / (norm1 * norm2))

            elif metric == DistanceMetric.EUCLIDEAN:
                # Euclidean distance (converted to similarity)
                distance = np.linalg.norm(v1 - v2)
                return float(1.0 / (1.0 + distance))

            elif metric == DistanceMetric.DOT_PRODUCT:
                # Normalized dot product
                return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

            elif metric == DistanceMetric.MANHATTAN:
                # Manhattan distance (converted to similarity)
                distance = np.sum(np.abs(v1 - v2))
                return float(1.0 / (1.0 + distance))

            else:
                raise ValueError(f"Unsupported distance metric: {metric}")

        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0

    def search_similar_documents(
        self,
        query: SearchQuery,
        query_embedding: Optional[List[float]] = None
    ) -> SearchResponse:
        """
        Search for similar documents using vector similarity

        Args:
            query: Search query parameters
            query_embedding: Pre-computed query embedding (optional)

        Returns:
            SearchResponse with results and metadata
        """
        start_time = time.time()

        if not self.connection:
            self._initialize_connection()

        try:
            # Generate query embedding if not provided
            if query_embedding is None:
                query_embedding = self._generate_query_embedding(query.text)
                if query_embedding is None:
                    return SearchResponse(
                        query=query,
                        execution_time_ms=(time.time() - start_time) * 1000,
                        search_metadata={'error': 'Failed to generate query embedding'}
                    )

            # Build search query
            search_results = []

            if query.search_type == SearchType.SEMANTIC:
                search_results = self._semantic_search(query, query_embedding)
            elif query.search_type == SearchType.HYBRID:
                search_results = self._hybrid_search(query, query_embedding)
            elif query.search_type == SearchType.KEYWORD:
                search_results = self._keyword_search(query)
            elif query.search_type == SearchType.FILTERED:
                search_results = self._filtered_search(query, query_embedding)

            execution_time = (time.time() - start_time) * 1000

            return SearchResponse(
                query=query,
                results=search_results,
                total_found=len(search_results),
                execution_time_ms=execution_time,
                search_metadata={
                    'search_type': query.search_type.value,
                    'distance_metric': query.distance_metric.value,
                    'query_embedding_dimensions': len(query_embedding)
                }
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Search failed: {e}")
            return SearchResponse(
                query=query,
                execution_time_ms=execution_time,
                search_metadata={'error': str(e)}
            )

    def _semantic_search(self, query: SearchQuery, query_embedding: List[float]) -> List[SearchResult]:
        """Perform pure semantic vector search"""
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Use the database function we created in the migration
                cursor.execute("""
                    SELECT * FROM find_similar_documents(
                        %(query_embedding)s::vector,
                        %(threshold)s,
                        %(limit)s,
                        %(collection_filter)s
                    )
                """, {
                    'query_embedding': query_embedding,
                    'threshold': query.threshold,
                    'limit': query.limit,
                    'collection_filter': query.collection_filter
                })

                rows = cursor.fetchall()
                results = []

                for i, row in enumerate(rows):
                    # Convert database result to SearchResult
                    # This would need to be integrated with actual document retrieval
                    result = SearchResult(
                        document=None,  # Would be populated from actual document
                        similarity_score=float(row['similarity']),
                        rank=i + 1,
                        search_type=SearchType.SEMANTIC,
                        metadata={
                            'doc_id': row['doc_id'],
                            'title': row['title'],
                            'content_preview': row['content'][:200] + '...' if row['content'] else ''
                        }
                    )
                    results.append(result)

                return results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def _hybrid_search(self, query: SearchQuery, query_embedding: List[float]) -> List[SearchResult]:
        """Perform hybrid vector + keyword search"""
        try:
            # Combine semantic and keyword search results
            semantic_results = self._semantic_search(query, query_embedding)

            # For now, just return semantic results
            # In a full implementation, this would combine with full-text search
            for result in semantic_results:
                result.search_type = SearchType.HYBRID

            return semantic_results

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

    def _keyword_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform traditional full-text search"""
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Build WHERE clause for filters
                conditions = ["search_vector @@ plainto_tsquery('english', %(query_text)s)"]
                params = {'query_text': query.text}

                if query.collection_filter:
                    conditions.append("collection = %(collection_filter)s")
                    params['collection_filter'] = query.collection_filter

                if query.date_from:
                    conditions.append("created_at >= %(date_from)s")
                    params['date_from'] = query.date_from

                if query.date_to:
                    conditions.append("created_at <= %(date_to)s")
                    params['date_to'] = query.date_to

                where_clause = " AND ".join(conditions)

                # Execute search
                cursor.execute(f"""
                    SELECT
                        id, doc_id, title, content, collection,
                        ts_rank(search_vector, plainto_tsquery('english', %(query_text)s)) as relevance_score
                    FROM master.vector_documents
                    WHERE {where_clause}
                    ORDER BY relevance_score DESC
                    LIMIT %(limit)s
                """, {**params, 'limit': query.limit})

                rows = cursor.fetchall()
                results = []

                for i, row in enumerate(rows):
                    result = SearchResult(
                        document=None,  # Would be populated from actual document
                        similarity_score=float(row['relevance_score']),
                        rank=i + 1,
                        search_type=SearchType.KEYWORD,
                        metadata={
                            'doc_id': row['doc_id'],
                            'title': row['title'],
                            'collection': row['collection']
                        }
                    )
                    results.append(result)

                return results

        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []

    def _filtered_search(self, query: SearchQuery, query_embedding: List[float]) -> List[SearchResult]:
        """Perform filtered vector search with metadata constraints"""
        try:
            # Start with semantic search
            base_results = self._semantic_search(query, query_embedding)

            # Apply additional metadata filters
            filtered_results = []
            for result in base_results:
                # Apply metadata filters if specified
                if self._matches_metadata_filters(result.metadata, query.metadata_filters):
                    filtered_results.append(result)

            # Update ranks after filtering
            for i, result in enumerate(filtered_results):
                result.rank = i + 1
                result.search_type = SearchType.FILTERED

            return filtered_results

        except Exception as e:
            logger.error(f"Filtered search failed: {e}")
            return []

    def _matches_metadata_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if metadata matches filter criteria"""
        for key, expected_value in filters.items():
            if key not in metadata:
                return False
            if metadata[key] != expected_value:
                return False
        return True

    def search_by_document_id(self, doc_id: str) -> Optional[VectorDocument]:
        """Retrieve specific document by ID"""
        if not self.connection:
            self._initialize_connection()

        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM master.vector_documents
                    WHERE doc_id = %s
                """, (doc_id,))

                row = cursor.fetchone()
                if row:
                    return self._row_to_document(row)

        except Exception as e:
            logger.error(f"Failed to retrieve document {doc_id}: {e}")

        return None

    def _row_to_document(self, row: Dict) -> VectorDocument:
        """Convert database row to VectorDocument"""
        # This would need to be implemented based on actual database schema
        # For now, return a placeholder
        return VectorDocument(
            doc_id=row.get('doc_id', ''),
            collection=row.get('collection', ''),
            title=row.get('title', ''),
            content=row.get('content', ''),
            content_vector=row.get('content_vector'),
            metadata=row.get('metadata', {})
        )

    def get_search_statistics(self) -> Dict[str, Any]:
        """Get search performance and usage statistics"""
        if not self.connection:
            self._initialize_connection()

        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Get vector search statistics
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_documents,
                        COUNT(*) FILTER (WHERE content_vector IS NOT NULL) as documents_with_embeddings,
                        AVG(quality_score) as avg_quality_score,
                        COUNT(DISTINCT collection) as unique_collections
                    FROM master.vector_documents
                """)

                stats = cursor.fetchone()

                return {
                    'timestamp': datetime.utcnow().isoformat(),
                    'database_stats': dict(stats) if stats else {},
                    'search_engine_status': 'healthy'
                }

        except Exception as e:
            logger.error(f"Failed to get search statistics: {e}")
            return {'error': str(e)}

    def optimize_search_indexes(self) -> Dict[str, Any]:
        """Optimize vector search indexes for better performance"""
        if not self.connection:
            self._initialize_connection()

        try:
            with self.connection.cursor() as cursor:
                # Analyze current index performance
                cursor.execute("""
                    ANALYZE master.vector_documents;
                """)

                # Get index statistics
                cursor.execute("""
                    SELECT
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan as index_scans,
                        idx_tup_read as tuples_read,
                        idx_tup_fetch as tuples_fetched
                    FROM pg_stat_user_indexes
                    WHERE tablename = 'vector_documents'
                    AND indexname LIKE '%vector%';
                """)

                index_stats = cursor.fetchall()

                return {
                    'timestamp': datetime.utcnow().isoformat(),
                    'optimization_status': 'completed',
                    'index_statistics': index_stats
                }

        except Exception as e:
            logger.error(f"Failed to optimize search indexes: {e}")
            return {'error': str(e)}

class SearchAnalytics:
    """Analytics and monitoring for search operations"""

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.connection = None

    def log_search_event(self, search_response: SearchResponse) -> bool:
        """Log search event for analytics"""
        try:
            # This would log to a search analytics table
            # For now, just log to the audit system
            audit_manager = get_audit_manager(self.db_config)
            return audit_manager.log_event(
                operation="SEARCH",
                table_name="vector_documents",
                record_id=f"search_{int(time.time())}",
                category=audit_manager.AuditCategory.DATA_ACCESS,
                additional_metadata={
                    'search_type': search_response.query.search_type.value,
                    'results_count': len(search_response.results),
                    'execution_time_ms': search_response.execution_time_ms,
                    'threshold': search_response.query.threshold
                }
            )
        except Exception as e:
            logger.error(f"Failed to log search event: {e}")
            return False

    def get_search_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get search analytics and trends"""
        if not self.connection:
            self.connection = psycopg2.connect(**self.db_config)

        try:
            if start_date is None:
                start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            if end_date is None:
                end_date = datetime.utcnow()

            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Get search performance trends
                cursor.execute("""
                    SELECT
                        DATE_TRUNC('hour', created_at) as hour,
                        COUNT(*) as search_count,
                        AVG(execution_time_ms) as avg_execution_time,
                        COUNT(*) FILTER (WHERE results_count > 0) as successful_searches
                    FROM search_analytics
                    WHERE created_at BETWEEN %(start_date)s AND %(end_date)s
                    GROUP BY DATE_TRUNC('hour', created_at)
                    ORDER BY hour
                """, {'start_date': start_date, 'end_date': end_date})

                trends = cursor.fetchall()

                return {
                    'period': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat()
                    },
                    'search_trends': [dict(row) for row in trends],
                    'generated_at': datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Failed to get search analytics: {e}")
            return {'error': str(e)}

# Global search engine instance
_search_engine: Optional[VectorSearchEngine] = None

def get_search_engine(db_config: Dict[str, Any]) -> VectorSearchEngine:
    """Get or create global search engine instance"""
    global _search_engine
    if _search_engine is None:
        _search_engine = VectorSearchEngine(db_config)
    return _search_engine

def search_documents(
    query_text: str,
    search_type: str = "semantic",
    limit: int = 10,
    threshold: float = 0.7,
    collection: Optional[str] = None,
    **kwargs
) -> SearchResponse:
    """Convenience function for document search"""
    query = SearchQuery(
        text=query_text,
        search_type=SearchType(search_type),
        limit=limit,
        threshold=threshold,
        collection_filter=collection,
        **kwargs
    )

    engine = get_search_engine(kwargs.get('db_config', {}))
    return engine.search_similar_documents(query)

def find_similar_documents(
    source_doc_id: str,
    limit: int = 10,
    threshold: float = 0.7,
    collection: Optional[str] = None
) -> List[SearchResult]:
    """Find documents similar to a source document"""
    # This would retrieve the source document's embedding and search
    # For now, return empty list
    return []
