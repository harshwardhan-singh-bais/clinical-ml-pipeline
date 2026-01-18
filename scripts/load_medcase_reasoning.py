"""
MedCaseReasoning Loader (TEST MODE)
====================================

PURPOSE: Reasoning style and prompt logic testing

DATASET: MedCaseReasoning (custom or HuggingFace)
SOURCE: [Specify source if available]

CRITICAL RULES:
❌ NOT embedded
❌ NOT stored in vector DB
❌ NOT authoritative
✅ Used for:
   - Reasoning pattern validation
   - Prompt logic checks
   - Traceability and justification stress tests

ROLE: Reasoning style and traceability validation (offline only)

Run: python scripts/load_medcase_reasoning.py
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# If MedCaseReasoning is on HuggingFace, import load_dataset
try:
    from datasets import load_dataset
except ImportError:
    load_dataset = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MedCaseReasoningLoader:
    """
    Load MedCaseReasoning cases for reasoning style and traceability testing.
    """
    def __init__(self):
        logger.info("Initializing MedCaseReasoning Loader")
        logger.info("=" * 60)
        logger.info("⚠️  DATASET ROLE: REASONING STYLE TESTING ONLY")
        logger.info("❌ NOT stored in vector DB")
        logger.info("❌ NOT used for facts")
        logger.info("=" * 60)

    def load_cases(self, split: str = "train", max_samples: int = 100) -> List[Dict]:
        """
        Load MedCaseReasoning cases.
        Args:
            split: Dataset split (train/test/validation)
            max_samples: Maximum number of samples to load
        Returns:
            List of MedCaseReasoning case dictionaries
        """
        logger.info(f"Loading MedCaseReasoning cases (split={split}, max={max_samples})...")
        if load_dataset:
            try:
                # Use the correct HuggingFace dataset name
                dataset = load_dataset("zou-lab/MedCaseReasoning", split=split)
                if max_samples:
                    dataset = dataset.select(range(min(max_samples, len(dataset))))
                cases = [dict(x) for x in dataset]
                logger.info(f"Loaded {len(cases)} cases.")
                return cases
            except Exception as e:
                logger.error(f"Failed to load MedCaseReasoning dataset: {e}")
                return []
        else:
            logger.warning("datasets library not available. Returning mock cases.")
            # Mock data for testing
            cases = [
                {"case_id": i, "reasoning": "Sample reasoning pattern", "traceability": True}
                for i in range(max_samples)
            ]
            logger.info(f"Loaded {len(cases)} mock cases.")
            return cases

if __name__ == "__main__":
    loader = MedCaseReasoningLoader()
    cases = loader.load_cases(max_samples=10)
    for case in cases:
        print(case)
