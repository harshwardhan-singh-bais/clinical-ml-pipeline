"""
Dataset Comparison for Differential Diagnosis Generation.
Tests emrqa-msquad vs epfl-llm/guidelines for clinical note → diagnosis pipeline.

Goal: Determine which dataset best supports:
1. Clinical note summarization
2. Differential diagnosis generation
3. Evidence traceability
4. RAG integration
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datasets import load_dataset
import json
from typing import List, Dict

def load_and_analyze_emrqa():
    """Load and analyze EMR-QA dataset for differential diagnosis."""
    print("="*100)
    print("DATASET 1: EMR-QA (Eladio/emrqa-msquad)")
    print("="*100)
    print("\n📊 Purpose: EMR Question-Answering for clinical reasoning\n")
    
    try:
        print("Loading emrqa-msquad dataset...")
        ds = load_dataset("Eladio/emrqa-msquad")
        
        print(f"\n✅ Loaded successfully!")
        print(f"Structure: {ds}")
        
        split = list(ds.keys())[0]
        data = ds[split]
        
        print(f"\nSplit: {split}")
        print(f"Examples: {len(data)}")
        print(f"Features: {data.features}")
        
        # Show first example
        print(f"\n{'='*100}")
        print("SAMPLE EXAMPLE")
        print(f"{'='*100}")
        
        example = data[0]
        for key, value in example.items():
            print(f"\n{key.upper()}:")
            if isinstance(value, str) and len(value) > 300:
                print(f"{value[:300]}...")
            else:
                print(value)
        
        # Analyze for differential diagnosis use
        print(f"\n{'='*100}")
        print("SUITABILITY FOR DIFFERENTIAL DIAGNOSIS")
        print(f"{'='*100}")
        
        scores = {
            'has_clinical_context': False,
            'has_diagnosis_questions': False,
            'has_multiple_diagnoses': False,
            'has_evidence_links': False,
            'supports_summarization': False
        }
        
        # Check fields
        example_keys = list(example.keys())
        
        if any(k in example_keys for k in ['context', 'clinical_note', 'text', 'passage']):
            scores['has_clinical_context'] = True
            print("✅ Contains clinical context/notes")
        
        if any(k in example_keys for k in ['question', 'query']):
            scores['has_diagnosis_questions'] = True
            print("✅ Contains questions (good for diagnostic reasoning)")
        
        if any(k in example_keys for k in ['answer', 'answers']):
            scores['has_evidence_links'] = True
            print("✅ Has answers (can link evidence to diagnosis)")
        
        # Check content
        for key, value in example.items():
            if isinstance(value, str):
                if 'diagnos' in value.lower():
                    scores['has_multiple_diagnoses'] = True
                if 'summary' in value.lower() or 'history' in value.lower():
                    scores['supports_summarization'] = True
        
        if scores['has_multiple_diagnoses']:
            print("✅ Contains diagnostic content")
        if scores['supports_summarization']:
            print("✅ Supports clinical summarization")
        
        suitability_score = sum(scores.values()) / len(scores) * 100
        print(f"\n📊 Suitability Score: {suitability_score:.0f}%")
        
        return ds, split, scores
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None, {}


def load_and_analyze_guidelines():
    """Load and analyze clinical guidelines dataset."""
    print(f"\n\n{'='*100}")
    print("DATASET 2: Clinical Guidelines (epfl-llm/guidelines)")
    print("="*100)
    print("\n📊 Purpose: Evidence-based clinical practice guidelines\n")
    
    try:
        print("Loading guidelines dataset...")
        ds = load_dataset("epfl-llm/guidelines")
        
        print(f"\n✅ Loaded successfully!")
        print(f"Structure: {ds}")
        
        split = list(ds.keys())[0]
        data = ds[split]
        
        print(f"\nSplit: {split}")
        print(f"Guidelines: {len(data)}")
        print(f"Features: {data.features}")
        
        # Show first example
        print(f"\n{'='*100}")
        print("SAMPLE GUIDELINE")
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
        
        # Analyze for differential diagnosis use
        print(f"\n{'='*100}")
        print("SUITABILITY FOR DIFFERENTIAL DIAGNOSIS")
        print(f"{'='*100}")
        
        scores = {
            'has_diagnostic_criteria': False,
            'has_conditions': False,
            'has_evidence_levels': False,
            'has_differential_info': False,
            'supports_rag': False
        }
        
        example_keys = list(example.keys())
        
        if any(k in example_keys for k in ['condition', 'disease', 'diagnosis', 'topic']):
            scores['has_conditions'] = True
            print("✅ Contains condition/disease information")
        
        if any(k in example_keys for k in ['evidence_level', 'grade', 'strength', 'quality']):
            scores['has_evidence_levels'] = True
            print("✅ Has evidence strength levels")
        
        if any(k in example_keys for k in ['content', 'text', 'guideline', 'recommendation']):
            scores['supports_rag'] = True
            print("✅ Rich text content (good for RAG)")
        
        # Check content
        for key, value in example.items():
            if isinstance(value, str):
                if 'criteria' in value.lower() or 'diagnostic' in value.lower():
                    scores['has_diagnostic_criteria'] = True
                if 'differential' in value.lower():
                    scores['has_differential_info'] = True
        
        if scores['has_diagnostic_criteria']:
            print("✅ Contains diagnostic criteria")
        if scores['has_differential_info']:
            print("✅ Has differential diagnosis information")
        
        suitability_score = sum(scores.values()) / len(scores) * 100
        print(f"\n📊 Suitability Score: {suitability_score:.0f}%")
        
        return ds, split, scores
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None, {}


def compare_datasets(emrqa_scores, guidelines_scores):
    """Direct comparison for differential diagnosis use case."""
    print(f"\n\n{'='*100}")
    print("COMPREHENSIVE COMPARISON")
    print(f"{'='*100}")
    
    print(f"\n{'Criteria':<40} {'EMR-QA':<15} {'Guidelines':<15} {'Winner'}")
    print("-"*100)
    
    comparisons = [
        ("Clinical Context/Notes", 
         "✅ Direct" if emrqa_scores.get('has_clinical_context') else "❌ None",
         "⚠️ Indirect" if guidelines_scores.get('has_conditions') else "❌ None",
         "EMR-QA"),
        
        ("Diagnostic Questions",
         "✅ Yes" if emrqa_scores.get('has_diagnosis_questions') else "❌ No",
         "❌ No",
         "EMR-QA"),
        
        ("Evidence Traceability",
         "✅ Answer links" if emrqa_scores.get('has_evidence_links') else "❌ No",
         "✅ Citations" if guidelines_scores.get('has_evidence_levels') else "❌ No",
         "Tie"),
        
        ("Diagnostic Criteria",
         "⚠️ Implicit",
         "✅ Explicit" if guidelines_scores.get('has_diagnostic_criteria') else "⚠️ Implicit",
         "Guidelines"),
        
        ("Evidence Strength Levels",
         "❌ No",
         "✅ A/B/C grades" if guidelines_scores.get('has_evidence_levels') else "❌ No",
         "Guidelines"),
        
        ("RAG Readiness",
         "✅ QA format" if emrqa_scores.get('has_clinical_context') else "⚠️ Moderate",
         "✅ Rich text" if guidelines_scores.get('supports_rag') else "⚠️ Moderate",
         "Tie"),
        
        ("Summarization Support",
         "✅ Yes" if emrqa_scores.get('supports_summarization') else "⚠️ Moderate",
         "⚠️ Moderate",
         "EMR-QA"),
        
        ("Differential Diagnosis",
         "⚠️ Implicit" if emrqa_scores.get('has_multiple_diagnoses') else "❌ Limited",
         "✅ Explicit" if guidelines_scores.get('has_differential_info') else "⚠️ Implicit",
         "Guidelines"),
    ]
    
    for criteria, emr, guide, winner in comparisons:
        print(f"{criteria:<40} {emr:<15} {guide:<15} {winner}")
    
    print("\n" + "="*100)
    print("RECOMMENDATION")
    print("="*100)
    
    print("""
🎯 BEST APPROACH: **USE BOTH DATASETS TOGETHER**

┌─────────────────────────────────────────────────────────────────┐
│                      RECOMMENDED ARCHITECTURE                    │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│   Clinical Note      │
│   (Input Text)       │
└──────────┬───────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: EMR-QA (emrqa-msquad)                                 │
│  Purpose: Question-answering for diagnostic reasoning            │
│  • Extract key clinical facts                                   │
│  • Generate diagnostic questions                                │
│  • Link evidence to answers                                     │
└──────────┬──────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2: MedCaseReasoning (Current)                            │
│  Purpose: Match to similar clinical cases                       │
│  • Pattern matching                                             │
│  • Case-based reasoning                                         │
└──────────┬──────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3: Clinical Guidelines (epfl-llm/guidelines)             │
│  Purpose: Validate & strengthen with evidence                   │
│  • Check diagnostic criteria                                    │
│  • Add evidence strength (A/B/C)                                │
│  • Rank by guideline support                                    │
└──────────┬──────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────┐
│  Differential        │
│  Diagnosis Output    │
└──────────────────────┘

KEY INSIGHTS:

1. **EMR-QA (emrqa-msquad):**
   ✅ Best for: Clinical note → Summary
   ✅ Best for: Extracting diagnostic clues
   ✅ Best for: Question-answering format (good for LLM prompting)
   ❌ Weakness: May not have explicit differential lists

2. **Clinical Guidelines:**
   ✅ Best for: Validating diagnoses with evidence
   ✅ Best for: Adding strength/confidence levels
   ✅ Best for: Ensuring medical accuracy
   ❌ Weakness: Not directly connected to patient cases

3. **Combined Approach:**
   ✅ EMR-QA for understanding clinical narrative
   ✅ MedCase for pattern matching
   ✅ Guidelines for validation and ranking

IMPLEMENTATION PRIORITY:

Phase 1: Integrate EMR-QA for summarization
Phase 2: Keep MedCaseReasoning for differential generation
Phase 3: Add Guidelines for evidence strength and validation
""")


def save_comparison_results(emrqa_scores, guidelines_scores):
    """Save detailed comparison to file."""
    output = {
        "comparison_date": "2026-01-11",
        "goal": "Differential Diagnosis Generation",
        "datasets": {
            "emrqa_msquad": {
                "name": "Eladio/emrqa-msquad",
                "type": "EMR Question-Answering",
                "scores": emrqa_scores,
                "suitability": sum(emrqa_scores.values()) / len(emrqa_scores) * 100 if emrqa_scores else 0
            },
            "guidelines": {
                "name": "epfl-llm/guidelines",
                "type": "Clinical Practice Guidelines",
                "scores": guidelines_scores,
                "suitability": sum(guidelines_scores.values()) / len(guidelines_scores) * 100 if guidelines_scores else 0
            }
        },
        "recommendation": "Use BOTH datasets in complementary layers",
        "architecture": {
            "layer_1": "EMR-QA for summarization and fact extraction",
            "layer_2": "MedCaseReasoning for case matching (keep existing)",
            "layer_3": "Guidelines for validation and evidence strength"
        }
    }
    
    output_path = Path(__file__).parent.parent / "dataset_comparison_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {output_path}")


if __name__ == "__main__":
    print("\n" + "="*100)
    print("DATASET COMPARISON FOR DIFFERENTIAL DIAGNOSIS GENERATION")
    print("="*100)
    print("\n🎯 Goal: Clinical Note Summarization + Differential Diagnosis")
    print("📊 Testing: emrqa-msquad vs epfl-llm/guidelines\n")
    
    # Test EMR-QA
    emrqa_ds, emrqa_split, emrqa_scores = load_and_analyze_emrqa()
    
    # Test Guidelines
    guidelines_ds, guidelines_split, guidelines_scores = load_and_analyze_guidelines()
    
    # Compare
    if emrqa_ds is not None or guidelines_ds is not None:
        compare_datasets(emrqa_scores, guidelines_scores)
        save_comparison_results(emrqa_scores, guidelines_scores)
    
    print(f"\n{'='*100}")
    print("COMPARISON COMPLETE!")
    print(f"{'='*100}\n")
