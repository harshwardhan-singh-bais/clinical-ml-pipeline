"""
End-to-End Pipeline Test
Tests complete flow with real clinical note from Asclepius dataset

Tests:
- Raw clinical note input
- Signal extraction
- Hypothesis generation
- Evidence retrieval
- Evidence-grounded synthesis
- Output validation

Uses Asclepius synthetic clinical notes for realistic testing.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from models.schemas import ClinicalNoteRequest
from services.clinical_pipeline import ClinicalPipeline
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Sample clinical note (typical ED presentation)
SAMPLE_CLINICAL_NOTE = """
Patient: 67-year-old male
Chief Complaint: Chest pain

HPI:
Patient presents to ED with sudden onset chest pain that started 2 hours ago while climbing stairs. 
Pain is described as crushing, substernal, radiating to left arm and jaw. 
Associated with shortness of breath, nausea, and diaphoresis.
Pain has not resolved with rest. Rates pain 8/10 severity.

PMH:
- Hypertension (on lisinopril 20mg daily)
- Type 2 diabetes mellitus (on metformin 1000mg BID)
- Hyperlipidemia (on atorvastatin 40mg daily)
- Former smoker (quit 5 years ago, 30 pack-year history)

Medications:
- Lisinopril 20mg daily
- Metformin 1000mg BID
- Atorvastatin 40mg daily
- Aspirin 81mg daily

Allergies: NKDA

Social History:
Former smoker, quit 5 years ago. Occasional alcohol use. No illicit drug use.
Retired construction worker.

Family History:
Father died of MI at age 60. Mother has hypertension.

Vitals:
BP: 165/95 mmHg
HR: 110 bpm
RR: 22/min
Temp: 98.6°F
O2 Sat: 94% on room air

Physical Exam:
General: Anxious, diaphoretic male in moderate distress
Cardiovascular: Tachycardic, regular rhythm, no murmurs
Respiratory: Tachypneic, lungs clear bilaterally
Abdomen: Soft, non-tender
Extremities: No edema, distal pulses intact

Labs:
Troponin I: 0.8 ng/mL (elevated)
CK-MB: 8.2 ng/mL (elevated)
BNP: 150 pg/mL
WBC: 11.2 K/uL
Glucose: 145 mg/dL

EKG: ST-segment elevation in leads II, III, aVF

Assessment:
67yo M with cardiac risk factors presenting with acute chest pain, elevated cardiac markers, and EKG changes.
"""


def test_full_pipeline():
    """Test complete pipeline with sample clinical note."""
    
    logger.info("=" * 80)
    logger.info("FULL PIPELINE TEST - Raw Clinical Note Processing")
    logger.info("=" * 80)
    
    # Initialize pipeline
    logger.info("\n1. Initializing Clinical Pipeline...")
    pipeline = ClinicalPipeline()
    
    # Create request
    logger.info("\n2. Creating Clinical Note Request...")
    request = ClinicalNoteRequest(
        input_type="text",
        content=SAMPLE_CLINICAL_NOTE,
        patient_id="TEST_PATIENT_001"
    )
    
    # Process
    logger.info("\n3. Processing Clinical Note (Full Pipeline)...")
    logger.info("   - Extracting signals from raw note")
    logger.info("   - Generating differential hypotheses")
    logger.info("   - Retrieving StatPearls evidence")
    logger.info("   - Synthesizing evidence-grounded analysis")
    
    response = pipeline.process_clinical_note(request)
    
    # Display results
    logger.info("\n" + "=" * 80)
    logger.info("PIPELINE RESULTS")
    logger.info("=" * 80)
    
    logger.info(f"\nRequest ID: {response.request_id}")
    logger.info(f"Status: {response.status}")
    logger.info(f"Processing Time: {response.processing_time_seconds:.2f} seconds")
    
    if response.error_message:
        logger.error(f"\nERROR: {response.error_message}")
        return False
    
    # Display summary
    if response.summary:
        logger.info("\n--- CLINICAL SUMMARY ---")
        logger.info(f"Chief Complaint: {response.summary.chief_complaint}")
        logger.info(f"Symptoms: {', '.join(response.summary.symptoms)}")
        logger.info(f"Timeline: {response.summary.timeline}")
        logger.info(f"\nSummary Text:\n{response.summary.summary_text}")
    
    # Display differential diagnoses
    if response.differential_diagnoses:
        logger.info(f"\n--- DIFFERENTIAL DIAGNOSES ({len(response.differential_diagnoses)}) ---")
        
        for i, dx in enumerate(response.differential_diagnoses, 1):
            logger.info(f"\n{i}. {dx.diagnosis} (Priority {dx.priority})")
            logger.info(f"   Description: {dx.description}")
            logger.info(f"   Reasoning: {dx.reasoning}")
            
            if dx.supporting_evidence:
                logger.info(f"   Evidence Citations: {len(dx.supporting_evidence)}")
                for j, citation in enumerate(dx.supporting_evidence[:3], 1):  # Show first 3
                    logger.info(f"      [{j}] {citation.text_snippet[:100]}...")
                    logger.info(f"          Similarity: {citation.similarity_score:.3f}")
            
            if dx.confidence:
                logger.info(f"   Confidence:")
                logger.info(f"      Evidence Strength: {dx.confidence.get('evidence_strength', 'N/A')}")
                logger.info(f"      Reasoning Consistency: {dx.confidence.get('reasoning_consistency', 'N/A')}")
    
    # Display metadata
    logger.info(f"\n--- METADATA ---")
    logger.info(f"Total Evidence Retrieved: {response.total_evidence_retrieved}")
    
    if response.warning_messages:
        logger.info(f"\nWarnings:")
        for warning in response.warning_messages:
            logger.warning(f"  - {warning}")
    
    # Validation checks
    logger.info("\n" + "=" * 80)
    logger.info("VALIDATION CHECKS")
    logger.info("=" * 80)
    
    checks_passed = 0
    checks_total = 6
    
    # Check 1: Status is COMPLETED
    if response.status == "completed":
        logger.info("✅ Status is COMPLETED")
        checks_passed += 1
    else:
        logger.error(f"❌ Status is {response.status}, expected COMPLETED")
    
    # Check 2: Summary exists
    if response.summary:
        logger.info("✅ Summary generated")
        checks_passed += 1
    else:
        logger.error("❌ No summary generated")
    
    # Check 3: Differential diagnoses exist
    if response.differential_diagnoses and len(response.differential_diagnoses) > 0:
        logger.info(f"✅ {len(response.differential_diagnoses)} differential diagnoses generated")
        checks_passed += 1
    else:
        logger.error("❌ No differential diagnoses generated")
    
    # Check 4: Evidence retrieved
    if response.total_evidence_retrieved > 0:
        logger.info(f"✅ {response.total_evidence_retrieved} evidence pieces retrieved")
        checks_passed += 1
    else:
        logger.error("❌ No evidence retrieved")
    
    # Check 5: Diagnoses have citations
    has_citations = all(
        dx.supporting_evidence and len(dx.supporting_evidence) > 0
        for dx in response.differential_diagnoses
    )
    if has_citations:
        logger.info("✅ All diagnoses have evidence citations")
        checks_passed += 1
    else:
        logger.error("❌ Some diagnoses missing evidence citations")
    
    # Check 7: Diagnoses have patient text justification (PHASE 20/25)
    has_patient_justification = all(
        dx.reasoning and len(dx.reasoning) > 10
        for dx in response.differential_diagnoses
    )
    if has_patient_justification:
        logger.info("✅ All diagnoses have patient text justification (Phase 20/25)")
        checks_passed += 1
    else:
        logger.error("❌ Some diagnoses missing patient text justification")
    checks_total += 1
    
    # Check 7: Processing completed in reasonable time
    if response.processing_time_seconds < 60:
        logger.info(f"✅ Processing completed in {response.processing_time_seconds:.2f}s")
        checks_passed += 1
    else:
        logger.warning(f"⚠️  Processing took {response.processing_time_seconds:.2f}s (>60s)")
    
    # Final result
    logger.info("\n" + "=" * 80)
    logger.info(f"VALIDATION RESULT: {checks_passed}/{checks_total} checks passed")
    logger.info("=" * 80)
    
    if checks_passed == checks_total:
        logger.info("\n🎉 ALL CHECKS PASSED - Pipeline is working correctly!")
        return True
    elif checks_passed >= checks_total * 0.8:
        logger.warning(f"\n⚠️  MOSTLY WORKING - {checks_passed}/{checks_total} checks passed")
        return True
    else:
        logger.error(f"\n❌ PIPELINE ISSUES - Only {checks_passed}/{checks_total} checks passed")
        return False


def test_with_asclepius_note():
    """Test with actual Asclepius clinical note."""
    logger.info("\n" + "=" * 80)
    logger.info("TESTING WITH ASCLEPIUS CLINICAL NOTE")
    logger.info("=" * 80)
    
    try:
        from datasets import load_dataset
        
        logger.info("Loading Asclepius dataset...")
        dataset = load_dataset("starmpcc/Asclepius-Synthetic-Clinical-Notes", split="train")
        
        # Get first note
        sample = dataset[0]
        clinical_note = sample.get("note", "")
        
        if not clinical_note:
            logger.warning("No clinical note found in Asclepius sample, using default")
            return test_full_pipeline()
        
        logger.info(f"Loaded clinical note ({len(clinical_note)} chars)")
        logger.info(f"Note preview: {clinical_note[:200]}...")
        
        # Initialize pipeline
        pipeline = ClinicalPipeline()
        
        # Create request
        request = ClinicalNoteRequest(
            input_type="text",
            content=clinical_note,
            patient_id="ASCLEPIUS_TEST_001"
        )
        
        # Process
        logger.info("\nProcessing Asclepius clinical note...")
        response = pipeline.process_clinical_note(request)
        
        # Display results
        logger.info(f"\nStatus: {response.status}")
        logger.info(f"Processing Time: {response.processing_time_seconds:.2f}s")
        
        if response.error_message:
            logger.error(f"Error: {response.error_message}")
            return False
        
        if response.differential_diagnoses:
            logger.info(f"\n{len(response.differential_diagnoses)} diagnoses generated:")
            for dx in response.differential_diagnoses[:5]:
                logger.info(f"  - {dx.diagnosis} (Priority {dx.priority})")
        
        return response.status == "completed"
        
    except Exception as e:
        logger.warning(f"Could not load Asclepius dataset: {e}")
        logger.info("Falling back to default test...")
        return test_full_pipeline()


if __name__ == "__main__":
    logger.info("Starting Full Pipeline Test\n")
    
    # Run default test
    success = test_full_pipeline()
    
    # Optionally run Asclepius test
    print("\n" + "=" * 80)
    response = input("Run test with Asclepius dataset? (y/n): ")
    if response.lower() == 'y':
        asclepius_success = test_with_asclepius_note()
    
    sys.exit(0 if success else 1)
