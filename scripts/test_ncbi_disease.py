"""
Test script for ncbi/ncbi_disease dataset.
Explores disease entity recognition and potential integration with differential diagnosis pipeline.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datasets import load_dataset
import json
from typing import Dict, List

def test_dataset_access():
    """Test if ncbi_disease dataset is accessible."""
    print("="*100)
    print("TESTING DATASET ACCESS: ncbi/ncbi_disease")
    print("="*100)
    
    try:
        print("\n🔄 Attempting to load ncbi/ncbi_disease dataset...")
        print("(This may take a moment on first load...)\n")
        
        dataset = load_dataset(
            "ncbi/ncbi_disease",
            trust_remote_code=True
        )
        
        print("✅ SUCCESS! Dataset loaded successfully!")
        return dataset, True
        
    except Exception as e:
        print(f"❌ FAILED to load dataset")
        print(f"\nError: {e}")
        print("\nPossible reasons:")
        print("1. Dataset may require authentication")
        print("2. Dataset may have been moved/renamed")
        print("3. Network connectivity issues")
        print("4. Hugging Face API issues")
        print("5. Remote code execution may be blocked")
        
        return None, False


def explore_dataset(dataset):
    """Explore NCBI disease dataset structure."""
    if dataset is None:
        return
    
    print(f"\n{'='*100}")
    print("DATASET STRUCTURE ANALYSIS")
    print(f"{'='*100}")
    
    print(f"\n📊 Dataset Structure:")
    print(dataset)
    
    # Get splits
    splits = list(dataset.keys())
    print(f"\n📁 Available Splits: {splits}")
    
    for split in splits:
        data = dataset[split]
        print(f"\n{split.upper()} Split:")
        print(f"  • Number of examples: {len(data)}")
        print(f"  • Features: {data.features}")
    
    # Analyze first split
    split_name = splits[0]
    data = dataset[split_name]
    
    print(f"\n{'='*100}")
    print(f"SAMPLE EXAMPLES FROM '{split_name.upper()}' SPLIT")
    print(f"{'='*100}")
    
    # Show first 3 examples
    for i in range(min(3, len(data))):
        print(f"\n{'─'*100}")
        print(f"EXAMPLE #{i+1}")
        print(f"{'─'*100}")
        
        example = data[i]
        
        for key, value in example.items():
            print(f"\n{key.upper()}:")
            
            if isinstance(value, str):
                if len(value) > 500:
                    print(f"{value[:500]}...")
                else:
                    print(value)
            elif isinstance(value, list):
                print(f"[List with {len(value)} items]")
                if len(value) > 0 and len(value) <= 5:
                    for item in value:
                        print(f"  • {item}")
                elif len(value) > 5:
                    print(f"  First 3 items:")
                    for item in value[:3]:
                        print(f"  • {item}")
            elif isinstance(value, dict):
                print(f"[Dictionary with {len(value)} keys]")
                for k, v in list(value.items())[:3]:
                    print(f"  {k}: {v}")
            else:
                print(value)
    
    return split_name, data


def analyze_for_differential_diagnosis(dataset, split_name):
    """Analyze suitability for differential diagnosis use case."""
    if dataset is None:
        return {}
    
    print(f"\n{'='*100}")
    print("SUITABILITY FOR DIFFERENTIAL DIAGNOSIS")
    print(f"{'='*100}")
    
    data = dataset[split_name]
    example = data[0]
    
    scores = {
        'has_disease_entities': False,
        'has_clinical_text': False,
        'has_disease_mentions': False,
        'has_annotations': False,
        'supports_ner': False,
        'has_disease_ids': False,
        'supports_normalization': False
    }
    
    example_keys = list(example.keys())
    print(f"\n📋 Available Fields: {example_keys}\n")
    
    # Check for disease entities
    if any(k in example_keys for k in ['diseases', 'entities', 'mentions', 'disease_name']):
        scores['has_disease_entities'] = True
        print("✅ Contains disease entities/mentions")
    
    # Check for clinical text
    if any(k in example_keys for k in ['text', 'abstract', 'content', 'passage']):
        scores['has_clinical_text'] = True
        print("✅ Contains clinical/biomedical text")
    
    # Check for annotations
    if any(k in example_keys for k in ['annotations', 'labels', 'tags']):
        scores['has_annotations'] = True
        print("✅ Has annotations (good for NER)")
        scores['supports_ner'] = True
    
    # Check for disease IDs
    if any(k in example_keys for k in ['disease_id', 'mesh_id', 'cui', 'concept_id']):
        scores['has_disease_ids'] = True
        print("✅ Has disease IDs (supports normalization)")
        scores['supports_normalization'] = True
    
    # Analyze content
    for key, value in example.items():
        if isinstance(value, str):
            if 'disease' in value.lower() or 'diagnosis' in value.lower():
                scores['has_disease_mentions'] = True
    
    if scores['has_disease_mentions']:
        print("✅ Contains disease/diagnosis mentions in text")
    
    # Calculate suitability score
    suitability = sum(scores.values()) / len(scores) * 100
    
    print(f"\n{'─'*100}")
    print(f"📊 Overall Suitability Score: {suitability:.0f}%")
    print(f"{'─'*100}")
    
    return scores


def analyze_use_cases(scores):
    """Suggest specific use cases based on dataset structure."""
    print(f"\n{'='*100}")
    print("POTENTIAL USE CASES")
    print(f"{'='*100}")
    
    use_cases = []
    
    if scores.get('supports_ner'):
        use_cases.append({
            'name': 'Disease Entity Recognition',
            'description': 'Extract disease mentions from clinical notes',
            'priority': 'HIGH',
            'integration': 'Add to NER pipeline for symptom extraction'
        })
    
    if scores.get('supports_normalization'):
        use_cases.append({
            'name': 'Disease Name Normalization',
            'description': 'Map disease mentions to standard IDs (MeSH, UMLS)',
            'priority': 'HIGH',
            'integration': 'Improve disease_id_mapping.json'
        })
    
    if scores.get('has_disease_entities'):
        use_cases.append({
            'name': 'Disease Vocabulary Expansion',
            'description': 'Expand known disease terms and synonyms',
            'priority': 'MEDIUM',
            'integration': 'Enhance rule-based scorer with more disease terms'
        })
    
    if scores.get('has_clinical_text'):
        use_cases.append({
            'name': 'Training Data for NER Models',
            'description': 'Fine-tune disease recognition models',
            'priority': 'MEDIUM',
            'integration': 'Train custom NER model for better extraction'
        })
    
    if not use_cases:
        use_cases.append({
            'name': 'Limited Direct Use',
            'description': 'Dataset may not directly support differential diagnosis',
            'priority': 'LOW',
            'integration': 'Consider alternative datasets'
        })
    
    for i, uc in enumerate(use_cases, 1):
        print(f"\n{i}. {uc['name']} [{uc['priority']} PRIORITY]")
        print(f"   Description: {uc['description']}")
        print(f"   Integration: {uc['integration']}")
    
    return use_cases


def compare_with_other_datasets(ncbi_scores):
    """Compare NCBI disease with previously tested datasets."""
    print(f"\n{'='*100}")
    print("COMPARISON WITH OTHER DATASETS")
    print(f"{'='*100}")
    
    print(f"\n{'Dataset':<30} {'Best For':<40} {'Priority'}")
    print("─"*100)
    
    comparisons = [
        ("ncbi/ncbi_disease", 
         "Disease entity recognition & normalization",
         "MEDIUM" if ncbi_scores.get('supports_ner') else "LOW"),
        
        ("Eladio/emrqa-msquad",
         "Clinical note summarization",
         "HIGH"),
        
        ("epfl-llm/guidelines",
         "Evidence validation & diagnostic criteria",
         "HIGH"),
        
        ("MedCaseReasoning",
         "Differential diagnosis generation",
         "HIGH (current)"),
    ]
    
    for dataset, purpose, priority in comparisons:
        print(f"{dataset:<30} {purpose:<40} {priority}")
    
    print(f"\n{'='*100}")
    print("INTEGRATION RECOMMENDATION")
    print(f"{'='*100}")
    
    if ncbi_scores.get('supports_ner') or ncbi_scores.get('supports_normalization'):
        print("""
✅ RECOMMENDED: Integrate as SUPPORTING LAYER

Use ncbi_disease for:
1. **Disease Entity Recognition** - Extract disease mentions from text
2. **Disease Normalization** - Map mentions to standard IDs
3. **Vocabulary Enhancement** - Expand disease term coverage

Integration Point:
├─ Add to preprocessing layer
├─ Improve symptom/disease extraction
└─ Enhance disease_id_mapping.json

Priority: MEDIUM (after EMR-QA and Guidelines)
""")
    else:
        print("""
⚠️ LIMITED DIRECT USE

This dataset appears to be more focused on:
- Named Entity Recognition (NER)
- Disease mention extraction
- Biomedical text annotation

For differential diagnosis, prioritize:
1. EMR-QA (summarization)
2. MedCaseReasoning (current - differential generation)
3. Guidelines (validation)

Consider ncbi_disease for:
- Improving disease name recognition
- Standardizing disease terminology
- Enhancing NER capabilities
""")


def save_analysis_results(dataset_accessible, scores, use_cases):
    """Save analysis results to JSON."""
    output = {
        "dataset": "ncbi/ncbi_disease",
        "test_date": "2026-01-11",
        "accessible": dataset_accessible,
        "analysis": {
            "scores": scores,
            "suitability_percentage": sum(scores.values()) / len(scores) * 100 if scores else 0,
            "use_cases": use_cases
        },
        "recommendation": {
            "priority": "MEDIUM" if scores.get('supports_ner') else "LOW",
            "best_for": "Disease entity recognition and normalization",
            "integration_layer": "Preprocessing / NER enhancement"
        }
    }
    
    output_path = Path(__file__).parent.parent / "ncbi_disease_analysis.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Analysis results saved to: {output_path}")


if __name__ == "__main__":
    print("\n🧪 NCBI DISEASE DATASET TEST")
    print(f"{'='*100}\n")
    
    # Step 1: Test access
    dataset, accessible = test_dataset_access()
    
    if accessible and dataset is not None:
        # Step 2: Explore structure
        split_name, data = explore_dataset(dataset)
        
        # Step 3: Analyze for differential diagnosis
        scores = analyze_for_differential_diagnosis(dataset, split_name)
        
        # Step 4: Suggest use cases
        use_cases = analyze_use_cases(scores)
        
        # Step 5: Compare with other datasets
        compare_with_other_datasets(scores)
        
        # Step 6: Save results
        save_analysis_results(accessible, scores, use_cases)
        
    else:
        print("\n⚠️ Cannot proceed with analysis - dataset not accessible")
        print("\nAlternative datasets to consider:")
        print("  • Eladio/emrqa-msquad (for summarization)")
        print("  • epfl-llm/guidelines (for validation)")
        print("  • HPAI-BSC/chain-of-diagnosis (for reasoning)")
        
        save_analysis_results(accessible, {}, [])
    
    print(f"\n{'='*100}")
    print("TEST COMPLETE!")
    print(f"{'='*100}\n")
