"""
PMC Dataset Indexing Script
Phase 7A: PMC Dataset Ingestion (Factual Knowledge)

CRITICAL RULES (from system guidelines):
- Stream PMC dataset (do NOT load fully into memory)
- Filter aggressively (clinical keywords, text length)
- MAX 3,000 articles
- MAX 40,000 chunks
- Target indexing time ≤ 1 hour
- Store in Supabase pgvector with metadata

Run: python scripts/index_pmc.py
"""


import logging
import time
import os
import sys
from datasets import load_dataset
from typing import Dict
import re
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.settings import settings
from utils.embeddings import BMRetrieverEmbeddings
from utils.db import SupabaseVectorStore
from services.chunking import MedicalChunker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class PMCIndexer:
    """
    PMC dataset indexer.
    
    Phase 7A: PMC Dataset Ingestion
    
    Streams, filters, chunks, embeds, and stores PMC articles.
    """
    
    # Hard limits (from system guidelines)
    MAX_ARTICLES = settings.MAX_PMC_ARTICLES  # 3,000
    MAX_CHUNKS = settings.MAX_PMC_CHUNKS  # 40,000
    MIN_TEXT_LENGTH = settings.MIN_TEXT_LENGTH  # 2,000
    MAX_TEXT_LENGTH = settings.MAX_TEXT_LENGTH  # 30,000
    
    # Clinical keywords for filtering
    CLINICAL_KEYWORDS = [
        "diagnosis",
        "differential",
        "clinical",
        "symptoms",
        "management",
        "treatment",
        "prognosis",
        "patient",
        "disease",
        "condition"
    ]
    
    # Exclude patterns
    EXCLUDE_PATTERNS = [
        "methods",
        "materials",
        "supplementary"
    ]
    
    def __init__(self):
        """Initialize PMC indexer."""
        logger.info("Initializing PMC Indexer...")
        
        self.embeddings = BMRetrieverEmbeddings()
        self.vector_store = SupabaseVectorStore()
        self.chunker = MedicalChunker()
        
        logger.info("PMC Indexer initialized")
    
    def filter_article(self, article: Dict) -> bool:
        """
        Filter PMC article based on clinical relevance.
        
        Phase 7A: Aggressive filtering
        
        Criteria:
        - Text length: 2,000 - 30,000 chars
        - Contains ≥ 2 clinical keywords
        - Not dominated by methods/materials sections
        - Not retracted
        
        Args:
            article: PMC article dictionary
        
        Returns:
            True if article should be included
        """
        text = article.get("text", "")
        text_lower = text.lower()
        
        # Length check
        text_len = len(text)
        if text_len < self.MIN_TEXT_LENGTH or text_len > self.MAX_TEXT_LENGTH:
            return False
        
        # Retraction check
        if article.get("retracted", "").lower() == "yes":
            logger.debug(f"Excluding retracted article: {article.get('pmid')}")
            return False
        
        # Clinical keyword check (need at least 2)
        keyword_count = sum(
            1 for keyword in self.CLINICAL_KEYWORDS
            if keyword in text_lower
        )
        
        if keyword_count < 2:
            return False
        
        # Exclude if dominated by methods/materials
        exclude_count = sum(
            1 for pattern in self.EXCLUDE_PATTERNS
            if text_lower.count(pattern) > 5
        )
        
        if exclude_count > 1:
            return False
        
        return True
    
    def clean_pmc_text(self, text: str) -> str:
        """
        Clean PMC article text.
        
        Phase 7A: Text cleaning
        
        Args:
            text: Raw PMC text
        
        Returns:
            Cleaned text
        """
        # Remove references section
        text = re.sub(
            r'\n\s*(REFERENCES|References)\s*\n.*',
            '',
            text,
            flags=re.DOTALL | re.IGNORECASE
        )
        
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        # Remove figure/table captions
        text = re.sub(
            r'\n\s*(Figure|Table|Fig\.)\s+\d+\.?[^\n]*\n',
            '\n',
            text,
            flags=re.IGNORECASE
        )
        
        return text.strip()
    
    def index_pmc_dataset(self, subset: str = "commercial"):
        """
        Index PMC dataset.
        
        Phase 7A: Full indexing pipeline
        
        Args:
            subset: PMC subset ("commercial", "non_commercial", or "other")
        """
        logger.info("=" * 50)
        logger.info("Starting PMC Dataset Indexing")
        logger.info("=" * 50)
        logger.info(f"Target: {self.MAX_ARTICLES} articles, {self.MAX_CHUNKS} chunks")
        logger.info(f"Subset: {subset}")
        
        start_time = time.time()
        
        # Load PMC dataset with streaming
        logger.info("Loading PMC dataset (streaming mode)...")
        dataset = load_dataset(
            "pmc/open_access",
            name=f"2023-01-01.{subset}",  # Use specific date config
            split="train",
            streaming=True  # CRITICAL: Stream, don't load all
        )
        
        articles_processed = 0
        articles_accepted = 0
        chunks_created = 0
        chunks_indexed = 0
        
        # Batch processing
        batch_embeddings = []
        batch_texts = []
        batch_metadata = []
        batch_size = 50
        
        logger.info("Processing PMC articles...")
        
        for article in dataset:
            articles_processed += 1
            
            # Stop at MAX_ARTICLES
            if articles_accepted >= self.MAX_ARTICLES:
                logger.info(f"Reached max articles limit: {self.MAX_ARTICLES}")
                break
            
            # Stop if chunk limit reached
            if chunks_created >= self.MAX_CHUNKS:
                logger.info(f"Reached max chunks limit: {self.MAX_CHUNKS}")
                break
            
            # Filter article
            if not self.filter_article(article):
                continue
            
            articles_accepted += 1
            
            # Clean text
            cleaned_text = self.clean_pmc_text(article.get("text", ""))
            
            # Chunk article
            article_metadata = {
                "pmcid": article.get("pmid", "unknown"),
                "accession_id": article.get("accession_id"),
                "license": article.get("license"),
                "citation": article.get("citation"),
                "retracted": article.get("retracted")
            }
            
            chunks = self.chunker.chunk_pmc_text(
                text=cleaned_text,
                pmcid=article_metadata["pmcid"],
                metadata=article_metadata
            )
            
            chunks_created += len(chunks)
            
            # Embed and batch
            for chunk in chunks:
                batch_texts.append(chunk["text"])
                batch_metadata.append(chunk)
                
                # Process batch when full
                if len(batch_texts) >= batch_size:
                    self._process_batch(
                        batch_texts,
                        batch_metadata
                    )
                    chunks_indexed += len(batch_texts)
                    
                    # Clear batch
                    batch_texts = []
                    batch_metadata = []
            
            # Log progress every 100 articles
            if articles_accepted % 100 == 0:
                elapsed = time.time() - start_time
                logger.info(
                    f"Progress: {articles_accepted} articles accepted, "
                    f"{chunks_indexed} chunks indexed "
                    f"({elapsed:.1f}s elapsed)"
                )
        
        # Process remaining batch
        if batch_texts:
            self._process_batch(batch_texts, batch_metadata)
            chunks_indexed += len(batch_texts)
        
        # Final stats
        elapsed_time = time.time() - start_time
        
        logger.info("=" * 50)
        logger.info("PMC Indexing Complete")
        logger.info("=" * 50)
        logger.info(f"Articles processed: {articles_processed}")
        logger.info(f"Articles accepted: {articles_accepted}")
        logger.info(f"Chunks created: {chunks_created}")
        logger.info(f"Chunks indexed: {chunks_indexed}")
        logger.info(f"Total time: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
        logger.info(f"Rate: {articles_accepted / (elapsed_time/60):.1f} articles/minute")
        logger.info("=" * 50)
        
        if elapsed_time > 3600:
            logger.warning(
                f"⚠ Indexing exceeded 1 hour target "
                f"({elapsed_time/60:.1f} minutes)"
            )
    
    def _process_batch(
        self,
        texts: list,
        metadata_list: list
    ):
        """
        Process a batch of chunks: embed and store.
        
        Args:
            texts: List of chunk texts
            metadata_list: List of chunk metadata
        """
        try:
            # Embed passages
            logger.debug(f"Embedding batch of {len(texts)} chunks...")
            embeddings = self.embeddings.embed_passages(texts)
            
            # Store in pgvector
            logger.debug(f"Storing batch in pgvector...")
            self.vector_store.insert_embeddings_batch(
                embeddings=embeddings,
                texts=texts,
                metadata_list=metadata_list,
                batch_size=len(texts)  # Insert as single batch
            )
            
        except Exception as e:
            logger.error(f"Error processing batch: {e}")


def main():
    """Main entry point."""
    logger.info("PMC Indexing Script")
    logger.info(f"Max articles: {settings.MAX_PMC_ARTICLES}")
    logger.info(f"Max chunks: {settings.MAX_PMC_CHUNKS}")
    
    indexer = PMCIndexer()
    
    # Index commercial subset (most permissive licenses)
    indexer.index_pmc_dataset(subset="commercial")
    
    logger.info("Indexing complete!")


if __name__ == "__main__":
    main()
