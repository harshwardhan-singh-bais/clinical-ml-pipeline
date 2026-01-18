"""
Qdrant Vector Database Service for Open-Patients Evidence Matching
Handles ingestion and retrieval of patient case narratives.
"""

import logging
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from config.settings import settings
from utils.embeddings import SentenceTransformerEmbeddings

logger = logging.getLogger(__name__)


class QdrantService:
    """
    Qdrant service for Open-Patients evidence retrieval.
    
    Role: THE MEMORY
    - Stores filtered patient narratives
    - Provides semantic similarity search
    - Returns similar patient stories for corroboration
    """
    
    def __init__(self):
        """Initialize Qdrant client."""
        logger.info("Initializing Qdrant Service...")
        
        if not settings.QDRANT_URL or not settings.QDRANT_API_KEY:
            logger.error("QDRANT_URL or QDRANT_API_KEY not configured!")
            self.client = None
            return
        
        try:
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY
            )
            self.collection_name = "open_patients_evidence"
            self.embeddings = SentenceTransformerEmbeddings()
            
            # Create collection if it doesn't exist
            self._create_collection_if_needed()
            
            logger.info(f"✅ Qdrant connected: {settings.QDRANT_URL}")
        
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            self.client = None
    
    def _create_collection_if_needed(self):
        """Create Qdrant collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=settings.EMBEDDING_DIMENSION,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✅ Collection '{self.collection_name}' created")
            else:
                logger.info(f"Collection '{self.collection_name}' already exists")
        
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
    
    def insert_batch(self, chunks: List[Dict]):
        """
        Insert chunks into Qdrant.
        
        Args:
            chunks: List of dicts with 'id', 'text', 'metadata'
        """
        if not self.client:
            logger.error("Qdrant client not initialized")
            return
        
        points = []
        
        for chunk in chunks:
            try:
                # Generate embedding
                embedding = self.embeddings.embed_documents([chunk["text"]])[0]
                
                # Create point
                points.append(
                    PointStruct(
                        id=chunk["id"],
                        vector=embedding,
                        payload={
                            "text": chunk["text"],
                            "case_id": chunk.get("case_id", ""),
                            "source": "open-patients"
                        }
                    )
                )
            
            except Exception as e:
                logger.error(f"Error processing chunk {chunk.get('id', 'unknown')}: {e}")
                continue
        
        if points:
            try:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                logger.info(f"✅ Inserted {len(points)} chunks into Qdrant")
            
            except Exception as e:
                logger.error(f"Error inserting batch into Qdrant: {e}")
    
    def search(self, query_text: str, top_k: int = 5) -> List[Dict]:
        """
        Search for similar patient narratives.
        
        Args:
            query_text: Clinical note or symptoms
            top_k: Number of results to return
        
        Returns:
            List of similar patient stories with metadata
        """
        if not self.client:
            logger.warning("Qdrant client not initialized")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query_text)
            
            # Search using query_points (newer Qdrant client)
            from qdrant_client.models import QueryRequest, NamedVector
            
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=top_k
            ).points
            
            # Format results
            evidence = []
            for hit in results:
                evidence.append({
                    "text": hit.payload.get("text", ""),
                    "case_id": hit.payload.get("case_id", ""),
                    "similarity_score": hit.score,
                    "dataset": "Open-Patients",
                    "source": "open-patients"
                })
            
            logger.info(f"Retrieved {len(evidence)} Open-Patients evidence chunks")
            return evidence
        
        except Exception as e:
            logger.error(f"Error searching Qdrant: {e}")
            return []
    
    def get_collection_stats(self) -> Dict:
        """Get collection statistics."""
        if not self.client:
            return {"error": "Client not initialized"}
        
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "points_count": collection_info.points_count,
                "status": str(collection_info.status)
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}

