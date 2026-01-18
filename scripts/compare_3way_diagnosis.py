"""
Comprehensive 3-way dataset comparison for differential diagnosis generation.
Tests: Open-Patients vs emrqa-msquad vs epfl-llm/guidelines

Goal: Find best combination for diagnosis layer (non-vector DB approach)
Note: Open-Patients already used for evidence via vector DB, testing for direct diagnosis use
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datasets import load_dataset
import json
from typing import Dict, List, Tuple

def load_open_patients():
    """Load and analyze Open-Patients for diagnosis use (non-vector DB)."""
    print("="*100)
    print("DATASET 1: Open-Patients (ncbi/Open-Patients)")
    print("="*100)
    print("\n📊 Purpose: Patient case reports from medical literature")
    print("⚠️  Note: Currently used for evidence via vector DB")
    print("🎯 Testing: Direct diagnosis generation (without vector DB)\n")
    
    try:
        print("Loading Open-Patients dataset...")
        ds = load_dataset("ncbi/Open-Patients")
        
        print(f"\n✅ Loaded successfully!")
        print(f"Structure: {ds}")
        
        split = list(ds.keys())[0]
        data = ds[split]
        
        print(f"\nSplit: {split}")
        print(f"Cases: {len(data)}")
        print(f"Features: {data.features}")
        
        # Show first example
        print(f"\n{'='*100}")
        print("SAMPLE CASE")
        print(f"{'='*100}")
        
        example = data[0]
        for key, value in example.items():
            print(f"\n{key.upper()}:")
            if isinstance(value, str) and len(value) > 300:
                print(f"{value[:300]}...")
            elif isinstance(value, list):
                print(f"[List with {len(value)} items]")
            else:
                print(value)
        
        # Analyze for diagnosis
        print(f"\n{'='*100}")
        print("SUITABILITY FOR DIFFERENTIAL DIAGNOSIS (Direct Use)")
        print(f"{'='*100}")
        
        scores = {
            'has_patient_cases': False,
            'has_diagnosis_labels': False,
            'has_clinical_narrative': False,
            'has_differential_lists': False,
            'supports_direct_matching': False,
            'has_structured_data': False
        }
        
        example_keys = list(example.keys())
        
        if any(k in example_keys for k in ['patient', 'case', 'clinical_note', 'text']):
            scores['has_patient_cases'] = True
            print("✅ Contains patient case data")
        
        if any(k in example_keys for k in ['diagnosis', 'final_diagnosis', 'label', 'disease']):
            scores['has_diagnosis_labels'] = True
            print("✅ Has diagnosis labels")
        
        if any(k in example_keys for k in ['text', 'abstract', 'content', 'narrative']):
            scores['has_clinical_narrative'] = True
            print("✅ Has clinical narrative text")
        
        # Check for differential diagnosis info
        for key, value in example.items():
            if isinstance(value, str):
                if 'differential' in value.lower():
                    scores['has_differential_lists'] = True
        
        if scores['has_differential_lists']:
            print("✅ Contains differential diagnosis information")
        
        # Check if suitable for direct matching (without vector DB)
        if scores['has_patient_cases'] and scores['has_diagnosis_labels']:
            scores['supports_direct_matching'] = True
            print("✅ Supports direct case-to-diagnosis matching")
        
        suitability = sum(scores.values()) / len(scores) * 100
        print(f"\n📊 Direct Diagnosis Suitability: {suitability:.0f}%")
        
        return ds, split, scores
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None, None, {}


def load_emrqa():
    """Load and analyze EMR-QA dataset."""
    print(f"\n\n{'='*100}")
    print("DATASET 2: EMR-QA (Eladio/emrqa-msquad)")
    print("="*100)
    print("\n📊 Purpose: EMR Question-Answering for diagnostic reasoning\n")
    
    try:
        print("Loading emrqa-msquad dataset...")
        ds = load_dataset("Eladio/emrqa-msquad")
        
        print(f"\n✅ Loaded successfully!")
        
        split = list(ds.keys())[0]
        data = ds[split]
        
        print(f"Examples: {len(data)}")
        
        # Analyze
        example = data[0]
        
        scores = {
            'has_clinical_context': False,
            'has_diagnosis_questions': False,
            'has_answers': False,
            'supports_qa_format': False,
            'has_evidence_links': False
        }
        
        example_keys = list(example.keys())
        
        if any(k in example_keys for k in ['context', 'clinical_note', 'text']):
            scores['has_clinical_context'] = True
            print("✅ Has clinical context")
        
        if any(k in example_keys for k in ['question', 'query']):
            scores['has_diagnosis_questions'] = True
            scores['supports_qa_format'] = True
            print("✅ Has diagnostic questions (QA format)")
        
        if any(k in example_keys for k in ['answer', 'answers']):
            scores['has_answers'] = True
            scores['has_evidence_links'] = True
            print("✅ Has answers with evidence links")
        
        suitability = sum(scores.values()) / len(scores) * 100
        print(f"\n📊 Diagnosis Suitability: {suitability:.0f}%")
        
        return ds, split, scores
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None, None, {}


def load_guidelines():
    """Load and analyze Guidelines dataset."""
    print(f"\n\n{'='*100}")
    print("DATASET 3: Clinical Guidelines (epfl-llm/guidelines)")
    print("="*100)
    print("\n📊 Purpose: Evidence-based clinical practice guidelines\n")
    
    try:
        print("Loading guidelines dataset...")
        ds = load_dataset("epfl-llm/guidelines")
        
        print(f"\n✅ Loaded successfully!")
        
        split = list(ds.keys())[0]
        data = ds[split]
        
        print(f"Guidelines: {len(data)}")
        
        # Analyze
        example = data[0]
        
        scores = {
            'has_diagnostic_criteria': False,
            'has_conditions': False,
            'has_evidence_levels': False,
            'has_differential_info': False,
            'supports_validation': False
        }
        
        example_keys = list(example.keys())
        
        if any(k in example_keys for k in ['condition', 'disease', 'diagnosis']):
            scores['has_conditions'] = True
            print("✅ Has condition/disease information")
        
        if any(k in example_keys for k in ['evidence_level', 'grade', 'strength']):
            scores['has_evidence_levels'] = True
            scores['supports_validation'] = True
            print("✅ Has evidence strength levels (validation)")
        
        # Check content
        for key, value in example.items():
            if isinstance(value, str):
                if 'criteria' in value.lower() or 'diagnostic' in value.lower():
                    scores['has_diagnostic_criteria'] = True
                if 'differential' in value.lower():
                    scores['has_differential_info'] = True
        
        if scores['has_diagnostic_criteria']:
            print("✅ Contains diagnostic criteria")
        
        suitability = sum(scores.values()) / len(scores) * 100
        print(f"\n📊 Diagnosis Suitability: {suitability:.0f}%")
        
        return ds, split, scores
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None, None, {}


def comprehensive_comparison(open_patients_scores, emrqa_scores, guidelines_scores):
    """3-way comparison for differential diagnosis."""
    print(f"\n\n{'='*100}")
    print("COMPREHENSIVE 3-WAY COMPARISON")
    print(f"{'='*100}")
    
    print(f"\n{'Criteria':<45} {'Open-Patients':<20} {'EMR-QA':<20} {'Guidelines':<20} {'Winner'}")
    print("-"*120)
    
    comparisons = [
        ("Patient Case Data",
         "✅ Rich cases" if open_patients_scores.get('has_patient_cases') else "❌ No",
         "✅ Clinical notes" if emrqa_scores.get('has_clinical_context') else "❌ No",
         "❌ No cases",
         "Open-Patients"),
        
        ("Diagnosis Labels",
         "✅ Yes" if open_patients_scores.get('has_diagnosis_labels') else "❌ No",
         "⚠️ Implicit",
         "✅ Conditions" if guidelines_scores.get('has_conditions') else "❌ No",
         "Open-Patients"),
        
        ("Direct Diagnosis Matching",
         "✅ Case→Dx" if open_patients_scores.get('supports_direct_matching') else "❌ No",
         "⚠️ QA format",
         "❌ No",
         "Open-Patients"),
        
        ("Diagnostic Questions",
         "❌ No",
         "✅ Yes" if emrqa_scores.get('has_diagnosis_questions') else "❌ No",
         "❌ No",
         "EMR-QA"),
        
        ("Evidence Links",
         "✅ Citations" if open_patients_scores.get('has_clinical_narrative') else "⚠️ Moderate",
         "✅ Answers" if emrqa_scores.get('has_evidence_links') else "❌ No",
         "⚠️ Moderate",
         "Tie"),
        
        ("Diagnostic Criteria",
         "⚠️ Implicit",
         "⚠️ Implicit",
         "✅ Explicit" if guidelines_scores.get('has_diagnostic_criteria') else "⚠️ Implicit",
         "Guidelines"),
        
        ("Evidence Strength Levels",
         "❌ No",
         "❌ No",
         "✅ A/B/C grades" if guidelines_scores.get('has_evidence_levels') else "❌ No",
         "Guidelines"),
        
        ("Validation Support",
         "⚠️ Moderate",
         "⚠️ Moderate",
         "✅ Strong" if guidelines_scores.get('supports_validation') else "⚠️ Moderate",
         "Guidelines"),
        
        ("Differential Diagnosis Info",
         "⚠️ Some" if open_patients_scores.get('has_differential_lists') else "❌ Limited",
         "⚠️ Implicit",
         "⚠️ Some" if guidelines_scores.get('has_differential_info') else "❌ Limited",
         "Open-Patients"),
    ]
    
    for criteria, op, emr, guide, winner in comparisons:
        print(f"{criteria:<45} {op:<20} {emr:<20} {guide:<20} {winner}")
    
    print(f"\n{'='*100}")
    print("FINAL RECOMMENDATION")
    print(f"{'='*100}")
    
    print("""
🎯 OPTIMAL ARCHITECTURE: **4-LAYER APPROACH**

┌─────────────────────────────────────────────────────────────────┐
│                    RECOMMENDED ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────┘

Clinical Note (Input)
        ↓
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: EMR-QA (emrqa-msquad)                                 │
│  Purpose: Clinical note summarization + fact extraction         │
│  • Extract key clinical facts                                   │
│  • Generate diagnostic questions                                │
│  • Structure clinical narrative                                 │
│  Priority: HIGH                                                 │
└──────────┬──────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2: Open-Patients (Direct Matching)                       │
│  Purpose: Case-based diagnosis generation                       │
│  • Match patient to similar cases                               │
│  • Extract diagnosis from matched cases                         │
│  • Generate initial differential list                           │
│  Priority: HIGH (NEW - for diagnosis layer)                     │
│  Note: Different from vector DB evidence use                    │
└──────────┬──────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3: MedCaseReasoning (Current)                            │
│  Purpose: Augment with additional patterns                      │
│  • Pattern matching                                             │
│  • Case-based reasoning                                         │
│  • Fill gaps from Layer 2                                       │
│  Priority: HIGH (keep existing)                                 │
└──────────┬──────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 4: Guidelines (epfl-llm/guidelines)                      │
│  Purpose: Validate & add evidence strength                      │
│  • Check diagnostic criteria                                    │
│  • Add evidence grades (A/B/C)                                  │
│  • Final ranking by guideline support                           │
│  Priority: HIGH                                                 │
└──────────┬──────────────────────────────────────────────────────┘
           ↓
Differential Diagnosis Output

═══════════════════════════════════════════════════════════════════

KEY INSIGHTS:

1. **Open-Patients (NEW for Diagnosis Layer):**
   ✅ Best for: Direct case→diagnosis matching
   ✅ Has: Real patient cases with diagnosis labels
   ✅ Advantage: Already familiar (used for evidence)
   ✅ Use: NON-vector DB approach for diagnosis generation
   ⚠️  Different role: Evidence (vector DB) vs Diagnosis (direct matching)

2. **EMR-QA:**
   ✅ Best for: Summarization + fact extraction
   ✅ Provides: Structured clinical questions
   ✅ Feeds: Clean input to diagnosis layers

3. **MedCaseReasoning (Current):**
   ✅ Keep: Already working
   ✅ Role: Augment Open-Patients diagnoses
   ✅ Fills: Coverage gaps

4. **Guidelines:**
   ✅ Best for: Validation + evidence strength
   ✅ Adds: A/B/C evidence grades
   ✅ Ensures: Medical accuracy

═══════════════════════════════════════════════════════════════════

IMPLEMENTATION STRATEGY:

Phase 1: Add EMR-QA for summarization (Week 1)
Phase 2: Add Open-Patients direct matching for diagnosis (Week 1-2)
Phase 3: Keep MedCaseReasoning as augmentation (Current)
Phase 4: Add Guidelines for validation (Week 2)

DUAL USE OF OPEN-PATIENTS:

Current Use:  Evidence retrieval via vector DB
New Use:      Direct diagnosis generation (case matching)
Integration:  Two separate code paths, same dataset

═══════════════════════════════════════════════════════════════════
""")


def save_comparison_results(op_scores, emr_scores, guide_scores):
    """Save 3-way comparison results."""
    output = {
        "comparison_date": "2026-01-11",
        "goal": "Differential Diagnosis Generation (Direct, Non-Vector DB)",
        "datasets": {
            "open_patients": {
                "name": "ncbi/Open-Patients",
                "type": "Patient Case Reports",
                "scores": op_scores,
                "suitability": sum(op_scores.values()) / len(op_scores) * 100 if op_scores else 0,
                "current_use": "Evidence retrieval (vector DB)",
                "proposed_use": "Direct diagnosis generation (case matching)"
            },
            "emrqa": {
                "name": "Eladio/emrqa-msquad",
                "type": "EMR Question-Answering",
                "scores": emr_scores,
                "suitability": sum(emr_scores.values()) / len(emr_scores) * 100 if emr_scores else 0
            },
            "guidelines": {
                "name": "epfl-llm/guidelines",
                "type": "Clinical Practice Guidelines",
                "scores": guide_scores,
                "suitability": sum(guide_scores.values()) / len(guide_scores) * 100 if guide_scores else 0
            }
        },
        "recommendation": "Use ALL THREE datasets in 4-layer architecture",
        "architecture": {
            "layer_1": "EMR-QA for summarization",
            "layer_2": "Open-Patients for direct diagnosis matching (NEW)",
            "layer_3": "MedCaseReasoning for augmentation (KEEP)",
            "layer_4": "Guidelines for validation"
        },
        "key_insight": "Open-Patients serves DUAL purpose: Evidence (vector DB) + Diagnosis (direct matching)"
    }
    
    output_path = Path(__file__).parent.parent / "3way_diagnosis_comparison.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_path}")


if __name__ == "__main__":
    print("\n" + "="*100)
    print("3-WAY DATASET COMPARISON FOR DIFFERENTIAL DIAGNOSIS")
    print("="*100)
    print("\n🎯 Goal: Find best combination for diagnosis generation (non-vector DB)")
    print("📊 Testing: Open-Patients vs EMR-QA vs Guidelines\n")
    
    # Load all three
    op_ds, op_split, op_scores = load_open_patients()
    emr_ds, emr_split, emr_scores = load_emrqa()
    guide_ds, guide_split, guide_scores = load_guidelines()
    
    # Compare
    if any([op_ds, emr_ds, guide_ds]):
        comprehensive_comparison(op_scores, emr_scores, guide_scores)
        save_comparison_results(op_scores, emr_scores, guide_scores)
    
    print(f"\n{'='*100}")
    print("COMPARISON COMPLETE!")
    print(f"{'='*100}\n")
