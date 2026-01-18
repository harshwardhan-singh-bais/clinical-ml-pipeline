"""
Open-Patients Dataset Ingestion with "Patient Journey" Filtering
Filters 180k cases down to 2000 (test mode) using narrative-based rules.
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from datasets import load_dataset
from typing import Dict, List
from services.qdrant_service import QdrantService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test mode: 2000 chunks max
MAX_CHUNKS = 2000

# Patient Journey Filtering Rules
PATIENT_ANCHORS = ["year-old", "years old", "male", "female", "patient", "man", "woman", "pt"]

CLINICAL_ACTION_VERBS = [
    "presented", "admitted", "complained", "diagnosed", "revealed",
    "experienced", "reported", "developed", "noted", "demonstrated",
    "showed", "was found to have", "displayed", "exhibited"
]

TEMPORALITY_MARKERS = [
    "days later", "on admission", "initially", "subsequently",
    "prior to", "history of", "on examination", "at presentation",
    "during evaluation", "after", "before", "following"
]

REASONING_SIGNALS = [
    "suggestive of", "consistent with", "differential", "ruled out",
    "likely", "suspicion", "assessment", "diagnosis", "suspected",
    "compatible with", "indicative of"
]


def passes_patient_journey_filter(text: str) -> Dict:
    """
    Apply "Patient Journey" filtering logic.
    
    Returns:
        Dict with 'passes' (bool) and 'score' (int)
    """
    text_lower = text.lower()
    score = 0
    
    # Level 1: Patient Anchor (Mandatory)
    has_anchor = any(anchor in text_lower for anchor in PATIENT_ANCHORS)
    if not has_anchor:
        return {"passes": False, "score": 0, "reason": "No patient anchor"}
    score += 1
    
    # Level 1: Clinical Action Verbs (≥2 required)
    verb_count = sum(1 for verb in CLINICAL_ACTION_VERBS if verb in text_lower)
    if verb_count < 2:
        return {"passes": False, "score":score, "reason": f"Only {verb_count} action verbs"}
    score += verb_count
    
    # Level 2: Temporality (Required)
    has_temporality = any(marker in text_lower for marker in TEMPORALITY_MARKERS)
    if not has_temporality:
        return {"passes": False, "score": score, "reason": "No temporality markers"}
    score += 2
    
    # Level 3: Reasoning Signal (≥1 required)
    reasoning_count = sum(1 for signal in REASONING_SIGNALS if signal in text_lower)
    if reasoning_count < 1:
        return {"passes": False, "score": score, "reason": "No reasoning signals"}
    score += reasoning_count
    
    # Level 4: Length (150-700 chars)
    if len(text) < 150:
        return {"passes": False, "score": score, "reason": "Too short"}
    if len(text) > 3000:
        return {"passes": False, "score": score, "reason": "Too long"}
    
    return {"passes": True, "score": score}


def ingest_open_patients():
    """Load and filter Open-Patients dataset, then insert into Qdrant."""
    logger.info("="*80)
    logger.info("OPEN-PATIENTS INGESTION (TEST MODE: 2000 CHUNKS)")
    logger.info("="*80)
    
    # Initialize Qdrant
    qdrant = QdrantService()
    if not qdrant.client:
        logger.error("❌ Qdrant client initialization failed. Aborting.")
        return
    
    # Load dataset
    logger.info("Loading Open-Patients dataset from Hugging Face...")
    try:
        dataset = load_dataset("ncbi/Open-Patients", split="train")
        logger.info(f"✅ Loaded {len(dataset)} total cases")
    except Exception as e:
        logger.error(f"❌ Failed to load dataset: {e}")
        return
    
    # Filter chunks
    logger.info("\n" + "="*80)
    logger.info("FILTERING WITH 'PATIENT JOURNEY' LOGIC")
    logger.info("="*80)
    
    filtered_chunks = []
    passed = 0
    failed = 0
    
    for idx, row in enumerate(dataset):
        if len(filtered_chunks) >= MAX_CHUNKS:
            logger.info(f"✅ Reached MAX_CHUNKS ({MAX_CHUNKS}). Stopping.")
            break
        
        try:
            description = row.get("description", "")
            if not description.strip():
                failed += 1
                continue
            
            # Apply filter
            filter_result = passes_patient_journey_filter(description)
            
            if filter_result["passes"]:
                filtered_chunks.append({
                    "id": idx,
                    "text": description.strip(),
                    "case_id": row.get("_id", f"open-patients-{idx}"),
                    "score": filter_result["score"]
                })
                passed += 1
            else:
                failed += 1
            
            # Progress logging
            if (passed + failed) % 5000 == 0:
                logger.info(f"Processed: {passed + failed} | Passed: {passed} | Failed: {failed}")
        
        except Exception as e:
            logger.debug(f"Error processing row {idx}: {e}")
            failed += 1
            continue
    
    logger.info("\n" + "="*80)
    logger.info(f"FILTERING COMPLETE")
    logger.info(f"Total Processed: {passed + failed}")
    logger.info(f"Passed Filter: {passed}")
    logger.info(f"Failed Filter: {failed}")
    logger.info(f"Selected for Ingestion: {len(filtered_chunks)}")
    logger.info("="*80)
    
    if not filtered_chunks:
        logger.error("❌ No chunks passed the filter!")
        return
    
    # Sort by score and take top chunks
    filtered_chunks = sorted(filtered_chunks, key=lambda x: x["score"], reverse=True)[:MAX_CHUNKS]
    
    # Insert into Qdrant in batches
    logger.info("\n" + "="*80)
    logger.info("INSERTING INTO QDRANT")
    logger.info("="*80)
    
    batch_size = 100
    for i in range(0, len(filtered_chunks), batch_size):
        batch = filtered_chunks[i:i+batch_size]
        qdrant.insert_batch(batch)
        logger.info(f"Inserted batch {i//batch_size + 1}/{(len(filtered_chunks) + batch_size - 1)//batch_size}")
    
    # Show stats
    stats = qdrant.get_collection_stats()
    logger.info("\n" + "="*80)
    logger.info("INGESTION COMPLETE")
    logger.info(f"Qdrant Collection Stats: {stats}")
    logger.info("="*80)


if __name__ == "__main__":
    ingest_open_patients()
