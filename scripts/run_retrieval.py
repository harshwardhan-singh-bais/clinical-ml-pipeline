
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.retrieval import LangChainRAGPipeline

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_retrieval.py 'your query here'")
        sys.exit(1)
    query = sys.argv[1]
    pipeline = LangChainRAGPipeline()
    results = pipeline.invoke_chain(query)
    
    if isinstance(results, dict) and "retrieved_evidence" in results:
        evidence_list = results["retrieved_evidence"]
        print(f"\n✓ Total evidence retrieved: {len(evidence_list)}")
        print(f"✓ Context length: {len(results.get('context_for_llm', ''))} chars")
        print(f"✓ Citations: {len(results.get('citations', []))}")
        
        if evidence_list:
            print(f"\n{'='*80}")
            print("RETRIEVED EVIDENCE:")
            print('='*80)
            for idx, evidence in enumerate(evidence_list):
                print(f"\n[{idx+1}] Title: {evidence.get('title', 'N/A')}")
                print(f"    Chunk ID: {evidence.get('chunk_id', 'N/A')}")
                print(f"    Similarity: {evidence.get('similarity_score', 0):.4f}")
                print(f"    Section: {evidence.get('section_type', 'N/A')}")
                print(f"    Content: {evidence.get('text', '')[:200]}...")
        else:
            print("No evidence found for this query.")
    elif isinstance(results, list):
        print(f"\nTotal results: {len(results)}")
        if results:
            for idx, doc in enumerate(results):
                print(f"\nResult {idx+1}:")
                print(doc.get('text', doc))
                print(f"Metadata: {doc.get('metadata', {})}")
        else:
            print("No results found for this query.")
    else:
        print("No output returned from pipeline.")

if __name__ == "__main__":
    main()
