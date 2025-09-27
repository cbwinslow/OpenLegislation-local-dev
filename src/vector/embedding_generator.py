"""
Vector Embedding Generation Pipeline

This module provides comprehensive vector embedding generation capabilities using both
OpenAI's API and local Sentence-BERT models, with caching, batching, and performance optimization.
"""

import os
import json
import time
import hashlib
from typing import List, Dict, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging

import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, desc, func
import psycopg2
import psycopg2.extras

# Embedding providers
try:
    import openai
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI not available. Install with 'pip install openai'")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("Warning: SentenceTransformers not available. Install with 'pip install sentence-transformers'")

from models.vector_document import VectorDocument, VectorMetadata, ProcessingStatus
from src.audit.audit_manager import get_audit_manager, AuditContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingProvider(str, Enum):
    """Available embedding providers"""
    OPENAI = "openai"
    SENTENCE_BERT = "sentence_bert"
    LOCAL_BERT = "local_bert"

class EmbeddingModel(str, Enum):
    """Available embedding models"""
    # OpenAI models
    TEXT_EMBEDDING_ADA_002 = "text-embedding-ada-002"  # 1536 dimensions
    TEXT_EMBEDDING_3_SMALL = "text-embedding-3-small"   # 1536 dimensions
    TEXT_EMBEDDING_3_LARGE = "text-embedding-3-large"   # 3072 dimensions

    # Sentence-BERT models
    ALL_MINILM_L6_V2 = "all-MiniLM-L6-v2"              # 384 dimensions
    ALL_MPNET_BASE_V2 = "all-mpnet-base-v2"            # 768 dimensions
    PARAPHRASE_MULTILINGUAL_MPNET_BASE_V2 = "paraphrase-multilingual-mpnet-base-v2"  # 768 dimensions

@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation"""
    provider: EmbeddingProvider = EmbeddingProvider.SENTENCE_BERT
    model: EmbeddingModel = EmbeddingModel.ALL_MINILM_L6_V2
    api_key: Optional[str] = None
    batch_size: int = 100
    max_retries: int = 3
    retry_delay: float = 1.0
    cache_enabled: bool = True
    cache_ttl_hours: int = 24
    normalize_vectors: bool = True
    dimensions: int = 384

    # Performance settings
    rate_limit_per_minute: int = 60
    timeout_seconds: int = 30

    # Quality settings
    min_text_length: int = 10
    max_text_length: int = 8192

@dataclass
class EmbeddingResult:
    """Result of embedding generation"""
    vector: List[float]
    model_used: str
    dimensions: int
    processing_time_ms: float
    cached: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BatchEmbeddingResult:
    """Result of batch embedding generation"""
    total_processed: int
    successful: int
    failed: int
    cached: int
    total_time_ms: float
    results: List[EmbeddingResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

class EmbeddingCache:
    """Cache for generated embeddings to avoid redundant API calls"""

    def __init__(self, db_config: Dict[str, Any], ttl_hours: int = 24):
        self.db_config = db_config
        self.ttl_hours = ttl_hours
        self.connection = None
        self._initialize_cache()

    def _initialize_cache(self) -> None:
        """Initialize cache table if it doesn't exist"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS master.embedding_cache (
                        id BIGSERIAL PRIMARY KEY,
                        text_hash VARCHAR(64) NOT NULL UNIQUE,
                        text_preview TEXT,
                        embedding_vector TEXT NOT NULL, -- JSON array as string
                        model_name VARCHAR(100) NOT NULL,
                        dimensions INTEGER NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        access_count INTEGER DEFAULT 1,
                        last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_embedding_cache_hash
                    ON master.embedding_cache(text_hash)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_embedding_cache_accessed
                    ON master.embedding_cache(last_accessed)
                """)
            self.connection.commit()
            logger.info("Embedding cache initialized")
        except Exception as e:
            logger.error(f"Failed to initialize embedding cache: {e}")
            raise

    def get(self, text_hash: str) -> Optional[List[float]]:
        """Retrieve cached embedding"""
        if not self.connection:
            self._initialize_cache()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT embedding_vector, access_count
                    FROM master.embedding_cache
                    WHERE text_hash = %s
                    AND created_at > NOW() - INTERVAL '%s hours'
                """, (text_hash, self.ttl_hours))

                row = cursor.fetchone()
                if row:
                    # Update access statistics
                    cursor.execute("""
                        UPDATE master.embedding_cache
                        SET access_count = access_count + 1,
                            last_accessed = NOW()
                        WHERE text_hash = %s
                    """, (text_hash,))
                    self.connection.commit()

                    return json.loads(row[0])
        except Exception as e:
            logger.error(f"Failed to retrieve from cache: {e}")

        return None

    def put(self, text_hash: str, vector: List[float], model_name: str, dimensions: int) -> bool:
        """Store embedding in cache"""
        if not self.connection:
            self._initialize_cache()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO master.embedding_cache
                    (text_hash, embedding_vector, model_name, dimensions)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (text_hash) DO UPDATE SET
                    access_count = embedding_cache.access_count + 1,
                    last_accessed = NOW()
                """, (text_hash, json.dumps(vector), model_name, dimensions))
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to store in cache: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    def cleanup(self, max_age_hours: Optional[int] = None) -> int:
        """Clean up old cache entries"""
        if max_age_hours is None:
            max_age_hours = self.ttl_hours * 2  # Clean up entries older than 2x TTL

        if not self.connection:
            self._initialize_cache()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM master.embedding_cache
                    WHERE created_at < NOW() - INTERVAL '%s hours'
                """, (max_age_hours,))
                deleted_count = cursor.rowcount
            self.connection.commit()
            logger.info(f"Cleaned up {deleted_count} old cache entries")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to cleanup cache: {e}")
            return 0

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.connection:
            self._initialize_cache()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_entries,
                        AVG(access_count) as avg_access_count,
                        MAX(created_at) as latest_entry,
                        MIN(created_at) as oldest_entry
                    FROM master.embedding_cache
                    WHERE created_at > NOW() - INTERVAL '%s hours'
                """, (self.ttl_hours,))

                row = cursor.fetchone()
                return dict(row) if row else {}
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}

class OpenAIEmbeddingGenerator:
    """OpenAI embedding generator with async support and rate limiting"""

    def __init__(self, api_key: str, config: EmbeddingConfig):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not available")
        if not api_key:
            raise ValueError("API key required for OpenAI embeddings")

        self.client = AsyncOpenAI(api_key=api_key)
        self.config = config
        self._rate_limit_window = []
        self._semaphore = asyncio.Semaphore(10)  # Limit concurrent requests

    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting"""
        now = time.time()
        # Clean old requests from window
        self._rate_limit_window = [t for t in self._rate_limit_window if now - t < 60]

        if len(self._rate_limit_window) >= self.config.rate_limit_per_minute:
            sleep_time = 60 - (now - self._rate_limit_window[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        self._rate_limit_window.append(now)

    async def generate_embedding(self, text: str) -> Optional[EmbeddingResult]:
        """Generate embedding for single text"""
        async with self._semaphore:
            await self._check_rate_limit()

            start_time = time.time()
            try:
                response = await asyncio.wait_for(
                    self.client.embeddings.create(
                        input=text,
                        model=self.config.model.value
                    ),
                    timeout=self.config.timeout_seconds
                )

                vector = response.data[0].embedding
                processing_time = (time.time() - start_time) * 1000

                return EmbeddingResult(
                    vector=vector,
                    model_used=self.config.model.value,
                    dimensions=len(vector),
                    processing_time_ms=processing_time,
                    metadata={
                        'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else None,
                        'provider': 'openai'
                    }
                )

            except Exception as e:
                processing_time = (time.time() - start_time) * 1000
                logger.error(f"OpenAI embedding generation failed: {e}")
                return EmbeddingResult(
                    vector=[],
                    model_used=self.config.model.value,
                    dimensions=0,
                    processing_time_ms=processing_time,
                    error=str(e)
                )

    async def generate_batch_embeddings(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings for batch of texts"""
        # Split into chunks based on batch size
        results = []
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i:i + self.config.batch_size]
            batch_results = await self._generate_batch_chunk(batch)
            results.extend(batch_results)
            # Small delay between batches to respect rate limits
            await asyncio.sleep(0.1)

        return results

    async def _generate_batch_chunk(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings for a single batch chunk"""
        async with self._semaphore:
            await self._check_rate_limit()

            start_time = time.time()
            try:
                response = await asyncio.wait_for(
                    self.client.embeddings.create(
                        input=texts,
                        model=self.config.model.value
                    ),
                    timeout=self.config.timeout_seconds * len(texts) // 10 + 10
                )

                processing_time = (time.time() - start_time) * 1000
                results = []

                for i, data in enumerate(response.data):
                    results.append(EmbeddingResult(
                        vector=data.embedding,
                        model_used=self.config.model.value,
                        dimensions=len(data.embedding),
                        processing_time_ms=processing_time / len(texts),
                        metadata={
                            'batch_index': i,
                            'tokens_used': data.usage.total_tokens if hasattr(data, 'usage') else None,
                            'provider': 'openai'
                        }
                    ))

                return results

            except Exception as e:
                processing_time = (time.time() - start_time) * 1000
                logger.error(f"OpenAI batch embedding generation failed: {e}")
                # Return error results for all texts in batch
                return [
                    EmbeddingResult(
                        vector=[],
                        model_used=self.config.model.value,
                        dimensions=0,
                        processing_time_ms=processing_time / len(texts),
                        error=str(e)
                    ) for _ in texts
                ]

class LocalEmbeddingGenerator:
    """Local embedding generator using Sentence-BERT"""

    def __init__(self, config: EmbeddingConfig):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("SentenceTransformers package not available")

        self.config = config
        self.model = None
        self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize the Sentence-BERT model"""
        try:
            logger.info(f"Loading Sentence-BERT model: {self.config.model.value}")
            self.model = SentenceTransformer(self.config.model.value)
            logger.info("Sentence-BERT model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Sentence-BERT model: {e}")
            raise

    def generate_embedding(self, text: str) -> Optional[EmbeddingResult]:
        """Generate embedding for single text"""
        start_time = time.time()
        try:
            if not self.model:
                self._initialize_model()

            # Generate embedding
            vector = self.model.encode(text, normalize_embeddings=self.config.normalize_vectors)

            processing_time = (time.time() - start_time) * 1000

            return EmbeddingResult(
                vector=vector.tolist(),
                model_used=self.config.model.value,
                dimensions=len(vector),
                processing_time_ms=processing_time,
                metadata={
                    'provider': 'local',
                    'normalized': self.config.normalize_vectors
                }
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Local embedding generation failed: {e}")
            return EmbeddingResult(
                vector=[],
                model_used=self.config.model.value,
                dimensions=0,
                processing_time_ms=processing_time,
                error=str(e)
            )

    def generate_batch_embeddings(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings for batch of texts"""
        try:
            if not self.model:
                self._initialize_model()

            start_time = time.time()

            # Generate embeddings in batch
            vectors = self.model.encode(
                texts,
                batch_size=self.config.batch_size,
                normalize_embeddings=self.config.normalize_vectors
            )

            processing_time = (time.time() - start_time) * 1000
            results = []

            for i, vector in enumerate(vectors):
                results.append(EmbeddingResult(
                    vector=vector.tolist(),
                    model_used=self.config.model.value,
                    dimensions=len(vector),
                    processing_time_ms=processing_time / len(texts),
                    metadata={
                        'batch_index': i,
                        'provider': 'local',
                        'normalized': self.config.normalize_vectors
                    }
                ))

            return results

        except Exception as e:
            logger.error(f"Local batch embedding generation failed: {e}")
            # Return error results for all texts
            return [
                EmbeddingResult(
                    vector=[],
                    model_used=self.config.model.value,
                    dimensions=0,
                    processing_time_ms=0,
                    error=str(e)
                ) for _ in texts
            ]

class EmbeddingGenerator:
    """Main embedding generator with provider selection and caching"""

    def __init__(self, config: EmbeddingConfig, db_config: Dict[str, Any]):
        self.config = config
        self.db_config = db_config
        self.cache = EmbeddingCache(db_config, config.cache_ttl_hours) if config.cache_enabled else None

        # Initialize provider
        self.provider = self._initialize_provider()

    def _initialize_provider(self):
        """Initialize the appropriate embedding provider"""
        if self.config.provider == EmbeddingProvider.OPENAI:
            if not OPENAI_AVAILABLE:
                logger.warning("OpenAI not available, falling back to local embeddings")
                return LocalEmbeddingGenerator(self.config)
            return OpenAIEmbeddingGenerator(self.config.api_key or os.getenv('OPENAI_API_KEY', ''), self.config)

        elif self.config.provider in [EmbeddingProvider.SENTENCE_BERT, EmbeddingProvider.LOCAL_BERT]:
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                raise ImportError("SentenceTransformers required for local embeddings")
            return LocalEmbeddingGenerator(self.config)

        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")

    def _get_text_hash(self, text: str) -> str:
        """Generate hash for text to use as cache key"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for embedding generation"""
        if not text or len(text.strip()) < self.config.min_text_length:
            return ""

        # Truncate if too long
        if len(text) > self.config.max_text_length:
            text = text[:self.config.max_text_length]

        # Basic cleaning
        text = text.strip()
        # Remove excessive whitespace
        text = ' '.join(text.split())

        return text

    def generate_embedding(self, text: str, use_cache: bool = True) -> Optional[EmbeddingResult]:
        """
        Generate embedding for text with caching support

        Args:
            text: Text to generate embedding for
            use_cache: Whether to use cached results

        Returns:
            EmbeddingResult or None if failed
        """
        # Preprocess text
        processed_text = self._preprocess_text(text)
        if not processed_text:
            return EmbeddingResult(
                vector=[],
                model_used=self.config.model.value,
                dimensions=0,
                processing_time_ms=0,
                error="Text too short or empty after preprocessing"
            )

        # Check cache first
        if use_cache and self.cache:
            text_hash = self._get_text_hash(processed_text)
            cached_vector = self.cache.get(text_hash)
            if cached_vector:
                return EmbeddingResult(
                    vector=cached_vector,
                    model_used=self.config.model.value,
                    dimensions=len(cached_vector),
                    processing_time_ms=0,
                    cached=True,
                    metadata={'cache_hit': True}
                )

        # Generate embedding
        if isinstance(self.provider, OpenAIEmbeddingGenerator):
            # Use async for OpenAI
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is already running, we need to handle this differently
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.provider.generate_embedding(processed_text))
                        result = future.result(timeout=30)
                else:
                    result = loop.run_until_complete(self.provider.generate_embedding(processed_text))
            except Exception as e:
                logger.error(f"Async embedding generation failed: {e}")
                result = None
        else:
            # Use sync for local models
            result = self.provider.generate_embedding(processed_text)

        # Cache successful results
        if result and not result.error and result.vector and self.cache:
            text_hash = self._get_text_hash(processed_text)
            self.cache.put(text_hash, result.vector, result.model_used, result.dimensions)

        return result

    def generate_batch_embeddings(self, texts: List[str], use_cache: bool = True) -> BatchEmbeddingResult:
        """
        Generate embeddings for batch of texts

        Args:
            texts: List of texts to process
            use_cache: Whether to use cached results

        Returns:
            BatchEmbeddingResult with results for all texts
        """
        start_time = time.time()
        results = []
        cached_count = 0

        # Preprocess all texts
        processed_texts = [self._preprocess_text(text) for text in texts]

        # Check cache for each text
        texts_to_process = []
        indices_to_process = []

        if use_cache and self.cache:
            for i, processed_text in enumerate(processed_texts):
                if processed_text:
                    text_hash = self._get_text_hash(processed_text)
                    cached_vector = self.cache.get(text_hash)
                    if cached_vector:
                        results.append(EmbeddingResult(
                            vector=cached_vector,
                            model_used=self.config.model.value,
                            dimensions=len(cached_vector),
                            processing_time_ms=0,
                            cached=True,
                            metadata={'cache_hit': True, 'original_index': i}
                        ))
                        cached_count += 1
                    else:
                        texts_to_process.append(processed_text)
                        indices_to_process.append(i)
                else:
                    results.append(EmbeddingResult(
                        vector=[],
                        model_used=self.config.model.value,
                        dimensions=0,
                        processing_time_ms=0,
                        error="Text too short or empty after preprocessing",
                        metadata={'original_index': i}
                    ))
        else:
            texts_to_process = processed_texts
            indices_to_process = list(range(len(processed_texts)))

        # Generate embeddings for non-cached texts
        if texts_to_process:
            if isinstance(self.provider, OpenAIEmbeddingGenerator):
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(
                                asyncio.run,
                                self.provider.generate_batch_embeddings(texts_to_process)
                            )
                            batch_results = future.result(timeout=60)
                    else:
                        batch_results = loop.run_until_complete(
                            self.provider.generate_batch_embeddings(texts_to_process)
                        )
                except Exception as e:
                    logger.error(f"Batch embedding generation failed: {e}")
                    batch_results = [
                        EmbeddingResult(
                            vector=[],
                            model_used=self.config.model.value,
                            dimensions=0,
                            processing_time_ms=0,
                            error=str(e)
                        ) for _ in texts_to_process
                    ]
            else:
                batch_results = self.provider.generate_batch_embeddings(texts_to_process)

            # Map results back to original indices
            for i, result in enumerate(batch_results):
                original_index = indices_to_process[i]
                result.metadata['original_index'] = original_index
                results.append(result)

        # Sort results by original index to maintain order
        results.sort(key=lambda x: x.metadata.get('original_index', 0))

        # Calculate batch statistics
        successful = sum(1 for r in results if not r.error and r.vector)
        failed = sum(1 for r in results if r.error or not r.vector)
        total_time = (time.time() - start_time) * 1000

        return BatchEmbeddingResult(
            total_processed=len(texts),
            successful=successful,
            failed=failed,
            cached=cached_count,
            total_time_ms=total_time,
            results=results,
            errors=[r.error for r in results if r.error]
        )

    def update_document_embeddings(self, documents: List[VectorDocument]) -> BatchEmbeddingResult:
        """
        Update embeddings for documents that need them

        Args:
            documents: List of documents to process

        Returns:
            BatchEmbeddingResult with processing statistics
        """
        # Filter documents that need embeddings
        texts_to_embed = []
        indices_to_embed = []

        for i, doc in enumerate(documents):
            if doc.is_ready_for_embedding():
                # Combine title and content for better embeddings
                text = f"{doc.title} {doc.content}".strip()
                texts_to_embed.append(text)
                indices_to_embed.append(i)

        if not texts_to_embed:
            return BatchEmbeddingResult(
                total_processed=len(documents),
                successful=0,
                failed=0,
                cached=0,
                total_time_ms=0,
                results=[],
                errors=[]
            )

        # Generate embeddings
        batch_result = self.generate_batch_embeddings(texts_to_embed)

        # Update documents with results
        for i, result in enumerate(batch_result.results):
            if not result.error and result.vector:
                original_index = indices_to_embed[i]
                documents[original_index].content_vector = result.vector
                documents[original_index].vector_info = VectorMetadata(
                    embedding_model=result.model_used,
                    embedding_dimensions=result.dimensions,
                    normalized=self.config.normalize_vectors,
                    embedding_time_ms=result.processing_time_ms
                )
                documents[original_index].mark_completed()

        return batch_result

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on embedding generator"""
        health = {
            'provider': self.config.provider.value,
            'model': self.config.model.value,
            'cache_enabled': self.config.cache_enabled,
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat()
        }

        try:
            # Test embedding generation with simple text
            test_result = self.generate_embedding("test", use_cache=False)
            if test_result and not test_result.error:
                health['test_embedding_successful'] = True
                health['test_dimensions'] = test_result.dimensions
            else:
                health['status'] = 'degraded'
                health['error'] = test_result.error if test_result else 'Unknown error'

        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = str(e)

        # Cache statistics
        if self.cache:
            try:
                health['cache_stats'] = self.cache.stats()
            except Exception as e:
                health['cache_error'] = str(e)

        return health

# Global embedding generator instance
_embedding_generator: Optional[EmbeddingGenerator] = None

def get_embedding_generator(
    db_config: Dict[str, Any],
    provider: str = "sentence_bert",
    model: str = "all-MiniLM-L6-v2",
    **kwargs
) -> EmbeddingGenerator:
    """Get or create global embedding generator instance"""
    global _embedding_generator
    if _embedding_generator is None:
        config = EmbeddingConfig(
            provider=EmbeddingProvider(provider),
            model=EmbeddingModel(model),
            **kwargs
        )
        _embedding_generator = EmbeddingGenerator(config, db_config)
    return _embedding_generator

def generate_document_embeddings(documents: List[VectorDocument]) -> BatchEmbeddingResult:
    """Convenience function for generating embeddings for documents"""
    # This would need to be initialized with proper config
    # For now, return a placeholder result
    return BatchEmbeddingResult(
        total_processed=len(documents),
        successful=0,
        failed=len(documents),
        cached=0,
        total_time_ms=0,
        errors=[f"Embedding generator not initialized for {len(documents)} documents"]
    )
