"""
Test script for epfl-llm/guidelines dataset integration.
Explores clinical guidelines structure and potential integration with pipeline.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datasets import load_dataset
import json
from typing import Dict, List

def explore_dataset():
    """Load and explore clinical guidelines dataset structure."""
    print("="*100)
    print("LOADING EPFL-LLM CLINICAL GUIDELINES DATASET")
    print("="*100)
    
    try:
        ds = load_dataset("epfl-llm/guidelines")
        
        print(f"\n✅ Dataset loaded successfully!")
        print(f"Dataset structure: {ds}")
        
        # Get first split
        split_name = list(ds.keys())[0]
        data = ds[split_name]
        
        print(f"\nSplit: {split_name}")
        print(f"Number of guidelines: {len(data)}")
        print(f"Features: {data.features}")
        
        # Show first example
        print("\n" + "="*100)
        print("FIRST GUIDELINE EXAMPLE")
        print("="*100)
        example = data[0]
        
        for key, value in example.items():
            print(f"\n{key.upper()}:")
            if isinstance(value, str) and len(value) > 500:
                print(f"{value[:500]}...")
            elif isinstance(value, list) and len(value) > 0:
                print(f"List with {len(value)} items")
                print(f"First item: {value[0]}")
            else:
                print(value)
        
        return ds, split_name
        
    except Exception as e:
        print(f"\n❌ Error loading dataset: {e}")
        print("\nMake sure you've run: pip install datasets")
        return None, None


def analyze_guidelines_structure(ds, split_name):
    """Analyze guideline content and structure."""
    if ds is None:
        return
    
    print(f"\n{'='*100}")
    print("ANALYZING GUIDELINES STRUCTURE")
    print(f"{'='*100}")
    
    try:
        data = ds[split_name]
        
        # Analyze first few guidelines
        print("\n📊 Analyzing first 10 guidelines...")
        
        conditions = []
        guideline_types = []
        
        for i in range(min(10, len(data))):
            example = data[i]
            
            # Extract condition/disease if available
            for field in ['condition', 'disease', 'topic', 'title', 'category']:
                if field in example:
                    conditions.append(example[field])
                    break
            
            # Check for guideline type
            for field in ['type', 'guideline_type', 'category']:
                if field in example:
                    guideline_types.append(example[field])
                    break
        
        if conditions:
            print(f"\n✅ Sample Conditions/Topics:")
            for cond in set(conditions[:5]):
                print(f"   • {cond}")
        
        if guideline_types:
            print(f"\n✅ Guideline Types:")
            for gt in set(guideline_types):
                print(f"   • {gt}")
        
        # Check for structured content
        example = data[0]
        print(f"\n📋 Content Structure:")
        
        content_fields = ['text', 'content', 'guideline', 'recommendation', 
                         'description', 'summary', 'details']
        
        for field in content_fields:
            if field in example:
                content = example[field]
                if isinstance(content, str):
                    print(f"   ✅ {field}: {len(content)} characters")
                elif isinstance(content, list):
                    print(f"   ✅ {field}: {len(content)} items")
        
        # Check for evidence levels
        evidence_fields = ['evidence_level', 'strength', 'grade', 'quality']
        for field in evidence_fields:
            if field in example:
                print(f"   ✅ {field}: {example[field]}")
        
    except Exception as e:
        print(f"\n❌ Error analyzing structure: {e}")
        import traceback
        traceback.print_exc()


def search_guidelines(ds, split_name, query="diabetes"):
    """Search guidelines for specific conditions."""
    if ds is None:
        return
    
    print(f"\n{'='*100}")
    print(f"SEARCHING GUIDELINES FOR: '{query}'")
    print(f"{'='*100}")
    
    try:
        data = ds[split_name]
        matches = []
        
        query_lower = query.lower()
        
        for i in range(len(data)):
            example = data[i]
            
            # Search in all text fields
            found = False
            for key, value in example.items():
                if isinstance(value, str) and query_lower in value.lower():
                    found = True
                    break
            
            if found:
                matches.append((i, example))
                
            if len(matches) >= 5:  # Limit to 5 matches
                break
        
        print(f"\n✅ Found {len(matches)} matching guidelines:\n")
        
        for idx, (i, example) in enumerate(matches, 1):
            print(f"{idx}. Guideline #{i}")
            
            # Show title/condition
            for field in ['title', 'condition', 'topic', 'disease']:
                if field in example:
                    print(f"   {field.title()}: {example[field]}")
                    break
            
            # Show content preview
            for field in ['text', 'content', 'guideline', 'recommendation']:
                if field in example:
                    content = str(example[field])
                    print(f"   Preview: {content[:200]}...")
                    break
            
            print()
        
        return matches
        
    except Exception as e:
        print(f"\n❌ Error searching guidelines: {e}")
        return []


def extract_guidelines_for_condition(ds, split_name, condition="hypertension"):
    """Extract all guidelines related to a specific condition."""
    if ds is None:
        return []
    
    print(f"\n{'='*100}")
    print(f"EXTRACTING GUIDELINES FOR: {condition.upper()}")
    print(f"{'='*100}")
    
    try:
        data = ds[split_name]
        relevant_guidelines = []
        
        condition_lower = condition.lower()
        
        for example in data:
            # Check if condition is mentioned
            mentioned = False
            
            for key, value in example.items():
                if isinstance(value, str) and condition_lower in value.lower():
                    mentioned = True
                    break
            
            if mentioned:
                relevant_guidelines.append(example)
        
        print(f"\n✅ Found {len(relevant_guidelines)} guidelines for {condition}")
        
        if relevant_guidelines:
            print(f"\n📄 Sample Guideline:")
            sample = relevant_guidelines[0]
            
            for key in ['title', 'recommendation', 'text', 'content']:
                if key in sample:
                    print(f"\n{key.upper()}:")
                    content = str(sample[key])
                    print(content[:400] + "..." if len(content) > 400 else content)
                    break
        
        return relevant_guidelines
        
    except Exception as e:
        print(f"\n❌ Error extracting guidelines: {e}")
        return []


def save_guidelines_sample(ds, split_name, output_file="guidelines_sample.json"):
    """Save sample guidelines to JSON."""
    if ds is None:
        return
    
    print(f"\n{'='*100}")
    print(f"SAVING GUIDELINES SAMPLE")
    print(f"{'='*100}")
    
    try:
        data = ds[split_name]
        sample = []
        
        for i in range(min(10, len(data))):
            example = dict(data[i])
            sample.append(example)
        
        output_path = Path(__file__).parent.parent / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sample, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Saved {len(sample)} guidelines to: {output_path}")
        
    except Exception as e:
        print(f"\n❌ Error saving sample: {e}")


def analyze_guideline_coverage(ds, split_name):
    """Analyze what conditions/diseases are covered."""
    if ds is None:
        return
    
    print(f"\n{'='*100}")
    print("ANALYZING GUIDELINE COVERAGE")
    print(f"{'='*100}")
    
    try:
        data = ds[split_name]
        
        # Common conditions to check
        conditions = [
            "diabetes", "hypertension", "heart failure", "asthma",
            "copd", "pneumonia", "sepsis", "stroke", "myocardial infarction",
            "chest pain", "abdominal pain", "headache", "GERD"
        ]
        
        coverage = {}
        
        print("\n🔍 Checking coverage for common conditions...\n")
        
        for condition in conditions:
            count = 0
            for example in data:
                for key, value in example.items():
                    if isinstance(value, str) and condition.lower() in value.lower():
                        count += 1
                        break
            
            coverage[condition] = count
            if count > 0:
                print(f"✅ {condition.title()}: {count} guidelines")
            else:
                print(f"❌ {condition.title()}: No guidelines found")
        
        print(f"\n📊 Total Coverage: {sum(1 for c in coverage.values() if c > 0)}/{len(conditions)} conditions")
        
        return coverage
        
    except Exception as e:
        print(f"\n❌ Error analyzing coverage: {e}")
        return {}


def suggest_integration_approach(ds, split_name):
    """Suggest how to integrate guidelines into clinical pipeline."""
    if ds is None:
        return
    
    print(f"\n{'='*100}")
    print("INTEGRATION RECOMMENDATIONS")
    print(f"{'='*100}")
    
    print("""
💡 SUGGESTED INTEGRATION APPROACHES:

1. **Knowledge Base Enhancement**
   - Extract condition-specific guidelines
   - Add to rule-based scoring engine
   - Use for evidence validation

2. **Diagnostic Workflow Integration**
   - Match patient symptoms to guideline criteria
   - Suggest diagnostic tests based on guidelines
   - Provide management recommendations

3. **Evidence Strength Calibration**
   - Use guideline evidence levels (A/B/C)
   - Weight diagnoses by guideline support
   - Show guideline-based confidence

4. **Safety Flag Generation**
   - Extract red flag symptoms from guidelines
   - Trigger alerts for high-risk presentations
   - Guide immediate action recommendations

5. **Treatment Suggestion Engine**
   - Parse management recommendations
   - Suggest initial workup based on guidelines
   - Provide evidence-based next steps

NEXT STEPS:
1. Identify relevant guidelines for your 6 rule-based conditions
2. Extract diagnostic criteria and red flags
3. Integrate into rule-based scoring engine
4. Add guideline citations to evidence provenance
""")


if __name__ == "__main__":
    print("\n🧪 CLINICAL GUIDELINES DATASET TEST")
    print(f"{'='*100}\n")
    
    # Step 1: Load and explore
    ds, split_name = explore_dataset()
    
    if ds is not None:
        # Step 2: Analyze structure
        analyze_guidelines_structure(ds, split_name)
        
        # Step 3: Analyze coverage
        coverage = analyze_guideline_coverage(ds, split_name)
        
        # Step 4: Save sample
        save_guidelines_sample(ds, split_name)
        
        # Step 5: Interactive search
        print("\n" + "="*100)
        search_choice = input("\n🔍 Search guidelines for specific condition? (y/n): ").strip().lower()
        if search_choice == 'y':
            query = input("Enter condition/topic to search: ").strip()
            if query:
                search_guidelines(ds, split_name, query)
                
                extract_choice = input(f"\n📄 Extract all guidelines for '{query}'? (y/n): ").strip().lower()
                if extract_choice == 'y':
                    guidelines = extract_guidelines_for_condition(ds, split_name, query)
        
        # Step 6: Integration recommendations
        suggest_integration_approach(ds, split_name)
    
    print(f"\n{'='*100}")
    print("TEST COMPLETE!")
    print(f"{'='*100}\n")
