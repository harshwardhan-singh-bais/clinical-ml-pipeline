"""
DDXPlus Debug & Test Script
Diagnoses issues with DDXPlus integration and provides detailed audit.

Tests:
1. File accessibility
2. JSON structure validation
3. Evidence mapping
4. Disease matching
5. Scoring logic
6. Full pipeline simulation
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DDXPlusDebugger:
    """Debug DDXPlus integration issues."""
    
    def __init__(self, data_dir: str = "."):
        """Initialize debugger."""
        self.data_dir = Path(data_dir)
        self.conditions = {}
        self.evidences = {}
        self.errors = []
        self.warnings = []
    
    def test_1_file_accessibility(self):
        """Test 1: Check if JSON files exist and are readable."""
        print("\n" + "="*80)
        print("TEST 1: File Accessibility")
        print("="*80)
        
        conditions_file = self.data_dir / "release_conditions.json"
        evidences_file = self.data_dir / "release_evidences.json"
        
        print(f"\nChecking directory: {self.data_dir.absolute()}")
        
        # Check conditions file
        if conditions_file.exists():
            print(f"✅ FOUND: {conditions_file}")
            print(f"   Size: {conditions_file.stat().st_size:,} bytes")
        else:
            print(f"❌ NOT FOUND: {conditions_file}")
            self.errors.append(f"Missing file: {conditions_file}")
        
        # Check evidences file
        if evidences_file.exists():
            print(f"✅ FOUND: {evidences_file}")
            print(f"   Size: {evidences_file.stat().st_size:,} bytes")
        else:
            print(f"❌ NOT FOUND: {evidences_file}")
            self.errors.append(f"Missing file: {evidences_file}")
        
        return len(self.errors) == 0
    
    def test_2_json_structure(self):
        """Test 2: Validate JSON structure."""
        print("\n" + "="*80)
        print("TEST 2: JSON Structure Validation")
        print("="*80)
        
        # Load conditions
        try:
            conditions_file = self.data_dir / "release_conditions.json"
            with open(conditions_file, 'r', encoding='utf-8') as f:
                self.conditions = json.load(f)
            
            print(f"\n✅ Loaded conditions: {len(self.conditions)} entries")
            
            # Show sample
            sample_key = list(self.conditions.keys())[0] if self.conditions else None
            if sample_key:
                print(f"\nSample condition: {sample_key}")
                sample = self.conditions[sample_key]
                print(f"  Keys: {list(sample.keys())}")
                print(f"  Name: {sample.get('condition_name', 'N/A')}")
                print(f"  Symptoms: {len(sample.get('symptoms', {}))} evidences")
            
        except Exception as e:
            print(f"❌ Error loading conditions: {e}")
            self.errors.append(f"Conditions load error: {e}")
        
        # Load evidences
        try:
            evidences_file = self.data_dir / "release_evidences.json"
            with open(evidences_file, 'r', encoding='utf-8') as f:
                self.evidences = json.load(f)
            
            print(f"\n✅ Loaded evidences: {len(self.evidences)} entries")
            
            # Show sample
            sample_key = list(self.evidences.keys())[0] if self.evidences else None
            if sample_key:
                print(f"\nSample evidence: {sample_key}")
                sample = self.evidences[sample_key]
                print(f"  Keys: {list(sample.keys())}")
                print(f"  Question: {sample.get('question_en', 'N/A')[:50]}...")
                print(f"  Type: {sample.get('data_type', 'N/A')}")
        
        except Exception as e:
            print(f"❌ Error loading evidences: {e}")
            self.errors.append(f"Evidences load error: {e}")
        
        return len(self.errors) == 0
    
    def test_3_evidence_mapping(self):
        """Test 3: Test symptom → evidence ID mapping."""
        print("\n" + "="*80)
        print("TEST 3: Evidence Mapping")
        print("="*80)
        
        # Test symptoms
        test_symptoms = [
            "chest burning",
            "heartburn",
            "worse after meals",
            "sour taste",
            "cough",
            "fever"
        ]
        
        print("\nTesting symptom normalization:")
        print("-" * 80)
        
        mapped_count = 0
        for symptom in test_symptoms:
            matches = self._find_evidence_matches(symptom)
            
            if matches:
                mapped_count += 1
                print(f"✅ '{symptom}'")
                for evidence_id, question in matches[:3]:
                    print(f"   → {evidence_id}: {question[:60]}...")
            else:
                print(f"❌ '{symptom}' - NO MATCH")
                self.warnings.append(f"No match for: {symptom}")
        
        print("-" * 80)
        print(f"Mapped: {mapped_count}/{len(test_symptoms)} symptoms")
        
        if mapped_count == 0:
            self.errors.append("CRITICAL: No symptoms mapped to evidences!")
        
        return mapped_count > 0
    
    def _find_evidence_matches(self, symptom_text: str) -> List[tuple]:
        """Find evidence IDs matching symptom text."""
        matches = []
        symptom_lower = symptom_text.lower()
        
        for evidence_id, evidence_data in self.evidences.items():
            question = evidence_data.get("question_en", "").lower()
            
            # Simple keyword matching
            if symptom_lower in question or any(word in question for word in symptom_lower.split()):
                matches.append((evidence_id, evidence_data.get("question_en", "")))
        
        return matches
    
    def test_4_disease_matching(self):
        """Test 4: Test disease matching logic."""
        print("\n" + "="*80)
        print("TEST 4: Disease Matching")
        print("="*80)
        
        # Simulate patient with GERD symptoms
        test_case = {
            "symptoms": ["chest burning", "worse after meals", "sour taste"],
            "expected_diagnosis": "GERD"
        }
        
        print(f"\nTest Case: {test_case['symptoms']}")
        print(f"Expected: {test_case['expected_diagnosis']}")
        print("-" * 80)
        
        # Map symptoms to evidence IDs
        evidence_ids = []
        for symptom in test_case['symptoms']:
            matches = self._find_evidence_matches(symptom)
            if matches:
                evidence_ids.append(matches[0][0])
        
        print(f"\nMapped Evidence IDs: {evidence_ids}")
        
        # Score all diseases
        results = []
        for disease_name, disease_data in self.conditions.items():
            disease_evidences = set(disease_data.get("symptoms", {}).keys())
            
            if not disease_evidences:
                continue
            
            matched = len(set(evidence_ids) & disease_evidences)
            total = len(disease_evidences)
            score = (matched / total * 100) if total > 0 else 0
            
            if score > 0:
                results.append({
                    'disease': disease_name,
                    'score': score,
                    'matched': matched,
                    'total': total
                })
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Show top 5
        print("\nTop 5 Matches:")
        print("-" * 80)
        print(f"{'Rank':<6} {'Disease':<40} {'Score':<10} {'Matched'}")
        print("-" * 80)
        
        for i, result in enumerate(results[:5], 1):
            print(f"{i:<6} {result['disease']:<40} {result['score']:>6.1f}%   {result['matched']}/{result['total']}")
        
        # Check if expected diagnosis is in top 3
        top_3_diseases = [r['disease'] for r in results[:3]]
        expected_found = any(test_case['expected_diagnosis'].lower() in d.lower() for d in top_3_diseases)
        
        if expected_found:
            print(f"\n✅ Expected diagnosis '{test_case['expected_diagnosis']}' found in top 3")
        else:
            print(f"\n❌ Expected diagnosis '{test_case['expected_diagnosis']}' NOT in top 3")
            print(f"   Top 3: {top_3_diseases}")
            self.warnings.append(f"Expected diagnosis not in top 3")
        
        return len(results) > 0
    
    def test_5_full_pipeline_simulation(self):
        """Test 5: Simulate full pipeline."""
        print("\n" + "="*80)
        print("TEST 5: Full Pipeline Simulation")
        print("="*80)
        
        # Simulate clinical note
        clinical_note = """
        Patient presents with episodic chest burning for 3 weeks.
        Pain worsens after meals and when lying flat.
        Reports sour taste in mouth and frequent belching.
        """
        
        print(f"\nClinical Note:\n{clinical_note}")
        
        # Extract symptoms (simulated)
        extracted_symptoms = [
            "chest burning",
            "worse after meals",
            "lying flat worsens",
            "sour taste",
            "belching"
        ]
        
        print(f"\nExtracted Symptoms: {extracted_symptoms}")
        
        # Normalize
        evidence_ids = []
        print("\nNormalization:")
        for symptom in extracted_symptoms:
            matches = self._find_evidence_matches(symptom)
            if matches:
                evidence_id = matches[0][0]
                evidence_ids.append(evidence_id)
                print(f"  '{symptom}' → {evidence_id}")
            else:
                print(f"  '{symptom}' → NO MATCH")
        
        print(f"\nNormalized Evidence IDs: {evidence_ids}")
        
        # Match diseases
        results = []
        for disease_name, disease_data in self.conditions.items():
            disease_evidences = set(disease_data.get("symptoms", {}).keys())
            
            if not disease_evidences:
                continue
            
            matched = len(set(evidence_ids) & disease_evidences)
            total = len(disease_evidences)
            score = (matched / total * 100) if total > 0 else 0
            
            if score > 0:
                results.append({
                    'disease': disease_data.get('cond-name-eng', disease_name),
                    'score': score,
                    'matched': matched,
                    'total': total
                })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        
        print("\nDifferential Diagnosis:")
        print("-" * 80)
        for i, result in enumerate(results[:5], 1):
            print(f"{i}. {result['disease']}")
            print(f"   Score: {result['score']:.1f}% ({result['matched']}/{result['total']} evidences)")
        
        return len(results) > 0
    
    def generate_audit_report(self):
        """Generate clinical reasoning audit report."""
        print("\n" + "="*80)
        print("CLINICAL REASONING AUDIT REPORT")
        print("="*80)
        
        audit = {
            "evidence_quality": {
                "high": 0,
                "moderate": 0,
                "non_specific": 0,
                "misleading": 0,
                "assessment": "insufficient" if self.errors else "sufficient"
            },
            "normalization_issues": [],
            "diagnosis_audit": [],
            "list_coherence": {
                "problem": len(self.errors) > 0,
                "explanation": "; ".join(self.errors) if self.errors else "No major issues"
            },
            "abstention_decision": {
                "should_abstain": len(self.errors) > 0,
                "reason": "Critical errors detected" if self.errors else "System functioning",
                "additional_data_needed": []
            },
            "failure_analysis": {
                "failure_stage": "evidence_normalization" if self.warnings else "none",
                "failure_type": "mapping_failure" if self.warnings else "none",
                "is_expected": False,
                "fix_category": "normalization" if self.warnings else "none"
            }
        }
        
        # Add normalization issues
        for warning in self.warnings:
            audit["normalization_issues"].append({
                "evidence": warning,
                "issue": "incorrect",
                "risk": "high",
                "explanation": "Evidence not mapped to DDXPlus vocabulary"
            })
        
        print("\nAudit Report (JSON):")
        print(json.dumps(audit, indent=2))
        
        return audit
    
    def run_all_tests(self):
        """Run all tests."""
        print("\n" + "="*100)
        print(" "*30 + "DDXPlus DEBUG & TEST SUITE")
        print("="*100)
        
        tests = [
            ("File Accessibility", self.test_1_file_accessibility),
            ("JSON Structure", self.test_2_json_structure),
            ("Evidence Mapping", self.test_3_evidence_mapping),
            ("Disease Matching", self.test_4_disease_matching),
            ("Full Pipeline Simulation", self.test_5_full_pipeline_simulation),
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
        print(" "*35 + "TEST SUMMARY")
        print("="*100)
        
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:<40} {status}")
        
        print("\n" + "="*100)
        print(f"Errors: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")
        print("="*100)
        
        if self.errors:
            print("\n❌ CRITICAL ERRORS:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        # Generate audit
        self.generate_audit_report()
        
        return len(self.errors) == 0


if __name__ == "__main__":
    # Run debugger
    debugger = DDXPlusDebugger(data_dir=".")
    success = debugger.run_all_tests()
    
    exit(0 if success else 1)
