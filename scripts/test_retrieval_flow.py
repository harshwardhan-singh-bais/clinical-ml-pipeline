"""
Test the exact flow of run_retrieval.py to find why it returns 0 results
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.retrieval import LangChainRAGPipeline
from services.chunking import MedicalChunker
from utils.embeddings import SentenceTransformerEmbeddings
from utils.db import SupabaseVectorStore
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("="*80)
    print("TESTING EXACT run_retrieval.py FLOW")
    print("="*80)
    
    # Test text - same as user's query
    test_text = "Biliary cystadenoma (BCA) is a slow-growing neoplasm arising from the bile ducts. The pathogenesis is that these lesions are still unknown—suggestion of theory of superficial injury and reactive process. Alternatively, it is a congenital disease arising from ectopic remnants or aberrancy of embryonic bile ducts. Another theory is that these neoplasms are secondary to implantation, explaining the ovarian-like stroma, overexpression of estrogen and progesterone receptors. It has a heterogeneous mixture with septations occupied with either mucinous (95%) or serous (5%) components. [7] [8]"
    
    # Step 1: Chunk the text (this is what invoke_chain does)
    print("\n1. Chunking patient text...")
    chunker = MedicalChunker()
    chunks = chunker.chunk_patient_note(test_text)
    print(f"✓ Created {len(chunks)} chunks")
    for i, chunk in enumerate(chunks):
        if isinstance(chunk, dict):
            print(f"  Chunk {i+1}: {chunk.get('text', str(chunk))[:80]}...")
        else:
            print(f"  Chunk {i+1}: {str(chunk)[:80]}...")
    
    # Step 2: Embed each chunk
    print("\n2. Embedding each chunk...")
    embeddings = SentenceTransformerEmbeddings()
    for i, chunk in enumerate(chunks):
        text = chunk.get('text') if isinstance(chunk, dict) else chunk
        if text:
            emb = embeddings.embed_query(text)
            print(f"  Chunk {i+1} embedding: dim={len(emb) if emb else 0}, first 3 values={emb[:3] if emb else 'None'}")
    
    # Step 3: Search for each chunk
    print("\n3. Searching for each chunk...")
    vector_store = SupabaseVectorStore()
    
    for i, chunk in enumerate(chunks):
        text = chunk.get('text') if isinstance(chunk, dict) else chunk
        if text:
            print(f"\n  Chunk {i+1} search:")
            print(f"    Text: {text[:100]}...")
            
            emb = embeddings.embed_query(text)
            results = vector_store.similarity_search(
                query_embedding=emb,
                top_k=5,
                threshold=0.15  # Current setting
            )
            
            print(f"    Results: {len(results)}")
            if results:
                for j, r in enumerate(results[:2]):
                    print(f"      [{j+1}] sim={r.get('similarity_score', 0):.4f}, title={r.get('title', 'N/A')[:50]}")
            else:
                print(f"    ⚠️ No results for this chunk!")
    
    # Step 4: Now test the full pipeline (same as run_retrieval.py)
    print("\n" + "="*80)
    print("4. Testing full LangChainRAGPipeline.invoke_chain()...")
    print("="*80)
    
    pipeline = LangChainRAGPipeline()
    results = pipeline.invoke_chain(test_text)
    
    print(f"\nPipeline results:")
    print(f"  - Total evidence: {results.get('total_evidence_count', 0)}")
    print(f"  - Retrieved evidence items: {len(results.get('retrieved_evidence', []))}")
    
    if results.get('retrieved_evidence'):
        print(f"\n  Top 3 evidence:")
        for i, ev in enumerate(results['retrieved_evidence'][:3]):
            print(f"  [{i+1}] {ev.get('title', 'N/A')[:60]}")
            print(f"      Similarity: {ev.get('similarity_score', 0):.4f}")
    else:
        print("  ⚠️ No evidence retrieved!")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
