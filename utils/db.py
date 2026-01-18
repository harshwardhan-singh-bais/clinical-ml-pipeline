"""
Supabase + pgvector Database Operations
StatPearls knowledge base storage and retrieval.

CRITICAL RULES:
- pgvector ONLY (no FAISS, no Chroma)
- HNSW index for fast retrieval
- Batched inserts
- StatPearls metadata (title, section_type, source)
"""

from supabase import create_client, Client
from typing import List, Dict, Optional, Tuple
import logging
from config.settings import settings
import numpy as np

logger = logging.getLogger(__name__)


class SupabaseVectorStore:
    """
    Supabase + pgvector integration for StatPearls knowledge base.
    
    Used for:
    - Store StatPearls embeddings (Offline)
    - Retrieve medical evidence (Runtime)
    """
    
    # Table and schema constants
    TABLE_NAME = "statpearls_embeddings"
    EMBEDDING_DIM = 768  # Gemini embedding dimension
    
    def __init__(self):
        """Initialize Supabase client."""
        logger.info("Initializing Supabase client")
        
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        
        # Use service role key for admin operations (indexing)
        self.admin_client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
        
        logger.info("Supabase client initialized successfully")
    
    def create_table_if_not_exists(self):
        """
        Create pgvector table for StatPearls embeddings if it doesn't exist.
        
        Table schema:
        - id: UUID primary key
        - embedding: VECTOR(768) - Gemini embeddings
        - content: TEXT - chunk text
        - title: TEXT - chunk title
        - chunk_id: TEXT - unique chunk identifier
        - section_type: TEXT - section category (differential_diagnosis, etc.)
        - source: TEXT - always "statpearls"
        - created_at: TIMESTAMP
        
        This should be run as a SQL migration, but included here for reference.
        """
        
        # SQL to create table (run manually or via Supabase dashboard)
        create_table_sql = f"""
        -- Enable pgvector extension
        CREATE EXTENSION IF NOT EXISTS vector;
        
        -- Create StatPearls embeddings table
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            embedding VECTOR({self.EMBEDDING_DIM}) NOT NULL,
            content TEXT NOT NULL,
            title TEXT,
            chunk_id TEXT UNIQUE NOT NULL,
            section_type TEXT,
            source TEXT DEFAULT 'statpearls',
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Create HNSW index for fast similarity search
        CREATE INDEX IF NOT EXISTS statpearls_embeddings_hnsw_idx
        ON {self.TABLE_NAME}
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
        
        -- Create index on section_type for faster filtering
        CREATE INDEX IF NOT EXISTS statpearls_embeddings_section_idx
        ON {self.TABLE_NAME} (section_type);
        
        -- Create index on chunk_id for faster lookups
        CREATE INDEX IF NOT EXISTS pmc_embeddings_chunk_id_idx
        ON {self.TABLE_NAME} (chunk_id);
        """
        
        logger.info(f"Table schema for {self.TABLE_NAME}:")
        logger.info(create_table_sql)
        
        return create_table_sql
    
    def insert_embeddings_batch(
        self,
        embeddings: List[List[float]],
        texts: List[str],
        metadata_list: List[Dict[str, str]],
        batch_size: int = 100
    ) -> int:
        """
        Insert StatPearls embeddings using raw PostgreSQL with proper VECTOR type.
        
        CRITICAL: Uses psycopg2 directly to avoid JSON encoding issues.
        
        Args:
            embeddings: List of embedding vectors
            texts: List of chunk texts
            metadata_list: List of metadata dicts (title, section_type, etc.)
            batch_size: Batch size for inserts
        
        Returns:
            Number of embeddings inserted
        """
        if not (len(embeddings) == len(texts) == len(metadata_list)):
            raise ValueError("embeddings, texts, and metadata_list must have same length")
        
        # Import psycopg2 for raw SQL
        import psycopg2
        import os
        
        total_inserted = 0
        
        # Get DATABASE_URL from settings
        database_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)
        
        # Connect using psycopg2
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        try:
            # Process in batches
            for i in range(0, len(embeddings), batch_size):
                batch_embeddings = embeddings[i:i + batch_size]
                batch_texts = texts[i:i + batch_size]
                batch_metadata = metadata_list[i:i + batch_size]
                
                # Use INSERT with ON CONFLICT for upsert
                for emb, text, meta in zip(batch_embeddings, batch_texts, batch_metadata):
                    # Convert embedding list to PostgreSQL array literal string
                    emb_str = '[' + ','.join(str(x) for x in emb) + ']'
                    
                    # Use parameterized query with VECTOR casting
                    cur.execute("""
                        INSERT INTO statpearls_embeddings (embedding, content, title, chunk_id, section_type, source)
                        VALUES (%s::vector, %s, %s, %s, %s, %s)
                        ON CONFLICT (chunk_id) DO UPDATE SET
                            embedding = EXCLUDED.embedding,
                            content = EXCLUDED.content,
                            title = EXCLUDED.title,
                            section_type = EXCLUDED.section_type,
                            source = EXCLUDED.source
                    """, (
                        emb_str,
                        text,
                        meta.get("title"),
                        meta.get("chunk_id"),
                        meta.get("section_type"),
                        meta.get("source", "statpearls")
                    ))
                    total_inserted += 1
               
                # Commit after each batch
                conn.commit()
                logger.info(f"Inserted batch {i // batch_size + 1}: {len(batch_embeddings)} records")
                
        except Exception as e:
            logger.error(f"Error inserting batch: {e}")
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()
        
        logger.info(f"Total embeddings inserted via psycopg2: {total_inserted}")
        return total_inserted
    
    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = None,
        threshold: float = None
    ) -> List[Dict]:
        """
        Perform similarity search on StatPearls embeddings.

        Args:
            query_embedding: Query vector (from clinical note)
            top_k: Number of results to return (default from settings)
            threshold: Similarity threshold (default from settings)

        Returns:
            List of retrieved chunks with metadata and scores
        """
        top_k = top_k or settings.TOP_K_RETRIEVAL
        threshold = threshold or settings.SIMILARITY_THRESHOLD

        try:
            # Use RPC function for similarity search
            # This assumes you've created a stored procedure in Supabase
            # See create_search_function() method below

            params = {
                "query_embedding": query_embedding,
                "match_count": top_k,
                "similarity_threshold": threshold
            }

            response = self.client.rpc(
                "match_statpearls_embeddings",
                params
            ).execute()

            raw_results = response.data if response.data else []
            logger.info(f"Retrieved {len(raw_results)} StatPearls chunks (raw)")

            # Normalize output: map 'content' to 'text'
            results = []
            for row in raw_results:
                # Temporary debug log for keys
                logger.error(f"RAW SQL ROW KEYS: {row.keys()}")
                results.append({
                    "chunk_id": row.get("chunk_id"),
                    "text": row.get("content"),
                    "title": row.get("title"),
                    "section_type": row.get("section_type"),
                    "source": row.get("source", "statpearls"),
                    "similarity_score": row.get("similarity"),  # normalized key
                    "citation": row.get("citation"),
                    "license": row.get("license"),
                    "retracted": row.get("retracted"),
                })

            return results

        except Exception as e:
            logger.error(f"Error during similarity search: {e}")
            return []
    
    def create_search_function(self) -> str:
        """
        SQL function for similarity search.
        
        This should be created in Supabase as a stored procedure.
        Run this SQL in Supabase SQL Editor.
        
        Returns:
            SQL string for the search function
        """
        
        search_function_sql = f"""
        CREATE OR REPLACE FUNCTION match_statpearls_embeddings(
            query_embedding VECTOR({self.EMBEDDING_DIM}),
            match_count INT DEFAULT 10,
            similarity_threshold FLOAT DEFAULT 0.7
        )
        RETURNS TABLE (
            id UUID,
            content TEXT,
            title TEXT,
            license TEXT,
            citation TEXT,
            retracted TEXT,
            chunk_id TEXT,
            source TEXT,
            similarity FLOAT
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
        
        logger.info("Similarity search function SQL:")
        logger.info(search_function_sql)
        
        return search_function_sql
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict]:
        """
        Retrieve a specific chunk by its ID.
        
        Phase 10: Evidence Traceability
        
        Args:
            chunk_id: Unique chunk identifier
        
        Returns:
            Chunk data with metadata
        """
        try:
            response = self.client.table(self.TABLE_NAME).select("*").eq("chunk_id", chunk_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving chunk {chunk_id}: {e}")
            return None
    
    def count_embeddings(self) -> int:
        """
        Count total embeddings in database.
        
        Returns:
            Total count of embeddings
        """
        try:
            response = self.client.table(self.TABLE_NAME).select("id", count="exact").execute()
            return response.count if hasattr(response, 'count') else 0
        except Exception as e:
            logger.error(f"Error counting embeddings: {e}")
            return 0
    
    def delete_all_embeddings(self):
        """
        Delete all embeddings from table.
        
        CAUTION: This will delete all PMC data.
        Use only for re-indexing or testing.
        """
        logger.warning("Deleting all embeddings from database")
        
        try:
            # Delete all records using admin client
            response = self.admin_client.table(self.TABLE_NAME).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            logger.info("All embeddings deleted")
        except Exception as e:
            logger.error(f"Error deleting embeddings: {e}")


# ========== HELPER FUNCTIONS ==========

def format_retrieval_results(
    raw_results: List[Dict]
) -> List[Dict]:
    """
    Format raw database results for use in LLM context.
    
    Phase 10: Evidence Traceability
    
    Args:
        raw_results: Raw results from similarity_search
    
    Returns:
        Formatted results ready for LLM context
    """
    formatted = []

    for r in raw_results:
        score = (
            r.get("similarity_score")
            if r.get("similarity_score") is not None
            else r.get("similarity", 0.0)
        )
        # Optional debug log
        # logger.warning(f"FORMAT SCORE CHECK: {score}")
        formatted.append({
            "chunk_id": r.get("chunk_id"),
            "text": r.get("text"),
            "title": r.get("title"),
            "section_type": r.get("section_type"),
            "source": r.get("source", "statpearls"),
            "similarity_score": float(score),
            "citation": r.get("citation"),
            "license": r.get("license"),
            "retracted": r.get("retracted"),
        })

    return formatted
