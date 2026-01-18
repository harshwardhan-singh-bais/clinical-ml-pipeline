"""
Fix Similarity Threshold in Supabase RPC Function
==================================================

The match_statpearls_embeddings function was created with a default
similarity_threshold of 0.7, which is too high for cross-domain retrieval.

This script updates it to 0.15 (matching settings.py).

Run: python scripts/fix_similarity_threshold.py
"""

import os
import sys
import psycopg2

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.settings import settings

DATABASE_URL = os.getenv("DATABASE_URL", settings.DATABASE_URL)

# Updated SQL with lower threshold
FIX_SQL = f"""
-- Drop old function
DROP FUNCTION IF EXISTS match_statpearls_embeddings(VECTOR, INT, FLOAT);

-- Recreate with lower default threshold
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
    print("=" * 60)
    print("Fixing Similarity Threshold in RPC Function")
    print("=" * 60)
    print(f"New default threshold: {settings.SIMILARITY_THRESHOLD}")
    print()
    
    print("Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()
    
    print("Updating RPC function...")
    cur.execute(FIX_SQL)
    
    print("✓ Function updated successfully!")
    print("=" * 60)
    print("New function signature:")
    print(f"  match_statpearls_embeddings(")
    print(f"    query_embedding VECTOR(768),")
    print(f"    match_count INT DEFAULT 10,")
    print(f"    similarity_threshold FLOAT DEFAULT 0.15  ← UPDATED")
    print(f"  )")
    print("=" * 60)
    
    cur.close()
    conn.close()
    
    print("\n✅ Done! Now run:")
    print("   python scripts/test_retrieval_relevance.py")

if __name__ == "__main__":
    main()
