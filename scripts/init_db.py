"""
Database Initialization Script for Supabase + pgvector (StatPearls)

- Enables pgvector extension
- Creates statpearls_embeddings table
- Creates HNSW vector index
- Creates similarity search function

Run: python scripts/init_db.py
"""

import os
import sys
import psycopg2
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.settings import settings

# Use DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL", settings.DATABASE_URL)

# SQL statements for StatPearls
CREATE_SQL = f"""
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS statpearls_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    embedding VECTOR({settings.EMBEDDING_DIMENSION}) NOT NULL,
    content TEXT NOT NULL,
    title TEXT,
    chunk_id TEXT UNIQUE NOT NULL,
    section_type TEXT,
    source TEXT DEFAULT 'statpearls',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS statpearls_embeddings_hnsw_idx
ON statpearls_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS statpearls_embeddings_section_idx
ON statpearls_embeddings (section_type);

CREATE INDEX IF NOT EXISTS statpearls_embeddings_chunk_id_idx
ON statpearls_embeddings (chunk_id);

-- Create similarity search function
CREATE OR REPLACE FUNCTION match_statpearls_embeddings(
    query_embedding VECTOR({settings.EMBEDDING_DIMENSION}),
    match_count INT DEFAULT 10,
    similarity_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    title TEXT,
    chunk_id TEXT,
    section_type TEXT,
    source TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        statpearls_embeddings.id,
        statpearls_embeddings.content,
        statpearls_embeddings.title,
        statpearls_embeddings.chunk_id,
        statpearls_embeddings.section_type,
        statpearls_embeddings.source,
        1 - (statpearls_embeddings.embedding <=> query_embedding) AS similarity
    FROM statpearls_embeddings
    WHERE 1 - (statpearls_embeddings.embedding <=> query_embedding) > similarity_threshold
    ORDER BY statpearls_embeddings.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
"""

def main():
    print("=" * 60)
    print("StatPearls Database Initialization")
    print("=" * 60)
    print("Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()
    print("Running database initialization SQL...")
    cur.execute(CREATE_SQL)
    print("✓ pgvector extension enabled")
    print("✓ statpearls_embeddings table created")
    print("✓ HNSW index created")
    print("✓ Similarity search function created")
    print("=" * 60)
    print("Database initialization complete!")
    print("=" * 60)
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
