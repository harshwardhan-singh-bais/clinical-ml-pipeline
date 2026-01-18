"""
Test RPC Function Directly
===========================

This will call the RPC function directly and show any errors.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.db import SupabaseVectorStore
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    print("=" * 80)
    print("Testing RPC Function Directly")
    print("=" * 80)
    
    vector_store = SupabaseVectorStore()
    
    # Create a dummy embedding (all zeros)
    dummy_embedding = [0.0] * 768
    
    print("\n1️⃣ Testing RPC call with dummy embedding...")
    print(f"   Embedding dimension: {len(dummy_embedding)}")
    print(f"   Match count: 5")
    print(f"   Threshold: 0.0")
    
    try:
        response = vector_store.client.rpc(
            "match_statpearls_embeddings",
            {
                "query_embedding": dummy_embedding,
                "match_count": 5,
                "similarity_threshold": 0.0
            }
        ).execute()
        
        print(f"\n✅ RPC call succeeded!")
        print(f"   Response data type: {type(response.data)}")
        print(f"   Number of results: {len(response.data) if response.data else 0}")
        
        if response.data:
            print(f"\n📊 First result:")
            first = response.data[0]
            print(f"   Keys: {list(first.keys())}")
            print(f"   Chunk ID: {first.get('chunk_id')}")
            print(f"   Similarity: {first.get('similarity')}")
        else:
            print("\n❌ RPC returned empty results")
            print("   Possible causes:")
            print("   1. All similarities are <= 0.0 (impossible with threshold=0.0)")
            print("   2. RPC function has a bug")
            print("   3. Embeddings are NULL in database")
            
    except Exception as e:
        print(f"\n❌ RPC call FAILED!")
        print(f"   Error: {e}")
        print("\n   This means the RPC function doesn't exist or has wrong signature")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
