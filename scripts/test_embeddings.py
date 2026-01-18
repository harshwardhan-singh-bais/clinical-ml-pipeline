"""
Test embedding generation and similarity search
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.embeddings import SentenceTransformerEmbeddings
from utils.db import SupabaseVectorStore
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("="*80)
    print("TESTING EMBEDDING GENERATION AND SIMILARITY SEARCH")
    print("="*80)
    
    # Test text from database
    test_text = "Biliary cystadenoma (BCA) is a slow-growing neoplasm arising from the bile ducts."
    
    # Initialize embedding service
    print("\n1. Initializing embedding service...")
    embeddings = SentenceTransformerEmbeddings()
    
    # Test 2: Generate embedding
    print("\n2. Generating embedding for test text...")
    try:
        embedding = embeddings.embed_query(test_text)
        print(f"✓ Embedding generated")
        print(f"  - Type: {type(embedding)}")
        print(f"  - Length: {len(embedding) if embedding else 'None'}")
        print(f"  - First 5 values: {embedding[:5] if embedding and len(embedding) > 0 else 'Empty'}")
        print(f"  - Is all zeros? {all(v == 0 for v in embedding) if embedding else 'N/A'}")
        
        if not embedding or len(embedding) == 0:
            print("✗ ERROR: Embedding is empty!")
            return
        
        if all(v == 0 for v in embedding):
            print("✗ ERROR: Embedding is all zeros! Model not loaded properly.")
            return
            
    except Exception as e:
        print(f"✗ Embedding generation failed: {e}")
        return
    
    # Test 3: Try similarity search with this embedding
    print("\n3. Testing similarity search with generated embedding...")
    vector_store = SupabaseVectorStore()
    
    try:
        # Use very low threshold to ensure we get results
        results = vector_store.similarity_search(
            query_embedding=embedding,
            top_k=5,
            threshold=0.0  # No threshold - get anything
        )
        
        print(f"✓ Search completed")
        print(f"  - Results: {len(results)}")
        
        if results:
            print("\n  Top 3 results:")
            for i, result in enumerate(results[:3]):
                print(f"  [{i+1}] Similarity: {result.get('similarity_score', 0):.4f}")
                print(f"      Title: {result.get('title', 'N/A')}")
                print(f"      Content: {result.get('text', '')[:100]}...")
        else:
            print("✗ No results returned even with threshold=0.0")
            print("This means embeddings in database don't match your embedding model!")
            
    except Exception as e:
        print(f"✗ Similarity search failed: {e}")
    
    # Test 4: Check what threshold would work
    print("\n4. Testing different thresholds...")
    if results:
        max_sim = max(r.get('similarity_score', 0) for r in results)
        print(f"  - Maximum similarity score: {max_sim:.4f}")
        print(f"  - Current threshold setting: {settings.SIMILARITY_THRESHOLD}")
        
        if max_sim < settings.SIMILARITY_THRESHOLD:
            print(f"✗ PROBLEM FOUND: Max similarity ({max_sim:.4f}) is below threshold ({settings.SIMILARITY_THRESHOLD})")
            print(f"  Recommended: Lower threshold to {max(0.0, max_sim * 0.8):.4f} or re-embed database")
    
    # Test 5: Check if exact text is being embedded the same way
    print("\n5. Fetching exact text from database and comparing embeddings...")
    try:
        response = vector_store.client.table("statpearls_embeddings")\
            .select("content, embedding")\
            .ilike("content", "%biliary cystadenoma%")\
            .limit(1)\
            .execute()
        
        if response.data:
            db_content = response.data[0]['content']
            db_embedding = response.data[0]['embedding']
            
            print(f"✓ Found matching row in database")
            print(f"  - DB content (first 100 chars): {db_content[:100]}")
            print(f"  - DB embedding length: {len(db_embedding) if db_embedding else 'None'}")
            
            # Generate new embedding for exact DB text
            new_embedding = embeddings.embed_query(db_content)
            
            # Calculate cosine similarity manually
            import numpy as np
            if new_embedding and db_embedding and len(new_embedding) == len(db_embedding):
                similarity = np.dot(new_embedding, db_embedding) / (
                    np.linalg.norm(new_embedding) * np.linalg.norm(db_embedding)
                )
                print(f"  - Cosine similarity (new vs DB embedding): {similarity:.4f}")
                
                if similarity < 0.5:
                    print(f"✗ PROBLEM: Embeddings are very different!")
                    print(f"  This means the database was embedded with a different model.")
                    print(f"  You need to re-embed the database or use the same model.")
                elif similarity < 0.8:
                    print(f"⚠️ WARNING: Similarity is low. Model might be different or not deterministic.")
                else:
                    print(f"✓ Embeddings match well!")
            else:
                print(f"✗ Cannot compare: dimension mismatch or empty embeddings")
                
    except Exception as e:
        print(f"✗ Database comparison failed: {e}")
    
    print("\n" + "="*80)
    print("EMBEDDING TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
