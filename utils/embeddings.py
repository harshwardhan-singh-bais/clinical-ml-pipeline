"""
Sentence Transformers Embedding Utilities
Used for StatPearls ingestion and runtime query embedding.

CRITICAL RULES:
- Use sentence-transformers for embeddings (local, no API required)
- No API quotas, works offline
- Simple, clean embedding calls
- CPU-safe implementation
"""

from sentence_transformers import SentenceTransformer
from typing import List
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


class SentenceTransformerEmbeddings:
    """
    Sentence Transformers embedding service for StatPearls and clinical queries.
    
    Uses local sentence-transformers model for embeddings (no API required).
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-mpnet-base-v2"):
        """
        Initialize sentence-transformers embeddings.
        
        Args:
            model_name: Sentence transformers model name
        """
        self.model_name = model_name
        try:
            logger.info(f"Loading sentence-transformers model: {self.model_name}")
            # Use local cache and increase timeout
            import os
            os.environ['SENTENCE_TRANSFORMERS_HOME'] = os.path.join(os.path.expanduser('~'), '.cache', 'sentence_transformers')
            self.model = SentenceTransformer(self.model_name, cache_folder=None)  # Uses default cache
            logger.info(f"Sentence transformers embeddings initialized with model: {self.model_name}")
            logger.info(f"Model loaded successfully, no API required")
        except Exception as e:
            logger.error(f"Failed to load sentence-transformers model: {e}")
            logger.warning("Embeddings will not be available. Pipeline may fail for retrieval operations.")
            self.model = None
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed documents (StatPearls chunks) using local model.
        
        Args:
            texts: List of document texts
        
        Returns:
            List of embedding vectors
        """
        if self.model is None:
            logger.error("Model not loaded. Cannot generate embeddings.")
            # Return zero vectors as fallback
            return [[0.0] * 768 for _ in texts]
        logger.info(f"Embedding {len(texts)} documents with sentence-transformers...")
        embeddings = self.model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """
        Embed a query (clinical note) using local model.
        
        Args:
            text: Query text
        
        Returns:
            Embedding vector
        """
        if self.model is None:
            logger.error("Model not loaded. Cannot generate query embedding.")
            # Return zero vector as fallback
            return [0.0] * 768
        embedding = self.model.encode([text], convert_to_numpy=True)
        return embedding[0].tolist()


