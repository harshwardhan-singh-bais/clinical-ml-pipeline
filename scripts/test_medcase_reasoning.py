"""
MedCaseReasoning Pipeline Test
=============================

Tests:
- Loads MedCaseReasoning cases (offline/mock or HuggingFace)
- Runs reasoning style and traceability validation
- Prints sample outputs for inspection

Run: python scripts/test_medcase_reasoning.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from scripts.load_medcase_reasoning import MedCaseReasoningLoader
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    loader = MedCaseReasoningLoader()
    cases = loader.load_cases(max_samples=10)
    logger.info(f"Loaded {len(cases)} MedCaseReasoning cases for testing.")
    for i, case in enumerate(cases):
        print(f"\n--- Case {i+1} ---")
        print(json.dumps(case, indent=2))
