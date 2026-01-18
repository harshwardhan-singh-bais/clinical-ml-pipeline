"""
CSV Dataset Validation Script
Tests the quality and validity of the Disease-Symptom CSV dataset.

Tests:
1. Pattern diversity per disease
2. Clinical plausibility (expected diagnoses)
3. Symptom dropout robustness
"""

import sys
import logging
import random
from pathlib import Path
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.disease_symptom_csv_service import DiseaseSymptomCSVService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CSVDatasetValidator:
    """Validate CSV dataset quality."""
    
    def __init__(self):
        """Initialize validator."""
        logger.info("="*80)
        logger.info("CSV DATASET VALIDATOR")
        logger.info("="*80)
        
        try:
            self.csv_service = DiseaseSymptomCSVService()
            logger.info(f"✅ Loaded {len(self.csv_service.all_diseases)} diseases")
            logger.info(f"✅ Loaded {len(self.csv_service.symptoms)} symptoms")
            logger.info(f"✅ Loaded {sum(len(p) for p in self.csv_service.disease_patterns.values())} total patterns")
        except Exception as e:
            logger.error(f"❌ Failed to load CSV: {e}")
            raise
    
    def test_1_pattern_diversity(self):
        """Test 1: Pattern diversity per disease."""
        print("\n" + "="*80)
        print("TEST 1: PATTERN DIVERSITY PER DISEASE")
        print("="*80)
        print("\nIf this fails → dataset is trash")
        
        # Count patterns per disease
        pattern_counts = {}
        for disease, patterns in self.csv_service.disease_patterns.items():
            pattern_counts[disease] = len(patterns)
        
        # Sort by pattern count
        sorted_diseases = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Show top 10 (most patterns)
        print("\n📊 Top 10 Diseases (Most Pattern Diversity):")
        print("-" * 80)
        print(f"{'Disease':<50} {'Patterns'}")
        print("-" * 80)
        for disease, count in sorted_diseases[:10]:
            print(f"{disease[:48]:<50} {count:>8}")
        
        # Show bottom 10 (least patterns)
        print("\n📊 Bottom 10 Diseases (Least Pattern Diversity):")
        print("-" * 80)
        print(f"{'Disease':<50} {'Patterns'}")
        print("-" * 80)
        for disease, count in sorted_diseases[-10:]:
            print(f"{disease[:48]:<50} {count:>8}")
        
        # Statistics
        total_patterns = sum(pattern_counts.values())
        avg_patterns = total_patterns / len(pattern_counts)
        max_patterns = max(pattern_counts.values())
        min_patterns = min(pattern_counts.values())
        
        print("\n📈 Statistics:")
        print(f"  Total patterns: {total_patterns:,}")
        print(f"  Average per disease: {avg_patterns:.1f}")
        print(f"  Max patterns: {max_patterns:,}")
        print(f"  Min patterns: {min_patterns:,}")
        
        # Validation
        if avg_patterns < 10:
            print("\n❌ FAIL: Average patterns too low (<10)")
            print("   Dataset lacks diversity")
            return False
        elif avg_patterns < 100:
            print("\n⚠️  WARNING: Low pattern diversity (<100 avg)")
            print("   Dataset is usable but limited")
            return True
        else:
            print("\n✅ PASS: Good pattern diversity")
            return True
    
    def test_2_clinical_plausibility(self):
        """Test 2: Clinical plausibility check."""
        print("\n" + "="*80)
        print("TEST 2: CLINICAL PLAUSIBILITY")
        print("="*80)
        print("\nIf this fails → dataset is not clinically valid")
        
        # Test case: Cardiac symptoms
        test_case = {
            "name": "Cardiac Symptoms",
            "symptoms": ["chest pain", "palpitations", "sweating", "anxiety"],
            "expected_in_top_10": [
                "panic disorder",
                "myocardial infarction",
                "angina",
                "arrhythmia",
                "gerd",
                "heart attack",
                "anxiety disorder",
                "coronary"
            ]
        }
        
        print(f"\n🧪 Test Case: {test_case['name']}")
        print(f"   Symptoms: {', '.join(test_case['symptoms'])}")
        
        # Generate diagnoses
        normalized_data = {"symptoms": test_case['symptoms']}
        diagnoses = self.csv_service.generate_diagnoses(
            clinical_note=" ".join(test_case['symptoms']),
            normalized_data=normalized_data,
            top_k=10
        )
        
        if not diagnoses:
            print("\n❌ FAIL: No diagnoses generated")
            return False
        
        # Show top 10
        print("\n📋 Top 10 Diagnoses:")
        print("-" * 80)
        print(f"{'Rank':<6} {'Disease':<50} {'Score'}")
        print("-" * 80)
        for dx in diagnoses:
            rank = dx.get('priority', 0)
            disease = dx.get('diagnosis', 'Unknown')[:48]
            score = dx.get('match_score', 0) * 100
            print(f"{rank:<6} {disease:<50} {score:>5.1f}%")
        
        # Check if expected diagnoses are present
        top_10_diseases = [dx.get('diagnosis', '').lower() for dx in diagnoses]
        
        found_expected = []
        for expected in test_case['expected_in_top_10']:
            if any(expected in disease for disease in top_10_diseases):
                found_expected.append(expected)
        
        print("\n🎯 Expected Diagnoses Check:")
        print(f"   Expected to find: {', '.join(test_case['expected_in_top_10'][:5])}...")
        print(f"   Found: {', '.join(found_expected) if found_expected else 'None'}")
        print(f"   Match rate: {len(found_expected)}/{len(test_case['expected_in_top_10'])}")
        
        # Validation
        if len(found_expected) == 0:
            print("\n❌ FAIL: No expected diagnoses found")
            print("   Dataset is not clinically valid")
            return False
        elif len(found_expected) < 3:
            print("\n⚠️  WARNING: Few expected diagnoses found")
            print("   Dataset has limited clinical coverage")
            return True
        else:
            print("\n✅ PASS: Expected diagnoses present")
            return True
    
    def test_3_symptom_dropout_robustness(self):
        """Test 3: Symptom dropout robustness."""
        print("\n" + "="*80)
        print("TEST 3: SYMPTOM DROPOUT ROBUSTNESS")
        print("="*80)
        print("\nIf this fails → dataset is fragile")
        
        # Test case
        full_symptoms = [
            "chest pain", "palpitations", "sweating", "anxiety",
            "shortness of breath", "dizziness", "nausea"
        ]
        
        print(f"\n🧪 Full Symptoms ({len(full_symptoms)}):")
        print(f"   {', '.join(full_symptoms)}")
        
        # Generate with full symptoms
        normalized_data = {"symptoms": full_symptoms}
        full_diagnoses = self.csv_service.generate_diagnoses(
            clinical_note=" ".join(full_symptoms),
            normalized_data=normalized_data,
            top_k=5
        )
        
        if not full_diagnoses:
            print("\n❌ FAIL: No diagnoses with full symptoms")
            return False
        
        full_top_5 = [dx.get('diagnosis', '') for dx in full_diagnoses]
        
        print(f"\n📋 Top 5 with Full Symptoms:")
        for i, disease in enumerate(full_top_5, 1):
            print(f"   {i}. {disease}")
        
        # Remove 30-40% symptoms randomly
        dropout_rate = 0.35  # 35%
        num_to_remove = int(len(full_symptoms) * dropout_rate)
        
        dropped_symptoms = full_symptoms.copy()
        random.seed(42)  # Reproducible
        for _ in range(num_to_remove):
            if dropped_symptoms:
                dropped_symptoms.pop(random.randint(0, len(dropped_symptoms) - 1))
        
        print(f"\n🔻 Dropped {num_to_remove} symptoms ({dropout_rate*100:.0f}%):")
        print(f"   Remaining: {', '.join(dropped_symptoms)}")
        
        # Generate with dropped symptoms
        normalized_data_dropped = {"symptoms": dropped_symptoms}
        dropped_diagnoses = self.csv_service.generate_diagnoses(
            clinical_note=" ".join(dropped_symptoms),
            normalized_data=normalized_data_dropped,
            top_k=5
        )
        
        if not dropped_diagnoses:
            print("\n❌ FAIL: No diagnoses with dropped symptoms")
            return False
        
        dropped_top_5 = [dx.get('diagnosis', '') for dx in dropped_diagnoses]
        
        print(f"\n📋 Top 5 with Dropped Symptoms:")
        for i, disease in enumerate(dropped_top_5, 1):
            print(f"   {i}. {disease}")
        
        # Check overlap
        overlap = set(full_top_5) & set(dropped_top_5)
        overlap_rate = len(overlap) / len(full_top_5) * 100
        
        print(f"\n🔄 Overlap Analysis:")
        print(f"   Overlap: {len(overlap)}/{len(full_top_5)} diagnoses")
        print(f"   Overlap rate: {overlap_rate:.1f}%")
        if overlap:
            print(f"   Common: {', '.join(overlap)}")
        
        # Validation
        if overlap_rate < 40:
            print("\n❌ FAIL: Low overlap (<40%)")
            print("   Dataset is too fragile to symptom dropout")
            return False
        elif overlap_rate < 60:
            print("\n⚠️  WARNING: Moderate overlap (40-60%)")
            print("   Dataset is somewhat robust")
            return True
        else:
            print("\n✅ PASS: High overlap (>60%)")
            print("   Dataset is robust to symptom dropout")
            return True
    
    def run_all_tests(self):
        """Run all validation tests."""
        print("\n" + "="*80)
        print("RUNNING ALL VALIDATION TESTS")
        print("="*80)
        
        tests = [
            ("Pattern Diversity", self.test_1_pattern_diversity),
            ("Clinical Plausibility", self.test_2_clinical_plausibility),
            ("Symptom Dropout Robustness", self.test_3_symptom_dropout_robustness),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                logger.error(f"❌ Error in {test_name}: {e}")
                import traceback
                traceback.print_exc()
                results.append((test_name, False))
        
        # Summary
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<40} {status}")
        
        passed = sum(1 for _, r in results if r)
        total = len(results)
        
        print("="*80)
        print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        print("="*80)
        
        # Final verdict
        if passed == total:
            print("\n✅ DATASET IS VALID")
            print("   All tests passed. Dataset is clinically sound.")
        elif passed >= total * 0.66:
            print("\n⚠️  DATASET IS USABLE")
            print("   Most tests passed. Dataset has some limitations.")
        else:
            print("\n❌ DATASET IS TRASH")
            print("   Too many failures. Dataset is not reliable.")
        
        return passed == total


if __name__ == "__main__":
    try:
        validator = CSVDatasetValidator()
        success = validator.run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Exiting...")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
