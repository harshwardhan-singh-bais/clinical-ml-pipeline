"""
Cross-Encoder Reranking for Evidence Quality
Reranks initial retrieval results using semantic similarity scoring.
"""

from typing import List, Dict, Tuple
from sentence_transformers import CrossEncoder
import logging

logger = logging.getLogger(__name__)


class EvidenceReranker:
    """
    Reranks retrieved evidence using a Cross-Encoder model.
    Cross-Encoders are slower but much more accurate than bi-encoders.
    """
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize cross-encoder reranker.
        
        Args:
            model_name: HuggingFace model name for cross-encoder
        """
        try:
            self.model = CrossEncoder(model_name)
            logger.info(f"CrossEncoder loaded: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load CrossEncoder: {e}")
            self.model = None
    
    def rerank(
        self,
        query: str,
        candidates: List[Dict],
        top_k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict]:
        """
        Rerank candidates using cross-encoder scoring.
        
        Args:
            query: Search query or clinical note
            candidates: List of evidence dicts with 'text' field
            top_k: Number of top results to return
            score_threshold: Minimum score to include (0.0 = no filter)
            
        Returns:
            Reranked list of evidence dicts with updated 'rerank_score'
        """
        if not self.model or not candidates:
            logger.warning("Reranking skipped (no model or no candidates)")
            return candidates[:top_k]
        
        # Prepare query-document pairs
        pairs = []
        for candidate in candidates:
            doc_text = candidate.get("text", "")
            if doc_text:
                pairs.append([query, doc_text])
        
        if not pairs:
            logger.warning("No valid text found in candidates for reranking")
            return candidates[:top_k]
        
        # Score all pairs
        try:
            scores = self.model.predict(pairs)
            
            # Attach scores to candidates
            for idx, score in enumerate(scores):
                if idx < len(candidates):
                    candidates[idx]["rerank_score"] = float(score)
                    # Keep original similarity for comparison
                    if "similarity_score" not in candidates[idx]:
                        candidates[idx]["similarity_score"] = candidates[idx].get("score", 0.0)
            
            # Sort by rerank score (descending)
            reranked = sorted(
                candidates,
                key=lambda x: x.get("rerank_score", -999),
                reverse=True
            )
            
            # Filter by threshold
            if score_threshold > 0:
                reranked = [c for c in reranked if c.get("rerank_score", 0) >= score_threshold]
            
            logger.info(f"Reranked {len(candidates)} candidates -> Top {min(top_k, len(reranked))} selected")
            
            return reranked[:top_k]
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return candidates[:top_k]
    
    def score_pair(self, query: str, document: str) -> float:
        """
        Score a single query-document pair.
        
        Args:
            query: Query text
            document: Document text
            
        Returns:
            Relevance score (higher = more relevant)
        """
        if not self.model:
            return 0.0
        
        try:
            score = self.model.predict([[query, document]])[0]
            return float(score)
        except Exception as e:
            logger.error(f"Scoring failed: {e}")
            return 0.0
    
    def batch_rerank_by_diagnosis(
        self,
        diagnoses: List[str],
        evidence_pool: List[Dict],
        top_k_per_diagnosis: int = 3
    ) -> Dict[str, List[Dict]]:
        """
        Rerank evidence separately for each diagnosis.
        
        Args:
            diagnoses: List of diagnosis names
            evidence_pool: Pool of all evidence chunks
            top_k_per_diagnosis: Number of chunks per diagnosis
            
        Returns:
            Dict mapping diagnosis -> top evidence chunks
        """
        results = {}
        
        for diagnosis in diagnoses:
            # Rerank evidence pool using diagnosis as query
            reranked = self.rerank(
                query=diagnosis,
                candidates=evidence_pool.copy(),  # Don't modify original
                top_k=top_k_per_diagnosis
            )
            results[diagnosis] = reranked
            logger.debug(f"Reranked {len(evidence_pool)} chunks for '{diagnosis}' -> {len(reranked)} selected")
        
        return results
