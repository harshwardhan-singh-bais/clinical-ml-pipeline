"""
Medical-Aware Text Chunking Service
Phase 5: Medical-Aware Chunking (User Input)

Uses LangChain for semantic-aware chunking.
Preserves clinical context, respects sentence boundaries.

CRITICAL RULES:
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List
import logging
import tiktoken
from config.settings import settings

logger = logging.getLogger(__name__)


class MedicalChunker:
    """
    Medical-aware text chunking using LangChain.
    
    Phase 5: Medical-Aware Chunking
    
    Ensures:
    - Clinical context preserved
    - Symptoms/labs not broken
    - Sentence boundaries respected
    """
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        """
        Initialize medical chunker.
        
        Args:
            chunk_size: Target chunk size in tokens (default from settings)
            chunk_overlap: Overlap size in tokens (default from settings)
        """
        self.chunk_size = chunk_size or settings.MAX_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        
        # Initialize tokenizer for accurate token counting
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
        except:
            # Fallback to cl100k_base encoding
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # LangChain text splitter with medical-aware separators (token-based sizing)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=self._count_tokens,
            separators=[
                "\n\n\n",  # Section breaks
                "\n\n",    # Paragraph breaks
                "\n",      # Line breaks
                ". ",      # Sentence breaks
                ", ",      # Clause breaks
                " ",       # Word breaks
                ""         # Character breaks (last resort)
            ],
            keep_separator=True
        )
        
        logger.info(
            f"MedicalChunker initialized: "
            f"chunk_size={self.chunk_size} tokens, "
            f"overlap={self.chunk_overlap} tokens"
        )
    
    def _count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Input text
        
        Returns:
            Number of tokens
        """
        return len(self.tokenizer.encode(text))
    
    def _tokens_to_chars(self, num_tokens: int) -> int:
        """
        Estimate character count from token count.
        
        Rough estimate: 1 token ≈ 4 characters for English.
        
        Args:
            num_tokens: Number of tokens
        
        Returns:
            Estimated character count
        """
        return num_tokens * 4
    
    def chunk_patient_note(
        self,
        text: str,
        patient_id: str = None
    ) -> List[dict]:
        """
        Chunk patient clinical note.
        
        Phase 5: Medical-Aware Chunking (User Input)
        
        IMPORTANT: These chunks are NOT stored permanently.
        They are temporary, used only for query embedding.
        
        Args:
            text: Cleaned and normalized clinical text
            patient_id: Optional patient identifier
        
        Returns:
            List of chunk dictionaries with metadata
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking")
            return []
        
        logger.info(f"Chunking patient note ({len(text)} chars)")
        
        # Split text using LangChain
        docs = self.text_splitter.create_documents([text])
        
        # Convert to dictionaries with metadata
        chunks = []
        for idx, doc in enumerate(docs):
            chunk = {
                "chunk_id": f"patient_chunk_{idx}",
                "text": doc.page_content,
                "token_count": self._count_tokens(doc.page_content),
                "sequence_number": idx,
                "source": "patient_input",
                "patient_id": patient_id
            }
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} chunks from patient note")
        
        # Log token distribution
        token_counts = [c["token_count"] for c in chunks]
        if token_counts:
            logger.info(
                f"Token distribution: "
                f"min={min(token_counts)}, "
                f"max={max(token_counts)}, "
                f"avg={sum(token_counts) / len(token_counts):.1f}"
            )
        
        return chunks
    
    def chunk_pmc_text(
        self,
        text: str,
        pmcid: str,
        metadata: dict = None
    ) -> List[dict]:
        """
        Chunk PMC article text.
        
        Phase 7A: PMC Dataset Ingestion (Offline)
        
        IMPORTANT: These chunks ARE stored in pgvector.
        
        Args:
            text: PMC article text
            pmcid: PubMed Central ID
            metadata: Additional metadata (citation, license, etc.)
        
        Returns:
            List of chunk dictionaries with metadata
        """
        if not text or not text.strip():
            logger.warning(f"Empty text for PMC article {pmcid}")
            return []
        
        logger.debug(f"Chunking PMC article {pmcid} ({len(text)} chars)")
        
        # Split text using LangChain
        docs = self.text_splitter.create_documents([text])
        
        # Convert to dictionaries with metadata
        chunks = []
        for idx, doc in enumerate(docs):
            chunk = {
                "chunk_id": f"pmc_{pmcid}_chunk_{idx}",
                "text": doc.page_content,
                "token_count": self._count_tokens(doc.page_content),
                "sequence_number": idx,
                "source": "PMC",
                "pmcid": pmcid,
                # Include metadata from parent article
                "accession_id": metadata.get("accession_id") if metadata else None,
                "license": metadata.get("license") if metadata else None,
                "citation": metadata.get("citation") if metadata else None,
                "retracted": metadata.get("retracted") if metadata else None
            }
            chunks.append(chunk)
        
        logger.debug(f"Created {len(chunks)} chunks from PMC {pmcid}")
        
        return chunks
    
    def validate_chunk_quality(self, chunk: dict) -> bool:
        """
        Validate that a chunk has sufficient quality.
        
        Checks:
        - Minimum length (>50 tokens)
        - Not just whitespace
        - Contains meaningful content
        
        Args:
            chunk: Chunk dictionary
        
        Returns:
            True if chunk is valid
        """
        text = chunk.get("text", "")
        token_count = chunk.get("token_count", 0)
        
        # Minimum length check
        if token_count < 50:
            return False
        
        # Whitespace check
        if not text.strip():
            return False
        
        # Check for minimum word count
        words = text.split()
        if len(words) < 20:
            return False
        
        # Check that it's not just numbers/symbols
        alphanumeric_ratio = sum(c.isalnum() for c in text) / max(len(text), 1)
        if alphanumeric_ratio < 0.6:
            return False
        
        return True
    
    def merge_short_chunks(
        self,
        chunks: List[dict],
        min_size: int = 100
    ) -> List[dict]:
        """
        Merge consecutive chunks that are too short.
        
        Args:
            chunks: List of chunk dictionaries
            min_size: Minimum token count per chunk
        
        Returns:
            List of merged chunks
        """
        if not chunks:
            return []
        
        merged = []
        current_chunk = chunks[0].copy()
        
        for next_chunk in chunks[1:]:
            if current_chunk["token_count"] < min_size:
                # Merge with next chunk
                current_chunk["text"] += " " + next_chunk["text"]
                current_chunk["token_count"] = self._count_tokens(current_chunk["text"])
            else:
                # Save current chunk and start new one
                merged.append(current_chunk)
                current_chunk = next_chunk.copy()
        
        # Add last chunk
        merged.append(current_chunk)
        
        logger.info(f"Merged {len(chunks)} chunks into {len(merged)} chunks")
        return merged


# ========== HELPER FUNCTIONS ==========

def create_langchain_documents(
    chunks: List[dict]
) -> List[Document]:
    """
    Convert chunk dictionaries to LangChain Document objects.
    
    Useful for integration with LangChain pipelines.
    
    Args:
        chunks: List of chunk dictionaries
    
    Returns:
        List of LangChain Document objects
    """
    documents = []
    
    for chunk in chunks:
        doc = Document(
            page_content=chunk["text"],
            metadata={
                "chunk_id": chunk["chunk_id"],
                "source": chunk.get("source"),
                "pmcid": chunk.get("pmcid"),
                "token_count": chunk.get("token_count")
            }
        )
        documents.append(doc)
    
    return documents
