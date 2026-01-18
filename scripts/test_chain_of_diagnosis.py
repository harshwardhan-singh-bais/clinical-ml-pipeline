"""
Test script for HPAI-BSC/chain-of-diagnosis dataset integration.
Explores dataset structure and tests clinical pipeline with real cases.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datasets import load_dataset
import json
from services.clinical_pipeline import ClinicalPipeline
from models.schemas import ClinicalNoteRequest, InputType

def explore_dataset():
    """Load and explore chain-of-diagnosis dataset structure."""
    print("="*100)
    print("LOADING CHAIN-OF-DIAGNOSIS DATASET")
    print("="*100)
    
    try:
        # Login required: huggingface-cli login
        ds = load_dataset("HPAI-BSC/chain-of-diagnosis")
        
        print(f"\n✅ Dataset loaded successfully!")
        print(f"Dataset structure: {ds}")
        
        # Get first split
        split_name = list(ds.keys())[0]
        data = ds[split_name]
        
        print(f"\nSplit: {split_name}")
        print(f"Number of examples: {len(data)}")
        print(f"Features: {data.features}")
        
        # Show first example
        print("\n" + "="*100)
        print("FIRST EXAMPLE")
        print("="*100)
        example = data[0]
        
        for key, value in example.items():
            print(f"\n{key.upper()}:")
            if isinstance(value, str) and len(value) > 500:
                print(f"{value[:500]}...")
            else:
                print(value)
        
        return ds, split_name
        
    except Exception as e:
        print(f"\n❌ Error loading dataset: {e}")
        print("\nMake sure you've:")
        print("1. Run: huggingface-cli login")
        print("2. Have access to HPAI-BSC/chain-of-diagnosis")
        return None, None


def test_with_pipeline(ds, split_name, num_cases=3):
    """Test clinical pipeline with dataset cases."""
    if ds is None:
        print("\n⚠️ Dataset not loaded. Skipping pipeline test.")
        return
    
    print("\n" + "="*100)
    print(f"TESTING CLINICAL PIPELINE WITH {num_cases} CASES")
    print("="*100)
    
    try:
        # Initialize pipeline
        print("\nInitializing clinical pipeline...")
        pipeline = ClinicalPipeline()
        
        data = ds[split_name]
        
        for i in range(min(num_cases, len(data))):
            print(f"\n{'='*100}")
            print(f"CASE #{i+1}")
            print(f"{'='*100}")
            
            example = data[i]
            
            # Extract clinical note (adjust field names as needed)
            # Common field names: 'text', 'clinical_note', 'case', 'history'
            clinical_text = None
            for field in ['text', 'clinical_note', 'case', 'history', 'patient_note', 'note']:
                if field in example:
                    clinical_text = example[field]
                    break
            
            if not clinical_text:
                print(f"⚠️ No clinical text found in example {i+1}")
                print(f"Available fields: {list(example.keys())}")
                continue
            
            print(f"\nInput text ({len(clinical_text)} chars):")
            print(clinical_text[:300] + "..." if len(clinical_text) > 300 else clinical_text)
            
            # Show ground truth if available
            if 'diagnosis' in example:
                print(f"\n✅ Ground Truth Diagnosis: {example['diagnosis']}")
            elif 'label' in example:
                print(f"\n✅ Ground Truth Label: {example['label']}")
            
            # Process with pipeline
            print("\n🔄 Processing with clinical pipeline...")
            
            request = ClinicalNoteRequest(
                input_type=InputType.TEXT,
                content=clinical_text
            )
            
            response = pipeline.process_clinical_note(request)
            
            print(f"\n{'='*80}")
            print("PIPELINE OUTPUT")
            print(f"{'='*80}")
            
            # Show summary
            if response.summary:
                print(f"\n📋 Summary: {response.summary.summary_text[:200]}...")
            
            # Show top 3 diagnoses
            if response.differential_diagnoses:
                print(f"\n🎯 Top Diagnoses:")
                for j, dx in enumerate(response.differential_diagnoses[:3], 1):
                    print(f"\n{j}. {dx.diagnosis}")
                    
                    # Show plausibility if available
                    conf = dx.confidence.overall_confidence
                    if conf >= 0.7:
                        plaus = "LIKELY"
                    elif conf >= 0.5:
                        plaus = "POSSIBLE"
                    else:
                        plaus = "UNLIKELY"
                    
                    print(f"   Clinical Plausibility: {plaus}")
                    print(f"   Reasoning: {dx.reasoning[:150]}...")
            
            print("\n" + "-"*80)
        
        print(f"\n✅ Tested {num_cases} cases successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during pipeline testing: {e}")
        import traceback
        traceback.print_exc()


def save_dataset_sample(ds, split_name, output_file="chain_of_diagnosis_sample.json"):
    """Save sample cases to JSON for analysis."""
    if ds is None:
        return
    
    print(f"\n{'='*100}")
    print(f"SAVING DATASET SAMPLE")
    print(f"{'='*100}")
    
    try:
        data = ds[split_name]
        sample = []
        
        for i in range(min(5, len(data))):
            example = dict(data[i])
            sample.append(example)
        
        output_path = Path(__file__).parent.parent / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sample, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Saved {len(sample)} examples to: {output_path}")
        
    except Exception as e:
        print(f"\n❌ Error saving sample: {e}")


def analyze_diagnosis_chain(ds, split_name):
    """Analyze the chain-of-diagnosis reasoning structure."""
    if ds is None:
        return
    
    print(f"\n{'='*100}")
    print("ANALYZING DIAGNOSIS CHAIN STRUCTURE")
    print(f"{'='*100}")
    
    try:
        data = ds[split_name]
        example = data[0 ]
        
        print("\nLooking for chain-of-thought/reasoning fields...")
        
        # Common reasoning field names
        reasoning_fields = ['reasoning', 'chain', 'thought_process', 'explanation', 
                          'rationale', 'steps', 'analysis']
        
        for field in reasoning_fields:
            if field in example:
                print(f"\n✅ Found reasoning field: '{field}'")
                print(f"Content preview: {str(example[field])[:300]}...")
        
        # Check for multi-step reasoning
        if 'chain' in str(example).lower():
            print("\n💡 Dataset contains chain-of-thought reasoning!")
        
    except Exception as e:
        print(f"\n❌ Error analyzing structure: {e}")


if __name__ == "__main__":
    print("\n🧪 CHAIN-OF-DIAGNOSIS DATASET TEST")
    print(f"{'='*100}\n")
    
    # Step 1: Load and explore
    ds, split_name = explore_dataset()
    
    if ds is not None:
        # Step 2: Analyze structure
        analyze_diagnosis_chain(ds, split_name)
        
        # Step 3: Save sample
        save_dataset_sample(ds, split_name)
        
        # Step 4: Test with pipeline
        test_choice = input("\n\n🔬 Test with clinical pipeline? (y/n): ").strip().lower()
        if test_choice == 'y':
            num_cases = int(input("Number of cases to test (1-10): ").strip() or "3")
            test_with_pipeline(ds, split_name, num_cases)
        else:
            print("\n⏭️  Skipping pipeline test.")
    
    print(f"\n{'='*100}")
    print("TEST COMPLETE!")
    print(f"{'='*100}\n")
