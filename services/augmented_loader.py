"""
Augmented Clinical Notes Dataset Loader
Loads noisy/corrupted notes for robustness testing.
"""

import logging
from datasets import load_dataset
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AugmentedNotesLoader:
    """
    Loads Augmented Clinical Notes dataset.
    
    Purpose: Robustness testing, NOT runtime evidence.
    """
    
    def __init__(self):
        """Initialize Augmented Notes loader."""
        logger.info("Initializing Augmented Notes Dataset Loader...")
        self.dataset = None
        self._load_dataset()
    
    def _load_dataset(self):
        """Load Augmented dataset from Hugging Face."""
        try:
            logger.info("Loading Augmented Notes dataset from Hugging Face...")
            self.dataset = load_dataset("AG Bonnet/augmented-clinical-notes", split="train")
            logger.info(f"✅ Loaded {len(self.dataset)} Augmented notes")
        except Exception as e:
            logger.error(f"Failed to load Augmented dataset: {e}")
            logger.warning("Augmented notes will not be available for testing")
            self.dataset = None
    
    def get_random_samples(self, count: int = 5) -> List[str]:
        """Get random noisy notes for testing."""
        if not self.dataset:
            return []
        
        import random
        indices = random.sample(range(len(self.dataset)), min(count, len(self.dataset)))
        samples = [self.dataset[i].get("text", "") for i in indices]
        return [s for s in samples if s.strip()]
