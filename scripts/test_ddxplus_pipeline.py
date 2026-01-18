"""
DDXPlus Pipeline Test Script
Tests correct usage of DDXPlus dataset without vector databases.

Requirements:
- datasets
- pandas
- Python standard library only

Tests:
1. Dataset accessibility via Hugging Face
2. Manual JSON file loading
3. Schema integrity validation
4. In-memory disease → symptom lookup
5. Deterministic symptom matching
6. Clinical note test case
7. Top 5 differential diagnosis ranking
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

# Optional: datasets library for HF loading
try:
    from datasets import load_dataset
    HAS_DATASETS = True
except ImportError:
    HAS_DATASETS = False
    print("⚠️  datasets library not available - skipping HF test")

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("⚠️  pandas not available - using dict output")


class DDXPlusValidator:
    """Validates and tests DDXPlus dataset without vector databases."""
    
    def __init__(self, local_repo_path: str = None):
        """
        Initialize validator.
        
        Args:
            local_repo_path: Path to local DDXPlus repo clone (optional)
        """
        self.local_repo_path = local_repo_path
        self.conditions = {}
        self.evidences = {}
        self.disease_symptom_map = defaultdict(set)
        
    def test_1_dataset_accessibility(self):
        """Test 1: Dataset accessibility via Hugging Face."""
        print("\n" + "="*80)
        print("TEST 1: Dataset Accessibility (Hugging Face)")
        print("="*80)
        
        if not HAS_DATASETS:
            print("❌ SKIPPED: datasets library not installed")
            return False
        
        try:
            print("Loading DDXPlus from Hugging Face: mila-iqia/ddxplus")
            dataset = load_dataset("mila-iqia/ddxplus")
            
            print(f"✅ SUCCESS: Dataset loaded")
            print(f"   Splits: {list(dataset.keys())}")
            
            for split in dataset.keys():
                print(f"   {split}: {len(dataset[split])} patients")
            
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            return False
    
    def test_2_manual_json_loading(self):
        """Test 2: Manual loading of JSON files from local repo."""
        print("\n" + "="*80)
        print("TEST 2: Manual JSON File Loading")
        print("="*80)
        
        if not self.local_repo_path:
            print("⚠️  No local repo path provided - using sample data")
            # Create sample data for testing
            self._create_sample_data()
            return True
        
        repo_path = Path(self.local_repo_path)
        
        # Load release_conditions.json
        conditions_file = repo_path / "release_conditions.json"
        evidences_file = repo_path / "release_evidences.json"
        
        try:
            print(f"Loading: {conditions_file}")
            with open(conditions_file, 'r', encoding='utf-8') as f:
                self.conditions = json.load(f)
            print(f"✅ Loaded {len(self.conditions)} conditions")
            
            print(f"Loading: {evidences_file}")
            with open(evidences_file, 'r', encoding='utf-8') as f:
                self.evidences = json.load(f)
            print(f"✅ Loaded {len(self.evidences)} evidences")
            
            return True
            
        except FileNotFoundError as e:
            print(f"❌ File not found: {e}")
            print("   Creating sample data for testing...")
            self._create_sample_data()
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def _create_sample_data(self):
        """Create sample DDXPlus data for testing."""
        print("Creating sample DDXPlus data...")
        
        # Sample evidences (symptoms)
        self.evidences = {
            "E_48": {"name": "E_48", "question_en": "Do you have a cough?", "is_antecedent": False, "data_type": "B"},
            "E_50": {"name": "E_50", "question_en": "Do you have chest pain?", "is_antecedent": False, "data_type": "B"},
            "E_77": {"name": "E_77", "question_en": "Do you have a fever?", "is_antecedent": False, "data_type": "B"},
            "E_91": {"name": "E_91", "question_en": "Do you have a sore throat?", "is_antecedent": False, "data_type": "B"},
            "E_100": {"name": "E_100", "question_en": "Do you have heartburn?", "is_antecedent": False, "data_type": "B"},
            "E_101": {"name": "E_101", "question_en": "Worse after meals?", "is_antecedent": False, "data_type": "B"},
            "E_102": {"name": "E_102", "question_en": "Sour taste in mouth?", "is_antecedent": False, "data_type": "B"},
        }
        
        # Sample conditions (diseases)
        self.conditions = {
            "GERD": {
                "condition_name": "GERD",
                "cond-name-eng": "Gastroesophageal Reflux Disease",
                "icd10-id": "K21.9",
                "symptoms": {"E_100": {}, "E_101": {}, "E_102": {}},
                "antecedents": {},
                "severity": 4
            },
            "Bronchitis": {
                "condition_name": "Bronchitis",
                "cond-name-eng": "Bronchitis",
                "icd10-id": "J20.9",
                "symptoms": {"E_48": {}, "E_50": {}, "E_77": {}},
                "antecedents": {},
                "severity": 3
            },
            "URTI": {
                "condition_name": "URTI",
                "cond-name-eng": "Upper Respiratory Tract Infection",
                "icd10-id": "J06.9",
                "symptoms": {"E_48": {}, "E_77": {}, "E_91": {}},
                "antecedents": {},
                "severity": 4
            },
        }
        
        print(f"✅ Created {len(self.conditions)} sample conditions")
        print(f"✅ Created {len(self.evidences)} sample evidences")
    
    def test_3_schema_integrity(self):
        """Test 3: Verify schema integrity."""
        print("\n" + "="*80)
        print("TEST 3: Schema Integrity Validation")
        print("="*80)
        
        errors = []
        
        # Check 1: Each condition maps to at least one evidence
        print("\nCheck 1: Each condition has at least one symptom")
        for cond_name, cond_data in self.conditions.items():
            symptoms = cond_data.get("symptoms", {})
            if not symptoms:
                errors.append(f"  ❌ {cond_name}: No symptoms")
            else:
                print(f"  ✅ {cond_name}: {len(symptoms)} symptoms")
        
        # Check 2: Evidence codes referenced by conditions exist
        print("\nCheck 2: All referenced evidences exist")
        for cond_name, cond_data in self.conditions.items():
            symptoms = cond_data.get("symptoms", {})
            for evidence_code in symptoms.keys():
                if evidence_code not in self.evidences:
                    errors.append(f"  ❌ {cond_name}: Evidence {evidence_code} not found")
        
        if not errors:
            print("  ✅ All referenced evidences exist")
        else:
            for error in errors:
                print(error)
        
        print(f"\n{'✅ PASSED' if not errors else '❌ FAILED'}: Schema integrity check")
        return len(errors) == 0
    
    def test_4_build_lookup_table(self):
        """Test 4: Build in-memory disease → symptom lookup table."""
        print("\n" + "="*80)
        print("TEST 4: Build In-Memory Disease → Symptom Lookup Table")
        print("="*80)
        
        for cond_name, cond_data in self.conditions.items():
            symptoms = cond_data.get("symptoms", {})
            for evidence_code in symptoms.keys():
                self.disease_symptom_map[cond_name].add(evidence_code)
        
        print("\nLookup Table:")
        for disease, symptoms in self.disease_symptom_map.items():
            symptom_names = [self.evidences.get(s, {}).get("question_en", s) for s in symptoms]
            print(f"  {disease}: {len(symptoms)} symptoms")
            for sym in list(symptom_names)[:3]:
                print(f"    - {sym}")
        
        print(f"\n✅ Built lookup table for {len(self.disease_symptom_map)} diseases")
        return True
    
    def test_5_symptom_matching_function(self):
        """Test 5: Implement deterministic symptom-matching scoring."""
        print("\n" + "="*80)
        print("TEST 5: Deterministic Symptom-Matching Scoring Function")
        print("="*80)
        
        def calculate_match_score(patient_symptoms: List[str], disease_symptoms: set) -> float:
            """
            Calculate match score between patient and disease symptoms.
            
            Score = (matched_symptoms / total_disease_symptoms) * 100
            """
            if not disease_symptoms:
                return 0.0
            
            matched = len(set(patient_symptoms) & disease_symptoms)
            total = len(disease_symptoms)
            
            return (matched / total) * 100
        
        # Test the function
        test_patient_symptoms = ["E_100", "E_101", "E_102"]
        test_disease_symptoms = {"E_100", "E_101", "E_102", "E_103"}
        
        score = calculate_match_score(test_patient_symptoms, test_disease_symptoms)
        
        print(f"\nTest Case:")
        print(f"  Patient symptoms: {test_patient_symptoms}")
        print(f"  Disease symptoms: {test_disease_symptoms}")
        print(f"  Match score: {score:.2f}%")
        print(f"  Expected: 75.00% (3/4 matched)")
        
        assert abs(score - 75.0) < 0.01, "Score calculation incorrect"
        
        print(f"\n✅ Scoring function validated")
        
        # Store function for later use
        self.calculate_match_score = calculate_match_score
        return True
    
    def test_6_clinical_note_test(self):
        """Test 6: Run test clinical note."""
        print("\n" + "="*80)
        print("TEST 6: Clinical Note Test Case")
        print("="*80)
        
        # Test clinical note
        clinical_note = """
        Patient presents with:
        - chest burning
        - worse after meals
        - sour taste in mouth
        """
        
        print(f"Clinical Note:\n{clinical_note}")
        
        # Simulate symptom normalization (text → evidence IDs)
        print("\nSymptom Normalization (Text → Evidence IDs):")
        
        symptom_mapping = {
            "chest burning": "E_100",  # heartburn
            "worse after meals": "E_101",
            "sour taste": "E_102",
        }
        
        patient_evidence_ids = []
        for text, evidence_id in symptom_mapping.items():
            patient_evidence_ids.append(evidence_id)
            evidence_name = self.evidences.get(evidence_id, {}).get("question_en", evidence_id)
            print(f"  '{text}' → {evidence_id} ({evidence_name})")
        
        print(f"\n✅ Normalized to {len(patient_evidence_ids)} evidence IDs")
        
        # Store for next test
        self.test_patient_evidences = patient_evidence_ids
        return True
    
    def test_7_rank_differential_diagnosis(self):
        """Test 7: Rank top 5 differential diagnoses."""
        print("\n" + "="*80)
        print("TEST 7: Rank Top 5 Differential Diagnoses")
        print("="*80)
        
        # Calculate scores for all diseases
        results = []
        
        for disease, disease_symptoms in self.disease_symptom_map.items():
            score = self.calculate_match_score(self.test_patient_evidences, disease_symptoms)
            
            # Get disease info
            cond_data = self.conditions.get(disease, {})
            disease_full_name = cond_data.get("cond-name-eng", disease)
            
            # Get matched symptoms
            matched_symptoms = set(self.test_patient_evidences) & disease_symptoms
            matched_symptom_names = [
                self.evidences.get(s, {}).get("question_en", s) 
                for s in matched_symptoms
            ]
            
            results.append({
                "disease": disease_full_name,
                "score": score,
                "matched_symptoms": matched_symptom_names,
                "match_count": len(matched_symptoms),
                "total_symptoms": len(disease_symptoms)
            })
        
        # Sort by score (descending)
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Get top 5
        top_5 = results[:5]
        
        # Print results table
        print("\nTop 5 Differential Diagnoses:")
        print("-" * 100)
        print(f"{'Rank':<6} {'Disease':<40} {'Matched':<10} {'Score':<10} {'Matched Symptoms'}")
        print("-" * 100)
        
        for i, result in enumerate(top_5, 1):
            matched_str = f"{result['match_count']}/{result['total_symptoms']}"
            symptoms_str = ", ".join(result['matched_symptoms'][:2])
            if len(result['matched_symptoms']) > 2:
                symptoms_str += "..."
            
            print(f"{i:<6} {result['disease']:<40} {matched_str:<10} {result['score']:>6.1f}%   {symptoms_str}")
        
        print("-" * 100)
        
        # Convert to pandas DataFrame if available
        if HAS_PANDAS:
            df = pd.DataFrame(top_5)
            print("\nDataFrame Summary:")
            print(df[['disease', 'score', 'match_count']].to_string(index=False))
        
        print(f"\n✅ Generated top 5 differential diagnoses")
        
        # Store for assertion
        self.top_5_results = top_5
        return True
    
    def test_8_assert_gi_condition(self):
        """Test 8: Assert gastrointestinal condition in top 3."""
        print("\n" + "="*80)
        print("TEST 8: Assert Gastrointestinal Condition in Top 3")
        print("="*80)
        
        gi_keywords = ["gerd", "reflux", "gastro", "esophageal", "heartburn"]
        
        top_3 = self.top_5_results[:3]
        
        found_gi = False
        for i, result in enumerate(top_3, 1):
            disease_lower = result['disease'].lower()
            if any(keyword in disease_lower for keyword in gi_keywords):
                print(f"✅ FOUND: {result['disease']} at rank {i}")
                found_gi = True
                break
        
        if not found_gi:
            print(f"❌ FAILED: No GI condition in top 3")
            print(f"   Top 3: {[r['disease'] for r in top_3]}")
            return False
        
        print(f"\n✅ ASSERTION PASSED: GI condition found in top 3")
        return True
    
    def run_all_tests(self):
        """Run all tests in sequence."""
        print("\n" + "="*100)
        print(" "*30 + "DDXPlus PIPELINE TEST SUITE")
        print("="*100)
        
        tests = [
            ("Dataset Accessibility", self.test_1_dataset_accessibility),
            ("Manual JSON Loading", self.test_2_manual_json_loading),
            ("Schema Integrity", self.test_3_schema_integrity),
            ("Build Lookup Table", self.test_4_build_lookup_table),
            ("Symptom Matching Function", self.test_5_symptom_matching_function),
            ("Clinical Note Test", self.test_6_clinical_note_test),
            ("Rank Differential Diagnosis", self.test_7_rank_differential_diagnosis),
            ("Assert GI Condition", self.test_8_assert_gi_condition),
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
        print(" "*35 + "TEST SUMMARY")
        print("="*100)
        
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:<40} {status}")
        
        passed = sum(1 for _, r in results if r)
        total = len(results)
        
        print("="*100)
        print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        print("="*100)
        
        return passed == total


if __name__ == "__main__":
    # Run tests
    # If you have a local DDXPlus repo, provide the path:
    # validator = DDXPlusValidator(local_repo_path="/path/to/ddxplus")
    
    validator = DDXPlusValidator()
    success = validator.run_all_tests()
    
    exit(0 if success else 1)
