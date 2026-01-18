"""
Add this to the END of clinical_pipeline_gold.py to make it directly executable
with comprehensive 35-phase logging.
"""

# ==================== DIRECT EXECUTION MODE ====================

if __name__ == "__main__":
    import sys
    
    # Configure detailed logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
    )
    
    print("=" * 100)
    print("🏥 CLINICAL ML PIPELINE - GOLD STANDARD EDITION")
    print("=" * 100)
    print("📊 All 35 Phases Enabled | Multi-Dataset Integration | Full Traceability")
    print("=" * 100)
    print()
    
    # Initialize pipeline
    print("🔧 Initializing Pipeline Components...")
    pipeline = ClinicalPipeline()
    print("✅ Pipeline Ready!")
    print()
    
    # Get input
    print("=" * 100)
    print("📝 ENTER CLINICAL NOTE")
    print("=" * 100)
    print("Paste your clinical note below (press Ctrl+Z then Enter on new line when done):")
    print("-" * 100)
    
    # Read multi-line input
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    clinical_note = "\n".join(lines)
    
    if not clinical_note.strip():
        print("❌ No input provided. Using sample note...")
        clinical_note = """
Patient: 65 y/o M
CC: SOB, chest tightness

HPI: Pt c/o increasing SOB x 3 days. Worse w/ exertion. C/o orthopnea - now sleeping on 3 pillows. 
Denies fever, denies cough. + bilateral leg swelling. 

PMHx: HTN, DM2, CAD s/p stent 2018

Exam:
- VS: BP 158/92, HR 98, RR 22, O2 sat 91% RA
- Gen: Mildly tachypneic, appears uncomfortable  
- CV: S3 gallop present, JVP elevated
- Lungs: Bibasilar crackles
- Extremities: 2+ pitting edema bilaterally

Labs:
- BNP: 1240 pg/mL (elevated)
- Troponin: 0.08 (mildly elevated)
- Cr: 1.4 (baseline 1.1)
"""
    
    print()
    print("=" * 100)
    print("⚙️  PROCESSING CLINICAL NOTE")
    print("=" * 100)
    print()
    
    # Create request
    request = ClinicalNoteRequest(
        input_type=InputType.TEXT,
        content=clinical_note,
        patient_id=f"DIRECT_EXEC_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    
    # Process with timing
    import time
    start_time = time.time()
    
    response = pipeline.process_clinical_note(request)
    
    elapsed = time.time() - start_time
    
    # Display results
    print()
    print("=" * 100)
    print("📊 RESULTS")
    print("=" * 100)
    print()
    print(f"Status: {response.status}")
    print(f"Processing Time: {elapsed:.2f}s")
    print(f"Total Evidence Retrieved: {response.total_evidence_retrieved}")
    print()
    
    if response.summary:
        print("-" * 100)
        print("📋 CLINICAL SUMMARY")
        print("-" * 100)
        print(f"Chief Complaint: {response.summary.chief_complaint}")
        print(f"Symptoms: {', '.join(response.summary.symptoms)}")
        print(f"Timeline: {response.summary.timeline}")
        print(f"\nSummary:\n{response.summary.summary_text}")
        print()
    
    if response.differential_diagnoses:
        print("-" * 100)
        print("🩺 DIFFERENTIAL DIAGNOSES")
        print("-" * 100)
        for dx in response.differential_diagnoses:
            print()
            print(f"{'[' + str(dx.priority) + ']':<5} {dx.diagnosis}")
            print(f"      Status: {dx.status}")
            print(f"      Confidence: {dx.confidence.overall_confidence:.1%}")
            print(f"      Evidence Strength: {dx.confidence.evidence_strength:.1%}")
            print(f"      Citations: {dx.confidence.citation_count}")
            
            if dx.patient_justification:
                print(f"      Justification: {', '.join(dx.patient_justification)}")
            
            if dx.supporting_evidence:
                print(f"      Evidence Sources ({len(dx.supporting_evidence)}):")
                for i, ev in enumerate(dx.supporting_evidence[:3], 1):
                    print(f"        {i}. {ev.chunk_id}")
                    if ev.similarity_score:
                        print(f"           Similarity: {ev.similarity_score:.1%}")
            
            print(f"      Reasoning: {dx.reasoning[:150]}...")
    
    # Save output
    output_file = f"OUTPUT_{request.patient_id}.json"
    import json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(response.model_dump(), f, indent=2, default=str)
    
    print()
    print("=" * 100)
    print(f"💾 Full output saved to: {output_file}")
    print("=" * 100)
    print()
    print("✅ Pipeline execution complete!")
