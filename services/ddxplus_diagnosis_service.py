"""
DDXPlus Diagnosis Service
Uses release_conditions.json and release_evidences.json for diagnosis generation.

NO VECTOR DB - Pure JSON lookup and matching.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

logger = logging.getLogger(__name__)


class DDXPlusDiagnosisService:
    """
    DDXPlus-based diagnosis generation using structured medical knowledge.
    
    Uses:
    - release_conditions.json: Disease → symptom mappings
    - release_evidences.json: Symptom vocabulary
    
    NO vector DB, NO embeddings - pure deterministic matching.
    """
    
    def __init__(self, data_dir: str = "."):
        """
        Initialize DDXPlus service.
        
        Args:
            data_dir: Directory containing JSON files (default: root)
        """
        logger.info("Initializing DDXPlusDiagnosisService...")
        
        self.data_dir = Path(data_dir)
        self.conditions = {}
        self.evidences = {}
        self.disease_symptom_map = defaultdict(set)
        
        self._load_data()
        self._build_lookup_table()
    
    def _load_data(self):
        """Load DDXPlus JSON files."""
        try:
            # Load conditions
            conditions_file = self.data_dir / "release_conditions.json"
            logger.info(f"Loading conditions from: {conditions_file}")
            
            with open(conditions_file, 'r', encoding='utf-8') as f:
                self.conditions = json.load(f)
            
            logger.info(f"✅ Loaded {len(self.conditions)} conditions")
            
            # Load evidences
            evidences_file = self.data_dir / "release_evidences.json"
            logger.info(f"Loading evidences from: {evidences_file}")
            
            with open(evidences_file, 'r', encoding='utf-8') as f:
                self.evidences = json.load(f)
            
            logger.info(f"✅ Loaded {len(self.evidences)} evidences")
            
        except FileNotFoundError as e:
            logger.error(f"❌ DDXPlus files not found: {e}")
            logger.error("   Please ensure release_conditions.json and release_evidences.json are in the root directory")
            raise
        except Exception as e:
            logger.error(f"❌ Error loading DDXPlus data: {e}")
            raise
    
    def _build_lookup_table(self):
        """Build disease → symptom lookup table."""
        logger.info("Building disease → symptom lookup table...")
        
        for cond_name, cond_data in self.conditions.items():
            # Get symptoms for this condition
            symptoms = cond_data.get("symptoms", {})
            
            for evidence_code in symptoms.keys():
                self.disease_symptom_map[cond_name].add(evidence_code)
        
        logger.info(f"✅ Built lookup table for {len(self.disease_symptom_map)} diseases")
    
    def normalize_symptoms(self, clinical_text: str, extracted_symptoms: List[str]) -> List[str]:
        """
        Normalize extracted symptoms to DDXPlus evidence IDs.
        
        Args:
            clinical_text: Raw clinical note
            extracted_symptoms: List of symptom strings
        
        Returns:
            List of evidence IDs (e.g., ["E_100", "E_101"])
        """
        evidence_ids = []
        
        # Simple keyword matching (can be enhanced with NLP)
        for symptom in extracted_symptoms:
            symptom_lower = symptom.lower()
            
            # Search evidences for matches
            for evidence_id, evidence_data in self.evidences.items():
                question = evidence_data.get("question_en", "").lower()
                
                # Simple keyword match
                if symptom_lower in question or any(word in question for word in symptom_lower.split()):
                    evidence_ids.append(evidence_id)
                    logger.debug(f"Matched '{symptom}' → {evidence_id}")
                    break
        
        return evidence_ids
    
    def calculate_match_score(
        self, 
        patient_evidences: List[str], 
        disease_evidences: Set[str],
        patient_data: Dict = None
    ) -> float:
        """
        PROPORTIONAL confidence scoring (NEVER > 100).
        Prevents overconfidence from simple matches.
        
        Scoring:
        - Base: Proportional to evidence matched (0-100)
        - Bonus: Multiple independent evidences (+10 max)
        - Penalty: Single nonspecific feature (-30)
        - Penalty: Contradicts negative findings (-10 each)
        
        Args:
            patient_evidences: List of patient evidence IDs
            disease_evidences: Set of disease evidence IDs
            patient_data: Full patient data with negations, modifiers
        
        Returns:
            Match score (0-100, HARD CAPPED)
        """
        if not disease_evidences:
            return 0.0
        
        # Count matches
        patient_evidences_set = set(patient_evidences)
        matches = patient_evidences_set & disease_evidences
        match_count = len(matches)
        
        if match_count == 0:
            return 0.0
        
        # PART 1: Base score (proportional, never > 100)
        total_disease_evidences = len(disease_evidences)
        base_score = (match_count / total_disease_evidences) * 100
        
        # PART 2: Bonus for multiple independent evidences
        if match_count >= 3:
            bonus = min(10, match_count * 2)  # Cap bonus at 10
        else:
            bonus = 0
        
        # PART 3: Penalty for few evidences (REDUCED)
        if match_count == 1:
            penalty_single = 15  # Reduced from -30 to -15
        elif match_count == 2:
            penalty_single = 5  # Reduced from -10 to -5
        else:
            penalty_single = 0
        
        # PART 4: Penalty for contradictions with negations (REDUCED, if patient_data provided)
        penalty_negation = 0
        if patient_data:
            negative_findings = patient_data.get("negative_findings", [])
            if negative_findings:
                # Check if any matched evidence contradicts a negation
                for negation in negative_findings:
                    negation_lower = negation.lower()
                    for evidence_id in matches:
                        evidence_data = self.evidences.get(evidence_id, {})
                        question = evidence_data.get("question_en", "").lower()
                        
                        # If negation contradicts this evidence
                        if negation_lower in question:
                            penalty_negation += 5  # Reduced from -10 to -5
        
        # CALCULATE FINAL SCORE
        final_score = base_score + bonus - penalty_single - penalty_negation
        
        # HARD CAP AT 100 (prevent overflow)
        normalized_score = min(max(final_score, 0), 100)
        
        # DEBUG: Always log score calculation
        logger.debug(f"DDXPlus score: matches={match_count}/{total_disease_evidences}, base={base_score:.2f}, bonus={bonus}, penalty_s={penalty_single}, penalty_n={penalty_negation}, final={final_score:.2f}, capped={normalized_score:.2f}")
        
        # CRITICAL CHECK
        if normalized_score > 100:
            logger.error(f"🔴 BUG: Score exceeded 100 after cap! base={base_score}, final={final_score}, capped={normalized_score}")
        
        return normalized_score
    
    def generate_diagnoses(
        self, 
        clinical_note: str, 
        normalized_data: Dict,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Generate differential diagnoses using DDXPlus.
        
        Args:
            clinical_note: Raw clinical text
            normalized_data: Dict with 'symptoms' key
            top_k: Number of diagnoses to return
        
        Returns:
            List of diagnosis dicts with provenance
        """
        logger.info("Generating diagnoses using DDXPlus...")
        
        # Get patient symptoms as strings
        patient_symptoms = normalized_data.get("symptom_names", normalized_data.get("symptoms", []))
        
        # Ensure symptoms are strings
        if patient_symptoms and isinstance(patient_symptoms[0], dict):
            patient_symptoms = [s.get("symptom", "") for s in patient_symptoms]
        
        if not patient_symptoms:
            logger.warning("No symptoms provided - cannot generate diagnoses")
            return []
        
        # Normalize symptoms to evidence IDs
        patient_evidence_ids = self.normalize_symptoms(clinical_note, patient_symptoms)
        
        if not patient_evidence_ids:
            logger.warning("No symptoms matched to DDXPlus evidences")
            return []
        
        logger.info(f"Matched {len(patient_evidence_ids)} symptoms to DDXPlus evidences")
        
        # Score all diseases
        results = []
        
        for disease_name, disease_evidences in self.disease_symptom_map.items():
            # Calculate match score with weighted confidence
            score = self.calculate_match_score(
                patient_evidence_ids, 
                disease_evidences,
                patient_data=normalized_data  # Pass for negation penalties
            )
            
            # DEBUG: Log returned score
            if score > 100:
                logger.error(f"🔴 calculate_match_score returned {score} for {disease_name} - SHOULD BE CAPPED AT 100!")
            
            if score > 0:  # Only include diseases with some match
                # Get disease metadata
                cond_data = self.conditions.get(disease_name, {})
                disease_full_name = cond_data.get("cond-name-eng", disease_name)
                severity = cond_data.get("severity", 5)
                
                # Get matched evidences
                matched_evidences = set(patient_evidence_ids) & disease_evidences
                matched_evidence_names = [
                    self.evidences.get(e, {}).get("question_en", e)
                    for e in matched_evidences
                ]
                
                # Determine evidence strength
                if score >= 60:
                    evidence_strength = "strong"
                elif score >= 40:
                    evidence_strength = "moderate"
                else:
                    evidence_strength = "weak"
                
                results.append({
                    'diagnosis': disease_full_name,
                    'priority': 0,  # Will be set after sorting
                    'status': 'ddxplus-matched',
                    'description': f'DDXPlus match ({score:.1f}% evidence overlap)',
                    'reasoning': f'{disease_full_name} matched based on {len(matched_evidences)} overlapping symptoms from DDXPlus knowledge base.',
                    'evidence_type': 'ddxplus-structured',
                    'match_score': score,
                    'severity': severity,
                    'matched_evidences': matched_evidence_names,
                    
                    # NEW: Symptom-Disease Mapping Evidence
                    'symptom_disease_mapping_sources': [{
                        'source': 'release_conditions.json (DDXPlus)',
                        'matched_conditions': matched_evidence_names,
                        'pathophysiology': f'{disease_full_name} pathophysiology match',
                        'evidence_strength': evidence_strength,
                        'match_score': score,
                        'condition_count': len(matched_evidences)
                    }],
                    
                    'provenance': {
                        'source': 'rule',  # DDXPlus is rule-based
                        'rule_applied': True,
                        'llm_used': False
                    }
                })
        
        # Sort by match score (descending)
        results.sort(key=lambda x: x['match_score'], reverse=True)
        
        # FINAL NORMALIZATION: Ensure all scores are in 0-100 range
        if results:
            max_score = max(r['match_score'] for r in results)
            if max_score > 100:
                # Normalize all scores relative to max
                for result in results:
                    result['match_score'] = min(100, (result['match_score'] / max_score) * 100)
                logger.info(f"Normalized DDXPlus scores (max was {max_score:.1f}, now capped at 100)")
        
        # Set priorities
        for i, result in enumerate(results[:top_k], 1):
            result['priority'] = i
        
        logger.info(f"✅ Generated {len(results[:top_k])} diagnoses from DDXPlus")
        
        return results[:top_k]
    
    def get_disease_info(self, disease_name: str) -> Dict:
        """Get detailed information about a disease."""
        return self.conditions.get(disease_name, {})
    
    def get_evidence_info(self, evidence_id: str) -> Dict:
        """Get detailed information about an evidence."""
        return self.evidences.get(evidence_id, {})
