"""
Disease-Symptom CSV Dataset Validation Script
Tests whether the disease-symptom CSV is suitable for differential diagnosis.

Tests:
1. Dataset loading and structure
2. Clinical coverage (multiple body systems)
3. Symptom-dataset alignment
4. Differential diagnosis simulation
5. Integration suitability assessment
"""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DiseaseSymptomCSVValidator:
    """Validate disease-symptom CSV dataset for differential diagnosis."""
    
    def __init__(self, csv_path: str = "Disease and symptoms dataset.csv"):
        """
        Initialize validator.
        
        Args:
            csv_path: Path to CSV file (default: root directory)
        """
        self.csv_path = Path(csv_path)
        self.diseases = []
        self.symptoms = []
        self.disease_symptom_matrix = {}
        self.errors = []
        self.warnings = []
    
    def test_1_load_dataset(self):
        """Test 1: Load and validate CSV structure."""
        print("\n" + "="*80)
        print("TEST 1: Dataset Loading & Structure")
        print("="*80)
        
        if not self.csv_path.exists():
            print(f"❌ FILE NOT FOUND: {self.csv_path.absolute()}")
            self.errors.append(f"Missing file: {self.csv_path}")
            return False
        
        print(f"✅ Found: {self.csv_path}")
        print(f"   Size: {self.csv_path.stat().st_size:,} bytes")
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                
                # Read header (symptoms)
                header = next(reader)
                self.symptoms = header[1:]  # Skip first column (disease name)
                
                print(f"\n✅ Loaded {len(self.symptoms)} symptoms")
                print(f"   Sample symptoms: {self.symptoms[:5]}")
                
                # Read diseases
                for row in reader:
                    if row:
                        disease_name = row[0]
                        symptom_values = [int(v) if v.isdigit() else 0 for v in row[1:]]
                        
                        self.diseases.append(disease_name)
                        self.disease_symptom_matrix[disease_name] = symptom_values
                
                print(f"✅ Loaded {len(self.diseases)} diseases")
                print(f"   Sample diseases: {self.diseases[:5]}")
                
            return True
            
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            self.errors.append(f"CSV load error: {e}")
            return False
    
    def test_2_clinical_coverage(self):
        """Test 2: Validate clinical coverage across body systems."""
        print("\n" + "="*80)
        print("TEST 2: Clinical Coverage (Body Systems)")
        print("="*80)
        
        if not self.diseases:
            print("❌ No diseases loaded")
            return False
        
        # Define body system keywords
        body_systems = {
            "Cardiac": ["heart", "cardiac", "coronary", "arrhythmia", "angina", "myocardial"],
            "Respiratory": ["lung", "respiratory", "pneumonia", "asthma", "bronchitis", "copd"],
            "Psychiatric": ["anxiety", "depression", "psychiatric", "panic", "bipolar", "schizophrenia"],
            "Gastrointestinal": ["gastro", "stomach", "intestin", "gerd", "ulcer", "colitis", "crohn"],
            "ENT": ["ear", "nose", "throat", "sinus", "tonsil", "pharyngitis"],
            "Neurological": ["neuro", "migraine", "seizure", "stroke", "parkinson", "alzheimer"],
            "Musculoskeletal": ["arthritis", "osteo", "muscle", "joint", "fracture"],
            "Endocrine": ["diabetes", "thyroid", "hormone", "adrenal"],
        }
        
        # Categorize diseases
        categorized = defaultdict(list)
        uncategorized = []
        
        for disease in self.diseases:
            disease_lower = disease.lower()
            found = False
            
            for system, keywords in body_systems.items():
                if any(keyword in disease_lower for keyword in keywords):
                    categorized[system].append(disease)
                    found = True
                    break
            
            if not found:
                uncategorized.append(disease)
        
        # Report coverage
        print("\nBody System Coverage:")
        print("-" * 80)
        
        for system, diseases in sorted(categorized.items()):
            print(f"\n{system}: {len(diseases)} diseases")
            for disease in diseases[:3]:
                print(f"  - {disease}")
        
        if uncategorized:
            print(f"\nUncategorized: {len(uncategorized)} diseases")
            print(f"  Sample: {uncategorized[:3]}")
        
        # Assessment
        systems_covered = len(categorized)
        print("\n" + "-" * 80)
        print(f"Total Systems Covered: {systems_covered}/8")
        
        if systems_covered >= 5:
            print("✅ GOOD: Multiple body systems represented")
            return True
        else:
            print("⚠️  POOR: Limited clinical coverage")
            self.warnings.append("Limited body system coverage")
            return False
    
    def test_3_disease_symptom_analysis(self):
        """Test 3: Analyze 10 distinct diseases with their symptoms."""
        print("\n" + "="*80)
        print("TEST 3: Disease-Symptom Analysis (10 Distinct Diseases)")
        print("="*80)
        
        if not self.disease_symptom_matrix:
            print("❌ No disease-symptom data loaded")
            return False
        
        # Select 10 diverse diseases
        selected_diseases = self.diseases[:10]
        
        print("\n10 Distinct Diseases with Symptoms:")
        print("="*80)
        
        for i, disease in enumerate(selected_diseases, 1):
            symptom_values = self.disease_symptom_matrix[disease]
            
            # Get symptoms where value = 1
            present_symptoms = [
                self.symptoms[j] for j, val in enumerate(symptom_values) if val == 1
            ]
            
            print(f"\n{i}. {disease}")
            print(f"   Total Symptoms: {len(present_symptoms)}")
            print(f"   Top 5 Symptoms:")
            for symptom in present_symptoms[:5]:
                print(f"     - {symptom}")
        
        return True
    
    def test_4_symptom_alignment(self):
        """Test 4: Test symptom-dataset alignment with clinical text."""
        print("\n" + "="*80)
        print("TEST 4: Symptom-Dataset Alignment")
        print("="*80)
        
        # Test clinical text
        clinical_text = """
        Patient reports episodic chest tightness, racing heart, dizziness, 
        shortness of breath, and difficulty sleeping.
        """
        
        print(f"\nClinical Text:\n{clinical_text}")
        
        # Extract canonical symptom terms
        extracted_symptoms = [
            "chest tightness",
            "racing heart",
            "dizziness",
            "shortness of breath",
            "difficulty sleeping"
        ]
        
        print(f"\nExtracted Symptoms: {extracted_symptoms}")
        
        # Match to dataset columns
        print("\nMatching to Dataset:")
        print("-" * 80)
        
        matched = []
        failed = []
        
        for symptom in extracted_symptoms:
            # Try exact match
            if symptom in self.symptoms:
                matched.append(symptom)
                print(f"✅ '{symptom}' → EXACT MATCH")
            else:
                # Try fuzzy match
                fuzzy_matches = self._find_fuzzy_matches(symptom)
                
                if fuzzy_matches:
                    matched.append(symptom)
                    print(f"✅ '{symptom}' → FUZZY MATCH: {fuzzy_matches[0]}")
                else:
                    failed.append(symptom)
                    print(f"❌ '{symptom}' → NO MATCH")
        
        # Calculate match rate
        match_rate = (len(matched) / len(extracted_symptoms)) * 100
        
        print("\n" + "-" * 80)
        print(f"Match Rate: {match_rate:.1f}% ({len(matched)}/{len(extracted_symptoms)})")
        
        if match_rate >= 70:
            print("✅ GOOD: Dataset aligns well with clinical text")
            return True
        else:
            print("❌ POOR: Dataset does not align with clinical text")
            self.errors.append(f"Low match rate: {match_rate:.1f}%")
            return False
    
    def _find_fuzzy_matches(self, symptom: str) -> List[str]:
        """Find fuzzy matches for a symptom."""
        symptom_lower = symptom.lower()
        matches = []
        
        for dataset_symptom in self.symptoms:
            dataset_lower = dataset_symptom.lower()
            
            # Check if words overlap
            symptom_words = set(symptom_lower.split())
            dataset_words = set(dataset_lower.split())
            
            overlap = symptom_words & dataset_words
            
            if len(overlap) >= 1:
                matches.append(dataset_symptom)
        
        return matches
    
    def test_5_differential_diagnosis_simulation(self):
        """Test 5: Simulate differential diagnosis generation."""
        print("\n" + "="*80)
        print("TEST 5: Differential Diagnosis Simulation")
        print("="*80)
        
        # Test case: Patient with chest pain symptoms
        test_symptoms = ["chest pain", "shortness of breath", "sweating", "nausea"]
        
        print(f"\nTest Case Symptoms: {test_symptoms}")
        
        # Find matching symptoms in dataset
        matched_symptom_indices = []
        
        for symptom in test_symptoms:
            for i, dataset_symptom in enumerate(self.symptoms):
                if symptom.lower() in dataset_symptom.lower():
                    matched_symptom_indices.append(i)
                    print(f"  '{symptom}' → {dataset_symptom}")
                    break
        
        if not matched_symptom_indices:
            print("❌ No symptoms matched - cannot generate diagnosis")
            return False
        
        # Score diseases
        disease_scores = []
        
        for disease, symptom_values in self.disease_symptom_matrix.items():
            # Count matching symptoms
            matches = sum(1 for i in matched_symptom_indices if i < len(symptom_values) and symptom_values[i] == 1)
            
            if matches > 0:
                # Calculate score
                total_disease_symptoms = sum(symptom_values)
                score = (matches / len(matched_symptom_indices)) * 100
                
                disease_scores.append({
                    'disease': disease,
                    'matches': matches,
                    'total': total_disease_symptoms,
                    'score': score
                })
        
        # Sort by score
        disease_scores.sort(key=lambda x: (x['matches'], x['score']), reverse=True)
        
        # Display top 5
        print("\nTop 5 Differential Diagnoses:")
        print("-" * 80)
        print(f"{'Rank':<6} {'Disease':<40} {'Matched':<10} {'Score'}")
        print("-" * 80)
        
        for i, result in enumerate(disease_scores[:5], 1):
            print(f"{i:<6} {result['disease']:<40} {result['matches']}/{len(matched_symptom_indices):<10} {result['score']:.1f}%")
        
        return len(disease_scores) > 0
    
    def test_6_integration_assessment(self):
        """Test 6: Assess suitability for integration."""
        print("\n" + "="*80)
        print("TEST 6: Integration Suitability Assessment")
        print("="*80)
        
        assessment = {
            "dataset_size": len(self.diseases),
            "symptom_count": len(self.symptoms),
            "errors": len(self.errors),
            "warnings": len(self.warnings)
        }
        
        print("\nDataset Metrics:")
        print(f"  Diseases: {assessment['dataset_size']}")
        print(f"  Symptoms: {assessment['symptom_count']}")
        print(f"  Errors: {assessment['errors']}")
        print(f"  Warnings: {assessment['warnings']}")
        
        print("\nSuitability Analysis:")
        print("-" * 80)
        
        # Size check
        if assessment['dataset_size'] >= 50:
            print("✅ Dataset Size: GOOD (50+ diseases)")
        else:
            print("⚠️  Dataset Size: SMALL (<50 diseases)")
        
        # Symptom coverage
        if assessment['symptom_count'] >= 100:
            print("✅ Symptom Coverage: GOOD (100+ symptoms)")
        else:
            print("⚠️  Symptom Coverage: LIMITED (<100 symptoms)")
        
        # Error check
        if assessment['errors'] == 0:
            print("✅ Data Quality: NO ERRORS")
        else:
            print(f"❌ Data Quality: {assessment['errors']} ERRORS")
        
        print("\n" + "="*80)
        print("RECOMMENDATION:")
        print("="*80)
        
        if assessment['errors'] == 0 and assessment['dataset_size'] >= 50:
            print("✅ SUITABLE for differential diagnosis generation")
            print("\nIntegration Approach:")
            print("  1. Load CSV into memory")
            print("  2. Build disease → symptom lookup")
            print("  3. Match patient symptoms to columns")
            print("  4. Score diseases by symptom overlap")
            print("  5. Return top 5 ranked diagnoses")
        else:
            print("⚠️  LIMITED suitability - use as supplement only")
            print("\nIssues:")
            for error in self.errors:
                print(f"  - {error}")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        return assessment['errors'] == 0
    
    def run_all_tests(self):
        """Run all validation tests."""
        print("\n" + "="*100)
        print(" "*25 + "DISEASE-SYMPTOM CSV VALIDATION SUITE")
        print("="*100)
        
        tests = [
            ("Dataset Loading", self.test_1_load_dataset),
            ("Clinical Coverage", self.test_2_clinical_coverage),
            ("Disease-Symptom Analysis", self.test_3_disease_symptom_analysis),
            ("Symptom Alignment", self.test_4_symptom_alignment),
            ("Differential Diagnosis Simulation", self.test_5_differential_diagnosis_simulation),
            ("Integration Assessment", self.test_6_integration_assessment),
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
                self.errors.append(f"{test_name}: {e}")
        
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
        
        return passed == total


if __name__ == "__main__":
    # Run validator
    validator = DiseaseSymptomCSVValidator(csv_path="Disease and symptoms dataset.csv")
    success = validator.run_all_tests()
    
    exit(0 if success else 1)
