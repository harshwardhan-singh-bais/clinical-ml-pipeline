"""
Augmented Clinical Notes Loader
================================

PURPOSE: Robustness and noise tolerance testing

DATASET: AGBonnet/augmented-clinical-notes
SOURCE: https://huggingface.co/datasets/AGBonnet/augmented-clinical-notes

CRITICAL RULES:
❌ NOT embedded
❌ NOT stored in vector DB
❌ NOT authoritative
✅ Used for:
   - OCR tolerance testing
   - Hallucination resistance testing
   - Prompt robustness checks
   - Missing field handling

ROLE: Stress testing and robustness validation (offline only)

Run: python scripts/load_augmented_notes.py
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


class AugmentedNotesLoader:
    """
    Load augmented clinical notes for robustness testing.
    
    These notes contain:
    - Perturbed text
    - Missing fields
    - Noise injection
    - OCR-like errors
    """
    
    def __init__(self):
        logger.info("Initializing Augmented Notes Loader")
        logger.info("=" * 60)
        logger.info("⚠️  DATASET ROLE: STRESS TESTING ONLY")
        logger.info("❌ NOT stored in vector DB")
        logger.info("❌ NOT used for facts")
        logger.info("=" * 60)
    
    def load_notes(self, split: str = "train", max_samples: int = 100) -> List[Dict]:
        """
        Load augmented clinical notes.
        
        Args:
            split: Dataset split (train/test/validation)
            max_samples: Maximum number of samples to load
        
        Returns:
            List of augmented note dictionaries
        """
        logger.info(f"Loading augmented notes (split={split}, max={max_samples})...")
        
        try:
            # Load dataset from HuggingFace
            dataset = load_dataset("AGBonnet/augmented-clinical-notes", split=split)
            
            # Limit samples
            if max_samples:
                dataset = dataset.select(range(min(max_samples, len(dataset))))
            
            logger.info(f"Loaded {len(dataset)} augmented clinical notes")
            
            # Convert to list of dicts
            notes = []
            for item in dataset:
                notes.append({
                    "text": item.get("text") or item.get("note") or item.get("clinical_note"),
                    "augmentation_type": item.get("augmentation_type") or "unknown",
                    "metadata": {k: v for k, v in item.items() if k not in ["text", "note", "clinical_note", "augmentation_type"]}
                })
            
            return notes
            
        except Exception as e:
            logger.error(f"Error loading augmented notes: {e}")
            return []
    
    def test_noise_tolerance(self, notes: List[Dict]) -> Dict:
        """
        Test system tolerance to noisy/perturbed clinical notes.
        
        Tests:
        - OCR error handling
        - Missing field tolerance
        - Noise injection impact
        
        Args:
            notes: List of augmented notes
        
        Returns:
            Test statistics
        """
        logger.info("Testing noise tolerance with augmented notes...")
        
        from services.chunking import MedicalChunker
        
        chunker = MedicalChunker()
        
        stats = {
            "total_notes": len(notes),
            "successfully_chunked": 0,
            "avg_chunks": 0,
            "augmentation_types": {}
        }
        
        total_chunks = 0
        
        for note in notes[:20]:  # Sample first 20
            text = note["text"]
            aug_type = note["augmentation_type"]
            
            # Track augmentation types
            stats["augmentation_types"][aug_type] = stats["augmentation_types"].get(aug_type, 0) + 1
            
            # Test chunking on noisy text
            try:
                chunks = chunker.chunk_patient_note(text)
                if chunks:
                    stats["successfully_chunked"] += 1
                    total_chunks += len(chunks)
            except Exception as e:
                logger.warning(f"Failed to chunk augmented note ({aug_type}): {e}")
        
        stats["avg_chunks"] = total_chunks / max(stats["successfully_chunked"], 1)
        
        logger.info(f"Noise tolerance stats: {stats}")
        return stats
    
    def test_hallucination_resistance(self, notes: List[Dict]) -> Dict:
        """
        Test if augmented notes cause hallucination in outputs.
        
        Args:
            notes: List of augmented notes
        
        Returns:
            Hallucination test results
        """
        logger.info("Testing hallucination resistance...")
        
        # This would require running the full pipeline
        # For now, just log the intent
        
        logger.info("Hallucination resistance test:")
        logger.info("  - Use augmented notes as input")
        logger.info("  - Check if LLM invents facts not in input")
        logger.info("  - Verify citations remain valid")
        
        return {
            "test_type": "hallucination_resistance",
            "notes_tested": len(notes),
            "status": "manual_verification_required"
        }


def main():
    """Main entry point."""
    logger.info("Augmented Clinical Notes Loader")
    logger.info("=" * 60)
    
    loader = AugmentedNotesLoader()
    
    # Load sample notes
    notes = loader.load_notes(split="train", max_samples=100)
    
    if notes:
        logger.info(f"Successfully loaded {len(notes)} augmented notes")
        
        # Test noise tolerance
        noise_stats = loader.test_noise_tolerance(notes)
        
        # Test hallucination resistance
        hallucination_stats = loader.test_hallucination_resistance(notes)
        
        logger.info("=" * 60)
        logger.info("Augmented notes loaded successfully")
        logger.info("Use these for:")
        logger.info("  - OCR tolerance testing")
        logger.info("  - Hallucination resistance")
        logger.info("  - Robustness validation")
        logger.info("=" * 60)
    else:
        logger.error("Failed to load notes")


if __name__ == "__main__":
    main()
