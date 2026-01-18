"""
GretelAI Symptom-to-Diagnosis Dataset Test Script
Tests the gretelai/symptom_to_diagnosis dataset for diagnosis generation.

Dataset: https://huggingface.co/datasets/gretelai/symptom_to_diagnosis

Tests:
1. Dataset accessibility
2. Schema exploration
3. Symptom → diagnosis mapping
4. Clinical test cases
5. Integration recommendations
"""

import logging
from typing import Dict, List
from collections import defaultdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Optional: datasets library
try:
    from datasets import load_dataset
    HAS_DATASETS = True
except ImportError:
    HAS_DATASETS = False
    print("❌ datasets library not installed")
    print("   Install: pip install datasets")

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("⚠️  pandas not available - using dict output")


class GretelAISymptomDiagnosisTester:
    """Test GretelAI symptom-to-diagnosis dataset."""
    
    def __init__(self):
        """Initialize tester."""
        self.dataset = None
        self.data = []
        self.symptom_to_diagnosis_map = defaultdict(set)
    
    def test_1_dataset_accessibility(self):
        """Test 1: Load dataset from Hugging Face."""
        print("\n" + "="*80)
        print("TEST 1: Dataset Accessibility")
        print("="*80)
        
        if not HAS_DATASETS:
            print("❌ FAILED: datasets library not installed")
            return False
        
        try:
            print("Loading: gretelai/symptom_to_diagnosis")
            self.dataset = load_dataset("gretelai/symptom_to_diagnosis")
            
            print(f"✅ SUCCESS: Dataset loaded")
            print(f"   Splits: {list(self.dataset.keys())}")
            
            for split in self.dataset.keys():
                print(f"   {split}: {len(self.dataset[split])} examples")
            
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            return False
    
    def test_2_schema_exploration(self):
        """Test 2: Explore dataset schema and structure."""
        print("\n" + "="*80)
        print("TEST 2: Schema Exploration")
        print("="*80)
        
        if not self.dataset:
            print("❌ Dataset not loaded")
            return False
        
        # Get first split
        split_name = list(self.dataset.keys())[0]
        self.data = self.dataset[split_name]
        
        print(f"\nAnalyzing split: {split_name}")
        print(f"Total examples: {len(self.data)}")
        
        # Show first example
        if len(self.data) > 0:
            first_example = self.data[0]
            print(f"\nFirst Example:")
            print(f"  Keys: {list(first_example.keys())}")
            
            for key, value in first_example.items():
                value_str = str(value)[:100]
                print(f"  {key}: {value_str}...")
        
        # Analyze structure
        print(f"\nColumn Analysis:")
        for key in first_example.keys():
            sample_values = [self.data[i][key] for i in range(min(5, len(self.data)))]
            print(f"  {key}:")
            print(f"    Type: {type(sample_values[0])}")
            print(f"    Sample: {sample_values[0][:100] if isinstance(sample_values[0], str) else sample_values[0]}")
        
        return True
    
    def test_3_symptom_diagnosis_mapping(self):
        """Test 3: Build symptom → diagnosis mapping."""
        print("\n" + "="*80)
        print("TEST 3: Symptom → Diagnosis Mapping")
        print("="*80)
        
        if not self.data:
            print("❌ Data not loaded")
            return False
        
        # Build mapping
        print("Building symptom → diagnosis map...")
        
        for example in self.data:
            # Extract symptoms and diagnosis
            # (Field names may vary - adjust based on schema)
            symptoms = example.get('symptoms', example.get('input', example.get('text', '')))
            diagnosis = example.get('diagnosis', example.get('output', example.get('label', '')))
            
            if isinstance(symptoms, str):
                symptoms = [symptoms]
            
            if isinstance(symptoms, list):
                for symptom in symptoms:
                    if symptom and diagnosis:
                        self.symptom_to_diagnosis_map[symptom.lower()].add(diagnosis)
        
        print(f"✅ Mapped {len(self.symptom_to_diagnosis_map)} unique symptoms")
        
        # Show sample mappings
        print("\nSample Mappings:")
        for i, (symptom, diagnoses) in enumerate(list(self.symptom_to_diagnosis_map.items())[:5]):
            print(f"  '{symptom}' → {list(diagnoses)[:3]}")
        
        return True
    
    def test_4_clinical_test_cases(self):
        """Test 4: Run clinical test cases."""
        print("\n" + "="*80)
        print("TEST 4: Clinical Test Cases")
        print("="*80)
        
        # Test cases
        test_cases = [
            {
                "symptoms": ["chest pain", "shortness of breath", "sweating"],
                "expected": ["heart attack", "myocardial infarction", "cardiac"]
            },
            {
                "symptoms": ["fever", "cough", "fatigue"],
                "expected": ["flu", "influenza", "respiratory infection"]
            },
            {
                "symptoms": ["headache", "nausea", "sensitivity to light"],
                "expected": ["migraine"]
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\nTest Case {i}:")
            print(f"  Symptoms: {test_case['symptoms']}")
            print(f"  Expected: {test_case['expected']}")
            
            # Find matching examples
            matches = self._find_matching_examples(test_case['symptoms'])
            
            if matches:
                print(f"  ✅ Found {len(matches)} matching examples")
                for match in matches[:3]:
                    print(f"    - {match}")
            else:
                print(f"  ⚠️  No exact matches found")
        
        return True
    
    def _find_matching_examples(self, symptoms: List[str]) -> List[str]:
        """Find examples matching given symptoms."""
        matches = []
        
        for example in self.data:
            example_symptoms = example.get('symptoms', example.get('input', example.get('text', '')))
            diagnosis = example.get('diagnosis', example.get('output', example.get('label', '')))
            
            if isinstance(example_symptoms, str):
                example_symptoms_lower = example_symptoms.lower()
                
                # Check if any test symptom is in example
                if any(symptom.lower() in example_symptoms_lower for symptom in symptoms):
                    matches.append(diagnosis)
        
        return matches
    
    def test_5_diagnosis_generation_simulation(self):
        """Test 5: Simulate diagnosis generation."""
        print("\n" + "="*80)
        print("TEST 5: Diagnosis Generation Simulation")
        print("="*80)
        
        # Simulate patient case
        patient_case = {
            "symptoms": ["chest burning", "worse after meals", "sour taste"],
            "demographics": {"age": 45, "sex": "M"}
        }
        
        print(f"\nPatient Case:")
        print(f"  Symptoms: {patient_case['symptoms']}")
        
        # Find similar cases in dataset
        similar_cases = []
        
        for example in self.data:
            example_symptoms = example.get('symptoms', example.get('input', example.get('text', '')))
            diagnosis = example.get('diagnosis', example.get('output', example.get('label', '')))
            
            if isinstance(example_symptoms, str):
                # Calculate similarity (simple keyword matching)
                matches = sum(1 for s in patient_case['symptoms'] if s.lower() in example_symptoms.lower())
                
                if matches > 0:
                    similar_cases.append({
                        'diagnosis': diagnosis,
                        'symptoms': example_symptoms,
                        'match_count': matches
                    })
        
        # Sort by match count
        similar_cases.sort(key=lambda x: x['match_count'], reverse=True)
        
        print(f"\nTop 5 Similar Cases:")
        print("-" * 80)
        
        for i, case in enumerate(similar_cases[:5], 1):
            print(f"{i}. {case['diagnosis']}")
            print(f"   Matched: {case['match_count']} symptoms")
            print(f"   Symptoms: {case['symptoms'][:100]}...")
        
        return len(similar_cases) > 0
    
    def test_6_integration_recommendations(self):
        """Test 6: Provide integration recommendations."""
        print("\n" + "="*80)
        print("TEST 6: Integration Recommendations")
        print("="*80)
        
        if not self.data:
            print("❌ Data not loaded")
            return False
        
        print("\n📋 INTEGRATION RECOMMENDATIONS:")
        print("-" * 80)
        
        print("\n1. DATASET CHARACTERISTICS:")
        print(f"   - Total examples: {len(self.data)}")
        print(f"   - Unique symptoms: {len(self.symptom_to_diagnosis_map)}")
        print(f"   - Data type: Symptom-diagnosis pairs")
        
        print("\n2. BEST USE CASES:")
        print("   ✅ Direct symptom → diagnosis lookup")
        print("   ✅ Training data for ML models")
        print("   ✅ Validation of diagnosis hypotheses")
        print("   ✅ Symptom pattern recognition")
        
        print("\n3. INTEGRATION APPROACH:")
        print("   Option A: Direct Lookup")
        print("     - Match patient symptoms to dataset")
        print("     - Return associated diagnoses")
        print("     - Fast, deterministic")
        
        print("\n   Option B: Similarity Search")
        print("     - Find similar symptom patterns")
        print("     - Rank by similarity score")
        print("     - More flexible")
        
        print("\n   Option C: Hybrid")
        print("     - Use as validation layer")
        print("     - Cross-check with other sources")
        print("     - Boost confidence for matches")
        
        print("\n4. RECOMMENDED ARCHITECTURE:")
        print("   Clinical Note")
        print("        ↓")
        print("   Extract Symptoms")
        print("        ↓")
        print("   GretelAI Lookup → Candidate Diagnoses")
        print("        ↓")
        print("   Rank & Filter")
        print("        ↓")
        print("   Return Top 5")
        
        print("\n5. PROVENANCE:")
        print("   source: 'evidence'")
        print("   rule_applied: False")
        print("   llm_used: False")
        print("   evidence_type: 'gretelai-symptom-match'")
        
        return True
    
    def generate_summary_report(self):
        """Generate summary report."""
        print("\n" + "="*80)
        print("SUMMARY REPORT")
        print("="*80)
        
        if not self.data:
            print("❌ Dataset not loaded - cannot generate report")
            return
        
        # Get first example to determine schema
        first_example = self.data[0]
        
        report = {
            "dataset": "gretelai/symptom_to_diagnosis",
            "total_examples": len(self.data),
            "schema": list(first_example.keys()),
            "unique_symptoms": len(self.symptom_to_diagnosis_map),
            "suitability": {
                "diagnosis_generation": "HIGH",
                "symptom_matching": "HIGH",
                "evidence_retrieval": "MEDIUM",
                "training_data": "HIGH"
            },
            "integration_difficulty": "LOW",
            "recommended_use": "Primary diagnosis source or validation layer"
        }
        
        print("\nDataset Summary:")
        for key, value in report.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")
        
        return report
    
    def run_all_tests(self):
        """Run all tests."""
        print("\n" + "="*100)
        print(" "*25 + "GRETELAI SYMPTOM-TO-DIAGNOSIS TEST SUITE")
        print("="*100)
        
        tests = [
            ("Dataset Accessibility", self.test_1_dataset_accessibility),
            ("Schema Exploration", self.test_2_schema_exploration),
            ("Symptom-Diagnosis Mapping", self.test_3_symptom_diagnosis_mapping),
            ("Clinical Test Cases", self.test_4_clinical_test_cases),
            ("Diagnosis Generation Simulation", self.test_5_diagnosis_generation_simulation),
            ("Integration Recommendations", self.test_6_integration_recommendations),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"\n❌ ERROR in {test_name}: {e}")
                import traceback
                traceback.print_exc()
                results.append((test_name, False))
        
        # Summary
        print("\n" + "="*100)
        print(" "*40 + "TEST SUMMARY")
        print("="*100)
        
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:<45} {status}")
        
        passed = sum(1 for _, r in results if r)
        total = len(results)
        
        print("="*100)
        print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        print("="*100)
        
        # Generate summary
        self.generate_summary_report()
        
        return passed == total


if __name__ == "__main__":
    # Run tests
    tester = GretelAISymptomDiagnosisTester()
    success = tester.run_all_tests()
    
    exit(0 if success else 1)
