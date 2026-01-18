"""
Diagnostic Script: Check What's Actually in the Database
=========================================================

This script will:
1. Show sample chunks from the database
2. Test direct text search (no embeddings)
3. Test with threshold = 0.0 (show ANY results)
4. Show actual similarity scores

Run: python scripts/diagnose_retrieval.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.db import SupabaseVectorStore
from utils.embeddings import SentenceTransformerEmbeddings
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("=" * 80)
    print("🔍 DIAGNOSTIC: Database Content & Retrieval Test")
    print("=" * 80)
    
    # Initialize
    vector_store = SupabaseVectorStore()
    embeddings = SentenceTransformerEmbeddings()
    
    # Test 1: Count total rows
    print("\n1️⃣ Checking total rows in database...")
    try:
        response = vector_store.client.table("statpearls_embeddings").select("id", count="exact").execute()
        print(f"✅ Total rows: {response.count}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 2: Show sample titles
    print("\n2️⃣ Sample titles in database (first 10)...")
    try:
        response = vector_store.client.table("statpearls_embeddings")\
            .select("title, section_type, chunk_id")\
            .limit(10)\
            .execute()
        
        for i, row in enumerate(response.data, 1):
            print(f"  [{i}] {row.get('title')} ({row.get('section_type')})")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Direct text search for "Heart Failure"
    print("\n3️⃣ Direct text search for 'Heart Failure'...")
    try:
        response = vector_store.client.table("statpearls_embeddings")\
            .select("title, content")\
            .ilike("content", "%heart failure%")\
            .limit(3)\
            .execute()
        
        print(f"✅ Found {len(response.data)} chunks with 'heart failure' in content")
        for i, row in enumerate(response.data, 1):
            print(f"  [{i}] {row.get('title')}")
            print(f"      Content preview: {row.get('content')[:150]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Semantic search with threshold = 0.0 (show everything)
    print("\n4️⃣ Semantic search with threshold = 0.0 (show ANY match)...")
    query = "Evidence of Heart Failure exacerbation with orthopnea"
    
    try:
        # Embed query
        query_embedding = embeddings.embed_query(query)
        print(f"✅ Query embedded (dim: {len(query_embedding)})")
        
        # Search with threshold = 0.0
        results = vector_store.similarity_search(
            query_embedding=query_embedding,
            top_k=5,
            threshold=0.0  # Show ANYTHING
        )
        
        print(f"✅ Retrieved {len(results)} results")
        
        if results:
            print("\n📊 Top results:")
            for i, result in enumerate(results, 1):
                print(f"\n  [{i}] Similarity: {result.get('similarity_score', 0):.4f}")
                print(f"      Title: {result.get('title')}")
                print(f"      Section: {result.get('section_type')}")
                print(f"      Content: {result.get('text', '')[:150]}...")
        else:
            print("❌ NO RESULTS EVEN WITH THRESHOLD = 0.0")
            print("   This means the RPC function is not returning anything!")
            
    except Exception as e:
        print(f"❌ Error during semantic search: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Check if embeddings are actually stored
    print("\n5️⃣ Checking if embeddings are actually in the database...")
    try:
        response = vector_store.client.table("statpearls_embeddings")\
            .select("chunk_id, embedding")\
            .limit(1)\
            .execute()
        
        if response.data and response.data[0].get('embedding'):
            emb = response.data[0]['embedding']
            print(f"✅ Embeddings ARE stored (sample length: {len(emb) if isinstance(emb, list) else 'N/A'})")
        else:
            print("❌ Embeddings are NULL or missing!")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
