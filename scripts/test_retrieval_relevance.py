"""
Verification Script: Test Retrieval Relevance
---------------------------------------------
Tests if the Supabase Vector Store contains RELEVANT chunks for
the user's top critical clinical inputs.

Usage: python scripts/test_retrieval_relevance.py
"""

import sys
import os
import logging
from typing import List

# Setup path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.retrieval import RAGRetriever
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Verification")

def test_query(retriever, query_text: str, expected_keyword: str):
    """
    Test a single query and check if results match expectation.
    """
    logger.info(f"\nTesting Query: '{query_text}'")
    logger.info(f"Looking for evidence containing: '{expected_keyword}'")
    
    # Run Retrieval
    results = retriever.retrieve_for_single_query(
        query_text=query_text,
        top_k=5
    )
    
    if not results:
        logger.error("❌ FAILED: No results returned from Vector DB.")
        return False
        
    # Check relevance
    found_relevant = False
    for res in results:
        title = res.get("title", "").lower()
        content = res.get("text", "").lower()
        
        # Check if title or content matches expected keyword
        if expected_keyword.lower() in title or expected_keyword.lower() in content:
            logger.info(f"✅ MATCH FOUND: {res.get('title')} (Score: {res.get('similarity_score', 0):.3f})")
            found_relevant = True
            break
            
    if not found_relevant:
        logger.warning("⚠ WARNING: Results found, but none contained the expected keyword.")
        logger.info("Top Result was: " + results[0].get("title", "Unknown"))
        return False
        
    return True

def main():
    logger.info("Initializing Retriever connection to Supabase...")
    retriever = RAGRetriever()
    
    # The Critical List (from user's SOAP notes)
    test_cases = [
        ("Evidence of Heart Failure exacerbation with orthopnea", "Heart Failure"),
        ("New onset Seizure with tonic-clonic activity", "Seizure"),
        ("Uncontrolled Diabetes Mellitus type 2 hyperglycemia", "Diabetes"),
        ("Acute Appendicitis with RLQ pain", "Appendicitis"),
        ("COPD exacerbation with shortness of breath", "COPD")
    ]
    
    score = 0
    for query, keyword in test_cases:
        if test_query(retriever, query, keyword):
            score += 1
            
    logger.info("="*60)
    logger.info(f"VERIFICATION SCORE: {score}/{len(test_cases)}")
    
    if score == len(test_cases):
        logger.info("✅ SUCCESS: High-Value Clinical Topics are indexable!")
    elif score > 0:
        logger.info("⚠ PARTIAL SUCCESS: Some topics missing.")
    else:
        logger.info("❌ FAILURE: Database does not contain critical topics.")
    logger.info("="*60)

if __name__ == "__main__":
    main()
