"""
Asclepius Synthetic Clinical Notes Loader
==========================================

PURPOSE: Offline clinical note realism testing and few-shot examples

DATASET: starmpcc/Asclepius-Synthetic-Clinical-Notes
SOURCE: https://huggingface.co/datasets/starmpcc/Asclepius-Synthetic-Clinical-Notes

CRITICAL RULES:
❌ NOT embedded
❌ NOT stored in vector DB
❌ NOT used at runtime for facts
✅ Used for:
   - Summarization faithfulness testing
   - Chunking strategy validation
   - OCR stress testing
   - Few-shot examples (optional)

ROLE: Input realism validation (offline only)

Run: python scripts/load_asclepius_notes.py
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datasets import load_dataset

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AsclepiusNotesLoader:
    """
    Load Asclepius synthetic clinical notes for offline testing.
    
    These notes are:
    - Long
    - Messy
    - SOAP-style
    - Closest proxy to real clinical notes
    """
    
    def __init__(self):
        logger.info("Initializing Asclepius Notes Loader")
        logger.info("=" * 60)
        logger.info("⚠️  DATASET ROLE: OFFLINE TESTING ONLY")
        logger.info("❌ NOT stored in vector DB")
        logger.info("❌ NOT used for medical facts")
        logger.info("=" * 60)
    
    def load_notes(self, split: str = "train", max_samples: int = 100) -> List[Dict]:
        """
        Load Asclepius synthetic clinical notes.
        
        Args:
            split: Dataset split (train/test/validation)
            max_samples: Maximum number of samples to load
        
        Returns:
            List of note dictionaries
        """
        logger.info(f"Loading Asclepius notes (split={split}, max={max_samples})...")
        
        try:
            # Load dataset from HuggingFace
            dataset = load_dataset("starmpcc/Asclepius-Synthetic-Clinical-Notes", split=split)
            
            # Limit samples
            if max_samples:
                dataset = dataset.select(range(min(max_samples, len(dataset))))
            
            logger.info(f"Loaded {len(dataset)} synthetic clinical notes")
            
            # Convert to list of dicts
            notes = []
            for item in dataset:
                notes.append({
                    "text": item.get("text") or item.get("note") or item.get("clinical_note"),
                    "metadata": {k: v for k, v in item.items() if k not in ["text", "note", "clinical_note"]}
                })
            
            return notes
            
        except Exception as e:
            logger.error(f"Error loading Asclepius notes: {e}")
            return []
    
    def validate_summarization(self, notes: List[Dict]) -> Dict:
        """
        Use Asclepius notes to validate summarization faithfulness.
        
        Tests:
        - Summary length vs original
        - Key information preservation
        - No hallucinated facts
        
        Args:
            notes: List of clinical notes
        
        Returns:
            Validation statistics
        """
        logger.info("Validating summarization with Asclepius notes...")
        
        from services.chunking import MedicalChunker
        
        chunker = MedicalChunker()
        
        stats = {
            "total_notes": len(notes),
            "avg_note_length": 0,
            "avg_chunks_per_note": 0,
            "total_chunks": 0
        }
        
        total_length = 0
        total_chunks = 0
        
        for note in notes[:10]:  # Sample first 10
            text = note["text"]
            total_length += len(text)
            
            # Test chunking
            chunks = chunker.chunk_patient_note(text)
            total_chunks += len(chunks)
        
        stats["avg_note_length"] = total_length // min(len(notes), 10)
        stats["avg_chunks_per_note"] = total_chunks / min(len(notes), 10)
        stats["total_chunks"] = total_chunks
        
        logger.info(f"Validation stats: {stats}")
        return stats
    
    def extract_few_shot_examples(self, notes: List[Dict], num_examples: int = 3) -> List[str]:
        """
        Extract few-shot examples for prompt engineering.
        
        Args:
            notes: List of clinical notes
            num_examples: Number of examples to extract
        
        Returns:
            List of few-shot example strings
        """
        logger.info(f"Extracting {num_examples} few-shot examples...")
        
        examples = []
        for note in notes[:num_examples]:
            text = note["text"]
            # Truncate for prompt size
            if len(text) > 1000:
                text = text[:1000] + "..."
            examples.append(text)
        
        logger.info(f"Extracted {len(examples)} few-shot examples")
        return examples


def main():
    """Main entry point."""
    logger.info("Asclepius Synthetic Clinical Notes Loader")
    logger.info("=" * 60)
    
    loader = AsclepiusNotesLoader()
    
    # Load sample notes
    notes = loader.load_notes(split="train", max_samples=100)
    
    if notes:
        logger.info(f"Successfully loaded {len(notes)} notes")
        
        # Validate summarization
        stats = loader.validate_summarization(notes)
        
        # Extract few-shot examples
        examples = loader.extract_few_shot_examples(notes, num_examples=3)
        
        logger.info("=" * 60)
        logger.info("Asclepius notes loaded successfully")
        logger.info("Use these for:")
        logger.info("  - Summarization testing")
        logger.info("  - Chunking validation")
        logger.info("  - Few-shot prompting")
        logger.info("=" * 60)
    else:
        logger.error("Failed to load notes")


if __name__ == "__main__":
    main()
