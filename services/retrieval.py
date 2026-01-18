"""
RAG Retrieval Service with LangChain
Retrieves StatPearls evidence for clinical reasoning.

Uses:
- LangChain for orchestration
- Supabase pgvector for similarity search
- Sentence-transformers embeddings for queries

CRITICAL RULES:
- Retrieve from StatPearls ONLY
- Top-K retrieval (default K=10)
- Similarity threshold filtering
- Citation metadata preserved
"""

from langchain_community.docstore.document import Document
from typing import List, Dict
import logging
from utils.embeddings import SentenceTransformerEmbeddings
from utils.db import SupabaseVectorStore, format_retrieval_results
from config.settings import settings

logger = logging.getLogger(__name__)


class RAGRetriever:
    """
    Retrieval-Augmented Generation (RAG) retriever.
    
    Fetch medical evidence from StatPearls with citation traceability.
    Uses LangChain for pipeline orchestration.
    """
    
    def __init__(
        self,
        embeddings: SentenceTransformerEmbeddings = None,
        vector_store: SupabaseVectorStore = None
    ):
        """
        Initialize RAG retriever.
        
        Args:
            embeddings: Sentence transformers embedding service
            vector_store: Supabase vector store
        """
        self.embeddings = embeddings or SentenceTransformerEmbeddings()
        self.vector_store = vector_store or SupabaseVectorStore()
        
        logger.info("RAGRetriever initialized")
    
    def retrieve_evidence(
        self,
        patient_chunks: List,
        top_k: int = None,
        threshold: float = None
    ) -> List[Dict]:
        """
        Retrieve StatPearls evidence for patient chunks (hardened, clinical-safe).

        Flow:
        1. Embed patient chunks as queries
        2. Search StatPearls vector store (source filter enforced)
        3. Retrieve top-K relevant chunks
        4. Rank by similarity score (correct key)
        5. Return with citations

        Args:
            patient_chunks: List of patient text chunks (dicts or strings)
            top_k: Number of results per query (default from settings)
            threshold: Similarity threshold (default from settings)

        Returns:
            List of retrieved StatPearls chunks with metadata
        """
        top_k = top_k or settings.TOP_K_RETRIEVAL
        threshold = threshold or settings.SIMILARITY_THRESHOLD

        if not patient_chunks:
            logger.warning("No patient chunks provided for retrieval")
            return []

        logger.info(f"Retrieving evidence for {len(patient_chunks)} patient chunks")

        # Handle patient_chunks as list of dicts or list of strings
        processed_chunks = []
        for i, chunk in enumerate(patient_chunks):
            if isinstance(chunk, dict) and "text" in chunk:
                processed_chunks.append(chunk)
            elif isinstance(chunk, str):
                processed_chunks.append({"chunk_id": f"auto_{i}", "text": chunk})
            else:
                logger.warning(f"Invalid patient chunk format at index {i}: {chunk}")
        patient_texts = [chunk["text"] for chunk in processed_chunks]

        # Embed patient chunks as queries using sentence-transformers
        logger.info("Embedding patient chunks as queries...")
        query_embeddings = []
        for text in patient_texts:
            emb = self.embeddings.embed_query(text)
            if isinstance(emb, list) and emb and isinstance(emb[0], list):
                emb = emb[0]
            query_embeddings.append(emb)

        all_results = []
        seen_chunk_ids = set()

        for idx, query_emb in enumerate(query_embeddings):
            logger.debug(f"Retrieving for patient chunk {idx + 1}/{len(query_embeddings)}")

            # Similarity search in pgvector (enforce source filter in SQL)
            results = self.vector_store.similarity_search(
                query_embedding=query_emb,
                top_k=top_k,
                threshold=threshold
            )

            for result in results:
                chunk_id = result.get("chunk_id")

                if not chunk_id or chunk_id in seen_chunk_ids:
                    continue
                if not result.get("text"):
                    continue

                seen_chunk_ids.add(chunk_id)
                result["related_patient_chunk_id"] = processed_chunks[idx]["chunk_id"]
                all_results.append(result)

        # Sort all results by similarity score (descending, correct key)
        all_results.sort(
            key=lambda x: x.get("similarity_score", 0),
            reverse=True
        )

        # Take top overall results
        all_results = all_results[: top_k * 2]

        logger.info(f"Retrieved {len(all_results)} unique StatPearls chunks")

        # Format for downstream use (traceability)
        formatted_results = format_retrieval_results(all_results)

        return formatted_results
    
    def retrieve_for_single_query(
        self,
        query_text: str,
        top_k: int = None,
        threshold: float = None
    ) -> List[Dict]:
        """
        Retrieve StatPearls evidence for a single query text.
        
        Convenience method for simple queries.
        
        Args:
            query_text: Single query text
            top_k: Number of results
            threshold: Similarity threshold
        
        Returns:
            List of retrieved PMC chunks
        """
        # Create a simple chunk dict
        patient_chunk = {
            "chunk_id": "query_0",
            "text": query_text,
            "source": "query"
        }
        
        return self.retrieve_evidence(
            patient_chunks=[patient_chunk],
            top_k=top_k,
            threshold=threshold
        )
    
    def build_context_for_llm(
        self,
        retrieved_evidence: List[Dict],
        max_chunks: int = 10
    ) -> str:
        """
        Build context string for LLM from retrieved evidence.
        
        Phase 12: Prompt Construction (evidence component)
        
        Format:
        - Each chunk numbered
        - Include StatPearls chunk_id and citation
        - Preserve traceability
        
        Args:
            retrieved_evidence: List of retrieved StatPearls chunks
            max_chunks: Maximum chunks to include
        
        Returns:
            Formatted context string for LLM
        """
        if not retrieved_evidence:
            return "No relevant StatPearls evidence found."
        
        # Limit chunks
        evidence_to_use = retrieved_evidence[:max_chunks]
        
        context_parts = [
            "===== STATPEARLS EVIDENCE =====\n",
            f"Retrieved {len(evidence_to_use)} relevant excerpts from StatPearls.\n"
        ]
        
        for idx, evidence in enumerate(evidence_to_use, 1):
            chunk_id = evidence.get("chunk_id", "unknown")
            source = evidence.get("source", "statpearls")
            text = evidence.get("text", "")
            citation = evidence.get("citation", "Citation not available")
            similarity = evidence.get("similarity_score", 0.0)
            
            context_parts.append(f"\n[EVIDENCE {idx}]")
            context_parts.append(f"Source: {source} (Chunk ID: {chunk_id})")
            context_parts.append(f"Relevance Score: {similarity:.3f}")
            context_parts.append(f"Citation: {citation}")
            context_parts.append(f"\nText:\n{text}\n")
            context_parts.append("-" * 80)
        
        context_parts.append("\n===== END EVIDENCE =====\n")
        
        return "\n".join(context_parts)
    
    def extract_citations_from_evidence(
        self,
        retrieved_evidence: List[Dict]
    ) -> List[Dict]:
        """
        Extract citation information for response.
        
        Phase 10: Evidence Traceability Layer
        
        Args:
            retrieved_evidence: Retrieved StatPearls chunks
        
        Returns:
            List of citation dictionaries for response schema
        """
        citations = []
        
        for evidence in retrieved_evidence:
            text_val = evidence.get("text")
            if text_val is None:
                text_snippet = ""
            else:
                text_snippet = text_val[:200] + "..."
            citation = {
                "chunk_id": evidence.get("chunk_id"),
                "source": evidence.get("source", "statpearls"),
                "text_snippet": text_snippet,
                "similarity_score": evidence.get("similarity_score", 0.0),
                "citation": evidence.get("citation")
            }
            citations.append(citation)
        
        return citations


# ========== LANGCHAIN INTEGRATION ==========

class LangChainRAGPipeline:
    """
    LangChain-based RAG pipeline.
    
    Phase 8: Pipeline Orchestration (LangChain)
    
    Integrates:
    - Sentence-transformers embeddings
    - Supabase pgvector
    - LangChain orchestration
    """
    
    def __init__(
        self,
        retriever: RAGRetriever = None
    ):
        """
        Initialize LangChain RAG pipeline.
        
        Args:
            retriever: RAG retriever instance
        """
        self.retriever = retriever or RAGRetriever()
        logger.info("LangChain RAG pipeline initialized")
    
    def create_retrieval_chain(self):
        """
        Create LangChain retrieval chain.
        
        This would integrate with LangChain's chain abstractions.
        For now, we use custom logic that's LangChain-compatible.
        
        Returns:
            Retrieval chain (custom for now)
        """
        # This is a placeholder for LangChain chain integration
        # In production, this would use LangChain's RetrievalQA or similar
        logger.info("Creating LangChain retrieval chain")
        return self.retriever
    
    def invoke_chain(
        self,
        patient_text: str,
        patient_chunks: List[dict] = None
    ) -> Dict:
        """
        Invoke the full RAG chain.
        
        Phase 8: Pipeline Orchestration
        
        Args:
            patient_text: Patient clinical note
            patient_chunks: Pre-chunked patient text (optional)
        
        Returns:
            Dictionary with retrieved evidence and metadata
        """
        if not patient_chunks:
            # Chunk patient text if not provided
            from services.chunking import MedicalChunker
            chunker = MedicalChunker()
            patient_chunks = chunker.chunk_patient_note(patient_text)
        
        # Retrieve evidence
        evidence = self.retriever.retrieve_evidence(patient_chunks)
        
        # Build context
        context = self.retriever.build_context_for_llm(evidence)
        
        # Extract citations
        citations = self.retriever.extract_citations_from_evidence(evidence)
        
        return {
            "retrieved_evidence": evidence,
            "context_for_llm": context,
            "citations": citations,
            "total_evidence_count": len(evidence)
        }
