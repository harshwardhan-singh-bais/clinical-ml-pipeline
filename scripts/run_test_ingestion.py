"""
🧪 TEST MODE: StatPearls Ingestion (2000 Chunks)
================================================

This script runs the StatPearls ingestion in TEST MODE with:
- MAX_CHUNKS: 2000 (limited for testing)
- Relevance Scoring: Enabled
- Target: High-yield clinical content only

Run this to populate your vector database with the top 2000
most clinically relevant chunks from StatPearls.

Usage:
    python scripts/run_test_ingestion.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.ingest_statpearls import StatPearlsIndexer
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Run test mode ingestion"""
    
    print("\n" + "="*80)
    print("🧪 STATPEARLS INGESTION - TEST MODE")
    print("="*80)
    print("\nConfiguration:")
    print(f"  • Max chunks: {StatPearlsIndexer.MAX_CHUNKS}")
    print(f"  • Batch size: {StatPearlsIndexer.BATCH_SIZE}")
    print(f"  • Filtering: Relevance Scoring (Score & Sort)")
    print(f"  • Target: Top {StatPearlsIndexer.MAX_CHUNKS} highest-scoring chunks")
    print("\n" + "="*80 + "\n")
    
    # Verify chunk directory exists
    chunk_dir = Path(__file__).parent.parent / "chunk"
    if not chunk_dir.exists():
        logger.error(f"❌ Chunk directory not found: {chunk_dir}")
        logger.error("   Please ensure the 'chunk/' folder exists in project root")
        return
    
    logger.info(f"✅ Chunk directory found: {chunk_dir}")
    
    # Count JSONL files
    jsonl_files = list(chunk_dir.glob("*.jsonl"))
    logger.info(f"✅ Found {len(jsonl_files)} JSONL files")
    
    if len(jsonl_files) == 0:
        logger.error("❌ No JSONL files found in chunk directory")
        return
    
    print("\n🚀 Starting ingestion...\n")
    
    try:
        # Initialize and run indexer
        indexer = StatPearlsIndexer()
        indexer.ingest_statpearls()
        
        print("\n" + "="*80)
        print("✅ INGESTION COMPLETE!")
        print("="*80)
        print(f"\n📊 Summary:")
        print(f"  • Target chunks: {StatPearlsIndexer.MAX_CHUNKS}")
        print(f"  • Database: Supabase pgvector (statpearls_embeddings table)")
        print(f"  • Next step: Run verification script")
        print(f"\n💡 Verify ingestion:")
        print(f"  python scripts/test_retrieval_relevance.py")
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        logger.error(f"\n❌ Ingestion failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
