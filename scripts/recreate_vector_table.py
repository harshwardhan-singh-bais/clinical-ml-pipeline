"""
Fix Database Schema: Recreate Table with Proper VECTOR Type
============================================================

PROBLEM: Embeddings are stored as TEXT instead of VECTOR type.
SOLUTION: Drop and recreate table with proper pgvector VECTOR type.

WARNING: This will DELETE all existing data!

Run: python scripts/recreate_vector_table.py
"""

import os
import sys
import psycopg2

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.settings import settings

DATABASE_URL = os.getenv("DATABASE_URL", settings.DATABASE_URL)

# SQL to recreate table with proper VECTOR type
RECREATE_SQL = f"""
-- Drop existing table
DROP TABLE IF EXISTS statpearls_embeddings CASCADE;

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table with PROPER VECTOR type
CREATE TABLE statpearls_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    embedding VECTOR({settings.EMBEDDING_DIMENSION}) NOT NULL,
    content TEXT NOT NULL,
    title TEXT,
    chunk_id TEXT UNIQUE NOT NULL,
    section_type TEXT,
    source TEXT DEFAULT 'statpearls',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create HNSW index for fast similarity search
CREATE INDEX statpearls_embeddings_hnsw_idx
ON statpearls_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Create indexes on metadata
CREATE INDEX statpearls_embeddings_section_idx
ON statpearls_embeddings (section_type);

CREATE INDEX statpearls_embeddings_chunk_id_idx
ON statpearls_embeddings (chunk_id);

-- Recreate RPC function with correct threshold
CREATE OR REPLACE FUNCTION match_statpearls_embeddings(
    query_embedding VECTOR({settings.EMBEDDING_DIMENSION}),
    match_count INT DEFAULT 10,
    similarity_threshold FLOAT DEFAULT 0.15
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
    print("=" * 80)
    print("⚠️  WARNING: RECREATING DATABASE TABLE")
    print("=" * 80)
    print("\nThis will:")
    print("  1. DROP the existing statpearls_embeddings table")
    print("  2. DELETE all 2000 existing records")
    print("  3. Recreate table with proper VECTOR(768) type")
    print("  4. Recreate RPC function")
    print("\nYou will need to re-run ingestion after this.")
    print("\n" + "=" * 80)
    
    response = input("\nType 'YES' to proceed: ")
    
    if response != "YES":
        print("❌ Aborted")
        return
    
    print("\n🔧 Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()
    
    print("🔧 Executing schema recreation...")
    cur.execute(RECREATE_SQL)
    
    print("\n✅ Table recreated successfully!")
    print("=" * 80)
    print("Schema:")
    print("  • Table: statpearls_embeddings")
    print(f"  • Embedding column: VECTOR({settings.EMBEDDING_DIMENSION})")
    print("  • HNSW index: CREATED")
    print("  • RPC function: CREATED (threshold=0.15)")
    print("=" * 80)
    
    cur.close()
    conn.close()
    
    print("\n📋 NEXT STEPS:")
    print("  1. Run ingestion: python scripts/run_test_ingestion.py")
    print("  2. Verify: python scripts/test_retrieval_relevance.py")
    print()

if __name__ == "__main__":
    main()
