"""
Symptom-Disease Dataset Service
Non-vector semantic matching for differential diagnosis generation.
Complements MedCaseReasoning with broader symptom coverage.
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Optional
from datasets import load_dataset
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class SymptomDiseaseService:
    """
    Loads and queries the symptom-disease dataset without vector indexing.
    Uses semantic fuzzy matching for diagnosis generation.
    Maps disease IDs to human-readable names.
    """
    
    def __init__(self):
        """Initialize and load the symptom-disease dataset."""
        logger.info("Initializing SymptomDiseaseService...")
        self.dataset = None
        self.disease_symptom_map = {}
        self.disease_id_map = {}
        self._load_disease_mapping()
        self._load_dataset()
    
    def _load_disease_mapping(self):
        """Load disease ID to name mapping."""
        try:
            mapping_path = Path(__file__).parent.parent / "config" / "disease_id_mapping.json"
            with open(mapping_path, 'r') as f:
                data = json.load(f)
                self.disease_id_map = data['disease_id_to_name']
            logger.info(f"✅ Loaded {len(self.disease_id_map)} disease ID mappings")
        except Exception as e:
            logger.warning(f"Failed to load disease ID mapping: {e}")
            self.disease_id_map = {}
    
    def _load_dataset(self):
        """Load symptom-disease dataset from HuggingFace."""
        try:
            logger.info("Loading symptom-disease dataset from HuggingFace...")
            self.dataset = load_dataset("dux-tecblic/symptom-disease-dataset")
            
            # Build disease → symptoms mapping for fast lookup
            self._build_disease_map()
            
            logger.info(f"✅ Loaded symptom-disease dataset: {len(self.disease_symptom_map)} unique diseases")
        except Exception as e:
            logger.error(f"Failed to load symptom-disease dataset: {e}")
            self.dataset = None
            self.disease_symptom_map = {}
    
    def _build_disease_map(self):
        """Build a mapping of disease → list of associated symptoms."""
        if not self.dataset or 'train' not in self.dataset:
            return
        
        logger.info(f"Building mapping from {len(self.dataset['train'])} rows...")
        
        for row in self.dataset['train']:
            # Standard format: 'label' = disease, 'text' = symptom
            # Try multiple variations
            disease = (
                row.get('label') or  # Most common for classification
                row.get('Label') or
                row.get('disease') or
                row.get('Disease') or
                row.get('prognosis')
            )
            
            symptom = (
                row.get('text') or  # Most common for classification
                row.get('Text') or
                row.get('symptom') or
                row.get('Symptom')
            )
            
            if disease and symptom:
                disease = str(disease).strip()
                symptom = str(symptom).strip().lower().replace('_', ' ')
                
                if disease not in self.disease_symptom_map:
                    self.disease_symptom_map[disease] = set()
                
                self.disease_symptom_map[disease].add(symptom)
        
        # Convert sets to lists
        self.disease_symptom_map = {
            disease: list(symptoms)
            for disease, symptoms in self.disease_symptom_map.items()
        }
        
        if self.disease_symptom_map:
            avg_symptoms = sum(len(s) for s in self.disease_symptom_map.values()) / len(self.disease_symptom_map)
            logger.info(f"Mapped {len(self.disease_symptom_map)} diseases, avg {avg_symptoms:.1f} symptoms/disease")
    
    def generate_diagnoses(
        self,
        patient_symptoms: List[str],
        negations: List[str] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Generate differential diagnoses using semantic symptom matching.
        
        Args:
            patient_symptoms: List of patient symptoms
            negations: List of negated/absent symptoms
            top_k: Number of top diagnoses to return
            
        Returns:
            List of diagnosis dictionaries with reasoning
        """
        if not self.disease_symptom_map:
            logger.warning("Symptom-disease dataset not loaded, returning empty results")
            return []
        
        # Normalize patient symptoms
        normalized_patient_symptoms = [s.lower().strip() for s in patient_symptoms]
        
        # Normalize negations
        normalized_negations = [s.lower().strip() for s in (negations or [])]
        
        # Score all diseases
        disease_scores = []
        
        for disease, disease_symptoms in self.disease_symptom_map.items():
            score = self._calculate_symptom_match_score(
                normalized_patient_symptoms,
                disease_symptoms,
                normalized_negations  # Pass negations
            )
            
            if score > 0.0:  # Only include if there's some match
                disease_scores.append({
                    'disease': disease,
                    'score': score,
                    'matched_symptoms': self._find_matched_symptoms(
                        normalized_patient_symptoms,
                        disease_symptoms
                    )
                })
        
        # Sort by score (descending)
        disease_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Take top K
        top_diseases = disease_scores[:top_k]
        
        # Format as diagnosis objects
        diagnoses = []
        for idx, match in enumerate(top_diseases, 1):
            # Map disease ID to real name
            disease_id = match['disease']
            disease_name = self.disease_id_map.get(str(disease_id), f"Unknown Disease ({disease_id})")
            
            diagnoses.append({
                "diagnosis": disease_name,  # Use mapped name
                "reasoning": self._generate_reasoning(
                    disease_name,
                    match['matched_symptoms'],
                    patient_symptoms
                ),
                "confidence": {
                    "overall_confidence": round(match['score'], 3),
                    "evidence_strength": round(match['score'] * 0.9, 3),
                    "reasoning_consistency": 0.85
                },
                "evidence_type": "symptom-disease-mapping",
                "external_evidence": {
                    "dataset": "dux-tecblic/symptom-disease-dataset",
                    "disease_id": disease_id,  # Keep original ID for reference
                    "matched_symptoms": match['matched_symptoms'],
                    "total_dataset_symptoms": len(self.disease_symptom_map.get(match['disease'], []))
                }
            })
        
        logger.info(f"Generated {len(diagnoses)} diagnoses from symptom-disease dataset")
        return diagnoses
    
    def _calculate_symptom_match_score(
        self,
        patient_symptoms: List[str],
        disease_symptoms: List[str],
        negations: List[str] = None
    ) -> float:
        """
        Calculate semantic similarity score between patient and disease symptoms.
        Uses fuzzy string matching (not vector similarity).
        
        APPLIES NEGATION PENALTY: If patient denies a key disease symptom, score decreases.
        
        Args:
            patient_symptoms: Patient's symptoms (normalized)
            disease_symptoms: Disease's known symptoms (normalized)
            negations: Patient's denied symptoms
            
        Returns:
            Match score (0.0-1.0)
        """
        if not patient_symptoms or not disease_symptoms:
            return 0.0
        
        total_match_score = 0.0
        
        for patient_symptom in patient_symptoms:
            # Find best match for this patient symptom among disease symptoms
            best_match_score = 0.0
            
            for disease_symptom in disease_symptoms:
                # Use fuzzy string matching (Sequence Matcher)
                similarity = self._fuzzy_match(patient_symptom, disease_symptom)
                
                if similarity > best_match_score:
                    best_match_score = similarity
            
            total_match_score += best_match_score
        
        # Normalize by number of patient symptoms
        average_match = total_match_score / len(patient_symptoms)
        
        # Boost if many symptoms match
        coverage_boost = len(patient_symptoms) / (len(patient_symptoms) + 2)
        
        final_score = average_match * coverage_boost
        
        # APPLY NEGATION PENALTY
        if negations:
            negation_penalty = 0.0
            for negation in negations:
                for disease_symptom in disease_symptoms:
                    if self._fuzzy_match(negation, disease_symptom) >= 0.7:
                        negation_penalty += 0.15  # -15% per negated key symptom
            
            final_score = max(final_score - negation_penalty, 0.0)
        
        return min(final_score, 1.0)
    
    def _fuzzy_match(self, str1: str, str2: str, threshold: float = 0.4) -> float:
        """
        Calculate fuzzy string similarity (0.0-1.0).
        Lowered threshold to 0.4 for better matching with simple symptom terms.
        
        Args:
            str1: First string
            str2: Second string
            threshold: Minimum similarity to consider a match (default 0.4)
            
        Returns:
            Similarity score
        """
        # Exact match
        if str1 == str2:
            return 1.0
        
        # Substring check
        if str1 in str2 or str2 in str1:
            return 0.9
        
        # Fuzzy matching
        similarity = SequenceMatcher(None, str1, str2).ratio()
        
        return similarity if similarity >= threshold else 0.0
    
    def _find_matched_symptoms(
        self,
        patient_symptoms: List[str],
        disease_symptoms: List[str]
    ) -> List[str]:
        """
        Find which patient symptoms matched with disease symptoms.
        
        Returns:
            List of matched symptom pairs
        """
        matched = []
        
        for patient_symptom in patient_symptoms:
            for disease_symptom in disease_symptoms:
                if self._fuzzy_match(patient_symptom, disease_symptom) >= 0.5:  # Lowered from 0.7
                    matched.append(f"{patient_symptom} → {disease_symptom}")
                    break  # One match per patient symptom
        
        return matched[:5]  # Limit to top 5
    
    def _generate_reasoning(
        self,
        disease: str,
        matched_symptoms: List[str],
        original_symptoms: List[str]
    ) -> str:
        """
        Generate clinical reasoning text for the diagnosis.
        
        Args:
            disease: Disease name
            matched_symptoms: Matched symptom pairs
            original_symptoms: Original patient symptoms
            
        Returns:
            Reasoning text
        """
        if not matched_symptoms:
            return f"{disease} is suggested based on overall symptom pattern analysis from the symptom-disease mapping dataset."
        
        # Extract just the patient-side symptoms
        patient_matched = [m.split('→')[0].strip() for m in matched_symptoms]
        
        reasoning = f"{disease} is supported by semantic alignment with the symptom-disease dataset. "
        reasoning += f"Key symptom matches include: {', '.join(patient_matched[:3])}. "
        reasoning += f"This hypothesis is derived from pattern matching across {len(matched_symptoms)} overlapping clinical features. "
        reasoning += "This is hypothesis generation and should support, not replace, clinical judgment."
        
        return reasoning
