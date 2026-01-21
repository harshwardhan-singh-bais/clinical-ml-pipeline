"""
StatPearls JSONL Ingestion Script
Pushes StatPearls chunks from JSONL files to Supabase statpearls_embeddings table

Table Schema:
- id (auto)
- embedding (vector)
- content (text)
- title (text)
- chunk_id (text)
- section_type (text)
- source (text)

Run: python scripts/ingest_statpearls_jsonl.py
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
        """
        Initialize ingester
        
        Args:
            chunk_dir: Directory containing JSONL files
        """
        self.chunk_dir = Path(chunk_dir)
        self.embeddings = BMRetrieverEmbeddings()
        
        # Initialize Supabase client
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        
        logger.info("StatPearls JSONL Ingester initialized")
    
    def load_chunks_from_jsonl_files(self) -> List[Dict]:
        """
        Load all chunks from JSONL files
        
        Returns:
            List of chunk dictionaries
        """
        logger.info(f"Loading chunks from {self.chunk_dir}...")
        
        all_chunks = []
        jsonl_files = list(self.chunk_dir.glob("*.jsonl"))
        
        logger.info(f"Found {len(jsonl_files)} JSONL files")
        
        for jsonl_file in jsonl_files:
            try:
                with open(jsonl_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            chunk = json.loads(line)
                            all_chunks.append(chunk)
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON error in {jsonl_file.name} line {line_num}: {e}")
                            continue
                
                if len(all_chunks) % 1000 == 0 and len(all_chunks) > 0:
                    logger.info(f"  Loaded {len(all_chunks)} chunks so far...")
                    
            except Exception as e:
                logger.error(f"Error loading {jsonl_file}: {e}")
                continue
        
        logger.info(f"✅ Total chunks loaded: {len(all_chunks)}")
        return all_chunks
    
    def get_existing_chunk_ids(self) -> set:
        """
        Get chunk_ids already in statpearls_embeddings table
        
        Returns:
            Set of existing chunk IDs
        """
        logger.info("Fetching existing chunk_ids from Supabase...")
        
        try:
            # Query all chunk_ids from statpearls_embeddings
            response = self.supabase.table('statpearls_embeddings').select('chunk_id').execute()
            
            existing_ids = set()
            if response.data:
                existing_ids = {row['chunk_id'] for row in response.data if row.get('chunk_id')}
            
            logger.info(f"✅ Found {len(existing_ids)} existing chunks in database")
            return existing_ids
            
        except Exception as e:
            logger.error(f"Error fetching existing chunks: {e}")
            logger.warning("Assuming 2000 chunks exist, will use chunk IDs to deduplicate")
            return set()
    
    def deduplicate_chunks(self, chunks: List[Dict], existing_ids: set) -> List[Dict]:
        """
        Remove chunks that are already in database
        
        Args:
            chunks: All chunks
            existing_ids: Set of existing chunk IDs
            
        Returns:
            New chunks to ingest
        """
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
        """
        Prepare chunk to match Supabase schema
        
        Args:
            chunk: Raw chunk from JSONL
            
        Returns:
            Prepared chunk matching table schema
        """
        # Match exact Supabase columns
        return {
            'content': chunk.get('content') or chunk.get('text') or '',
            'title': chunk.get('title') or 'Unknown',
            'chunk_id': chunk.get('chunk_id') or chunk.get('id') or '',
            'section_type': chunk.get('section_type') or chunk.get('section') or 'body',
            'source': 'StatPearls'
        }
    
    def ingest_chunks(self, chunks: List[Dict], target_count: int = 15000, batch_size: int = 50):
        """
        Ingest chunks to Supabase statpearls_embeddings table
        
        Args:
            chunks: Chunks to ingest
            target_count: Target number of chunks to ingest
            batch_size: Batch size for ingestion
        """
        logger.info("="*80)
        logger.info(f"STARTING STATPEARLS JSONL INGESTION")
        logger.info("="*80)
        logger.info(f"Target chunks: {target_count}")
        logger.info(f"Available chunks: {len(chunks)}")
        logger.info(f"Batch size: {batch_size}")
        logger.info("="*80)
        
        start_time = time.time()
        
        # Limit to target count
        chunks_to_ingest = chunks[:target_count]
        total_chunks = len(chunks_to_ingest)
        
        logger.info(f"Will ingest: {total_chunks} chunks")
        
        batch_chunks = []
        chunks_ingested = 0
        
        for idx, chunk in enumerate(chunks_to_ingest, 1):
            try:
                # Prepare chunk
                prepared = self.prepare_chunk_for_ingestion(chunk)
                
                # Get content for embedding
                content = prepared['content']
                if not content:
                    logger.warning(f"Empty content for chunk {idx}, skipping")
                    continue
                
                # Generate embedding
                embedding = self.embeddings.embed_query(content)
                
                # Add embedding to prepared chunk
                prepared['embedding'] = embedding
                
                batch_chunks.append(prepared)
                
                # Process batch when full
                if len(batch_chunks) >= batch_size:
                    self._insert_batch(batch_chunks)
                    chunks_ingested += len(batch_chunks)
                    
                    # Log progress
                    elapsed = time.time() - start_time
                    rate = chunks_ingested / elapsed if elapsed > 0 else 0
                    eta = (total_chunks - chunks_ingested) / rate if rate > 0 else 0
                    
                    logger.info(
                        f"Progress: {chunks_ingested}/{total_chunks} "
                        f"({chunks_ingested/total_chunks*100:.1f}%) | "
                        f"Rate: {rate:.1f} chunks/sec | "
                        f"ETA: {eta/60:.1f} min"
                    )
                    
                    # Clear batch
                    batch_chunks = []
                
            except Exception as e:
                logger.error(f"Error preparing chunk {idx}: {e}")
                continue
        
        # Process remaining batch
        if batch_chunks:
            self._insert_batch(batch_chunks)
            chunks_ingested += len(batch_chunks)
        
        # Final stats
        elapsed_time = time.time() - start_time
        
        logger.info("="*80)
        logger.info("INGESTION COMPLETE")
        logger.info("="*80)
        logger.info(f"Total chunks ingested: {chunks_ingested}")
        logger.info(f"Total time: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
        logger.info(f"Average rate: {chunks_ingested/elapsed_time:.1f} chunks/sec")
        logger.info("="*80)
    
    def _insert_batch(self, chunks: List[Dict]):
        """
        Insert batch into Supabase
        
        Args:
            chunks: Batch of prepared chunks with embeddings
        """
        try:
            # Insert to statpearls_embeddings table
            response = self.supabase.table('statpearls_embeddings').insert(chunks).execute()
            
            if response.data:
                logger.debug(f"✅ Inserted batch of {len(chunks)} chunks")
            else:
                logger.warning(f"⚠️  Batch insert returned no data")
                
        except Exception as e:
            logger.error(f"❌ Error inserting batch: {e}")
            # Try inserting one by one if batch fails
            logger.info("Retrying with individual inserts...")
            for chunk in chunks:
                try:
                    self.supabase.table('statpearls_embeddings').insert(chunk).execute()
                except Exception as e2:
                    logger.error(f"Failed to insert chunk {chunk.get('chunk_id')}: {e2}")


def main():
    """Main entry point"""
    logger.info("StatPearls JSONL Ingestion Script")
    logger.info("="*80)
    
    # Initialize ingester
    ingester = StatPearlsJSONLIngester(chunk_dir="chunk")
    
    # Load chunks from JSONL files
    all_chunks = ingester.load_chunks_from_jsonl_files()
    
    if len(all_chunks) == 0:
        logger.error("❌ No chunks found in JSONL files!")
        return
    
    # Get existing chunk IDs from database
    existing_ids = ingester.get_existing_chunk_ids()
    
    # Filter out existing chunks
    new_chunks = ingester.deduplicate_chunks(all_chunks, existing_ids)
    
    if len(new_chunks) == 0:
        logger.warning("⚠️  No new chunks to ingest! All chunks already exist in database.")
        return
    
    # Ingest up to 15,000 new chunks
    ingester.ingest_chunks(new_chunks, target_count=15000, batch_size=50)
    
    logger.info("✅ Done!")


if __name__ == "__main__":
    main()
