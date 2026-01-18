"""
Check Embedding Storage Format
===============================

This will show us the actual format of embeddings in the database.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.db import SupabaseVectorStore
import json

def main():
    print("=" * 80)
    print("Checking Embedding Format in Database")
    print("=" * 80)
    
    vector_store = SupabaseVectorStore()
    
    # Get one row with embedding
    response = vector_store.client.table("statpearls_embeddings")\
        .select("chunk_id, embedding")\
        .limit(1)\
        .execute()
    
    if response.data:
        row = response.data[0]
        embedding = row.get('embedding')
        
        print(f"\nChunk ID: {row.get('chunk_id')}")
        print(f"Embedding type: {type(embedding)}")
        print(f"Embedding value (first 50 chars): {str(embedding)[:50]}")
        
        if isinstance(embedding, str):
            print("\n❌ PROBLEM: Embedding is stored as STRING, not VECTOR!")
            print("   The database column type is wrong.")
            print("   Need to recreate table with proper VECTOR type.")
        elif isinstance(embedding, list):
            print(f"\n✅ Embedding is a list with {len(embedding)} dimensions")
            print(f"   Sample values: {embedding[:5]}")
        else:
            print(f"\n⚠️ Embedding is type: {type(embedding)}")
    else:
        print("❌ No data found")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
