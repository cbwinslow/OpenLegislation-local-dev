# Vector Database Implementation Guide

## Overview

This guide provides detailed implementation instructions for vector databases in legislative data analysis, focusing on PostgreSQL with pgvector and alternative cloud solutions.

## PostgreSQL with pgvector Setup

### Installation

```bash
# Install PostgreSQL with pgvector
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib
sudo apt-get install postgresql-15-pgvector

# macOS with Homebrew
brew install postgresql@15
brew install pgvector

# Compile from source
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### Database Configuration

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create legislative database
CREATE DATABASE legislative_analysis;
\c legislative_analysis;

-- Enable extension in the database
CREATE EXTENSION IF NOT EXISTS vector;
```

### Schema Design

#### Document Storage
```sql
-- Legislative documents with embeddings
CREATE TABLE legislative_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_system VARCHAR(50) NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    author_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Text embeddings for similarity search
CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES legislative_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(768) NOT NULL, -- BERT base dimension
    model_version VARCHAR(20) NOT NULL DEFAULT 'bert-base-uncased',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for efficient similarity search
CREATE INDEX ON document_embeddings 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

#### Member Behavior Analysis
```sql
-- Member profiles and behavior vectors
CREATE TABLE members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bioguide_id VARCHAR(20) UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    party VARCHAR(50),
    state VARCHAR(2),
    district VARCHAR(10),
    chamber VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Voting pattern embeddings
CREATE TABLE member_voting_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    session_id VARCHAR(20) NOT NULL,
    voting_pattern vector(512) NOT NULL, -- Custom voting embedding
    consistency_score FLOAT,
    ideological_position POINT, -- 2D ideological space
    voting_bloc_members UUID[], -- Array of similar voting members
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Text consistency embeddings
CREATE TABLE member_text_consistency (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    text_type VARCHAR(50) NOT NULL, -- 'speech', 'statement', 'social_media'
    text_content TEXT NOT NULL,
    embedding vector(768) NOT NULL,
    consistency_score FLOAT,
    sentiment_score FLOAT,
    bias_indicators JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Vector Operations

#### Inserting Embeddings
```sql
-- Insert document embeddings
INSERT INTO document_embeddings (document_id, chunk_index, chunk_text, embedding)
VALUES 
    ('doc-uuid-1', 0, 'First chunk of legislative text', '[0.1, 0.2, ...]'),
    ('doc-uuid-1', 1, 'Second chunk of legislative text', '[0.15, 0.25, ...]');

-- Insert member voting patterns
INSERT INTO member_voting_patterns (member_id, session_id, voting_pattern, consistency_score)
VALUES 
    ('member-uuid-1', '118th', '[0.3, -0.1, 0.8, ...]', 0.85);
```

#### Similarity Search
```sql
-- Find similar documents
SELECT 
    dd.id,
    dd.title,
    dd.content,
    1 - (de.embedding <=> '[0.1, 0.2, 0.3, ...]') as similarity
FROM document_embeddings de
JOIN legislative_documents dd ON de.document_id = dd.id
WHERE 1 - (de.embedding <=> '[0.1, 0.2, 0.3, ...]') > 0.8
ORDER BY similarity DESC
LIMIT 10;

-- Find members with similar voting patterns
SELECT 
    m1.bioguide_id,
    m2.bioguide_id as similar_member,
    1 - (m1.voting_pattern <=> m2.voting_pattern) as similarity
FROM member_voting_patterns m1
JOIN member_voting_patterns m2 ON m1.member_id != m2.member_id
WHERE m1.session_id = '118th' AND m2.session_id = '118th'
  AND 1 - (m1.voting_pattern <=> m2.voting_pattern) > 0.75
ORDER BY similarity DESC;
```

## Python Integration

### Database Connection
```python
import psycopg2
from psycopg2.extras import execute_values
import numpy as np

class VectorDatabase:
    def __init__(self, dbname='legislative_analysis', user='postgres', password='password'):
        self.conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host='localhost',
            port='5432'
        )
        self.conn.autocommit = True
    
    def insert_embedding(self, document_id, chunk_index, text, embedding):
        """Insert text embedding into database"""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO document_embeddings 
                (document_id, chunk_index, chunk_text, embedding)
                VALUES (%s, %s, %s, %s)
            """, (document_id, chunk_index, text, embedding.tolist()))
    
    def similarity_search(self, query_embedding, threshold=0.8, limit=10):
        """Find similar documents using vector similarity"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT dd.title, dd.content, 
                       1 - (de.embedding <=> %s) as similarity
                FROM document_embeddings de
                JOIN legislative_documents dd ON de.document_id = dd.id
                WHERE 1 - (de.embedding <=> %s) > %s
                ORDER BY similarity DESC
                LIMIT %s
            """, (query_embedding.tolist(), query_embedding.tolist(), threshold, limit))
            
            return cur.fetchall()
```

### Embedding Generation
```python
from transformers import AutoTokenizer, AutoModel
import torch

class EmbeddingGenerator:
    def __init__(self, model_name='bert-base-uncased'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
    
    def generate_embedding(self, text):
        """Generate BERT embedding for text"""
        inputs = self.tokenizer(
            text, 
            return_tensors='pt', 
            truncation=True, 
            max_length=512,
            padding=True
        )
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use [CLS] token embedding or mean pooling
            embedding = outputs.last_hidden_state[:, 0, :].squeeze().cpu().numpy()
        
        return embedding
    
    def generate_voting_pattern_embedding(self, votes):
        """Generate custom embedding for voting patterns"""
        # Convert votes to numerical representation
        vote_matrix = self.votes_to_matrix(votes)
        
        # Apply dimensionality reduction or custom encoding
        embedding = self.encode_voting_pattern(vote_matrix)
        
        return embedding
```

## Cloud Vector Databases

### Pinecone Implementation
```python
import pinecone
from sentence_transformers import SentenceTransformer

class PineconeVectorStore:
    def __init__(self, api_key, environment='us-west1-gcp'):
        pinecone.init(api_key=api_key, environment=environment)
        
        # Create index for legislative documents
        self.index_name = "legislative-docs"
        if self.index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=self.index_name,
                dimension=768,
                metric="cosine"
            )
        
        self.index = pinecone.Index(self.index_name)
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
    
    def upsert_documents(self, documents):
        """Upsert document embeddings to Pinecone"""
        embeddings = self.encoder.encode([doc['text'] for doc in documents])
        
        vectors = []
        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            vectors.append({
                'id': f"doc-{doc['id']}",
                'values': embedding.tolist(),
                'metadata': {
                    'title': doc['title'],
                    'source': doc['source'],
                    'type': doc['type']
                }
            })
        
        self.index.upsert(vectors=vectors, namespace='legislative')
    
    def search_similar(self, query, top_k=10):
        """Search for similar documents"""
        query_embedding = self.encoder.encode([query])[0]
        
        results = self.index.query(
            vector=query_embedding.tolist(),
            top_k=top_k,
            include_metadata=True,
            namespace='legislative'
        )
        
        return results['matches']
```

### Weaviate Implementation
```python
import weaviate

class WeaviateVectorStore:
    def __init__(self, url='http://localhost:8080'):
        self.client = weaviate.Client(url)
        
        # Define schema for legislative documents
        schema = {
            "class": "LegislativeDocument",
            "description": "Legislative document with text and embeddings",
            "vectorizer": "none",  # We'll provide our own embeddings
            "moduleConfig": {
                "text2vec-openai": {
                    "model": "ada",
                    "type": "text"
                }
            },
            "properties": [
                {
                    "name": "title",
                    "dataType": ["text"],
                    "description": "Document title"
                },
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Document content"
                },
                {
                    "name": "source",
                    "dataType": ["string"],
                    "description": "Source system"
                },
                {
                    "name": "documentType",
                    "dataType": ["string"],
                    "description": "Type of legislative document"
                }
            ]
        }
        
        self.client.schema.create_class(schema)
    
    def add_document(self, doc_id, title, content, embedding, source, doc_type):
        """Add document with embedding to Weaviate"""
        data_object = {
            "title": title,
            "content": content,
            "source": source,
            "documentType": doc_type
        }
        
        self.client.data_object.create(
            data_object=data_object,
            class_name="LegislativeDocument",
            uuid=doc_id,
            vector=embedding.tolist()
        )
    
    def semantic_search(self, query_embedding, limit=10):
        """Search documents by semantic similarity"""
        result = self.client.query.get(
            "LegislativeDocument",
            ["title", "content", "source", "documentType"],
            vector=query_embedding.tolist(),
            limit=limit
        )
        
        return result['data']['Get']['LegislativeDocument']
```

## Performance Optimization

### Indexing Strategies
```sql
-- IVFFlat index for large datasets
CREATE INDEX CONCURRENTLY document_embedding_idx 
ON document_embeddings 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 1000);

-- HNSW index for better recall
CREATE INDEX CONCURRENTLY document_embedding_hnsw_idx 
ON document_embeddings 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);
```

### Batch Operations
```python
def batch_insert_embeddings(self, embeddings_data, batch_size=1000):
    """Efficiently insert multiple embeddings"""
    values_list = [
        (doc_id, chunk_idx, text, embedding.tolist())
        for doc_id, chunk_idx, text, embedding in embeddings_data
    ]
    
    with self.conn.cursor() as cur:
        execute_values(
            cur,
            """
                INSERT INTO document_embeddings 
                (document_id, chunk_index, chunk_text, embedding)
                VALUES %s
            """,
            values_list,
            template=None,
            page_size=batch_size
        )
```

### Connection Pooling
```python
from psycopg2 import pool

class VectorDatabasePool:
    def __init__(self, min_conn=1, max_conn=10, **db_params):
        self.pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=min_conn,
            maxconn=max_conn,
            **db_params
        )
    
    def get_connection(self):
        return self.pool.getconn()
    
    def put_connection(self, conn):
        self.pool.putconn(conn)
    
    def close_all(self):
        self.pool.closeall()
```

## Monitoring and Maintenance

### Performance Metrics
```sql
-- Monitor index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE tablename IN ('document_embeddings', 'member_voting_patterns');

-- Monitor vector operation performance
EXPLAIN (ANALYZE, BUFFERS) 
SELECT dd.title, 1 - (de.embedding <=> '[0.1, 0.2, 0.3]') as similarity
FROM document_embeddings de
JOIN legislative_documents dd ON de.document_id = dd.id
WHERE 1 - (de.embedding <=> '[0.1, 0.2, 0.3]') > 0.8
ORDER BY similarity DESC
LIMIT 10;
```

### Backup and Recovery
```bash
# Backup vector data
pg_dump -h localhost -U postgres -d legislative_analysis \
    -t document_embeddings -t member_voting_patterns \
    -f vector_backup.sql

# Restore vector data
psql -h localhost -U postgres -d legislative_analysis -f vector_backup.sql
```

## Security Considerations

### Access Control
```sql
-- Create role for vector operations
CREATE ROLE vector_analyst;
GRANT SELECT ON legislative_documents TO vector_analyst;
GRANT SELECT ON document_embeddings TO vector_analyst;
GRANT SELECT ON member_voting_patterns TO vector_analyst;

-- Row-level security for sensitive data
ALTER TABLE member_text_consistency ENABLE ROW LEVEL SECURITY;
CREATE POLICY member_data_policy ON member_text_consistency
    FOR ALL TO vector_analyst
    USING (member_id IN (SELECT id FROM members WHERE bioguide_id = current_user));
```

### Data Encryption
```python
# Encrypt sensitive embeddings before storage
from cryptography.fernet import Fernet

class SecureVectorStore:
    def __init__(self, key):
        self.cipher = Fernet(key)
    
    def encrypt_embedding(self, embedding):
        """Encrypt embedding before storage"""
        embedding_bytes = embedding.tobytes()
        return self.cipher.encrypt(embedding_bytes)
    
    def decrypt_embedding(self, encrypted_embedding):
        """Decrypt embedding after retrieval"""
        decrypted_bytes = self.cipher.decrypt(encrypted_embedding)
        return np.frombuffer(decrypted_bytes, dtype=np.float32)
```

This implementation guide provides the foundation for vector database operations in legislative analysis, supporting both local PostgreSQL deployments and cloud-based solutions.