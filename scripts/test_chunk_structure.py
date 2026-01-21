"""
Test script to check StatPearls JSONL files
Run: python scripts/test_chunk_structure.py
"""

import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_jsonl_structure():
    """Test JSONL chunk folder structure"""
    
    chunk_dir = Path("chunk")
    
    if not chunk_dir.exists():
        logger.error(f"❌ {chunk_dir} folder not found!")
        return
    
    logger.info(f"✅ Found {chunk_dir} folder")
    
    # Get all JSONL files
    jsonl_files = list(chunk_dir.glob("*.jsonl"))
    logger.info(f"📁 Found {len(jsonl_files)} JSONL files")
    
    if len(jsonl_files) == 0:
        logger.error("❌ No JSONL files found in chunk/ folder!")
        logger.info("Looking for other file types...")
        all_files = list(chunk_dir.glob("*.*"))
        logger.info(f"Found {len(all_files)} total files:")
        for f in all_files[:10]:
            logger.info(f"  - {f.name}")
        return
    
    # Sample first few files
    total_chunks = 0
    sample_chunk = None
    
    for idx, jsonl_file in enumerate(jsonl_files[:5], 1):
        try:
            chunk_count = 0
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        chunk = json.loads(line)
                        chunk_count += 1
                        
                        if not sample_chunk:
                            sample_chunk = chunk
                            
                    except json.JSONDecodeError:
                        continue
                
            total_chunks += chunk_count
            logger.info(f"  File {idx}: {jsonl_file.name} - {chunk_count} chunks")
                
        except Exception as e:
            logger.error(f"  ❌ Error reading {jsonl_file.name}: {e}")
    
    logger.info(f"\n📊 Total chunks in first 5 files: {total_chunks}")
    
    # Show sample chunk structure
    if sample_chunk:
        logger.info("\n📋 Sample Chunk Structure:")
        logger.info("="*80)
        logger.info(f"Keys: {list(sample_chunk.keys())}")
        logger.info("\nSample chunk:")
        for key, value in sample_chunk.items():
            if isinstance(value, str) and len(value) > 100:
                logger.info(f"  {key}: {value[:100]}...")
            else:
                logger.info(f"  {key}: {value}")
        logger.info("="*80)
        
        # Check required fields for Supabase
        required_fields = ['content', 'title', 'chunk_id', 'section_type']
        logger.info("\n✅ Checking Supabase schema compatibility:")
        for field in required_fields:
            alt_field = 'text' if field == 'content' else ('id' if field == 'chunk_id' else field)
            if field in sample_chunk or alt_field in sample_chunk:
                logger.info(f"  ✓ {field}: Found")
            else:
                logger.warning(f"  ⚠️  {field}: Missing (will use default)")
    
    # Estimate total
    if len(jsonl_files) > 5 and total_chunks > 0:
        avg_per_file = total_chunks / 5
        estimated_total = avg_per_file * len(jsonl_files)
        logger.info(f"\n📈 Estimated total chunks: {estimated_total:.0f}")
        logger.info(f"   (Based on average of {avg_per_file:.1f} chunks/file)")
        
        if estimated_total > 2000:
            new_chunks = estimated_total - 2000
            logger.info(f"\n✅ After removing 2,000 existing: ~{new_chunks:.0f} new chunks available")
    
    return {
        'total_files': len(jsonl_files),
        'sample_chunk_count': total_chunks,
        'sample_chunk': sample_chunk
    }


if __name__ == "__main__":
    logger.info("Testing JSONL chunk folder structure...")
    logger.info("="*80)
    
    result = test_jsonl_structure()
    
    logger.info("\n" + "="*80)
    if result and result.get('sample_chunk_count', 0) > 0:
        logger.info("✅ Test complete! Ready for ingestion.")
    else:
        logger.error("❌ Test failed. Check chunk/ folder.")
