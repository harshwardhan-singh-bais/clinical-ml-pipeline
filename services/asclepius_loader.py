"""
Asclepius Dataset Loader
Loads synthetic clinical notes for validation and testing.
"""

import logging
from datasets import load_dataset
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AsclepiusDatasetLoader:
    """
    Loads Asclepius synthetic clinical notes.
    
    Purpose: Validation and testing, NOT runtime evidence.
    """
    
    def __init__(self):
        """Initialize Asclepius loader."""
        logger.info("Initializing Asclepius Dataset Loader...")
        self.dataset = None
        self._load_dataset()
    
    def _load_dataset(self):
        """Load Asclepius dataset from Hugging Face."""
        try:
            logger.info("Loading Asclepius dataset from Hugging Face...")
            self.dataset = load_dataset("starmpcc/Asclepius-Synthetic-Clinical-Notes", split="train")
            logger.info(f"✅ Loaded {len(self.dataset)} Asclepius notes")
        except Exception as e:
            logger.error(f"Failed to load Asclepius dataset: {e}")
            self.dataset = None
    
    def get_random_samples(self, count: int = 5) -> List[str]:
        """Get random clinical notes for testing."""
        if not self.dataset:
            return []
        
        import random
        indices = random.sample(range(len(self.dataset)), min(count, len(self.dataset)))
        samples = [self.dataset[i].get("note", "") for i in indices]
        return [s for s in samples if s.strip()]
    
    def get_note_by_index(self, index: int) -> Optional[str]:
        """Get specific note by index."""
        if not self.dataset or index >= len(self.dataset):
            return None
        return self.dataset[index].get("note", "")
