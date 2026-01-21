"""
StatPearls JSONL Ingestion Script - TRIAL VERSION
Pushes 500 chunks as a test run

Run: python scripts/ingest_statpearls_trial.py
"""

import logging
import time
import os
import sys
import json
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.settings import settings
from utils.embeddings import BMRetrieverEmbeddings
from supabase import create_client, Client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class StatPearlsJSONLIngester:
    """Ingest StatPearls chunks from JSONL files to Supabase"""
    
    def __init__(self, chunk_dir: str = "chunk"):
        self.chunk_dir = Path(chunk_dir)
        self.embeddings = BMRetrieverEmbeddings()
        
        # Initialize Supabase client
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        
        logger.info("StatPearls JSONL Ingester initialized")
    
    def load_chunks_from_jsonl_files(self, limit: int = None) -> List[Dict]:
        """Load chunks from JSONL files"""
        logger.info(f"Loading chunks from {self.chunk_dir}...")
        
        all_chunks = []
        jsonl_files = list(self.chunk_dir.glob("*.jsonl"))
        
        logger.info(f"Found {len(jsonl_files)} JSONL files")
        
        for jsonl_file in jsonl_files:
            if limit and len(all_chunks) >= limit:
                break
                
            try:
                with open(jsonl_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if limit and len(all_chunks) >= limit:
                            break
                            
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            chunk = json.loads(line)
                            all_chunks.append(chunk)
                        except json.JSONDecodeError as e:
                            continue
                    
            except Exception as e:
                logger.error(f"Error loading {jsonl_file}: {e}")
                continue
        
        logger.info(f"✅ Total chunks loaded: {len(all_chunks)}")
        return all_chunks
    
    def get_existing_chunk_ids(self) -> set:
        """Get chunk_ids already in database"""
        logger.info("Fetching existing chunk_ids from Supabase...")
        
        try:
            response = self.supabase.table('statpearls_embeddings').select('chunk_id').execute()
            
            existing_ids = set()
            if response.data:
                existing_ids = {row['chunk_id'] for row in response.data if row.get('chunk_id')}
            
            logger.info(f"✅ Found {len(existing_ids)} existing chunks in database")
            return existing_ids
            
        except Exception as e:
            logger.error(f"Error fetching existing chunks: {e}")
            return set()
    
    def deduplicate_chunks(self, chunks: List[Dict], existing_ids: set) -> List[Dict]:
        """Remove chunks already in database"""
        logger.info(f"Filtering out existing chunks...")
        
        new_chunks = []
        for chunk in chunks:
            chunk_id = chunk.get('chunk_id') or chunk.get('id') or str(len(new_chunks))
            
            if chunk_id not in existing_ids:
                new_chunks.append(chunk)
        
        logger.info(f"✅ New chunks to ingest: {len(new_chunks)}")
        logger.info(f"   (Filtered out {len(chunks) - len(new_chunks)} existing chunks)")
        
        return new_chunks
    
    def prepare_chunk_for_ingestion(self, chunk: Dict) -> Dict:
        """Prepare chunk for Supabase schema"""
        return {
            'content': chunk.get('content') or chunk.get('text') or '',
            'title': chunk.get('title') or 'Unknown',
            'chunk_id': chunk.get('chunk_id') or chunk.get('id') or '',
            'section_type': chunk.get('section_type') or chunk.get('section') or 'body',
            'source': 'StatPearls'
        }
    
    def ingest_chunks(self, chunks: List[Dict], batch_size: int = 10):
        """Ingest chunks to Supabase"""
        total_chunks = len(chunks)
        
        logger.info("="*80)
        logger.info(f"🧪 TRIAL RUN: INGESTING {total_chunks} CHUNKS")
        logger.info("="*80)
        logger.info(f"Batch size: {batch_size}")
        logger.info("="*80)
        
        start_time = time.time()
        
        batch_chunks = []
        chunks_ingested = 0
        
        for idx, chunk in enumerate(chunks, 1):
            try:
                # Prepare chunk
                prepared = self.prepare_chunk_for_ingestion(chunk)
                
                content = prepared['content']
                if not content:
                    logger.warning(f"Empty content for chunk {idx}, skipping")
                    continue
                
                # Generate embedding
                logger.debug(f"Embedding chunk {idx}/{total_chunks}...")
                embedding = self.embeddings.embed_query(content)
                
                prepared['embedding'] = embedding
                batch_chunks.append(prepared)
                
                # Process batch when full
                if len(batch_chunks) >= batch_size:
                    self._insert_batch(batch_chunks)
                    chunks_ingested += len(batch_chunks)
                    
                    # Log progress
                    elapsed = time.time() - start_time
                    rate = chunks_ingested / elapsed if elapsed > 0 else 0
                    
                    logger.info(
                        f"✅ Progress: {chunks_ingested}/{total_chunks} "
                        f"({chunks_ingested/total_chunks*100:.0f}%) | "
                        f"Rate: {rate:.1f} chunks/sec"
                    )
                    
                    batch_chunks = []
                
            except Exception as e:
                logger.error(f"❌ Error preparing chunk {idx}: {e}")
                continue
        
        # Process remaining batch
        if batch_chunks:
            self._insert_batch(batch_chunks)
            chunks_ingested += len(batch_chunks)
        
        # Final stats
        elapsed_time = time.time() - start_time
        
        logger.info("="*80)
        logger.info("🎉 TRIAL COMPLETE")
        logger.info("="*80)
        logger.info(f"Total chunks ingested: {chunks_ingested}")
        logger.info(f"Total time: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
        logger.info(f"Average rate: {chunks_ingested/elapsed_time:.1f} chunks/sec")
        logger.info("="*80)
    
    def _insert_batch(self, chunks: List[Dict]):
        """Insert batch into Supabase"""
        try:
            response = self.supabase.table('statpearls_embeddings').insert(chunks).execute()
            
            if response.data:
                logger.debug(f"✅ Inserted batch of {len(chunks)} chunks")
            else:
                logger.warning(f"⚠️  Batch insert returned no data")
                
        except Exception as e:
            logger.error(f"❌ Error inserting batch: {e}")
            # Try one by one
            logger.info("Retrying with individual inserts...")
            for chunk in chunks:
                try:
                    self.supabase.table('statpearls_embeddings').insert(chunk).execute()
                except Exception as e2:
                    logger.error(f"Failed: {chunk.get('chunk_id')}: {e2}")


def main():
    """Main entry point - TRIAL RUN"""
    logger.info("🧪 TRIAL RUN: StatPearls JSONL Ingestion (500 chunks)")
    logger.info("="*80)
    
    # TRIAL: Only 500 chunks
    TRIAL_COUNT = 500
    
    # Initialize ingester
    ingester = StatPearlsJSONLIngester(chunk_dir="chunk")
    
    # Load chunks (limit to enough for trial)
    all_chunks = ingester.load_chunks_from_jsonl_files(limit=3000)  # Load extra in case duplicates
    
    if len(all_chunks) == 0:
        logger.error("❌ No chunks found in JSONL files!")
        return
    
    # Get existing chunk IDs
    existing_ids = ingester.get_existing_chunk_ids()
    
    # Filter out existing
    new_chunks = ingester.deduplicate_chunks(all_chunks, existing_ids)
    
    if len(new_chunks) == 0:
        logger.warning("⚠️  No new chunks to ingest!")
        return
    
    # TRIAL: Ingest only 500 chunks
    trial_chunks = new_chunks[:TRIAL_COUNT]
    logger.info(f"\n🧪 TRIAL: Ingesting {len(trial_chunks)} chunks")
    
    ingester.ingest_chunks(trial_chunks, batch_size=10)
    
    logger.info("\n✅ Trial complete!")
    logger.info(f"Next: Run full ingestion to add remaining chunks")


if __name__ == "__main__":
    main()
