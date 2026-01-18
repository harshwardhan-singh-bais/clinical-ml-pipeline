"""
Test database connection and check what's in the database
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.db import SupabaseVectorStore
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("="*80)
    print("TESTING DATABASE CONNECTION AND CONTENT")
    print("="*80)
    
    # Initialize vector store
    vector_store = SupabaseVectorStore()
    
    # Test 1: Check table exists
    print("\n1. Checking if statpearls_embeddings table exists...")
    try:
        response = vector_store.client.table("statpearls_embeddings").select("id").limit(1).execute()
        print(f"✓ Table exists. Sample ID: {response.data[0]['id'] if response.data else 'No data'}")
    except Exception as e:
        print(f"✗ Table check failed: {e}")
        return
    
    # Test 2: Count total rows
    print("\n2. Counting total rows in statpearls_embeddings...")
    try:
        response = vector_store.client.table("statpearls_embeddings").select("id", count="exact").execute()
        print(f"✓ Total rows: {response.count}")
    except Exception as e:
        print(f"✗ Count failed: {e}")
    
    # Test 3: Check columns
    print("\n3. Checking table columns (first row)...")
    try:
        response = vector_store.client.table("statpearls_embeddings").select("*").limit(1).execute()
        if response.data:
            print(f"✓ Columns: {list(response.data[0].keys())}")
            print(f"✓ Sample content (first 100 chars): {response.data[0].get('content', '')[:100]}")
        else:
            print("✗ No data in table")
    except Exception as e:
        print(f"✗ Column check failed: {e}")
    
    # Test 4: Check if RPC function exists
    print("\n4. Testing if match_statpearls_embeddings function exists...")
    try:
        # Try calling with dummy embedding
        dummy_embedding = [0.0] * 768  # sentence-transformers dimension
        response = vector_store.client.rpc(
            "match_statpearls_embeddings",
            {
                "query_embedding": dummy_embedding,
                "match_count": 1,
                "similarity_threshold": 0.0
            }
        ).execute()
        print(f"✓ Function exists. Returned {len(response.data)} rows")
        if response.data:
            print(f"✓ Sample result keys: {list(response.data[0].keys())}")
    except Exception as e:
        print(f"✗ RPC function failed: {e}")
        print("\n⚠️ You need to create the RPC function in Supabase!")
        print("Run the SQL from create_search_function() in your Supabase SQL editor.")
    
    # Test 5: Search for exact text that should exist
    print("\n5. Testing exact text search (biliary cystadenoma)...")
    try:
        response = vector_store.client.table("statpearls_embeddings")\
            .select("*")\
            .ilike("content", "%biliary cystadenoma%")\
            .limit(5)\
            .execute()
        print(f"✓ Found {len(response.data)} rows with 'biliary cystadenoma'")
        if response.data:
            for i, row in enumerate(response.data):
                print(f"  [{i+1}] chunk_id: {row.get('chunk_id')}, title: {row.get('title')}")
        else:
            print("✗ No rows found with this text")
    except Exception as e:
        print(f"✗ Text search failed: {e}")
    
    print("\n" + "="*80)
    print("DATABASE TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
